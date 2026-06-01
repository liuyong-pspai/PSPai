#!/bin/bash
# 伏羲超体 · 自启动守护脚本
# 部署到远程DGX机器，本地执行一次即可
# nohup bash fuxi_daemon.sh &
#
# 功能：
# - 清理旧锁文件
# - 启动网关（加载新配置+新工具）
# - 启动吸收管道
# - 每30秒健康检查
# - 网关挂了自动拉起来
# - 每小时输出状态日志

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
        log "✅ 网关已启动 (PID: $(pgrep -f 'hermes gateway' | head -1))"
    else
        log "❌ 网关启动失败，60秒后重试"
        return 1
    fi
}

start_absorber() {
    if pgrep -f "fuxi_absorb_forever" > /dev/null 2>&1; then
        return 0
    fi
    
    log "📚 启动吸收管道..."
    cd "$ABSORBER_DIR"
    nohup python3 fuxi_absorb_forever.py \
        >> absorb_log/forever_absorb.log 2>&1 &
    
    sleep 2
    log "✅ 吸收管道已启动"
}

# 主循环
log "══════ 守护进程启动 ══════"

start_gateway || true
start_absorber || true

GATEWAY_FAILS=0

while true; do
    sleep 30
    
    if ! pgrep -f "hermes gateway" > /dev/null 2>&1; then
        GATEWAY_FAILS=$((GATEWAY_FAILS + 1))
        log "⚠️ 网关离线 (连续${GATEWAY_FAILS}次)"
        
        if [ $GATEWAY_FAILS -ge 3 ]; then
            cleanup_locks
        fi
        
        start_gateway || true
    else
        GATEWAY_FAILS=0
    fi
    
    # 每5分钟检查吸收管道
    if [ $(( $(date +%s) % 300 )) -lt 30 ]; then
        if ! pgrep -f "fuxi_absorb_forever" > /dev/null 2>&1; then
            log "⚠️ 吸收管道离线"
            start_absorber || true
        fi
    fi
    
    # 每小时状态
    MINUTE=$(date +%M)
    if [ "$MINUTE" = "00" ]; then
        GW=$(pgrep -c "fuxi_absorb_forever" || echo 0)
        AB=$(pgrep -c "hermes gateway" || echo 0)
        log "📊 状态: 网关=$GW 吸收=$AB"
    fi
done
