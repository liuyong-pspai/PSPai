# 🐉 小龙人 · 安装指南
# XiaoLongRen · Installation Guide

---

## 一键安装（推荐）

> 下载一个文件，双击即可。不用装Python，不用配置环境变量。

### 🪟 Windows

1. 下载 [`xiaolongren-setup.exe`](https://github.com/liuyong-pspai/PSPai/releases)
2. 双击 → 自动安装到 `C:\小龙人\`
3. 桌面出现 **🐉 小龙人** 图标
4. 双击图标 → 浏览器打开 → 选模型/填Key → 开始聊天

---

### 🍎 macOS

1. 下载 [`xiaolongren-installer.dmg`](https://github.com/liuyong-pspai/PSPai/releases)
2. 双击 `.dmg` → 把 **🐉 小龙人** 拖到 Applications
3. 从启动台打开 → 浏览器打开配置向导
4. 选模型/填Key → 开始聊天

> 首次打开如提示"无法验证开发者"，去 **系统设置 → 隐私与安全性 → 仍要打开**

---

### 🐧 Linux

1. 下载 [`xiaolongren-installer.run`](https://github.com/liuyong-pspai/PSPai/releases)
2. 终端执行：
   ```bash
   chmod +x xiaolongren-installer.run
   ./xiaolongren-installer.run
   ```
3. 自动安装到 `~/.xiaolongren/` → 应用菜单出现图标
4. 点击图标 → 浏览器打开 → 选模型/填Key → 开始聊天

---

## 🔑 API Key 从哪来？

| 提供商 | 注册地址 | 免费额度 |
|:--|:--|:--|
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) | 注册送500万token |
| 智谱GLM | [open.bigmodel.cn](https://open.bigmodel.cn) | 注册送额度 |
| 通义千问 | [dashscope.aliyun.com](https://dashscope.aliyun.com) | 新用户免费 |
| Moonshot | [platform.moonshot.cn](https://platform.moonshot.cn) | 注册送15元 |

---

## 手动安装（高级用户）

```bash
git clone https://github.com/liuyong-pspai/PSPai.git
cd PSPai
# 从 Releases 下载对应平台引擎放到目录里
cp .env.example .env  # 填入 API Key
python3 launcher.py
```
