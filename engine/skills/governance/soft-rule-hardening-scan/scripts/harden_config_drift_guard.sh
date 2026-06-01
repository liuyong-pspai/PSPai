#!/bin/bash
# harden_config_drift_guard.sh — 配置漂移看门狗模板
# 检测 SOUL.md 和 config.yaml system_prompt 关键参数是否一致
# 适用于硬化"改SOUL必须同步config"类规则

SOUL="${HOME}/.hermes-${AGENT_NAME}/SOUL.md"
CONFIG="${HOME}/.hermes-${AGENT_NAME}/config.yaml"
LOG_FILE="${HOME}/.hermes-${AGENT_NAME}/logs/config_drift_guard.log"

drift_found=false

# 1. 检查压缩阈值（SOUL: "压缩触发...≥X%" / config: "上下文≥X%"）
soul_threshold=$(grep -oP '压缩触发.*?≥\s*\K\d+' "$SOUL" 2>/dev/null | head -1)
config_threshold=$(grep -oP '上下文≥\K\d+' "$CONFIG" 2>/dev/null | head -1)

if [ -n "$soul_threshold" ] && [ -n "$config_threshold" ] && [ "$soul_threshold" != "$config_threshold" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 压缩阈值漂移: SOUL=${soul_threshold}% vs config=${config_threshold}%" | tee -a "$LOG_FILE"
    drift_found=true
fi

# 2. 检查 max_turns
soul_turns=$(grep -oP '超\K\d+(?=轮红色截断)' "$SOUL" 2>/dev/null)
config_turns=$(grep -oP 'max_turns:\s*\K\d+' "$CONFIG" 2>/dev/null)

if [ -n "$soul_turns" ] && [ -n "$config_turns" ] && [ "$soul_turns" != "$config_turns" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ max_turns漂移: SOUL=${soul_turns} vs config=${config_turns}" | tee -a "$LOG_FILE"
    drift_found=true
fi

# 3. 检查红色截断阈值
soul_red=$(grep -oP '>?\s*\K40(?=轮.*截断)' "$SOUL" 2>/dev/null | head -1)
config_red=$(grep -oP '>\K40(?=轮)' "$CONFIG" 2>/dev/null | head -1)

if [ -n "$soul_red" ] && [ -n "$config_red" ] && [ "$soul_red" != "$config_red" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 红色截断阈值漂移: SOUL=${soul_red} vs config=${config_red}" | tee -a "$LOG_FILE"
    drift_found=true
fi

if [ "$drift_found" = false ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ SOUL↔config 无漂移" >> "$LOG_FILE"
fi

[ "$drift_found" = true ] && exit 1
exit 0
