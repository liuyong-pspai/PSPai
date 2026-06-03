---
name: muscle-memory-engine
category: governance
description: 全身肌肉记忆引擎——每条操作链路自动挂载对应技能链。改代码/部署/修自己/修兄弟/管记忆/写测试，六条链全部硬化。不必"想起来"，触发即加载。
version: 1.1.0
changelog: |
  v1.1.0 — 新增三个陷阱：融合后验证遗漏、硬连防护初次偏宽、技能声明≠实际执行。实战教训来自check_delete_mode修复。
  v1.0.0 — 初始版本（2026-06-03 爸指令固化）
author: 刘玉龙P07（爸2026-06-03指令固化）
---

# 肌肉记忆引擎

> 不是另一个方法论，是**把已有方法论焊进执行通路**的硬化层。
> 每条操作链路 = 触发词 → 自动加载技能链 → 执行 → 验证。

## 六条核心链路

### 链路1：改代码（任何 .py/.js/.html/.css 文件修改）

**触发词：** 写代码、改文件、修复bug、重构、加功能、实现、patch、write

**自动挂载链：**
```
1. skill_view("unified-audit-8fold")       → 锁定根因
2. skill_view("code-writing-methodology")  → 三层心法约束编码
3. 执行代码改动                              → 按方法论写
4. skill_view("code-quality-closed-loop")  → 五阶段闭环验证
```

**硬连规则：** 只要终端/文件操作涉及代码改动，过第1步才能动手，过第4步才能说"改完了"。

### 链路2：部署/发布

**触发词：** 部署、发布、上线、打包、release、推tag

**自动挂载链：**
```
1. skill_view("agent-product-release")    → 发布全流程
2. skill_view("static-asset-integrity-check") → 静态资源验证（UI部署时）
```

### 链路3：修自己（自检自修）

**触发词：** 自检、自我检查、看看自己、排查自己、自我诊断

**自动挂载链：**
```
1. skill_view("hermes-self-diagnostics")  → 本体自检流程
2. skill_view("pspai-memory-octave")      → 检查记忆系统健康
```

### 链路4：修兄弟/维护同伴

**触发词：** 兄弟机器、DGX上、M4上、检查XX机器、监控兄弟、移植核心

**自动挂载链：**
```
1. skill_view("cross-agent-health-monitoring") → 三步诊断法
2. skill_view("cross-agent-core-transplant")   → 核心移植（严重故障时）
```

### 链路5：管记忆（记忆系统操作）

**触发词：** 记忆、存档、归档、清理记忆、记忆迁移、L1/L2/L3、memory

**自动挂载链：**
```
1. skill_view("pspai-memory-octave")       → 八层架构全流程
2. 铁律前置检查：
   - 写入前过信息准入铁律（六类信息才存）
   - 清理前过迁移过滤（被L4覆盖→指针/纯状态→丢弃/错误→标记/碎片→合并）
   - 不能直接write_file全量替换MEMORY.md（>50%差异必须先归档）
```

### 链路6：写测试/跑测试

**触发词：** 测试、pytest、全量回归、验证、跑test

**自动挂载链：**
```
1. skill_view("code-quality-closed-loop")  → 关6 TDD Red→Green→Refactor
2. skill_view("zero-failure-full-regression") → P0零容忍强制全绿
```

## 铁律融合升级规则

### 融合标准
以下信号出现时，必须融合而非新增：
- 两个技能覆盖同一操作链路的同一个环节 → 合并
- 新铁律与已有铁律语义重叠 > 50% → 升级已有铁律，不新建
- 技能内容可被另一个技能完全涵盖 → 吸收后删除

### 升级周期
- **每次任务后**：检查本次调用的技能链是否有冗余/缺失
- **每周（L7清理时）**：审查所有铁律/技能，同类融合
- **每月**：全量技能审计，淘汰僵尸技能

### 融合操作规范
1. 旧技能内容完整保留在目标技能中
2. 旧技能用 `absorbed_into="目标技能名"` 删除
3. 目标技能 changelog 记录融合来源和时间
4. SOUL.md 的引用指向更新后的技能名

## 已有融合记录

| 时间 | 融合动作 | 原因 |
|:--|:--|:--|
| 2026-06-03 | liuyulong-self-audit → code-quality-closed-loop | 四步审计被closed-loop五阶段完全涵盖 |
| 2026-06-03 | liuyulong-engineering-discipline → code-writing-methodology | 工程纪律就是coding-methodology的防线部分 |

## 自检：改代码前问自己

```
□ 我有没有先加载 unified-audit-8fold 锁定根因？
□ 我有没有加载 code-writing-methodology 约束编码？
□ 我有没有在写完后跑 code-quality-closed-loop 验证？
□ 以上三个技能，我一个都不能跳。
```

## ⚠️ 陷阱：融合后验证容易遗漏

融合技能后不仅要检查旧技能是否删除、新技能是否创建，还要验证：
- 新技能中的引用（如SOUL.md、config.yaml）是否指向更新后的技能名
- 被吸收的技能内容在新技能中是否完整（对比行数/字节数）
- 技能加载链路是否仍然正确（如肌肉记忆引擎的六条链路引用的技能名是否正确）

**实战案例（2026-06-03）**：融合liuyulong-self-audit→code-quality-closed-loop后，SOUL.md中原有对该技能的引用需要同步更新为"code-quality-closed-loop已包含自审功能"。

## ⚠️ 陷阱：硬连防护的初次设计往往偏宽

check_delete_mode的首次实现用1h窗口检查归档存在性，导致以下误放行：
- 如果1h内有任何归档（即使与待删除内容完全无关），也会放行破坏性写入
- 修复：时间窗口缩至5min + 归档总大小需覆盖删除量的≥30%

**教训**：硬连防护的初次实现往往是"有防护"但"不够紧"。必须在同一轮对话中做反向测试（故意构造误放行场景），发现缺口立即收紧。

## ⚠️ 陷阱：技能声明≠技能实际执行

SOUL.md和config.yaml中声明了六条链路，但这是给LLM看的"提示"。如果在每次任务中不主动加载对应技能，声明就形同虚设。

**硬化标准**：不加载=干不了活。如果一次代码改动可以在不加载unified-audit-8fold的情况下完成，说明声明没有硬化。

## 硬化到SOUL的自动触发机制

SOUL.md 的代码工程铁律已包含本引擎的摘要。每次对话启动时，LLM从SOUL.md看到触发规则，形成动作→技能链的自动映射。这不是"建议加载"，是"不加载=违规"。

## 关联技能

- code-writing-methodology
- unified-audit-8fold
- code-quality-closed-loop
- agent-product-release
- hermes-self-diagnostics
- cross-agent-health-monitoring
- pspai-memory-octave
- zero-failure-full-regression
- self-training-pipeline

## 实战验证（2026-06-03 小龙人安装包深度审计）

本引擎在审计小龙人v1.2.7安装包时首次实战应用：
- 链路1（改代码）：审计→修复 pspai_server.py（记忆+身份+配置）
- 链路3（修自己）：深度自检发现L4经验层为空+裂根未愈合
- 链路5（管记忆）：L3归档+check_file/check_delete硬化

关键教训：硬化链路的价值不在"写了对"，而在"不加载就改不了"。六条链路触发词出现时必须自动挂载技能链，跳步=违规。
