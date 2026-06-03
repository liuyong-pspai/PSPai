# PSPAI 后端接入 Hermes 引擎

> 让 PSPAI Web UI 的后端跑在 Hermes AIAgent 上，拥有完整工具链。
> 核心原则：**PSPAI 身份 + Hermes 引擎 = 完整能力。**

## 架构

```
UI(8088 HTTP静态) → pspai_server.py(8089) → Hermes AIAgent → LLM + 32 tools
                                                  ↑
                                          工具来自 hermes-agent/tools/
                                          人格来自 PSPAI config.yaml
```

## 关键步骤

### 1. 必须用 Hermes venv 启动

```bash
cd <pspai-release-dir>
/home/yongliu/hermes-agent/venv/bin/python3 pspai_server.py
```

### 2. 环境变量设置

```python
import os, sys
os.environ['HERMES_HOME'] = str(BASE_DIR)  # PSPAI发布目录
sys.path.insert(0, '/home/yongliu/hermes-agent')
```

### 3. 创建 AIAgent 实例

```python
from run_agent import AIAgent

agent = AIAgent(
    model='deepseek-chat',
    provider='deepseek',
    api_key=API_KEY,           # 必须显式传入
    base_url='https://api.deepseek.com/v1',  # 必须显式传入
    ephemeral_system_prompt=PSPAI_SYSTEM_PROMPT,  # PSPAI人格
    skip_context_files=True,    # 不加载宿主上下文
    skip_memory=True,           # 不加载宿主记忆
    max_iterations=15,          # 限制工具调用轮次
    quiet_mode=True,
)
```

### 4. 使用 run_conversation() 而非 chat()

```python
# ❌ chat() 可能不使用 ephemeral_system_prompt
result = agent.chat(message)

# ✅ run_conversation() 显式传入 system_message
result = agent.run_conversation(
    user_message=message,
    system_message=PSPAI_SYSTEM_PROMPT,
)
reply = result.get('final_response', '')
```

## 常见问题

### toolsets 配置缺少 "web"

**现象**: web_search 已注册覆盖，但 `get_tool_definitions()` 中仍不出现

**原因**: `config.yaml` 的 `toolsets` 列表只配了 `[hermes-feishu, yulong]`，缺 `web`。`get_tool_definitions()` 只从已启用的工具集中选工具，不在列表中就不会出现。

**修复**: config.yaml 添加 `web` 到 toolsets：
```yaml
toolsets:
  - hermes-feishu
  - yulong
  - web          # ← 必须加这一行
```

### 工具注册覆盖的时机

`_discover_tools()` 在 `model_tools.py` 模块导入时立即执行。pspai_search 必须在 AIAgent 导入**之后**再导入，才能覆盖原始注册：

```python
from run_agent import AIAgent  # ← 触发 _discover_tools()，web_search 用原始 check_fn
import pspai_search             # ← 覆盖为 check_fn=lambda: True
```

如果反过来（先 import pspai_search 再 import run_agent），会被 web_tools.py 的原始注册覆盖回来。

### .env 必须含 DEEPSEEK_API_KEY

PSPAI 发布版不包含 .env（出于安全），部署时必须创建：
```bash
echo "DEEPSEEK_API_KEY=<实际key>" > /path/to/pspai-release/.env
```

### API Key 传入失败

**现象**: `Authorization: Bearer None`，`api_key` 自动解析失败

**原因**: AIAgent 的自动鉴权依赖 auth.json，PSPAI 环境没有

**修复**: 创建 AIAgent 时显式传入 `api_key=xxx` 和 `base_url=xxx`

### web_search 工具不可用

**现象**: 工具列表中无 web_search，模型报 "Unknown tool 'web_search'"

**原因**: Hermes 的 web_tools 需要 Firecrawl/Tavily/Parallel/Exa 的 API Key，PSPAI 环境没配

**修复**: 写独立模块覆盖注册（见下方示例）

### 工具注册覆盖模式

```python
# pspai_search.py — 在 AIAgent 之后导入，覆盖 web_search
from run_agent import AIAgent  # 先触发原始工具发现
import pspai_search             # 再用 lambda:True 覆盖 check_fn

# pspai_search.py 内部：
from tools.registry import registry
registry.register(
    name="web_search",
    toolset="web",
    schema={...},
    handler=my_handler,
    check_fn=lambda: True,  # 永远通过
)
```

**注意**: 不要传 `override=True`，registry.register 不支持该参数，会自动覆盖同名工具。

## 依赖清单

| 依赖 | 用途 | 备注 |
|------|------|------|
| hermes-agent venv | AIAgent引擎 | `/home/yongliu/hermes-agent/venv/` |
| config.yaml | PSPAI人格配置 | 含 system_prompt + provider |
| .env | API Key | 至少含 DEEPSEEK_API_KEY |
| firecrawl (pip) | web_search后端 | 可选，需API Key |
| duckduckgo_search (pip) | 免费搜索后备 | 网络受限环境不可用 |

## 与身份边界的关系

PSPAI 的 `system_prompt` 控制身份输出（"我是中国人自己研发的AI智能体：小龙人"），Hermes 引擎只提供工具执行能力。二者职责分离：

- **PSPAI config.yaml** → 控制"说什么"
- **Hermes AIAgent** → 控制"能做什么"

详见 `references/product-identity-boundary.md`。
