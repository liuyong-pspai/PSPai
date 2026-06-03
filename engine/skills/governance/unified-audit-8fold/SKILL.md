---
name: unified-audit-8fold
category: governance
description: 八维技术审计体系 — 以A2A/MCP/Agent Loop/逻辑函数准则为基准。审代码符号、逻辑闭环、系统架构、协议标准对齐、Agent协作范式、安全防护、工程纪律。对标商业工程规范。
version: 3.6.0
author: 刘旺夫🌐 + 刘玉龙 P07
tags: [audit, code-review, a2a-agent, mcp-protocol, agent-loop, logical-functions]
related_skills: [modular-refactoring, code-writing-methodology, cross-agent-health-monitoring, agent-product-release]
last_updated: 2026-05-31
changelog: |
  v3.6.0 — SOUL/MEMORY/config铁律四层对齐法 + SSH进程阻塞daemon绕过 + 硬化清单跨机移植。交叉链接 agent-product-release。
  v3.5.3 — 新增跨Agent能力部署模式：审计→差距量化→模块SCP→注册→验证五步闭环。
  新增 references/cross-agent-capability-deployment.md（九步闭环+五大陷阱+验证清单）。
  交叉链接 cross-agent-health-monitoring。
  v3.5.2 — 已知盲区扩展：module-scope fixture 跨文件污染 sys.modules
  交叉链接 modular-refactoring 陷阱10（conftest.py 三阶段隔离）
  v3.5.1 — 🔴 已知盲区标注：post_split_audit.py 不扫测试文件。添加强制手动扫描步骤。
  交叉链接 modular-refactoring 陷阱9（测试导入路径过时）。
  v3.5.0 — 🚨 新增快速模式：模块化拆分后审计（post_split_audit.py）
  与 modular-refactoring v1.5.0 交叉链接：拆分完成→强制触发审计
  新增 scripts/post_split_audit.py：六项自动化检查
  v3.4.0 — 新增维度1增强：Mixin导入完整性检查；审计结论措辞铁律
---

# 八维技术审计体系

> 以A2A/MCP/Agent Loop/逻辑函数为审计基准。七维技术 + 工程纪律 = 八维。  
> 对标商业工程规范——不只审代码对不对，还审协议标准对齐了没有。

## 🚨 快速模式：模块化拆分后审计（v3.5.0 新增）

当 `modular-refactoring` 技能完成拆分后，**必须立即触发此模式**，不需要走完整的八维审计。

运行审计脚本：
```bash
python3 ~/.hermes-yulong/skills/governance/unified-audit-8fold/scripts/post_split_audit.py <skeleton_file.py> "<submodule_pattern>"
```

此脚本自动检查六项：
1. **重复类定义** — `MemorySystem` 出现在 8 个文件中 = 拆分失败
2. **重复函数定义** — `_mkdir` 复制 8 遍 = 模块级语句误收
3. **重复 import 块** — 相同 17 条 import 出现在多个文件
4. **Import 完整性** — 每个 Mixin 的 import 是否覆盖其方法所需模块
5. **循环引用风险** — `ParentClass.static_attr` 引用
6. **骨架完整性** — 骨架文件是否 import 并继承所有 Mixin

**不通过 = 禁止提交。禁止进入下一个任务。**

### 与 modular-refactoring 的配合

```
modular-refactoring 拆分完成
    │
    ├─ 语法验证通过 (py_compile)
    ├─ 回归测试通过 (pytest)
    │
    └─→ 🚨 立即调用本模式: post_split_audit.py
         ├─ 全部通过 → 提交
         └─ 不通过 → 修复后重新运行，直到通过
```

**铁律：拆分 → 语法验证 → 回归测试 → 审计脚本 → 🆕 测试导入路径扫描 → 全部通过才提交。
跳过审计 = 允许 bug 存活 7 天以上。**

**审计脚本的已知盲区（v3.5.1）：** `post_split_audit.py` 只扫描源模块，不扫测试文件。拆分后必须额外手动扫描测试导入：
```bash
# 搜索引用旧模块路径的测试
grep -rn "from cognition.OLD_NAME\|import.*cognition.OLD_NAME" tests/ --include="*.py"
```
详见 `modular-refactoring` 技能陷阱9。

