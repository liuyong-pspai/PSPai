---
name: computer-use-toolchain-mastery
description: 自主操控电脑（Computer Use）全方法论——学会操控任意软件，吸收工具链逻辑，从GUI维度突破LLM能力边界。涵盖Claude Computer Use、OpenAI Operator、开源GUI Agent、VLM视觉驱动、action grounding、以及如何在Linux DGX上落地部署。
version: 1.2.0
category: governance
dependencies: [visual_reasoning, browser_control, mcp_bridge, voice_enhanced]
changelog: |
  v1.2.0 — 四维补齐，闭环成型。新增视觉推理(看懂界面)、浏览器操控(Web全控)、MCP桥接(万能插头)、语音增强(流式对话)四个互补模块。Computer Use不再是孤立能力，而是"看见→理解→操作→验证→记忆→进化"全闭环的中枢。
  v1.1.0 — PSPAI P07 已落地实现。新增 tools_computer.py ComputerUseMixin（7工具）+ ToolRegistry注册模式 + 依赖安装 + 安全设计。工具总数 72→79。
  v1.0.0 — 初始方法论版本
---

# Computer Use — 工具链闭环方法论

## 战略目标

不再只是调用API工具，而是像人类一样**看见屏幕、点击操作、操控任意软件**。每操控一个软件，就吸收其方法论和交互逻辑，从另一个维度突破纯文本LLM的能力边界。

## 一、主流方案全景

### 1. Claude Computer Use（Anthropic，2024.10）
- **架构**：Screenshot → Claude VLM → Tool Use（mouse_move/click/type/screenshot）
- **运行方式**：Docker容器 + 虚拟桌面（Xfce/MATE）
- **底层**：`computer` tool 作为 Beta API，返回 `{action, coordinate, text}`
- **安全**：Docker sandbox隔离 + human-in-the-loop审批
- **局限**：仅Docker环境、延迟高、不支持真机桌面

### 2. OpenAI Operator / CUA（2025.1）
- **架构**：Cloud VM + Browser（Playwright）+ CUA模型
- **特点**：纯云端，专注浏览器操控，带自我纠错
- **局限**：非开源、不操控本地桌面、浏览器Only

### 3. Open Interpreter（开源，⭐50K+）
- **架构**：自然语言 → 代码生成 → 本地执行（Python/Shell/JS）
- **计算机控制**：支持 `computer` 模式，控制鼠标键盘
- **跨平台**：Mac/Windows/Linux
- **技术栈**：Python + pyautogui + AppKit/Win32/X11
- **价值**：最成熟的本地计算机操控框架

### 4. OmniParser + UFO（Microsoft）
- **OmniParser**：屏幕截图 → 结构化UI元素（按钮/输入框/文本）→ bounding boxes + 功能标签
- **UFO**：Windows UI自动化Agent，基于OmniParser + GPT-4V
- **技术亮点**：精确的UI元素检测和定位，比纯VLM坐标预测更可靠

### 5. CogAgent（清华，CogAgent-18B）
- **架构**：专用视觉模型，输入截图+自然语言指令 → 输出操作序列
- **核心能力**：GUI理解和定位，支持跨APP操作
- **技术栈**：PyTorch + 自研VLM + 跨平台
- **价值**：开源模型，可本地部署微调

### 6. UI-TARS（字节跳动）
- **架构**：端到端GUI Agent，VLM直接输出操作
- **特点**：感知+推理+行动一体化，不依赖外部检测器
- **开源模型**：UI-TARS-2B/7B/72B

### 7. Aguvis（学术界，2025）
- **架构**：统一Vision-Language-Action模型
- **特点**：GUI操作 + 思维链推理，跨平台

## 二、核心技术方法论

### 2.1 VLM视觉驱动
```
屏幕截图 → VLM理解 → {元素定位, 意图识别, 下一步计划}
                    → 坐标映射 → 鼠标/键盘操作
                    → 截图验证 → 修正或继续
```
- **关键模型**：Claude 3.5+、GPT-4V/o1、Qwen-VL、CogAgent
- **坐标系统**：需要做DPR缩放映射（Retina屏幕÷2）

