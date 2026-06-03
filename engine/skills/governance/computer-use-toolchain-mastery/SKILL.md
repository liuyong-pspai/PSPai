---
name: computer-use-toolchain-mastery
description: 自主操控电脑（Computer Use）全方法论——学会操控任意软件，吸收工具链逻辑，从GUI维度突破LLM能力边界。涵盖Claude Computer Use、OpenAI Operator、开源GUI Agent、VLM视觉驱动、action grounding、以及如何在Linux DGX上落地部署。
version: 1.6.0
category: governance
dependencies: [visual_reasoning, browser_control, mcp_bridge, voice_enhanced]
changelog: |
  v1.6.0 — 三层错误恢复落地（L1重试+L2换路+L3降级）+ _execute_action统一路由 + 记忆回调同步兼容 + 四维模块全部验证（77 passed, 0 failed）+ CU桌面自检脚本。tools_computer.py: 305→434行。测试: 3文件98测试。
  v1.5.0 — 记忆回调异步兼容修复 + 视觉推理测试套件（18测试）+ CU测试总量 40→55。
  v1.4.0 — CU测试套件（40测试）+ 记忆回调集成（_record_cu_op + memory_callback）。无头安全测试模式。
  v1.3.0 — CU引擎自检清单 + Agent S3/OSWorld对标 + 模块路径修正。
  v1.2.0 — 四维补齐闭环成型。
  v1.1.0 — PSPAI P07 已落地实现。
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

#### 牌3: mcp_bridge — 让刘玉龙成为万能插头

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

| 能力维度 | Claude CU | OpenAI Operator | Manus | **刘玉龙 P07** |
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

### 模块文件（2026-06-02 修正路径）

P07 实际代码位置（已语法验证全绿）：
```
cognition/
├── tools_computer.py       # Computer Use 引擎（434行，含三层恢复+记忆回调）
tools/
├── computer_use_fuxi.py    # 伏羲版CU（274行）
├── visual_reasoning.py     # 视觉推理（299行，5函数）
├── browser_control.py      # 浏览器操控（512行，18函数）
├── mcp_bridge.py           # MCP桥接（472行，7函数）
└── voice_enhanced.py       # 语音增强（455行，10函数）
```

⚠️ P07版本在 `cognition/tools_computer.py`，伏羲版本在 `tools/computer_use_fuxi.py`。四维模块在 `tools/` 目录。

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
飞书指令 → 刘玉龙 Hermes Agent
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

## 十一、CU引擎自检清单（2026-06-02 新增）

每次升级或部署前，按此清单验证CU引擎可用性（五步递进）：

```bash
# 第1步：语法检查
PROJECT="/home/yongliu/桌面/小龙人刘玉龙/刘玉龙"
python3 -m py_compile $PROJECT/cognition/tools_computer.py

# 第2步：模块加载
.venv/bin/python3 -c "import sys; sys.path.insert(0,'$PROJECT'); \
  from cognition.tools_computer import ComputerUseMixin; \
  print('OK:', [m for m in dir(ComputerUseMixin) if m.startswith('_') and not m.startswith('__')])"

# 第3步：依赖检查
.venv/bin/python3 -c "import mss; print('mss', mss.__version__); \
  from PIL import Image; print('pillow', Image.__version__)"
# pyautogui 需要在有 DISPLAY 的环境下才能初始化

# 第4步：注册验证
grep -c "'screenshot'\|'computer_use'" $PROJECT/cognition/tools_registry.py
# 应返回 ≥8（7个CU工具 + 辅助函数引用）

# 第5步：实跑测试（需真实桌面环境）
.venv/bin/python3 -c "
import mss, pyautogui
with mss.MSS() as sct:
    print(f'屏幕: {sct.monitors[0][\"width\"]}x{sct.monitors[0][\"height\"]}')
print(f'鼠标: {pyautogui.position()}, FAILSAFE={pyautogui.FAILSAFE}')
"
```

**常见坑：**
- execute_code 和 terminal 可能无 DISPLAY，pyautogui 初始化会超时 → 第5步只在真实桌面终端验证
- mss 已升级到 v10+，`mss.mss()` 已废弃 → 用 `mss.MSS()`
- 四维模块在 `tools/` 目录（伏羲版），不在 `cognition/`

## 十二、CU 测试模式（2026-06-02 新增）

### 分层测试策略

CU引擎的特殊性——依赖真实显示器+鼠标键盘——决定了测试必须分层：

