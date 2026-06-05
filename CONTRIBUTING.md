# 🤝 参与贡献 · Contributing to XiaoLongRen

欢迎参与小龙人项目！无论你是开发者、设计师还是普通用户，都可以贡献力量。

Welcome! Contributions from developers, designers, and users are all welcome.

---

## 🐛 报告Bug · Bug Reports

1. 打开 Issues → New Issue → Bug Report
2. 描述问题：什么操作？什么现象？什么环境？
3. 附上截图（如有）

Describe: what you did, what happened, what should have happened, your environment.

---

## 💡 功能建议 · Feature Requests

在 Issues 中提交，标签用 `enhancement`。
告诉我们需要什么功能、为什么需要它。

Tag with `enhancement`. Tell us what you need and why.

---

## 🔌 开发插件 · Writing Plugins

小龙人支持插件扩展。插件放在 `plugins/` 目录：

```javascript
// plugins/my-tool.js
XLR.registerPlugin({
  name: 'my-tool',
  label: { zh: '我的工具', en: 'My Tool' },
  tools: [
    {
      name: 'hello',
      description: { zh: '打招呼', en: 'Say hello' },
      params: { name: 'string' },
      handler(params) { return `你好 ${params.name}！`; }
    }
  ]
});
```

---

## 📐 代码规范 · Code Style

- JavaScript ES6+
- 缩进2空格
- 函数注释用JSDoc
- 提交信息用中文

---

## 📄 协议 · License

体验层：MIT License
内核引擎：PSPAI Core License

---

## 🏗️ 项目结构 · Project Structure

```
pwa/
├── index.html          — 电脑版UI
├── mobile.html         — 手机版UI
├── xiaolongren-core.js — 核心引擎
├── plugin-loader.js    — 插件加载器
├── plugins/            — 插件目录
├── lang/               — 语言包
├── launcher.py         — 桌面启动器
├── install.bat/sh      — 安装脚本
└── assets/             — 资源文件
```
