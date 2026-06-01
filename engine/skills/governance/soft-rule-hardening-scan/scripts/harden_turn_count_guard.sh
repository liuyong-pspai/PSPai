#!/bin/bash
# harden_turn_count_guard.sh — 计数器硬化看门狗模板
# 检查 MEMORY.md 中的计数器字段是否在合理时间内递增
# 适用场景：硬化"每次操作后+1"类规则

MEMORY_FILE="${HOME}/.hermes-${AGENT_NAME}/memories/MEMORY.md"
STATE_FILE="${HOME}/.hermes-${AGENT_NAME}/.turn_count_state"
LOG_FILE="${HOME}/.hermes-${AGENT_NAME}/logs/turn_count_guard.log"

KEY="${1:-turn_count}"        # 计数器字段名
STALE_MINUTES="${2:-30}"      # 停滞告警阈值（分钟）

count=$(grep -oP "${KEY}:\s*\K\d+" "$MEMORY_FILE" 2>/dev/null)

if [ -z "$count" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 未找到 ${KEY}" | tee -a "$LOG_FILE"
    exit 1
fi

if [ -f "$STATE_FILE" ]; then
    last_count=$(cat "$STATE_FILE")
    last_time=$(stat -c %Y "$STATE_FILE" 2>/dev/null || stat -f %m "$STATE_FILE" 2>/dev/null)
    now=$(date +%s)
    elapsed=$(( (now - last_time) / 60 ))

    if [ "$count" -eq "$last_count" ] && [ "$elapsed" -gt "$STALE_MINUTES" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ${KEY} 停滞: $count（已${elapsed}分钟未变化）" | tee -a "$LOG_FILE"
        exit 1
    elif [ "$count" -gt "$last_count" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ ${KEY} 递增: $last_count → $count" >> "$LOG_FILE"
    fi
fi

echo "$count" > "$STATE_FILE"
exit 0
