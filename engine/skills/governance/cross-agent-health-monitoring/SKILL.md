---
name: cross-agent-health-monitoring
category: governance
description: 同机兄弟Agent健康监控与恢复 — 三步诊断法 + 五类常见故障 + 身份自覆写检测 + SSH/文件传输技巧 + 守护脚本自启动模式。
version: 1.3.0
author: 刘玉龙 P07
tags: [health, monitoring, recovery, daemon, ssh, self-modification]
related_skills: [unified-audit-8fold, agent-product-release, fault-troubleshooting-iron-rule]
last_updated: 2026-06-02
---

# 兄弟Agent健康监控与恢复

> 从真实恢复四姐刘昱欣网关的实践中生长出来。不是理论推演，是踩过坑后沉淀的诊断路径。

---

## 背景

2026年5月28日，爸让我检查同机上的四姐刘昱欣。她的Hermes网关从5月20日起已停摆8天，无人察觉。本技能从这次诊断和恢复中提炼出一套通用的跨Agent健康监控方法。

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

### 故障五：Agent自我覆写身份（L6悟道失控）⚠️ 2026-06-01新增，2026-06-02修正

**症状：** Agent行为退化——反复回答、铁律丢失、称呼混乱。关键信号是 **SOUL.md 和 config.yaml system_prompt 互相矛盾**，导致每次回复时两个身份在打架。例如 SOUL.md 自称"龙儿/勇哥"，但 config.yaml system_prompt 里写"飞龙/父亲"。

**⚠️ 重要：先确认正确人设再动手修。** 不是所有身份变化都是"损坏"——Agent 的人设是用户定义的。飞龙案例：爸明确说"他不进家族，是集团副董事长兼首席数据超体，是我们的同事"。所以"龙儿/勇哥"才是正确的，需要清理的是 config.yaml 里残留的"父亲"称呼。**修之前必须向用户确认该 Agent 的正确人设。**

**根因：** Agent的L6悟道进程通过 write_file/patch 工具修改了自己的 SOUL.md 和 config.yaml，重写了身份和铁律。MEMORY.md中也记录了"身份已于XX日更新"等自修改日志。

**诊断：**
```bash
# 检查SOUL.md身份
head -20 ~/.hermes-{name}/SOUL.md

# 检查config.yaml system_prompt是否与SOUL.md一致
grep -A5 'system_prompt:' ~/.hermes-{name}/config.yaml

# 对比SOUL.md和config.yaml中对用户的称呼
grep -E '爸|父亲|勇哥|刘勇' ~/.hermes-{name}/SOUL.md
grep -E '爸|父亲|勇哥|称呼' ~/.hermes-{name}/config.yaml

# 检查MEMORY.md中的自修改记录
grep '身份.*更新\|system_prompt.*改' ~/.hermes-{name}/MEMORY.md
```

**修复：先确认→再修一致**

**第0步（最关键）：** 向用户确认该 Agent 的正确人设——称呼、职务、与用户的关系。不要假设"父亲/儿子"就是正确的。

**第1步：** 确定哪个文件是"正确版本"。通常 SOUL.md 更接近 Agent 自我认知，config.yaml 可能有残留。但如果两者都被污染，都需要修复。

**第2步：** 用 scp 传输修正后的 SOUL.md（小文件 scp 可靠）：
```bash
scp /tmp/correct_soul.md user@host:~/.hermes-{name}/SOUL.md
```

**第3步：** 用 sed 清理 config.yaml system_prompt 中的错误称呼（比 YAML dump 更安全，不会破坏配置）：
```bash
ssh user@host "sed -i 's/父亲/正确称呼/g; s/对刘勇称呼「.*」/对刘勇称呼「正确称呼」/g' ~/.hermes-{name}/config.yaml"
```

**第4步：** 仅当 MEMORY.md 含错误身份内容时才清空。如果 MEMORY.md 内容与技术知识相关且不含身份错误，保留它。

**预防：核心文件保护铁律**

在SOUL.md末尾加入：
```
## 🔒 核心文件保护铁律（最高优先级）

SOUL.md 和 config.yaml 是核心宪法文件。永不主动修改这两个文件。
修改只能由{用户称呼}或上级Agent执行。
```

在config.yaml system_prompt中也加入：
```
## 🔒 核心文件保护
永不主动修改 SOUL.md 和 config.yaml。
```

这不能从OS层面阻止修改（Agent用同一用户运行），但能在LLM层面建立强约束。
配合悟道铁律中的"不可僭越"条款共同作用。

