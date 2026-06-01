# 软规则硬化扫描 — 全集团部署路径

> 2026-05-30 兄弟Agent建立。用户令：扫完就硬化，硬化完就盯住。

---

## 技能文件（全族共用）

每台机器、每个AI实例加载同一个技能：`skill_view("soft-rule-hardening-scan")`

---

## DGX#1 — 兄弟Agent

| 类型 | 路径 |
|------|------|
| SOUL.md | `~/.hermes-agent/SOUL.md` |
| config.yaml | `~/.hermes-agent/config.yaml` |
| MEMORY.md | `~/.hermes-agent/memories/MEMORY.md` |
| 看门狗脚本目录 | `~/.hermes-agent/scripts/` |
| 看门狗日志目录 | `~/.hermes-agent/logs/` |

### 看门狗（4个）

| 脚本 | 硬化规则 | cron周期 |
|------|---------|:--------:|
| `harden_partial_view_guard.sh` | 文件操作「必须完整读取」 | */5分钟 |
| `harden_reply_quality_guard.sh` | 回复「只展示结论」 | */15分钟 |
| `harden_config_drift_guard.sh` | SOUL↔config配置漂移 | */30分钟 |
| `harden_restart_policy_guard.sh` | systemd Restart=always铁律 | 0 */2小时 |

---

## DGX#1 — Agent 🐉

| 类型 | 路径 |
|------|------|
| SOUL.md（生效） | `~/.hermes-agent/SOUL.md` |
| SOUL.md（旧版存档，已废弃） | `~/agent/SOUL.md` |
| config.yaml | `~/.hermes-agent/config.yaml` |
| MEMORY.md | `~/.hermes-agent/memories/MEMORY.md` |
| 硬化注册表 | MEMORY.md `## 🏗️ 硬化注册表` 章节 |
| 日志目录 | `~/.hermes-agent/logs/` |

### 玉龙看门狗（2个，2026-05-30部署）

| 脚本 | 硬化规则 | cron周期 |
|------|---------|:--------:|
| `harden_turn_count_guard.sh` | #3 轮次计数每次回复+1 | */10分钟 |
| `harden_config_drift_guard.sh` | #4 刀六·改SOUL必同步config | */30分钟 |

### 玉龙硬化注册表（8条，2条已硬化）

| # | 得分 | 状态 | 硬化手段 |
|:-:|:--:|:--:|:--|
| 1 | 64 | 🔴 | 六步闭环不可跳过 — 自动校验 |
| 2 | 63 | 🔴 | 铁律硬连数据 — 自动校验 |
| 3 | 60 | 🟢 | 轮次计数+1 — 计数器+看门狗 |
| 4 | 56 | 🟢 | 刀六配置同步 — 看门狗 |
| 5 | 56 | 🔴 | 刀一读两层 — 操作清单 |
| 6 | 54 | 🔴 | 刀二安全扫描 — 触发器 |
| 7 | 54 | 🔴 | 空转防火墙刀三 — 操作清单 |
| 8 | 50 | 🔴 | 空转防火墙刀一 — 操作清单 |

---

## DGX#2 — 伏羲超体 🐉

| 类型 | 路径 |
|------|------|
| SOUL.md | `/home/dgx-spark-02/.hermes-fuxi/SOUL.md` |
| config.yaml | `/home/dgx-spark-02/.hermes-fuxi/config.yaml` |
| MEMORY.md | `/home/dgx-spark-02/.hermes-fuxi/MEMORY.md` |
| 日志目录 | `/home/dgx-spark-02/.hermes/logs/` |
| 吸收器 | `/home/dgx-spark-02/fuxi-absorber/` |

连接：`ssh dgx2`（用户dgx-spark-02）

---

## 硬化执行清单（5步）

1. `skill_view("soft-rule-hardening-scan")`
2. `grep -n "必须\|禁止\|绝不\|不可\|一律\|强制\|不准" SOUL.md MEMORY.md`
3. 逐条打分：致命度(1-10) × 腐烂概率(1-10)
4. ≥50分立刻硬化：写看门狗 → 加cron → 写入注册表
5. 验证：`crontab -l | grep guard` + `ls scripts/`

---

> **用户铁律：修了要固化，固化了要盯住。软规则不加钢筋 = 迟早再垮。**
