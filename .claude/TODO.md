# A-Share Hub - 任务清单

## 📊 项目进度总览

**当前阶段**: Phase 9 - 历史数据回填
**整体进度**: 8/10 完成 (80%)
**最后更新**: 2025-10-15

```
Phase 0: ✅ 已完成 (手动)
Phase 1: ✅ 已完成
Phase 2: ✅ 已完成
Phase 3: ✅ 已完成
Phase 4: ✅ 已完成
Phase 5: ✅ 已完成
Phase 6: ✅ 已完成
Phase 7: ✅ 已完成
Phase 8: ✅ 已完成
Phase 9: ⏸️ 待开始
```

---

## Phase 0: 准备工作（手动）

**执行者**: 开发者手动操作  
**预计耗时**: 5分钟  
**依赖**: 无  
**状态**: ⏸️ 待开始

### 任务清单

- [x] 0.1 创建项目目录
  - 创建 `a-share-hub` 目录
  - 进入项目根目录

- [x] 0.2 初始化Git仓库
  - `git init`
  - 配置user.name和user.email
  - 创建GitHub远程仓库

- [x] 0.3 创建文档目录结构
  - 创建 `.claude/` 目录
  - 创建 `prompts/{init,features,testing,maintenance}` 目录

- [x] 0.4 复制核心文档
  - 从画布复制 `CLAUDE.md` 到 `.claude/CLAUDE.md`
  - 从画布复制 `WORKFLOW.md` 到 `.claude/WORKFLOW.md`
  - 从画布复制 `TODO.md` 到 `.claude/TODO.md`（本文件）
  - 创建空白 `SESSION.md`
  - 创建空白 `DEVLOG.md`
  - 创建空白 `DECISIONS.md`

- [x] 0.5 首次提交
  - `git add .claude/`
  - `git commit -m "docs: 初始化项目文档"`
  - `git tag v0.0.0 -m "项目启动"`

- [x] 0.6 推送到GitHub
  - `git remote add origin [仓库地址]`
  - `git push -u origin main`
  - `git push origin --tags`

### 验收标准
- ✅ GitHub仓库已创建且包含文档
- ✅ 本地Git仓库初始化完成
- ✅ `.claude/` 目录包含所有核心文档
- ✅ 已打标签 v0.0.0

---

## Phase 1: 项目初始化

**执行者**: Claude Code  
**预计耗时**: 10分钟  
**依赖**: Phase 0  
**分支**: `phase-1-init`  
**标签**: v0.1.0  
**状态**: ✅ 已完成

### 任务清单

- [x] 1.1 创建项目目录结构 ✅
  - 创建所有一级目录（config, core, models, collectors等）
  - 创建所有 `__init__.py` 文件
  - 创建 `logs/.gitkeep`

- [x] 1.2 创建基础配置文件 ✅
  - 创建 `requirements.txt`（包含所有依赖）
  - 创建 `.gitignore`（Python项目标准）
  - 创建 `.env.example`（环境变量模板）

- [x] 1.3 创建项目文档 ✅
  - 创建 `README.md`（项目说明）
  - 创建 `docs/API.md`（占位）

- [x] 1.4 创建主程序入口 ✅
  - 创建 `main.py`（空框架）

- [x] 1.5 验证项目结构 ✅
  - 运行 `ls -la` 验证目录
  - 运行 `python -m pytest --collect-only` 验证测试发现

### 验收标准
- ✅ 所有目录和文件已创建
- ✅ `requirements.txt` 包含所有必需依赖
- ✅ `.gitignore` 正确配置
- ✅ 可以执行 `python main.py`（即使是空程序）
- ✅ Git提交清晰（至少2-3个提交）

---

## Phase 2: 配置管理模块

**执行者**: Claude Code
**预计耗时**: 15分钟
**依赖**: Phase 1
**分支**: `phase-2-config`
**标签**: v0.2.0
**状态**: ✅ 已完成

### 任务清单

- [x] 2.1 实现配置基础结构 ✅
  - 创建 `config/settings.py`
  - 实现 `ClickHouseConfig` 类
  - 实现 `RedisConfig` 类
  - 实现 `Settings` 主配置类
  - 支持环境变量嵌套（`env_nested_delimiter="__"`）

- [x] 2.2 添加配置验证 ✅
  - 端口范围验证（1-65535）
  - 必填项验证
  - 类型验证（pydantic自动）

- [x] 2.3 创建环境变量文件 ✅
  - 更新 `.env.example`（完整的配置项）
  - 创建 `.env`（从example复制）

