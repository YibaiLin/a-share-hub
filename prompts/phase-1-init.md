# Phase 1: 项目初始化

## 任务目标

创建完整的项目目录结构和基础配置文件，为后续开发搭建框架。

## 前置条件

- Phase 0已完成（Git仓库已初始化，核心文档已创建）
- 当前分支：phase-1-init
- 已读取SESSION.md了解当前状态

## 要创建的文件

### 目录结构
```
a-share-hub/
├── config/
│   └── __init__.py
├── core/
│   └── __init__.py
├── models/
│   └── __init__.py
├── collectors/
│   └── __init__.py
├── storage/
│   └── __init__.py
├── schedulers/
│   └── __init__.py
├── api/
│   ├── __init__.py
│   └── routes/
│       └── __init__.py
├── utils/
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config/
│   │   └── __init__.py
│   ├── test_core/
│   │   └── __init__.py
│   ├── test_collectors/
│   │   └── __init__.py
│   ├── test_storage/
│   │   └── __init__.py
│   └── test_api/
│       └── __init__.py
├── scripts/
├── logs/
│   └── .gitkeep
├── docs/
│   └── API.md
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
└── main.py
```

## 详细实现要求

### 1. 创建所有目录和__init__.py文件

**要求**：
- 所有Python包目录必须有`__init__.py`
- 空目录使用`.gitkeep`占位
- 确保目录结构与CLAUDE.md一致

**执行**：
```python
# 使用Python脚本批量创建
import os

dirs = [
    'config', 'core', 'models', 'collectors', 'storage',
    'schedulers', 'api', 'api/routes', 'utils', 'tests',
    'tests/test_config', 'tests/test_core', 'tests/test_collectors',
    'tests/test_storage', 'tests/test_api', 'scripts', 'logs', 'docs'
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    if d not in ['scripts', 'logs', 'docs']:
        open(f'{d}/__init__.py', 'w').close()

open('logs/.gitkeep', 'w').close()
```

### 2. 创建requirements.txt

**内容**：
```txt
# 数据源
akshare>=1.12.0

# 数据库和缓存
clickhouse-connect>=0.7.0
redis>=5.0.0

# 任务调度
apscheduler>=3.10.0

# Web框架
fastapi>=0.110.0
uvicorn[standard]>=0.27.0

# 配置和验证
pydantic>=2.6.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0

# 日志
loguru>=0.7.0

# 工具库
tenacity>=8.2.0
pandas>=2.2.0
numpy>=1.26.0

# 测试
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# 开发工具
black>=24.0.0
ruff>=0.1.0
```

### 3. 创建.gitignore

