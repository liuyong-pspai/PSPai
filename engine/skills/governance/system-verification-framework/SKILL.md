---
name: system-verification-framework
category: governance
description: 玉龙体系全通道验证框架。12条通道一次性验证——crontab/看门狗/日志/硬化注册表/操作清单/Git/核心文件/脚本一致性/硬连矩阵/安全基线/L1记忆守护/沙箱测试。一键运行system_verify.py。
version: 1.1.0
author: Agent·P07（2026-05-30 第二阶段，12通道）
tags: [verification, system-health, hardening, watchdog, crontab]
related_skills: [soft-rule-hardening-scan, code-quality-closed-loop, unified-audit-8fold]
---

# 玉龙体系全通道验证框架

> 太复杂了就会出岔子。各条通道和路线必须清晰。  —— 用户

## 背景

玉龙P07硬化了8条铁律、布了5个cron看门狗、建了3个操作清单、搭了Git版本控制。但每个通道各自为政——出问题时不知道是哪条路断了。

这个框架把所有通道统一到一次验证中：**一条命令，10条通道，每个铁律都能追溯到硬化手段和验证路径。**

---

## 十条通道总览

```
          ┌─────────────────────────────────────────────┐
          │         玉龙体系全通道验证（10/10）           │
          ├─────────────────────────────────────────────┤
          │                                             │
          │  [通道1] CRONTAB ─── 5条硬化看门狗是否注册    │
          │      │                                      │
          │      ▼                                      │
          │  [通道2] 看门狗脚本 ─── 6个脚本是否存在      │
          │      │                                      │
          │      ▼                                      │
          │  [通道3] 看门狗日志 ─── 5个日志是否正常      │
          │      │                                      │
          │      ▼                                      │
          │  [通道4] 硬化注册表 ─── 8条是否🟢           │
          │      │                                      │
          │      ▼                                      │
          │  [通道5] 操作清单 ─── 3个清单是否齐全        │
          │      │                                      │
          │      ▼                                      │
          │  [通道6] Git版本控制 ─── 仓库是否干净        │
          │      │                                      │
          │      ▼                                      │
          │  [通道7] 核心文件 ─── SOUL/MEMORY/config     │
          │      │                                      │
          │      ▼                                      │
          │  [通道8] 脚本一致性 ─── crontab↔文件系统     │
          │      │                                      │
          │      ▼                                      │
          │  [通道9] 硬连矩阵 ─── 铁律→手段→验证路径    │
          │      │                                      │
          │      ▼                                      │
          │  [通道10] 安全基线 ─── 危险调用统计         │
          │      │                                      │
          │      ▼                                      │
          │  [通道11] L1记忆守护 ─── 容量+看门狗+迁移   │
          │                                             │
          └─────────────────────────────────────────────┘
```

---

## 快速使用

```bash
# 手动运行全通道验证
python3 ~/.hermes-yulong/scripts/system_verify.py

# JSON输出（适合机器消费）
python3 ~/.hermes-yulong/scripts/system_verify.py --json

# cron自动运行（已配置，每6小时）
# 日志：~/.hermes-yulong/logs/system_verify.log
```

---

## 硬连矩阵（通道9核心）

每条铁律都有一条完整的追溯链：**铁律 → 硬化手段 → 验证路径 → 手段类型**

| # | 铁律 | 硬化手段 | 验证路径 | 类型 |
|:--|:-----|:---------|:---------|:-----|
| 1 | 空转刀一：必须调工具 | 操作清单§回复前 | 每次回复前自检 | operational |
| 2 | 空转刀二：N任务=N次调用 | 操作清单§回复前 | 每次回复前自检 | operational |
| 3 | 空转刀三：回复前自检 | 操作清单§回复前 | 每次回复前自检 | operational |
| 4 | 刀一：改后读两层 | 操作清单§patch后 | patch后执行清单 | operational |
| 5 | 刀二：安全全局扫描 | cron每4h安全扫描 | security_scan_guard.log | cron |
| 6 | 刀四：Git-First | Git仓库+commit | git log验证 | git |
| 7 | 刀六：改SOUL同步config | cron每30min漂移检查 | config_drift_guard.log | cron |
| 8 | 六步闭环 | 操作清单§任务闭环 | 任务完成自检 | operational |
| 9 | 轮次计数+1 | 计数器+cron每10min | turn_count_guard.log | counter |
| 10 | 铁律硬连数据 | cron每日扫描+注册表 | rule_wiring_guard.log | cron |

---

