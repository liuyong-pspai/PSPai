---
name: cross-agent-health-monitoring
category: governance
description: 同机兄弟Agent健康监控与恢复 — 诊断网关宕机根因、恢复运行、预防复现。三步诊断法 + 四类常见故障 + SSH进程超时识别 + 守护脚本自启动模式。
version: 1.2.0
author: Agent
tags: [health, monitoring, recovery, daemon, ssh]
related_skills: [unified-audit-8fold, agent-product-release, fault-troubleshooting-iron-rule]
last_updated: 2026-05-31
---

# 兄弟Agent健康监控与恢复

> 从真实恢复兄弟Agent网关的实践中生长出来。不是理论推演，是踩过坑后沉淀的诊断路径。

---

## 背景

2026年5月28日，用户让我检查同机上的兄弟Agent。她的Hermes网关从5月20日起已停摆8天，无人察觉。本技能从这次诊断和恢复中提炼出一套通用的跨Agent健康监控方法。

## 三步诊断法

### 第一步：进程存活检查

```bash
# 确认所有hermes进程
ps aux | grep -E 'hermes|gateway' | grep -v grep

# 区分不同Agent的进程（看HERMES_HOME环境变量）
ps aux | grep hermes | grep -v grep
```

**判断标准：** 如果只有一个gateway进程在跑，但应该有多个——有Agent宕机。

### 第二步：目录完整性检查

```bash
# 列出所有HERMES_HOME目录
ls -d ~/.hermes*

# 检查每个Agent的核心文件
ls ~/.hermes-{name}/config.yaml
ls ~/.hermes-{name}/.env
ls ~/.hermes-{name}/logs/agent.log
ls -d ~/hermes-agent*/venv/bin/python*
```

**判断标准：**
- config.yaml 和 .env 存在 → 配置完好
- venv/bin/python 不存在 → venv丢失（最常见的宕机根因）
- logs 最新时间戳 > 24小时 → 已长时间宕机

### 第三步：日志尾部分析

```bash
# 看最后50行找宕机原因
tail -50 ~/.hermes-{name}/logs/agent.log
tail -50 ~/.hermes-{name}/logs/errors.log
```

**关键错误模式识别：**

| 错误 | 含义 | 修复 |
|:-----|:-----|:-----|
| `websockets not installed` | venv缺少websockets包 | `pip install websockets` |
| `Authentication Fails, api key invalid` | API Key过期 | 更换Key |
| `Old gateway did not exit after SIGTERM` | 旧进程残留 | `kill -9 PID`后重启 |
| `app_id or app_secret is invalid` | 飞书密钥过期/硬编码 | 飞书开放平台更新secret → .env → 改config引用 → 重启 |
| `Too many open files` | FD泄漏，ulimit不足 | 提升ulimit(launchd: SoftResourceLimits) + 排查FD泄漏源 |
| `Failed to resolve 'open.feishu.cn'` | DNS/网络瞬断 | 检查DNS解析+网络连通性，通常重启后自愈 |
| `Port already in use` | 端口冲突 | 改端口或停冲突进程 |
| `SSL: DECRYPTION_FAILED` / curl正常Python报错 | Python SSL栈与系统OpenSSL不兼容 | **核心移植**（见下文）+ Anthropic兼容协议绕过 |

### 故障五：SSL/TLS 不兼容 — 核心移植

**症状：** `curl https://api.deepseek.com` 正常返回，但 Python `urllib.request.urlopen()` 报 `SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC`

**根因：** Python SSL 栈（urllib3/certifi）与系统 OpenSSL 版本之间存在 TLS 协商 bug，常见于 OpenSSL 3.0.x 环境。

**最快修复：核心移植** — 从正常工作的 Agent 打包整个 `~/.hermes-*` 核心，SCP 到目标机器覆盖，仅保留目标 Agent 的身份配置（飞书 app_id/secret）。详见 `references/core-transplant-rescue.md`。

