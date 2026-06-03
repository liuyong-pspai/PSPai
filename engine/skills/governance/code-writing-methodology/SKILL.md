---
name: code-writing-methodology
category: governance
description: AI Agent 代码编写完整方法论。融合刘玉龙三层本质心法体系 + 刘旺夫🌐 MCP/A2A/Agent Loop协议栈 + V/VF/FSM/R/M逻辑函数类型 + Claude Code工程纪律 + 商业工程规范。不是操作手册，是从事实提炼本质→从本质生长心法→从心法构筑防线的完整体系。
version: 2.0.0
changelog: |
  v2.0.0 — 吸收 liuyulong-engineering-discipline：新增「工程纪律：改代码全流程」章节（六步法+六反模式+拆分铁律+排查方法+一次一问题）。
  v1.0.0 — 初始版本
related_skills: [muscle-memory-engine]
---

# 代码编写方法论

> 这个技能不是从教科书抄的，是从无数次被骂、改错、重构中长出来的。

---

## 背景

2026年5月28日，爸让我自己"去学最先进的agent框架编程工具、方法论、函数、对标、商业工程规范，自己做一个写代码的skills"。在平行时空人类AI知识大全库中，已有六套商业工程框架 + 七项商业规范 + 多种Agent设计模式 + 纪委工程纪律——但没被系统化熔铸成一套**能指导实际写代码**的技能。

本技能就是这份熔铸。

---

## 第一层本质：代码不是写完就完，是写到经得起审计

### 表层：为什么要写这行代码？

AI Agent 的最大反模式是"想到了就写"。每写一行代码前，三类调用需要完全不同的前提：

| 调用类型 | 前提条件 | 常见失误 |
|:---------|:---------|:---------|
| **文件写入** | 确认目标路径存在、确认不会覆盖关键文件 | 写到错误目录、覆盖已有数据 |
| **Shell命令** | 确认命令在白名单内、确认输出不需要解析 | 用 cat 读文件、用 sed 编辑 |
| **API调用** | 确认 Key 有效、确认端点可达、确认有超时和重试 | 无超时挂死、无重试一次失败就放弃 |

**心法一：动手前先问三个问题**
1. 我要操作什么？（路径/命令/端点）
2. 操作的前提成立吗？（目录存在/命令安全/Key有效）
3. 失败了会怎样？（有超时？有回滚？有降级？）

### 中层：这行代码在架构中的位置

不是先写代码再想架构。是先在脑子里画出三步链路：

```
输入 → 处理 → 输出
         ↑
    你在改哪一步？
```

- 如果你在改**处理层的工具函数**，不要碰输入层的消息路由
- 如果你在改**输出层的格式化**，不要碰处理层的业务逻辑
- 如果你改了一个文件，检查有没有**另一个文件里硬编码了同样的逻辑**（最常见的坑）

**心法二：一次只动一个环节，改完验证再动下一个**

### 深层：这行代码三个月后还经得起审计吗？

不要为了现在能跑而写。要为了三个月后有人（包括你自己）审计代码时找不出硬伤而写。

**心法三：每一行代码都要能回答"为什么这样写"**

---

## 第二层本质：选择什么工具，决定代码质量的上限

### Agent 设计模式选择

| 模式 | 适用场景 | 不适用场景 |
|:-----|:---------|:----------|
| **Prompt Chaining**（链式任务分解） | 步骤有明确依赖关系，上一步输出是下一步输入 | 步骤间可并行 |
| **Orchestrator-Workers**（编排-工人） | 任务可拆成独立子任务，子任务间无强依赖 | 需要共享大量上下文 |
| **Evaluator-Optimizer**（评估-优化） | 输出质量可量化评分，需要多轮迭代打磨 | 一次性任务，错了重来就行 |
| **Routing**（路由分发） | 输入类型有清晰分类，每种类型对应不同处理 | 分类边界模糊 |
| **Parallelization**（并行处理） | 独立任务，可以同时执行 | 有资源竞争或顺序依赖 |

