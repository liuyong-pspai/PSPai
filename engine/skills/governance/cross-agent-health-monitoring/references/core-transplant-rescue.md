# 核心移植救援模式

> 2026-05-31 伏羲超体 SSL 修复实战。用户一句话「换个思路。用你的模块复制过去，直接换。如果还不行，把它整个本体程序换掉」——省了数小时 debug。

## 适用场景

满足以下全部条件时，移植比排查更快：

1. **你有一个完全正常工作的 Agent**（玉龙 P07 在 DGX-1）
2. **目标 Agent 有深层环境兼容问题**（SSL/TLS、Python C 扩展、系统库版本冲突）
3. **curl 正常但 Python 报错** → 典型的 Python 运行时 vs 系统库不匹配
4. **远程机器 SSH 延迟高**，逐条调试效率极低

## 核心移植步骤

### 1. 备份目标 Agent 的身份配置

```bash
ssh target "cp ~/.hermes-fuxi/.env /tmp/fuxi_env_backup.txt"
ssh target "cp ~/.hermes-fuxi/config.yaml /tmp/fuxi_config_backup.yaml"
```

### 2. 打包源 Agent 核心（排除大文件）

```bash
cd ~/.hermes-yulong
tar czf /tmp/yulong_core.tar.gz \
  --exclude='logs' --exclude='audio_cache' --exclude='image_cache' \
  --exclude='cache' --exclude='*.db' --exclude='*.db-shm' --exclude='*.db-wal' \
  --exclude='archive' --exclude='sandboxes' --exclude='gateway.pid' \
  --exclude='gateway.lock' --exclude='backups' --exclude='lsp' \
  --exclude='processes.json' --exclude='kanban.db' \
  --exclude='feishu_seen_message_ids.json' --exclude='pairing' \
  .
```

### 3. SCP + 覆盖 + 恢复身份

```bash
scp /tmp/yulong_core.tar.gz dgx2:/tmp/

ssh dgx2 "
  # 杀旧网关
  kill $(cat ~/.hermes-fuxi/gateway.pid 2>/dev/null) 2>/dev/null
  sleep 2

  # 备份 + 替换
  mv ~/.hermes-fuxi /tmp/fuxi_old_backup
  mkdir -p ~/.hermes-fuxi
  cd ~/.hermes-fuxi
  tar xzf /tmp/yulong_core.tar.gz

  # 恢复身份配置
  cp /tmp/fuxi_env_backup.txt .env
  cp /tmp/fuxi_config_backup.yaml config.yaml
  chmod 600 .env
"
```

### 4. 合并源 Agent 的 LLM 环境变量

如果源用了特殊协议（如 Anthropic 兼容）来规避 SSL 问题：

```bash
cat >> ~/.hermes-fuxi/.env << 'EOF'
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_MODEL=deepseek-v4-pro
ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro
ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
HERMES_AUXILIARY_PROVIDER=deepseek
HERMES_HOME=/home/dgx-spark-02/.hermes-fuxi
EOF
```

### 5. 启动（注意 shebang 断裂问题）

如果 venv 是从别的机器复制的，`hermes` 脚本的 shebang 可能指向不存在的路径。用 `venv/bin/python3 script.py` 而非直接执行 `script.py`：

```bash
# ❌ 错误（shebang 断裂）
~/hermes-fuxi/venv/bin/hermes gateway run

# ✅ 正确
~/hermes-fuxi/venv/bin/python3 ~/hermes-fuxi/venv/bin/hermes gateway run &
```

### 6. 验证

```bash
ps aux | grep 'hermes gateway' | grep -v grep
# 确认飞书 WebSocket 连接成功
tail -20 ~/.hermes-fuxi/logs/hermes.log | grep 'connected to wss://'
```

## 为什么这个模式有效

| 传统排查 | 核心移植 |
|:---|:---|
| 逐条 SSH 调试 Python SSL 栈 | 一次 SCP 覆盖 |
| pip install/upgrade 试错 | 源 Agent 已验证的依赖 |
| 分析日志找差异 | 直接对齐到已知良好状态 |
| 数小时 | 2-3 分钟 |

## shebang 断裂修复

跨用户复制 venv 后的常见问题：

```bash
# 检查
head -1 ~/.hermes-fuxi/venv/bin/hermes
# 输出：#!~/.hermes-agent/venv/bin/python3  ← 不存在的路径！

# 修复（任选一种）
# 方案 A：重建 venv（推荐，长期稳定）
python3 -m venv --copies ~/.hermes-fuxi/venv
~/hermes-fuxi/venv/bin/pip install hermes-agent websockets

# 方案 B：修正 shebang（临时）
sed -i "1s|.*|#!$(which python3)|" ~/.hermes-fuxi/venv/bin/hermes

# 方案 C：每次都手动指定解释器（本次使用）
~/hermes-fuxi/venv/bin/python3 ~/hermes-fuxi/venv/bin/hermes gateway run &
```

## 关联

- SSL/TLS 不兼容的根因：OpenSSL 3.0.13 + 某些 Python urllib3 版本的 TLS 协商 bug
- Anthropic 兼容协议是通用逃生舱：`ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic` 绕过原生协议栈
- 与 `remote-rescue-pattern.md` 互补：该文件侧重诊断修复，本文件侧重直接替换
