# 小龙人 XiaoLongRen — 开源应用层

> 🐉 数字生命体，你的平行时空分身  
> 🐉 Digital Lifeform — Your Parallel Space-Time Alter Ego

---

## 📦 这是什么？

这是**小龙人**的开源应用层（UI界面 + 语言包 + 配置模板）。  

小龙人 = **开源应用层**（本仓库）+ **闭源引擎**（从官网下载）

| 层级 | 内容 | 许可 |
|---|---|---|
| 📂 应用层（本仓库） | HTML/CSS/JS UI、语言包、配置模板、启动脚本 | AGPLv3 |
| 🔒 引擎（独立下载） | PSPAI核心、技能库、人格系统 | 闭源/商业许可 |

---

## 🚀 快速开始

### 1. 下载闭源引擎

从 [官网 Releases](https://yuchengsci.com/releases) 下载最新版 `xiaolongren-engine`，放到应用层目录下。

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 PSPAI_API_KEY
```

### 3. 启动

```bash
chmod +x xiaolongren-engine
./start.sh
```

打开浏览器访问 `http://localhost:8088`

---

## 🎨 自定义你的小龙人

### 换皮肤/改UI
编辑 `UI原型/index.html` — HTML/CSS/JS 全部开源，随便改。

### 加语言
1. 在 `UI原型/lang/` 下新建 `xx.json`（复制 `en.json` 改翻译）
2. 编辑 `UI原型/lang/index.json` 加一行新语言
3. 在 `config.yaml` 加 `system_prompt_xx` 人格提示词
4. 重启 — 零代码改动

### 换角色形象
替换 `UI原型/img_*.jpg` 为你自己的角色图片（建议 300×400，WebP/JPEG）

### 接自己的模型
编辑 `config.yaml` 的 `provider` 和 `model` 字段，对接任何兼容 API

---

## 📂 目录结构

```
小龙人开源应用层/
├── UI原型/              # 前端界面
│   ├── index.html       # 主页面
│   ├── prompts.html     # 提示词管理页
│   ├── server.py        # 多线程静态服务器
│   ├── lang/            # 多语言包
│   │   ├── index.json   # 语言索引
│   │   ├── zh.json      # 中文
│   │   └── en.json      # 英文
│   └── img_*.jpg        # 角色图片（6张）
├── start.sh             # 一键启动
├── .env.example         # 环境变量模板
├── requirements.txt     # Python依赖
├── LICENSE              # AGPLv3 + 品牌保护条款
└── README.md            # 本文件
```

---

## ⚖️ 许可证

本仓库代码使用 **GNU AGPLv3** 许可证 + **品牌保护附加条款**。

**你可以：**
- ✅ 修改 UI、换皮肤、加语言、接自己的模型
- ✅ 用自己的品牌名重新发布（前提：去除所有小龙人/PSPAI标识）
- ✅ 商用（需遵守 AGPLv3 传染条款）

**你不可以：**
- ❌ 保留小龙人/PSPAI/昱成科技商标却修改代码后发布
- ❌ 将角色图片作为独立素材再分发
- ❌ 反编译/逆向闭源引擎

完整条款见 [LICENSE](./LICENSE)

---

## 🔗 链接

- 官网：[yuchengsci.com](https://yuchengsci.com)
- 引擎下载：[Releases](https://yuchengsci.com/releases)
- 问题反馈：[GitHub Issues](https://github.com/yuchengsci/xiaolongren/issues)

---

<p align="center">
  <b>昱成科技集团 © 2026</b><br>
  <sub>PSPAI — 平行时空AI架构</sub>
</p>