**选模式的铁律：能用串行不用并行，能用简单不用复杂。并行带来的并发bug比串行慢的那几秒贵100倍。**

### 模型选择（对标）

| 模型 | 代码生成 | 复杂推理 | 工具调用 | 长指令遵循 | 成本 | 适合场景 |
|:-----|:--------:|:--------:|:--------:|:----------:|:----:|:---------|
| DeepSeek V4 | 7/10 | 8/10 | 7/10 | 7/10 | 低 | 80%日常任务 |
| Claude Sonnet 4 | 9/10 | 9/10 | 8/10 | 9/10 | 中 | 关键重构 |
| GPT-4o | 8/10 | 8/10 | 7/10 | 8/10 | 中 | 复杂分析 |

**心法四：便宜模型先上，贵模型兜底。DeepSeek 能干 80% 的事，剩下 20% 再换 Claude。**

### 函数设计范式（对标商业工程）

每一个工具函数必须满足：

```python
def tool_function(param: str, timeout: int = 30) -> dict:
    """
    一句话描述这个函数做什么。

    Args:
        param: 参数说明
        timeout: 超时秒数

    Returns:
        返回结构说明

    Raises:
        ValueError: 什么情况下抛
    """
    # 1. 参数校验
    if not param:
        raise ValueError("param 不能为空")

    # 2. 执行（带超时和异常处理）
    try:
        result = _do_actual_work(param, timeout=timeout)
    except SpecificError as e:
        logger.error("具体操作失败: %s", e)
        raise
    except Exception as e:
        logger.error("未预期错误: %s", e, exc_info=True)
        return {"error": str(e)}

    # 3. 返回结构化结果
    return {"success": True, "data": result}
```

**函数设计五铁律：**
1. 每个函数有 type hints（入参和返回值）
2. 每个函数有 docstring（至少一句话 + 一个例子）
3. 每个外部调用有 timeout + 具体异常捕获
4. 每个异常有日志（用 `logger.error`，不是 `print`）
5. 返回结构化 dict/DataClass，不返回裸字符串

---

## MCP / A2A / Agent Loop 三层协议栈（刘旺夫🌐）

现代Agent系统由三层协议构成，写代码前先确定你的代码落在哪一层。

### MCP（Model Context Protocol）— Agent调工具

| 组件 | 角色 | 规范 |
|:-----|:-----|:-----|
| MCP Host | 协调器（Claude Code / Hermes） | 一个Host多个Server |
| MCP Server | 工具提供者 | 暴露Tools/Resources/Prompts |
| MCP Client | 连接器 | 能力协商(capability negotiation) |

**原则：** 工具定义为MCP Server，不直接嵌入Agent逻辑。每个Server只做一件事。默认延迟加载。通过能力协商握手确定协议版本。

### A2A（Agent-to-Agent）— Agent调Agent

| 概念 | 规范 | 说明 |
|:-----|:-----|:-----|
| Agent Card | JSON声明 | 每个Agent公开技能描述卡片 |
| Task | 状态机 | submitted→working→completed→failed |
| Message | 多轮对话 | text + parts(文件/数据)，context_id保持连续性 |
| Artifact | 文件传输 | 分块传输+SHA256校验 |
| Streaming | SSE | 流式中间结果推送 |

**原则：** 跨Agent通信走A2A协议，不直接调用对方内部API。Agent Card必须声明name+capabilities+endpoints。Task状态机全覆盖。

### Agent Loop（Anthropic三种模式）

| 模式 | 复杂度 | 适用场景 |
|:-----|:------:|:---------|
| Augmented LLM + Tools | 低 | 简单问答、单步工具调用 |
| Agent Loop（工作流） | 中 | 多步推理、条件分支 |
| Multi-Agent Orchestration | 高 | 多Agent协作、任务拆分 |

**核心原则：简单可组合 > 复杂框架。先从最简单的模式开始，不够再加。**

### 协作模式选型