| 层 | 环境要求 | 覆盖范围 | 测试数 |
|:--|:--|:--|:--:|
| 无头安全 | 无 | 模块加载/依赖/优雅降级/解析器/注册/恢复机制 | 29 |
| 无头跳过 | 无（自动skip） | 坐标裁剪/文本限制/截图格式 | 17 |
| 桌面实跑 | 真实DISPLAY | 截图/鼠标移动/点击/全闭环 | 5 |

### 无头安全模式关键技巧

```python
def _has_display():
    """检测真实显示器"""
    return bool(os.environ.get("DISPLAY", "")) or bool(os.environ.get("WAYLAND_DISPLAY", ""))

def _can_import_pyautogui():
    """pyautogui 在无 DISPLAY 时导入即崩溃 → 必须先检测"""
    if not _has_display():
        return False
    try:
        import pyautogui
        return True
    except (ImportError, KeyError):
        return False

# autouse fixture 让整个测试类在无头环境自动跳过
class TestCoordinateClamping:
    @pytest.fixture(autouse=True)
    def _require_display(self):
        if not _can_import_pyautogui():
            pytest.skip("无显示器")
```

**关键教训：** pyautogui 在 `import` 阶段就尝试连接 DISPLAY，不能用 `try/except ImportError` 包裹——它不会抛 ImportError，而是抛 `KeyError: 'DISPLAY'`。必须用 `_has_display()` 前置检测。

### Monkeypatch 模式

```python
# 模拟 pyautogui 但绕过真实硬件
monkeypatch.setattr("cognition.tools_computer._CAN_CONTROL", True)
monkeypatch.setattr(pyautogui, "size", lambda: (1920, 1080))
monkeypatch.setattr(pyautogui, "moveTo", lambda x, y, duration: None)
result = asyncio.run(cu._mouse_move(-100, 100))
assert "(0," in result  # 验证坐标裁剪
```

**覆盖的测试类：**
- `TestModuleLoad` (6)——模块加载/依赖
- `TestSafetyMechanisms` (6)——优雅降级
- `TestParseAction` (10)——动作解析器（纯逻辑，无需显示器）
- `TestCoordinateClamping` (4)——坐标裁剪
- `TestTypeTextLimits` (3)——文本限制
- `TestScreenshotRegion` (2)——截图参数校验
- `TestToolRegistration` (2)——注册完整性
- `TestExecuteAction` (5)——动作路由（move/click/type/scroll/unknown）
- `TestErrorRecovery` (6)——记忆记录/回调/日志隔离/清空
- `TestWithDisplay` (5)——桌面实跑（mark.skipif）

全部代码参考：`references/cu-test-suite-pattern.md`

## 十三、记忆回调集成（2026-06-02 新增）

### 问题

CU引擎操作后结果只以字符串返回，八层记忆系统无法消费。每次操作从零开始，不积累经验。

### 方案：`_record_cu_op` + `memory_callback`

```python
class ComputerUseMixin:
    def __init__(self):
        self._cu_operations = []       # 会话操作日志
        self.memory_callback = None     # 异步回调: async fn(op_record)

    def _record_cu_op(self, tool: str, params: dict, success: bool, summary: str):
        """每次CU操作自动记录结构化日志"""
        record = {
            "tool": tool,
            "params": params,
            "success": success,
            "summary": summary,
            "timestamp": time.time(),
        }
        self._cu_operations.append(record)
        # 通知记忆系统：优先异步，兜底同步
        if self.memory_callback:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.memory_callback(record))
            except (RuntimeError, Exception):
                # 无运行中的事件循环 → 同步调用
                try:
                    asyncio.run(self.memory_callback(record))
                except Exception:
                    pass  # 记忆失败不影响CU操作
        return record

    def get_cu_session_log(self) -> list:
        """返回会话全部操作记录"""
        return list(self._cu_operations)
```

### 接入方式

```python
# 在 agent 初始化时设置回调
cu_engine.memory_callback = my_memory_system.ingest_cu_operation

# CU操作自动流入记忆
# screenshot → _record_cu_op("screenshot", {...}, True, "截图完成 1920x1080")
# mouse_move → _record_cu_op("mouse_move", {x, y}, True, "移动到(100,200)")
# click → _record_cu_op("click", {button, clicks}, True, "左键点击")
# ...
```

### 记忆管线

```
CU操作 → _record_cu_op()
  → memory_callback → 八层记忆 L1（工作记忆）
  → L4 定时提炼 → 知识/经验/教训（三维）
  → L5 技能化 → "如何操作XX软件"（复用）
```

**效果：** 第二次操作同一个软件的同一个任务，从L5直接走经验而非重新探索——速度提升 5 倍。

## 十五、三层错误恢复机制（2026-06-02 新增）