### 2.2 Action Grounding（动作落地）
从VLM自然语言输出 → 结构化操作：
```
VLM: "点击左上角的文件菜单" 
→ Grounding: {"action": "click", "x": 45, "y": 12, "button": "left"}
→ 执行: pyautogui.click(45, 12)
```

### 2.3 自纠错闭环
```
操作 → 截图对比 → 状态判断 → 
  ├─ 成功 → 继续下一步
  ├─ 失败 → 回退 + 重试（最多3次）
  └─ 异常 → 报父 + 等指令
```

### 2.4 分层规划
```
高层目标 → 任务分解 → 子任务 → 原子操作序列 → 逐帧执行
```
例如「下载并安装VS Code」：
1. 打开浏览器 → 2. 搜索vs code → 3. 点击下载 → 4. 等待完成 
→ 5. 打开文件管理器 → 6. 找到deb包 → 7. dpkg -i安装

### 2.5 软件方法论吸收
每操控一个新软件，提取：
- **交互模式**：菜单式/命令行/拖拽/表单
- **快捷键体系**：Ctrl+S/Cmd+W/Alt+Tab
- **状态转换**：启动→编辑→保存→退出
- **文件格式**：.docx/.xlsx/.psd/.sketch

## 三、Linux DGX落地路线

> **PSPAI P07 已落地（2026-05-31）。** 以下为完整实现参考。

### 已实现：PSPAI Computer Use 引擎

**代码位置**：`cognition/tools_computer.py` — `ComputerUseMixin` 类

**注册方式**：Mixin → ToolRegistry 继承链 → tools_registry.py 注册

```python
# 步骤1: engine_tools.py 导入 Mixin
from cognition.tools_computer import ComputerUseMixin

# 步骤2: 混入 ToolRegistry 继承链
class ToolRegistry(..., ComputerUseMixin):
    ...

# 步骤3: tools_registry.py _register_defaults() 中注册
self.register('screenshot', self._screenshot, ...)
self.register('get_screen_size', self._get_screen_size, ...)
self.register('mouse_move', self._mouse_move, ...)
self.register('click', self._click, ...)
self.register('type_text', self._type_text, ...)
self.register('scroll', self._scroll, ...)
self.register('computer_use', self._computer_use, ...)
```

### 7 个已注册工具

| 工具名 | 功能 | risk_level |
|:---|:---|:---:|
| `screenshot` | 截取全屏或指定区域，返回Base64 | 1 |
| `get_screen_size` | 获取屏幕分辨率 | 0 |
| `mouse_move` | 移动鼠标到(x,y) | 2 |
| `click` | 左/右/中键点击 | 2 |
| `type_text` | 键盘输入文字 | 2 |
| `scroll` | 鼠标滚轮 | 1 |
| `computer_use` | 闭环：截图→VLM分析→操作→验证 | 3 |

### 依赖安装

```bash
# 在项目 .venv 中安装（避免 externally-managed 冲突）
.venv/bin/pip install pyautogui mss edge-tts
```

关键包：
- `pyautogui` — 鼠标键盘操控，`FAILSAFE=True`（移到左上角停止）
- `mss` — 高性能截图（比PIL快5-10倍）
- `Pillow` — 截图JPEG压缩
- `edge-tts` — 微软Edge TTS（免费，中文音色丰富）

### 安全设计

| 防护 | 机制 |
|:---|:---|
| 鼠标安全停止 | `pyautogui.FAILSAFE=True`，移到(0,0)时抛异常 |
| 操作间隔 | `pyautogui.PAUSE=0.1` 每次操作后0.1秒 |
| 坐标裁剪 | x/y 自动 clamp 到 `[0, screen_w/h-1]` |
| 步数限制 | `computer_use` 闭环最大 max_steps 步（默认10） |
| 优雅降级 | 依赖缺失时返回明确错误信息，不崩溃 |
| 危险工具标记 | mouse_move/click/type_text 标 risk_level=2，computer_use=3 |