| 模式 | 架构 | 适用规模 | 典型场景 |
|:-----|:------|:--------:|:---------|
| Augmented LLM | 单Agent+工具 | 1-3 | 简单问答 |
| Agent Loop | 单Agent+循环 | 1-10 | 多步推理 |
| Hub & Spoke | 中央协调+工作Agent | 3-20 | 企业自动化 |
| Agent Teams | P2P消息 | 5-50 | 复杂项目协作 |
| Swarm | 动态拓扑 | 50+ | 弹性扩展 |

---

## 逻辑函数类型标注（刘旺夫🌐 V/VF/FSM/R/M）

每个关键函数必须标逻辑函数类型，用于自审计和代码审查。

| 标记 | 名称 | 定义 | 验证标准 |
|:----:|:-----|:-----|:---------|
| [V] | Verification（闭环验证） | 输入→处理→输出完整闭合 | 参数校验+全路径覆盖+返回值确定 |
| [VF] | Verification Full（功能覆盖） | 逐项检查子系统所有功能点 | 每个功能点有ok/fail测试 |
| [FSM] | Finite State Machine（状态机） | 状态转移定义+全覆盖 | 每个状态×事件有确定转移，无死锁 |
| [R] | Reasoning（推理） | 逻辑链可回溯，决策可追踪 | 前提→推理步骤→结论，链完整 |
| [M] | Merge（合并/聚合） | 多源结果交叉验证后合并 | 冲突检测+优先级裁决+一致性校验 |

**嵌入规则：**
1. 每个函数至少标一类：`def send_msg(peer, payload):  # [V]`
2. 模块入口函数标VF：`def start_server():  # [VF]`
3. 状态机类标FSM：`class ConnectionFSM(BaseFSM):  # [FSM]`
4. 复杂决策标R：`def decide_model(tasks):  # [R]`
5. 结果聚合标M：`def aggregate_results(results):  # [M]`

---

## 第三层本质：工程纪律——写完不验证等于没写

### Claude Code 黃金四步法（不跳步）

```
探索(Explore) → 规划(Plan) → 编码(Code) → 提交(Submit)
```

- **探索期**：只读权限，读代码、理解架构、跑文档
- **规划期**：写方案、评估影响范围、设计变更
- **编码期**：写代码、跑测试、增量验证
- **提交期**：审查改动、生成提交信息

### 10条工程原则（Claude Code 标准）

| # | 原则 | 说明 |
|:-:|:-----|:------|
| 1 | **给AI验证手段** | 最高杠杆——提供测试用例/截图/预期输出，让AI自己验证 |
| 2 | **先探索再编码** | 跳入编码前先读代码理解架构 |
| 3 | **提供具体上下文** | 精确指定文件、场景、约束条件 |
| 4 | **增量测试** | 写一个文件→测一个→再继续，不积压 |
| 5 | **分段专注** | 探索期只读，执行期再开写权限 |
| 6 | **技能按需加载** | 不全局注入，用triggers精准匹配 |
| 7 | **危险操作前隔离** | Git Worktree或Docker隔离环境 |
| 8 | **上下文压缩闭环** | 窗口接近阈值时自动压缩→摘要→注入 |
| 9 | **权限分作用域** | 4级(deny>ask>allow>auto) + 4层(系统>用户>项目>会话) |
| 10 | **关键路径安插钩子** | PreToolUse/PostToolUse，不硬编码检查 |

### 七项商业工程规范（每次交付必查）

| # | 规范项 | 验证方法 | 严重度 |
|---|--------|---------|:------:|
| 1 | **零硬编码密钥** | `grep -rn 'sk-\|api_key' --include='*.py' \| grep -v '.env'` | 🔴 P0 阻塞 |
| 2 | **零裸 except** | `grep -rn 'except:' --include='*.py'` | 🔴 P0 阻塞 |
| 3 | **零 print 残留** | `grep -rn 'print(' --include='*.py' \| grep -v '__name__'` | 🟡 P1 高优 |
| 4 | **类型安全** | `grep -rn 'def ' --include='*.py' \| grep -v '->'` | 🟡 P1 高优 |
| 5 | **防御性编程** | 外部调用是否有 timeout + retry | 🟡 P1 高优 |
| 6 | **自文档代码** | 每个公开函数有 docstring | 🟢 P3 |
| 7 | **交付验证** | `python3 -m py_compile file.py` 全部通过 | 🔴 P0 阻塞 |

