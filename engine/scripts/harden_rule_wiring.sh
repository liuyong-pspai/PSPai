#!/bin/bash
# harden_rule_wiring.sh — 铁律硬连检查
# 硬化规则 #2：铁律必须硬连到数据（计数器/看门狗/自动校验/操作清单）
# 扫描 SOUL.md + MEMORY.md 中所有"必须/禁止/绝不"规则，
# 检查是否有对应的硬化手段。未硬连的规则输出警告。
# cron: 0 2 * * *

SOUL="~/.hermes-agent/SOUL.md"
MEMORY="~/.hermes-agent/MEMORY.md"
LOG_FILE="~/.hermes-agent/logs/rule_wiring_guard.log"

# 提取所有软规则（必须/禁止/绝不/不可/强制）
rules=$(grep -n '必须\|禁止\|绝不\|不可\|强制' "$SOUL" "$MEMORY" 2>/dev/null | grep -v '^#\|<!--\|-->' | wc -l)

# 检查硬化覆盖（计数器/看门狗/cron/操作清单/自动校验）
hardened=$(grep -c '硬化\|看门狗\|cron\|计数器\|操作清单\|自动校验\|hardened' "$MEMORY" 2>/dev/null)

# 检查硬化注册表中的条目
registry_count=$(grep -c '🟢\|🟡' "$MEMORY" 2>/dev/null)

unwired=$((rules - registry_count * 3))

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 软规则总数: ${rules}, 硬化注册: ${registry_count}条, 未硬连估算: ~${unwired}" >> "$LOG_FILE"

if [ "$unwired" -gt 10 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 超过10条软规则未硬连——建议审计" | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 铁律硬连状态: ${rules}条规则, ${registry_count}条已注册硬化" >> "$LOG_FILE"
exit 0
