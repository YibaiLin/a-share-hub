"""
日线采集器测试
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from collectors.daily import DailyCollector


class TestDailyCollector:
    """日线采集器测试"""

    @pytest.fixture
    def mock_akshare_data(self):
        """Mock的AKShare返回数据"""
        return pd.DataFrame({
            "日期": ["2024-01-15", "2024-01-16"],
            "开盘": [10.5, 10.8],
            "收盘": [10.6, 10.9],
            "最高": [10.7, 11.0],
            "最低": [10.4, 10.7],
            "成交量": [1000000, 1200000],
            "成交额": [106000000, 130000000],
            "涨跌幅": [1.5, 2.8],
        })

    @pytest.mark.asyncio
    @patch('collectors.daily.ak.stock_zh_a_hist')
    async def test_fetch_data_success(self, mock_ak, mock_akshare_data):
        """测试成功获取数据"""
        mock_ak.return_value = mock_akshare_data

        collector = DailyCollector()
        data = await collector.fetch_data(
            symbol="000001",
            start_date="20240115",
            end_date="20240116"
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 2
        mock_ak.assert_called_once()

    @pytest.mark.asyncio
    @patch('collectors.daily.ak.stock_zh_a_hist')
    async def test_fetch_data_with_suffix(self, mock_ak, mock_akshare_data):
        """测试带后缀的股票代码"""
        mock_ak.return_value = mock_akshare_data

        collector = DailyCollector()
        await collector.fetch_data(symbol="000001.SZ")

        # 应该去掉后缀
        call_args = mock_ak.call_args
        assert call_args.kwargs['symbol'] == "000001"

    @pytest.mark.asyncio
    @patch('collectors.daily.ak.stock_zh_a_hist')
    async def test_fetch_data_empty(self, mock_ak):
        """测试空数据"""
        mock_ak.return_value = pd.DataFrame()

        collector = DailyCollector()
        data = await collector.fetch_data(symbol="000001")

        assert data.empty

    def test_transform_data_success(self, mock_akshare_data):
        """测试数据转换成功"""
        collector = DailyCollector()
        result = collector.transform_data(mock_akshare_data)

        assert len(result) == 2
        assert result[0]["trade_date"] == "20240115"
        assert result[0]["open"] == 1050  # 10.5 * 100
        assert result[0]["close"] == 1060
        assert result[0]["pct_change"] == 150  # 1.5 * 100

    def test_transform_data_empty(self):
        """测试空DataFrame转换"""
        collector = DailyCollector()
        result = collector.transform_data(pd.DataFrame())

        assert result == []

    def test_validate_data_success(self):
        """测试有效数据验证"""
        collector = DailyCollector()

        data = [
            {
                "trade_date": "20240115",
                "open": 1050,
                "high": 1070,
                "low": 1040,
                "close": 1060,
                "volume": 1000000,
                "amount": 106000000,
                "pct_change": 150,
            }
        ]

        assert collector.validate_data(data) is True

    def test_validate_data_empty(self):
        """测试空数据验证"""
        collector = DailyCollector()
        assert collector.validate_data([]) is True

    def test_validate_data_missing_field(self):
        """测试缺少字段"""
        collector = DailyCollector()

        data = [
            {
                "trade_date": "20240115",
                "open": 1050,
                # 缺少其他字段
            }
        ]

        assert collector.validate_data(data) is False

    def test_validate_data_invalid_price(self):
        """测试无效价格"""
        collector = DailyCollector()

        data = [
            {
                "trade_date": "20240115",
                "open": -100,  # 无效价格（小于-1）
                "high": 1070,
                "low": 1040,
                "close": 1060,
                "volume": 1000000,
                "amount": 106000000,
                "pct_change": 150,
            }
        ]

        assert collector.validate_data(data) is False

    def test_validate_data_high_low_inconsistent(self):
        """测试最高价低于最低价"""
        collector = DailyCollector()

        data = [
            {
                "trade_date": "20240115",
                "open": 1050,
                "high": 1040,  # 最高价
                "low": 1070,   # 最低价
                "close": 1060,
                "volume": 1000000,
                "amount": 106000000,
                "pct_change": 150,
            }
        ]

        assert collector.validate_data(data) is False

    @pytest.mark.asyncio
    @patch('collectors.daily.ak.stock_zh_a_hist')
    async def test_collect_full_process(self, mock_ak, mock_akshare_data):
        """测试完整采集流程"""
        mock_ak.return_value = mock_akshare_data

        collector = DailyCollector()
        data = await collector.collect(symbol="000001")

        assert len(data) == 2
        assert data[0]["open"] == 1050
        assert data[1]["close"] == 1090