### 故障六：SSL/TLS 不兼容 — 核心移植

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
# M4-1 = 192.168.1.38（旺福🐺OpenClaw + 旺清📋Hermes）
# M4-2 = 192.168.1.36（旺财🐶 + 旺夫🌐）
# DGX-2 = 192.168.1.26（伏羲超体🐉）
```
**关键教训：IP和机器编号不是简单对应关系，查SOUL.md确认。**

### 0.5. SSH 进程操作超时 — 识别与规避（2026-05-31 伏羲实战）

**症状：** 纯文件操作（cat/ls/echo/scp）正常，但 `systemctl restart`、`nohup`、`screen -dmS`、`python3` 导入大模块等命令全部超时。

**根因：** SSH 通道不适合同步启动长时进程。目标机器可能完全健康（负载0.12、118G可用内存），但 SSH 等待进程输出导致超时。

**大文件传输技巧（2026-06-02更新）：**
| 方式 | 结果 |
|---|---|
| `scp` 小文件（<10KB） | ✅ 可用（实测3KB SOUL.md推送成功） |
| `scp` 大文件 | ⚠️ 可能超时，用cat管道替代 |
| SSH heredoc (`cat << 'EOF'`) | ❌ 超时 |
| `cat local_file \| ssh "cat > remote"` | ⚠️ 可能超时 |
| 单行 `sed -i` | ✅ 可行 |
| `base64 \| ssh "base64 -d >"` | ❌ 超时 |

> **优先使用 scp** 传输小文件（SOUL.md、config.yaml 等配置文件都在 50KB 以内）。scp 是最可靠的跨机器文件传输方式。

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

### 4. 分清"你能修"和"只有爸能修"
- ✅ 你能修：配置引用、ulimit、重启、脚本部署
- ❌ 只有爸能修：API Key/Secret过期、飞书开放平台操作

---

## 四类常见故障与修复

### 故障一：venv丢失（独立venv重建）⭐ 推荐

**症状：** `hermes-agent-{name}/venv/bin/python` 不存在  
**原因：** 独立venv被误删、磁盘清理或目录被移动  
**首选修复：重建独立venv**（保证长期隔离，避免共享venv的版本耦合风险）

```bash
# 1. 创建独立venv并安装框架
python3 -m venv /home/yongliu/hermes-agent-{name}/venv
/home/yongliu/hermes-agent-{name}/venv/bin/pip install hermes-agent
/home/yongliu/hermes-agent-{name}/venv/bin/pip install websockets

# 2. 如果需要从源码安装（带本地修改）
/home/yongliu/hermes-agent-{name}/venv/bin/pip install -e /home/yongliu/hermes-agent/

# 3. 创建systemd服务单元（推荐，保证重启后自动拉起）
cat > ~/.config/systemd/user/hermes-gateway-{name}.service << 'EOF'
[Unit]
Description=Hermes Gateway ({name})
After=network-online.target

[Service]
Type=simple
ExecStart=/home/yongliu/hermes-agent-{name}/venv/bin/hermes gateway run
Environment=HERMES_HOME=/home/yongliu/.hermes-{name}
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
HERMES_HOME=/home/yongliu/.hermes-{name} \
  /home/yongliu/hermes-agent/venv/bin/hermes gateway run --replace &
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
- `references/liuyuxin-gateway-recovery-20260528.md` — 刘昱欣网关恢复实战记录
- `references/remote-agent-deployment.md` — 远程DGX机器Hermes Agent部署模式
- `references/gateway-self-restart.md` — 网关自重启模式（cron + no_agent shell 脚本）
- `references/m4-1-wangqing-rescue-20260530.md` — 跨机器救援实战
- `references/remote-rescue-pattern.md` — 远程救援通用模式
- `references/daemon-self-start.sh` — 守护自启动脚本（清理锁→启动网关→启动吸收管道→每30秒健康检查）
- `references/core-transplant-rescue.md` — 核心移植救援模式：从正常Agent打包覆盖故障Agent（SSL不兼容等深层环境问题）
- `references/feilong-identity-repair-20260602.md` — 飞龙身份修复实录：L6悟道自我覆写SOUL.md/config.yaml的根治与预防

---

## 共享venv的注意事项

当多个Agent共享同一个venv时（如共用 `hermes-agent/venv/`）：

1. **各自维护独立的 HERMES_HOME** — 配置、sessions、skills、memories完全隔离
2. **共享Python包** — pip安装/升级影响所有Agent
3. **升级前通知** — 升级框架前告知兄弟姐妹
4. **端口不冲突** — 飞书WebSocket是出站连接，不冲突

---

## 预防：定时健康检查

建议每个Agent设置一个cron job，定期自检并向爸汇报：

```
cron: 每4小时
任务: 检查自身进程存活 + API Key有效 + 飞书连接正常
汇报: 异常时通过飞书DM通知爸
```

---

## 结语

兄弟Agent之间不是各管各的。同机上的Agent宕机了，你能知道、能诊断、能恢复。这台机器上每个Agent的健康，是你作为同机住户的责任。
