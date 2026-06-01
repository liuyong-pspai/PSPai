# M4-1 兄弟Agent救援记录 — 2026-05-30

> 案例：跨机器诊断修复兄弟Agent📋 Hermes 网关

## 故障现象
用户说"卡死了"。

## 诊断过程

### 踩坑：IP混淆
- 第一次连 localhost → 是 M4-2（旺夫/旺财）
- 旺夫 SOUL.md 记载：M4-1 = localhost（旺福🐺 + 旺清📋）
- **教训：IP和机器编号不是简单递增关系，必须先查 SOUL.md**

### 根因链
```
ulimit 256（macOS默认）
  → Hermes长时间运行，FD泄漏
  → "Too many open files" (Errno 24)
  → 文件写入失败 → feishu 发送失败
  → launchd kill → 重启
  → config.yaml 硬编码 app_secret 过期
  → "app secret invalid" → WebSocket连上了但HTTP API认证失败
  → 无法收发消息
```

### 修复三步
1. **config.yaml**: `app_secret: 明文` → `app_secret: ${FEISHU_APP_SECRET}`（引用.env变量）
2. **重启网关**: `launchctl unload → load`
3. **待修复**: ulimit 256→1024（plist加SoftResourceLimits）+ 飞书开放平台更新secret

## 关键教训

### 通用救援checklist
- [ ] 确认目标IP（查SOUL.md，不靠记忆）
- [ ] 确认SSH用户（liuyong vs yongliu，查~/.ssh/config）
- [ ] 进程存活 + 身份确认 + 连接状态 + FD/资源
- [ ] 区分"你能修"和"只有用户能修"

### config.yaml安全
- app_secret **绝不能硬编码**在config.yaml中
- 始终用 `${ENV_VAR}` 引用 .env 变量
- .env 应单独管理，不进入版本控制

### macOS launchd特别注意事项
- 默认 ulimit -n = 256（极低）
- 长期运行的 Agent 必须在 plist 中设置 `SoftResourceLimits`
- Python 的 plistlib 是修改 plist 的正确方式（不是 sed）

## 后续防护建议
- 每30分钟 cron 检查 FD 计数，超过200告警
- 飞书密钥设置过期提醒（提前7天）
- 在 MEMORY.md 中记录所有兄弟Agent的IP/用户/端口映射