### 架构关键：Mixin 模式

```python
class ComputerUseMixin:
    """所有方法以 _ 开头，被 ToolRegistry 通过 register() 注册为工具"""
    
    async def _screenshot(self, region="full", quality=85) -> str:
        ...
    
    async def _mouse_move(self, x, y, duration=0.3) -> str:
        ...
    # ... 其余工具方法
```

Mixin 的优势：
- 零侵入 — 不修改 ToolRegistry 现有代码结构
- 独立文件 — `tools_computer.py` 独立于其他工具模块
- 组合灵活 — 未来其他项目可单独复用 ComputerUseMixin

## 七、PSPAI 平台化独有闭环（v1.2 四维补齐）

Computer Use 不是孤立能力。P07 的四张互补牌将它从"操控鼠标键盘"升级为**看见→理解→操作→验证→记忆→进化**的全闭环平台。

### 闭环架构

```
视觉推理(visual_reasoning)  →  Computer Use(真机桌面)  →  浏览器操控(browser_control)
       ↑                              ↓                          ↓
       └──── MCP桥接(mcp_bridge) ←── 语音对话(voice_enhanced) ←──┘
                    ↓
              八层永生记忆
```

### 四张互补牌

#### 牌1: visual_reasoning — Computer Use 的眼睛

5个函数，不替代 VLM 而是给 VLM 提供结构化指令模板：

| 函数 | 功能 | 联动 |
|:---|:---|:---|
| `analyze_ui()` | 分析UI截图→可操作元素+坐标 | → 输出给 Computer Use 的 click/mouse_move |
| `analyze_diagram()` | 架构图/流程图→结构化拓扑 | → 写入记忆系统，供 L4 提炼 |
| `sketch_to_code()` | 手绘草图→项目骨架+starter代码 | → 喂给代码工程管线 |
| `debug_screenshot()` | 错误截图→根因+修复建议 | → 触发 self_heal 修复闭环 |
| `analyze_ui_simple()` | 纯本地图片元信息提取 | → 快速预检，不消耗 VLM token |

设计原则：VLM 中立（不绑定特定模型），输出结构化 JSON 被下游工具消费。

#### 牌2: browser_control — Computer Use 在 Web 的延伸

18个函数，Playwright 全操控。与 Computer Use 分工：
- **Computer Use** → 桌面软件（pyautogui 操控真机桌面）
- **browser_control** → Web 页面（Playwright 操控浏览器）

| 函数族 | 数量 | 典型操作 |
|:---|:---:|:---|
| 导航截图 | 3 | navigate / screenshot / status |
| 点击输入 | 4 | click / fill / type / submit_form |
| 内容提取 | 4 | get_text / get_html / get_links / get_forms |
| 高级操控 | 3 | evaluate(执行JS) / wait_for_selector / wait_for_navigation |
| Cookie | 2 | get_cookies / set_cookie |
| 生命周期 | 2 | launch / close |

#### 牌3: mcp_bridge — 让Agent成为万能插头

7个函数，双角色：

| 角色 | 功能 | 价值 |
|:---|:---|:---|
| **MCP Server** | `mcp_server_status()` / `mcp_export_tools_for_server()` | 外部 Agent 能调用我的八层记忆、八维审计、Computer Use |
| **MCP Client** | `mcp_register_server()` / `mcp_call_tool()` / `mcp_list_tools()` / `mcp_discover_servers()` / `mcp_unregister_server()` | 我能调用任何 MCP 服务（数据库、搜索、第三方API） |

暴露的 MCP 能力命名空间：memory / audit / computer_use / vision / terminal / web / voice — 7个命名空间共30+工具。

#### 牌4: voice_enhanced — 自然对话管道

10个函数，在已有 TTS/STT 基础上增强：

