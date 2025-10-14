"""
健康检查API测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from api.main import app


class TestHealthAPI:
    """健康检查API测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    def test_health_check(self, client):
        """测试基本健康检查"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "healthy"
        assert data["data"]["status"] == "healthy"
        assert "timestamp" in data["data"]

    @patch('api.routes.health.get_db_client')
    def test_health_check_db_success(self, mock_get_client, client):
        """测试数据库健康检查成功"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_get_client.return_value = mock_client

        response = client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "healthy"

    @patch('api.routes.health.get_db_client')
    def test_health_check_db_failure(self, mock_get_client, client):
        """测试数据库健康检查失败"""
        mock_client = Mock()
        mock_client.ping.return_value = False
        mock_get_client.return_value = mock_client

        response = client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 500
        assert data["data"]["status"] == "unhealthy"

    @patch('api.routes.health.get_db_client')
    def test_health_check_db_error(self, mock_get_client, client):
        """测试数据库健康检查异常"""
        mock_get_client.side_effect = Exception("Connection failed")

        response = client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 500
        assert data["data"]["status"] == "error"