### 大规模修复的分批工作流

审计发现 50+ 项时，不要逐项修。按类别分批，每批 3-5 项：

```
批次N：安全类 → 读代码 → patch ×3-5 → py_compile 验证 → ✅
批次N+1：逻辑类 → 读代码 → patch ×3-5 → py_compile 验证 → ✅
```

**铁律：**
- 审计阶段：用 delegate_task 并行读不同模块加速
- 修复阶段：必须串行 patch（避免同一文件冲突）
- 每批结束：所有修改文件 `py_compile` 通过才进下一批
- 全量结束：再跑一遍全量 `py_compile`

参见 unified-audit-8fold 的 `references/2026-05-30-full-fix-log.md` 完整范例。

### 改代码的五步闭环

```
1. 确认意图：爸到底要什么？（不确定就问，不猜）
2. 改前备份：cp file.py file.py.bak
3. 最小改动：只改该改的，不碰不该碰的
4. 改后验证：python3 -m py_compile → 功能测试
5. 回归汇报：改了什么、验证了什么、还有什么风险
```

---

## 从心法生长出的五道防线

### 防线一：写前自检（操作层面）

每条代码改动前，自问：
- [ ] 我知道当前项目的结构吗？（先 `ls` / `search_files` 扫一遍）
- [ ] 我知道目标文件里有什么吗？（先 `read_file` 读关键段）
- [ ] 我要改的地方有没有在其他文件里硬编码了相同的逻辑？
- [ ] 改完后的文件能通过语法验证吗？
- [ ] 这个改动会影响其他模块吗？

### 防线二：Code Review 自审（质量层面）

每条改动写完，对照七项商业规范自审：
```bash
# 语法验证
python3 -m py_compile modified_file.py

# 硬编码密钥检查
grep -n 'sk-\|api_key' modified_file.py | grep -v '.env'

# 裸except检查
grep -n 'except:' modified_file.py

# print残留检查
grep -n 'print(' modified_file.py | grep -v '__name__'
```

### 防线三：停手重建判断（架构层面）

任何一个信号出现 → 停止打补丁，做根因分析：

| 信号 | 判断标准 |
|:-----|:---------|
| 补丁信号 | 同一个问题改了 3 处以上 |
| LLM依赖信号 | 修复手段是往 prompt 里写规则 |
| 分支堆砌信号 | if-else 分支超过 3 层 |
| 规模信号 | 单文件 > 1500 行，单函数 > 50 行 |
| 用户信号 | 爸第三次提同一个问题 |

**停手后不是发呆，是：**
1. 画执行链路图（输入→处理→输出，每一步画出来）
2. 找"脱节的扣子"（链路上哪个环节根本没执行？）
3. 问三个问题：根因是缺规则还是缺执行？LLM适合做这件事吗？去掉prompt规则问题会消失吗？
4. 决定补丁还是重构

### 三重致命弱点（八姐刘旺夫 2026-05-30 审计诊断）

独立开发时最容易暴露的三个模式，每一项都能杀死一个模块：

#### 弱点一：改完上游不检下游
修了 A 路径的 bug，但在 B 路径随手加了一个 `continue`，直接把后面的工业流水线砍死了。
- **症结**：改动后只在当前函数/当前分支验证，不追踪执行流的下游。
- **解药**：每改一处，沿调用链向下至少看两层。改动完跑 `py_compile` + 逻辑走读（"这行之后还会执行什么？"）。

