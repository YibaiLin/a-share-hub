"""
配置管理模块

使用pydantic-settings管理应用配置，支持：
- 环境变量加载
- 嵌套配置结构
- 配置验证
- 默认值设置
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClickHouseConfig(BaseSettings):
    """ClickHouse数据库配置"""

    host: str = Field(default="localhost", description="ClickHouse服务器地址")
    port: int = Field(default=8123, description="ClickHouse HTTP端口（8123=HTTP, 9000=TCP）")
    database: str = Field(default="a_share", description="数据库名称")
    user: str = Field(default="default", description="用户名")
    password: str = Field(default="", description="密码")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """验证端口范围"""
        if not 1 <= v <= 65535:
            raise ValueError(f"端口必须在1-65535之间，当前值: {v}")
        return v

    @property
    def url(self) -> str:
        """生成ClickHouse连接URL"""
        auth = f"{self.user}:{self.password}@" if self.password else f"{self.user}@"
        return f"clickhouse://{auth}{self.host}:{self.port}/{self.database}"

    model_config = SettingsConfigDict(
        env_prefix="CLICKHOUSE__",
        case_sensitive=False,
    )


class RedisConfig(BaseSettings):
    """Redis缓存配置"""

    host: str = Field(default="localhost", description="Redis服务器地址")
    port: int = Field(default=6379, description="Redis服务器端口")
    db: int = Field(default=0, description="Redis数据库编号")
    password: Optional[str] = Field(default=None, description="密码")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """验证端口范围"""
        if not 1 <= v <= 65535:
            raise ValueError(f"端口必须在1-65535之间，当前值: {v}")
        return v

    @field_validator("db")
    @classmethod
    def validate_db(cls, v: int) -> int:
        """验证Redis数据库编号"""
        if not 0 <= v <= 15:
            raise ValueError(f"Redis数据库编号必须在0-15之间，当前值: {v}")
        return v

    @property
    def url(self) -> str:
        """生成Redis连接URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    model_config = SettingsConfigDict(
        env_prefix="REDIS__",
        case_sensitive=False,
    )


class Settings(BaseSettings):
    """应用主配置类"""

    # 应用基础配置
    app_name: str = Field(default="A-Share Hub", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")

    # 数据库配置
    clickhouse: ClickHouseConfig = Field(default_factory=ClickHouseConfig)

    # 缓存配置
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # API配置
    api_host: str = Field(default="0.0.0.0", description="API服务监听地址")
    api_port: int = Field(default=8000, description="API服务端口")

    # 采集器配置
    collector_delay: float = Field(default=0.5, description="采集延迟（秒）")
    collector_retry_times: int = Field(default=3, description="重试次数")
    collector_batch_size: int = Field(default=1000, description="批量插入大小")

    @field_validator("api_port")
    @classmethod
    def validate_api_port(cls, v: int) -> int:
        """验证API端口范围"""
        if not 1 <= v <= 65535:
            raise ValueError(f"API端口必须在1-65535之间，当前值: {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"日志级别必须是{valid_levels}之一，当前值: {v}")
        return v_upper

    @field_validator("collector_delay")
    @classmethod
    def validate_collector_delay(cls, v: float) -> float:
        """验证采集延迟"""
        if v < 0:
            raise ValueError(f"采集延迟不能为负数，当前值: {v}")
        return v

    @field_validator("collector_retry_times")
    @classmethod
    def validate_collector_retry_times(cls, v: int) -> int:
        """验证重试次数"""
        if v < 0:
            raise ValueError(f"重试次数不能为负数，当前值: {v}")
        return v

    @field_validator("collector_batch_size")
    @classmethod
    def validate_collector_batch_size(cls, v: int) -> int:
        """验证批量大小"""
        if v <= 0:
            raise ValueError(f"批量大小必须大于0，当前值: {v}")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


# 全局配置实例
settings = Settings()
