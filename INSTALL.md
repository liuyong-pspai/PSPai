# 🐉 小龙人 · 三平台安装完全指南
# XiaoLongRen · Complete Installation Guide (All Platforms)

---

## 第一步 · Step 1：下载 · Download

### Git 克隆 · Clone（推荐 · Recommended）

```bash
git clone https://github.com/liuyong-pspai/PSPai.git
cd PSPai
```

### 下载 ZIP · Download ZIP

打开 https://github.com/liuyong-pspai/PSPai  
点绿色 **Code** → **Download ZIP** → 解压到桌面 · Unzip to desktop

---

## 第二步 · Step 2：下载引擎 · Download Engine

打开 [Releases](https://github.com/liuyong-pspai/PSPai/releases)  
下载对应系统的引擎文件 · Download the engine for your OS:

| 系统 · OS | 下载文件 · File |
|:--|:--|
| 🐧 Linux | `xiaolongren-engine-linux-x86_64` |
| 🍎 macOS | `xiaolongren-engine-macos` |
| 🪟 Windows | `xiaolongren-engine-windows.exe` |

**把下载的引擎文件放到 PSPai 目录里**（和 start.sh 放一起）。  
**Place the downloaded engine in the PSPai folder** (same folder as start.sh).

---

## 第三步 · Step 3：分系统操作 · OS-Specific Setup

---

### 🪟 Windows

#### 1. 下载 · Download

1. 打开 https://github.com/liuyong-pspai/PSPai/releases
2. 下载 **两个文件**：
   - `xiaolongren-open-source.tar.gz`（开源层，213KB）
   - `xiaolongren-engine-windows.exe`（引擎，8.91MB）
3. 把两个文件解压/放到同一个文件夹，比如 `C:\Users\你的用户名\Desktop\小龙人\`
4. 解压 `xiaolongren-open-source.tar.gz`（用7-Zip或WinRAR，Win11自带解压）
5. 确保 `start.bat` 和 `xiaolongren-engine-windows.exe` 在同一目录

#### 2. 安装 Python · Install Python

1. 打开 https://www.python.org/downloads/
2. 点黄色 **Download Python 3.12.x**
3. 运行安装程序
4. ⚠️ **底部必须勾选 "Add Python to PATH"**（不勾后面全报错）
5. 点 Install Now → 等待完成

验证：按 `Win+R` → 输入 `cmd` → 回车 → 输入：
```
python --version
```
应显示 `Python 3.12.x`

#### 3. 配置 API Key · Configure

1. 复制 `.env.example` → 重命名为 `.env`
2. 用记事本打开 `.env`
3. 把 `PSPAI_API_KEY=***` 改成你的 Key（去 https://platform.deepseek.com 注册免费拿）
4. 保存

#### 4. 启动 · Launch

**双击 `start.bat`**

浏览器会自动打开 http://localhost:8088

> 如果杀毒软件弹窗拦截引擎exe，点「更多信息」→「仍要运行」

#### 5. Windows 常见问题 · FAQ

| 问题 | 解决 |
|:--|:--|
| `python 不是内部或外部命令` | 重装Python，**必须勾选 "Add Python to PATH"** |
| `pip 不是内部或外部命令` | `python -m pip install PyYAML Pillow requests` |
| 杀毒软件报警 | 引擎是PyInstaller打包的exe，点「更多信息」→「仍要运行」 |
| 双击bat闪退 | 右键bat文件→编辑，看报错信息；或者在cmd里cd到目录再运行 `start.bat` |
| `未找到引擎文件` | 检查 `xiaolongren-engine-windows.exe` 是否和 `start.bat` 在同一文件夹 |
| 端口8088被占用 | 关掉占用程序，或改 `UI原型/server.py` 里的 `PORT` |
| 浏览器打开空白 | 等5秒刷新，引擎启动需要时间 |

---

### 🍎 macOS

#### 安装 Python · Install Python

打开 **终端 · Terminal**（启动台 → 其他 → 终端 · Launchpad → Other → Terminal）

验证 · Verify:
```bash
python3 --version
```
若显示 `Python 3.x.x` → 已有。  
If shows version → already installed.

若没装 · If not: https://www.python.org/downloads/ 下载 macOS 安装包。

#### 授权引擎 · Authorize Engine

macOS 拦截陌生程序，先手动授权 · macOS blocks unknown apps:

```bash
cd ~/Desktop/PSPai    # 或你的解压目录 · or your unzip location
chmod +x xiaolongren-engine-macos
xattr -d com.apple.quarantine xiaolongren-engine-macos 2>/dev/null
```

#### 配置 · Configure

```bash
cp .env.example .env
nano .env
```

把 `PSPAI_API_KEY=***` 改成你的 Key，`Ctrl+O` 保存，`Ctrl+X` 退出。

#### 启动 · Launch

```bash
bash start.sh
```

浏览器自动打开 · Auto-opens: **http://localhost:8088**

#### macOS 常见问题 · FAQ

| 问题 · Problem | 解决 · Solution |
|:--|:--|
| "无法打开，来自未认证开发者" "Unverified Developer" | 系统设置 → 隐私与安全性 → 仍要打开 · System Settings → Privacy → Open Anyway |
| `xattr: command not found` | 忽略，直接 `bash start.sh` · Skip, run directly |
| `pip: command not found` | `python3 -m pip install PyYAML Pillow requests` |

---

### 🐧 Linux

#### 安装 Python · Install Python

通常已自带 · Usually pre-installed:
```bash
python3 --version
```

若没装 · If not installed:
```bash
# Ubuntu / Debian
sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

#### 授权引擎 · Authorize Engine

```bash
cd ~/PSPai
chmod +x xiaolongren-engine-linux-x86_64
```

#### 配置 · Configure

```bash
cp .env.example .env
nano .env    # 或用 vim / gedit
```

#### 启动 · Launch

```bash
bash start.sh
```

浏览器打开 · Open: **http://localhost:8088**

#### Linux 常见问题 · FAQ

| 问题 · Problem | 解决 · Solution |
|:--|:--|
| `Permission denied` | `chmod +x xiaolongren-engine-linux-x86_64` |
| `pip: externally managed` | `pip install --user PyYAML Pillow requests` |
| 端口占用 Port in use | `lsof -ti:8088 | xargs kill` 然后重试 · then retry |

---

## 第四步 · Step 4：验证 · Verify

浏览器打开 · Open http://localhost:8088

1. 看到龙渊头像 ✅ · See Dragon Abyss avatar
2. 打字发送 ✅ · Type & send a message
3. AI 回复了 ✅ · AI replies

**🐉 小龙人已经在你的电脑上跑起来了！**  
**🐉 XiaoLongRen is running on your machine!**

---

## 🔑 获取 API Key · Get API Key

小龙人需要大模型 API Key 才能聊天。  
XiaoLongRen needs an LLM API key to chat.

推荐渠道 · Recommended:

| 平台 | 链接 | 说明 |
|:--|:--|:--|
| DeepSeek | https://platform.deepseek.com | 国产，性价比高 · Cheap & fast |
| 硅基流动 SiliconFlow | https://siliconflow.cn | 国内直连 · China direct |
| OpenAI | https://platform.openai.com | 国际 · International |

注册后在控制台获取 Key，填入 `.env` 的 `PSPAI_API_KEY=` 后面。  
After signup, get your key from the dashboard, fill in `.env` → `PSPAI_API_KEY=your_key`.

---

## 🛑 停止 · Stop

在终端按 `Ctrl+C` · Press `Ctrl+C` in terminal.

---

## 🔄 更新 · Update

```bash
cd PSPai
git pull
# 若 Releases 有新引擎，重新下载替换 · Re-download engine if updated
bash start.sh
```