- [x] 2.4 添加单元测试 ✅
  - 创建 `tests/test_config/test_settings.py`
  - 测试默认配置加载
  - 测试环境变量覆盖
  - 测试嵌套配置
  - 测试配置验证

### 验收标准
- ✅ 可以成功加载配置：`from config.settings import settings`
- ✅ 环境变量覆盖正常工作
- ✅ 配置验证能捕获无效值
- ✅ 单元测试全部通过（覆盖率 > 80%）
- ✅ 可以通过 `settings.clickhouse.url` 访问嵌套配置

---

## Phase 3: 核心模块（数据库连接、日志）

**执行者**: Claude Code
**预计耗时**: 20分钟
**依赖**: Phase 2
**分支**: `phase-3-core`
**标签**: v0.3.0
**状态**: ✅ 已完成

### 任务清单

- [x] 3.1 实现日志系统 ✅
  - 创建 `core/logger.py`
  - 配置loguru日志格式
  - 配置日志级别和输出
  - 配置日志轮转（按日期）
  - 支持控制台和文件双输出

- [x] 3.2 实现ClickHouse连接池 ✅
  - 创建 `core/database.py`
  - 实现 `ClickHouseClient` 类
  - 实现异步连接管理
  - 实现连接池配置
  - 添加错误处理和重连机制

- [x] 3.3 实现Redis连接池 ✅
  - 创建 `core/cache.py`
  - 实现 `RedisClient` 类
  - 实现异步连接管理
  - 实现连接池配置
  - 添加错误处理

- [x] 3.4 添加单元测试 ✅
  - 创建 `tests/test_core/test_logger.py`
  - 创建 `tests/test_core/test_database.py`
  - 创建 `tests/test_core/test_cache.py`
  - 测试连接建立和关闭
  - 测试错误处理

### 验收标准
- ✅ 日志可以正常输出到控制台和文件
- ✅ 可以成功连接ClickHouse：`await db_client.execute("SELECT 1")`
- ✅ 可以成功连接Redis：`await redis_client.ping()`
- ✅ 连接池正常工作
- ✅ 单元测试全部通过

---

## Phase 4: 数据库初始化

**执行者**: Claude Code
**预计耗时**: 15分钟
**依赖**: Phase 3
**分支**: `phase-4-database`
**标签**: v0.4.0
**状态**: ✅ 已完成

### 任务清单

- [x] 4.1 创建数据库初始化脚本 ✅
  - 创建 `scripts/init_db.py`
  - 实现命令行参数解析（--reset等）
  - 添加表存在性检查

- [x] 4.2 定义ClickHouse表结构 ✅
  - 创建 `stock_basic` 表（股票基础信息）
  - 创建 `stock_daily` 表（日线数据）
  - 创建 `stock_minute` 表（分钟线数据）
  - 配置正确的分区策略
  - 配置正确的排序键

- [x] 4.3 实现表创建逻辑 ✅
  - 按顺序创建表
  - 添加详细日志
  - 实现幂等性（可重复执行）

- [x] 4.4 验证和测试 ✅
  - 运行脚本验证表创建
  - 测试重复执行（幂等性）
  - 测试 --reset 参数

### 验收标准
- ✅ 执行 `python scripts/init_db.py` 成功创建所有表
- ✅ 可以重复执行脚本（幂等）
- ✅ 表结构符合CLAUDE.md中的设计
- ✅ 分区策略正确（日线按月，分钟线按日）
- ✅ 可以执行基本查询验证表结构

---

## Phase 5: 基础采集器框架

**执行者**: Claude Code  
**预计耗时**: 25分钟  
**依赖**: Phase 4  
**分支**: `phase-5-collector`  
**标签**: v0.5.0  
**状态**: ⏸️ 待开始

### 任务清单

- [ ] 5.1 实现基础采集器类
  - 创建 `collectors/base.py`
  - 实现 `BaseCollector` 抽象基类
  - 实现限流机制（0.5秒延迟）
  - 实现重试机制（tenacity，3次重试）
  - 实现日志记录
  - 定义抽象方法（fetch_data, transform_data, validate_data）

- [ ] 5.2 实现数据转换工具
  - 创建 `utils/data_transform.py`
  - 实现 `price_to_int()` 函数（×100）
  - 实现 `int_to_price()` 函数（÷100）
  - 实现 `handle_null()` 函数（转-1）
  - 添加数据清洗函数

- [ ] 5.3 实现日期工具
  - 创建 `utils/date_helper.py`
  - 实现 `is_trading_day()` 函数
  - 实现 `get_trading_calendar()` 函数
  - 实现 `format_date()` 函数
  - 实现交易时间判断

