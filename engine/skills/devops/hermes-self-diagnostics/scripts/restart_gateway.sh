#!/bin/bash
# P07 硬重启网关 — 独立于Agent进程，可被cron(no_agent=true)调用
# 为什么用这个：Agent无法从自身进程内重启（hermes gateway restart 会杀掉父进程导致超时）
# 方案：cronjob(no_agent=true, script=this_script) 由外部调度器独立执行

set -e

HERMES_HOME=/home/yongliu/.hermes-yulong
HERMES_BIN=/home/yongliu/hermes-agent/venv/bin/hermes
LOCK_FILE="$HERMES_HOME/gateway.lock"
PID_FILE="$HERMES_HOME/gateway.pid"

echo "=== P07 硬重启 $(date) ==="

# 1. 杀所有Hermes gateway进程（不用PID文件，防止过期PID）
echo "[1/5] 杀旧网关 ..."
pkill -f "hermes_cli.main gateway" 2>/dev/null || true
sleep 2
pkill -9 -f "hermes_cli.main gateway" 2>/dev/null || true
sleep 1

# 2. 清理锁文件（上次失败12:29就是因为锁冲突）
echo "[2/5] 清理锁 ..."
rm -f "$LOCK_FILE" "$PID_FILE"

# 3. 验证
echo "[3/5] 验证 ..."
if pgrep -f "hermes_cli.main gateway" > /dev/null; then
    echo "❌ 旧进程未死，退出"
    exit 1
fi

# 4. 启动
echo "[4/5] 起新网关 ..."
cd "$HERMES_HOME"
HERMES_HOME="$HERMES_HOME" "$HERMES_BIN" gateway run --replace > /dev/null 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"
sleep 3

# 5. 验证
echo "[5/5] 验证启动 ..."
if kill -0 "$NEW_PID" 2>/dev/null; then
    echo "✅ 新网关 PID=$NEW_PID"
else
    echo "❌ 启动失败"
    exit 1
fi
