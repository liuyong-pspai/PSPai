#!/bin/bash
# 小龙人 XiaoLongRen — 一键启动脚本
# 用法: bash start.sh
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "🐉 小龙人 XiaoLongRen 启动中..."

# 1. 检查 .env
if [ ! -f .env ]; then
    echo "❌ 未找到 .env 文件"
    echo "   请先复制: cp .env.example .env"
    echo "   然后编辑 .env 填入 PSPAI_API_KEY"
    exit 1
fi

# 2. 检查 Python
PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &>/dev/null; then
        PYTHON=$cmd
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python，请先安装 Python 3.10+"
    echo "   https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python: $($PYTHON --version)"

# 3. 找引擎二进制文件
ENGINE=""
OS="$(uname -s)"
case "$OS" in
    Linux)  ENGINE="xiaolongren-engine-linux-x86_64" ;;
    Darwin) ENGINE="xiaolongren-engine-macos" ;;
    MINGW*|MSYS*|CYGWIN*) ENGINE="xiaolongren-engine-windows.exe" ;;
esac

if [ -z "$ENGINE" ]; then
    echo "❌ 无法识别操作系统: $OS"
    exit 1
fi

if [ ! -f "$ENGINE" ]; then
    echo "❌ 未找到引擎文件: $ENGINE"
    echo ""
    echo "   请从 GitHub Releases 下载对应平台的引擎:"
    echo "   https://github.com/liuyong-pspai/PSPai/releases"
    echo ""
    echo "   下载后把文件放到当前目录: $(pwd)"
    exit 1
fi

# 4. 授权引擎 (macOS/Linux)
if [ "$OS" != "MINGW"* ] && [ "$OS" != "MSYS"* ] && [ "$OS" != "CYGWIN"* ]; then
    chmod +x "$ENGINE" 2>/dev/null || true
fi

echo "✅ 引擎: $ENGINE"

# 5. 安装 Python 依赖
if [ ! -f .deps_installed ]; then
    echo "📦 安装 Python 依赖..."
    pip install -q PyYAML Pillow requests
    touch .deps_installed
    echo "✅ 依赖安装完成"
fi

# 6. 启动引擎
echo "🚀 启动 PSPAI 引擎 (8089)..."
./"$ENGINE" &
ENGINE_PID=$!

# 7. 启动 launcher（内置HTTP服务器+引擎管理）
echo "🚀 启动小龙人 (内置HTTP服务器:8088)..."
$PYTHON launcher.py &
UI_PID=$!

sleep 2

# 8. 检查
if kill -0 $ENGINE_PID 2>/dev/null && kill -0 $UI_PID 2>/dev/null; then
    echo ""
    echo "═══════════════════════════════════════"
    echo "  🐉  小龙人 已启动！"
    echo "  🌐  打开浏览器访问: http://localhost:8088"
    echo "═══════════════════════════════════════"
    echo ""
    echo "按 Ctrl+C 停止"

    # 尝试打开浏览器
    if command -v xdg-open &>/dev/null; then
        xdg-open http://localhost:8088 2>/dev/null || true
    elif command -v open &>/dev/null; then
        open http://localhost:8088 2>/dev/null || true
    elif command -v start &>/dev/null; then
        start http://localhost:8088 2>/dev/null || true
    fi

    trap "kill $ENGINE_PID $UI_PID 2>/dev/null; echo '🛑 已停止'" EXIT
    wait
else
    echo "❌ 启动失败"
    kill $ENGINE_PID $UI_PID 2>/dev/null
    exit 1
fi
