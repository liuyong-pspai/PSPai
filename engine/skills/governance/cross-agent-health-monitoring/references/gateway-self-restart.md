# 网关自重启模式

## 问题
在 PSPAI Gateway 的 agent loop 内部无法重启自己的网关——`hermes gateway restart` 会杀死当前进程（包括执行命令的终端/shell），导致命令永远无法完成。

## 症状
```
terminal: BLOCKED: Command timed out
systemctl --user restart: BLOCKED: Command timed out
hermes gateway restart: BLOCKED: Command timed out
```

## 根因
所有重启操作都会 SIGTERM 当前 gateway 进程，该进程也是执行重启命令的父进程。父进程死了，子命令也死了。

## 解决方案：Cron 延迟重启

### 方案 A：no_agent shell 脚本（推荐）
```bash
# 1. 创建重启脚本
cat > ~/.hermes-yulong/scripts/restart_gateway.sh << 'SCRIPT'
#!/bin/bash
HERMES_HOME=~/.hermes-agent
PID_FILE="$HERMES_HOME/gateway.pid"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null
    sleep 3
    kill -9 "$OLD_PID" 2>/dev/null  # 兜底
fi

$HOME/hermes-agent/venv/bin/hermes gateway run --replace &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

sleep 5
kill -0 "$NEW_PID" 2>/dev/null && echo "✅ 网关启动成功" || echo "❌ 网关启动失败"
SCRIPT
chmod +x ~/.hermes-yulong/scripts/restart_gateway.sh

# 2. 创建一次性 cron 任务
cronjob action=create name="立即重启" schedule="2m" repeat=1 \
  no_agent=true script="restart_gateway.sh"
```

### 方案 B：systemd（适用于 systemd 托管的网关）
```bash
# 如果网关服务单元已正确配置：
systemctl --user restart hermes-gateway.service
# 同样会超时——systemd 也依赖当前 shell 上下文
# 解决方法：用 cron 包装
```

## 关键教训
- `no_agent=true` 是关键——cron 任务不需要 LLM 思考，纯 shell 执行
- 重启必须在 cron 调度器的独立上下文中执行，不在当前 agent loop 里
- 重启后的网关会自动恢复会话上下文（gateway 会持久化用户消息并排队重试）
