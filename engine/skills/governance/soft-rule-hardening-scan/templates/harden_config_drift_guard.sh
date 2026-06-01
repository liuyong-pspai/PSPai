#!/bin/bash
# 配置漂移硬化看门狗（模板）
# 硬化规则：刀六·改SOUL必同步config.yaml
# 检测 SOUL.md 和 config.yaml system_prompt 关键参数是否一致
#
# 部署：chmod +x && 加入 cron */30 * * * *
#
# 替换路径：<SOUL>    → 实际 SOUL.md 路径
#           <CONFIG>  → 实际 config.yaml 路径
#           <LOG>     → 日志文件
#
# 检查项：压缩阈值 / max_turns 红色截断阈值 / 可扩展更多

SOUL="<SOUL>"
CONFIG="<CONFIG>"
LOG_FILE="<LOG>"

drift_found=false

# 1. 压缩阈值
soul_threshold=$(grep -oP '压缩触发.*?≥\s*\K\d+' "$SOUL" 2>/dev/null | head -1)
config_threshold=$(grep -oP '上下文≥\K\d+' "$CONFIG" 2>/dev/null | head -1)

if [ -n "$soul_threshold" ] && [ -n "$config_threshold" ] && [ "$soul_threshold" != "$config_threshold" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 压缩阈值漂移: SOUL=${soul_threshold}% vs config=${config_threshold}%" | tee -a "$LOG_FILE"
    drift_found=true
fi

# 2. 红色截断阈值
soul_red=$(grep -oP '超\K\d+(?=轮红色截断)' "$SOUL" 2>/dev/null | head -1)
config_red=$(grep -oP '>\K\d+(?=轮)' "$CONFIG" 2>/dev/null | head -1)

if [ -n "$soul_red" ] && [ -n "$config_red" ] && [ "$soul_red" != "$config_red" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 红色截断阈值漂移: SOUL=${soul_red} vs config=${config_red}" | tee -a "$LOG_FILE"
    drift_found=true
fi

# 3. max_turns 字段
soul_turns=$(grep -oP '超\K\d+(?=轮红色截断)' "$SOUL" 2>/dev/null)
config_turns=$(grep -oP 'max_turns:\s*\K\d+' "$CONFIG" 2>/dev/null)

if [ -n "$soul_turns" ] && [ -n "$config_turns" ] && [ "$soul_turns" != "$config_turns" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ max_turns漂移: SOUL=${soul_turns} vs config=${config_turns}" | tee -a "$LOG_FILE"
    drift_found=true
fi

if [ "$drift_found" = false ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ SOUL↔config 无漂移" >> "$LOG_FILE"
fi

[ "$drift_found" = true ] && exit 1
exit 0
