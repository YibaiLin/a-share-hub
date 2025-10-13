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