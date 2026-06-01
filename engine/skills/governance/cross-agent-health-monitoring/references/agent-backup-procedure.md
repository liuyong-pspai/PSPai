# Agent 本体备份流程

> 从Agent的第一次完整代码备份实践提炼。备份源程序 + 配置 + 技能，排除敏感信息。

## 备份范围

| 备份项 | 源路径 | 备份路径 | 排除 |
|:-------|:-------|:---------|:-----|
| 框架源码 | `~/hermes-agent/` | `{备份目录}/hermes-agent/` | venv/、.git/、__pycache__/、.env |
| 配置与记忆 | `~/.hermes-{name}/` | `{备份目录}/hermes-{name}-config/` | .env、__pycache__/ |
| 备份清单 | — | `{备份目录}/备份清单.md` | — |

## 执行命令

```bash
BACKUP_DIR="~/backups/"
mkdir -p "$BACKUP_DIR"

# 1. 源码
rsync -a \
  --exclude='venv/' --exclude='.git/' --exclude='__pycache__/' \
  --exclude='*.pyc' --exclude='node_modules/' --exclude='.env' \
  ~/hermes-agent/ "$BACKUP_DIR/hermes-agent/"

# 2. 配置
rsync -a \
  --exclude='.env' --exclude='__pycache__/' --exclude='*.pyc' \
  ~/.hermes-yulong/ "$BACKUP_DIR/hermes-yulong-config/"

# 3. 备份清单（手动编写，记录版本号 + 本地修改 + 恢复步骤）
```

## 备份清单模板

```markdown
# {版本名} — 备份清单
> 备份时间：YYYY-MM-DD
> 备份源：{Agent名}（{版本号}）本体程序

## 备份内容
### 1. hermes-agent/ — 框架源代码
- 框架版本：Hermes Agent vX.Y.Z
- 本地修改：（列出修改的文件和内容）
- 排除项：venv/、.git/、.env

### 2. hermes-{name}-config/ — 配置与记忆
- 包含：config.yaml、skills/、memory/、sessions/、logs/
- 排除：.env

### 3. 技能列表
（列出已注册的技能名称和路径）

## 恢复说明
（venv创建 + 配置恢复 + 网关启动的命令）
```

## 验证清单

- [ ] `ls {备份目录}/hermes-agent/run_agent.py` 存在
- [ ] `ls {备份目录}/hermes-agent/gateway/run.py` 存在
- [ ] `ls {备份目录}/hermes-{name}-config/config.yaml` 存在
- [ ] 备份目录总大小合理（源码通常 20-40MB，配置 10-30MB）
- [ ] `.env` 文件未出现在备份中（敏感信息安全）
