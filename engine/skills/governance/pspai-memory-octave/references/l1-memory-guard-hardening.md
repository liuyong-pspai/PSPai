# L1 记忆裂根硬化实战

> 2026-06-03 硬化完成——从纸面规则到硬连防护

## 背景

MEMORY.md 被 L6 悟道#004 定位为「无保护写入目标」——任何 agent 可通过 `write_file` 全量替换而不经过归档检查。2026-06-02 对话清理导致 MEMORY.md 从 12KB→1KB（-91%），6+知识块未归档即丢失。

## 硬化方案

在 `scripts/l1_memory_guard.py` 中新增两个硬连模式：

### check_file 模式

```bash
python3 l1_memory_guard.py check_file
```

监控 MEMORY.md **文件大小**（独立于 memory 工具配额）：
- 🟢 FILE_OK: ≤8KB 正常
- 🟡 FILE_WARN: ≥8KB 告警，建议迁移
- 🔴 FILE_HARD: ≥10KB 硬上限，需立即迁移

同时统计近24h内的新归档数，辅助判断管道是否通畅。

cron：每1小时执行一次。

### check_delete 模式

```bash
echo "$new_content" | python3 l1_memory_guard.py check_delete
```

写前对比新旧差异，拦截破坏性全量替换：

1. 差异 > 50% 且新内容 < 旧内容（缩减）→ 检查最近5min内是否有新归档
2. 无归档 → **拦截**（⛔ 破坏性写入拦截）
3. 有归档但归档大小 < 删除量的30% → **拦截**（不足覆盖）
4. 有归档且覆盖≥30% → 放行（⚠️ 大幅缩减，但已归档）

### 初次设计的教训

原始版本用 1h 窗口检查归档存在性，导致以下误放行：
- 如果1h内有任何归档（即使与待删除内容完全无关），也放行破坏性写入

修复：时间窗口缩至 5min + 新增归档总量覆盖率检查（≥30%）。

## 防护层级

```
Layer 0（纸面规则）: SOUL.md 铁律 "不删除只迁移"
Layer 1（硬连防护）: l1_memory_guard.py check_delete — 写入前拦截
Layer 2（文件监控）: l1_memory_guard.py check_file cron每1h — 文件大小看门狗
Layer 3（悟道审计）: L6 Cron八步流程第5步 — 铁律违规检测
```

## 关联

- pspai-memory-octave SKILL.md: 裂根警告 + 双重清理机制冲突
- archive/2026-06-03-l6-enlightenment-04.md: 裂根终极定位
- scripts/l1_memory_guard.py: 完整实现
