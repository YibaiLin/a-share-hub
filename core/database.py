"""
ClickHouse数据库连接池

提供ClickHouse连接管理：
- 连接池管理
- 异步查询接口
- 错误处理和重连
- 资源自动清理
"""

from typing import Any, Optional
from contextlib import asynccontextmanager
import clickhouse_connect
from clickhouse_connect.driver import Client
from clickhouse_connect.driver.exceptions import DatabaseError
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings
from core.logger import logger


class ClickHouseClient:
    """ClickHouse客户端类"""

    def __init__(self, database: Optional[str] = None):
        """
        初始化ClickHouse客户端

        Args:
            database: 数据库名称，如果为None则使用配置中的database
        """
        self.client: Optional[Client] = None
        self._config = settings.clickhouse
        self._database = database if database is not None else self._config.database

    def connect(self) -> None:
        """
        建立ClickHouse连接

        Raises:
            DatabaseError: 连接失败时抛出
        """
        try:
            self.client = clickhouse_connect.get_client(
                host=self._config.host,
                port=self._config.port,
                database=self._database,
                username=self._config.user,
                password=self._config.password,
            )
            logger.info(
                f"ClickHouse连接成功: {self._config.host}:{self._config.port}/{self._database}"
            )
        except Exception as e:
            logger.error(f"ClickHouse连接失败: {e}")
            raise DatabaseError(f"Failed to connect to ClickHouse: {e}") from e

    def close(self) -> None:
        """关闭ClickHouse连接"""
        if self.client:
            try:
                self.client.close()
                logger.info("ClickHouse连接已关闭")
            except Exception as e:
                logger.warning(f"关闭ClickHouse连接时出错: {e}")
            finally:
                self.client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def execute(self, query: str, parameters: Optional[dict] = None) -> Any:
        """
        执行SQL查询

        Args:
            query: SQL查询语句
            parameters: 查询参数（可选）

        Returns:
            查询结果

        Raises:
            DatabaseError: 查询执行失败
        """
        if not self.client:
            self.connect()

        try:
            logger.debug(f"执行查询: {query[:100]}...")
            result = self.client.query(query, parameters=parameters)
            return result
        except Exception as e:
            logger.error(f"查询执行失败: {e}, SQL: {query[:100]}")
            raise DatabaseError(f"Query execution failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def insert(
        self,
        table: str,
        data: list[list],
        column_names: Optional[list[str]] = None,
    ) -> None:
        """
        批量插入数据

        Args:
            table: 表名
            data: 数据列表（二维数组）
            column_names: 列名列表（可选）

        Raises:
            DatabaseError: 插入失败
        """
        if not self.client:
            self.connect()

        try:
            logger.debug(f"插入数据到表 {table}, 行数: {len(data)}")
            self.client.insert(table, data, column_names=column_names)
            logger.info(f"成功插入 {len(data)} 行数据到表 {table}")
        except Exception as e:
            logger.error(f"数据插入失败: {e}, 表: {table}")
            raise DatabaseError(f"Insert failed: {e}") from e

    def query_df(self, query: str, parameters: Optional[dict] = None) -> Any:
        """
        执行查询并返回DataFrame

        Args:
            query: SQL查询语句
            parameters: 查询参数（可选）

        Returns:
            pandas.DataFrame

        Raises:
            DatabaseError: 查询执行失败
        """
        if not self.client:
            self.connect()

        try:
            logger.debug(f"执行查询(DataFrame): {query[:100]}...")
            result = self.client.query_df(query, parameters=parameters)
            return result
        except Exception as e:
            logger.error(f"查询执行失败: {e}, SQL: {query[:100]}")
            raise DatabaseError(f"Query execution failed: {e}") from e

    def ping(self) -> bool:
        """
        检查连接是否正常

        Returns:
            bool: 连接正常返回True，否则返回False
        """
        try:
            if not self.client:
                return False
            result = self.client.query("SELECT 1")
            return result.result_rows[0][0] == 1
        except Exception as e:
            logger.warning(f"ClickHouse连接检查失败: {e}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 全局客户端实例
_db_client: Optional[ClickHouseClient] = None


def get_db_client() -> ClickHouseClient:
    """
    获取全局ClickHouse客户端实例

    Returns:
        ClickHouseClient: 数据库客户端实例
    """
    global _db_client
    if _db_client is None:
        _db_client = ClickHouseClient()
        _db_client.connect()
    return _db_client


def close_db_client() -> None:
    """关闭全局ClickHouse客户端"""
    global _db_client
    if _db_client is not None:
        _db_client.close()
        _db_client = None


__all__ = ["ClickHouseClient", "get_db_client", "close_db_client"]
