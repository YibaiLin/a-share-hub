# A-Share Hub - 开发流程指南

> 本文档面向开发者（你），说明如何使用Claude Code进行项目开发

## 快速开始

### Phase 0: 手动准备（首次，5分钟）

```bash
# 1. 创建项目目录
mkdir a-share-hub
cd a-share-hub

# 2. 初始化Git
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# 3. 创建文档目录
mkdir -p .claude prompts/{init,features,testing,maintenance}

# 4. 创建核心文档（从画布复制内容）
# 创建以下文件：
# .claude/CLAUDE.md
# .claude/TODO.md
# .claude/DECISIONS.md
# .claude/WORKFLOW.md (本文件)
# .claude/SESSION.md
# .claude/DEVLOG.md

# 5. 首次提交
git add .claude/
git commit -m "docs: 初始化项目文档"
git tag v0.0.0 -m "项目启动"

# 6. 创建GitHub仓库并关联
git remote add origin https://github.com/YibaiLin/a-share-hub.git
git push -u origin main
git push origin --tags
```

### Phase 1-8: 迭代开发

每个Phase遵循相同的流程。

---

## 标准开发流程

### 流程图

```
你：创建分支
    ↓
你：告诉Claude Code开始Phase X
    ↓
Claude Code：读取文档，确认状态
    ↓
你：确认继续
    ↓
Claude Code：展示执行计划
    ↓
你：确认计划
    ↓
Claude Code：实现代码 + 测试 + 提交
    ↓
Claude Code：展示结果汇总
    ↓
你：快速验证（30秒）
    ↓
    测试通过？
    ↓YES          ↓NO
你：确认完成    你：描述问题
    ↓              ↓
Claude Code：    Claude Code：
更新文档        分析并修复
合并分支          ↓
推送GitHub     重新验证
    ↓
完成！
```

---

## 详细操作步骤

### 1. 开始新的Phase

#### 1.1 创建功能分支
```bash
git checkout -b phase-X-name

# 示例：
git checkout -b phase-1-init
git checkout -b phase-2-config
```

#### 1.2 启动会话
在Claude Code对话框中输入：
```
请按照 prompts/phase-1-init.md 的要求实现代码。

先读取SESSION.md了解当前状态。
```

或者更简单：
```
继续Phase 1开发
```

#### 1.3 Claude Code确认状态
Claude Code会输出：
```markdown
## 会话状态确认

📍 当前位置：
- Phase: 1
- 任务: 项目初始化
- 进度: 0%
- 分支: phase-1-init

📋 本次计划：
- [ ] 1.1 创建项目目录结构
- [ ] 1.2 配置requirements.txt
- [ ] 1.3 配置.gitignore

请确认是否继续？
```

#### 1.4 你确认
```
继续
```

---

### 2. Claude Code工作中

#### 2.1 Claude Code展示计划
```markdown
## 执行计划

### 将要创建的文件
- config/__init__.py
- config/settings.py
- requirements.txt
- .gitignore

### 实现思路
1. 创建目录结构
2. 配置依赖文件
3. 运行测试验证
```

#### 2.2 你确认计划
```
OK，开始实现
```

#### 2.3 Claude Code实现并测试
这个过程你不需要做什么，等待即可。

#### 2.4 Claude Code展示结果
```markdown
## 执行结果

### 已创建的文件
- config/__init__.py
- config/settings.py
- requirements.txt
- .gitignore

### Git提交
- abc1234 - chore: 创建项目结构
- def5678 - chore: 配置依赖文件

### 测试结果
- 通过: 5个
- 失败: 0个

### 需要人工验证
1. 检查目录结构是否完整
2. 验证requirements.txt内容
```

---

### 3. 你验证结果

#### 3.1 快速验证（30秒）
```bash
# 方式1：运行测试
conda activate alpha
pytest tests/ -v

# 方式2：简单检查
ls -la config/
cat requirements.txt

# 方式3：手动测试
python -c "from config.settings import settings; print(settings.app_name)"
```

#### 3.2 结果判断

**✅ 测试通过**
```
测试通过，继续
```

