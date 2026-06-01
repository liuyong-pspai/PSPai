# 跨机器救援模式 — 从 M4-1 旺清修复实战提炼

> 来源：2026-05-30 Agent跨机器救援兄弟Agent📋

## 故障发现

用户说"XX卡死了" → 立即SSH到目标机器

## 救援五步法

### 0. 确认正确目标
- **不靠记忆**：IP和机器编号不是简单递增关系
- **查SOUL.md**：旺夫（其他兄弟）的SOUL.md通常记载完整的三机六智能体布局
- **查~/.ssh/config**：确认用户名（可能是liuyong而非yongliu）

### 1. 进程存活
```bash
ps aux | grep hermes | grep -v grep
```

### 2. 身份确认
```bash
head -5 ~/.hermes/SOUL.md
```

### 3. 四维诊断
```bash
# 连接状态
cat ~/.hermes/gateway_state.json

# FD泄漏
lsof -p {PID} | wc -l && ulimit -n

# 最近错误
tail -20 ~/.hermes/logs/gateway.log | grep -E 'ERROR|WARNING'

# DNS/网络
nslookup open.feishu.cn
```

### 4. 分层修复（先治标，再治本）
| 优先级 | 问题 | 修复 |
|:--|:--|:--|
| P0 | app_secret硬编码 | `sed` 改为 `${FEISHU_APP_SECRET}` |
| P0 | 进程僵死 | `launchctl unload/load` 重启 |
| P1 | FD泄漏 | plist加 `SoftResourceLimits.NumberOfFiles: 1024` |
| P1 | 密钥过期 | 飞书开放平台更新（只有用户能做） |

### 5. 分清边界
- ✅ Agent能修：配置引用、ulimit、重启、脚本部署
- ❌ 只有用户能修：API Key/Secret过期、飞书开放平台操作

## 关键教训

1. **连错机器的代价**：localhost ≠ M4-1，先查SOUL.md确认
2. **macOS ulimit坑**：默认256，Hermes长期运行必然FD泄漏
3. **硬编码密钥是定时炸弹**：config.yaml绝对不要写明文secret
4. **飞书密钥过期无预警**：需要定期检查或设置提醒
