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
# 启动调度器（默认）
python main.py

# 启动API服务
python main.py --api

# 同时启动调度器和API
python main.py --all
```

## 数据采集

### 初始化数据库

首次使用前，需要初始化ClickHouse数据库表：

```bash
python scripts/init_db.py

# 如果需要重置数据库
python scripts/init_db.py --reset
```

### 历史数据回填

采集全市场近5年日线数据（约5000只股票）：

```bash
# 全市场回填（推荐）
python scripts/backfill.py --start-date 20200101 --all

# 指定股票回填
python scripts/backfill.py --start-date 20200101 --symbols 000001.SZ,600000.SH,000002.SZ

# 指定日期范围
python scripts/backfill.py --start-date 20200101 --end-date 20231231 --all

# 断点续传（中断后继续）
python scripts/backfill.py --resume

# 控制并发数（谨慎使用，避免API限流）
python scripts/backfill.py --all --concurrency 3

# 清除进度重新开始
python scripts/backfill.py --all --clean
```

**预计时间**：
- 全市场（5000只）：约42分钟（0.5秒/只）
- 单只股票：约0.5-1秒

**数据量**：
- 5000只 × 5年 × 约250个交易日 = 约625万条记录
- 存储空间：约1-2GB（ClickHouse压缩后）

### 定时任务

启动定时任务调度器，自动采集每日数据：

```bash
# 仅启动调度器
python main.py

# 同时启动调度器和API
python main.py --all

# 手动测试日线采集任务
python main.py --test
```

**定时任务配置**：
- 日线数据采集：每个交易日 18:30
- 股票列表更新：每日 08:00

### 常见问题

**Q: 如何查看回填进度？**
A: 脚本会实时显示进度条，同时进度保存在`.backfill_progress.json`文件中。

**Q: 回填中断后如何继续？**
A: 使用 `python scripts/backfill.py --resume` 从断点继续。

**Q: 如何处理失败的股票？**
A: 回填完成后会显示失败股票列表，可以使用`--symbols`参数单独重新采集。

**Q: 是否会重复插入数据？**
A: 不会。存储层有自动去重机制，相同日期的数据会自动跳过。

**Q: 如何加快回填速度？**
A: 可以使用 `--concurrency` 参数增加并发数，但需要注意API限流风险。建议从3开始尝试。

**Q: 为什么有的股票采集失败？**
A: 可能原因：1) 股票已退市 2) 数据源暂时无数据 3) 网络问题。失败股票会记录在进度文件中，可以稍后重试。

## 项目结构

详见 `.claude/CLAUDE.md`

## 开发指南

详见 `.claude/WORKFLOW.md`

## API文档

启动服务后访问：http://localhost:8000/docs

## License

MIT