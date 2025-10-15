"""
失败监控器：监控连续失败并触发暂停

用途：
- 检测连续失败的次数
- 达到阈值时触发暂停
- 支持暂停冷却恢复
"""

import time
from core.logger import logger


class FailureMonitor:
    """
    失败监控器

    特性：
    - 监控连续失败次数
    - 达到阈值时触发暂停
    - 支持冷却时间后自动恢复
    - 成功时重置计数
    """

    def __init__(
        self,
        threshold: int = 10,
        pause_duration: int = 60,
        enable: bool = True
    ):
        """
        初始化失败监控器

        Args:
            threshold: 连续失败阈值（次）
            pause_duration: 暂停时长（秒）
            enable: 是否启用监控
        """
        self.threshold = threshold
        self.pause_duration = pause_duration
        self.enable = enable
        self.consecutive_failures = 0
        self.total_failures = 0
        self.pause_until = 0.0
        self.pause_count = 0

    def on_success(self) -> None:
        """
        记录成功：重置连续失败计数
        """
        if not self.enable:
            return

        if self.consecutive_failures > 0:
            logger.info(f"采集成功，重置失败计数（之前连续失败{self.consecutive_failures}次）")
            self.consecutive_failures = 0

    def on_failure(self, error_msg: str = "") -> None:
        """
        记录失败：增加失败计数，检查是否需要暂停

        Args:
            error_msg: 错误消息
        """
        if not self.enable:
            return

        self.consecutive_failures += 1
        self.total_failures += 1

        logger.warning(
            f"采集失败（连续{self.consecutive_failures}次，总计{self.total_failures}次）"
            f"{': ' + error_msg if error_msg else ''}"
        )

        # 检查是否达到阈值
        if self.consecutive_failures >= self.threshold:
            self._trigger_pause()

    def _trigger_pause(self) -> None:
        """触发暂停"""
        self.pause_until = time.time() + self.pause_duration
        self.pause_count += 1

        logger.error(
            f"⚠️  连续失败{self.consecutive_failures}次，达到阈值{self.threshold}！"
            f"\n暂停{self.pause_duration}秒以避免API封禁..."
            f"\n（这是第{self.pause_count}次暂停）"
        )

    def should_pause(self) -> bool:
        """
        检查是否应该暂停

        Returns:
            True表示需要暂停，False表示可以继续
        """
        if not self.enable:
            return False

        if time.time() < self.pause_until:
            return True

        return False

    def get_remaining_pause_time(self) -> float:
        """
        获取剩余暂停时间

        Returns:
            剩余暂停秒数，0表示未暂停
        """
        if not self.enable:
            return 0.0

        remaining = self.pause_until - time.time()
        return max(0.0, remaining)

    def wait_if_paused(self) -> None:
        """
        如果正在暂停，则等待到暂停结束

        注意：这是同步阻塞方法
        """
        if not self.enable:
            return

        remaining = self.get_remaining_pause_time()
        if remaining > 0:
            logger.warning(f"等待暂停结束，剩余{remaining:.1f}秒...")
            time.sleep(remaining)
            logger.info("暂停结束，恢复采集")
            # 暂停后重置连续失败计数（给一次机会）
            self.consecutive_failures = 0

    def reset(self) -> None:
        """重置监控器状态（但保留总失败数）"""
        self.consecutive_failures = 0
        self.pause_until = 0.0
        logger.info("失败监控器已重置")

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            包含统计信息的字典
        """
        return {
            "consecutive_failures": self.consecutive_failures,
            "total_failures": self.total_failures,
            "pause_count": self.pause_count,
            "is_paused": self.should_pause(),
            "remaining_pause_time": self.get_remaining_pause_time(),
        }

    def __str__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return (
            f"FailureMonitor("
            f"consecutive={stats['consecutive_failures']}, "
            f"total={stats['total_failures']}, "
            f"paused={stats['is_paused']}, "
            f"pause_count={stats['pause_count']})"
        )


__all__ = ["FailureMonitor"]
