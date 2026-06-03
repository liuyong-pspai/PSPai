---
name: mobile-voice-agent
version: 1.0.0
category: devops
description: 手机PWA实时语音Agent开发方法论——浏览器原生语音API+WebSocket全双工+四平台通吃。当爸说「做手机版」「实时语音」「像打电话一样聊天」「不要按键播放」时触发。
tags: [mobile, voice, pwa, webrtc, speech-recognition, tts, websocket, full-duplex]
last_updated: 2026-06-02
---

# 手机版实时语音 Agent

> 把AI装进手机，像打电话一样自然对话。不用按键播放，不用等待——张嘴就说，直接听到回复。

## 核心理念

**不是"语音版聊天机器人"，是"打电话给一个AI人"。**

区别：
| 传统语音助手 | 小龙人语音 |
|:--|:--|
| 按键说话 → 松手等待 → 按播放 | 张嘴就说 → 边说AI边听 → 直接听到回复 |
| 一问一答，不能打断 | 全双工，随时插话 |
| 语音只是输入方式 | 语音是"在场感" |

## 技术架构

```
手机浏览器 (PWA)
  │
  ├─ 🎤 Web Speech API (SpeechRecognition) — 语音→文字
  │    • 浏览器内置，零安装，四平台通吃
  │    • continuous: true → 持续收听，边说边识别
  │    • interimResults: true → 实时显示识别中内容
  │
  ├─ 🔊 Web Speech API (SpeechSynthesis) — 文字→语音
  │    • 浏览器内置，零安装
  │    • 可随时 cancel() → 实现"用户插话立即打断"
  │
  ├─ 📡 WebSocket → 后端引擎
  │    • 发送识别的文字
  │    • 接收LLM回复文字
  │    • 传输角色切换指令
  │
  └─ 📱 PWA Manifest + Service Worker
       • 添加到桌面 = 原生App体验
       • 离线缓存基础UI
```

**后端引擎（DGX#1本地）：**
```
WebSocket Server (Python websockets)
  ├─ 接收文字 → LLM API (DeepSeek) → 回复文字
  ├─ 角色人格注入（6个角色的system prompt）
  ├─ 对话历史管理（短期上下文，切换角色清空）
  └─ 中断处理（新消息到达 → 取消当前LLM请求）
```

## 四平台兼容策略

| 平台 | 浏览器 | SpeechRecognition | SpeechSynthesis | PWA |
|:--|:--|:--:|:--:|:--:|
| 🤖 Android | Chrome/Edge | ✅ | ✅ | ✅ |
| 🍎 iOS | Safari | ✅ | ✅ | ✅ |
| 🇨🇳 鸿蒙 | 浏览器 | ✅ | ✅ | ✅ |
| 🖥️ 桌面 | Chrome/Edge | ✅ | ✅ | ✅ |

**关键设计决策：用浏览器原生语音API，不用Whisper/edge-tts。**
- Whisper太大（1.5GB+），不适合服务器端实时处理
- Edge TTS需要额外进程
- 浏览器Speech API是W3C标准，所有现代浏览器原生支持
- 零依赖，零安装，用户打开网页就能用

## 费用分析

| 环节 | 跑在哪里 | 花费 |
|:--|:--|:--|
| 🎤 语音识别 | 手机浏览器 | 0（浏览器内置） |
| 🔊 文字→语音 | 手机浏览器 | 0（浏览器内置） |
| 🧠 LLM推理 | DeepSeek API | 跟打字一样（¥1-2/百万token） |
| 🗄️ 记忆 | 本地 | 0 |

**结论：语音不增加LLM成本。** 送到大模型的是文字，说话只是输入方式。
一个用户每天聊1小时 ≈ 3元/月，每天10分钟 ≈ 0.5元/月。

## 交互设计原则

1. **一个按钮就够了** — 用户只需一个金色圆钮："按住说话/松手发送"
2. **立即反馈** — 识别到文字 → 角色光环变色 → TTS马上播放
3. **随意打断** — 用户任何时候说话 → 当前TTS立即停止 → 开始听新的
4. **角色可视** — 头像呼吸动画 + 光环脉冲 + 对话气泡浮动
5. **状态透明** — 连接状态（绿/红点）、聆听中（光环）、思考中（文字提示）

## 后端实现要点

```python
# WebSocket 语音引擎核心逻辑
async def handle_voice(websocket):
    current_task = None  # 当前LLM请求
    
    async for raw in websocket:
        msg = json.loads(raw)
        
        if msg['type'] == 'text':
            # 取消之前的回复（用户插话！）
            if current_task and not current_task.done():
                current_task.cancel()
                await websocket.send(json.dumps({"type": "interrupted"}))
            
            # 异步调用LLM
            current_task = asyncio.create_task(
                call_llm_and_reply(websocket, msg['text'])
            )
        
        elif msg['type'] == 'switch_character':
            # 切角色 → 清上下文
            clear_history()
```

