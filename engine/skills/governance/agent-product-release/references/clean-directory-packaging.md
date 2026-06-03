# 干净目录打包发布

> 当不需要内核编译（.so），而是直接发布源码+资源包时使用。
> 适用于：MVP原型发布、UI原型交付、战略文档合集。

## 打包原则

**必须包含：**
- 核心配置文件（config.yaml、agent_card.json）
- 身份/记忆文件（MEMORY.md、USER.md）
- 技能库（skills/）和脚本（scripts/）
- 记忆归档（memories_archive/）
- 产品原型文件（UI原型/）
- 战略文档（战略文档/）
- README.txt 发布说明

**必须排除：**
- `sessions/` `logs/` `image_cache/` `audio_cache/` `cache/` — 运行时数据
- `cron/` — cron任务输出
- `.git/` — 版本历史
- `gateway.*` `auth.*` `*.lock` — 运行时状态/安全令牌
- `__pycache__/` `.pytest_cache/` — 编译缓存
- `kanban.db` `.hermes_history` — 本地数据库

## 操作步骤

```bash
mkdir -p "/path/to/发布版本"
# 逐个目录显式复制，不用 cp -r *
cp config.yaml agent_card.json "/path/to/发布版本/"
cp memories/MEMORY.md memories/USER.md "/path/to/发布版本/"
cp -r memories/archive "/path/to/发布版本/memories_archive/"
cp -r skills "/path/to/发布版本/"
# 产品文件 + 文档
mkdir -p "/path/to/发布版本/UI原型"
cp prototype/*.html prototype/*.jpg "/path/to/发布版本/UI原型/"
mkdir -p "/path/to/发布版本/战略文档"
cp "集团日志/*.md" "/path/to/发布版本/战略文档/"
# 验证
find "/path/to/发布版本" -type f | wc -l
du -sh "/path/to/发布版本"
```

## 陷阱

- **不能用 `cp -r *` 全量复制** — 会把sessions/logs/cache带进去
- **逐个目录显式复制** — 确保只复制需要的
- **清理编译缓存** — __pycache__ 和 .pytest_cache 必须排除
- **README必须写** — 接收方需要知道内容结构和部署方式