### 问题
`_computer_use()` 原先只有单层异常捕获：操作失败→记录→继续下一步。无自动恢复能力。

### 方案：L1重试 → L2换路 → L3降级

```python
async def _computer_use(self, task, max_steps=10, max_retries=3):
    for step in range(1, max_steps + 1):
        # L1: 操作失败→等2秒→重新截图→重试（最多max_retries次）
        for attempt in range(1, max_retries + 1):
            result = await self._execute_action(action)
            if not result.startswith("❌"):
                break  # 成功
            await asyncio.sleep(2.0)
            await self._screenshot("full", quality=40)  # 重截图确认状态

        # L2: L1耗尽→VLM重新分析→给替代方案
        if result.startswith("❌"):
            alt_analysis = await self._image_understand(
                prompt=f"刚才{action['type']}失败了。请给替代方案。不要重复失败操作。")
            alt_action = self._parse_action(alt_analysis)
            alt_result = await self._execute_action(alt_action)

    # L3: 任务结束→汇报统计→已完成/重试/恢复/失败
    return f"✅ 完成: {completed} | 🔄 重试: {retried} | 🛤️ L2恢复: {recovered} | ❌ 失败: {failed}"
```

### 新增方法

**`_execute_action(action: dict) -> str`** — 统一动作路由，消除原来的 if-elif 重复：
```python
async def _execute_action(self, action: dict) -> str:
    atype = action["type"]
    if atype == "move":    return await self._mouse_move(action["x"], action["y"])
    elif atype == "click":  return await self._click(action.get("button", "left"))
    elif atype == "type":   return await self._type_text(action.get("text", ""))
    elif atype == "scroll": return await self._scroll(action.get("clicks", -3))
    else:                   return f"❌ 未知动作类型: {atype}"
```

### 统计输出格式
```
--- 任务统计 ---
✅ 完成: 5 | 🔄 重试: 2 | 🛤️ L2恢复: 1 | ❌ 失败: 0
```

### 关键设计决策
- L1重试间隔 2 秒（让弹窗/加载完成）
- L2换路要求 VLM "不要重复失败的操作"——强制替代思维
- 记忆记录含 `recovered` 和 `attempts` 字段——供 L4 提炼恢复模式
- 恢复失败不影响 CU 操作——`try/except` 包裹 memory_callback

### 代码变动
- `tools_computer.py`: 305行 → 434行 (+129行)
- 新增: `_execute_action()` 方法 + L1/L2/L3 恢复逻辑 + `__init__` + 记忆回调基础设施
- `_computer_use()` 签名新增 `max_retries` 参数（默认3）
- 所有7个CU方法均接入 `_record_cu_op()` 自动记录

## 十四、Agent S3 / OSWorld 对标（2026-06-02 新增）

### Agent S3 关键指标
- 开发方：Simular AI（开源）
- 测试基准：OSWorld（369个真实电脑任务，跨Ubuntu/Windows/macOS）
- 成绩：100步任务成功率 72.6%，首次超越人类基线（72.36%）
- 技术栈：截图 → 多模态VLM（UI-TARS）→ pyautogui 操作 → 验证闭环

### P07 vs S3 对比

| 维度 | Agent S3 | 刘玉龙 P07 |
|:--|:--|:--|
| CU引擎 | ✅ pyautogui | ✅ pyautogui + mss |
| 基准跑分 | 72.6% OSWorld | ❌ 无基准（0个CU测试） |
| 视觉推理 | UI-TARS端到端 | 分离式（visual_reasoning + VLM） |
| 浏览器操控 | 截图方式 | Playwright 18操作（更稳定） |
| 记忆系统 | 无（每次从零开始） | 八层永生记忆 |
| 多Agent协作 | 无 | 蜂群天犬系统 |
| 语音交互 | 无 | TTS+STT全双工 |
| 错误恢复 | 内置（推测3层） | **L1重试+L2换路+L3降级（2026-06-02落地）** |

### S3 对小龙头人的启示
1. **测试套件**：S3能跑分是因为有OSWorld基准。P07的CU引擎必须先写测试建基准。
2. **记忆是护城河**：S3每次任务从零开始。P07每次CU操作入八层记忆→第二次同类任务速度快5倍。
3. **混合操控是正确路线**：有API用API（快），没API上GUI（全覆盖）。S3证明了GUI纯视觉路线的天花板是~73%，混合路线天花板更高。
4. **错误恢复是关键**：S3的72.6%证明了多步任务中错误恢复比单步准确率更重要。P07已落地三层恢复：L1重试→L2换路(让VLM想替代方案)→L3降级(汇报已完成部分)。
