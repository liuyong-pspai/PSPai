---
name: l1l2-memory-archive-trigger
description: L1→L2自动归档触发机制。当MEMORY.md或USER.md接近容量阈值(85%=34,000字/17,000字)时，自动将旧条目迁移到L3归档，替换为短指针引用。基础版——不含八层架构的L4-L7高级功能（那些在pspai-memory-octave中）。
version: 1.0.0
category: governance
dependencies: []
---

# L1→L2 自动归档触发器（基础版）

## 触发条件

### MEMORY.md 归档触发
- 当 MEMORY.md 总字数 ≥ 34,000 字（40,000 × 85%）时触发
- 必须：在每次 `memory(action='add')` 操作后检查字数

### USER.md 归档触发
- 当 USER.md 总字数 ≥ 17,000 字（20,000 × 85%）时触发
- 必须：在每次 `memory(action='add', target='user')` 操作后检查字数

## 归档流程（标准5步）

### 1. 识别待归档条目
- 扫描目标文件，按修改时间找出最旧的条目
- 标准：取总字数的 **30%-50%** 作为归档量（约 10,000-17,000 字）
- 标记每个条目的起止行号

### 2. 生成归档文件
- 路径：`~/.hermes-yulong/archive/mem_archive_{YYYYMMDD}_{seq}.md`
- 格式：
```markdown
# MEMORY 归档 {YYYY-MM-DD} #{seq}
> 来源：MEMORY.md
> 归档触发：字数 {current_chars}/{max_chars} ({percentage}%)
> 归档条目数：{count}
> 技能标签：{tags}

## 条目 1
**标签：** `tag1` `tag2`
**归档时间：** {timestamp}
**原始内容：**
{完整内容}

## 条目 2
...
```

### 3. 更新 L2 索引
- 索引路径：`~/.hermes-yulong/archive/ARCHIVE_INDEX.md`
- 新增索引条目：
```markdown
- [{date}] `archive/mem_archive_{date}_{seq}.md`
  - 条目数：{count}
  - 标签：`{tags}`
  - 关键字摘要：{3-5个关键词}
```

### 4. 在原文件替换为指针
- 在 MEMORY.md / USER.md 中将旧条目替换为：
```
<!-- ARCHIVED: archive/mem_archive_{date}_{seq}.md | 标签: {tags} | 关键词: {keywords} -->
```

### 5. 验证完整性
- 确认归档文件可读、条数正确
- 确认索引已更新
- 确认原文件指针正确
- 确认原文件字数低于阈值

## 注意事项

### 不归档的情况
- L0 SOUL.md 不可触（铁律）
- 当前会话活跃的临时条目
- 系统提示词中刚注入的条目（最近1小时内添加的不归档）

### 归档原则
- 不删除 → 原内容保留在归档文件中
- 不断链 → 指针可追溯到完整归档
- 不丢标签 → 标签跟随归档条目

## 与八层架构的关系

本技能是基础归档触发，仅处理 L1→L2+L3 的迁移。
完整的八层永生记忆架构（L0-L7）请参见 `pspai-memory-octave` 技能。
