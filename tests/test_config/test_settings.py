"""
配置管理模块测试
"""

import os
import pytest
from pydantic import ValidationError
from config.settings import Settings, ClickHouseConfig, RedisConfig


class TestClickHouseConfig:
    """ClickHouse配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ClickHouseConfig()
        assert config.host == "localhost"
        assert config.port == 9000
        assert config.database == "a_share"
        assert config.user == "default"
        assert config.password == ""

    def test_url_generation(self):
        """测试URL生成"""
        config = ClickHouseConfig()
        assert config.url == "clickhouse://default@localhost:9000/a_share"

        # 测试带密码的URL
        config_with_pwd = ClickHouseConfig(password="secret")
        assert config_with_pwd.url == "clickhouse://default:secret@localhost:9000/a_share"

    def test_port_validation(self):
        """测试端口验证"""
        # 有效端口
        config = ClickHouseConfig(port=8123)
        assert config.port == 8123

        # 无效端口 - 太小
        with pytest.raises(ValidationError, match="端口必须在1-65535之间"):
            ClickHouseConfig(port=0)

        # 无效端口 - 太大
        with pytest.raises(ValidationError, match="端口必须在1-65535之间"):
            ClickHouseConfig(port=65536)

    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("CLICKHOUSE__HOST", "192.168.1.100")
        monkeypatch.setenv("CLICKHOUSE__PORT", "8123")
        monkeypatch.setenv("CLICKHOUSE__DATABASE", "test_db")

        config = ClickHouseConfig()
        assert config.host == "192.168.1.100"
        assert config.port == 8123
        assert config.database == "test_db"


class TestRedisConfig:
    """Redis配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None

    def test_url_generation(self):
        """测试URL生成"""
        config = RedisConfig()
        assert config.url == "redis://localhost:6379/0"

        # 测试带密码的URL
        config_with_pwd = RedisConfig(password="secret")
        assert config_with_pwd.url == "redis://:secret@localhost:6379/0"

    def test_port_validation(self):
        """测试端口验证"""
        # 有效端口
        config = RedisConfig(port=6380)
        assert config.port == 6380

        # 无效端口
        with pytest.raises(ValidationError, match="端口必须在1-65535之间"):
            RedisConfig(port=0)

    def test_db_validation(self):
        """测试数据库编号验证"""
        # 有效数据库编号
        config = RedisConfig(db=5)
        assert config.db == 5

        # 无效数据库编号 - 太小
        with pytest.raises(ValidationError, match="Redis数据库编号必须在0-15之间"):
            RedisConfig(db=-1)

        # 无效数据库编号 - 太大
        with pytest.raises(ValidationError, match="Redis数据库编号必须在0-15之间"):
            RedisConfig(db=16)

    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("REDIS__HOST", "192.168.1.200")
        monkeypatch.setenv("REDIS__PORT", "6380")
        monkeypatch.setenv("REDIS__DB", "2")

        config = RedisConfig()
        assert config.host == "192.168.1.200"
        assert config.port == 6380
        assert config.db == 2