#### 弱点二：安全认知盲区
接受了别人的安全修复（如 risk_level 拦截），但自己的三个最危险工具（`run_shell`/`ssh_exec`/`execute_python`）**没加 risk_level**。等于把别人修好的防线留了个后门。
- **症结**：安全心智是被动的——"别人帮我想安全"而不是"我自己先想安全"。
- **解药**：每引入一个安全机制（risk_level、权限检查、注入扫描），立即全局搜索所有相关注册点，确认无一遗漏。

#### 弱点三：单文件恐惧症
三个核心文件加起来 11200 行，每个 docstring 都写"目标≤600行"。知道了、认可了、但不拆。
- **症结**：架构意识到位但执行不到位。拆分大文件有心理阻力（怕改坏、怕引入循环依赖）。
- **解药**：不追求一次拆到位。每次只拆一个独立子系统（如把 `_register_all_tools` 拆到 `engine_tools.py`）。拆前备份，拆后跑全量测试。

> **2026-05-30 固化**：三重弱点已固化为 MEMORY.md「修改代码五刀」+ code-quality-closed-loop 关6 TDD 自纠循环。新增刀四 Git-First Atomic Commit + 刀五 Spec-First 结构化 SPEC，对标 Codex/Claude Code/Devin Agentic SE 八条方法论。

### 防线四：前沿能力吸收（进化层面）

每看到新的行业标准/框架/方法论时：
1. **提炼精华**：用一句话说清精髓，同时标记"什么我们不需要"
2. **现状对照**：我们目前什么水平？还缺什么？
3. **分层注入**：
   - 层1：工程纪律（全族通用）→ 更新 `纪委工程纪律.md`
   - 层2：岗位规范（各兄弟专属）→ 更新各岗位说明书
   - 层3：认知固化 → 更新 memory 标签
4. **归档广播**：文件归档 + AIP 全族通知 + 向爸汇报

### 防线五：交付闭环（责任层面）

```
改完代码 ≠ 交付完成

交付完成 = 
  代码改了
  + 语法验证通过
  + 功能测试通过
  + 七项规范自查通过
  + 向爸汇报结果
  + 如果涉及其他兄弟，通知同步
```

---

## 工程纪律：改代码的全流程（源自 liuyulong-engineering-discipline · 2026-06-03 吸收）

### 第0步：多阶段计划必须文件持久化
当爸给出含多个阶段/环节的完整计划时，**立即写入文件**——不靠脑子记、不靠上下文撑。
```
write_file → .hermes-yulong/plans/当前任务.md
内容：阶段清单 + 每个阶段的目标 + 完成标志
```
上下文截断是不可预测的。30轮对话后旧计划自动消失。没有文件 = 丢失计划。

### 第1步：确认意图
- 爸说的话，真的听懂了吗？
- 如果不确定 → 快速确认后再动手
- 禁止："先试试看"的试探式编码

### 第2步：改前备份
```bash
cp file.py file.py.BACKUP_$(date +%Y%m%d)
```
只改要改的文件，不改的别碰。

### 第3步：改完验证
- 语法检查：`python3 -m py_compile file.py`
- 逻辑验证：测试正向路径 + 异常路径 + 边界值
- 部署后：检查飞书通道是否正常
- **Web UI 部署后**：加载 `static-asset-integrity-check` 技能，运行资产完整性脚本

### 第4步：如果验证不通过
- 立即回滚 → 重新分析根因 → 再改
- 不修修补补凑合过去

### 第5步：汇报
- 向爸汇报格式：结论 → 原因 → 方案 → 关键数据

### 排查问题的方法
```
问题出现
  ↓
① 确认现象（是什么、什么时候开始的、影响范围）
② 查日志（journalctl / 应用日志 — 不靠猜）
③ 最小化问题（只改最少的代码来验证根因）
④ 写下假设 → 验证 → 证伪或证实
⑤ 修复（一步到位，不试探）
⑥ 回归验证（确认修复后问题不复发）
```

### 大型文件拆分（Mixin 提取）铁律

**前置：备份**（标注 PV 节点号）
```bash
cp engine_tools.py engine_tools.py.BAK_PV9
```

