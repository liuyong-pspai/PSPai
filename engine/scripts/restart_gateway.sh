#!/bin/bash
# 重启Hermes网关
systemctl --user stop hermes-gateway.service 2>/dev/null
sleep 2
pkill -f "hermes-agent/venv/bin/python3.*gateway run" 2>/dev/null
sleep 2
rm -f /tmp/hermes_gateway.lock 2>/dev/null
systemctl --user start hermes-gateway.service 2>/dev/null
sleep 3
echo "RESTARTED $(date)" >> /tmp/hermes_restart.log
