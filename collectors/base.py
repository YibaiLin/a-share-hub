"""
基础采集器抽象类

提供所有采集器的通用功能：
- 限流机制（防止API频繁请求）
- 重试机制（网络异常自动重试）
- 日志记录
- 抽象方法定义
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Optional
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from core.logger import logger
from config.settings import settings


class RateLimiter:
    """限流器：控制请求频率"""

    def __init__(self, delay: float = 0.5):
        """
        初始化限流器

        Args:
            delay: 每次请求之间的延迟（秒）
        """
        self.delay = delay
        self.last_call = 0.0

    async def wait(self) -> None:
        """等待到允许下次请求的时间"""
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            wait_time = self.delay - elapsed
            logger.debug(f"限流等待: {wait_time:.2f}秒")
            await asyncio.sleep(wait_time)
        self.last_call = time.time()


class BaseCollector(ABC):
    """
    采集器基类

    所有数据采集器必须继承此类并实现抽象方法
    """

    def __init__(self):
        """初始化采集器"""
        self.rate_limiter = RateLimiter(delay=settings.collector_delay)
        self.retry_times = settings.collector_retry_times
        logger.info(f"初始化采集器: {self.__class__.__name__}")

    @abstractmethod
    async def fetch_data(self, **kwargs) -> Any:
        """
        获取原始数据（抽象方法）

        Args:
            **kwargs: 查询参数

        Returns:
            原始数据（具体格式由子类定义）

        Raises:
            Exception: 数据获取失败
        """
        pass

    @abstractmethod
    def transform_data(self, raw_data: Any) -> list[dict]:
        """
        转换数据格式（抽象方法）

        Args:
            raw_data: 原始数据

        Returns:
            转换后的数据列表

        Raises:
            Exception: 数据转换失败
        """
        pass

    @abstractmethod
    def validate_data(self, data: list[dict]) -> bool:
        """
        验证数据有效性（抽象方法）

        Args:
            data: 待验证的数据

        Returns:
            True表示数据有效，False表示无效

        Raises:
            Exception: 验证过程出错
        """
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def collect(self, **kwargs) -> list[dict]:
        """
        执行完整的数据采集流程

        包括：限流 → 获取 → 转换 → 验证

        Args:
            **kwargs: 查询参数

        Returns:
            处理后的数据列表

        Raises:
            Exception: 采集过程中的任何错误
        """
        try:
            # 限流等待
            await self.rate_limiter.wait()

            # 获取原始数据
            logger.debug(f"开始获取数据: {kwargs}")
            raw_data = await self.fetch_data(**kwargs)

            if raw_data is None or (hasattr(raw_data, '__len__') and len(raw_data) == 0):
                logger.warning(f"未获取到数据: {kwargs}")
                return []

            # 转换数据格式
            logger.debug(f"开始转换数据")
            data = self.transform_data(raw_data)

            # 验证数据
            logger.debug(f"开始验证数据")
            if not self.validate_data(data):
                logger.error(f"数据验证失败: {kwargs}")
                raise ValueError("Data validation failed")

            logger.info(f"采集成功: 获取 {len(data)} 条数据")
            return data

        except Exception as e:
            logger.error(f"采集失败: {e}, 参数: {kwargs}")
            raise

    async def batch_collect(self, params_list: list[dict]) -> list[dict]:
        """
        批量采集数据

        Args:
            params_list: 参数列表，每个元素是一个查询参数字典

        Returns:
            所有采集到的数据合并后的列表

        Raises:
            Exception: 批量采集过程中的错误
        """
        all_data = []

        for params in params_list:
            try:
                data = await self.collect(**params)
                all_data.extend(data)
            except Exception as e:
                logger.error(f"批量采集失败: {e}, 参数: {params}")
                # 继续处理下一个，不中断整个批量任务
                continue

        logger.info(f"批量采集完成: 共 {len(all_data)} 条数据")
        return all_data


__all__ = ["BaseCollector", "RateLimiter"]
