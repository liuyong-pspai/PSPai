# 静态前端 + Python API 后端轻量集成架构

> 来源：2026-06-01 小龙人UI ↔ PSPAI后端联调实战

## 架构图

```
浏览器 → :8088 (http.server, 静态HTML/CSS/JS)
       → :8089 (Python HTTP API, 对话/改名/头像)
            │
            ├── /api/chat    → DeepSeek API (urllib)
            ├── /api/name    → data/names.json
            ├── /api/avatar  → data/avatars/*.jpg
            └── /api/status  → 健康检查
```

## 核心模式

### 1. 纯标准库，零依赖
```python
import http.server, json, urllib.request, base64, re
```
不需要 Flask/FastAPI，`http.server.BaseHTTPRequestHandler` 足够处理 JSON API。

### 2. CORS 手动设置
```python
self.send_header("Access-Control-Allow-Origin", "*")
self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
```
必须有 `do_OPTIONS` 方法处理预检请求。

### 3. 数据持久化：JSON + 文件系统
```
data/
├── names.json       # 角色名映射
├── avatars/
│   ├── custom_0.jpg
│   ├── custom_1.png
│   └── custom_2.jpg
└── ...
```

### 4. LLM 集成：成功返回 → 失败回退规则引擎
```python
def chat_with_llm(char_index, char_name, user_msg):
    # 1. 从 config.yaml 加载 system prompt
    # 2. 维护对话历史 (内存 dict)
    # 3. 调用 DeepSeek API (urllib)
    # 4. 失败时返回 None → 调用方回退规则引擎
```

### 5. 前后端数据双写
```javascript
// 前端 localStorage（离线可用）
localStorage.setItem('xiaolongren_char_names', JSON.stringify(charNames));
// 后端持久化（跨设备同步）
fetch(API_BASE + '/api/name', {method:'POST', ...}).catch(function(){});
```

### 6. 改名协议：[NAME:xxx] 标签
LLM 回复中嵌入 `[NAME:新名字]` 标签，后端解析后自动改名并通知前端刷新UI。

## 常见坑

| 坑 | 症状 | 修复 |
|:---|:---|:---|
| .env 未加载 | API正常但回复是规则引擎模板 | `export $(grep -v '^#' .env \| xargs)` |
| CORS未设 | 浏览器跨域错误 | 每个响应加 `Access-Control-Allow-Origin: *` |
| 端口冲突 | Address already in use | `ss -tlnp \| grep 8089` 检查 |
