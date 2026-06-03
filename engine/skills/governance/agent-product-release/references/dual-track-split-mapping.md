# 双轨发布：文件拆分映射

> 2026-06-01 小龙人 v1.0 发布实战总结
> 核心原则：**皮可以换，魂换不了** — UI开源(皮)，引擎闭源(魂)

## 拆分决策矩阵

| 文件/目录 | 去向 | 理由 |
|:---|---:|:---|
| `pspai_server.py` | 🔒闭源 | PSPAI引擎，Agent思考调度逻辑 |
| `pspai_search.py` | 🔒闭源 | 搜索策略和算法，核心竞争力 |
| `skills/` | 🔒闭源 | 26个技能，Agent行为能力库 |
| `scripts/` | 🔒闭源 | 8个运维自动化脚本 |
| `config.yaml` | 🔒闭源 | 含中英文人格提示词，IP核心 |
| `agent_card.json` | 🔒闭源 | 工具注册表，能力清单 |
| `UI原型/index.html` | 📂开源 | 主界面，HTML/CSS/JS |
| `UI原型/lang/` | 📂开源 | 多语言包JSON |
| `UI原型/img_*.jpg` | 📂开源 | 角色占位图（客户可替换） |
| `UI原型/server.py` | 📂开源 | 多线程静态服务器 |
| `UI原型/prompts.html` | 📂开源 | 提示词管理页 |
| `start.sh` | 📂开源 | 一键启动脚本 |
| `.env.example` | 📂开源 | 环境变量模板（无密钥） |
| `requirements.txt` | 📂开源 | Python依赖清单 |
| `README.md` | 📂开源 | 双语使用说明 |
| `LICENSE` | 📂开源 | AGPLv3 + 品牌保护条款 |

## 绝对不能放入开源包的文件

- `SOUL.md` — 个人人格文件
- `MEMORY.md` — 持久记忆数据
- `USER.md` — 用户档案
- `sessions/` — 会话记录
- `logs/` — 运行日志
- `models_dev_cache.json` — 模型缓存
- `__pycache__/` — Python缓存
- `.git/` — 开发仓库历史
- IP地址/密钥/令牌 — 任何个人数据

## 客户能做什么 vs 不能做什么

**能做的（开源层）：**
- 改HTML/CSS/JS外壳、换颜色调布局
- 加语言包（丢JSON文件零代码改动）
- 替换角色图片为自己的IP
- 接自己的模型（改config.yaml provider字段）
- 用自己的品牌名重新发布（去除小龙人/PSPAI标识后）

**不能做的（闭源层）：**
- 看Agent怎么思考、怎么调度工具
- 修改技能库逻辑
- 偷工程方法论
- 反编译闭源二进制