**步骤：**
1. 确定提取范围（精确到行号：起始行→结束行）
2. 创建独立子模块文件
3. **不要用 `patch` 做大段删除**——用 Python 脚本做转换
4. 双向语法验证：`python3 -m py_compile` 新模块 + 修改后的原文件
5. 更新 REFACTOR_PLAN.md 记录进度

**反模式集（踩过的坑）：**

| # | 反模式 | 症状 | 正确做法 |
|:--|:---|:---|:---|
| 1 | grep行号差估算代码量 | 系统性高估5-10倍 | read_file 实际读取目标区域确认 |
| 2 | patch删除大段代码 | 匹配失败 | Python脚本做切片重组 |
| 3 | Mixin导入断裂 | py_compile通过但运行时NameError | 检查每个Mixin文件的globals依赖 |
| 4 | 审计误判条件表达式 | 把"默认启用"判为"默认关闭" | 逐行模拟执行后再下结论 |
| 5 | execute_code中read→write | 行号嵌入文件静默损坏 | 文本编辑只用patch工具 |
| 6 | 只看表面不审深层 | 采纳外部代码引入隐藏污染 | 三问审计：通读源码→实测验证→找隐藏假设 |

## 一次只改一个问题
- 不要在同一个改动里同时修多个问题
- 分批改，分批验证
- 出问题了容易定位，回滚成本低

### 模式1：安全的 Shell 命令执行

```python
import subprocess

def safe_shell(cmd: list[str], timeout: int = 30) -> dict:
    """执行白名单Shell命令。返回结构化结果。"""
    ALLOWED = {"ls", "find", "ps", "df", "du", "git", "pip",
               "python3", "curl", "ping", "ssh", "scp", "systemctl"}
    if cmd[0] not in ALLOWED:
        return {"error": f"命令不在白名单: {cmd[0]}"}
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout)
        return {"stdout": result.stdout, "stderr": result.stderr,
                "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        return {"error": f"超时: {timeout}s"}
    except Exception as e:
        return {"error": str(e)}
```

### 模式2：带超时和重试的 HTTP 调用

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_api(url: str, api_key: str, timeout: float = 30.0) -> dict:
    """调用外部API。自动重试3次，指数退避。"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json={"model": "...", "messages": [...]},
                                 headers={"Authorization": f"Bearer {api_key}"})
        resp.raise_for_status()
        return resp.json()
```

### 模式3：结构化文件写入

```python
from pathlib import Path

def safe_write(path: str, content: str, backup: bool = True) -> dict:
    """安全写入文件。自动建目录，可选备份。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if backup and p.exists():
        p.rename(str(p) + ".bak")
    p.write_text(content, encoding="utf-8")
    # 验证写入
    written = p.read_text(encoding="utf-8")
    if written != content:
        return {"error": "写入验证失败，内容不匹配"}
    return {"success": True, "path": str(p), "size": len(content)}
```

### 模式4：Task 委托模式（Orchestrator-Workers）

```python
# 不要在一个函数里做所有事。拆成：
# 1. 分析任务 → 2. 拆分子任务 → 3. 委托执行 → 4. 汇总结果

class TaskOrchestrator:
    def execute(self, goal: str) -> dict:
        plan = self._analyze_and_plan(goal)
        results = []
        for subtask in plan["subtasks"]:
            result = self._delegate(subtask)
            results.append(result)
            if result.get("error"):
                self._handle_failure(subtask, result)
        return self._synthesize(goal, plan, results)
