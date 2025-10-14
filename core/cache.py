"""
Redis缓存连接池

提供Redis连接管理：
- 异步连接池
- 基础缓存操作
- 错误处理
- 资源自动清理
"""

from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError
from config.settings import settings
from core.logger import logger


class RedisClient:
    """Redis客户端类"""

    def __init__(self):
        """初始化Redis客户端"""
        self.client: Optional[Redis] = None
        self._config = settings.redis

    async def connect(self) -> None:
        """
        建立Redis连接

        Raises:
            RedisError: 连接失败时抛出
        """
        try:
            # 创建连接池
            pool = redis.ConnectionPool(
                host=self._config.host,
                port=self._config.port,
                db=self._config.db,
                password=self._config.password if self._config.password else None,
                decode_responses=True,
                max_connections=10,
            )
            self.client = Redis(connection_pool=pool)

            # 测试连接
            await self.client.ping()

            logger.info(
                f"Redis连接成功: {self._config.host}:{self._config.port}/{self._config.db}"
            )
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise RedisError(f"Failed to connect to Redis: {e}") from e

    async def close(self) -> None:
        """关闭Redis连接"""
        if self.client:
            try:
                await self.client.aclose()
                logger.info("Redis连接已关闭")
            except Exception as e:
                logger.warning(f"关闭Redis连接时出错: {e}")
            finally:
                self.client = None

    async def ping(self) -> bool:
        """
        检查连接是否正常

        Returns:
            bool: 连接正常返回True，否则返回False
        """
        try:
            if not self.client:
                return False
            return await self.client.ping()
        except Exception as e:
            logger.warning(f"Redis连接检查失败: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        if not self.client:
            await self.connect()

        try:
            value = await self.client.get(key)
            return value
        except Exception as e:
            logger.error(f"获取缓存失败: {e}, key: {key}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ex: 过期时间（秒），None表示永不过期

        Returns:
            bool: 设置成功返回True
        """
        if not self.client:
            await self.connect()

        try:
            await self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}, key: {key}")
            return False

    async def delete(self, *keys: str) -> int:
        """
        删除缓存

        Args:
            keys: 要删除的键

        Returns:
            int: 删除的键数量
        """
        if not self.client:
            await self.connect()

        try:
            count = await self.client.delete(*keys)
            return count
        except Exception as e:
            logger.error(f"删除缓存失败: {e}, keys: {keys}")
            return 0

    async def exists(self, *keys: str) -> int:
        """
        检查键是否存在

        Args:
            keys: 要检查的键

        Returns:
            int: 存在的键数量
        """
        if not self.client:
            await self.connect()

        try:
            count = await self.client.exists(*keys)
            return count
        except Exception as e:
            logger.error(f"检查键存在失败: {e}, keys: {keys}")
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间

        Args:
            key: 缓存键
            seconds: 过期时间（秒）

        Returns:
            bool: 设置成功返回True
        """
        if not self.client:
            await self.connect()

        try:
            result = await self.client.expire(key, seconds)
            return result
        except Exception as e:
            logger.error(f"设置过期时间失败: {e}, key: {key}")
            return False

    async def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        mapping: Optional[dict] = None,
    ) -> int:
        """
        设置哈希表字段值

        Args:
            name: 哈希表名
            key: 字段名
            value: 字段值
            mapping: 字段映射字典

        Returns:
            int: 新增字段数量
        """
        if not self.client:
            await self.connect()

        try:
            count = await self.client.hset(name, key, value, mapping)
            return count
        except Exception as e:
            logger.error(f"设置哈希表失败: {e}, name: {name}")
            return 0

    async def hget(self, name: str, key: str) -> Optional[str]:
        """
        获取哈希表字段值

        Args:
            name: 哈希表名
            key: 字段名

        Returns:
            字段值，不存在返回None
        """
        if not self.client:
            await self.connect()

        try:
            value = await self.client.hget(name, key)
            return value
        except Exception as e:
            logger.error(f"获取哈希表字段失败: {e}, name: {name}, key: {key}")
            return None

    async def hgetall(self, name: str) -> dict:
        """
        获取哈希表所有字段

        Args:
            name: 哈希表名

        Returns:
            dict: 字段映射字典
        """
        if not self.client:
            await self.connect()

        try:
            data = await self.client.hgetall(name)
            return data
        except Exception as e:
            logger.error(f"获取哈希表失败: {e}, name: {name}")
            return {}

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 全局客户端实例
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """
    获取全局Redis客户端实例

    Returns:
        RedisClient: Redis客户端实例
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    return _redis_client


async def close_redis_client() -> None:
    """关闭全局Redis客户端"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


__all__ = ["RedisClient", "get_redis_client", "close_redis_client"]
