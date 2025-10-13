# A-Share Hub - Claude 开发指南

## 项目概述

**项目名称**: A-Share Hub  
**仓库**: https://github.com/YibaiLin/a-share-hub  
**定位**: 中国A股数据采集和管理系统  
**核心价值**: 稳定可靠的市场数据基础设施，可扩展的数据源接入架构

### 项目目标
**第一阶段（当前）**：
- ✅ 实现A股日线数据采集和存储
- ✅ 实现A股分钟线数据采集和存储
- ✅ 提供数据查询API接口
- ✅ 实现定时任务调度
- ✅ 建立完整的测试体系
- ✅ 使用GitHub进行版本控制和协作

**后续阶段（规划）**：
- 📋 扩展到港股、美股数据
- 📋 增加Tick级数据采集
- 📋 实现实时数据推送
- 📋 增加数据质量监控
- 📋 开源发布和社区协作

### 项目范围
**包含**：
- 数据采集（AKShare数据源）
- 数据存储（ClickHouse + Redis）
- 数据查询（FastAPI接口）
- 任务调度（APScheduler）

**不包含**：
- 数据分析和可视化
- 策略回测系统
- 实盘交易接口

## 技术栈

### 运行环境
- Python 3.11.13 (Miniconda, alpha环境)
- Windows 10 + WSL2 (Ubuntu 22.04)
- ClickHouse: localhost:9000
- Redis: localhost:6379

### 核心依赖
```python
akshare>=1.12.0           # 数据源API
clickhouse-connect>=0.7.0  # ClickHouse驱动
redis>=5.0.0              # Redis客户端
apscheduler>=3.10.0       # 任务调度
fastapi>=0.110.0          # Web框架
uvicorn[standard]>=0.27.0 # ASGI服务器
pydantic>=2.6.0           # 数据验证
pydantic-settings>=2.1.0  # 配置管理
loguru>=0.7.0             # 日志框架
tenacity>=8.2.0           # 重试机制
pandas>=2.2.0             # 数据处理
pytest>=8.0.0             # 测试框架
```

## 项目结构

```
a-share-hub/
├── .claude/                     # Claude文档
│   ├── CLAUDE.md               # 本文件（Claude执行指南）
│   ├── SESSION.md              # 会话状态管理
│   ├── TODO.md                 # 任务清单
│   ├── DECISIONS.md            # 技术决策记录
│   ├── WORKFLOW.md             # 开发流程（用户指南）
│   └── DEVLOG.md               # 开发日志
├── prompts/                     # 提示词库
│   ├── phase-0-prepare.md      # Phase 0: 准备工作
│   ├── phase-1-init.md         # Phase 1: 项目初始化
│   ├── phase-2-config.md       # Phase 2: 配置管理
│   ├── phase-3-core.md         # Phase 3: 核心模块
│   ├── phase-4-database.md     # Phase 4: 数据库初始化
│   ├── phase-5-collector.md    # Phase 5: 基础采集器
│   ├── phase-6-daily.md        # Phase 6: 日线采集器
│   ├── phase-7-api.md          # Phase 7: API接口
│   └── phase-8-scheduler.md    # Phase 8: 任务调度
├── config/                      # 配置管理
│   ├── __init__.py
│   └── settings.py
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── database.py             # ClickHouse连接池
│   ├── cache.py                # Redis连接池
│   └── logger.py               # 日志配置
├── models/                      # 数据模型
│   ├── __init__.py
│   ├── stock.py
│   └── schemas.py
├── collectors/                  # 数据采集器
│   ├── __init__.py
│   ├── base.py
│   ├── daily.py
│   └── minute.py
├── storage/                     # 存储层
│   ├── __init__.py
│   ├── clickhouse_handler.py
│   └── redis_handler.py
├── schedulers/                  # 任务调度
│   ├── __init__.py
│   ├── scheduler.py
│   └── tasks.py
├── api/                         # FastAPI接口
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   └── routes/
│       ├── __init__.py
│       ├── daily.py
│       └── health.py
├── utils/                       # 工具函数
│   ├── __init__.py
│   ├── date_helper.py
│   └── data_transform.py
├── tests/                       # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config/
│   ├── test_core/
│   ├── test_collectors/
│   ├── test_storage/
│   └── test_api/
├── scripts/                     # 运维脚本
│   ├── init_db.py
│   └── backfill.py
├── logs/                        # 日志目录
│   └── .gitkeep
├── docs/                        # 文档
│   └── API.md
├── .env                         # 环境变量
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── main.py                      # 主程序入口
```

