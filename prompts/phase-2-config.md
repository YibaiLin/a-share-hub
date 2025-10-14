# Phase 2: 配置管理模块

## 任务目标

实现基于pydantic-settings的配置管理系统，支持环境变量、类型验证和嵌套配置。

## 前置条件

- Phase 1已完成（项目结构已创建）
- 当前分支：phase-2-config
- 已读取SESSION.md了解当前状态

## 要创建/修改的文件

- `config/settings.py` - 配置类定义
- `.env` - 环境变量文件（从.env.example复制）
- `tests/test_config/test_settings.py` - 配置测试

## 详细实现要求

### 1. 实现config/settings.py

**完整代码**：

```python
"""
配置管理模块

使用pydantic-settings实现配置加载和验证
"""
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class ClickHouseConfig(BaseSettings):
    """ClickHouse配置"""
    
    host: str = Field(default="localhost", description="ClickHouse主机地址")
    port: int = Field(default=9000, ge=1, le=65535, description="ClickHouse端口")
    database: str = Field(default="stock_data", description="数据库名称")
    user: str = Field(default="default", description="用户名")
    password: str = Field(default="", description="密码")
    
    @property
    def url(self) -> str:
        """生成连接URL"""
        if self.password:
            return f"clickhouse://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"clickhouse://{self.user}@{self.host}:{self.port}/{self.database}"
    
    class Config:
        env_prefix = "CLICKHOUSE__"


class RedisConfig(BaseSettings):
    """Redis配置"""
    
    host: str = Field(default="localhost", description="Redis主机地址")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis端口")
    db: int = Field(default=0, ge=0, description="数据库编号")
    password: Optional[str] = Field(default=None, description="密码")
    max_connections: int = Field(default=10, ge=1, le=100, description="最大连接数")
    
    @property
    def url(self) -> str:
        """生成连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS__"


class Settings(BaseSettings):
    """主配置类"""
    
    # 应用配置
    app_name: str = Field(default="A-Share Hub", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    version: str = Field(default="0.2.0", description="版本号")
    
    # 服务配置
    host: str = Field(default="0.0.0.0", description="服务主机")
    port: int = Field(default=8000, ge=1, le=65535, description="服务端口")
    
    # 数据库配置（嵌套）
    clickhouse: ClickHouseConfig = Field(default_factory=ClickHouseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    
    # 采集配置
    collector_delay: float = Field(default=0.5, ge=0, description="采集延迟（秒）")
    batch_size: int = Field(default=1000, ge=1, description="批量大小")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_dir: str = Field(default="logs", description="日志目录")
    
    @validator('port')
    def validate_port(cls, v):
        """验证端口范围"""
        if not 1 <= v <= 65535:
            raise ValueError('端口必须在1-65535之间')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'日志级别必须是以下之一：{valid_levels}')
        return v_upper
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False


# 全局配置实例
settings = Settings()


if __name__ == "__main__":
    # 测试配置加载
    print("=" * 60)
    print("配置信息")
    print("=" * 60)
    print(f"应用名称: {settings.app_name}")
    print(f"调试模式: {settings.debug}")
    print(f"版本号: {settings.version}")
    print(f"服务地址: {settings.host}:{settings.port}")
    print(f"ClickHouse: {settings.clickhouse.url}")
    print(f"Redis: {settings.redis.url}")
    print(f"采集延迟: {settings.collector_delay}秒")
    print(f"批量大小: {settings.batch_size}")
    print(f"日志级别: {settings.log_level}")
    print("=" * 60)
```

### 2. 创建.env文件

**操作**：
```bash
cp .env.example .env
```

**说明**：
- 从.env.example复制创建.env
- 开发者可以根据实际环境修改.env
- .env已在.gitignore中，不会提交到Git

### 3. 创建测试文件

**tests/test_config/test_settings.py**：

