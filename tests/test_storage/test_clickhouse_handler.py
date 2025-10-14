"""
ClickHouse存储处理器测试
"""

import pytest
from unittest.mock import Mock, MagicMock
from storage.clickhouse_handler import ClickHouseHandler


class TestClickHouseHandler:
    """ClickHouse处理器测试"""

    @pytest.fixture
    def mock_client(self):
        """Mock的ClickHouse客户端"""
        client = Mock()
        client.insert = Mock()
        client.execute = Mock()
        client.query_df = Mock()
        return client

    @pytest.fixture
    def handler(self, mock_client):
        """创建Handler实例"""
        return ClickHouseHandler(client=mock_client)

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return [
            {
                "trade_date": "20240115",
                "open": 1050,
                "high": 1070,
                "low": 1040,
                "close": 1060,
                "pre_close": 1045,
                "change": 15,
                "pct_change": 150,
                "volume": 1000000,
                "amount": 106000000,
            },
            {
                "trade_date": "20240116",
                "open": 1060,
                "high": 1100,
                "low": 1050,
                "close": 1090,
                "pre_close": 1060,
                "change": 30,
                "pct_change": 280,
                "volume": 1200000,
                "amount": 130000000,
            },
        ]

    def test_insert_daily_success(self, handler, mock_client, sample_data):
        """测试成功插入数据"""
        # Mock去重返回全部数据（无重复）
        mock_result = Mock()
        mock_result.result_rows = []
        mock_client.execute.return_value = mock_result

        count = handler.insert_daily("000001.SZ", sample_data, deduplicate=False)

        assert count == 2
        mock_client.insert.assert_called_once()

    def test_insert_daily_empty(self, handler, sample_data):
        """测试插入空数据"""
        count = handler.insert_daily("000001.SZ", [])

        assert count == 0

    def test_insert_daily_with_dedup(self, handler, mock_client, sample_data):
        """测试带去重的插入"""
        # Mock去重查询：第一条已存在
        mock_result = Mock()
        mock_result.result_rows = [("20240115",)]
        mock_client.execute.return_value = mock_result

        count = handler.insert_daily("000001.SZ", sample_data, deduplicate=True)

        # 应该只插入1条（第二条是新的）
        assert count == 1

    def test_query_daily_success(self, handler, mock_client):
        """测试查询数据成功"""
        # Mock查询结果
        mock_result = Mock()
        mock_result.result_rows = [
            (
                "000001.SZ",
                "20240115",
                1050,
                1070,
                1040,
                1060,
                1045,
                15,
                150,
                1000000,
                106000000,
            )
        ]
        mock_client.execute.return_value = mock_result

        data = handler.query_daily("000001.SZ", start_date="20240115")

        assert len(data) == 1
        assert data[0]["ts_code"] == "000001.SZ"
        assert data[0]["close"] == 1060

    def test_query_daily_with_date_range(self, handler, mock_client):
        """测试日期范围查询"""
        mock_result = Mock()
        mock_result.result_rows = []
        mock_client.execute.return_value = mock_result

        handler.query_daily(
            "000001.SZ",
            start_date="20240101",
            end_date="20240131"
        )

        # 验证SQL包含日期范围
        call_args = mock_client.execute.call_args
        sql = call_args[0][0]
        assert "20240101" in sql
        assert "20240131" in sql

    def test_query_daily_with_limit(self, handler, mock_client):
        """测试限制返回数量"""
        mock_result = Mock()
        mock_result.result_rows = []
        mock_client.execute.return_value = mock_result

        handler.query_daily("000001.SZ", limit=10)

        # 验证SQL包含LIMIT
        call_args = mock_client.execute.call_args
        sql = call_args[0][0]
        assert "LIMIT 10" in sql

    def test_delete_daily(self, handler, mock_client):
        """测试删除数据"""
        handler.delete_daily("000001.SZ", start_date="20240101")

        mock_client.execute.assert_called_once()
        call_args = mock_client.execute.call_args
        sql = call_args[0][0]
        assert "DELETE" in sql

    def test_get_latest_date_exists(self, handler, mock_client):
        """测试获取最新日期（有数据）"""
        from datetime import datetime

        mock_result = Mock()
        mock_result.result_rows = [(datetime(2024, 1, 15),)]
        mock_client.execute.return_value = mock_result

        latest_date = handler.get_latest_date("000001.SZ")

        assert latest_date == "20240115"

    def test_get_latest_date_not_exists(self, handler, mock_client):
        """测试获取最新日期（无数据）"""
        mock_result = Mock()
        mock_result.result_rows = [(None,)]
        mock_client.execute.return_value = mock_result

        latest_date = handler.get_latest_date("000001.SZ")

        assert latest_date is None

    def test_batch_insert(self, handler, mock_client):
        """测试批量插入"""
        # 创建大量数据（超过batch_size）
        handler.batch_size = 10
        large_data = []
        for i in range(25):
            large_data.append({
                "trade_date": f"2024011{i % 10}",
                "open": 1000 + i,
                "high": 1010 + i,
                "low": 990 + i,
                "close": 1005 + i,
                "pre_close": 1000,
                "change": i,
                "pct_change": i * 10,
                "volume": 1000000,
                "amount": 100000000,
            })

        # Mock去重返回全部数据
        mock_result = Mock()
        mock_result.result_rows = []
        mock_client.execute.return_value = mock_result

        count = handler.insert_daily("000001.SZ", large_data, deduplicate=False)

        # 应该分3批插入（10 + 10 + 5）
        assert count == 25
        assert mock_client.insert.call_count == 3
