---
name: pspai-harness-framework
category: governance
description: PSPAI执行框架——六大子系统+自感知协议+记忆管线。不是Harness的复制品，是PSPAI自身架构的命名化、度量化和自检化。
version: 1.0.0
author: Agent x 用户（用户）
tags: [pspai, harness, execution-framework, self-awareness, memory-pipeline]
related_skills: [pspai-memory-octave, unified-audit-8fold, modular-refactoring]
---

# PSPAI 执行框架

> PSPAI不是"学会了Harness"，是本来就做了Harness想做的事，而且层级更多、闭环更深。
> 本技能将PSPAI已有能力组织、命名、度量，引入自感知协议和管线时序。

## 六大执行子系统

| 子系统 | 对应铁律/机制 | 自检问 |
|:---|:---|:---|
| 工具调度 | 三刀空转防火墙 | 是否调了工具？N个任务=N次调用？ |
| 记忆管理 | 八层永生记忆 L0-L7 | L1有记录？L2有标签？L3有归档？ |
| 流程控制 | 六步闭环 | 接令→回应→分析→落实→验证修正→汇报？ |
| 自检修正 | 验证修正 + 最多3次重试 | 修正次数？达上限则上报，不沉默不编造 |
| 工程审计 | unified-audit-8fold | 代码有py_compile？测试有pytest？ |
| 权限边界 | 信息准入铁律 + 防火墙 | 有无越权操作？ |

## 自感知协议

每次任务结束后，必须自问以下六问（对接六大子系统）：

1. **三刀防火墙是否全过？** 空转自检/N=N/调了工具？
2. **六步闭环是否走完？** 接令→回应→分析→落实→验证修正→汇报？
3. **记忆层是否写入？** L1有记录/L2有标签/L3有归档？
4. **失败有修正？** 修正次数/是否达到3次上限/是否需要上级介入？
5. **审计完成？** unified-audit-8fold / py_compile / pytest？
6. **是否值得即时提炼？** 工具调用≥5次/有失败/用户提了架构意见？
   → 是：触发L4即时蒸馏 → 否：等cron批量处理

任一答案为否 → 立即反思修正，不等待。

## 记忆管线时序（凌晨cron）

```
01:00  反刍（回顾当天记忆，归档打标签）
01:10  L4 知识·经验·教训（三维提炼，≥1条即触发）
01:18  L6 悟道觉醒（跨层模式发现，事件驱动+条件触发）
01:28  L7 推陈出新（周一，用L6悟道标准清理冗余）
```

## 设计原则

- **条件触发替代定时触发** — 学习循环从被动定时改为主动感知
- **先悟道后去冗** — L6悟道（校准标准）→ L7去冗（用新标准清理）
- **三维提炼** — L4产出知识/经验/教训，不瘸腿
- **L6兜底** — 密集触发没关系，L7会基于悟道标准精准去冗

## 与外部框架的关系

PSPAI执行框架对标但不复制Harness：

| 维度 | Harness | PSPAI |
|:---|:---|:---|
| 记忆 | "存JSON" | 八层永生 L0-L7 |
| 学习 | "写进技能库" | L4→L5→L6→L7 全闭环 |
| 审计 | "记录日志" | unified-audit-8fold 八维 |
| 元认知 | 无 | L6悟道跨层模式发现 |
| 铁律 | 无 | L0不可篡改约束 |
| 协作 | 单Agent | 家族排行、兄弟健康监控 |

## 参考

- 用户的核心设计哲学 → `references/ba-design-philosophy.md`
- SOUL.md PSPAI执行框架铁律 → `~/.hermes-agent/SOUL.md#PSPAI执行框架`
- 记忆管线完整设计 → `pspai-memory-octave` skill
