# 实时语音Agent · 完整技术架构

> 2026-06-02 实战建立。小龙人手机版全双工语音Agent。

## 架构图

```
┌─────────────────────────────────────────────┐
│              手机浏览器 (PWA)                 │
│                                               │
│  🎤 SpeechRecognition ──→ WebSocket ──→ 后端 │
│  🔊 SpeechSynthesis   ←── WebSocket ←── 后端 │
│                                               │
│  📱 PWA Manifest  → 添加到桌面 = 原生App    │
│  💾 Service Worker → 离线缓存                │
│  ⚙️ 可配置后端 URL → localStorage 持久化     │
└─────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│              后端语音引擎                     │
│                                               │
│  WebSocket Server (Python websockets)        │
│    ├─ 接收文字 → LLM API → 回复文字          │
│    ├─ 6角色系统提示词注入                     │
│    ├─ 对话历史管理（切角色清空）              │
│    └─ 中断处理（新消息→取消当前LLM请求）      │
└─────────────────────────────────────────────┘
```

## 费用模型

| 环节 | 跑在哪里 | 花费 |
|:--|:--|:--|
| 🎤 语音识别 | 手机浏览器 Web Speech API | 0 |
| 🔊 语音合成 | 手机浏览器 SpeechSynthesis | 0 |
| 🧠 LLM推理 | DeepSeek API (云端) | ¥1-2/百万token |
| 💾 记忆存储 | 后端本地磁盘 | 0 |

**每天聊1小时 ≈ 3元/月。语音不增加LLM成本。**

## 四平台兼容矩阵

| 平台 | 浏览器 | SpeechRecognition | SpeechSynthesis | PWA 安装 |
|:--|:--|:--:|:--:|:--:|
| 🤖 Android | Chrome / Edge | ✅ | ✅ | ✅ |
| 🍎 iOS | Safari | ✅ | ✅ | ✅ |
| 🇨🇳 鸿蒙 | 浏览器 / Chrome | ✅ | ✅ | ✅ |
| 💻 桌面 | Chrome / Edge | ✅ | ✅ | ✅ |

## 关键代码模式

### 后端 WebSocket 中断处理

```python
async def handle(websocket):
    task = None
    async for raw in websocket:
        msg = json.loads(raw)
        if msg['type'] == 'text':
            if task and not task.done():
                task.cancel()  # ← 用户插话！立即取消当前回复
                await websocket.send(json.dumps({"type": "interrupted"}))
            task = asyncio.create_task(reply(websocket, msg['text']))
```

### 前端打断机制

```javascript
function startListening() {
    speechSynthesis.cancel();  // ← 停止当前TTS！
    recognition.start();        // ← 开始听新的话
}
```

### LLM 语音专用参数

```python
{
    "model": "deepseek-chat",
    "max_tokens": 80,    # 语音回复必须短
    "temperature": 0.7,
    "messages": [
        {"role": "system", "content": "你是龙渊。回复简短口语化，像在打电话，2-3句以内。"},
    ]
}
```

## 部署文件清单

```
小龙人手机APP/
├── www/                    # PWA前端
│   ├── index.html          # 主界面（单文件，零构建）
│   ├── manifest.json       # PWA配置
│   ├── sw.js               # Service Worker
│   └── img_*.jpg           # 6角色头像（即图标）
├── backend/
│   └── voice_server.py     # WebSocket语音引擎
├── start.sh                # 开发模式启动
└── README.md               # 部署说明
```
