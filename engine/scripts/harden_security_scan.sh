#!/bin/bash
# harden_security_scan.sh — 刀二安全扫描看门狗
# 硬化规则 #6：安全机制·立即全局扫描
# 扫描代码库中高风险模式，检查是否有对应的安全措施
# cron: 0 */4 * * *

TARGET_DIR="~/.hermes-agent/skills"
YULONG_CODE="~/.hermes-agent"
LOG_FILE="~/.hermes-agent/logs/security_scan_guard.log"

risk_found=false

# 1. 检查 subprocess.run 是否使用 shell=False
shell_true=$(grep -rn 'shell\s*=\s*True' "$TARGET_DIR" "$YULONG_CODE" 2>/dev/null | grep -v '.git/' | wc -l)
if [ "$shell_true" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 发现 ${shell_true} 处 shell=True" | tee -a "$LOG_FILE"
    risk_found=true
fi

# 2. 检查是否有 os.system 调用（总是shell=True）
os_system=$(grep -rn '\bos\.system(' "$TARGET_DIR" "$YULONG_CODE" 2>/dev/null | grep -v '.git/' | wc -l)
if [ "$os_system" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 发现 ${os_system} 处 os.system()（风险：shell注入）" | tee -a "$LOG_FILE"
    risk_found=true
fi

# 3. 检查是否有 eval/exec
eval_count=$(grep -rn '\beval(' "$TARGET_DIR" "$YULONG_CODE" 2>/dev/null | grep -v '.git/' | wc -l)
if [ "$eval_count" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 发现 ${eval_count} 处 eval()（风险：代码注入）" | tee -a "$LOG_FILE"
    risk_found=true
fi

# 4. 检查路径穿越防护
path_traversal=$(grep -rn '\.\.' "$TARGET_DIR" "$YULONG_CODE" 2>/dev/null | grep -v '.git/' | grep -v '\.\.\/' | grep -E 'os\.path|open\(|Path\(' | grep -v '\.\./' | wc -l)
# 简化：检查 open/Path 调用中是否有 .. 但缺少 _check_sensitive_path
missing_guard=$(grep -rn 'open\(' "$TARGET_DIR" "$YULONG_CODE" 2>/dev/null | grep -v '.git/' | grep -v '_check_sensitive_path\|sensitive' | grep -F '..' | wc -l)
if [ "$missing_guard" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ ${missing_guard} 处文件操作含 .. 但缺路径穿越检查" | tee -a "$LOG_FILE"
    risk_found=true
fi

if [ "$risk_found" = false ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 安全扫描无风险" >> "$LOG_FILE"
    exit 0
fi

exit 1