### LLM 调用参数（语音专用）

```python
{
    "model": "deepseek-chat",
    "max_tokens": 80,   # 语音回复要短！2-3句话即可
    "temperature": 0.7,  # 适中有温度
    "messages": [
        {"role": "system", "content": "你是龙渊。回复简短口语化，像在打电话，2-3句以内。"},
        ...  # 最近3轮历史
    ]
}
```

## 前端实现要点

### SpeechRecognition 配置

```javascript
const r = new SpeechRecognition();
r.lang = 'zh-CN';           // 中文
r.continuous = true;        // 持续听，不只一句话
r.interimResults = true;    // 实时中间结果
r.maxAlternatives = 1;      // 只要最佳匹配

r.onresult = (e) => {
    // e.results[N].isFinal → true 时发送
    // interim时显示灰色提示文字
};
```

### 打断机制

```javascript
function startListening() {
    speechSynthesis.cancel();  // 立即打断当前TTS！
    recognition.start();        // 开始听
}

// 任何时候用户按下按钮：
// 1. cancel TTS（停止说话）
// 2. start recognition（开始听）
// 这就是全双工的核心
```

## 部署模式

### 局域网模式（在家测试）

前端和后端都在 DGX#1 本地，同一WiFi下手机访问。

```
用户手机 → http://192.168.1.35:8088/mobile.html → WebSocket ws://192.168.1.35:8765
```

### 随时移动模式（出门在外）

**前端部署到 GitHub Pages**（免费，永久在线）：
1. `www/` 目录 push 到 GitHub
2. Settings → Pages → 选 main 分支 → 获得 `https://用户名.github.io/仓库名`

**后端部署到 Render/Railway**（免费配额）：
1. 上传 `backend/voice_server.py`
2. 设置环境变量 `DEEPSEEK_API_KEY`
3. 获得公网 WebSocket 地址

**用户首次打开 → 弹出设置框 → 填入后端地址 → 连接。**
地址持久化在 `localStorage`，下次自动连接。

### PWA 四平台安装

| 平台 | 操作 |
|:--|:--|
| 🤖 Android | Chrome打开 → 菜单 → "添加到主屏幕" |
| 🍎 iOS | Safari打开 → 分享 → "添加到主屏幕" |
| 🇨🇳 鸿蒙 | 浏览器打开 → 菜单 → "添加至桌面" |
| 💻 桌面 | 浏览器直接打开 |

**不需要应用商店，不需要编译，不需要审核。** PWA Manifest + Service Worker = 原生App体验。

### 前端可配置后端（关键设计）

```javascript
// 首次使用：弹出设置框，填入后端地址
// 地址存入 localStorage，下次自动连接
let addr = localStorage.getItem('xlr_addr') || '';
if (!addr) showSettings();  // 未配置 → 弹框
else connectWS();

// 设置面板：一个输入框 + 一个连接按钮
// 用户可以随时点右上角⚙️修改后端地址
```

**这是"随时移动"的核心——前端不变，后端地址随时换。**

## 陷阱

- **不要在DGX-1上编译Whisper** — 太大（1.5GB+），直接用浏览器Speech API
- **不要用edge-tts** — 需要额外安装+进程管理，浏览器SpeechSynthesis 一行代码搞定
- **LLM max_tokens 设80以内** — 语音回复太长用户不耐烦，2-3句刚好
- **iOS Safari SpeechRecognition 需要HTTPS** — 局域网测试用HTTP可以，生产环境必须HTTPS
- **Android Chrome 首次需要用户手势** — 不能在页面加载时自动开始语音，需要按钮点击触发
- **WebSocket 断开要自动重连** — onclose 里 setTimeout 重试
- **局域网版和手机APP版应分开** — 局域网版放开源应用层目录用于快速测试，手机APP版放独立目录作为正式产品
- **PWA manifest图标用角色头像即可** — 不需要单独设计图标，用 img_longyuan.jpg 直接引用
- **Service Worker 缓存基础UI资源** — 离线时至少展示界面，连接恢复后自动重连

## 与 OpenAI Hackathon 的对标

| Hackathon项目 | 我们对应的能力 |
|:--|:--|
| Agentic OS（语音→UI） | 语音→记忆检索→回复 |
| Curo（苏格拉底引导） | 角色人格系统引导对话风格 |
| Wagner（Agent参会） | 锁屏PWA后台常驻 |
| 外科分诊（语音+视觉） | 语音+记忆连续性 |

**核心差异：他们有语音没记忆，我们语音+记忆+多角色，三条护城河。**

## 参考资料

- `references/voice-agent-architecture.md` — 完整技术架构+代码模式+部署清单