- [ ] 5.4 添加单元测试
  - 创建 `tests/test_collectors/test_base.py`
  - 创建 `tests/test_utils/test_data_transform.py`
  - 创建 `tests/test_utils/test_date_helper.py`
  - 测试限流机制
  - 测试重试机制
  - 测试数据转换
  - 测试日期工具

### 验收标准
- ✅ BaseCollector可以被继承
- ✅ 限流机制工作正常（两次调用间隔≥0.5秒）
- ✅ 重试机制正常（失败后自动重试）
- ✅ 价格转换正确（12.34 → 1234）
- ✅ 单元测试全部通过（覆盖率 > 80%）

---

## Phase 6: 日线采集器+存储

**执行者**: Claude Code  
**预计耗时**: 30分钟  
**依赖**: Phase 5  
**分支**: `phase-6-daily`  
**标签**: v0.6.0  
**状态**: ⏸️ 待开始

### 任务清单

- [ ] 6.1 实现日线采集器
  - 创建 `collectors/daily.py`
  - 实现 `DailyCollector` 类（继承BaseCollector）
  - 对接AKShare的 `stock_zh_a_hist` 接口
  - 实现 `fetch_data()` 方法
  - 实现 `transform_data()` 方法（价格×100）
  - 实现 `validate_data()` 方法

- [ ] 6.2 实现ClickHouse存储操作
  - 创建 `storage/clickhouse_handler.py`
  - 实现 `ClickHouseHandler` 类
  - 实现 `insert_daily()` 方法（批量插入，1000条/批）
  - 实现 `query_daily()` 方法（按日期和股票查询）
  - 实现去重逻辑
  - 添加错误处理

- [ ] 6.3 定义数据模型
  - 创建 `models/stock.py`
  - 定义 `StockDaily` 数据模型
  - 定义字段验证规则

- [ ] 6.4 添加单元测试
  - 创建 `tests/test_collectors/test_daily.py`
  - 创建 `tests/test_storage/test_clickhouse_handler.py`
  - Mock AKShare接口
  - 测试数据采集
  - 测试数据转换
  - 测试数据存储

- [ ] 6.5 手动验证
  - 采集单只股票数据（如000001.SZ）
  - 验证数据存储到ClickHouse
  - 查询验证数据正确性

### 验收标准
- ✅ 可以成功采集任意股票的日线数据
- ✅ 价格数据正确转换（×100）
- ✅ 数据成功存储到ClickHouse
- ✅ 可以查询并验证数据
- ✅ 批量操作正常工作
- ✅ 单元测试全部通过（覆盖率 > 80%）
- ✅ 手动测试：`python -c "from collectors.daily import DailyCollector; ..."`

---

## Phase 7: API接口

**执行者**: Claude Code  
**预计耗时**: 30分钟  
**依赖**: Phase 6  
**分支**: `phase-7-api`  
**标签**: v0.7.0  
**状态**: ⏸️ 待开始

### 任务清单

- [ ] 7.1 创建FastAPI应用
  - 创建 `api/main.py`
  - 初始化FastAPI应用
  - 配置CORS
  - 配置全局异常处理
  - 配置生命周期事件

- [ ] 7.2 实现依赖注入
  - 创建 `api/dependencies.py`
  - 实现数据库连接依赖
  - 实现Redis连接依赖
  - 实现配置依赖

- [ ] 7.3 实现健康检查接口
  - 创建 `api/routes/health.py`
  - 实现 `GET /health` 接口
  - 实现 `GET /health/db` 接口（检查数据库）
  - 实现 `GET /health/cache` 接口（检查Redis）

- [ ] 7.4 实现日线数据查询接口
  - 创建 `api/routes/daily.py`
  - 实现 `GET /api/daily/{ts_code}` 接口
  - 支持日期范围过滤（start_date, end_date）
  - 支持分页（limit, offset）
  - 价格数据自动÷100
  - 定义响应模型

- [ ] 7.5 定义API响应模型
  - 创建 `models/schemas.py`
  - 定义 `DailyResponse` 模型
  - 定义 `HealthResponse` 模型
  - 定义通用响应模型

- [ ] 7.6 添加单元测试
  - 创建 `tests/test_api/test_health.py`
  - 创建 `tests/test_api/test_daily.py`
  - 使用 TestClient 测试接口
  - Mock数据库查询
  - 测试各种参数组合

