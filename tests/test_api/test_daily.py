"""
日线数据API测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from api.main import app
from api.dependencies import get_db_handler


class TestDailyAPI:
    """日线数据API测试"""

    @pytest.fixture
    def mock_handler(self):
        """Mock的Handler"""
        handler = Mock()
        handler.query_daily.return_value = [
            {
                "ts_code": "000001.SZ",
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
            }
        ]
        return handler

    @pytest.fixture
    def client(self, mock_handler):
        """测试客户端"""
        def override_get_db_handler():
            yield mock_handler

        app.dependency_overrides[get_db_handler] = override_get_db_handler
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_get_daily_data_success(self, client, mock_handler):
        """测试成功查询日线数据"""
        response = client.get("/api/daily/000001.SZ")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["ts_code"] == "000001.SZ"
        assert data["data"]["count"] == 1
        assert len(data["data"]["data"]) == 1

        # 验证价格已还原
        item = data["data"]["data"][0]
        assert item["open"] == 10.5
        assert item["close"] == 10.6

    def test_get_daily_data_with_params(self, client, mock_handler):
        """测试带参数查询"""
        response = client.get(
            "/api/daily/000001.SZ",
            params={
                "start_date": "20240101",
                "end_date": "20240131",
                "limit": 10,
            }
        )

        assert response.status_code == 200
        mock_handler.query_daily.assert_called_once()

    def test_get_daily_data_empty(self):
        """测试空数据"""
        mock_handler = Mock()
        mock_handler.query_daily.return_value = []

        def override_get_db_handler():
            yield mock_handler

        app.dependency_overrides[get_db_handler] = override_get_db_handler
        client = TestClient(app)

        response = client.get("/api/daily/000001.SZ")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["count"] == 0

        app.dependency_overrides.clear()

    def test_get_latest_daily_success(self, client, mock_handler):
        """测试获取最新数据"""
        response = client.get("/api/daily/000001.SZ/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["ts_code"] == "000001.SZ"

    def test_get_latest_daily_not_found(self):
        """测试无数据情况"""
        mock_handler = Mock()
        mock_handler.query_daily.return_value = []

        def override_get_db_handler():
            yield mock_handler

        app.dependency_overrides[get_db_handler] = override_get_db_handler
        client = TestClient(app)

        response = client.get("/api/daily/000001.SZ/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert data["data"] is None

        app.dependency_overrides.clear()

    def test_get_daily_data_error(self):
        """测试查询异常"""
        mock_handler = Mock()
        mock_handler.query_daily.side_effect = Exception("Database error")

        def override_get_db_handler():
            yield mock_handler

        app.dependency_overrides[get_db_handler] = override_get_db_handler
        client = TestClient(app)

        response = client.get("/api/daily/000001.SZ")

        assert response.status_code == 500

        app.dependency_overrides.clear()
