---
name: pspai-eternal-memory
category: memory
description: PSPAI永生记忆体系基础层。不删除不丢失——MEMORY.md(40,000字热缓存)接近85%阈值时，将旧条目迁移到带标签的归档文件(L3)，替换为短引用指针。归档通过search_files/grep永可查。配合MEMORY_INDEX.md(L2)标签索引实现快速检索。已升级为八层架构(pspai-memory-octave)，本技能保留迁移操作细节。
---

# ⚠️ 已升级为 pspai-memory-octave（八层永生记忆）

> 本文档是 PSPAI 永生记忆的 **v1.0 版本**（二层层架构：热层 MEMORY.md → 冷层 archive）。
> **v2.0 已发布：`pspai-memory-octave`（八层永生记忆架构 L0-L7，含 cron 自动闭环）。**
> 此后所有记忆相关操作请以 `pspai-memory-octave` 为准。
> 
> 以下内容保留作为 v1.0 历史参考。

# PSPAI 永生记忆体系（v1.0 — 已升级）

## 核心原则

> **不删除，只迁移。满了打标签归档，永可查。**

MEMORY.md 是热缓存（每轮注入 LLM context），40,000 字符上限（85%触发迁移=34,000字符）。对标所有智能体中最大。
归档文件是冷存储（按需检索），无容量上限。是真正的长期记忆。

---

## 架构：二层记忆

```
热层（active）                 冷层（archive）
MEMORY.md          ←满了→     archive/YYYY-MM-DD-tag.md
每轮注入 LLM                   按需 search_files/grep
2200 字符上限                   无容量上限
依赖 LLM 理解                   依赖索引检索
```

---

## 触发条件

MEMORY.md 使用率 ≥ 85%（34,000/40,000 字符）时触发迁移。

## 迁移步骤

### 1. 选条目
从 MEMORY.md 中选出最旧或"已固化/不再高频使用"的条目。
**判断标准：**
- 一次性事件记录（如"某日修复了XX"）→ 优先归档
- 稳定架构事实（如"同机双网关"）→ 保留在热层
- 经验模式（如"websockets修复方法"）→ 保留在热层（高频复用）

### 2. 打标签
为被迁移的条目打 1-3 个标签：
- `#架构` `#网络` `#修复` `#API` `#路径` `#技能` `#` `#M4-2` `#教训`

### 3. 写归档文件
创建 `archive/YYYY-MM-DD-tag.md`，写入被迁移条目的完整内容：
```markdown
# 标签1 #标签2
> 归档时间：YYYY-MM-DD
> 来源：MEMORY.md 热层迁移

（完整原始内容）
```

### 4. 替换指    针
在 MEMORY.md 中将被迁移条目替换为：
```
→ 详见 archive/YYYY-MM-DD-tag
```

### 5. 更新索引
在 `archive/MEMORY_INDEX.md` 中添加一行：
```markdown
| #标签 | archive/YYYY-MM-DD-tag.md | 一句话概要 | YYYY-MM-DD |
```

---

## 检索方法

```bash
# 按标签查
grep -rl "#架构" ~/.hermes-agent/memories/archive/

# 按关键词查
grep -rn "websockets" ~/.hermes-agent/memories/archive/

# 全文搜索
search_files pattern="关键词" path=~/.hermes-agent/memories/archive/
```

---

## ⚠️ P0 级陷阱：漏掉写归档文件这步

`memory.replace()` 只能修改 MEMORY.md 的内容。**它不会自动创建 archive 文件到磁盘。**

2026-05-28 实际事故：4 条记忆被标记为"已迁移"，MEMORY.md 中替换为短指针，但 archive 文件从未写入。原始内容永久丢失，靠记忆重建。

**迁移 = 4 步缺一不可：**
1. `memory.replace()` — 替换 MEMORY.md 中的条目为短指针
2. `write_file()` — 将原始内容写入 archive/YYYY-MM-DD-tag.md
3. `read_file` 验证 — 确认 archive 文件存在且内容完整
4. 更新 `archive/MEMORY_INDEX.md` — 添加标签索引条目

## ⚠️ 记忆变更需网关重启

config.yaml 中的 memory_char_limit / user_char_limit / memory_migrate_threshold 等配置变更，需要**网关重启**才能被 AIAgent.__init__() 重新读取。

重启方案：`hermes-self-diagnostics` 技能内置 `scripts/restart_gateway.sh`，通过 `cronjob(no_agent=true, script=restart_gateway.sh)` 由外部调度器执行。Agent 无法从自身进程内重启（hermes gateway restart 杀掉父进程导致超时）。
