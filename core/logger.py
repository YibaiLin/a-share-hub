"""
日志系统

使用loguru配置应用日志，支持：
- 控制台和文件双输出
- 日志级别配置
- 日志文件轮转（按日期）
- 结构化日志格式
"""

import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger() -> None:
    """
    配置应用日志系统

    - 移除默认handler
    - 添加控制台输出（彩色格式）
    - 添加文件输出（JSON格式，按日期轮转）
    """
    # 移除默认handler
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
    )

    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 添加文件输出 - INFO级别及以上
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        encoding="utf-8",
        enqueue=True,  # 异步写入
    )

    # 添加错误日志文件 - ERROR级别及以上
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",
        retention="90 days",  # 错误日志保留更久
        encoding="utf-8",
        enqueue=True,
    )

    logger.info(f"日志系统初始化完成，日志级别: {settings.log_level}")


# 导出logger实例
__all__ = ["logger", "setup_logger"]
