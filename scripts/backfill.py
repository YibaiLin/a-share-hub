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
                    try:
                        # 更新进度条描述
                        pbar.set_postfix_str(f"当前: {ts_code}")

                        # 采集数据
                        data = await daily_collector.collect(
                            symbol=ts_code,
                            start_date=start_date,
                            end_date=end_date
                        )

                        if not data:
                            logger.debug(f"{ts_code} 无数据")
                            tracker.mark_success(ts_code, 0)
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

                        logger.debug(f"✓ {ts_code}: {inserted} 条记录")

                    except Exception as e:
                        logger.error(f"✗ {ts_code} 采集失败: {e}")
                        tracker.mark_failed(ts_code)
                        failed_count += 1

                    finally:
                        pbar.update(1)

        # 生成报告
        logger.info("=" * 80)
        logger.info("回填完成")
        logger.info("=" * 80)

        report = _generate_report(tracker, start_time)
        _print_report(report)

        return report

    except Exception as e:
        logger.error(f"回填失败: {e}")
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

    args = parser.parse_args()

    # 验证参数
    if args.clean:
        tracker = ProgressTracker()
        tracker.clear_progress()
        logger.info("进度已清除")
        return

    if args.resume:
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
