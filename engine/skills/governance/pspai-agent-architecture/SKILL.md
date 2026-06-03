---
name: pspai-agent-architecture
version: 1.1.0
description: |
  PSPAI品牌Agent的正确架构——如何将PSPAI身份/前端连接到Hermes引擎，
  使Agent拥有完整工具能力（终端/文件/搜索/记忆/委派等），同时对外呈现PSPAI身份。
  触发：创建新的PSPAI Agent、PSPAI UI后端对接、PSPAI工具能力缺失诊断。
triggers:
  - PSPAI后端
  - PSPAI架构
  - PSPAI工具
  - 创建PSPAI Agent
  - 小龙人后端
  - AIAgent集成
  - PSPAI能力
  - Hermes引擎对接
---

# PSPAI Agent Architecture

## 核心原则
**PSPAI和玉龙跑同一套引擎，只换人格配置。**

爸原话：*"现在你（刘玉龙）是怎么运行的？它（PSPAI）挂上UI以后就要怎么运行。他是PSPAI架构，身体里有15%的hermes框架维持稳定。这个不能去改。"*

PSPAI Agent 必须使用 Hermes 的 `AIAgent` 引擎（`run_agent.py`）。唯一变化的是系统提示词（身份）和配置。不要自己写 HTTP 代理绕过 Hermes——造出来的 Agent 只有壳没有工具。

## 正确架构

```
PSPAI UI (Static HTML/JS)
       │ HTTP JSON
       ▼
pspai_server.py (薄HTTP前端 — 只做路由)
       │ Python API
       ▼
Hermes AIAgent (run_agent.py)
       │
       ▼
DeepSeek API + 31个工具
```

PSPAI 服务器是身份层，接收 UI 的 HTTP 请求后委托给 Hermes AIAgent。Hermes 引擎提供 31 个工具、记忆、上下文管理等全部能力。

**PSPAI 绝不直接调 LLM。** 始终通过 Hermes AIAgent，它处理工具调用、上下文压缩、记忆、迭代管理。

## 三要三不要

### ✅ 要
1. 设置 `HERMES_HOME` 指向 PSPAI 发布目录
2. PSPAI 发布版有独立的 `.env`、`config.yaml`、`skills/`
3. 创建 AIAgent 时显式传入 `api_key` 和 `base_url`

### ❌ 不要
1. 裸HTTP代理直接调LLM——Agent声称有工具但全不能执行
2. 忘记传API Key——env里有但AIAgent构造没拿到，请求头变 `Bearer None`
3. 共用玉龙的 HERMES_HOME——会加载开发者的上下文文件和个人记忆

## Setup 步骤

### 1. 环境变量 + Python 路径
**必须用 Hermes venv 的 Python**，不能用系统 Python——Hermes 依赖 `fire`、`openai`、`yaml` 等包只在 venv 里。

```python
#!/usr/bin/env python3
# 运行命令：/home/yongliu/hermes-agent/venv/bin/python3 pspai_server.py

import os, sys
os.environ['HERMES_HOME'] = '/path/to/pspai-release'
sys.path.insert(0, '/path/to/hermes-agent')
```

### 2. API Key (.env)
```env
DEEPSEEK_API_KEY=sk-xxx
```

PSPAI 发布版需有独立 `.env`（不能共用玉龙的——玉龙的 `.env` 含 `HERMES_HOME` 重定向、飞书密钥等个人配置）。

### 3. 加载 PSPAI 系统提示词
```python
import yaml
with open(os.path.join(BASE_DIR, 'config.yaml')) as f:
    cfg = yaml.safe_load(f)
PSPAI_PROMPT = cfg.get('agent', {}).get('system_prompt', '')
```

### 4. 创建 Agent（完整配方）
```python
from run_agent import AIAgent

agent = AIAgent(
    model='deepseek-chat',          # 不需要 'deepseek/' 前缀
    provider='deepseek',            # 必须显式传，否则路径解析失败
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url='https://api.deepseek.com/v1',
    ephemeral_system_prompt=PSPAI_PROMPT,  # 注入PSPAI身份，覆盖Hermes默认
    skip_context_files=True,
    skip_memory=True,
    max_iterations=15,              # PSPAI对话不需要太深迭代
    quiet_mode=True,                # 生产环境静默模式
)
```

**四个必须显式传的参数**（不传会失败）：
- `provider='deepseek'` — 不做会走 `auto` 分支，provider 空字符串
- `api_key=` — 不做请求头变 `Bearer None`
- `base_url=` — 不做 endpoint 为空
- `ephemeral_system_prompt=` — 不做 Agent 自称 "Hermes Agent by Nous Research"

### 5. 处理对话 — 必须用 run_conversation
```python
def handle_chat(user_message):
    result = agent.run_conversation(
        user_message=user_message,
        system_message=PSPAI_PROMPT,  # 每次调用都显式传入
    )
    return result.get('final_response', '')
```

