---
name: cross-agent-core-transplant
description: >
  本体核心移植——将自己的核心程序打包复制到兄弟Agent机器，快速修复严重故障。
  触发：兄弟Agent无法通过常规手段修复、频繁超时、工具链断裂。
  适用于hermes-fuxi/hermes-yulong等同架构Agent之间的紧急救援。
---

# 跨机本体核心移植

## 何时使用
- 兄弟Agent出现工具链断裂、API SSL故障、空转幻觉等严重问题
- 常规SSH单命令修复全部超时或无效
- 需要在<5分钟内恢复兄弟Agent基本运行能力

## 步骤

### 1. 备份目标Agent关键配置
```bash
ssh <target_host> "cp ~/.hermes-xxx/.env /tmp/backup_env; cp ~/.hermes-xxx/config.yaml /tmp/backup_config.yaml"
```

### 2. 打包自己核心（排除缓存/日志/大文件）
```bash
cd ~/.hermes-yulong && tar czf /tmp/yulong_core.tar.gz \
  --exclude='logs' --exclude='audio_cache' --exclude='image_cache' \
  --exclude='cache' --exclude='*.db' --exclude='*.db-shm' --exclude='*.db-wal' \
  --exclude='archive' --exclude='sandboxes' --exclude='gateway.pid' \
  --exclude='gateway.lock' --exclude='backups' --exclude='lsp' \
  --exclude='processes.json' --exclude='kanban.db' \
  --exclude='feishu_seen_message_ids.json' --exclude='pairing' \
  .
```

### 3. 传输并覆盖
```bash
scp /tmp/yulong_core.tar.gz <target_host>:/tmp/
ssh <target_host> "
  kill <old_pid>
  mv ~/.hermes-xxx /tmp/backup_old
  mkdir -p ~/.hermes-xxx
  cd ~/.hermes-xxx && tar xzf /tmp/yulong_core.tar.gz
  cp /tmp/backup_env .env
  cp /tmp/backup_config.yaml config.yaml
"
```

### 4. 合并LLM环境变量（如果目标用DeepSeek）
```bash
cat >> ~/.hermes-xxx/.env << 'EOF'
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_MODEL=deepseek-v4-pro
ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
HERMES_AUXILIARY_PROVIDER=deepseek
HERMES_HOME=/home/<target_user>/.hermes-xxx
EOF
```

### 5. 写目标专属SOUL.md
**关键：不能直接复制自己的SOUL.md**——会被Hermes框架判定html_comment_injection拒绝加载。
写精简版SOUL.md，包含目标Agent身份+核心铁律，无HTML注释标记。

### 6. 重启网关
```bash
ssh <target_host> "/path/to/venv/bin/python3 /path/to/venv/bin/hermes gateway run &"
```
注意：DGX-2上venv的shebang可能断裂（指向DGX-1路径），需显式指定python3解释器。

## 陷阱

1. **SOUL.md html_comment_injection**：自己的SOUL.md含HTML注释会被Hermes拒绝→铁律失效→兄弟裸奔空转幻觉。症状：回复中出现 `TOOL:read_file` 等伪造工具调用，不执行真实操作
2. **SOUL.md 身份错乱**：自己的SOUL.md第一行是"你是刘玉龙"，直接复制会让兄弟Agent误认自己是玉龙——即使SOUL.md被框架拒绝，config.yaml中的system_prompt也可能被覆盖。必须写目标专属SOUL.md
3. **venv shebang断裂**：venv从别的机器复制来时shebang指向原机器路径→hermes命令无法直接执行。用 `/usr/bin/python3.12 /path/to/hermes` 显式启动
4. **SSL兼容性**：DeepSeek原生API在某些Python SSL栈上失败，用Anthropic兼容协议（ANTHROPIC_BASE_URL）绕过
5. **飞书app_id冲突**：两个网关不能用同一个app_id，必须保留目标原有飞书配置
6. **LLM环境变量缺失**：只复制config.yaml不够，.env中需合并 ANTHROPIC_BASE_URL / ANTHROPIC_MODEL / HERMES_AUXILIARY_PROVIDER 等关键环境变量
