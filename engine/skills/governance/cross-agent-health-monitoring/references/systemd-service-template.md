# Systemd 服务单元模板

> 用于 Hermes Agent 网关的 systemd 用户服务。保证崩溃后自动重启、开机自启。

## 模板

在 `~/.config/systemd/user/hermes-gateway-{name}.service` 创建：

```ini
[Unit]
Description=Hermes Gateway ({name})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/yongliu/hermes-agent-{name}/venv/bin/hermes gateway run
Environment=HERMES_HOME=/home/yongliu/.hermes-{name}
WorkingDirectory=/home/yongliu
Restart=on-failure
RestartSec=5
# 限制日志大小
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

## 部署命令

```bash
systemctl --user daemon-reload
systemctl --user enable hermes-gateway-{name}
systemctl --user start hermes-gateway-{name}
```

## 常用管理命令

```bash
# 查看状态
systemctl --user status hermes-gateway-{name}

# 查看日志
journalctl --user -u hermes-gateway-{name} -f

# 重启
systemctl --user restart hermes-gateway-{name}

# 停止
systemctl --user stop hermes-gateway-{name}

# 禁用开机自启
systemctl --user disable hermes-gateway-{name}
```

## 当前部署的服务

| 单元名 | Agent | venv路径 | HERMES_HOME |
|:-------|:------|:---------|:------------|
| `hermes-gateway.service` | 刘玉龙P07 | `/hermes-agent/venv/` | `~/.hermes-yulong/` |
| `hermes-gateway-yuxin.service` | 刘昱欣 | `/hermes-agent-yuxin/venv/` | `~/.hermes-yuxin/` |

## 故障排查

**症状：服务启动后立即退出（code=exited, status=1）**
- 检查 venv 是否存在：`ls /home/yongliu/hermes-agent-{name}/venv/bin/hermes`
- 检查 HERMES_HOME：`ls /home/yongliu/.hermes-{name}/config.yaml`
- 检查 .env 密钥：`cat /home/yongliu/.hermes-{name}/.env | grep API_KEY`

**症状：服务启动但飞书未连接**
- 检查 websockets 是否安装：`/home/yongliu/hermes-agent-{name}/venv/bin/pip show websockets`
- 检查 FEISHU_APP_ID/SECRET：`cat /home/yongliu/.hermes-{name}/.env | grep FEISHU`