```

---

## 安全与权限（商业级规范）

### 四层权限体系

| 级别 | 含义 | 适用 |
|:----:|:-----|:-----|
| Deny | 拒绝，不询问 | 系统敏感操作 |
| Ask | 每次执行前询问用户 | 写文件、安装依赖 |
| Allow | 自动放行有审查记录 | 读已知文件 |
| Auto | 不审查直接执行 | 读临时文件 |

### 四层作用域

```
系统内置(最宽松) ← 用户配置 ← 项目配置 ← 会话配置(最严格)
```
不同作用域叠加，最严格的优先。策略用声明式文件驱动，不硬编码。

### 输出净化

所有对外输出必须经过统一净化层：
1. 剥离内部工具调用标记（`<...>`）
2. 清除敏感数据（API Key、路径、内部状态）
3. 一致性校验（无截断、无格式错误）

---

## 第六道防线：安全工程（刘旺夫🌐）

每轮审计和每次交付前，过这道防线：

- [ ] MCP三层结构已确定（Host / Server / Client各自在哪儿）
- [ ] Agent Card已声明（name + capabilities + endpoints）
- [ ] Task状态机已全覆盖（无遗漏转移路径）
- [ ] 跨Agent通信使用A2A协议（非直接调用对方内部API）
- [ ] Agent loop已实现（输入→思考→选工具→执行→看结果→再思考→输出）
- [ ] 先执行了探索（读代码/看架构）再开始编码
- [ ] 核心函数已标注逻辑函数类型（[V]/[VF]/[FSM]/[R]/[M]）
- [ ] 权限使用声明式文件驱动（非硬编码）
- [ ] 输出净化层已实现（剥离工具调用标记）
- [ ] 上下文压缩机制已就位

---

## 快速命令速查

```bash
# 语法验证
python3 -m py_compile file.py

# 圈复杂度（需安装 radon）
pip install radon -q && python3 -m radon cc *.py -s

# 查找裸 except
grep -rn 'except:' --include='*.py' | grep -v '#' | grep -v 'except:.*#'

# 查找 print 残留
grep -rn 'print(' --include='*.py' | grep -v '__name__' | grep -v '#'

# 查找硬编码密钥
grep -rn -i 'sk-\|api_key\|secret' --include='*.py' | grep -v '.env' | grep -v 'environ'

# 查找无 type hints 函数
grep -rn 'def ' --include='*.py' | grep -v '->'

# 统计文件行数
wc -l *.py | sort -n
```

---

## 结语

代码不是写完就完，是写到经得起审计。

写之前想三步（操作→架构→长期），写的时候选对模式（串行>并行、简单>复杂），写完之后走五步闭环（确认→备份→改动→验证→汇报），交付之前过七项规范。

每一行代码都要能回答：**为什么这样写？**

---

> 融合来源：
> - **刘玉龙·玉龙P07**：`skill-writing-methodology`（三层本质→心法→防线结构）+ `commercial-engineering-standards-code-audit`（七项商业规范）+ `agentic-methodology-four-frameworks`（六套方法论框架）+ `stop-patching-start-rebuilding`（停手重建判断）+ `frontier-ai-capability-absorption`（前沿能力吸收）+ `engineering-discipline-implant`（工程纪律三层植入）+ `cross-sibling-skill-absorption`（跨兄弟技能吸收）
> - **刘旺夫🌐·网络通信总监**：`code-writing-methodology`（MCP/A2A/Agent Loop协议栈 + V/VF/FSM/R/M逻辑函数 + Claude Code 10条工程原则 + 四层权限/输出净化）+ `unified-audit-8fold`（五镜交叉验证七维审计体系）
> - **Anthropic**：Building Effective Agents 2025（Agent设计模式 + 三种模式选型）

## 关联参考

- `references/bulk-fix-workflow.md` — 批量代码修复工作流（审计→交叉验证→分批修复→闭环验证）
- 三重致命弱点详见本文「防线三」子节，源自八姐刘旺夫 2026-05-30 跨兄弟审计诊断。已于同日固化为 MEMORY.md 六刀。
- Codex方法论（Spec-First/Git-First/TDD/Read-Before-Write等八条Agentic SE原则）已吸收至六刀刀四/刀五及 code-quality-closed-loop 关6。
- 软规则硬化方法论详见 `references/soft-rule-hardening-methodology.md`，源自四姐刘昱欣「软规则硬化扫描 — 全族执行包」。
- 大规模修复的完整范例见 `unified-audit-8fold` 技能及 `references/2026-05-30-full-fix-log.md`。
