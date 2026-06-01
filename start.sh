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
    echo "   请复制 .env.example → .env 并填入 API Key"
    echo "   cp .env.example .env"
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
    exit 1
fi

# 3. 检查/创建虚拟环境
if [ ! -d venv ]; then
    echo "📦 创建虚拟环境..."
    $PYTHON -m venv venv
fi
source venv/bin/activate

# 4. 安装依赖
if [ ! -f .deps_installed ]; then
    echo "📦 安装依赖..."
    pip install -q PyYAML Pillow requests
    touch .deps_installed
fi

# 5. 启动服务
echo "🚀 启动 PSPAI 后端 (8089)..."
$PYTHON pspai_server.py &
PSPAI_PID=$!

echo "🚀 启动静态文件服务 (8088)..."
cd UI原型
$PYTHON server.py &
UI_PID=$!
cd "$DIR"

sleep 2

# 6. 检查服务
if kill -0 $PSPAI_PID 2>/dev/null && kill -0 $UI_PID 2>/dev/null; then
    echo ""
    echo "✅ 小龙人已启动！"
    echo "   🌐 打开浏览器访问: http://localhost:8088"
    echo "   📍 PSPAI后端: http://localhost:8089"
    echo ""
    echo "   按 Ctrl+C 停止所有服务"
    
    # 尝试打开浏览器
    if command -v xdg-open &>/dev/null; then
        xdg-open http://localhost:8088 2>/dev/null || true
    elif command -v open &>/dev/null; then
        open http://localhost:8088 2>/dev/null || true
    fi
    
    # 等待并清理
    trap "kill $PSPAI_PID $UI_PID 2>/dev/null; echo '已停止'" EXIT
    wait
else
    echo "❌ 启动失败，请检查日志"
    kill $PSPAI_PID $UI_PID 2>/dev/null
    exit 1
fi
