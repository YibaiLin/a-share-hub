"""
历史数据回填脚本

用于批量采集全市场历史日线数据
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import setup_logger, logger
from core.database import get_db_client, close_db_client
from collectors.stock_list import StockListCollector
from collectors.daily import DailyCollector
from storage.clickhouse_handler import ClickHouseHandler
from utils.progress import ProgressTracker
from utils.date_helper import format_date
from utils.failure_monitor import FailureMonitor
from utils.rate_limit_detector import RateLimitDetector, is_rate_limit_error


async def backfill_all_stocks(
    start_date: str,
    end_date: str,
    concurrency: int = 1,
    resume: bool = False
):
    """
    回填全市场股票数据

    Args:
        start_date: 开始日期（YYYYMMDD）
        end_date: 结束日期（YYYYMMDD）
        concurrency: 并发数（默认1）
        resume: 是否断点续传

    Returns:
        采集报告字典
    """
    logger.info("=" * 80)
    logger.info("开始历史数据回填")
    logger.info("=" * 80)
    logger.info(f"日期范围: {start_date} ~ {end_date}")
    logger.info(f"并发数: {concurrency}")
    logger.info(f"断点续传: {'是' if resume else '否'}")

    start_time = datetime.now()

    try:
        # 初始化进度跟踪器
        tracker = ProgressTracker()

        # 获取股票列表
        logger.info("获取股票列表...")
        stock_list_collector = StockListCollector()
        all_stocks = await stock_list_collector.get_all_stocks()
        logger.info(f"获取到 {len(all_stocks)} 只股票")

        # 检查是否恢复进度
        if resume and tracker.has_progress():
            logger.info("检测到已有进度，继续回填")
            stocks_to_collect = tracker.get_remaining_stocks(all_stocks)
            tracker.print_summary()
        else:
            logger.info("开始新的回填任务")
            tracker.init_progress(start_date, end_date, len(all_stocks))
            stocks_to_collect = all_stocks

        if not stocks_to_collect:
            logger.info("所有股票已完成，无需回填")
            return _generate_report(tracker, start_time)

        logger.info(f"待采集: {len(stocks_to_collect)} 只股票")

        # 初始化采集器和存储
        daily_collector = DailyCollector()
        client = get_db_client()
        handler = ClickHouseHandler(client)

        # 初始化失败监控器
        failure_monitor = FailureMonitor(
            threshold=10,  # 连续失败10次触发暂停
            pause_duration=60,  # 暂停60秒
            enable=True
        )
        logger.info(f"失败监控: 阈值={failure_monitor.threshold}, 暂停时长={failure_monitor.pause_duration}秒")

        # 初始化智能限流探测器（指定数据源和接口）
        rate_limit_detector = RateLimitDetector(
            enable=True,
            source="akshare",
            interface="stock_zh_a_hist",
            data_type="daily",
            description="A股日线数据"
        )
        logger.info("智能限流探测: 已启用")

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(concurrency)

        # 批量采集
        success_count = 0
        failed_count = 0

        # 使用tqdm显示进度
        with tqdm(
            total=len(stocks_to_collect),
            desc="采集进度",
            unit="只",
            ncols=100
        ) as pbar:
            for ts_code in stocks_to_collect:
                async with semaphore:
                    # 检查失败监控器是否需要暂停
                    failure_monitor.wait_if_paused()

                    # 检查智能限流探测器是否需要暂停
                    should_wait, wait_seconds = await rate_limit_detector.should_pause()
                    if should_wait:
                        # 更新进度条显示等待状态
                        if rate_limit_detector.state == "PROBING":
                            pbar.set_postfix_str(f"探测等待 (第{rate_limit_detector.probe_count + 1}次)")
                        elif rate_limit_detector.state == "CONFIRMED":
                            pbar.set_postfix_str(f"智能暂停 ({wait_seconds}秒)")
                        await asyncio.sleep(wait_seconds)

                    try:
                        # 更新进度条描述
                        pbar.set_postfix_str(f"当前: {ts_code}")

                        # 采集数据
                        data = await daily_collector.collect(
                            symbol=ts_code,
                            start_date=start_date,
                            end_date=end_date
                        )

                        # 记录成功请求到限流探测器
                        rate_limit_detector.record_success()

                        # 如果在探测阶段试探成功，确认窗口
                        if rate_limit_detector.state == "PROBING":
                            await rate_limit_detector.on_probe_success()
                            logger.info("继续采集...")

                        if not data:
                            logger.debug(f"{ts_code} 无数据")
                            tracker.mark_success(ts_code, 0)
                            # 无数据算成功（可能停牌）
                            failure_monitor.on_success()
                            pbar.update(1)
                            continue

                        # 存储数据
                        inserted = handler.insert_daily(
                            ts_code=ts_code,
                            data=data,
                            deduplicate=True
                        )

                        # 标记成功
                        tracker.mark_success(ts_code, inserted)
                        success_count += 1
                        # 通知监控器采集成功
                        failure_monitor.on_success()

                        logger.debug(f"✓ {ts_code}: {inserted} 条记录")

                    except Exception as e:
                        error_msg = str(e)

                        # 判断是否为限流错误
                        if is_rate_limit_error(e):
                            logger.warning(f"🚨 {ts_code} 触发限流: {error_msg}")

                            # 根据当前状态通知限流探测器
                            if rate_limit_detector.state == "NORMAL":
                                await rate_limit_detector.on_rate_limit_triggered()
                            elif rate_limit_detector.state == "PROBING":
                                await rate_limit_detector.on_probe_failed()
                            elif rate_limit_detector.state == "CONFIRMED":
                                await rate_limit_detector.on_rate_limit_re_triggered()

                            # 标记失败（后续可重试）
                            tracker.mark_failed(ts_code, f"限流: {error_msg}")
                            failed_count += 1
                            # 不继续采集当前股票，等待探测完成
                        else:
                            # 其他错误
                            logger.error(f"✗ {ts_code} 采集失败: {error_msg}")
                            tracker.mark_failed(ts_code, error_msg)
                            failed_count += 1
                            # 通知监控器采集失败
                            failure_monitor.on_failure(error_msg)

                    finally:
                        pbar.update(1)

        # 生成报告
        logger.info("=" * 80)
        logger.info("回填完成")
        logger.info("=" * 80)

        # 打印监控统计
        monitor_stats = failure_monitor.get_stats()
        if monitor_stats["pause_count"] > 0:
            logger.info(f"监控统计: 暂停{monitor_stats['pause_count']}次, 总失败{monitor_stats['total_failures']}次")

        # 打印限流探测统计
        rate_limit_detector.print_summary()

        report = _generate_report(tracker, start_time)
        _print_report(report)

        return report

    except Exception as e:
        logger.error(f"回填失败: {e}")
        raise

    finally:
        close_db_client()


async def retry_failed_stocks():
    """
    重试失败的股票

    从进度文件中读取失败股票列表，重新采集

    Returns:
        采集报告字典
    """
    logger.info("=" * 80)
    logger.info("重试失败股票")
    logger.info("=" * 80)

    start_time = datetime.now()

    try:
        # 加载进度
        tracker = ProgressTracker()
        if not tracker.has_progress():
            logger.error("未找到进度文件，无法重试")
            return None

        failed_stocks = tracker.get_failed_stocks()
        failed_details = tracker.get_failed_details()

        if not failed_stocks:
            logger.info("没有失败的股票需要重试")
            return None

        logger.info(f"发现 {len(failed_stocks)} 只失败股票")

        # 显示失败详情（前10个）
        for ts_code in failed_stocks[:10]:
            error = failed_details.get(ts_code, "未知错误")
            logger.warning(f"  - {ts_code}: {error}")
        if len(failed_stocks) > 10:
            logger.warning(f"  ... 还有 {len(failed_stocks) - 10} 只")

        # 获取日期范围
        start_date = tracker.progress_data.get("start_date")
        end_date = tracker.progress_data.get("end_date")
        logger.info(f"日期范围: {start_date} ~ {end_date}")

        # 初始化采集器和存储
        daily_collector = DailyCollector()
        client = get_db_client()
        handler = ClickHouseHandler(client)

        # 初始化失败监控器
        failure_monitor = FailureMonitor(
            threshold=10,
            pause_duration=60,
            enable=True
        )

        # 初始化智能限流探测器（指定数据源和接口）
        rate_limit_detector = RateLimitDetector(
            enable=True,
            source="akshare",
            interface="stock_zh_a_hist",
            data_type="daily",
            description="A股日线数据"
        )
        logger.info("智能限流探测: 已启用")

        success_count = 0
        failed_count = 0

        # 使用tqdm显示进度
        with tqdm(total=len(failed_stocks), desc="重试进度", unit="只", ncols=100) as pbar:
            for ts_code in failed_stocks:
                # 检查失败监控器是否需要暂停
                failure_monitor.wait_if_paused()

                # 检查智能限流探测器是否需要暂停
                should_wait, wait_seconds = await rate_limit_detector.should_pause()
                if should_wait:
                    if rate_limit_detector.state == "PROBING":
                        pbar.set_postfix_str(f"探测等待 (第{rate_limit_detector.probe_count + 1}次)")
                    elif rate_limit_detector.state == "CONFIRMED":
                        pbar.set_postfix_str(f"智能暂停 ({wait_seconds}秒)")
                    await asyncio.sleep(wait_seconds)

                try:
                    pbar.set_postfix_str(f"当前: {ts_code}")

                    # 采集数据
                    data = await daily_collector.collect(
                        symbol=ts_code,
                        start_date=start_date,
                        end_date=end_date
                    )

                    # 记录成功请求
                    rate_limit_detector.record_success()

                    # 如果在探测阶段试探成功，确认窗口
                    if rate_limit_detector.state == "PROBING":
                        await rate_limit_detector.on_probe_success()
                        logger.info("继续重试...")

                    if not data:
                        logger.debug(f"{ts_code} 无数据")
                        tracker.mark_success(ts_code, 0)
                        failure_monitor.on_success()
                        success_count += 1
                        pbar.update(1)
                        continue

                    # 存储数据
                    inserted = handler.insert_daily(
                        ts_code=ts_code,
                        data=data,
                        deduplicate=True
                    )

                    # 标记成功
                    tracker.mark_success(ts_code, inserted)
                    failure_monitor.on_success()
                    success_count += 1

                    logger.info(f"✓ {ts_code}: {inserted} 条记录")

                except Exception as e:
                    error_msg = str(e)

                    # 判断是否为限流错误
                    if is_rate_limit_error(e):
                        logger.warning(f"🚨 {ts_code} 触发限流: {error_msg}")

                        # 根据当前状态通知限流探测器
                        if rate_limit_detector.state == "NORMAL":
                            await rate_limit_detector.on_rate_limit_triggered()
                        elif rate_limit_detector.state == "PROBING":
                            await rate_limit_detector.on_probe_failed()
                        elif rate_limit_detector.state == "CONFIRMED":
                            await rate_limit_detector.on_rate_limit_re_triggered()
                        tracker.mark_failed(ts_code, f"限流: {error_msg}")
                        failed_count += 1
                    else:
                        logger.error(f"✗ {ts_code} 重试失败: {error_msg}")
                        tracker.mark_failed(ts_code, error_msg)
                        failure_monitor.on_failure(error_msg)
                        failed_count += 1

                finally:
                    pbar.update(1)

        # 生成报告
        logger.info("=" * 80)
        logger.info("重试完成")
        logger.info("=" * 80)

        # 打印监控统计
        monitor_stats = failure_monitor.get_stats()
        if monitor_stats["pause_count"] > 0:
            logger.info(f"监控统计: 暂停{monitor_stats['pause_count']}次, 总失败{monitor_stats['total_failures']}次")

        # 打印限流探测统计
        rate_limit_detector.print_summary()

        report = {
            "total_retried": len(failed_stocks),
            "success": success_count,
            "failed": failed_count,
            "duration": (datetime.now() - start_time).total_seconds()
        }

        logger.info(f"重试股票数: {report['total_retried']}")
        logger.info(f"成功: {report['success']}")
        logger.info(f"失败: {report['failed']}")
        logger.info(f"耗时: {report['duration']:.1f} 秒")

        # 显示剩余失败股票
        remaining_failed = tracker.get_failed_stocks()
        if remaining_failed:
            logger.warning(f"仍有 {len(remaining_failed)} 只失败: {', '.join(remaining_failed[:5])}")
            if len(remaining_failed) > 5:
                logger.warning(f"... 还有 {len(remaining_failed) - 5} 只")

        return report

    except Exception as e:
        logger.error(f"重试失败: {e}")
        raise

    finally:
        close_db_client()


async def backfill_specific_stocks(
    symbols: list[str],
    start_date: str,
    end_date: str
):
    """
    回填指定股票数据

    Args:
        symbols: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        采集报告字典
    """
    logger.info("=" * 80)
    logger.info("回填指定股票")
    logger.info("=" * 80)
    logger.info(f"股票列表: {', '.join(symbols)}")
    logger.info(f"日期范围: {start_date} ~ {end_date}")

    start_time = datetime.now()

    try:
        # 初始化采集器和存储
        daily_collector = DailyCollector()
        client = get_db_client()
        handler = ClickHouseHandler(client)

        success_count = 0
        failed_count = 0
        total_records = 0

        # 使用tqdm显示进度
        with tqdm(total=len(symbols), desc="采集进度", unit="只", ncols=100) as pbar:
            for ts_code in symbols:
                try:
                    pbar.set_postfix_str(f"当前: {ts_code}")

                    # 采集数据
                    data = await daily_collector.collect(
                        symbol=ts_code,
                        start_date=start_date,
                        end_date=end_date
                    )

                    if not data:
                        logger.warning(f"{ts_code} 无数据")
                        pbar.update(1)
                        continue

                    # 存储数据
                    inserted = handler.insert_daily(
                        ts_code=ts_code,
                        data=data,
                        deduplicate=True
                    )

                    success_count += 1
                    total_records += inserted
                    logger.info(f"✓ {ts_code}: {inserted} 条记录")

                except Exception as e:
                    logger.error(f"✗ {ts_code} 采集失败: {e}")
                    failed_count += 1

                finally:
                    pbar.update(1)

        # 生成简化报告
        report = {
            "total_stocks": len(symbols),
            "success": success_count,
            "failed": failed_count,
            "total_records": total_records,
            "duration": (datetime.now() - start_time).total_seconds()
        }

        logger.info("=" * 80)
        logger.info("回填完成")
        logger.info("=" * 80)
        _print_report(report)

        return report

    except Exception as e:
        logger.error(f"回填失败: {e}")
        raise

    finally:
        close_db_client()


def _generate_report(tracker: ProgressTracker, start_time: datetime) -> dict:
    """
    生成采集报告

    Args:
        tracker: 进度跟踪器
        start_time: 开始时间

    Returns:
        报告字典
    """
    stats = tracker.get_statistics()
    duration = (datetime.now() - start_time).total_seconds()

    return {
        "total_stocks": stats["total_stocks"],
        "completed": stats["completed"],
        "success": stats["success"],
        "failed": stats["failed"],
        "total_records": stats["total_records"],
        "duration": duration,
        "failed_stocks": tracker.get_failed_stocks()
    }


def _print_report(report: dict):
    """
    打印采集报告

    Args:
        report: 报告字典
    """
    logger.info(f"总股票数: {report.get('total_stocks', 0)}")
    logger.info(f"成功: {report.get('success', 0)}")
    logger.info(f"失败: {report.get('failed', 0)}")
    logger.info(f"总记录数: {report.get('total_records', 0)}")
    logger.info(f"耗时: {report.get('duration', 0):.1f} 秒")

    if report.get("failed_stocks"):
        failed = report["failed_stocks"]
        logger.warning(f"失败股票 ({len(failed)}): {', '.join(failed[:10])}")
        if len(failed) > 10:
            logger.warning(f"... 还有 {len(failed) - 10} 只")


def main():
    """
    主函数
    """
    # 初始化日志
    setup_logger()

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="A-Share Hub - 历史数据回填脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 全市场回填（推荐）
  python scripts/backfill.py --start-date 20200101 --all

  # 指定股票回填
  python scripts/backfill.py --start-date 20200101 --symbols 000001.SZ,600000.SH

  # 断点续传
  python scripts/backfill.py --resume

  # 重试失败股票
  python scripts/backfill.py --retry-failed

  # 控制并发数
  python scripts/backfill.py --start-date 20200101 --all --concurrency 3

  # 清除进度重新开始
  python scripts/backfill.py --start-date 20200101 --all --clean
        """
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="开始日期（YYYYMMDD），如 20200101"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=format_date(datetime.now()),
        help="结束日期（YYYYMMDD），默认今天"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="回填全市场股票"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="指定股票代码（逗号分隔），如 000001.SZ,600000.SH"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="断点续传（从上次中断处继续）"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="重试失败的股票"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="并发数（默认1，建议不超过5）"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清除进度重新开始"
    )
    parser.add_argument(
        "--show-boundaries",
        action="store_true",
        help="显示限流边界信息"
    )

    args = parser.parse_args()

    # 验证参数
    if args.show_boundaries:
        # 显示限流边界信息
        from utils.rate_limit_detector import print_all_boundaries
        print_all_boundaries()
        return

    if args.clean:
        tracker = ProgressTracker()
        tracker.clear_progress()
        logger.info("进度已清除")
        return

    if args.retry_failed:
        # 重试失败股票模式
        asyncio.run(retry_failed_stocks())

    elif args.resume:
        # 断点续传模式
        tracker = ProgressTracker()
        if not tracker.has_progress():
            logger.error("未找到可恢复的进度，请先执行回填任务")
            sys.exit(1)

        # 从进度中获取日期范围
        start_date = tracker.progress_data.get("start_date")
        end_date = tracker.progress_data.get("end_date")

        asyncio.run(backfill_all_stocks(
            start_date=start_date,
            end_date=end_date,
            concurrency=args.concurrency,
            resume=True
        ))

    elif args.all:
        # 全市场回填
        if not args.start_date:
            logger.error("全市场回填需要指定--start-date参数")
            sys.exit(1)

        asyncio.run(backfill_all_stocks(
            start_date=args.start_date,
            end_date=args.end_date,
            concurrency=args.concurrency,
            resume=False
        ))

    elif args.symbols:
        # 指定股票回填
        if not args.start_date:
            logger.error("指定股票回填需要指定--start-date参数")
            sys.exit(1)

        symbols = [s.strip() for s in args.symbols.split(",")]
        asyncio.run(backfill_specific_stocks(
            symbols=symbols,
            start_date=args.start_date,
            end_date=args.end_date
        ))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
