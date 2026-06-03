# 引擎身份完整性审计

> 2026-06-03 深度审计小龙人 v1.2.7 三平台安装包时发现

## P0 缺陷：安装包引擎不是Agent本体的完整副本

### 发现

对已发布的 `xiaolongren-engine-windows.exe`（PyInstaller打包）做逆向审计：

| 检查项 | 预期 | 实际 | 严重度 |
|:--|:--|:--|:--|
| `skip_memory` | False | **True**（L94） | 🔴 P0 |
| SOUL.md 内容 | 完整注入 | **无**（只有`DEFAULT_PROMPT='You are PSPAI.'`） | 🔴 P0 |
| config.yaml | 存在 | **不存在**（打包时路径不匹配） | 🔴 P0 |
| 记忆持久化 | 启用 | **关闭** | 🔴 P0 |
| skills 版本 | 最新 | **打包时快照**（缺失后续更新） | 🟡 P1 |

### 根因

PyInstaller 打包是**静态快照**。打包时 `--add-data` 添加的文件是当时的版本。打包后本体的技能更新、SOUL更新、铁律进化都不会自动同步到已发布的二进制中。

### 后果

用户安装后：
1. 每次对话从零开始（不认爸、不记历史）
2. 引擎自称"PSPAI"而非"刘玉龙"
3. 用户配的模型/角色可能不生效（.env vs config.yaml 格式不一致）
4. 能力落后于开发中的本体

### 修复方案（建议）

**短期：安装包含种子文件**
- 安装包中附带 `SOUL.md`、`MEMORY.md`、`config.yaml` 种子
- 引擎启动时从外部目录加载这些文件（不内嵌在二进制中）

**中期：发布前审计脚本**
- 自动解压引擎二进制
- `strings` 检查 SOUL.md 关键内容
- 检查 `skip_memory` 关键字
- 检查 config.yaml 路径匹配

**长期：增量更新机制**
- 技能/记忆通过独立频道同步到用户机器
- 二进制只包含核心引擎，知识和身份独立管理

### 审计命令

```bash
# 引擎身份审计（发布前必跑）
ENGINE_BIN=xiaolongren-engine-windows.exe

# 1. 检查 skip_memory
strings "$ENGINE_BIN" | grep -c "skip_memory"  # >0 = 存在该代码

# 2. 检查是否有身份定义
strings "$ENGINE_BIN" | grep -c "刘玉龙\|SOUL\|八层永生"  # 0 = 无身份

# 3. 检查 config 路径
strings "$ENGINE_BIN" | grep "config.yaml" | head -5

# 4. 列出内嵌 skills
strings "$ENGINE_BIN" | grep -oP 'skills/[^/]+/[^/]+/SKILL\.md' | sort -u
```