**❌ 测试失败**
```
Phase 1执行失败，错误信息：
[粘贴错误信息]

请帮我分析并修复
```

---

### 4. Phase完成

#### 4.1 Claude Code更新文档
自动更新：
- SESSION.md
- DEVLOG.md
- TODO.md

#### 4.2 Claude Code准备合并
```markdown
## Git操作汇总

### 本Phase提交历史
1. abc1234 - chore: 创建项目结构
2. def5678 - chore: 配置依赖文件
3. ghi9012 - docs: 更新文档

### 准备合并
- 源分支: phase-1-init
- 目标分支: main
- 提交数量: 3
- 标签: v0.1.0

### 准备推送到GitHub
- 仓库: https://github.com/YibaiLin/a-share-hub
- 推送内容: main分支 + 标签v0.1.0

是否确认合并并推送？
```

#### 4.3 你确认
```
确认
```

#### 4.4 完成
```markdown
✅ Phase 1 完成

- 已合并到main分支
- 已打标签v0.1.0
- 已推送到GitHub

查看: https://github.com/YibaiLin/a-share-hub/releases/tag/v0.1.0

下次会话将继续Phase 2。
```

---

## 常见场景

### 场景1：中途遇到问题

**问题**：代码测试失败
```
Phase 2执行出现问题：
pytest tests/test_config.py失败

错误信息：
[粘贴完整错误堆栈]

环境：
- Python 3.11.13
- pydantic-settings 2.1.0
```

**Claude Code**：分析问题并给出修复方案
```
问题分析：...
解决方案：...
```

**然后修复**，你再次验证。

---

### 场景2：需要调整计划

**你**：
```
Phase 2的计划需要调整：
- 原计划：实现4个子任务
- 调整为：先完成前2个，后2个放到Phase 2.1

请更新TODO.md
```

**Claude Code**：更新TODO.md并确认调整后的计划

---

### 场景3：跨天继续开发

**第二天开始**
```
继续昨天的开发
```

**Claude Code**：
```markdown
已读取SESSION.md和DEVLOG.md

昨天状态：
- 完成Phase 2的60%
- 当前任务：2.3 添加配置测试
- 遇到的问题：[已解决]

今天计划：
- 完成剩余的2.3和2.4任务
- 预计耗时：1小时

是否继续？
```

---

### 场景4：Phase中途结束会话

**你**：
```
今天到这，保存状态
```

**Claude Code**：
```markdown
## 会话总结

本次完成：
- ✅ 任务2.1
- ✅ 任务2.2
- ⏸️ 任务2.3进行中（50%）

已更新SESSION.md，记录了：
- 当前进度
- 遇到的问题
- 下次继续的任务

⏸️ Phase 2未完成，暂不推送GitHub
📌 下次会话继续2.3任务

所有更改已提交到phase-2-config分支。
```

---

## Git操作参考

### 你需要做的Git操作

**只有Phase开始时创建分支**：
```bash
git checkout -b phase-X-name
```

**其余Git操作都由Claude Code完成**：
- ✅ git add
- ✅ git commit
- ✅ git merge
- ✅ git tag
- ✅ git push

---

## 环境配置

### Windows Terminal + Miniconda

```powershell
# 激活conda环境
conda activate alpha

# 确认Python版本
python --version  # 应该是3.11.13

# 如需重装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 启动API（后续Phase）
uvicorn api.main:app --reload
```

---

## 时间预估

| Phase | 名称 | 预计耗时 |
|-------|------|----------|
| Phase 0 | 手动准备 | 5分钟 |
| Phase 1 | 项目初始化 | 10分钟 |
| Phase 2 | 配置管理 | 15分钟 |
| Phase 3 | 核心模块 | 20分钟 |
| Phase 4 | 数据库初始化 | 15分钟 |
| Phase 5 | 基础采集器框架 | 25分钟 |
| Phase 6 | 日线采集器+存储 | 30分钟 |
| Phase 7 | API接口 | 30分钟 |
| Phase 8 | 任务调度 | 25分钟 |
| **总计** | | **~2.5小时** |

