# 小龙人 XiaoLongRen

> 🐉 数字生命体，你的平行时空分身  
> 🐉 Digital Lifeform — Your Parallel Space-Time Alter Ego

---

## 📸 截图预览 · Screenshots

<p align="center">
  <img src="screenshots/screenshot-01.jpg" width="30%" alt="chat">
  <img src="screenshots/screenshot-02.jpg" width="30%" alt="UI">
  <img src="screenshots/screenshot-03.jpg" width="30%" alt="dialog">
</p>
<p align="center">
  <img src="screenshots/screenshot-04.jpg" width="30%" alt="characters">
  <img src="screenshots/screenshot-05.jpg" width="30%" alt="interface">
</p>

---

## 📦 这是什么？ · What is this?

**小龙人** = **开源应用层**（本仓库）+ **闭源引擎**（从 Releases 下载）

**XiaoLongRen** = **Open-source UI layer** (this repo) + **Proprietary engine** (download from Releases)

| 层级 Layer | 内容 Content | 许可 License |
|---|---|---|
| 📂 应用层 UI Layer | HTML/CSS/JS、语言包 i18n、配置模板 config、启动脚本 launcher | AGPLv3 |
| 🔒 引擎 Engine | PSPAI核心 Core、技能库 Skills、人格系统 Persona、八层记忆 8-Layer Memory | 闭源/免费 Proprietary / Free |

---

## 🚀 安装 · Quick Start

### ① 下载本仓库 · Clone this repo

```bash
git clone https://github.com/liuyong-pspai/PSPai.git
cd PSPai
```

也可以直接下载 ZIP · Or download ZIP: 点绿色按钮 **Code → Download ZIP** → 解压 unzip。

### ② 下载引擎 · Download engine

打开 [Releases](https://github.com/liuyong-pspai/PSPai/releases)，下载对应系统的引擎，放到 PSPai 目录里。  
Download the engine file for your OS and place it in the PSPai folder.

| 系统 OS | 文件 File |
|:--|:--|
| 🐧 Linux | `xiaolongren-engine-linux-x86_64` |
| 🍎 macOS | `xiaolongren-engine-macos` |
| 🪟 Windows | `xiaolongren-engine-windows.exe` |

### ③ 配置 · Configure

```bash
cp .env.example .env
```

编辑 `.env`，填入 API Key · Edit `.env` and fill in your API key:

```
PSPAI_API_KEY=你的Key
```

> 免费获取 Key · Get a free key: [DeepSeek](https://platform.deepseek.com) or [SiliconFlow](https://siliconflow.cn)

### ④ 启动 · Launch

```bash
pip install PyYAML Pillow requests   # 仅首次 · first time only
bash start.sh
```

浏览器打开 · Open browser: **http://localhost:8088**

---

### 🪟 Windows 注意 · Notes

安装 Python 时必须勾选 **"Add Python to PATH"**。  
Must check **"Add Python to PATH"** when installing Python.

若杀毒软件拦截引擎exe → 点"允许"。  
If antivirus blocks the engine exe → click "Allow".

### 🍎 macOS 注意 · Notes

首次运行前解锁引擎 · Unlock engine before first run:
```bash
chmod +x xiaolongren-engine-macos
xattr -d com.apple.quarantine xiaolongren-engine-macos 2>/dev/null
```
若提示"无法验证开发者"→ 系统设置 → 隐私与安全性 → 仍要打开。  
If "unverified developer" → System Settings → Privacy & Security → Open Anyway.

### 🐧 Linux 注意 · Notes

```bash
chmod +x xiaolongren-engine-linux-x86_64
```

---

## ✨ 核心特性 · Features

| 特性 Feature | 说明 Description |
|:--|:--|
| 🧠 八层永生记忆 · 8-Layer Memory | L0-L7，不遗忘、会生长 · Never forgets, self-evolving |
| 🎭 六个角色 · 6 Characters | 龙渊/赤羽/凌/轻墨/霜华/夜影 |
| 🖥️ 三平台 · Cross-Platform | Windows / macOS / Linux |
| 🌍 多语言 · i18n | 中文 / English，可扩展 extensible |
| 🔓 开源前端 · Open-source UI | AGPLv3，随便改 fully customizable |

---

## 🎨 自定义 · Customization

### 换皮肤 / Change theme
编辑 `UI原型/index.html` — HTML/CSS/JS 全部开源。  
Edit `UI原型/index.html` — fully open-source.

### 加语言 / Add language
1. 在 `UI原型/lang/` 下新建 `xx.json` · Create new `xx.json` under `UI原型/lang/`
2. 编辑 `UI原型/lang/index.json` 加一行 · Add one line to `index.json`
3. 重启 · Restart

### 换角色 / Change character
替换 `UI原型/img_*.jpg` · Replace the image files.

### 接自己的模型 / Use your own LLM
编辑 `config.yaml` 的 `provider` / `model` 字段。  
Edit `provider` / `model` in `config.yaml`.

---

## 📂 目录结构 · Structure

```
├── UI原型/              # 前端 UI
│   ├── index.html       # 主页面 Main page
│   ├── server.py        # 静态服务器 Static server
│   └── lang/            # 多语言包 i18n
├── screenshots/         # 截图 Screenshots
├── start.sh             # 一键启动 Launcher
├── .env.example         # 配置模板 Config template
├── requirements.txt     # 依赖 Python deps
├── INSTALL.md           # 详细安装指南 Full install guide
├── CHANGELOG.md         # 更新日志 Changelog
├── CONTRIBUTING.md      # 贡献指南 Contributing
└── LICENSE              # AGPLv3
```

---

## 📖 完整安装指南 · Full Install Guide

遇到问题？查看完整指南（含常见问题解答）· See full guide (with FAQ):

> [INSTALL.md](https://github.com/liuyong-pspai/PSPai/blob/master/INSTALL.md)

---

## ⚖️ 许可证 · License

本仓库 · This repo: **AGPLv3** + 品牌保护条款 Brand Protection

- ✅ 改UI、加语言、接模型、商用 · Modify, i18n, custom LLM, commercial use
- ❌ 保留商标改代码发布、反编译引擎 · Rebrand & redistribute, reverse-engineer engine

---

<p align="center">
  <b>昱成科技集团 © 2026</b><br>
  <sub>PSPAI — 平行时空AI · Parallel Space-Time AI</sub>
</p>