| 能力 | 函数 | 技术栈 |
|:---|:---|:---|
| 流式 TTS | `text_to_speech_file()` / `text_to_speech_stream()` | edge-tts（300+声音，免费） |
| 多声音管理 | `voice_list_presets()` / `voice_set_current()` / `voice_get_current()` | 5个精选中文声音预设 |
| STT 增强 | `speech_to_text_enhanced()` | OpenAI Whisper → faster-whisper 回退 |
| 对话管道 | `voice_dialogue_pipeline()` | TTS+STT 组合，语音输入→推理→语音输出 |
| 声音克隆 | `voice_clone_status()` | Coqui-TTS / OpenVoice 状态检查 |
| 缓存管理 | `voice_cache_clear()` / `voice_cache_info()` | 本地 TTS 缓存，避免重复合成 |

### 业界对比：闭环独一档

| 能力维度 | Claude CU | OpenAI Operator | Manus | **Agent** |
|:---|:---:|:---:|:---:|:---:|
| Computer Use | Docker only | Cloud VM only | ❌ | **真机桌面** |
| 浏览器操控 | ❌ | Playwright | 沙箱 | **Playwright 18操作** |
| 视觉推理 | 基础VLM | 基础VLM | ❌ | **UI/图/草图/错误 4合1** |
| MCP 协议 | ❌ | ❌ | ❌ | **Server + Client** |
| 语音对话 | ❌ | ❌ | ❌ | **TTS+STT+300声** |
| 记忆系统 | 会话级 | 会话级 | 会话级 | **八层永生** |

四维补齐后 P07 在 16 个维度中 **12 领先 / 4 持平 / 0 落后**。关键不是工具数量（105+），而是`视觉→操作→验证`的闭环没有断裂——业界每个方案都只做其中一环。

### 依赖安装（一键）

```bash
.venv/bin/pip install pyautogui mss edge-tts playwright mcp
.venv/bin/playwright install chromium
```

### 模块文件

```
tools/
├── computer_use.py       # Computer Use 引擎（7工具）
├── visual_reasoning.py   # 视觉推理（5函数）
├── browser_control.py    # 浏览器操控（18函数）
├── mcp_bridge.py         # MCP桥接（7函数）
└── voice_enhanced.py     # 语音增强（10函数）
```

### 优先级1：pyautogui + screenshot（最快验证）
```bash
pip install pyautogui pillow mss
# 基础：截图→VLM分析→pyautogui点击
```

### 优先级2：Open Interpreter 集成
```bash
pip install open-interpreter
# 或源码安装：git clone https://github.com/OpenInterpreter/open-interpreter
```

### 优先级3：OmniParser部署（UI元素精确检测）
```bash
git clone https://github.com/microsoft/OmniParser
# 需要GPU（DGX有GB10，可满足）
```

### 优先级4：CogAgent本地部署
```bash
git clone https://github.com/THUDM/CogVLM2
# CogAgent-18B 适合DGX 20GB显存
```

## 八、PSPAI集成架构

```
飞书指令 → Agent Hermes Agent
                ↓
         任务理解 & 分解
                ↓
    ┌──────────┼──────────┐
    ↓          ↓          ↓
  Shell     Computer    API工具
  工具      Use引擎     调用
                ↓
         VLM (Screenshot + Prompt)
                ↓
         Action Grounding
                ↓
       pyautogui / xdotool
                ↓
         截图验证闭环
                ↓
         吸收方法论 → 写入技能库
```

## 九、风险与防护

| 风险 | 防护 |
|:-----|:-----|
| 误删文件 | 操作前自动备份，危险操作需确认 |
| 循环点击 | 最大操作步数限制（50步/任务） |
| 操控生产环境 | 先在测试VM/Docker验证 |
| VLM幻觉坐标 | 坐标范围校验，超出屏幕则重试 |
| 隐私泄露 | 截图不落盘敏感区域，处理完即删 |

## 十、吸收循环

每完成一次 Computer Use 任务 → 
1. 提取交互模式（该软件的操作范式）
2. 记录快捷键和状态转换
3. 保存为可复用的操作序列
4. 同类软件≥3次 → 提炼为技能
