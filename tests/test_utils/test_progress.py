"""
测试进度管理器
"""

import pytest
import json
from pathlib import Path
from utils.progress import ProgressTracker


@pytest.fixture
def temp_progress_file(tmp_path):
    """创建临时进度文件路径"""
    return tmp_path / "test_progress.json"


@pytest.fixture
def tracker(temp_progress_file):
    """创建进度跟踪器实例"""
    return ProgressTracker(str(temp_progress_file))


class TestProgressTracker:
    """测试ProgressTracker类"""

    def test_init_empty_progress(self, tracker):
        """测试初始化空进度"""
        assert tracker.progress_data["total_stocks"] == 0
        assert tracker.progress_data["completed_stocks"] == []
        assert tracker.progress_data["failed_stocks"] == []

    def test_init_progress(self, tracker):
        """测试初始化进度数据"""
        tracker.init_progress("20200101", "20251015", 100)

        assert tracker.progress_data["start_date"] == "20200101"
        assert tracker.progress_data["end_date"] == "20251015"
        assert tracker.progress_data["total_stocks"] == 100
        assert tracker.progress_data["start_time"] != ""

    def test_save_and_load_progress(self, temp_progress_file):
        """测试保存和加载进度"""
        # 创建并保存进度
        tracker1 = ProgressTracker(str(temp_progress_file))
        tracker1.init_progress("20200101", "20251015", 50)
        tracker1.mark_success("000001.SZ", 100)

        # 加载进度
        tracker2 = ProgressTracker(str(temp_progress_file))
        assert tracker2.progress_data["total_stocks"] == 50
        assert "000001.SZ" in tracker2.progress_data["completed_stocks"]
        assert tracker2.progress_data["statistics"]["success"] == 1

    def test_is_completed(self, tracker):
        """测试检查股票是否已完成"""
        tracker.progress_data["completed_stocks"] = ["000001.SZ", "000002.SZ"]

        assert tracker.is_completed("000001.SZ") is True
        assert tracker.is_completed("000003.SZ") is False

    def test_mark_success(self, tracker):
        """测试标记成功"""
        tracker.init_progress("20200101", "20251015", 100)
        tracker.mark_success("000001.SZ", 250)

        assert "000001.SZ" in tracker.progress_data["completed_stocks"]
        assert tracker.progress_data["statistics"]["success"] == 1
        assert tracker.progress_data["statistics"]["total_records"] == 250

    def test_mark_success_removes_from_failed(self, tracker):
        """测试标记成功会从失败列表移除"""
        tracker.progress_data["failed_stocks"] = ["000001.SZ"]
        tracker.mark_success("000001.SZ", 100)

        assert "000001.SZ" not in tracker.progress_data["failed_stocks"]
        assert "000001.SZ" in tracker.progress_data["completed_stocks"]

    def test_mark_failed(self, tracker):
        """测试标记失败"""
        tracker.init_progress("20200101", "20251015", 100)
        tracker.mark_failed("000001.SZ")

        assert "000001.SZ" in tracker.progress_data["failed_stocks"]
        assert tracker.progress_data["statistics"]["failed"] == 1

    def test_mark_failed_removes_from_completed(self, tracker):
        """测试标记失败会从完成列表移除"""
        tracker.progress_data["completed_stocks"] = ["000001.SZ"]
        tracker.mark_failed("000001.SZ")

        assert "000001.SZ" not in tracker.progress_data["completed_stocks"]
        assert "000001.SZ" in tracker.progress_data["failed_stocks"]

    def test_get_remaining_stocks(self, tracker):
        """测试获取待采集股票列表"""
        tracker.progress_data["completed_stocks"] = ["000001.SZ", "000002.SZ"]

        all_stocks = ["000001.SZ", "000002.SZ", "000003.SZ", "600000.SH"]
        remaining = tracker.get_remaining_stocks(all_stocks)

        assert len(remaining) == 2
        assert "000001.SZ" not in remaining
        assert "000003.SZ" in remaining
        assert "600000.SH" in remaining

    def test_get_statistics(self, tracker):
        """测试获取统计信息"""
        tracker.init_progress("20200101", "20251015", 100)
        tracker.mark_success("000001.SZ", 250)
        tracker.mark_success("000002.SZ", 230)
        tracker.mark_failed("600000.SH")

        stats = tracker.get_statistics()

        assert stats["total_stocks"] == 100
        assert stats["completed"] == 2
        assert stats["remaining"] == 98
        assert stats["success"] == 2
        assert stats["failed"] == 1
        assert stats["total_records"] == 480
        assert stats["progress_percent"] == 2.0

    def test_get_failed_stocks(self, tracker):
        """测试获取失败股票列表"""
        tracker.progress_data["failed_stocks"] = ["000001.SZ", "600000.SH"]

        failed = tracker.get_failed_stocks()

        assert len(failed) == 2
        assert "000001.SZ" in failed
        assert "600000.SH" in failed

    def test_clear_progress(self, tracker, temp_progress_file):
        """测试清除进度"""
        tracker.init_progress("20200101", "20251015", 100)
        tracker.mark_success("000001.SZ", 250)

        # 确保文件存在
        assert temp_progress_file.exists()

        # 清除进度
        tracker.clear_progress()

        # 文件应该被删除
        assert not temp_progress_file.exists()
        assert tracker.progress_data["total_stocks"] == 0
        assert tracker.progress_data["completed_stocks"] == []

    def test_has_progress(self, tracker):
        """测试检查是否有进度"""
        # 初始状态：无进度
        assert tracker.has_progress() is False

        # 初始化后：有进度
        tracker.init_progress("20200101", "20251015", 100)
        tracker.mark_success("000001.SZ", 250)
        assert tracker.has_progress() is True

    def test_progress_persistence(self, temp_progress_file):
        """测试进度持久化"""
        # 第一个tracker写入数据
        tracker1 = ProgressTracker(str(temp_progress_file))
        tracker1.init_progress("20200101", "20251015", 100)
        tracker1.mark_success("000001.SZ", 250)
        tracker1.mark_success("000002.SZ", 230)
        tracker1.mark_failed("600000.SH")

        # 第二个tracker读取数据
        tracker2 = ProgressTracker(str(temp_progress_file))

        # 验证数据一致
        assert tracker2.progress_data["start_date"] == "20200101"
        assert tracker2.progress_data["total_stocks"] == 100
        assert len(tracker2.progress_data["completed_stocks"]) == 2
        assert len(tracker2.progress_data["failed_stocks"]) == 1
        assert tracker2.progress_data["statistics"]["success"] == 2
        assert tracker2.progress_data["statistics"]["total_records"] == 480

    def test_print_summary(self, tracker, capsys):
        """测试打印摘要"""
        tracker.init_progress("20200101", "20251015", 100)
        tracker.mark_success("000001.SZ", 250)
        tracker.mark_success("000002.SZ", 230)

        tracker.print_summary()

        # 不直接验证输出，因为使用了logger
        # 只验证方法可以正常调用
        assert True
