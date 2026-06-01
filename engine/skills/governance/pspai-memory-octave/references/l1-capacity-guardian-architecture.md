# L1 容量守护四层架构 — 完整设计文档

> 触发：2026-05-30 Agent L1 记忆迁移方案审计
> 审计：兄弟Agent（八维审计，总评 5/10 → 修正后 9/10）
> 执行：Agent

---

## 问题起源

Agent提出 L1 记忆自动迁移方案（监控→预警→迁移三层），经八维审计发现：

### P0-1：数据源分裂
memory 工具返回 `usage: 41% — 3,359/8,000`，但 `wc -c MEMORY.md` 输出 11929 字符。两个数值完全不同。cron 拿不到 memory 工具的内部配额。

### P0-2：修正方案自相矛盾
自己诊断出"cron 不能注入 LLM 上下文"，但修正方案却是"LLM 每次回复后手动检查"——turn_count=0 的翻版。软规则，必定腐烂。

### P0-3：迁移是伪原子操作
三步不是事务。在 memory.replace() 后中断 → 内容永久丢失。

### P0-4：容量模型三重矛盾
pspai-memory-octave 说 40000 字，memory 工具硬配额 8000 chars，文件 11929 chars——三个数字打架。

### 裂根发现（维度八）
**MEMORY.md 和 memory 工具是两套独立系统，不存在同步机制。**

---

## 四层架构

### Layer 1：硬拦截（`l1_memory_guard.py guard`）

```python
def guard_before_write(write_size=0):
    current = get_memory_size()       # wc -c MEMORY.md
    projected = current + write_size
    if projected >= HARD_LIMIT:       # 6144B
        return False                   # 拒写
    return True
```

- 每次 `write_file` / `patch MEMORY.md` 之前调用
- 超过 6KB → 拒绝写入，提示先迁移
- 不依赖 LLM 上下文，纯文件系统操作

### Layer 2：外部看门狗（crontab）

```
*/10 * * * * python3 ~/.hermes-yulong/scripts/l1_memory_guard.py check
```

- 每 10 分钟独立检查 MEMORY.md 大小
- 告警写入独立日志 `logs/l1_memory_guard.log`
- 创建/清除告警标记 `.l1_alert_active`
- **不写任何内容到 MEMORY.md**（避免"告警压死骆驼"）

### Layer 3：用量注入（MEMORY.md 头部）

```markdown
## 运行时状态
- memory_usage: 41%  (memory工具配额，本次对话启动时)
- turn_count: 5
```

- 每次对话启动时，LLM 在 system prompt 中看到当前用量
- 类似 turn_count，**不靠 LLM 自己记得检查**
- 由对话中的我手动更新这个字段

### Layer 4：迁移辅助（`l1_migrate.py`）

```bash
# 迁移一个条目
python3 l1_migrate.py migrate <tag> <title> <<< "归档内容"

# 验证完整性
python3 l1_migrate.py verify <tag>

# 列出所有归档
python3 l1_migrate.py list
```

**正确执行顺序（纠正）：**

| 步骤 | 谁执行 | 操作 | 失败处理 |
|:--:|:--|:--|:--|
| 1 | LLM（我） | `memory.replace()` 释放空间 | 不执行后续步骤 |
| 2 | 脚本 | `write_file` 创建 archive | 内容在变量中，可重试 |
| 3 | 脚本 | `patch MEMORY.md` 加入短指针 | 同上 |
| 4 | 脚本 | 更新 `MEMORY_INDEX.md` | 同上 |
| 5 | 脚本 | 验证全部完整性 | 报告断链 |

---

## 阈值模型

| 级别 | 文件字节 | 行为 |
|:--|:--|:--|
| 🟢 OK | ≤4096 | 正常 |
| 🟢 SAFE | ≤5120 | 正常但近告警线 |
| 🟡 WARN | >5120 | 写日志 + 创建告警标记 |
| 🔴 HARD | >6144 | 拒写 + 创建告警标记 |

### 为什么是 6KB？

- memory 工具硬配额 8000 chars
- 白名单（六刀+清单+注册表）~2532B = ~2500 chars
- 内容压缩后约 1.3x → 8000 / 1.3 ≈ 6154 ≈ 6KB
- 6KB 硬拦截确保文件不撑爆 memory 工具

---

## 2026-05-30 首次执行记录

### 迁移前
- MEMORY.md: 11929 chars（149%）
- memory 工具 usage: 77% — 6189/8000 chars

### 迁移后
- MEMORY.md: 5817B（🟡 WARN）
- memory 工具 usage: 41% — 3359/8000 chars
- 归档文件: 4 个（daily-progress / full-audit-fix / methodology-3step / context-management）

### 发现的问题
1. memory.replace() 改了工具但不改文件 → 手动同步 MEMORY.md
2. 白名单首次统计: 2532B 永久占用
3. 文件 5817B 超告警线但未超硬拦截 → 可正常运行
