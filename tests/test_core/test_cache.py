"""
Redis缓存连接测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from redis.exceptions import RedisError
from core.cache import RedisClient, get_redis_client, close_redis_client


class TestRedisClient:
    """Redis客户端测试"""

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_connect_success(self, mock_redis_class, mock_pool_class):
        """测试成功连接"""
        # Mock连接池和客户端
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_class.return_value = mock_client

        # 创建并连接
        client = RedisClient()
        await client.connect()

        # 验证连接已建立
        assert client.client is not None
        mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_connect_failure(self, mock_redis_class, mock_pool_class):
        """测试连接失败"""
        # Mock连接池
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        # Mock客户端ping失败
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection failed"))
        mock_redis_class.return_value = mock_client

        # 验证抛出异常
        client = RedisClient()
        with pytest.raises(RedisError, match="Failed to connect"):
            await client.connect()

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_close(self, mock_redis_class, mock_pool_class):
        """测试关闭连接"""
        # Mock连接池和客户端
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.aclose = AsyncMock()
        mock_redis_class.return_value = mock_client

        # 连接并关闭
        client = RedisClient()
        await client.connect()
        await client.close()

        # 验证客户端已关闭
        mock_client.aclose.assert_called_once()
        assert client.client is None

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_ping_success(self, mock_redis_class, mock_pool_class):
        """测试ping成功"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_class.return_value = mock_client

        # 测试ping
        client = RedisClient()
        await client.connect()
        result = await client.ping()

        assert result is True

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_get_set(self, mock_redis_class, mock_pool_class):
        """测试get和set操作"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.set = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value="test_value")
        mock_redis_class.return_value = mock_client

        # 测试set和get
        client = RedisClient()
        await client.connect()

        # 测试set
        result = await client.set("test_key", "test_value", ex=60)
        assert result is True
        mock_client.set.assert_called_once_with("test_key", "test_value", ex=60)

        # 测试get
        value = await client.get("test_key")
        assert value == "test_value"
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_delete(self, mock_redis_class, mock_pool_class):
        """测试删除操作"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.delete = AsyncMock(return_value=2)
        mock_redis_class.return_value = mock_client

        # 测试delete
        client = RedisClient()
        await client.connect()
        count = await client.delete("key1", "key2")

        assert count == 2
        mock_client.delete.assert_called_once_with("key1", "key2")

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_exists(self, mock_redis_class, mock_pool_class):
        """测试exists操作"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.exists = AsyncMock(return_value=1)
        mock_redis_class.return_value = mock_client

        # 测试exists
        client = RedisClient()
        await client.connect()
        count = await client.exists("test_key")

        assert count == 1

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_hash_operations(self, mock_redis_class, mock_pool_class):
        """测试哈希表操作"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.hset = AsyncMock(return_value=1)
        mock_client.hget = AsyncMock(return_value="field_value")
        mock_client.hgetall = AsyncMock(return_value={"field1": "value1"})
        mock_redis_class.return_value = mock_client

        # 测试hash操作
        client = RedisClient()
        await client.connect()

        # hset
        count = await client.hset("test_hash", "field1", "value1")
        assert count == 1

        # hget
        value = await client.hget("test_hash", "field1")
        assert value == "field_value"

        # hgetall
        data = await client.hgetall("test_hash")
        assert data == {"field1": "value1"}

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_context_manager(self, mock_redis_class, mock_pool_class):
        """测试异步上下文管理器"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.aclose = AsyncMock()
        mock_redis_class.return_value = mock_client

        # 使用异步上下文管理器
        async with RedisClient() as client:
            assert client.client is not None

        # 验证连接已关闭
        mock_client.aclose.assert_called_once()


class TestGlobalRedisClient:
    """全局Redis客户端测试"""

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_get_global_client(self, mock_redis_class, mock_pool_class):
        """测试获取全局客户端"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_class.return_value = mock_client

        # 获取全局客户端
        client1 = await get_redis_client()
        client2 = await get_redis_client()

        # 验证返回同一个实例
        assert client1 is client2

        # 清理
        await close_redis_client()

    @pytest.mark.asyncio
    @patch("core.cache.redis.ConnectionPool")
    @patch("core.cache.Redis")
    async def test_close_global_client(self, mock_redis_class, mock_pool_class):
        """测试关闭全局客户端"""
        # Mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.aclose = AsyncMock()
        mock_redis_class.return_value = mock_client

        # 获取并关闭
        await get_redis_client()
        await close_redis_client()

        # 验证关闭被调用
        mock_client.aclose.assert_called_once()