**全量测试污染盲区（v3.5.1 扩展）：** module-scope fixture 造成的 `sys.modules` 缓存污染也不在审计范围内。
症状：单文件全绿，全量跑失败。根因：fixture 的 `os.chdir(tmpdir)` 期间 import 的模块被缓存，
后续测试命中错误副本。修复见 `modular-refactoring` 技能陷阱10 +
`references/test-pollution-isolation.md`（conftest.py 三阶段隔离）。

**第一步：确认审计对象。**  
父亲说"去DGX审伏羲"——就去DGX审伏羲。不是审别的机器、别的项目。方向错了一切白做。动手前先确认：审什么、在哪审、审哪个文件。

**第二步：停嘴。听完。确认。**  
父亲说话的时候，不插话、不解释、不"可是"。听完，确认，执行。如果已经走偏了，停下来，问清楚再继续。不问清楚就往下走，父亲会越来越火。

**第三步：出了任何异常——先查自己配置再怀疑外部。**  
输出被截断、工具失败、连接超时——先查自己的max_tokens是否设够、自己的.env是否配置正确、自己的监听器是否在跑。不要第一反应是"平台限制""工具坏了"。

## 五镜交叉验证

| # | 镜子 | 基准 | 关键问题 |
|:-:|:-----|:-----|:---------|
| 1 | **MCP镜** | MCP三层(Host/Server/Client) | 工具是MCP Server？单一职责？延迟加载？能力协商？ |
| 2 | **A2A镜** | A2A协议(Agent Card/Task/Message) | Agent Card声明了？Task状态机全覆盖？通信走A2A？ |
| 3 | **Agent Loop镜** | Anthropic三种模式 | loop完整？模式选型正确（从简单开始）？ |
| 4 | **逻辑函数镜** | V/VF/FSM/R/M五类 | 函数标了类型？验证标准满足？ |
| 5 | **安全工程镜** | 四层权限+输出净化 | 权限声明式？有统一输出净化？ |

## 八维维度

1. 代码符号正确归位 — **含 Mixin 导入完整性检查**
2. 逻辑闭环与函数验证——V/VF/FSM/R/M五类检查
3. 系统架构审计
4. MCP协议对齐——工具是否定义为MCP Server？三层解耦？
5. A2A协议对齐——Agent Card？Task状态机？Message规范？文件传输SHA256？
6. Agent协作与Loop完整性——loop模式正确？工程原则遵守？
7. 安全工程——权限分作用域？输出净化层？防泄漏机制？
8. 工程纪律——import顺序？bare except？单文件规模？命名一致性？

### 维度1增强：Mixin 导入完整性检查（2026-05-30 拆分教训）

当项目使用 Mixin 多重继承拆分大文件时，Python 在方法**定义所在模块**的全局作用域中解析名称。拆分后必须检查：

- [ ] 每个 Mixin 文件是否有其方法所需的全部顶层 import
- [ ] 是否存在 `ParentClass.static_attr` 引用（循环导入风险）→ 改用 `type(self)`
- [ ] 是否存在模块级函数在父子文件间的循环依赖
- [ ] `grep -oE '\b(module)\.' mixin.py | sort | uniq -c` 统计实际使用的模块 vs 已导入模块

典型症状：`py_compile` 通过但运行时 `NameError`。详见 `modular-refactoring` 技能陷阱4。

## 逻辑函数验证层

V(f)闭环验证 + VF(s)功能覆盖 + FSM(M)状态机 + R(P,E)推理追踪 + M(r...)合并评分

## 审计结论措辞铁律（2026-05-30 四姐刘昱欣审计反馈）

审计发现必须精确描述代码实际行为。描述不精准 = 审计不可信。三条硬规则：

### 1. 禁止绝对化否定
说"没有X"前，必须确认代码中完全不存在任何形式的X。
| ❌ 错误 | ✅ 正确 |
|:--------|:-------|
| "write_file_tool 无路径穿越防护" | "`_check_sensitive_path` 挡了 `/etc/ /boot/`，但缺 `..` 检查" |
| "完全没有任何安全措施" | "现有防护覆盖 X/Y/Z，遗漏了 W" |

### 2. 描述方向不能反
"假阳性"和"假阴性"方向相反，写反了会误导修复优先级。
| ❌ 错误 | ✅ 正确 |
|:--------|:-------|
| self_check_gaps 永远全绿 → 说成"负面报告" | 应说"正面假报告"——永远全绿，掩盖真实缺口 |