class TestSettings:
    """主配置类测试"""

    def test_default_config(self):
        """测试默认配置"""
        settings = Settings()
        assert settings.app_name == "A-Share Hub"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_nested_config(self):
        """测试嵌套配置访问"""
        settings = Settings()

        # 访问ClickHouse配置
        assert settings.clickhouse.host == "localhost"
        assert settings.clickhouse.port == 9000
        assert settings.clickhouse.url.startswith("clickhouse://")

        # 访问Redis配置
        assert settings.redis.host == "localhost"
        assert settings.redis.port == 6379
        assert settings.redis.url.startswith("redis://")

    def test_env_nested_delimiter(self, monkeypatch):
        """测试环境变量嵌套分隔符"""
        monkeypatch.setenv("CLICKHOUSE__HOST", "testhost")
        monkeypatch.setenv("REDIS__PORT", "6380")

        settings = Settings()
        assert settings.clickhouse.host == "testhost"
        assert settings.redis.port == 6380

    def test_log_level_validation(self):
        """测试日志级别验证"""
        # 有效日志级别
        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"

        # 大小写不敏感
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"

        # 无效日志级别
        with pytest.raises(ValidationError, match="日志级别必须是"):
            Settings(log_level="INVALID")

    def test_api_port_validation(self):
        """测试API端口验证"""
        # 有效端口
        settings = Settings(api_port=8080)
        assert settings.api_port == 8080

        # 无效端口
        with pytest.raises(ValidationError, match="API端口必须在1-65535之间"):
            Settings(api_port=0)

    def test_collector_config_validation(self):
        """测试采集器配置验证"""
        # 有效配置
        settings = Settings(
            collector_delay=1.0,
            collector_retry_times=5,
            collector_batch_size=500
        )
        assert settings.collector_delay == 1.0
        assert settings.collector_retry_times == 5
        assert settings.collector_batch_size == 500

        # 无效延迟
        with pytest.raises(ValidationError, match="采集延迟不能为负数"):
            Settings(collector_delay=-1)

        # 无效重试次数
        with pytest.raises(ValidationError, match="重试次数不能为负数"):
            Settings(collector_retry_times=-1)

        # 无效批量大小
        with pytest.raises(ValidationError, match="批量大小必须大于0"):
            Settings(collector_batch_size=0)

    def test_env_file_loading(self, tmp_path, monkeypatch):
        """测试从.env文件加载配置"""
        # 创建临时.env文件
        env_file = tmp_path / ".env"
        env_file.write_text(
            "APP_NAME=Test App\n"
            "DEBUG=true\n"
            "LOG_LEVEL=DEBUG\n"
            "CLICKHOUSE__HOST=testhost\n"
            "REDIS__PORT=6380\n"
        )

        # 切换工作目录
        monkeypatch.chdir(tmp_path)

        settings = Settings()
        assert settings.app_name == "Test App"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.clickhouse.host == "testhost"
        assert settings.redis.port == 6380

    def test_extra_fields_ignored(self):
        """测试额外字段被忽略"""
        # 不应该抛出错误
        settings = Settings(unknown_field="value")
        assert not hasattr(settings, "unknown_field")


class TestSettingsIntegration:
    """配置集成测试"""

    def test_full_config_from_env(self, monkeypatch):
        """测试完整的环境变量配置"""
        # 设置所有环境变量
        env_vars = {
            "APP_NAME": "Production App",
            "DEBUG": "false",
            "LOG_LEVEL": "WARNING",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "CLICKHOUSE__HOST": "192.168.1.100",
            "CLICKHOUSE__PORT": "8123",
            "CLICKHOUSE__DATABASE": "prod_db",
            "CLICKHOUSE__USER": "admin",
            "CLICKHOUSE__PASSWORD": "secret",
            "REDIS__HOST": "192.168.1.200",
            "REDIS__PORT": "6380",
            "REDIS__DB": "5",
            "REDIS__PASSWORD": "redis_secret",
            "COLLECTOR_DELAY": "1.0",
            "COLLECTOR_RETRY_TIMES": "5",
            "COLLECTOR_BATCH_SIZE": "2000",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        settings = Settings()

        # 验证基础配置
        assert settings.app_name == "Production App"
        assert settings.debug is False
        assert settings.log_level == "WARNING"
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 9000

        # 验证ClickHouse配置
        assert settings.clickhouse.host == "192.168.1.100"
        assert settings.clickhouse.port == 8123
        assert settings.clickhouse.database == "prod_db"
        assert settings.clickhouse.user == "admin"
        assert settings.clickhouse.password == "secret"

        # 验证Redis配置
        assert settings.redis.host == "192.168.1.200"
        assert settings.redis.port == 6380
        assert settings.redis.db == 5
        assert settings.redis.password == "redis_secret"

        # 验证采集器配置
        assert settings.collector_delay == 1.0
        assert settings.collector_retry_times == 5
        assert settings.collector_batch_size == 2000

    def test_connection_urls(self):
        """测试连接URL生成"""
        settings = Settings()

        # ClickHouse URL
        ch_url = settings.clickhouse.url
        assert "clickhouse://" in ch_url
        assert str(settings.clickhouse.port) in ch_url
        assert settings.clickhouse.database in ch_url

        # Redis URL
        redis_url = settings.redis.url
        assert "redis://" in redis_url
        assert str(settings.redis.port) in redis_url
        assert str(settings.redis.db) in redis_url
