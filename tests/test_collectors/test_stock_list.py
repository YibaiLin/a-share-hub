"""
测试股票列表采集器
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from collectors.stock_list import StockListCollector


@pytest.fixture
def collector():
    """创建采集器实例"""
    return StockListCollector()


@pytest.fixture
def mock_stock_data():
    """模拟AKShare返回的股票列表数据"""
    return pd.DataFrame({
        "code": ["000001", "000002", "600000", "688001", "430001"],
        "name": ["平安银行", "万科A", "浦发银行", "科创板1", "北交所1"]
    })


class TestStockListCollector:
    """测试StockListCollector类"""

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, collector, mock_stock_data):
        """测试成功获取股票列表"""
        with patch("akshare.stock_info_a_code_name", return_value=mock_stock_data):
            result = await collector.fetch_data()

            assert not result.empty
            assert len(result) == 5
            assert "code" in result.columns
            assert "name" in result.columns

    @pytest.mark.asyncio
    async def test_fetch_data_empty(self, collector):
        """测试获取空列表"""
        with patch("akshare.stock_info_a_code_name", return_value=pd.DataFrame()):
            result = await collector.fetch_data()

            assert result.empty

    @pytest.mark.asyncio
    async def test_fetch_data_failure(self, collector):
        """测试获取失败"""
        with patch("akshare.stock_info_a_code_name", side_effect=Exception("API错误")):
            with pytest.raises(Exception, match="API错误"):
                await collector.fetch_data()

    def test_transform_data_success(self, collector, mock_stock_data):
        """测试数据转换"""
        result = collector.transform_data(mock_stock_data)

        assert len(result) == 5
        assert result[0] == {
            "ts_code": "000001.SZ",
            "name": "平安银行",
            "code": "000001"
        }
        assert result[2]["ts_code"] == "600000.SH"  # 上海
        assert result[3]["ts_code"] == "688001.SH"  # 科创板
        assert result[4]["ts_code"] == "430001.BJ"  # 北交所

    def test_transform_data_empty(self, collector):
        """测试空数据转换"""
        result = collector.transform_data(pd.DataFrame())
        assert result == []

    def test_validate_data_success(self, collector):
        """测试验证有效数据"""
        data = [
            {"ts_code": "000001.SZ", "name": "平安银行"},
            {"ts_code": "600000.SH", "name": "浦发银行"}
        ]

        assert collector.validate_data(data) is True

    def test_validate_data_empty(self, collector):
        """测试验证空数据"""
        assert collector.validate_data([]) is True

    def test_validate_data_missing_field(self, collector):
        """测试缺少必需字段"""
        data = [{"name": "平安银行"}]  # 缺少ts_code

        assert collector.validate_data(data) is False

    def test_validate_data_invalid_format(self, collector):
        """测试无效格式"""
        # 无效的市场代码
        data = [{"ts_code": "000001.XX"}]
        assert collector.validate_data(data) is False

        # 代码不是6位数字
        data = [{"ts_code": "00001.SZ"}]
        assert collector.validate_data(data) is False

        # 缺少市场代码
        data = [{"ts_code": "000001"}]
        assert collector.validate_data(data) is False

    def test_format_ts_code_sz(self, collector):
        """测试深圳交易所代码格式化"""
        assert collector._format_ts_code("000001") == "000001.SZ"
        assert collector._format_ts_code("300001") == "300001.SZ"

    def test_format_ts_code_sh(self, collector):
        """测试上海交易所代码格式化"""
        assert collector._format_ts_code("600000") == "600000.SH"
        assert collector._format_ts_code("680001") == "680001.SH"
        assert collector._format_ts_code("688001") == "688001.SH"

    def test_format_ts_code_bj(self, collector):
        """测试北交所代码格式化"""
        assert collector._format_ts_code("430001") == "430001.BJ"
        assert collector._format_ts_code("830001") == "830001.BJ"
        assert collector._format_ts_code("870001") == "870001.BJ"
        assert collector._format_ts_code("880001") == "880001.BJ"

    @pytest.mark.asyncio
    async def test_get_all_stocks(self, collector, mock_stock_data):
        """测试获取所有股票代码列表"""
        with patch("akshare.stock_info_a_code_name", return_value=mock_stock_data):
            result = await collector.get_all_stocks()

            assert len(result) == 5
            assert result[0] == "000001.SZ"
            assert result[2] == "600000.SH"
            assert result[4] == "430001.BJ"
            assert all(isinstance(code, str) for code in result)

    @pytest.mark.asyncio
    async def test_collect_integration(self, collector, mock_stock_data):
        """测试完整采集流程"""
        with patch("akshare.stock_info_a_code_name", return_value=mock_stock_data):
            result = await collector.collect()

            assert len(result) == 5
            assert all("ts_code" in stock for stock in result)
            assert all("name" in stock for stock in result)
            assert result[0]["ts_code"] == "000001.SZ"