**内容**：
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# 项目特定
.env
.env.local
logs/*.log
!logs/.gitkeep
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
Thumbs.db

# 临时文件
tmp/
temp/
*.tmp
```

### 4. 创建.env.example

**内容**：
```bash
# 应用配置
APP_NAME="A-Share Hub"
DEBUG=false
VERSION=0.1.0

# 服务配置
HOST=0.0.0.0
PORT=8000

# ClickHouse配置
CLICKHOUSE__HOST=localhost
CLICKHOUSE__PORT=9000
CLICKHOUSE__DATABASE=stock_data
CLICKHOUSE__USER=default
CLICKHOUSE__PASSWORD=

# Redis配置
REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__DB=0
REDIS__PASSWORD=
REDIS__MAX_CONNECTIONS=10

# 采集配置
COLLECTOR_DELAY=0.5
BATCH_SIZE=1000
MAX_RETRIES=3

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs
```

### 5. 创建README.md

**内容**：
```markdown
# A-Share Hub

中国A股数据采集和管理系统

## 项目简介

A-Share Hub是一个稳定可靠的A股市场数据基础设施，支持：
- 日线数据采集和存储
- 分钟线数据采集和存储
- RESTful API数据查询
- 定时任务调度

## 技术栈

- **Python**: 3.11.13
- **数据源**: AKShare
- **数据库**: ClickHouse
- **缓存**: Redis
- **API**: FastAPI
- **调度**: APScheduler

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，配置数据库连接等
```

### 初始化数据库

```bash
python scripts/init_db.py
```

### 启动服务

```bash
# 启动调度器
python main.py

# 启动API服务
uvicorn api.main:app --reload
```

## 项目结构

详见 `.claude/CLAUDE.md`

## 开发指南

详见 `.claude/WORKFLOW.md`

## API文档

启动服务后访问：http://localhost:8000/docs

## License

MIT

### 6.创建main.py

**内容：**

```python
"""
A-Share Hub 主程序入口

用途：启动任务调度器
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """主函数"""
    print("A-Share Hub")
    print("=" * 50)
    print("项目初始化完成！")
    print("下一步：Phase 2 - 配置管理模块")
    print("=" * 50)


if __name__ == "__main__":
    main()
```

### 7. 创建tests/conftest.py

**内容**：
```python
"""
pytest配置文件

定义全局fixtures和配置
"""
import pytest
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def project_root_dir():
    """项目根目录"""
    return project_root


@pytest.fixture
def test_data_dir():
    """测试数据目录"""
    return project_root / "tests" / "data"
```

### 8. 创建docs/API.md

**内容**：
```markdown
# API 文档

## 概述

A-Share Hub RESTful API

**Base URL**: `http://localhost:8000`

## 接口列表

### 健康检查

**GET /health**

检查服务状态

**响应示例**：
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

*更多接口将在Phase 7中添加*

## Git提交策略

### 提交1: 创建目录结构

```bash
git add config/ core/ models/ collectors/ storage/ schedulers/ api/ utils/ tests/ scripts/ logs/ docs/
git commit -m "chore: 创建项目目录结构"
```

### 提交2: 添加配置文件
```bash
git add requirements.txt .gitignore .env.example
git commit -m "chore: 添加项目配置文件"
```

### 提交3: 添加文档和主程序
```bash
git add README.md main.py docs/ tests/conftest.py
git commit -m "docs: 添加README和主程序入口"
```

### 提交4: 更新文档
```bash
git add .claude/TODO.md .claude/SESSION.md .claude/DEVLOG.md
git commit -m "docs: 更新TODO和会话状态"
```

## 测试验证

### 1. 验证目录结构
```bash
# 检查所有目录都已创建
ls -la

# 检查__init__.py文件
find . -name "__init__.py" | wc -l
# 应该输出：17（或更多）
```

### 2. 验证Python导入
```bash
python -c "import config; import core; import models; print('导入成功')"
```

### 3. 验证主程序
```bash
python main.py
# 应该输出欢迎信息
```

### 4. 验证测试框架
```bash
pytest --collect-only
# 应该能发现tests目录
```

## 验收标准

### 必须满足
- ✅ 所有目录已创建
- ✅ 所有__init__.py文件已创建
- ✅ requirements.txt包含所有必需依赖
- ✅ .gitignore配置正确
- ✅ README.md内容完整
- ✅ main.py可以运行
- ✅ 至少3-4个清晰的Git提交
- ✅ TODO.md已更新（标记Phase 1完成）
- ✅ SESSION.md已更新
- ✅ DEVLOG.md已添加记录

### 预期结果
- 项目结构清晰完整
- 可以执行`python main.py`
- 可以执行`pytest --collect-only`
- Git历史清晰

## 完成后操作

1. 向用户展示执行结果汇总
2. 等待用户验证
3. 用户确认后，准备合并和推送

## 注意事项

- 确保所有路径分隔符兼容Windows和Linux
- 所有文件使用UTF-8编码
- 注意.gitignore中logs目录的特殊处理（忽略.log但不忽略目录）
- main.py暂时只是占位，Phase 8会完善

## 预计耗时

10-15分钟