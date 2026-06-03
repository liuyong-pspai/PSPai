# AGENTS.md 自动注入毒药 — 2026-05-29 发现

## 背景

2026年5月28日，一个会话撑了16小时，产生200+条消息反复问答。根因之一：`hermes-agent/AGENTS.md`(20KB) 被 Hermes Agent 框架自动发现并注入每次对话。

## 自动注入机制

Hermes Agent 自动扫描工作目录及子目录下的以下文件并注入 system prompt：
- `AGENTS.md`
- `CLAUDE.md`
- `.cursorrules`
- `.hermes.md`

由于我的工作目录是 `/home/yongliu`，`hermes-agent/` 是子目录，20KB 的 `AGENTS.md` 被自动发现。

## 伤害计算

每次对话注入量：
- SOUL.md → system_prompt：~8KB
- config.yaml system_prompt 文本：~5KB
- AGENTS.md 自动注入：~20KB
- MEMORY.md + USER.md：~4KB
- **合计：~37KB 每次对话的基础开销**

加上 213 条历史消息，轻松撑爆 DeepSeek 128K 上下文窗口。

## 修复方案

1. **覆盖法**：在 `~/.hermes-yulong/AGENTS.md` 创建空文件，Hermes 优先加载 hermes-home 下的版本
2. **配置法**：config.yaml 加 `skip_context_files: true`
3. **彻底法**：移动或删除 `hermes-agent/AGENTS.md`（不推荐——影响开发）

采用方案1+2，双保险。

## 教训

- 任何自动注入的上下文文件都是潜在的上下文杀手
- AGENTS.md 应该精简，不适合放完整开发指南
- 定期检查 context_files 注入量，防止沉默膨胀
