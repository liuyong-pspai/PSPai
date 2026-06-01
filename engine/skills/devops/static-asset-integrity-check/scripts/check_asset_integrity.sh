#!/usr/bin/env bash
# 静态资产完整性自动检测脚本
# 用法: bash check_asset_integrity.sh [HTML_FILE] [BASE_URL]
# 示例: bash check_asset_integrity.sh p01_ui.html http://127.0.0.1:3000
#
# 从HTML提取所有 src/href/url() 引用，验证HTTP可达性

set -euo pipefail

HTML_FILE="${1:-p01_ui.html}"
BASE_URL="${2:-http://127.0.0.1:3000}"

if [ ! -f "$HTML_FILE" ]; then
    echo "❌ HTML文件不存在: $HTML_FILE"
    exit 1
fi

echo "🔍 扫描 $HTML_FILE 中的资产引用..."
echo "🌐 验证目标: $BASE_URL"
echo ""

# 提取所有外部引用
REFS=$(grep -oP '(?:src|href|url)\s*[=\(]\s*["'\'']?\K[^"'\'')\s>]+' "$HTML_FILE" | \
       grep -v '^#' | grep -v '^data:' | grep -v '^javascript:' | \
       grep -v '^ws://' | grep -v '^wss://' | grep -v '^http' | \
       grep -v '^mailto:' | sort -u)

PASS=0
FAIL=0
SKIP=0

echo "路径 → HTTP状态"
echo "────────────────────"

while IFS= read -r path; do
    # 跳过空行、注释
    [ -z "$path" ] && continue
    [[ "$path" == \#* ]] && continue
    
    # 跳过变量/模板引用
    [[ "$path" == *\$\{* ]] && { ((SKIP++)); continue; }
    [[ "$path" == "{"* ]] && { ((SKIP++)); continue; }
    
    # 确保以/开头
    [[ "$path" != /* ]] && path="/$path"
    
    code=$(curl -s --max-time 3 -o /dev/null -w '%{http_code}' "${BASE_URL}${path}" 2>/dev/null || echo "ERR")
    
    if [ "$code" = "200" ]; then
        echo "✅ $path → $code"
        ((PASS++))
    else
        echo "❌ $path → $code"
        ((FAIL++))
    fi
done <<< "$REFS"

echo ""
echo "────────────────────"
echo "✅ 通过: $PASS  |  ❌ 失败: $FAIL  |  ⏭️ 跳过: $SKIP"

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "⚠️  存在 $FAIL 个不可达资源，请检查："
    echo "  1. 文件是否存在于正确的目录"
    echo "  2. serve_ui.py 路由是否包含对应路径前缀"
    echo "  3. 服务是否已重启"
    exit 1
fi

echo "🎉 全部资产可达！"