```python
"""
配置管理模块测试
"""
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
        assert config.database == "stock_data"
        assert config.user == "default"
    
    def test_url_without_password(self):
        """测试无密码的URL生成"""
        config = ClickHouseConfig()
        url = config.url
        assert "clickhouse://" in url
        assert "default@localhost:9000/stock_data" in url
        assert ":" not in url.split("@")[0].split("//")[1]  # 确保没有密码
    
    def test_url_with_password(self):
        """测试有密码的URL生成"""
        config = ClickHouseConfig(password="secret")
        url = config.url
        assert "clickhouse://default:secret@" in url
    
    def test_port_validation(self):
        """测试端口验证"""
        with pytest.raises(ValidationError):
            ClickHouseConfig(port=0)
        with pytest.raises(ValidationError):
            ClickHouseConfig(port=65536)


class TestRedisConfig:
    """Redis配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.max_connections == 10
    
    def test_url_without_password(self):
        """测试无密码的URL生成"""
        config = RedisConfig()
        assert config.url == "redis://localhost:6379/0"
    
    def test_url_with_password(self):
        """测试有密码的URL生成"""
        config = RedisConfig(password="secret")
        assert config.url == "redis://:secret@localhost:6379/0"


class TestSettings:
    """主配置测试"""
    
    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()
        assert settings.app_name == "A-Share Hub"
        assert settings.debug is False
        assert settings.version == "0.2.0"
        assert settings.port == 8000
    
    def test_nested_config(self):
        """测试嵌套配置"""
        settings = Settings()
        assert settings.clickhouse.host == "localhost"
        assert settings.redis.host == "localhost"
    
    def test_port_validation(self):
        """测试端口验证"""
        with pytest.raises(ValidationError):
            Settings(port=0)
        with pytest.raises(ValidationError):
            Settings(port=70000)
    
    def test_log_level_validation(self):
        """测试日志级别验证"""
        settings = Settings(log_level="info")
        assert settings.log_level == "INFO"  # 应该转为大写
        
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")
    
    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("APP_NAME", "Test App")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("PORT", "9000")
        
        settings = Settings()
        assert settings.app_name == "Test App"
        assert settings.debug is True
        assert settings.port == 9000
    
    def test_nested_env_override(self, monkeypatch):
        """测试嵌套配置的环境变量覆盖"""
        monkeypatch.setenv("CLICKHOUSE__HOST", "192.168.1.100")
        monkeypatch.setenv("CLICKHOUSE__PORT", "9001")
        monkeypatch.setenv("REDIS__HOST", "192.168.1.101")
        
        settings = Settings()
        assert settings.clickhouse.host == "192.168.1.100"
        assert settings.clickhouse.port == 9001
        assert settings.redis.host == "192.168.1.101"
```

## Git提交策略

### 提交1: 实现配置基础结构
```bash
git add config/settings.py
git commit -m "feat: 实现配置管理基础结构

- 实现ClickHouseConfig配置类
- 实现RedisConfig配置类
- 实现Settings主配置类
- 支持环境变量嵌套配置
- 添加配置验证（端口范围、日志级别）"
```

### 提交2: 创建环境变量文件
```bash
git add .env
git commit -m "chore: 创建.env配置文件"
```

### 提交3: 添加配置测试
```bash
git add tests/test_config/
git commit -m "test: 添加配置管理单元测试

- 测试默认配置加载
- 测试URL生成
- 测试配置验证
- 测试环境变量覆盖
- 测试嵌套配置
- 测试覆盖率: 90%+"
```

### 提交4: 更新文档
```bash
git add .claude/TODO.md .claude/SESSION.md .claude/DEVLOG.md
git commit -m "docs: 更新TODO和会话状态"
```

## 测试验证

### 1. 测试配置加载
```bash
python config/settings.py
# 应该输出配置信息
```

### 2. 测试Python导入
```bash
python -c "from config.settings import settings; print(settings.app_name)"
# 应该输出: A-Share Hub
```

### 3. 运行单元测试
```bash
pytest tests/test_config/ -v
# 所有测试应该通过
```

### 4. 测试覆盖率
```bash
pytest --cov=config --cov-report=term tests/test_config/
# 覆盖率应该 > 80%
```

### 5. 测试环境变量覆盖
```bash
export DEBUG=true
python -c "from config.settings import settings; print(settings.debug)"
# 应该输出: True
```

## 验收标准

### 必须满足
- ✅ config/settings.py实现完整
- ✅ 支持嵌套配置（clickhouse、redis）
- ✅ 支持环境变量覆盖（`__`分隔符）
- ✅ 配置验证工作正常（端口、日志级别）
- ✅ .env文件已创建
- ✅ 单元测试全部通过
- ✅ 测试覆盖率 > 80%
- ✅ 可以导入：`from config.settings import settings`
- ✅ TODO.md已更新
- ✅ SESSION.md已更新
- ✅ DEVLOG.md已添加记录

### 预期结果
- 配置系统完整可用
- 类型验证工作正常
- 环境变量覆盖生效
- 测试覆盖充分

## 常见问题

### Q: pydantic-settings导入失败？
**A**: 确保安装了正确的版本：
```bash
pip install pydantic-settings>=2.1.0
```

### Q: 环境变量嵌套配置不生效？
**A**: 检查是否配置了`env_nested_delimiter = "__"`

### Q: 端口验证不生效？
**A**: 检查Field参数：`ge=1, le=65535`

## 注意事项

- `.env`文件已在`.gitignore`中，不会提交
- 配置类使用`default_factory`避免共享实例问题
- 验证器返回转换后的值（如日志级别转大写）
- 测试时使用`monkeypatch`模拟环境变量

## 预计耗时

15-20分钟