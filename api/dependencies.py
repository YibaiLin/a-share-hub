"""
API依赖注入

提供数据库连接、配置等依赖
"""

from typing import Generator
from core.database import ClickHouseClient, get_db_client
from storage.clickhouse_handler import ClickHouseHandler
from config.settings import settings


def get_settings():
    """获取配置"""
    return settings


def get_db_handler() -> Generator[ClickHouseHandler, None, None]:
    """
    获取数据库Handler

    Yields:
        ClickHouseHandler: 数据库处理器

    Examples:
        ```python
        @app.get("/data")
        def get_data(handler: ClickHouseHandler = Depends(get_db_handler)):
            return handler.query_daily("000001.SZ")
        ```
    """
    client = get_db_client()
    handler = ClickHouseHandler(client=client)
    try:
        yield handler
    finally:
        # 不需要关闭，使用全局客户端
        pass


__all__ = ["get_settings", "get_db_handler"]