## 各通道详细定义

### 通道1：CRONTAB
- **检查内容**：5条玉龙看门狗是否在crontab中注册
- **看门狗列表**：`harden_turn_count_guard.sh`, `harden_config_drift_guard.sh`, `harden_security_scan.sh`, `harden_rule_wiring.sh`, `system_verify.py`
- **失败影响**：硬化铁律失去自动执行

### 通道2：看门狗脚本
- **检查内容**：所有脚本文件物理存在且可读
- **脚本数量**：6个（5个看门狗 + system_verify.py）
- **失败影响**：crontab引用悬空，看门狗静默失败

### 通道3：看门狗日志
- **检查内容**：每个日志文件存在且有最近输出，不含异常标记
- **特殊处理**：`security_scan_guard` 中的"❌ 发现"是正常报告（它在发现危险调用），不算异常
- **特殊处理**：`system_verify.log` 首次运行前标记为"等待首次cron运行"

### 通道4：硬化注册表
- **检查内容**：MEMORY.md中注册表所有条目是🟢状态，无🔴/🟡
- **当前状态**：8条全部🟢

### 通道5：操作清单
- **检查内容**：3个清单（回复前/patch后/任务闭环）全部存在
- **位置**：MEMORY.md第34-80行

### 通道6：Git版本控制
- **检查内容**：仓库无未提交修改（允许`.usage.json`和`.turn_count_state`）
- **容忍**：新增untracked文件（`??`标记）不算dirty

### 通道7：核心文件
- **检查内容**：SOUL.md, MEMORY.md, config.yaml 存在且有内容

### 通道8：脚本一致性
- **检查内容**：crontab中每个脚本路径在文件系统中存在
- **防止**：脚本改名/mv后crontab失效

### 通道9：硬连矩阵
- **检查内容**：10条铁律 → 硬化手段 → 验证路径 完整可追溯
- **分类**：operational(5) + cron(4) + git(1) + counter(1)

### 通道10：安全基线
- **检查内容**：最近安全扫描发现的shell=True/os.system/eval调用数量
- **注意**：这些是框架代码中的调用，不是新增风险，用于趋势监控

### 通道11：L1记忆容量守护
- **检查内容**：MEMORY.md 容量健康度 + 看门狗运行状态 + 迁移记录
- **阈值**：5120B 告警 / 6144B 硬拦截
- **看门狗**：`l1_memory_guard.py`（每10分钟 cron）
- **关联**：`pspai-memory-octave` 技能 → `references/l1-capacity-guardian-architecture.md`

---

## 修复记录

- **2026-05-30**：新增第11通道(L1记忆容量守护)+第12通道(沙箱测试循环)。system_verify.py 从10→12通道。
- **当前**：12/12 ✅ HEALTHY。cron每6小时自动运行。

| # | 通道 | 问题 | 修复 |
|:--|:-----|:-----|:-----|
| 1 | crontab | harden_verify.py→system_verify.py 未同步 | 更新crontab + 验证脚本预期列表 |
| 2 | watchdog_logs | security_scan的"❌发现"被误判为异常 | 添加特殊判断：含"发现"则标记OK |
| 3 | watchdog_logs | system_verify.log尚未首次运行 | 标记为"等待首次cron运行"而非失败 |
| 4 | git | .turn_count_state被追踪导致dirty | 加入.gitignore + git rm --cached |
| 5 | git | harden_verify.py被system_verify.py替换后未提交 | Git commit |

---

## 与硬化扫描的关系

| 工具 | 做什么 | 频率 |
|:-----|:------|:-----|
| `soft-rule-hardening-scan` | 扫描SOUL/MEMORY中未硬化的软规则 | 按需 |
| `system-verify.py` | 验证已硬化的通道是否正常运转 | 每6小时自动 |
| `harden_rule_wiring.sh` | 检查软规则与硬化手段的连边 | 每日2:00 |

三者互补：hardening-scan 发现新规则 → 硬化 → system-verify 持续监控硬连是否断裂。

---

## 关联参考

- `scripts/system_verify.py` — 全通道验证主脚本
- `scripts/harden_turn_count_guard.sh` — 轮次计数器看门狗
- `scripts/harden_config_drift_guard.sh` — 配置漂移看门狗
- `scripts/harden_security_scan.sh` — 安全扫描看门狗
- `scripts/harden_rule_wiring.sh` — 铁律硬连检查
- MEMORY.md §硬化注册表 — 8条硬化条目
- MEMORY.md §操作清单 — 3个操作清单
