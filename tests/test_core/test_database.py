"""
ClickHouse数据库连接测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from clickhouse_connect.driver.exceptions import DatabaseError
from core.database import ClickHouseClient, get_db_client, close_db_client


class TestClickHouseClient:
    """ClickHouse客户端测试"""

    @patch("core.database.clickhouse_connect.get_client")
    def test_connect_success(self, mock_get_client):
        """测试成功连接"""
        # Mock客户端
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 创建并连接
        client = ClickHouseClient()
        client.connect()

        # 验证连接已建立
        assert client.client is not None
        mock_get_client.assert_called_once()

    @patch("core.database.clickhouse_connect.get_client")
    def test_connect_failure(self, mock_get_client):
        """测试连接失败"""
        # Mock连接失败
        mock_get_client.side_effect = Exception("Connection failed")

        # 验证抛出异常
        client = ClickHouseClient()
        with pytest.raises(DatabaseError, match="Failed to connect"):
            client.connect()

    @patch("core.database.clickhouse_connect.get_client")
    def test_close(self, mock_get_client):
        """测试关闭连接"""
        # Mock客户端
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 连接并关闭
        client = ClickHouseClient()
        client.connect()
        client.close()

        # 验证客户端已关闭
        mock_client.close.assert_called_once()
        assert client.client is None

    @patch("core.database.clickhouse_connect.get_client")
    def test_execute_query(self, mock_get_client):
        """测试执行查询"""
        # Mock客户端和查询结果
        mock_client = Mock()
        mock_result = Mock()
        mock_result.result_rows = [[1]]
        mock_client.query.return_value = mock_result
        mock_get_client.return_value = mock_client

        # 执行查询
        client = ClickHouseClient()
        client.connect()
        result = client.execute("SELECT 1")

        # 验证查询被调用
        assert result is not None
        mock_client.query.assert_called_once()

    @patch("core.database.clickhouse_connect.get_client")
    def test_execute_with_retry(self, mock_get_client):
        """测试查询重试机制"""
        # Mock客户端
        mock_client = Mock()
        # 第一次失败，第二次成功
        mock_client.query.side_effect = [
            Exception("Temporary error"),
            Mock(result_rows=[[1]]),
        ]
        mock_get_client.return_value = mock_client

        # 执行查询（应该重试成功）
        client = ClickHouseClient()
        client.connect()
        result = client.execute("SELECT 1")

        # 验证重试了2次
        assert result is not None
        assert mock_client.query.call_count == 2

    @patch("core.database.clickhouse_connect.get_client")
    def test_insert_data(self, mock_get_client):
        """测试插入数据"""
        # Mock客户端
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 插入数据
        client = ClickHouseClient()
        client.connect()
        test_data = [[1, "test"], [2, "test2"]]
        client.insert("test_table", test_data, column_names=["id", "name"])

        # 验证插入被调用
        mock_client.insert.assert_called_once_with(
            "test_table",
            test_data,
            column_names=["id", "name"],
        )

    @patch("core.database.clickhouse_connect.get_client")
    def test_ping_success(self, mock_get_client):
        """测试ping成功"""
        # Mock客户端
        mock_client = Mock()
        mock_result = Mock()
        mock_result.result_rows = [[1]]
        mock_client.query.return_value = mock_result
        mock_get_client.return_value = mock_client

        # 测试ping
        client = ClickHouseClient()
        client.connect()
        assert client.ping() is True

    @patch("core.database.clickhouse_connect.get_client")
    def test_ping_failure(self, mock_get_client):
        """测试ping失败"""
        # Mock客户端
        mock_client = Mock()
        mock_client.query.side_effect = Exception("Connection lost")
        mock_get_client.return_value = mock_client

        # 测试ping
        client = ClickHouseClient()
        client.connect()
        assert client.ping() is False

    @patch("core.database.clickhouse_connect.get_client")
    def test_context_manager(self, mock_get_client):
        """测试上下文管理器"""
        # Mock客户端
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 使用上下文管理器
        with ClickHouseClient() as client:
            assert client.client is not None

        # 验证连接已关闭
        mock_client.close.assert_called_once()

    @patch("core.database.clickhouse_connect.get_client")
    def test_query_df(self, mock_get_client):
        """测试查询返回DataFrame"""
        # Mock客户端
        mock_client = Mock()
        mock_df = Mock()
        mock_client.query_df.return_value = mock_df
        mock_get_client.return_value = mock_client

        # 执行查询
        client = ClickHouseClient()
        client.connect()
        result = client.query_df("SELECT * FROM test")

        # 验证
        assert result is not None
        mock_client.query_df.assert_called_once()


class TestGlobalClient:
    """全局客户端测试"""

    @patch("core.database.clickhouse_connect.get_client")
    def test_get_global_client(self, mock_get_client):
        """测试获取全局客户端"""
        # Mock客户端
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 获取全局客户端
        client1 = get_db_client()
        client2 = get_db_client()

        # 验证返回同一个实例
        assert client1 is client2

        # 清理
        close_db_client()

    @patch("core.database.clickhouse_connect.get_client")
    def test_close_global_client(self, mock_get_client):
        """测试关闭全局客户端"""
        # Mock客户端
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 获取并关闭
        get_db_client()
        close_db_client()

        # 验证关闭被调用
        mock_client.close.assert_called_once()
