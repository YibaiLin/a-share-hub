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
    """
    限流器：控制请求频率，支持智能动态延迟调整

    特性：
    - 基础延迟控制
    - 自适应延迟（失败后增加延迟）
    - 成功后恢复延迟
    """

    def __init__(
        self,
        delay: float = 0.5,
        min_delay: float = 1.0,
        max_delay: float = 5.0,
        adaptive: bool = True
    ):
        """
        初始化限流器

        Args:
            delay: 基础延迟（秒）
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            adaptive: 是否启用自适应延迟
        """
        self.base_delay = delay
        self.current_delay = delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.adaptive = adaptive
        self.last_call = 0.0
        self.consecutive_failures = 0

    async def wait(self) -> None:
        """等待到允许下次请求的时间"""
        elapsed = time.time() - self.last_call
        if elapsed < self.current_delay:
            wait_time = self.current_delay - elapsed
            logger.debug(f"限流等待: {wait_time:.2f}秒 (当前延迟: {self.current_delay:.2f}秒)")
            await asyncio.sleep(wait_time)
        self.last_call = time.time()

    def on_success(self) -> None:
        """
        请求成功回调：重置失败计数，恢复延迟
        """
        if not self.adaptive:
            return

        self.consecutive_failures = 0

        # 逐渐恢复到基础延迟（每次成功减少10%）
        if self.current_delay > self.base_delay:
            self.current_delay = max(
                self.base_delay,
                self.current_delay * 0.9
            )
            logger.debug(f"延迟恢复: {self.current_delay:.2f}秒")

    def on_failure(self) -> None:
        """
        请求失败回调：增加延迟

        策略：
        - 第1次失败：延迟 × 1.5
        - 第2次失败：延迟 × 2.0
        - 第3次及以上：延迟 × 2.5（但不超过max_delay）
        """
        if not self.adaptive:
            return

        self.consecutive_failures += 1

        # 根据连续失败次数调整增长倍数
        if self.consecutive_failures == 1:
            multiplier = 1.5
        elif self.consecutive_failures == 2:
            multiplier = 2.0
        else:
            multiplier = 2.5

        old_delay = self.current_delay
        self.current_delay = min(
            self.max_delay,
            self.current_delay * multiplier
        )

        logger.warning(
            f"连续失败{self.consecutive_failures}次，延迟增加: "
            f"{old_delay:.2f}s → {self.current_delay:.2f}s"
        )

    def reset(self) -> None:
        """重置延迟到基础值"""
        self.current_delay = self.base_delay
        self.consecutive_failures = 0
        logger.info(f"延迟已重置: {self.base_delay:.2f}秒")


class BaseCollector(ABC):
    """
    采集器基类

    所有数据采集器必须继承此类并实现抽象方法
    """

    def __init__(self):
        """初始化采集器"""
        self.rate_limiter = RateLimiter(
            delay=settings.collector_delay,
            min_delay=settings.collector_min_delay,
            max_delay=settings.collector_max_delay,
            adaptive=settings.collector_adaptive_delay
        )
        self.retry_times = settings.collector_retry_times
        logger.info(
            f"初始化采集器: {self.__class__.__name__} "
            f"(延迟: {settings.collector_delay}s, "
            f"自适应: {'开启' if settings.collector_adaptive_delay else '关闭'})"
        )

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
                # 空数据也算成功（股票可能停牌）
                self.rate_limiter.on_success()
                return []

            # 转换数据格式
            logger.debug(f"开始转换数据")
            data = self.transform_data(raw_data)

            # 验证数据
            logger.debug(f"开始验证数据")
            if not self.validate_data(data):
                logger.error(f"数据验证失败: {kwargs}")
                self.rate_limiter.on_failure()
                raise ValueError("Data validation failed")

            logger.info(f"采集成功: 获取 {len(data)} 条数据")
            # 采集成功，通知限流器
            self.rate_limiter.on_success()
            return data

        except Exception as e:
            logger.error(f"采集失败: {e}, 参数: {kwargs}")
            # 采集失败，通知限流器增加延迟
            self.rate_limiter.on_failure()
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
