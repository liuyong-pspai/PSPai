#!/bin/bash
# 轮次计数器硬化看门狗（模板）
# 硬化规则：轮次计数每次回复后+1
# 检查 MEMORY.md 中的 turn_count 是否在合理时间内有变化
# 
# 部署：chmod +x && 加入 cron */10 * * * *
#
# 替换路径：<MEMORY_FILE> → 实际 MEMORY.md 路径
#           <STATE_FILE>  → 状态存储文件
#           <LOG_FILE>    → 日志文件
#           <STALE_MIN>   → 停滞告警阈值（分钟）

MEMORY_FILE="<MEMORY_FILE>"
STATE_FILE="<STATE_FILE>"
LOG_FILE="<LOG_FILE>"
STALE_MIN=30

count=$(grep -oP 'turn_count:\s*\K\d+' "$MEMORY_FILE" 2>/dev/null)

if [ -z "$count" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 未找到 turn_count" | tee -a "$LOG_FILE"
    exit 1
fi

if [ -f "$STATE_FILE" ]; then
    last_count=$(cat "$STATE_FILE")
    last_time=$(stat -c %Y "$STATE_FILE" 2>/dev/null)
    now=$(date +%s)
    elapsed=$(( (now - last_time) / 60 ))

    if [ "$count" -eq "$last_count" ] && [ "$elapsed" -gt "$STALE_MIN" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ turn_count 停滞: $count（已${elapsed}分钟未变化）" | tee -a "$LOG_FILE"
        exit 1
    elif [ "$count" -gt "$last_count" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ turn_count 递增: $last_count → $count" >> "$LOG_FILE"
    fi
fi

echo "$count" > "$STATE_FILE"
exit 0