- [ ] 7.7 验证和文档
  - 启动API服务：`uvicorn api.main:app --reload`
  - 访问 Swagger UI：http://localhost:8000/docs
  - 手动测试所有接口
  - 更新 `docs/API.md`

### 验收标准
- ✅ API服务可以成功启动
- ✅ 健康检查接口返回正常
- ✅ 日线查询接口返回正确数据
- ✅ 价格数据已还原（÷100）
- ✅ Swagger文档完整可用
- ✅ 单元测试全部通过
- ✅ 手动测试：`curl http://localhost:8000/health`

---

## Phase 8: 任务调度系统

**执行者**: Claude Code
**预计耗时**: 25分钟
**依赖**: Phase 6, 7
**分支**: `phase-8-scheduler`
**标签**: v0.8.0
**状态**: ✅ 已完成

### 任务清单

- [x] 8.1 实现调度器配置 ✅
  - 创建 `schedulers/scheduler.py`
  - 配置APScheduler
  - 实现优雅关闭（处理SIGTERM）
  - 添加调度器状态管理

- [x] 8.2 定义采集任务 ✅
  - 创建 `schedulers/tasks.py`
  - 实现日线采集任务（每日18:30执行）
  - 实现股票列表更新任务（每日8:00执行）
  - 实现任务执行日志
  - 实现失败重试

- [x] 8.3 实现主程序 ✅
  - 更新 `main.py`
  - 启动调度器
  - 启动API服务（可选，同时运行）
  - 实现优雅退出
  - 添加命令行参数

- [x] 8.4 添加测试 ✅
  - 创建 `tests/test_schedulers/test_tasks.py`
  - 测试任务定义
  - 测试任务执行逻辑
  - Mock定时触发

- [x] 8.5 验证和文档 ✅
  - 运行 `python main.py` 启动调度器
  - 验证任务按时执行
  - 验证日志输出
  - 更新 `README.md` 添加使用说明

### 验收标准
- ✅ 调度器可以成功启动
- ✅ 定时任务配置正确
- ✅ 可以手动触发任务验证
- ✅ 优雅关闭正常工作（Ctrl+C）
- ✅ 日志记录完整
- ✅ 单元测试通过
- ✅ 手动测试：观察任务执行

---

## Phase 9: 历史数据回填脚本

**执行者**: Claude Code
**预计耗时**: 40分钟
**依赖**: Phase 6 (DailyCollector)
**分支**: `phase-9-backfill`
**标签**: v0.9.0
**状态**: 🟡 进行中

### 任务清单

- [x] 9.1 实现股票列表采集器 ✅
  - 创建 `collectors/stock_list.py`
  - 实现 `StockListCollector` 类（继承BaseCollector）
  - 对接AKShare的 `stock_info_a_code_name` 接口
  - 实现数据转换（转换为ts_code格式）
  - 实现股票列表缓存

- [x] 9.2 实现进度管理器 ✅
  - 创建 `utils/progress.py`
  - 实现 `ProgressTracker` 类
  - 实现进度保存（JSON文件）
  - 实现进度加载和恢复
  - 实现统计信息汇总
  - 实现进度条显示（tqdm）

- [x] 9.3 实现回填脚本核心 ✅
  - 创建 `scripts/backfill.py`
  - 实现命令行参数解析（argparse）
  - 实现全市场采集逻辑
  - 实现指定股票采集逻辑
  - 实现断点续传功能
  - 实现并发控制（asyncio.Semaphore）
  - 实现批量采集和限流
  - 实现错误处理和重试
  - 实现采集报告生成

- [x] 9.4 添加单元测试 ✅
  - 创建 `tests/test_collectors/test_stock_list.py`
  - 创建 `tests/test_utils/test_progress.py`
  - 创建 `tests/test_scripts/test_backfill.py`
  - Mock AKShare接口
  - 测试股票列表采集
  - 测试进度管理（保存/加载/恢复）
  - 测试回填脚本逻辑
  - 测试断点续传

- [x] 9.5 更新文档 ✅
  - 更新 `README.md` 添加数据采集章节
  - 添加使用示例和说明
  - 添加常见问题FAQ
  - 更新 `DECISIONS.md` 记录ADR-009
  - 更新 `TODO.md` 标记任务完成
  - 更新 `SESSION.md` 记录会话状态

- [x] 9.6 手动验证和测试 ✅
  - 测试获取股票列表功能
  - 测试单只股票回填
  - 测试批量回填（10只股票）
  - 测试断点续传功能
  - 测试并发控制
  - 验证数据存储正确性
  - 生成测试报告

