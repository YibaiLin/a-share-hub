"""
失败监控器测试
"""

import pytest
import time
from utils.failure_monitor import FailureMonitor


class TestFailureMonitor:
    """失败监控器测试"""

    def test_init(self):
        """测试初始化"""
        monitor = FailureMonitor(threshold=5, pause_duration=30, enable=True)

        assert monitor.threshold == 5
        assert monitor.pause_duration == 30
        assert monitor.enable is True
        assert monitor.consecutive_failures == 0
        assert monitor.total_failures == 0
        assert monitor.pause_count == 0

    def test_on_success_resets_consecutive_failures(self):
        """测试成功重置连续失败计数"""
        monitor = FailureMonitor(threshold=3)

        # 模拟失败
        monitor.on_failure()
        monitor.on_failure()
        assert monitor.consecutive_failures == 2
        assert monitor.total_failures == 2

        # 成功后重置连续失败
        monitor.on_success()
        assert monitor.consecutive_failures == 0
        assert monitor.total_failures == 2  # 总失败数不变

    def test_on_failure_increments_counters(self):
        """测试失败增加计数"""
        monitor = FailureMonitor(threshold=10)

        monitor.on_failure()
        assert monitor.consecutive_failures == 1
        assert monitor.total_failures == 1

        monitor.on_failure("Network error")
        assert monitor.consecutive_failures == 2
        assert monitor.total_failures == 2

    def test_trigger_pause_on_threshold(self):
        """测试达到阈值触发暂停"""
        monitor = FailureMonitor(threshold=3, pause_duration=1)

        # 前2次失败不暂停
        monitor.on_failure()
        monitor.on_failure()
        assert monitor.should_pause() is False
        assert monitor.pause_count == 0

        # 第3次失败触发暂停
        monitor.on_failure()
        assert monitor.should_pause() is True
        assert monitor.pause_count == 1

    def test_pause_duration(self):
        """测试暂停时长"""
        monitor = FailureMonitor(threshold=2, pause_duration=0.5)

        # 触发暂停
        monitor.on_failure()
        monitor.on_failure()

        # 立即检查：应该在暂停中
        assert monitor.should_pause() is True
        remaining = monitor.get_remaining_pause_time()
        assert 0.4 < remaining <= 0.5

        # 等待暂停结束
        time.sleep(0.6)
        assert monitor.should_pause() is False
        assert monitor.get_remaining_pause_time() == 0.0

    def test_wait_if_paused(self):
        """测试暂停等待"""
        monitor = FailureMonitor(threshold=1, pause_duration=0.3)

        # 触发暂停
        monitor.on_failure()
        assert monitor.consecutive_failures == 1

        # 等待暂停结束
        start = time.time()
        monitor.wait_if_paused()
        elapsed = time.time() - start

        # 应该等待约0.3秒
        assert 0.25 < elapsed < 0.4
        # 暂停后连续失败计数应该重置
        assert monitor.consecutive_failures == 0
        assert monitor.total_failures == 1  # 总失败数不变

    def test_multiple_pauses(self):
        """测试多次暂停"""
        monitor = FailureMonitor(threshold=2, pause_duration=0.2)

        # 第一次暂停
        monitor.on_failure()
        monitor.on_failure()
        assert monitor.pause_count == 1

        # 等待暂停结束
        monitor.wait_if_paused()

        # 再次触发暂停
        monitor.on_failure()
        monitor.on_failure()
        assert monitor.pause_count == 2

    def test_disabled_monitor(self):
        """测试禁用监控器"""
        monitor = FailureMonitor(threshold=2, enable=False)

        # 失败不会触发任何操作
        monitor.on_failure()
        monitor.on_failure()
        monitor.on_failure()

        assert monitor.consecutive_failures == 0
        assert monitor.total_failures == 0
        assert monitor.should_pause() is False
        assert monitor.pause_count == 0

    def test_reset(self):
        """测试重置"""
        monitor = FailureMonitor(threshold=5)

        # 模拟失败和暂停
        for _ in range(5):
            monitor.on_failure()

        assert monitor.consecutive_failures == 5
        assert monitor.total_failures == 5
        assert monitor.should_pause() is True

        # 重置（保留总失败数）
        monitor.reset()
        assert monitor.consecutive_failures == 0
        assert monitor.total_failures == 5  # 总失败数保留
        assert monitor.should_pause() is False

    def test_get_stats(self):
        """测试获取统计信息"""
        monitor = FailureMonitor(threshold=3, pause_duration=1)

        # 触发暂停
        monitor.on_failure()
        monitor.on_failure()
        monitor.on_failure()

        stats = monitor.get_stats()
        assert stats["consecutive_failures"] == 3
        assert stats["total_failures"] == 3
        assert stats["pause_count"] == 1
        assert stats["is_paused"] is True
        assert 0 < stats["remaining_pause_time"] <= 1

    def test_str_representation(self):
        """测试字符串表示"""
        monitor = FailureMonitor(threshold=3)
        monitor.on_failure()

        str_repr = str(monitor)
        assert "FailureMonitor" in str_repr
        assert "consecutive=1" in str_repr
        assert "total=1" in str_repr

    def test_success_after_pause(self):
        """测试暂停后成功"""
        monitor = FailureMonitor(threshold=2, pause_duration=0.2)

        # 触发暂停
        monitor.on_failure()
        monitor.on_failure()
        assert monitor.should_pause() is True

        # 等待暂停结束
        monitor.wait_if_paused()
        assert monitor.consecutive_failures == 0

        # 成功采集
        monitor.on_success()
        assert monitor.consecutive_failures == 0
        assert monitor.total_failures == 2
