# 🐉 小龙人 · 三平台安装完全指南

---

## 第一步：下载（三平台通用）

### 方式一：Git 克隆（推荐）

```bash
git clone https://github.com/liuyong-pspai/PSPai.git
cd PSPai
```

### 方式二：直接下载 ZIP

打开 https://github.com/liuyong-pspai/PSPai  
点绿色 **Code** → **Download ZIP** → 解压到桌面

---

## 第二步：下载引擎

打开 https://github.com/liuyong-pspai/PSPai/releases  
下载对应你电脑系统的引擎文件：

| 你的系统 | 下载这个文件 |
|:--|:--|
| 🐧 Linux | `xiaolongren-engine-linux-x86_64` |
| 🍎 macOS | `xiaolongren-engine-macos` |
| 🪟 Windows | `xiaolongren-engine-windows.exe` |

**把下载的引擎文件放到 PSPai 目录里**（和 start.sh 放一起）。

---

## 第三步：分系统操作

---

### 🪟 Windows 用户

#### 3.1 安装 Python（如果还没装）

1. 打开 https://www.python.org/downloads/
2. 点黄色 **Download Python 3.12.x**
3. 运行安装程序
4. ⚠️ **一定要勾选** "Add Python to PATH"（页面底部的勾选框！）
5. 点 Install → 等待完成

验证：按 `Win+R`，输入 `cmd`，回车，输入：
```
python --version
```
应该显示 `Python 3.12.x`

#### 3.2 配置 API Key

在 PSPai 目录里：
1. 复制 `.env.example` → 重命名为 `.env`
2. 用记事本打开 `.env`
3. 把 `PSPAI_API_KEY=***` 改成你的真实 API Key
4. 保存

#### 3.3 安装依赖

按 `Win+R`，输入 `cmd`，回车。

```cmd
cd 桌面\PSPai
pip install PyYAML Pillow requests
```

#### 3.4 启动

```cmd
cd 桌面\PSPai
start.sh
```

浏览器会自动打开 http://localhost:8088

如果没自动打开，手动打开浏览器输入这个地址。

#### 3.5 Windows 常见问题

| 问题 | 解决 |
|:--|:--|
| `python 不是内部命令` | 重装Python，必须勾选"Add Python to PATH" |
| `pip 不是内部命令` | `python -m pip install PyYAML Pillow requests` |
| 杀毒软件报警 | 引擎是PyInstaller打包的exe，点"允许" |
| 端口被占用 | 关掉其他程序，或改 `UI原型/server.py` 里的 `PORT` |

---

### 🍎 macOS 用户

#### 3.1 安装 Python（通常已自带）

打开 **终端**（在"启动台→其他→终端"）。

验证：
```bash
python3 --version
```
如果显示 `Python 3.x.x` → 已有，跳到下一步。  
如果没装 → https://www.python.org/downloads/ 下载 macOS 安装包。

#### 3.2 授权引擎

macOS 会对陌生程序设限，先手动授权：

```bash
cd ~/桌面/PSPai   # 或者你解压到的目录
chmod +x xiaolongren-engine-macos
xattr -d com.apple.quarantine xiaolongren-engine-macos 2>/dev/null
```

#### 3.3 配置 API Key

```bash
cp .env.example .env
nano .env
```

把 `PSPAI_API_KEY=***` 改成你的真实 Key。  
`Ctrl+O` 保存，`Ctrl+X` 退出。

#### 3.4 启动

```bash
bash start.sh
```

浏览器会自动打开 http://localhost:8088

#### 3.5 macOS 常见问题

| 问题 | 解决 |
|:--|:--|
| "无法打开，来自未认证开发者" | 系统设置→隐私与安全性→仍要打开 |
| `xattr: command not found` | 忽略，直接 `bash start.sh` |
| `pip: command not found` | `python3 -m pip install PyYAML Pillow requests` |

---

### 🐧 Linux 用户

#### 3.1 安装 Python（通常已自带）

```bash
python3 --version
```

如果没装：
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

#### 3.2 授权引擎

```bash
cd ~/PSPai
chmod +x xiaolongren-engine-linux-x86_64
```

#### 3.3 配置 API Key

```bash
cp .env.example .env
nano .env    # 或用 vim / gedit
```

把 `PSPAI_API_KEY=***` 改成你的真实 Key，保存。

#### 3.4 启动

```bash
bash start.sh
```

浏览器会自动打开 http://localhost:8088

#### 3.5 Linux 常见问题

| 问题 | 解决 |
|:--|:--|
| `Permission denied` | `chmod +x xiaolongren-engine-linux-x86_64` |
| `pip: externally managed` | `pip install --user PyYAML Pillow requests` |
| 端口被占用 | `lsof -ti:8088 | xargs kill` 然后重试 |
| Wayland 下无 GUI | 引擎是命令行服务，用浏览器访问即可 |

---

## 第四步：验证成功

浏览器打开 http://localhost:8088 后：

1. 看到龙渊头像 → ✅
2. 底部输入框打字发送 → ✅
3. AI 回复了 → ✅

**恭喜！小龙人已经在你的电脑上跑起来了 🐉**

---

## 获取 API Key

小龙人需要大模型 API Key 才能聊天。

推荐渠道：
- **DeepSeek**：https://platform.deepseek.com （国产，性价比高）
- **硅基流动**：https://siliconflow.cn （国内直连）
- **OpenAI**：https://platform.openai.com

注册后获取 API Key，填入 `.env` 文件的 `PSPAI_API_KEY=` 后面。

---

## 停止运行

在终端按 `Ctrl+C` 即可停止。

---

## 更新到最新版

```bash
cd PSPai
git pull
# 如果 Releases 有新引擎，重新下载替换
bash start.sh
```
