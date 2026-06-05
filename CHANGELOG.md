# 🐉 小龙人 更新日志 · XiaoLongRen CHANGELOG

## v1.2.0 — 电脑版发布（2026-06-05）

### 🆕 新增
- **电脑版一键安装包**：解压双击即用，自动打开浏览器配置模型
- **语音输入**：SpeechRecognition API，支持说话转文字自动发送
- **兼容性降级层**：IndexedDB不可用时自动切内存存储，CSP限制下Blob URL回退
- **环境能力检测**：启动时检测7项能力，UI指示灯直观展示
- **插件架构**：selfDiagnose / healthCheck / bridge 三件套

### 🔧 改进
- 语音/记忆不可用时显示用户友好提示，不再技术报警
- SVG矢量图标替代emoji按钮
- 品牌图标更新为龙形标识

### 📦 平台支持
- Windows (.bat 一键启动)
- macOS / Linux (.sh 一键启动)

---

## v1.1.0 — 手机PWA版（2026-06-04）

### 🆕 新增
- 41工具完整插件架构
- 八层永生记忆引擎
- 三界主题切换（龙宫/科技/Loft）
- PWA安装支持（添加到桌面）
- 多语言中英双语

### 🔧 改进
- Android APK构建管线（Capacitor + CI）
- Gitee国内镜像下载

---

## v1.0.0 — 初始发布（2026-06-01）

- 小龙人核心对话引擎
- 多模型支持（DeepSeek/OpenAI/Moonshot/智谱/通义）
- 基础记忆系统
- Web UI三界主题