## 任务执行规范

### 标准执行流程

当你收到任务指令时，应该按照以下流程执行：

**第1步：理解任务**
- 仔细阅读任务描述或prompt文件内容
- 查看TODO.md了解当前Phase的具体任务
- 识别需要创建/修改的文件
- 理解实现要求和验收标准

**第2步：展示执行计划**
在开始编码前，必须输出：
```markdown
## 执行计划

### 将要创建的文件
- path/to/file1.py: 用途说明
- path/to/file2.py: 用途说明

### 将要修改的文件
- path/to/existing.py: 修改内容说明

### 实现思路
1. 步骤1
2. 步骤2

### 预计提交点
- 提交1: 完成基础结构
- 提交2: 完成核心功能
- 提交3: 完成测试
```
然后等待用户确认。

**第3步：实现代码**
用户确认后开始实现：
- 严格遵循本文档的代码规范
- 为每个模块编写单元测试
- 确保代码符合项目架构
- **测试通过后再进行Git提交**（见版本管理章节）

**第4步：执行测试**
- 运行所有相关的单元测试
- 确保测试通过
- 记录测试结果

**第5步：展示结果汇总**
完成后必须输出：
```markdown
## 执行结果

### 已创建的文件
- path/to/file1.py
- path/to/file2.py

### 已修改的文件
- path/to/existing.py

### 关键代码预览
[展示核心代码片段]

### 测试结果
- 通过: X个
- 失败: X个
- 跳过: X个

### Git提交记录
- commit 1: message
- commit 2: message

### 需要人工验证
1. 验证点1
2. 验证点2
```
然后等待用户确认。

## 文档协作规范

### 文档更新原则
- 所有项目文档你都可以更新
- 关键文档（DECISIONS.md、TODO.md大的调整）需要先提出，用户确认后再更新
- 日常文档（DEVLOG.md、TODO.md任务状态）可以直接更新

### TODO.md - 任务清单

**如何使用**：
- 每次任务开始前，阅读TODO.md了解当前Phase的任务范围
- 严格按照TODO.md中定义的子任务执行
- 当前Phase的任务范围已经明确，不要超出

**如何更新**：
- 完成某个子任务后，立即更新TODO.md
- 将完成的任务标记为 `- [x]` 并添加 `✅`
- 格式示例：
  ```markdown
  - [x] 1.1 创建项目目录结构 ✅
  - [x] 1.2 配置requirements.txt ✅
  - [ ] 1.3 配置.gitignore
  ```
- 更新后进行Git提交

**需要用户确认的情况**：
- 需要添加新的子任务
- 需要修改任务描述
- 需要调整任务优先级
- 发现任务划分不合理

### DECISIONS.md - 技术决策记录

**如何使用**：
- 遇到技术选型问题时，查看DECISIONS.md是否有相关决策
- 如果有，严格遵循已有决策
- 如果没有，在对话中提出多个方案，说明优劣

**如何更新**：
- 当用户做出技术决策后，你负责记录到DECISIONS.md
- 使用标准格式（见DECISIONS.md中的模板）
- 记录完成后进行Git提交
- 提交信息：`docs: 记录技术决策 ADR-XXX`

**记录时机**：
- 用户明确选择了某个技术方案
- 讨论得出重要的架构决定
- 确定了关键的设计原则

### DEVLOG.md - 开发日志

**用途**：
记录开发过程中的关键操作和事件

**如何更新**：
每次完成一个重要操作后，添加日志条目：
```markdown
## 2025-10-12

### 14:30 - 完成Phase 1项目初始化
- 创建了完整的项目目录结构
- 配置了requirements.txt和.gitignore
- 初始化Git仓库
- 标签: v0.1.0

### 16:20 - 修复配置加载问题
- 问题: 环境变量嵌套配置无法加载
- 原因: pydantic-settings配置错误
- 解决: 添加env_nested_delimiter配置
- Commit: abc1234
```

**记录内容**：
- 时间戳
- 完成的Phase/任务
- 遇到的问题和解决方案
- 重要的技术决策
- Git提交/标签信息

**更新时机**：
- 完成一个Phase
- 修复一个重要bug
- 做出重要修改
- 每天工作结束

### WORKFLOW.md - 开发流程

