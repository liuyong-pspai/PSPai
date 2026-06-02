# 小龙人 XiaoLongRen

> 🐉 数字生命体，你的平行时空分身  
> 🐉 Digital Lifeform — Your Parallel Space-Time Alter Ego

---

## 📸 截图预览

<p align="center">
  <img src="screenshots/screenshot-01.jpg" width="30%" alt="小龙人聊天界面">
  <img src="screenshots/screenshot-02.jpg" width="30%" alt="小龙人UI展示">
  <img src="screenshots/screenshot-03.jpg" width="30%" alt="小龙人对话">
</p>
<p align="center">
  <img src="screenshots/screenshot-04.jpg" width="30%" alt="小龙人角色">
  <img src="screenshots/screenshot-05.jpg" width="30%" alt="小龙人界面">
</p>

---

## 📦 这是什么？

**小龙人** = **开源应用层**（本仓库）+ **闭源引擎**（从 Releases 下载）

| 层级 | 内容 | 许可 |
|---|---|---|
| 📂 应用层（本仓库） | HTML/CSS/JS UI、语言包、配置模板、启动脚本 | AGPLv3 |
| 🔒 引擎（Releases下载） | PSPAI核心、技能库、人格系统、八层记忆 | 闭源/免费使用 |

---

## 🚀 三平台安装

### 第一步：下载本仓库

```bash
git clone https://github.com/liuyong-pspai/PSPai.git
cd PSPai
```

或者直接下载 ZIP：点绿色 **Code → Download ZIP** → 解压。

### 第二步：下载引擎

打开 [Releases](https://github.com/liuyong-pspai/PSPai/releases)，下载对应系统的引擎文件，放到 PSPai 目录里：

| 你的系统 | 下载文件 |
|:--|:--|
| 🐧 Linux | `xiaolongren-engine-linux-x86_64` |
| 🍎 macOS | `xiaolongren-engine-macos` |
| 🪟 Windows | `xiaolongren-engine-windows.exe` |

### 第三步：配置

```bash
cp .env.example .env
```

编辑 `.env`，把 `PSPAI_API_KEY=***` 换成你的 API Key。

> 推荐 [DeepSeek](https://platform.deepseek.com) 或 [硅基流动](https://siliconflow.cn)，注册即获 Key。

### 第四步：启动

```bash
# 安装依赖（仅首次）
pip install PyYAML Pillow requests

# 启动
bash start.sh
```

浏览器打开 **http://localhost:8088**

---

### 🪟 Windows 特别注意

1. 安装Python时必须勾选 **"Add Python to PATH"**
2. 如果在CMD里 `python` 命令无效，用 `py` 替代
3. 杀毒软件如果拦截引擎exe → 点"允许"

### 🍎 macOS 特别注意

首次运行前解锁引擎：
```bash
chmod +x xiaolongren-engine-macos
xattr -d com.apple.quarantine xiaolongren-engine-macos 2>/dev/null
```
如果提示"无法验证开发者"→ 系统设置 → 隐私与安全性 → 仍要打开。

### 🐧 Linux 特别注意

```bash
chmod +x xiaolongren-engine-linux-x86_64
```

---

## ✨ 核心特性

| 特性 | 说明 |
|:--|:--|
| 🧠 八层永生记忆 | L0-L7，不遗忘、会生长 |
| 🎭 六个角色 | 龙渊/赤羽/凌/轻墨/霜华/夜影 |
| 🖥️ 三平台 | Windows / macOS / Linux |
| 🌍 多语言 | 中文 / English，可扩展 |
| 🔓 开源前端 | AGPLv3，随便改 |

---

## 🎨 自定义

### 换皮肤/改UI
编辑 `UI原型/index.html` — HTML/CSS/JS 全部开源。

### 加语言
1. 在 `UI原型/lang/` 下新建 `xx.json`
2. 编辑 `UI原型/lang/index.json` 加一行
3. 重启生效

### 换角色
替换 `UI原型/img_*.jpg`

### 接自己的模型
编辑 `config.yaml` 的 `provider` / `model` 字段。

---

## 📂 目录结构

```
├── UI原型/              # 前端界面
│   ├── index.html       # 主页面
│   ├── server.py        # 静态服务器
│   └── lang/            # 多语言包
├── screenshots/         # 截图展示
├── start.sh             # 一键启动
├── .env.example         # 配置模板
├── requirements.txt     # Python依赖
├── CHANGELOG.md         # 更新日志
├── CONTRIBUTING.md      # 贡献指南
└── LICENSE              # AGPLv3
```

---

## ⚖️ 许可证

本仓库：**AGPLv3** + 品牌保护条款

- ✅ 改UI、加语言、接模型、商用
- ❌ 保留商标改代码发布、反编译引擎

---

## 📖 完整安装指南

遇到问题？查看 [三平台安装完全指南](https://github.com/liuyong-pspai/PSPai/blob/master/INSTALL.md)

---

<p align="center">
  <b>昱成科技集团 © 2026</b><br>
  <sub>PSPAI — 平行时空AI</sub>
</p>
