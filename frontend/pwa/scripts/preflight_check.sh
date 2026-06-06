#!/bin/bash
# ============================================================
# 小龙人手机版 启动前验证脚本
# 功能：JS语法检查 + 资源完整性校验
# 未通过则拒绝启动服务器
# ============================================================
set -e

HTML_DIR="/home/yongliu/桌面/小龙人开源应用层/frontend/pwa/html"
ERRORS=0

echo "[preflight] 小龙人手机版启动前验证..."
echo ""

# === 1. 检查核心JS文件是否存在 ===
echo "[1/4] 检查核心文件..."
for f in "xiaolongren-core.js" "plugin-loader.js" "tools.js" "sensors.js" "media.js" "search.js"; do
    if [ -f "$HTML_DIR/$f" ]; then
        echo "  ✓ $f ($(wc -c < "$HTML_DIR/$f") bytes)"
    else
        echo "  ✗ $f 缺失!"
        ERRORS=$((ERRORS+1))
    fi
done

# === 2. JS语法检查（用node或python） ===
echo ""
echo "[2/4] JS语法检查..."
if command -v node &>/dev/null; then
    # node可用，用-c做严格检查
    for f in "xiaolongren-core.js" "plugin-loader.js" "tools.js" "sensors.js" "media.js" "search.js" "evolution.js"; do
        jsf="$HTML_DIR/$f"
        [ -f "$jsf" ] || continue
        if node -c "$jsf" 2>/dev/null; then
            echo "  ✓ $f 语法通过"
        else
            echo "  ✗ $f 语法错误!"
            ERRORS=$((ERRORS+1))
        fi
    done
elif command -v python3 &>/dev/null; then
    # 用python做基本语法验证
    for f in "xiaolongren-core.js" "plugin-loader.js" "tools.js" "sensors.js" "media.js" "search.js" "evolution.js"; do
        jsf="$HTML_DIR/$f"
        [ -f "$jsf" ] || continue
        if python3 -c "
import re
with open('$jsf') as f:
    c = f.read()
# 检查基本结构：括号匹配
opens = c.count('{') + c.count('[') + c.count('(')
closes = c.count('}') + c.count(']') + c.count(')')
if opens != closes:
    exit(1)
" 2>/dev/null; then
            echo "  ✓ $f 括号匹配"
        else
            echo "  ✗ $f 括号不匹配!"
            ERRORS=$((ERRORS+1))
        fi
    done
else
    echo "  ⚠ 既无node也无python3，跳过语法检查"
fi

# === 3. 检查首页引用的资源是否都在 ===
echo ""
echo "[3/4] 检查HTML引用的资源..."
# 提取mobile.html中引用的所有本地文件
grep -oP '(src|href)="([^"]+)"' "$HTML_DIR/mobile.html" 2>/dev/null | grep -v 'http' | grep -v '//' | sed 's/[a-z]*="//;s/"$//' | sort -u | while read -r ref; do
    refpath="$HTML_DIR/$ref"
    if [ -f "$refpath" ] || [ -d "$refpath" ]; then
        echo "  ✓ $ref"
    else
        echo "  ✗ $ref 引用了但不存在!"
        ERRORS=$((ERRORS+1))
    fi
done

# === 4. 检查server.py ===
echo ""
echo "[4/4] 检查server.py..."
if [ -f "$HTML_DIR/server.py" ]; then
    if python3 -m py_compile "$HTML_DIR/server.py" 2>/dev/null; then
        echo "  ✓ server.py 语法通过"
    else
        echo "  ✗ server.py 语法错误!"
        ERRORS=$((ERRORS+1))
    fi
else
    echo "  - server.py 不存在（可能用内置http.server）"
fi

# === 结果 ===
echo ""
if [ "$ERRORS" -gt 0 ]; then
    echo "[FAIL] 发现 $ERRORS 个错误，拒绝启动服务器"
    exit 1
else
    echo ""
    echo "==================================="
    echo "[PASS] 全部检查通过，正在启动服务器..."
    echo "==================================="
    cd "$HTML_DIR"
    exec python3 -m http.server 8080 --bind 0.0.0.0
fi