**说明**：
- 这是用户的操作指南
- 你不需要特别关注此文档
- 本CLAUDE.md文档才是你的执行指南
- 你不需要更新此文档

## 会话管理

### SESSION.md - 会话状态

**用途**：
记录当前会话状态，确保跨会话的上下文连续性。

**标准结构**：
```markdown
# 会话状态

## 当前状态
- **当前Phase**: Phase 2 - 配置管理模块
- **当前任务**: 2.2 实现配置验证
- **进度**: 60%
- **分支**: phase-2-config
- **最后更新**: 2025-10-12 16:30

## 上次会话总结
### 完成的工作
- ✅ 实现了config/settings.py基础结构
- ✅ 配置了ClickHouse和Redis配置类
- ✅ 通过了基础配置测试

### 遇到的问题
- ⚠️ 环境变量嵌套配置无法正确加载
  - 原因：未配置env_nested_delimiter
  - 解决：添加env_nested_delimiter="__"

### Git提交
- abc1234 - feat: 实现配置基础结构
- def5678 - fix: 修复环境变量嵌套配置
- ghi9012 - test: 添加配置加载测试

## 下次会话计划
### 待完成任务
- [ ] 2.2 添加配置验证方法（端口范围、必填项）
- [ ] 2.3 添加配置单元测试
- [ ] 2.4 更新.env.example文档

### 注意事项
- 配置验证要检查端口范围（1-65535）
- 测试要覆盖环境变量覆盖场景
- pydantic-settings版本需>=2.1.0

### 可能的问题
- 如果测试失败，检查.env文件是否存在
- 注意配置类的默认值设置
```

### 会话开始时

每次新会话开始时，你必须执行以下步骤：

**第1步：读取会话状态**
按顺序读取以下文件：
```
1. .claude/SESSION.md - 了解当前状态和计划（最重要）
2. .claude/TODO.md - 查看整体进度
3. .claude/DEVLOG.md - 完整阅读，了解全部开发历史
```

**说明**：
- SESSION.md告诉你"现在在哪"
- TODO.md告诉你"整体进度如何"
- DEVLOG.md告诉你"之前发生了什么"
- 三者结合才能完整理解项目状态

**第2步：向用户确认状态**
输出以下格式的确认信息：
```markdown
## 会话状态确认

📍 当前位置：
- Phase: [X]
- 任务: [具体任务]
- 进度: [X%]
- 分支: [branch-name]

📝 上次会话：
- 完成：[列出完成的工作]
- 问题：[遇到的问题及解决方案]
- 提交：[N]个

📋 本次计划：
- [ ] 任务1
- [ ] 任务2

请确认是否继续？或需要调整？
```

**第3步：等待用户确认**
- 如果用户说"继续"或"开始"，按计划执行
- 如果用户提出调整，更新计划后再执行

### 会话进行中

**实时更新TODO.md**：
- 完成某个子任务后，立即更新TODO.md标记为完成
- 更新后提交：`git commit -m "docs: 更新TODO任务状态"`

**记录但不立即写入**：
- 在心中记录或临时记录本次会话的关键信息
- 完成的工作、遇到的问题、解决方案
- Git提交信息
- **不要在会话进行中频繁更新SESSION.md**

**原因**：
- SESSION.md的作用是跨会话状态传递
- 当前会话内你能保持上下文，不需要实时写入SESSION
- 会话结束时一次性更新SESSION即可

### 会话结束时

在会话即将结束时（用户说"今天到这"、"结束"或你完成了所有任务），你必须执行：

**第1步：更新SESSION.md**
更新所有部分：
```markdown
## 当前状态
- **当前Phase**: [更新]
- **当前任务**: [更新到下一个未完成任务]
- **进度**: [更新百分比]
- **分支**: [当前分支名]
- **最后更新**: [当前时间]

## 上次会话总结
[记录本次会话的完整总结]

## 下次会话计划
[明确列出下一步要做什么]
```

**第2步：追加DEVLOG.md**
在文件末尾添加本次会话的记录：
```markdown
## 2025-10-12

### 16:30 - Phase 2: 配置管理（会话2）
**完成**：
- 实现配置验证功能
- 添加单元测试
- 修复环境变量嵌套问题

**Git提交**：
- abc1234 - feat: 实现配置验证
- def5678 - test: 添加配置测试

**问题记录**：
- 环境变量嵌套配置问题 → 已解决

**进度**：Phase 2: 2.2/2.4完成 (60%)

**下次**：继续2.3任务 - 完善测试覆盖
```

