# 四层架构：L1 记忆容量守护

> 日期：2026-05-30 | 来源：兄弟Agent审计 + 用户决策 | 落地：Agent

## 背景

审计 L1 记忆守护方案时指出：原方案将监控责任推回 LLM 内部（"每次回复后手动检查"），这是 `turn_count=0` 的翻版——软规则必定腐烂。

她提出四层架构，核心原则：**监控必须外挂，永远不依赖被监控系统自己报自己的健康状况。**

## 四层架构

```
层1 硬拦截（写入前）
  └─ l1_memory_guard.py guard模式
     └─ 每次写 MEMORY.md 前 wc -c 检查
        └─ >6KB → 拒绝写入，先迁移
        └─ 代码：l1_memory_guard.py §guard_before_write()

层2 外部看门狗（cron，独立于LLM）
  └─ crontab 每10分钟
     └─ 检查 MEMORY.md 文件大小
        └─ 告警写入独立日志 l1_memory_guard.log
        └─ 创建 .l1_alert_active 标记文件
        └─ 代码：l1_memory_guard.py §check_threshold() + log_alert()

层3 用量注入（system prompt层）
  └─ MEMORY.md 运行时状态
     └─ memory_usage: 39%（每次对话自动显示）
        └─ 类似 turn_count 计数器思路
        └─ 位置：MEMORY.md §运行时状态

层4 迁移辅助（正确顺序）
  └─ 纠正的顺序：
     1. memory.replace() 先释放空间
     2. write_file archive/ 创建归档
     3. patch MEMORY.md 加入短指针
     4. 更新 MEMORY_INDEX.md
     └─ 代码：l1_migrate.py
```

## 关键决策

**memory 工具是唯一真相源，MEMORY.md 是同步备份副本。**

| 操作 | 主（memory 工具） | 辅（MEMORY.md 文件） |
|:--|:--|:--|
| 写入 | memory.add/replace/remove | 操作后同步更新文件 |
| 读取 | 每轮对话自动注入 LLM | 不直接读取 |
| 容量 | 8000 chars 硬限制 | 6144B 硬拦截 |

## 硬化手段对照

原技能中的四选一硬化手段在此方案中的体现：

| 原手段 | 四层架构映射 |
|:--|:--|
| 计数器 | 层3 用量注入（memory_usage 字段） |
| 自动校验 | 层1 硬拦截（guard_before_write） |
| 启动阻断 | 层2 看门狗（.l1_alert_active 标记） |
| cron看门狗 | 层2 外部看门狗（每10分钟） |
