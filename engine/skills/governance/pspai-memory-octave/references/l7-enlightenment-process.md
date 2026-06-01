# L7 悟道引擎 — 执行流程详解

> 来源：`pspai-memory-octave` L7 段 · 首次实战 2026-05-29

---

## 五步执行法

### 第一步：全量并行读取

同时读取所有层的状态（不逐层串行，并行提速）：

| 读取项 | 工具 | 目的 |
|:-----|:-----|:-----|
| MEMORY.md | read_file | L1 热存内容+容量 |
| USER.md | read_file | L1 用户记忆 |
| MEMORY_INDEX.md | read_file | L2 标签索引 |
| archive/* 目录 | search_files(target=files) | L3 归档清单 |
| experience/* 目录 | search_files(target=files) | L4 经验产出 |
| skills_list | skills_list | L5 技能总数 |
| SOUL.md | read_file | L0 铁律 |
| 最近会话 | session_search | 上下文活动 |

### 第二步：跨层交叉分析

分析维度（不检查单层状态，只找跨层关系）：

| 分析维度 | 具体问题 | 发现的模式示例 |
|:-----|:-----|:-----|
| 标签增长速率 | 哪些标签的 L3 归档增长最快？ | 全在 5/28，24h 零新增 → 时间断崖 |
| 归档阻塞点 | L1→L3 管道哪里断了？ | L1 太小(5.7%)不触发迁移 → L4 死锁 |
| L1 冗余度 | MEMORY.md 中是否有 L0/L3 已覆盖的内容？ | 家族排行双重存储 SOUL.md |
| 管道断裂 | L3→L4 或 L4→L5 的触发条件是否可达？ | ≥3 阈值永远达不到 → 鸡生蛋死锁 |
| 技能覆盖率 | L5 技能有多少来自自动管道 vs 手动？ | 17/17 全手动 → L4→L5 管道空转 |
| 跨层联动 | 一层操作是否意外影响另一层？ | L6补录→L4解锁（联动发现） |

### 第三步：撰写悟道笔记

输出到 `archive/YYYY-MM-DD-l7-enlightenment-NN.md`，结构：

```markdown
---
date: YYYY-MM-DD
tags: [enlightenment, l7, ...]
source: L7悟道引擎 cron
version: N
---

# 悟道笔记 #NNN

## 发现1：标题
### 现象
### 根因
### 影响
### 建议修正

## 发现2：...

## 记忆系统健康度评分
| 层 | 状态 | 评分 | 说明 |
...

## 行动建议汇总
| 优先级 | 行动 | 目标层 | 可自动执行 |
...
```

### 第四步：更新 MEMORY.md（L1）

在 MEMORY.md 末尾追加 § 段摘要（≤10 行），格式：

```
§
L7悟道#NNN（日期）：发现摘要
(1) 🔴 核心问题 →
(2) 🟡 次要发现 →
→ 详见 archive/YYYY-MM-DD-l7-enlightenment-NN.md
```

**原则**：MEMORY.md 只存结论指针，详细分析在 archive。

### 第五步：更新 MEMORY_INDEX.md（L2）

1. 标签目录树新增 `enlightenment` 标签条目
2. 时间倒序表新增一行
3. 归档总数 +1
4. 去冗扫描记录追加一行

---

## 边界规则

| 可以做的 | 不可以做的 |
|:-----|:-----|
| 读取所有层（L0-L6） | 修改 SOUL.md（L0） |
| 写入悟道笔记到 archive（L3） | 直接修改 skill SKILL.md（L5）— 需用户批准 |
| 追加发现到 MEMORY.md（L1） | 删除任何归档文件 |
| 更新 MEMORY_INDEX.md（L2） | 跳过五步直接输出 |

---

## 首次实战教训（2026-05-29）

1. **并行读提速**：8 个 read_file/search_files 应同时发出，不要串行
2. **去重优先**：先检查 SOUL.md↔MEMORY.md 重复，这是最容易被忽略的浪费
3. **阈值可达性**：不只检查「是否达标」，还要检查「在当前数据量下是否可达」
4. **意外联动是金子**：L6→L4 的意外联动比计划中的流程更有价值——这是 emergent behavior
5. **写后验证**：悟道笔记写完后必须 `read_file` 验证 + 检查 MEMORY_INDEX.md 无重复条目