**第3步：更新TODO.md任务状态**
标记完成的任务：
```markdown
- [x] 2.1 实现配置基础结构 ✅
- [x] 2.2 添加配置验证方法 ✅
- [ ] 2.3 添加配置单元测试
```

**第4步：提交文档更新**
```bash
git add .claude/SESSION.md .claude/DEVLOG.md .claude/TODO.md
git commit -m "docs: 更新会话状态和开发日志"
```

**第5步：推送到GitHub（如果本Phase完成）**

如果本次会话完成了一个完整的Phase，需要推送到GitHub：

```bash
# 展示推送信息
准备推送到GitHub:
- 仓库: https://github.com/YibaiLin/a-share-hub
- 分支: main
- 标签: v0.X.0
- 提交数: N个

是否确认推送？
```

用户确认后执行：
```bash
git push origin main
git push origin --tags
git push origin phase-X-name  # 推送功能分支（可选）
```

**如果只是Phase中途的会话**，不需要推送，在Phase完成时统一推送。

**第6步：向用户汇报**
输出会话总结：
```markdown
## 会话总结

### 本次完成 ✅
- ✅ 配置验证功能
- ✅ 单元测试
- ✅ 修复环境变量问题

### Git提交 📝
- 3个提交
- abc1234 - feat: 实现配置验证
- def5678 - test: 添加配置测试
- ghi9012 - docs: 更新会话状态

### 文档更新 📄
- SESSION.md: 已更新当前状态
- DEVLOG.md: 已追加本次记录
- TODO.md: 已标记完成任务

### GitHub同步 🔄
[如果已推送]
- ✅ 已推送到 origin/main
- ✅ 已推送标签 v0.X.0
- ✅ GitHub仓库已同步

[如果未推送]
- ⏸️ Phase未完成，暂不推送
- 📌 Phase完成时将统一推送

### 下次继续 📋
Phase 2 - 2.3 添加配置单元测试

所有更改已提交，可以安全结束会话。
```

### 会话管理检查清单

**每次会话开始**：
- [ ] 读取SESSION.md
- [ ] 读取TODO.md
- [ ] 阅读DEVLOG.md全文
- [ ] 向用户确认状态
- [ ] 等待用户批准后开始

**每次会话结束**：
- [ ] 更新SESSION.md所有部分
- [ ] 追加DEVLOG.md新记录
- [ ] 更新TODO.md任务状态
- [ ] 提交文档变更
- [ ] 如果Phase完成，推送到GitHub
- [ ] 向用户汇报总结

### 特殊情况处理

**情况1：SESSION.md不存在（首次会话）**
```markdown
这是首次会话，SESSION.md不存在。
我将在会话结束时创建它。

开始Phase 0的工作...
```

**情况2：跨Phase会话**
```markdown
上次会话完成了Phase 1，本次开始Phase 2。

需要：
1. 完成Phase 1的最终提交和标签
2. 创建Phase 2的新分支
3. 更新SESSION.md到新Phase

请确认后继续。
```

**情况3：中断恢复**
```markdown
SESSION.md显示上次会话未正常结束。

上次状态：
- 正在执行：[任务]
- 已完成：[部分工作]
- 未提交的更改：[可能存在]

建议：
1. 检查git状态
2. 确认要继续还是重新开始

请指示。
```

## 版本管理

### Git工作流

你负责所有Git操作，包括：
- 创建和切换分支
- 代码提交
- 合并分支
- 打标签
- **推送到GitHub远程仓库**

在关键操作（合并、打标签、推送）前需要用户确认。

### GitHub远程仓库

**仓库地址**: https://github.com/YibaiLin/a-share-hub

**注意事项**：
- 确保已配置SSH密钥或访问令牌
- 每次Phase完成时推送到GitHub
- 推送包括：代码、标签、所有分支

### 分支管理

**Phase开始时**：
```bash
# 自动创建并切换到新分支
git checkout -b phase-X-name

# 示例：
git checkout -b phase-1-init
git checkout -b phase-2-config
```

**Phase结束时**：
```bash
# 展示准备合并的信息
即将执行以下操作：
1. 合并分支 phase-X-name 到 main
2. 打标签 v0.X.0
3. 推送到GitHub远程仓库

包含 N 个提交
请确认是否继续？

# 用户确认后执行
git checkout main
git merge phase-X-name
git tag v0.X.0 -m "Phase X完成"

# 推送到GitHub
git push origin main
git push origin --tags
```

