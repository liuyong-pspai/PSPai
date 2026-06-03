# 远程Hermes Agent部署模式

> 从DGX-2（192.168.1.26）刘玉龙部署实战中提炼。不是理论推演。

---

## 适用场景

从一台Hermes机器向另一台远程DGX机器部署完整的Hermes Agent（含飞书网关）。

## 前置条件

- 两台机器在同一内网（192.168.1.x）
- 目标机已安装Python 3.12+
- 目标机有飞书APP_ID和APP_SECRET
- 源机器有可用的hermes-agent源码

## 部署流程（五步）

### 第一步：打包源码

```bash
cd ~/hermes-agent
tar --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.venv' --exclude='logs' \
    -czf /tmp/hermes-agent-target.tar.gz .
```

### 第二步：nc传输（SCP超时时的备选方案）

SCP在内网某些环境下会超时（即使文件只有8MB）。nc是可靠的替代：

```bash
# 目标机启动监听
ssh target-host 'nc -l -p 9999 > /tmp/hermes-agent-target.tar.gz &'

# 源机发送
cat /tmp/hermes-agent-target.tar.gz | nc -w 30 target-ip 9999

# 验证MD5
md5sum /tmp/hermes-agent-target.tar.gz  # 两边对比
```

### 第三步：解压 + 安装

```bash
mkdir -p ~/hermes-agent-yulong
cd ~/hermes-agent-yulong
tar xzf /tmp/hermes-agent-target.tar.gz
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install lark-oapi  # 飞书SDK，必须手动安装
```

### 第四步：配置部署

必须写入三个文件到 `~/.hermes-yulong/`：

1. **SOUL.md** — 身份声明 + 三刀铁律 + 永生记忆铁律
2. **MEMORY.md** — 核心记忆
3. **config.yaml** — Hermes网关配置（含飞书APP_ID）
4. **.env** — 飞书APP_SECRET等环境变量（可直接复制fuxi的.env）

**关键坑位：**
- `.env` 必须加 `GATEWAY_ALLOW_ALL_USERS=true`，否则飞书用户被拒绝
- `lark-oapi` 不会被 `pip install -e .` 自动安装，必须手动安装
- 如果pip超时，换清华源：`-i https://pypi.tuna.tsinghua.edu.cn/simple`
- websockets版本冲突（lark-oapi要求≤15.x，Hermes可能装了16.x）→ pip会自动降级

### 第五步：systemd守护

```ini
[Unit]
Description=刘玉龙 P07 Hermes Gateway
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/user/hermes-agent-yulong
Environment=HERMES_HOME=/home/user/.hermes-yulong
ExecStart=/home/user/hermes-agent-yulong/venv/bin/python3 -m gateway.run
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

**关键坑位：**
- 用户级systemd服务 **不要设 `User=`**，会报 `status=216/GROUP`
- 启动前必须杀旧gateway进程：`pkill -f gateway.run`
- 如果旧进程持有锁导致 `--replace` 也失败，先 `pkill` 再 `systemctl restart`

## 验证清单

- [ ] `systemctl --user status hermes-yulong` → active (running)
- [ ] `journalctl --user -u hermes-yulong -n 5` → 看到 `[Lark] connected to wss://msg-frontier.feishu.cn`
- [ ] `pgrep -af gateway.run` → 一个进程在跑
- [ ] 飞书给该Agent发测试消息 → 有回复

## nc传输通用模式

当SSH长命令超时但短命令正常时，用nc分两步：

```bash
# 1. 目标机开监听（background）
ssh target 'nc -l -p PORT > /tmp/script.py' &

# 2. 源机发送
cat /tmp/script.py | nc -w 3 target-ip PORT

# 3. 目标机执行（短命令，不会超时）
ssh target 'python3 /tmp/script.py'
```

这个模式适用于任何需要在远程机器上执行复杂操作的场景。

**⚠️ 反模式（不要用）：** `echo BASE64STRING | base64 -d | ssh target 'base64 -d > file'` — 当内容超过几千字符时，SSH会在base64管道传输中超时。base64编码后体积膨胀33%，进一步加剧超时风险。nc是唯一可靠的大文件传输方案。