**🚨 不要用 `agent.chat()`** —— 它在嵌入模式下不保留系统提示词，LLM 会遗忘 PSPAI 身份，开始自称 Hermes Agent。`run_conversation()` 接收显式 `system_message` 参数，每次对话都重新注入身份。

### 6. 多角色隔离
```python
# 每个角色独立 AIAgent 实例
agents = {}  # key: char_index -> AIAgent

def get_agent(char_index):
    key = str(char_index)
    if key not in agents:
        agents[key] = AIAgent(
            model='deepseek-chat',
            provider='deepseek',
            api_key=API_KEY,
            base_url='https://api.deepseek.com/v1',
            ephemeral_system_prompt=PSPAI_PROMPT,
            skip_context_files=True,
            skip_memory=True,
            max_iterations=15,
            quiet_mode=True,
        )
    return agents[key]
```

每个角色独立 Agent 实例，避免对话上下文串扰。

## DeepSeek Provider 配置

Hermes 内置（`hermes_cli/auth.py`），无需 `custom_providers`：
```python
"deepseek": ProviderConfig(
    id="deepseek",
    auth_type="api_key",
    inference_base_url="https://api.deepseek.com/v1",
    api_key_env_vars=("DEEPSEEK_API_KEY",),
)
```

## 多语言支持 — 系统提示词注入模式

前端传 `lang` 参数到 `/api/chat`，后端必须把语言指令注入**系统提示词**末尾——不是用户消息前缀。

### 为什么不能用用户消息前缀

```
[Reply in English.] 用户说：Hello    ← 弱指令，系统提示词优先级更高
```

系统提示词里全是中文规则 → LLM 根本不理用户消息里的 `[Reply in English.]`。

### 正确做法

```python
lang = data.get("lang", "zh")
if lang == "en":
    lang_injection = (
        "\n\n## LANGUAGE REQUIREMENT\n"
        "You MUST reply in English. All your responses must be in English. "
        "Do NOT use Chinese."
    )
    system_prompt = PSPAI_SYSTEM_PROMPT + lang_injection
else:
    system_prompt = PSPAI_SYSTEM_PROMPT

result = agent.run_conversation(
    user_message=context_msg,
    system_message=system_prompt,  # ← 注入后的提示词
)
```

### 症状诊断

| 症状 | 原因 | 修复 |
|------|------|------|
| 前端切英文后LLM仍回复中文 | 语言指令在用户消息前缀而不是系统提示词 | 注入到 `system_message` |

## 关键文件

| 文件 | 用途 |
|------|------|
| `/home/yongliu/hermes-agent/run_agent.py` | AIAgent 类 |
| `~/桌面/小龙人发布版本/config.yaml` | PSPAI 系统提示词 + provider |
| `~/桌面/小龙人发布版本/.env` | API Key |
| `~/桌面/小龙人发布版本/skills/` | 清理后的技能库 (27个) |

## 故障排查

| 症状 | 原因 | 修复 |
|------|------|------|
| Agent 声称有10项技能但全不执行 | pspai_server.py 绕过 Hermes 直接调 LLM | 改用 Hermes AIAgent |
| `Bearer None` / 401 | API Key 未传进 AIAgent 构造函数 | 显式传 `api_key=` + `base_url=` |
| Warning: API key appears invalid (got: 'none') | 同上 | 同上 |
| 上下文文件被注入 | 没设 `skip_context_files=True` | 加上 |
| 加载了开发者的个人记忆 | 没设 `HERMES_HOME` 到 PSPAI 目录 | 设置正确路径 |
| Agent 自称 "Hermes Agent by Nous Research" | 没用 `ephemeral_system_prompt` 注入 PSPAI 身份 | 传 `ephemeral_system_prompt=PSPAI_PROMPT` |
| 同上，即使传了 ephemeral_system_prompt 仍自称 Hermes | 用了 `agent.chat()` 而非 `run_conversation()` | 改用 `run_conversation(user_message, system_message=PSPAI_PROMPT)` |
| `ModuleNotFoundError: No module named 'fire'` | 用了系统 Python 而非 Hermes venv | 用 `/home/yongliu/hermes-agent/venv/bin/python3` |
| Endpoint 为空字符串 | provider 未显式传或传入错误格式 | 传 `provider='deepseek'` |

## 经验教训 (2026-06-01)

> 详细测试记录：`references/integration-test-results.md`

原始 `pspai_server.py` 是一个用 `http.server` + `urllib.request` 直连 DeepSeek 的裸代理。系统提示词里列了 10 项技能（终端/文件/搜索/记忆/委派等），但 LLM 只能**念出来**——它没有任何工具可以真正执行。用户在 UI 里看到 Agent 自称"我能帮你做这些"，但所有的操作型指令都会失败。

根因：PSPAI 没用 Hermes 引擎。修复：重写后端使用 `AIAgent`，31 个工具全量加载。