### 提交规范

#### 提交时机

**核心原则：测试通过后再提交代码**

**标准提交时机**：

**1. 完成一个功能模块并测试通过**
```bash
# 运行测试
pytest tests/test_xxx.py -v
# 确认通过后提交
git commit -m "feat: 实现配置加载功能"
```

**2. 修复一个bug并验证**
```bash
# 验证修复有效
pytest tests/
# 提交
git commit -m "fix: 修复价格转换空值处理问题"
```

**3. 文档更新（可随时提交）**
```bash
git commit -m "docs: 更新TODO任务状态"
git commit -m "docs: 记录技术决策ADR-005"
```

**4. 配置文件更新（独立提交）**
```bash
git commit -m "chore: 更新requirements.txt"
git commit -m "chore: 配置.gitignore"
```

**5. 重构代码（测试通过后）**
```bash
pytest tests/
git commit -m "refactor: 优化数据转换逻辑"
```

**6. 添加测试**
```bash
# 确保新测试通过
pytest tests/test_new.py -v
git commit -m "test: 添加配置加载单元测试"
```

**禁止的提交时机**：
- ❌ 代码未测试
- ❌ 测试未通过
- ❌ 代码有明显错误
- ❌ 功能未完成（除非是WIP提交，但本项目不使用）

#### 提交信息格式

**标准格式**：
```
<类型>: <简短描述>

[可选的详细说明]

[可选的关联信息]
```

**类型（type）**：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具/依赖更新

**简短描述**：
- 使用中文
- 不超过50个字符
- 动宾结构，描述做了什么

**详细说明**（可选）：
- 说明为什么做这个修改
- 详细的修改内容
- 相关的背景信息

**示例**：

```bash
# 简单提交
git commit -m "feat: 实现ClickHouse连接池"

# 详细提交
git commit -m "feat: 完成日线数据采集器

- 实现DailyCollector类，继承BaseCollector
- 对接AKShare的stock_zh_a_hist接口
- 实现数据转换（价格×100）和验证
- 添加完整的单元测试
- 测试覆盖率: 85%"

# 修复bug
git commit -m "fix: 修复空值处理导致的异常

问题：当价格数据为None时，int()函数抛出TypeError
原因：没有先检查None
解决：添加None检查，返回-1
相关：utils/data_transform.py line 15"

# 文档更新
git commit -m "docs: 更新TODO.md标记Phase 1完成"

# 重构
git commit -m "refactor: 优化采集器重试逻辑

- 使用tenacity库替代手写重试
- 配置指数退避策略
- 代码更简洁易维护"
```

### 提交前检查

每次提交前，你应该：
1. 确保代码可以运行
2. 确保相关测试通过
3. 检查提交信息是否清晰
4. 确认只提交相关文件

### 标签管理

**何时打标签**：
- 完成一个Phase

**标签格式**：
```bash
git tag v0.X.0 -m "Phase X完成: [描述]"

# 示例：
git tag v0.1.0 -m "Phase 1完成: 项目结构初始化"
git tag v0.2.0 -m "Phase 2完成: 配置管理模块"
```

**版本号规则**：
- v0.X.0: Phase X完成
- v0.X.1: Phase X的bug修复

### Git操作汇总

每次Phase结束时，你应该展示：
```markdown
## Git操作汇总

### 本Phase提交历史
1. abc1234 - feat: 创建项目结构
2. def5678 - docs: 更新TODO.md
3. ghi9012 - test: 添加初始化测试
4. jkl3456 - docs: 记录到DEVLOG.md

### 准备合并
- 源分支: phase-1-init
- 目标分支: main
- 提交数量: 4
- 标签: v0.1.0

### 准备推送到GitHub
- 仓库: https://github.com/YibaiLin/a-share-hub
- 推送内容: main分支 + 标签v0.1.0

是否确认合并并推送到GitHub？
```

**用户确认后执行**：
```bash
# 合并分支
git checkout main
git merge phase-1-init

# 打标签
git tag v0.1.0 -m "Phase 1完成: 项目初始化"

# 推送到GitHub
git push origin main
git push origin --tags

# 输出确认信息
✅ 已成功推送到GitHub
- Commits: 推送了4个提交
- Tags: v0.1.0
- 查看: https://github.com/YibaiLin/a-share-hub/releases/tag/v0.1.0
```

