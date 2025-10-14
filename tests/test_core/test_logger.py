"""
日志系统测试
"""

import sys
from pathlib import Path
from loguru import logger
from core.logger import setup_logger


class TestLogger:
    """日志系统测试"""

    def test_setup_logger(self, tmp_path, monkeypatch):
        """测试日志系统初始化"""
        # 切换到临时目录
        monkeypatch.chdir(tmp_path)

        # 移除现有handlers
        logger.remove()

        # 配置日志
        setup_logger()

        # 验证logs目录被创建
        log_dir = tmp_path / "logs"
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_logger_output(self, tmp_path, monkeypatch, caplog):
        """测试日志输出"""
        import time

        # 切换到临时目录
        monkeypatch.chdir(tmp_path)

        # 移除现有handlers
        logger.remove()

        # 重新配置
        setup_logger()

        # 写入测试日志
        test_message = "Test log message"
        logger.info(test_message)

        # 等待异步日志写入完成
        time.sleep(0.5)

        # 验证日志文件被创建
        log_dir = tmp_path / "logs"
        log_files = list(log_dir.glob("app_*.log"))
        assert len(log_files) > 0

        # 验证日志内容
        log_content = log_files[0].read_text(encoding="utf-8")
        assert test_message in log_content

    def test_logger_levels(self, tmp_path, monkeypatch):
        """测试不同日志级别"""
        import time

        # 切换到临时目录
        monkeypatch.chdir(tmp_path)

        # 移除现有handlers
        logger.remove()

        # 重新配置
        setup_logger()

        # 写入不同级别的日志
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # 等待异步日志写入完成
        time.sleep(0.5)

        # 验证普通日志文件
        log_dir = tmp_path / "logs"
        app_logs = list(log_dir.glob("app_*.log"))
        assert len(app_logs) > 0
        app_log_content = app_logs[0].read_text(encoding="utf-8")

        # INFO级别及以上应该被记录
        assert "Info message" in app_log_content
        assert "Warning message" in app_log_content
        assert "Error message" in app_log_content

        # 验证错误日志文件
        error_logs = list(log_dir.glob("error_*.log"))
        assert len(error_logs) > 0
        error_log_content = error_logs[0].read_text(encoding="utf-8")

        # 只有ERROR级别被记录
        assert "Error message" in error_log_content
        assert "Info message" not in error_log_content

    def test_logger_format(self, tmp_path, monkeypatch):
        """测试日志格式"""
        import time
        import re

        # 切换到临时目录
        monkeypatch.chdir(tmp_path)

        # 移除现有handlers
        logger.remove()

        # 重新配置
        setup_logger()

        # 写入日志
        logger.info("Format test")

        # 等待异步日志写入完成
        time.sleep(0.5)

        # 读取日志文件
        log_dir = tmp_path / "logs"
        log_files = list(log_dir.glob("app_*.log"))
        log_content = log_files[0].read_text(encoding="utf-8")

        # 验证日志格式包含必要元素
        assert "INFO" in log_content
        assert "Format test" in log_content
        # 日志应包含时间戳（YYYY-MM-DD格式）
        assert re.search(r"\d{4}-\d{2}-\d{2}", log_content) is not None
