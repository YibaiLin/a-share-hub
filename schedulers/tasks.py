"""
定时任务定义

定义所有的采集任务
"""

import asyncio
from datetime import datetime
from core.logger import logger
from core.database import get_db_client
from storage.clickhouse_handler import ClickHouseHandler
from collectors.daily import DailyCollector
from utils.date_helper import is_trading_day, get_previous_trading_day, format_date


async def collect_daily_data_task():
    """
    日线数据采集任务

    执行时间: 每个交易日 18:30
    功能: 采集所有股票的日线数据

    说明:
    - 仅在交易日执行
    - 采集当日的日线数据
    - 自动处理失败重试
    """
    task_name = "日线数据采集"
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"🚀 开始执行任务: {task_name}")
    logger.info(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 检查是否为交易日
        today = datetime.now().date()
        if not is_trading_day(today):
            logger.warning(f"今天({today})不是交易日，跳过采集")
            return

        # 获取要采集的日期（前一交易日）
        trade_date = get_previous_trading_day(today)
        trade_date_str = format_date(trade_date, '%Y%m%d')

        logger.info(f"📅 采集日期: {trade_date_str}")

        # 初始化采集器和存储
        collector = DailyCollector()
        client = get_db_client()
        handler = ClickHouseHandler(client)

        # TODO: 这里应该从stock_basic表获取所有股票代码
        # 现在先采集几只测试股票
        test_stocks = ["000001.SZ", "600000.SH", "000002.SZ"]

        success_count = 0
        failed_stocks = []

        for ts_code in test_stocks:
            try:
                logger.info(f"📊 开始采集: {ts_code}")

                # 采集数据
                data = await collector.collect(
                    symbol=ts_code,
                    start_date=trade_date_str,
                    end_date=trade_date_str
                )

                if not data:
                    logger.warning(f"⚠️  {ts_code} 无数据")
                    continue

                # 存储数据
                inserted = handler.insert_daily(
                    ts_code=ts_code,
                    data=data,
                    deduplicate=True
                )

                logger.info(f"✅ {ts_code} 采集完成: 插入{inserted}条记录")
                success_count += 1

            except Exception as e:
                logger.error(f"❌ {ts_code} 采集失败: {e}")
                failed_stocks.append(ts_code)
                continue

        # 汇总结果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info(f"✅ 任务完成: {task_name}")
        logger.info(f"⏱️  耗时: {duration:.2f}秒")
        logger.info(f"📊 成功: {success_count}/{len(test_stocks)}")
        if failed_stocks:
            logger.warning(f"❌ 失败股票: {', '.join(failed_stocks)}")
        logger.info("=" * 60)

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error("=" * 60)
        logger.error(f"❌ 任务失败: {task_name}")
        logger.error(f"⏱️  耗时: {duration:.2f}秒")
        logger.error(f"💥 错误: {e}")
        logger.error("=" * 60)
        raise


async def update_stock_list_task():
    """
    更新股票列表任务

    执行时间: 每日 08:00
    功能: 从AKShare获取最新的股票列表并更新到stock_basic表

    说明:
    - 每日执行一次
    - 获取所有A股股票列表
    - 更新到数据库
    """
    task_name = "股票列表更新"
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"🚀 开始执行任务: {task_name}")
    logger.info(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # TODO: 实现股票列表采集
        # 1. 从AKShare获取股票列表: ak.stock_info_a_code_name()
        # 2. 转换数据格式
        # 3. 存储到stock_basic表

        logger.info("⚠️  股票列表更新功能待实现")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info(f"✅ 任务完成: {task_name}")
        logger.info(f"⏱️  耗时: {duration:.2f}秒")
        logger.info("=" * 60)

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error("=" * 60)
        logger.error(f"❌ 任务失败: {task_name}")
        logger.error(f"⏱️  耗时: {duration:.2f}秒")
        logger.error(f"💥 错误: {e}")
        logger.error("=" * 60)
        raise


# 手动触发任务（用于测试）
async def trigger_daily_collect():
    """
    手动触发日线采集

    用于测试和手动补数据

    Examples:
        ```python
        import asyncio
        from schedulers.tasks import trigger_daily_collect

        asyncio.run(trigger_daily_collect())
        ```
    """
    logger.info("📢 手动触发日线采集任务")
    await collect_daily_data_task()


async def trigger_stock_list_update():
    """
    手动触发股票列表更新

    用于测试和手动更新

    Examples:
        ```python
        import asyncio
        from schedulers.tasks import trigger_stock_list_update

        asyncio.run(trigger_stock_list_update())
        ```
    """
    logger.info("📢 手动触发股票列表更新任务")
    await update_stock_list_task()


__all__ = [
    "collect_daily_data_task",
    "update_stock_list_task",
    "trigger_daily_collect",
    "trigger_stock_list_update",
]
