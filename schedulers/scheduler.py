"""
任务调度器

使用APScheduler实现定时任务调度
"""

import signal
import sys
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from core.logger import logger
from config.settings import settings


class Scheduler:
    """
    任务调度器

    功能:
    - 管理定时任务
    - 处理优雅关闭
    - 记录任务执行日志

    Examples:
        ```python
        scheduler = Scheduler()

        # 添加定时任务
        scheduler.add_job(
            func=my_task,
            trigger=CronTrigger(hour=18, minute=30),
            job_id="daily_collect",
            name="日线数据采集"
        )

        # 启动调度器
        await scheduler.start()

        # 停止调度器
        await scheduler.shutdown()
        ```
    """

    def __init__(self):
        """初始化调度器"""
        self.scheduler = AsyncIOScheduler(
            timezone=settings.app_timezone,
            job_defaults={
                'coalesce': True,  # 合并错过的任务
                'max_instances': 1,  # 同一任务最多同时运行1个实例
                'misfire_grace_time': 300,  # 错过执行时间5分钟内仍执行
            }
        )

        # 添加事件监听
        self.scheduler.add_listener(
            self._job_executed,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error,
            EVENT_JOB_ERROR
        )

        # 注册信号处理
        self._register_signals()

        logger.info("调度器初始化完成")

    def _register_signals(self):
        """
        注册信号处理器

        处理SIGTERM和SIGINT信号，实现优雅关闭
        """
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备关闭调度器...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def _job_executed(self, event):
        """
        任务执行完成事件处理

        Args:
            event: 任务执行事件
        """
        job_id = event.job_id
        logger.info(f"✅ 任务执行成功: {job_id}")

    def _job_error(self, event):
        """
        任务执行错误事件处理

        Args:
            event: 任务错误事件
        """
        job_id = event.job_id
        exception = event.exception
        logger.error(f"❌ 任务执行失败: {job_id}, 错误: {exception}")

    def add_job(self, func, trigger, job_id: str, name: str, **kwargs):
        """
        添加定时任务

        Args:
            func: 任务函数
            trigger: 触发器(CronTrigger, IntervalTrigger等)
            job_id: 任务唯一标识
            name: 任务名称
            **kwargs: 其他参数传递给APScheduler

        Examples:
            ```python
            # Cron触发器（每天18:30执行）
            scheduler.add_job(
                func=collect_daily_data,
                trigger=CronTrigger(hour=18, minute=30),
                job_id="daily_collect",
                name="日线数据采集"
            )

            # 间隔触发器（每5分钟执行一次）
            from apscheduler.triggers.interval import IntervalTrigger
            scheduler.add_job(
                func=collect_minute_data,
                trigger=IntervalTrigger(minutes=5),
                job_id="minute_collect",
                name="分钟线数据采集"
            )
            ```
        """
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True,
            **kwargs
        )
        logger.info(f"添加任务: {name} (id={job_id})")

    def remove_job(self, job_id: str):
        """
        移除任务

        Args:
            job_id: 任务ID
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"移除任务: {job_id}")
        except Exception as e:
            logger.error(f"移除任务失败: {job_id}, 错误: {e}")

    def get_jobs(self) -> list:
        """
        获取所有任务

        Returns:
            任务列表
        """
        return self.scheduler.get_jobs()

    def start(self):
        """
        启动调度器

        启动后会按照配置的触发器执行任务
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("=" * 60)
            logger.info("⏰ 调度器启动成功")
            logger.info(f"📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"🌍 时区: {settings.app_timezone}")

            # 显示所有任务
            jobs = self.get_jobs()
            if jobs:
                logger.info(f"📋 已注册 {len(jobs)} 个任务:")
                for job in jobs:
                    next_run = job.next_run_time
                    next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "未定义"
                    logger.info(f"  - {job.name} ({job.id}): 下次执行时间 {next_run_str}")
            else:
                logger.warning("⚠️  没有已注册的任务")

            logger.info("=" * 60)
        else:
            logger.warning("调度器已在运行")

    def shutdown(self, wait: bool = True):
        """
        关闭调度器

        Args:
            wait: 是否等待正在执行的任务完成
        """
        if self.scheduler.running:
            logger.info("正在关闭调度器...")
            self.scheduler.shutdown(wait=wait)
            logger.info("✅ 调度器已关闭")
        else:
            logger.warning("调度器未在运行")

    def is_running(self) -> bool:
        """
        检查调度器是否正在运行

        Returns:
            True表示运行中
        """
        return self.scheduler.running

    def pause(self):
        """暂停调度器（不执行任务）"""
        if self.scheduler.running:
            self.scheduler.pause()
            logger.info("调度器已暂停")

    def resume(self):
        """恢复调度器"""
        if self.scheduler.running:
            self.scheduler.resume()
            logger.info("调度器已恢复")


__all__ = ["Scheduler"]