- [ ] 9.7 优化API限流保护机制（Bug修复与增强）🟡
  - 增加默认采集延迟（0.5s → 1.5s）
  - 实现智能动态延迟机制
    - RateLimiter支持自适应延迟调整
    - 失败时自动增加延迟（最大5秒）
    - 成功时逐步降低延迟
  - 实现连续失败监控和暂停机制
    - 创建FailureMonitor类
    - 连续失败5次触发暂停
    - 渐进式暂停（5分钟→10分钟→15分钟，最大30分钟）
    - 暂停倒计时显示
  - 完善失败处理和补齐机制
    - 增强失败记录（记录错误类型和时间）
    - 生成详细失败报告（按错误类型分组）
    - 保存失败清单到文件（.backfill_failed_stocks.txt）
    - 实现--retry-failed参数（自动重试失败股票）
    - 多次重试后仍失败的自动更新清单
    - 全部成功后自动删除失败清单
  - 更新配置文件（.env.example和.env）
  - 添加单元测试
    - 测试智能延迟机制
    - 测试失败监控器
    - 测试失败重试逻辑
  - 手动验证（采集10只股票验证不再限流）

### 验收标准
- ✅ 可以成功获取全A股股票列表（约5000只）
- ✅ 支持全市场数据回填（--all参数）
- ✅ 支持指定股票回填（--symbols参数）
- ✅ 支持指定日期范围（--start-date, --end-date）
- ✅ 支持断点续传（--resume参数）
- ✅ 并发控制正常工作（--concurrency参数）
- ✅ 实时进度显示清晰（进度条、ETA、速度）
- ✅ 错误处理完善（失败股票记录，不影响其他）
- ✅ 数据自动去重（不重复插入）
- ✅ 生成完整采集报告
- ✅ 单元测试全部通过（覆盖率 > 80%）
- ✅ 文档完整（README使用说明）
- ✅ 手动测试：成功回填10只股票5年数据

---

## 🔮 Backlog - 未来规划

### 功能增强（v0.9.x）
- [ ] 实现分钟线数据采集
  - 分钟线采集器
  - 交易时段判断
  - 实时缓存到Redis

- [ ] 实现分钟线查询接口
  - API路由
  - 响应模型

- [ ] 实现实时行情缓存
  - Redis缓存策略
  - 自动过期管理

### 高级功能（v1.x）
- [ ] Tick级数据采集
- [ ] WebSocket实时推送
- [ ] 多数据源支持（Tushare、东财）
- [ ] 数据质量监控面板
- [ ] 自动化回测接口

### 性能优化
- [ ] 采集并发优化（协程池）
- [ ] ClickHouse查询优化（物化视图）
- [ ] API响应缓存
- [ ] 数据库索引优化

### 运维工具
- [ ] Grafana监控面板
- [ ] 数据完整性检查脚本
- [ ] 自动化备份脚本
- [ ] 性能分析工具
- [ ] 告警系统

---

## 📝 开发日志

### 2025-10-12
- ✅ 完成项目规划和文档设计
- ✅ 创建CLAUDE.md、WORKFLOW.md、TODO.md
- ⏸️ 准备开始Phase 0

---

## 🎯 里程碑

| 里程碑 | 版本 | 目标 | 状态 |
|-------|------|------|------|
| 项目启动 | v0.0.0 | 完成文档和规划 | ✅ |
| 基础框架 | v0.1.0-v0.4.0 | 项目结构+配置+数据库 | ⏸️ |
| 核心功能 | v0.5.0-v0.6.0 | 采集器+存储 | ⏸️ |
| 完整系统 | v0.7.0-v0.8.0 | API+调度 | ⏸️ |
| 第一版 | v1.0.0 | 生产可用 | ⏸️ |

---

## 📊 统计信息

**总任务数**: 54个子任务  
**已完成**: 0个  
**进行中**: 0个  
**待开始**: 54个  

**预计总耗时**: ~2.5小时  
**已用时间**: 0小时  

---

## 💡 使用说明

### 对于Claude Code

1. **任务开始前**：阅读当前Phase的任务清单
2. **任务执行中**：严格按照子任务顺序执行
3. **任务完成后**：标记完成的任务为 `- [x]` 并添加 `✅`
4. **更新进度**：更新顶部的进度总览

### 对于开发者

1. **查看整体进度**：看顶部的进度总览
2. **了解当前任务**：看当前Phase的详细清单
3. **规划未来**：看Backlog部分
4. **回顾历史**：看开发日志部分

---

**下一步：开始Phase 0！** 🚀