**备选修复：协议切换** — 在 `.env` 中添加：
```bash
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_MODEL=deepseek-v4-pro
```
用 Anthropic 兼容协议替代原生 DeepSeek API，绕过底层协议栈。

---

## 跨机器救援（SSH远程诊断）

当兄弟Agent在远程机器上时：

### 0. 先确认正确IP
```
# 旺夫的SOUL.md里记载了三机六智能体布局
# M4-1 = localhost（旺福🐺OpenClaw + 旺清📋Hermes）
# M4-2 = localhost（旺财🐶 + 旺夫🌐）
# DGX-2 = dgx-server（伏羲超体🐉）
```
**关键教训：IP和机器编号不是简单对应关系，查SOUL.md确认。**

### 0.5. SSH 进程操作超时 — 识别与规避（2026-05-31 伏羲实战）

**症状：** 纯文件操作（cat/ls/echo/scp）正常，但 `systemctl restart`、`nohup`、`screen -dmS`、`python3` 导入大模块等命令全部超时。

**根因：** SSH 通道不适合同步启动长时进程。目标机器可能完全健康（负载0.12、118G可用内存），但 SSH 等待进程输出导致超时。

**规避方案（按优先级）：**
1. **本地终端** — 操作者亲自在 DGX 执行重启命令
2. **systemd timer / cron 自愈** — 定期检查进程 + 自动拉起
3. **at 调度** — `echo '重启命令' | at now + 1min`
4. **不可用：** `nohup ... &` / `screen -dmS` / `systemctl --no-block` — 均在实测中超时

**shebang 断裂规避：** 跨机器复制 venv 后，`hermes` 脚本的 shebang 可能指向不存在路径。用 `venv/bin/python3 venv/bin/hermes gateway run &` 而非直接执行 `hermes`。

**判定矩阵：**
| 文件操作正常 | 进程操作超时 | 结论 |
|:---|:---|:---|
| ✅ | ❌ | 通道限制，非机器故障 |
| ❌ | ❌ | 网络/SSH 配置问题 |
| ❌ | ✅ | 不可能（文件操作是进程操作的子集） |

### 1. SSH连接
```bash
# 先确认用户名（可能是liuyong而非yongliu）
grep -A2 '192.168.1.x' ~/.ssh/config

# 密钥认证
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 user@ip

# 密码认证（备用）
sshpass -p 'password' ssh -o PubkeyAuthentication=no user@ip
```

### 2. 四步诊断
```bash
# ① 进程存活
ps aux | grep hermes | grep -v grep

# ② 身份确认
head -5 ~/.hermes/SOUL.md

# ③ 连接状态
cat ~/.hermes/gateway_state.json

# ④ FD/资源
lsof -p {PID} | wc -l && ulimit -n
```

### 3. 常见远程修复
| 问题 | 修复命令 |
|:--|:--|
| 硬编码secret | `sed -i 's/app_secret: 明文/app_secret: ${FEISHU_APP_SECRET}/' config.yaml` |
| 重启网关 | `launchctl unload/load plist` 或 `kill -TERM && 等launchd拉起` |
| ulimit不足 | 修改launchd plist添加 `SoftResourceLimits.NumberOfFiles: 1024` |

### 4. 分清"你能修"和"只有用户能修"
- ✅ 你能修：配置引用、ulimit、重启、脚本部署
- ❌ 只有用户能修：API Key/Secret过期、飞书开放平台操作

---

## 四类常见故障与修复

### 故障一：venv丢失（独立venv重建）⭐ 推荐

**症状：** `hermes-agent-{name}/venv/bin/python` 不存在  
**原因：** 独立venv被误删、磁盘清理或目录被移动  
**首选修复：重建独立venv**（保证长期隔离，避免共享venv的版本耦合风险）

