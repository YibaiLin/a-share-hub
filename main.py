"""
A-Share Hub 主程序入口

用途:
- 启动任务调度器（默认模式）
- 启动API服务器（--api模式）
- 同时启动调度器和API（--all模式）

使用方式:
    python main.py              # 仅启动调度器
    python main.py --api        # 仅启动API服务
    python main.py --all        # 同时启动调度器和API
    python main.py --test       # 手动触发日线采集任务（测试）
"""

import sys
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.logger import setup_logger, logger
from core.database import get_db_client, close_db_client
from config.settings import settings
from schedulers.scheduler import Scheduler
from schedulers.tasks import (
    collect_daily_data_task,
    update_stock_list_task,
    trigger_daily_collect,
)
from apscheduler.triggers.cron import CronTrigger


def start_scheduler():
    """
    启动任务调度器

    注册所有定时任务并启动调度
    """
    scheduler = Scheduler()

    # 注册任务1: 日线数据采集（每个交易日18:30执行）
    scheduler.add_job(
        func=collect_daily_data_task,
        trigger=CronTrigger(hour=18, minute=30),
        job_id="collect_daily_data",
        name="日线数据采集"
    )

    # 注册任务2: 股票列表更新（每日08:00执行）
    scheduler.add_job(
        func=update_stock_list_task,
        trigger=CronTrigger(hour=8, minute=0),
        job_id="update_stock_list",
        name="股票列表更新"
    )

    # 启动调度器
    scheduler.start()

    try:
        # 保持运行（阻塞主线程）
        logger.info("调度器运行中... 按 Ctrl+C 停止")
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("收到停止信号，正在关闭...")
        scheduler.shutdown()


def start_api():
    """
    启动API服务器

    使用uvicorn启动FastAPI应用
    """
    import uvicorn
    logger.info("启动API服务器...")
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
        reload=False,
    )


def start_all():
    """
    同时启动调度器和API服务

    使用多线程运行两个服务
    """
    import threading

    logger.info("启动完整服务（调度器 + API）...")

    # 启动API服务（在新线程中）
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # 启动调度器（在主线程中）
    start_scheduler()


async def test_daily_collect():
    """
    测试模式：手动触发日线采集任务

    用于调试和手动补数据
    """
    logger.info("测试模式：手动触发日线采集")
    await trigger_daily_collect()
    logger.info("测试完成")


def main():
    """
    主函数

    解析命令行参数并启动相应服务
    """
    # 初始化日志
    setup_logger()

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="A-Share Hub - 中国A股数据采集和管理系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py              启动调度器（默认）
  python main.py --api        启动API服务器
  python main.py --all        启动完整服务
  python main.py --test       测试日线采集
        """
    )

    parser.add_argument(
        "--api",
        action="store_true",
        help="仅启动API服务器"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="同时启动调度器和API服务"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="测试模式：手动触发日线采集任务"
    )

    args = parser.parse_args()

    # 显示启动信息
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.app_name} v0.8.0")
    logger.info("=" * 60)

    # 测试数据库连接
    try:
        client = get_db_client()
        if client.ping():
            logger.info("✅ ClickHouse连接正常")
        else:
            logger.warning("⚠️  ClickHouse连接异常")
    except Exception as e:
        logger.error(f"❌ ClickHouse连接失败: {e}")
        sys.exit(1)

    # 根据参数启动相应服务
    try:
        if args.test:
            # 测试模式
            asyncio.run(test_daily_collect())
        elif args.api:
            # 仅启动API
            start_api()
        elif args.all:
            # 启动完整服务
            start_all()
        else:
            # 默认：仅启动调度器
            start_scheduler()

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        raise
    finally:
        # 清理资源
        logger.info("正在清理资源...")
        close_db_client()
        logger.info("✅ 程序已退出")


if __name__ == "__main__":
    main()
