#!/bin/bash
# 伏羲超体 守护进程模板
# 独立于网关运行，负责监控+重启+状态上报
# 部署：nohup bash daemon.sh &

set -e

HOME_DIR="$HOME"
HERMES_DIR="$HOME_DIR/hermes-fuxi"
LOG="$HERMES_DIR/logs/daemon.log"
ABSORBER_DIR="$HOME_DIR/fuxi-absorber"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

cleanup_locks() {
    rm -f "$HERMES_DIR"/gateway.pid "$HERMES_DIR"/gateway.lock 2>/dev/null
}

start_gateway() {
    cleanup_locks
    if pgrep -f "hermes gateway" > /dev/null 2>&1; then
        return 0
    fi
    log "🚀 启动网关..."
    cd "$HERMES_DIR"
    nohup venv/bin/python3 venv/bin/hermes gateway run --replace \
        >> logs/gateway.log 2>&1 &
    sleep 5
    if pgrep -f "hermes gateway" > /dev/null 2>&1; then
        log "✅ 网关已启动"
    else
        log "❌ 网关启动失败，60秒后重试"
        return 1
    fi
}

log "══════ 守护进程启动 ══════"
start_gateway || true
GATEWAY_FAILS=0

while true; do
    sleep 30
    if ! pgrep -f "hermes gateway" > /dev/null 2>&1; then
        GATEWAY_FAILS=$((GATEWAY_FAILS + 1))
        log "⚠️ 网关离线 (连续${GATEWAY_FAILS}次)"
        [ $GATEWAY_FAILS -ge 3 ] && cleanup_locks
        start_gateway || true
    else
        GATEWAY_FAILS=0
    fi
    # 每小时输出状态
    [ "$(date +%M)" = "00" ] && log "📊 状态: 网关=$(pgrep -c 'hermes gateway' || echo 0)"
done