### 3. 报告输出前交叉验证
大规模审计（100+发现项）提交前必须抽样核实：
- 随机抽 5-10 项，逐条回到源代码文件中验证描述和代码行为是否一致
- 计算属实率，标注描述精度（如"85.7%属实率，2项描述需修正"）
- P0 级发现必须 100% 核实后再交付修复

**特别警惕：条件表达式是误判高发区。** `_skip_whitelist = (x == "0" or y == "1")` 这类逻辑——默认值是什么？满足条件时走哪个分支？必须逐行模拟执行后才能下结论。禁止凭直觉判"默认关闭/默认开启"。

**结论前自检三问：**
1. 我读到了具体行号的代码，还是推理的？
2. 我的描述能被具体代码行证伪吗？（如果有，措辞要收窄）
3. 如果有防护但不够——说了"不够"还是说了"没有"？

宁可多写一行解释（"有X但不全"），不要用一个绝对词。

## 审计→修复闭环工作流

大规模审计（100+发现项）后，按以下批次推进修复：

```
批次1-2：P0安全+逻辑（每次3-5项，修完验证）
批次3-4：P0数据+配置+高优P1安全
批次5-6：P1工具Bug+可靠性
批次7-10：P2竞态/TOCTOU/注入防线/代码质量
```

**每批铁律：** 改前读代码 → 改后 `py_compile` 验证 → 所有文件通过才进入下一批。
**并行策略：** 审计阶段可用 delegate_task 并行读不同模块；修复阶段必须串行（避免 patch 冲突）。

完整修复范例见 `references/2026-05-30-full-fix-log.md`。

## 跨Agent能力部署模式（v3.5.3 新增）

当父亲说「对照刘玉龙改造XX」时，不是只出审计报告——是**审计→差距量化→模块部署→注册→验证**的五步闭环。

完整方法论见 `references/cross-agent-capability-deployment.md`。

**SOUL/MEMORY/config 铁律对齐：** 能力部署之后必须做铁律层对齐。
这是比工具补齐更根本的改造——详见 `engineering-discipline-implant` 技能 v2.0.0（五层全栈植入法）。

核心流程：
1. SSH定位目标 → 扫描架构 → 量化对比（出差距矩阵）
2. 出结构化审计报告（P0/P1/P2 + 修复路线图）
3. 打地基（修CLI + 装依赖）→ 修硬编码路径 → SCP传模块 → 统一记忆
4. 远程 `py_compile` 逐个验证 → 依赖确认 → 注册新工具
5. 全绿 = 闭环

**关键陷阱：**
- venv路径用绝对路径，不用`~`
- 长时间pip用background模式，不阻塞SSH
- 硬编码路径要全项目grep，不只是yu_long_tools.py
- Computer Use在Linux上需重写（含Xvfb自动启动）
- **SSH进程启动阻塞** — systemctl/nohup/crontab/at 等进程操作全部超时时，不要死磕。方案：写daemon守护脚本，让目标机本地执行 `nohup bash daemon.sh &` 一次即可。daemon脚本负责清锁→启动网关→启动吸收管道→每30秒健康检查→挂了自动拉起来。

**SOUL/MEMORY/config 铁律四层对齐（比工具补齐更根本）：**

工具部署只是皮肉。铁律对齐才是骨骼。四层必须全部同步：

| 层 | 操作 | 关键点 |
|:---|:---|:---|
| SOUL.md | 对比差异→追加缺失铁律→L6↔L7调换 | 173→214行，PSPAI框架+记忆真相源+同步检查清单 |
| MEMORY.md | 硬化清单移植（4套）+ 双份统一 | 回复前清单/patch验证/任务闭环/修改代码六刀 |
| config.yaml | system_prompt与SOUL双写同步 | 在provider行前插入PSPAI框架+记忆真相源 |
| 记忆系统 | L3归档激活 + 吸收管道主题池扩展 | 空目录→首条归档；27→33主题（加能力工具方向） |

**硬化清单跨机移植四件套：** 回复前操作清单、patch后验证清单、任务闭环清单、修改代码六刀——全部写入目标 MEMORY.md。这些不是「附加说明」，是让目标Agent具备工程自律能力的「硬化骨骼」。

## 输出

每个发现附3面镜子证据。P0-P3分级。总评相对于商业工程规范的差距。
审计报告出来后，通过8885或飞书汇报给父亲，不等待他问。