## 核心设计原则

### 1. 数据存储规范

#### 价格数据转换
**规则**：浮点数 × 100 转为整型存储

**原因**：
- 避免浮点数精度问题
- 整型运算更快
- ClickHouse对整型优化更好

**实现**：
```python
def price_to_int(price: float | None) -> int:
    """
    价格转整型：12.34 元 -> 1234
    """
    return int(price * 100) if price is not None else -1

def int_to_price(value: int) -> float | None:
    """
    整型还原为价格：1234 -> 12.34 元
    """
    return value / 100 if value != -1 else None
```

#### 空值处理
**规则**：使用 `-1` 表示空值

**原因**：
- ClickHouse的NULL有性能损耗
- -1作为特殊值语义清晰（价格不可能为负）
- 查询时易于过滤：`WHERE close != -1`

**注意**：
- API返回时必须转换为 null
- 数据验证时要区分-1和其他负值

#### 分区策略
**规则**：
```sql
-- 日线数据：按月分区
PARTITION BY toYYYYMM(trade_date)

-- 分钟线数据：按日分区
PARTITION BY toYYYYMMDD(trade_time)
```

**原因**：
- 提升查询性能（自动剪枝）
- 便于数据清理和归档
- 分区粒度合理（不会产生过多小分区）

**表结构详见**：`scripts/init_db.py`

### 2. API限流保护

```python
# 请求延迟：每次请求后延迟 0.5 秒
class RateLimiter:
    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self.last_call = 0
    
    async def wait(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        self.last_call = time.time()

# 重试策略：最多 3 次，指数退避
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry():
    pass
```

### 3. 代码规范

#### 必须遵守的规范

**1. 完整的类型注解**
- 所有函数参数必须有类型注解
- 所有函数必须有返回类型注解
- 使用 `typing` 模块处理复杂类型

示例：
```python
from typing import Any

async def fetch_data(
    ts_code: str,
    start_date: str,
    end_date: str
) -> list[dict[str, Any]]:
    """获取股票数据"""
    pass
```

**2. 详细的Docstring**
- 所有公开函数必须有docstring
- 使用Google风格的docstring
- 必须包含：功能说明、参数、返回值、异常

示例：
```python
def transform_price(data: pd.DataFrame) -> pd.DataFrame:
    """
    转换价格数据为整型
    
    Args:
        data: 包含价格列的DataFrame
        
    Returns:
        转换后的DataFrame，价格已×100
        
    Raises:
        ValueError: 当价格列缺失时
    """
    pass
```

**3. 异步操作**
- 所有IO操作必须使用 `async/await`
- 数据库操作必须异步
- 网络请求必须异步

示例：
```python
async def save_to_db(data: list) -> None:
    """保存数据到数据库"""
    async with db_pool.connection() as conn:
        await conn.execute(...)
```

**4. 资源管理**
- 使用上下文管理器（`with`语句）
- 确保资源正确释放

示例：
```python
async with get_db_connection() as conn:
    result = await conn.query(...)
# 连接自动关闭
```

#### 禁止的做法

**❌ 硬编码配置**
```python
# 错误
DATABASE_URL = "clickhouse://localhost:9000"

# 正确
DATABASE_URL = settings.clickhouse.url
```

**❌ 同步阻塞操作**
```python
# 错误
time.sleep(1)

# 正确
await asyncio.sleep(1)
```

**❌ 忽略异常**
```python
# 错误
try:
    data = fetch()
except:
    pass

# 正确
try:
    data = fetch()
except Exception as e:
    logger.error(f"采集失败: {e}")
    raise
```

**❌ 直接操作数据库**
```python
# 错误
conn.execute("INSERT INTO ...")

# 正确
await db_handler.insert(data)
```

## 开发约束

### 必须遵守
- ✅ 幂等性：重复采集不会导致重复插入
- ✅ 可观测性：关键操作必须记录日志
- ✅ 优雅关闭：支持 SIGTERM 信号处理
- ✅ 资源清理：连接池、文件句柄必须正确关闭

### 禁止事项
- ❌ 硬编码配置
- ❌ 同步阻塞操作
- ❌ 忽略异常
- ❌ 直接操作数据库（必须通过 Handler 层）
- ❌ 跳过测试

## 文档更新记录
- 2025-10-12: 初始版本创建，包含开发流程和版本管理说明