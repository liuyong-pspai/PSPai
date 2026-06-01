#!/bin/bash
# harden_turn_count_guard.sh — 计数器硬化看门狗
# 硬化规则 #3：轮次计数每次回复后+1
# 检查 MEMORY.md 中的 turn_count 是否在合理时间内有变化
# cron: */10 * * * *

MEMORY_FILE="~/.hermes-agent/memories/MEMORY.md"
STATE_FILE="~/.hermes-agent/.turn_count_state"
LOG_FILE="~/.hermes-agent/logs/turn_count_guard.log"

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

    if [ "$count" -eq "$last_count" ] && [ "$elapsed" -gt 30 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ turn_count 停滞: $count（已${elapsed}分钟未变化）" | tee -a "$LOG_FILE"
        exit 1
    elif [ "$count" -gt "$last_count" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ turn_count 递增: $last_count → $count" >> "$LOG_FILE"
    fi
fi

echo "$count" > "$STATE_FILE"
exit 0