---

## 文档查看指南

### 你需要经常看的文档

**开发时**：
- `TODO.md` - 了解整体进度
- `SESSION.md` - 了解当前状态
- 本文档 - 遇到操作问题时查阅

**决策时**：
- `DECISIONS.md` - 查看已有决策

**回顾时**：
- `DEVLOG.md` - 查看开发历史
- GitHub commits - 查看代码变更历史

### Claude Code需要看的文档

- `CLAUDE.md` - 执行指南（最重要）
- `TODO.md` - 任务范围
- `SESSION.md` - 当前状态
- `DEVLOG.md` - 历史记录

---

## 快速命令参考

```bash
# 创建新Phase分支
git checkout -b phase-X-name

# 查看当前状态
git status
git log --oneline -5

# 测试
pytest tests/ -v                    # 运行所有测试
pytest tests/test_xxx.py -v        # 运行特定测试
pytest --cov=. tests/              # 测试覆盖率

# 查看文档
cat .claude/SESSION.md             # 当前状态
cat .claude/TODO.md                # 任务清单
git log --oneline --graph          # Git历史
```

---

## 最佳实践

### DO ✅

1. **每次会话开始时让Claude Code读取SESSION.md**
   ```
   继续开发（先读取SESSION.md）
   ```

2. **快速验证，不要深度审查**
   - 看测试结果
   - 快速检查文件
   - 有问题立即提出

3. **明确描述问题**
   ```
   # 好的问题描述
   Phase 2测试失败
   错误：KeyError: 'database'
   文件：config/settings.py line 23
   
   # 不好的
   代码不工作
   ```

4. **及时更新DECISIONS.md**
   - 做出技术选型后立即记录
   - 让Claude Code帮你写

5. **Phase完成后推送到GitHub**
   - 保持远程仓库同步
   - 便于备份和协作

### DON'T ❌

1. **不要跳过确认步骤**
   - Claude Code展示计划时，看一眼再确认

2. **不要一次做太多Phase**
   - 一个一个来，逐步推进

3. **不要忽略测试失败**
   - 立即修复，不要带着问题继续

4. **不要手动修改Git历史**
   - 让Claude Code管理Git

5. **不要在会话中途突然切换任务**
   - 完成当前Phase再切换

---

## 故障排查

### 问题：Claude Code不记得上次做了什么

**原因**：没有读取SESSION.md

**解决**：
```
请先读取SESSION.md，然后继续
```

---

### 问题：测试一直失败

**步骤**：
1. 复制完整错误信息给Claude Code
2. 描述你尝试过的解决方法
3. 提供环境信息
4. 让Claude Code分析并修复

---

### 问题：分支混乱

**预防**：
- 每个Phase用独立分支
- Phase完成后立即合并
- 不要在main分支直接开发

**恢复**：
```bash
# 查看当前分支
git branch

# 切换到main
git checkout main

# 如果需要，重置到某个tag
git reset --hard v0.X.0
```

---

## 项目里程碑

- ✅ v0.0.0: 项目启动，文档完成
- ⏸️ v0.1.0: Phase 1 - 项目初始化
- ⏸️ v0.2.0: Phase 2 - 配置管理
- ⏸️ v0.3.0: Phase 3 - 核心模块
- ⏸️ v0.4.0: Phase 4 - 数据库初始化
- ⏸️ v0.5.0: Phase 5 - 基础采集器
- ⏸️ v0.6.0: Phase 6 - 日线采集器
- ⏸️ v0.7.0: Phase 7 - API接口
- ⏸️ v0.8.0: Phase 8 - 任务调度
- 🎯 v1.0.0: 第一版发布

---

## 总结

**你的角色**：
- 创建分支
- 告诉Claude Code做什么
- 快速验证结果
- 确认关键操作

**Claude Code的角色**：
- 读取文档了解状态
- 实现代码和测试
- 管理Git操作
- 更新文档

**协作方式**：
- 你专注于需求和验证
- Claude Code专注于实现
- 通过文档传递上下文

---

**现在可以开始Phase 0了！** 🚀