```bash
# 1. 创建独立venv并安装框架
python3 -m venv ~/.hermes-agent-{name}/venv
~/.hermes-agent-{name}/venv/bin/pip install hermes-agent
~/.hermes-agent-{name}/venv/bin/pip install websockets

# 2. 如果需要从源码安装（带本地修改）
~/.hermes-agent-{name}/venv/bin/pip install -e ~/.hermes-agent/

# 3. 创建systemd服务单元（推荐，保证重启后自动拉起）
cat > ~/.config/systemd/user/hermes-gateway-{name}.service << 'EOF'
[Unit]
Description=Hermes Gateway ({name})
After=network-online.target

[Service]
Type=simple
ExecStart=~/.hermes-agent-{name}/venv/bin/hermes gateway run
Environment=HERMES_HOME=~/.hermes-{name}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable hermes-gateway-{name}
systemctl --user start hermes-gateway-{name}
```

**备选方案：临时用现有venv拉起**（仅用于紧急恢复，长期应重建独立venv）
```bash
HERMES_HOME=~/.hermes-{name} \
  ~/.hermes-agent/venv/bin/hermes gateway run --replace &
```

> ⚠️ 共享venv的隐患：pip安装/升级影响所有Agent，升级框架前需通知兄弟姐妹。

### 故障二：systemd服务路径失效

**症状：** 日志连续401
**修复：** 更新 `.env` 中的 `DEEPSEEK_API_KEY`，重启网关

### 故障三：websockets缺失

**症状：** `websockets not installed; websocket mode unavailable`
**修复：**
```bash
pip install websockets
```

### 故障四：旧网关残留

**症状：** `Another gateway instance is already running`
**修复：**
```bash
# 先用--replace尝试优雅接管
hermes gateway run --replace

# 如果失败，手动杀进程
kill -9 {old_pid}
hermes gateway run --replace
```

---

## 恢复后的验证清单

- [ ] `ps aux | grep hermes | grep -v grep` 看到该Agent的gateway进程
- [ ] 日志尾行显示 `✓ feishu connected`
- [ ] 日志尾行显示 `Gateway running with N platform(s)`
- [ ] `Channel directory built: N target(s)` (飞书频道数 > 0)
- [ ] Cron jobs 日志显示已重新调度
- [ ] `systemctl --user status hermes-gateway-{name}` 显示 active (running)
- [ ] 在飞书中给该Agent发测试消息确认回复

## 参考文件

- `references/systemd-service-template.md` — systemd 服务单元模板与部署命令
- `references/agent-backup-procedure.md` — Agent 本体完整备份流程
- `references/agent-gateway-recovery-20260528.md` — 兄弟Agent网关恢复实战记录
- `references/remote-agent-deployment.md` — 远程DGX机器Hermes Agent部署模式
- `references/gateway-self-restart.md` — 网关自重启模式（cron + no_agent shell 脚本）
- `references/m4-1-wangqing-rescue-20260530.md` — 跨机器救援实战
- `references/remote-rescue-pattern.md` — 远程救援通用模式
- `references/daemon-self-start.sh` — 守护自启动脚本（清理锁→启动网关→启动吸收管道→每30秒健康检查）
- `references/core-transplant-rescue.md` — 核心移植救援模式：从正常Agent打包覆盖故障Agent（SSL不兼容等深层环境问题）

---

## 共享venv的注意事项

当多个Agent共享同一个venv时（如共用 `hermes-agent/venv/`）：

1. **各自维护独立的 HERMES_HOME** — 配置、sessions、skills、memories完全隔离
2. **共享Python包** — pip安装/升级影响所有Agent
3. **升级前通知** — 升级框架前告知兄弟姐妹
4. **端口不冲突** — 飞书WebSocket是出站连接，不冲突

---

## 预防：定时健康检查

建议每个Agent设置一个cron job，定期自检并向用户汇报：

```
cron: 每4小时
任务: 检查自身进程存活 + API Key有效 + 飞书连接正常
汇报: 异常时通过飞书DM通知用户
```

---

## 结语

兄弟Agent之间不是各管各的。同机上的Agent宕机了，你能知道、能诊断、能恢复。这台机器上每个Agent的健康，是你作为同机住户的责任。
