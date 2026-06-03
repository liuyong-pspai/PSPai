# 一键安装 + 浏览器配置向导 模式

> 适用于桌面Agent产品的零门槛安装方案。用户只需：下载→双击→桌面图标→浏览器选模型填Key→开始用。
> 2026-06-02 小龙人Windows版实战建立。

## 核心设计

### 痛点
传统安装流程（OpenClaw式）需要用户：
1. 装Python（勾PATH——很多人不会）
2. 下载多个文件
3. 手动解压到同一目录
4. 用记事本编辑 `.env` 填API Key
5. 双击启动脚本

**任何一步卡住 = 用户流失。**

### 方案
将安装简化为：**一个exe → 双击 → 桌面图标 → 浏览器配置向导 → 开始聊天**

## 架构

### 打包内容（setup.exe）
```
setup.exe 内含:
├── python/              # Python 3.12 embeddable (无需用户装Python)
├── frontend/            # 前端HTML/CSS/JS/图片
│   ├── index.html       # 聊天界面（含首次运行检测）
│   ├── config.html      # 配置向导UI
│   └── ...
├── xiaolongren-engine.exe  # PSPAI引擎
├── launcher.py          # 智能启动器（核心）
└── install.bat          # 安装引导（复制文件+创建快捷方式）
```

### 启动器核心逻辑（launcher.py）

```
启动 → 检查 config.json 是否存在
  ├── 不存在 → 启动HTTP服务器(8088) → 打开 config.html
  │            → 等待用户填写配置 → POST /api/config → 保存 config.json
  │            → 生成 .env → 启动引擎 → 打开聊天界面
  └── 存在   → 生成 .env → 启动引擎 → 打开聊天界面
```

### HTTP服务器双重角色
同一个服务器（端口8088）同时提供：
- **静态文件服务**：`/` → index.html, `/config.html` → 配置向导
- **配置API**：
  - `GET /api/config-file` → `{"exists": true/false}`（前端检测是否需要配置）
  - `POST /api/config` → 保存 config.json（配置向导提交）

### 首次运行检测（index.html内嵌）
```javascript
// 页面加载时检测配置状态
fetch('/api/config-file')
  .then(r => r.json())
  .then(d => { if (!d.exists) location.href = '/config.html'; })
  .catch(() => {});
```

## 配置向导UI设计

### 步骤1：选模型
- 6个提供商卡片（DeepSeek/OpenAI/Anthropic/Moonshot/智谱/通义千问）
- 显示标签：免费额度/¥1/百万token/最强模型
- 填API Key（可切换显示/隐藏）
- 选具体模型（下拉）
- 自定义API地址（可选）

### 步骤2：选角色
- 6个数字人卡片（龙渊/赤羽/凌/轻墨/霜华/夜影）
- emoji + 名字 + 描述

### 步骤3：确认
- 显示配置摘要
- 保存按钮 → POST /api/config → 跳转到聊天界面

### 语言支持
右上角中/英切换，所有文字动态翻译。

## CI集成

```yaml
# .github/workflows/release.yml
build-installer:
  needs: build-engine  # 依赖引擎构建完成
  runs-on: windows-2022
  steps:
    - uses: actions/download-artifact@v4  # 下载引擎产物
    - run: python installer/make_installer.py
    - uses: softprops/action-gh-release@v2  # 上传setup.exe
```

## 三平台打包方案（v1.2.0）

| 平台 | 安装包格式 | 打包方式 | 安装目标 | 快捷方式 |
|:--|:--|:--|:--|:--|
| 🪟 Windows | `.zip` (便携) | `shutil.make_archive` | 解压到 `C:\XiaoLongRen\` | 桌面 .lnk (PowerShell COM) |
| 🍎 macOS | `.dmg` | hdiutil create | 拖到 /Applications | .app bundle 即图标 |
| 🐧 Linux | `.run` (自解压) | shell heredoc + tar.gz payload | `~/.xiaolongren/` | .desktop 文件 |

### 统一打包脚本

`installer/make_installer.py` — 自动检测当前平台，调用对应构建函数：

```
main() → 检测 sys.platform
  ├── win32  → build_windows()  → xiaolongren-setup.zip
  ├── darwin → build_macos()    → xiaolongren-installer.dmg
  └── linux  → build_linux()    → xiaolongren-installer.run
```

三平台共用同一套 `prepare_build_dir()`（复制前端+引擎+launcher.py），差异仅在打包外壳。

### Windows: 便携zip + install.bat（不用7z）

```python
# 1. 下载 Python embeddable zip → 解压 → 启用pip
# 2. 生成 install.bat（GBK编码）→ 复制文件+装依赖+创建快捷方式+启动
# 3. 7z a -mx=9 压缩 → 拼上7z.sfx模块 + SFX config → setup.exe
```

### macOS: .app bundle → .dmg

```python
# 创建标准 .app 目录结构
XiaoLongRen.app/
└── Contents/
    ├── Info.plist          # CFBundleExecutable, CFBundleIdentifier 等
    ├── MacOS/
    │   └── xiaolongren     # 可执行shell脚本（#!/bin/bash）
    └── Resources/          # 前端 + 引擎 + launcher.py

# launcher 脚本首次运行时复制资源到 ~/.xiaolongren/
# 然后 exec python3 launcher.py
```

### Linux: 自解压 .run

```bash
# 结构: shell脚本头 + __PAYLOAD__ 标记 + tar.gz 二进制数据
# 用户执行: chmod +x xxx.run && ./xxx.run
# 脚本逻辑:
#   1. 用 sed 提取 __PAYLOAD__ 之后的 tar.gz
#   2. 解压到 ~/.xiaolongren/
#   3. pip install -r requirements.txt
#   4. 创建 ~/.local/share/applications/xiaolongren.desktop
#   5. 启动 python3 launcher.py
```

### 启动器跨平台适配

```python
# find_python() — 三平台查找策略
# 1. Windows: 内置 Python embeddable (APP_DIR/python/python.exe)
# 2. macOS: /usr/bin/python3 → /usr/local/bin/python3 → /opt/homebrew/bin/python3
# 3. 系统PATH: python3 → python

# find_engine() — 三平台引擎候选名
# Windows: xiaolongren-engine-windows.exe / .exe / engine.exe
# macOS/Linux: xiaolongren-engine / xiaolongren-engine-macos / xiaolongren-engine-linux-x86_64
```

## CI 三平台并行构建

```yaml
build-installer:
  needs: build-engine        # 等三平台引擎全编完
  strategy:
    matrix:
      include:
        - platform: windows  # runs-on: windows-2022
        - platform: macos    # runs-on: macos-14
        - platform: linux    # runs-on: ubuntu-22.04
  steps:
    - download-artifact      # 获取对应平台引擎
    - run: python installer/make_installer.py  # 自动检测平台→打包
    - upload to Release      # 上传安装包
```

## 桌面快捷方式

### Windows
```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\🐉 小龙人.lnk')
$Shortcut.TargetPath = 'C:\小龙人\python\pythonw.exe'
$Shortcut.Arguments = 'C:\小龙人\launcher.py'
$Shortcut.WorkingDirectory = 'C:\小龙人'
$Shortcut.Save()
```

### macOS
`.app` bundle 自身即启动图标，拖到 Applications 后从启动台打开。Info.plist 声明为 `APPL` 类型应用。

### Linux
```desktop
[Desktop Entry]
Name=🐉 小龙人
Exec=python3 /home/user/.xiaolongren/launcher.py
Path=/home/user/.xiaolongren/
Icon=/home/user/.xiaolongren/frontend/img_longyuan.jpg
Terminal=false
Type=Application
Categories=Utility;AI;
```

## 陷阱

- **Python embeddable需要修改 `python312._pth`**，取消 `#import site` 注释 + 添加 `Lib/site-packages` 路径，否则pip装不了依赖
- **install.bat编码必须GBK**，否则Windows cmd显示乱码
- **配置文件独立于二进制**，config.json在安装目录，不在打包内部，用户可重新安装不丢配置
- **不要教用户编辑.env**——API Key有格式要求（sk-开头），填错格式引擎启动失败，用户无解。必须用UI收集
- **首次启动需要联网**下载pip依赖（requirements.txt），离线用户需预装依赖后再打包
- **7z SFX vs PyInstaller双方案**：7z SFX更轻量（约30MB vs 50MB+），但需要Windows CI上装7-Zip。PyInstaller作为回退
- **🚨 Windows CI构建步骤必须用PowerShell！** — `os.path.expandvars`、`shutil.which("7z")` 在bash shell (MINGW64)下解析不了Windows路径。v1.2.0→v1.2.3反复失败3次，根因即此。修复：CI中 `if: matrix.platform == 'windows'` → `shell: powershell`，且用 `python` 而非 `python3`

### Windows CI 调试实录（2026-06-02，v1.2.0→v1.2.7，8次迭代）

**症状**：`build-installer` job的"Build installer"步骤在Windows上反复失败（❌），macOS/Linux安装包构建全部成功。

**失败的尝试：**
1. v1.2.0：7z SFX方案 → `os.path.expandvars` 在bash中env var为空 → fallback没生成输出文件
2. v1.2.1：加 `choco install 7zip` → 7z装上了但bash的`shutil.which()`找不到
3. v1.2.2：硬编码多路径查找7z → bash看到的文件系统路径不同
4. v1.2.3：改用 `shell: powershell` → 7z找到了但7z.sfx模块路径仍然解析失败
5. v1.2.4：**彻底放弃7z** → 改为纯zip打包 → 但bat内容出现双重转义（`\\r\\n`变成字面量）
6. v1.2.5：重写make_installer.py用bytes写bat（避免编码问题）→ bash下`python3`不存在
7. v1.2.6：加 `python3 || python` 兼容 → 依然失败（bash环境其他问题）
8. v1.2.7：**改用 `shell: cmd`**（Windows原生cmd.exe）→ ❌ 依然失败（2026-06-03确认：Release中无 `xiaolongren-setup.zip`）

**最终结论（v1.2.7后）：** 8次CI迭代均未解决Windows build-installer问题。所有版本中Windows引擎二进制(`xiaolongren-engine-windows.exe`)编译成功，但安装包构建失败。

### 兜底方案：手动构建Windows安装包（2026-06-03实战验证）

当CI Windows build-installer持续失败时，手动在Linux构建并上传：

```python
# 步骤1：从Release下载Windows引擎exe
curl -o engine/dist/xiaolongren-engine-windows.exe \
  "https://github.com/liuyong-pspai/PSPai/releases/download/vX.Y.Z/xiaolongren-engine-windows.exe"

# 步骤2：构建zip（Python脚本）
import shutil, tempfile, zipfile
from pathlib import Path

BUILD = Path(tempfile.mkdtemp(prefix='xlr_'))
shutil.copytree('UI原型', BUILD / 'frontend', dirs_exist_ok=True)
shutil.copy2('launcher.py', BUILD / 'launcher.py')
shutil.copy2('engine/dist/xiaolongren-engine-windows.exe', BUILD / 'xiaolongren-engine.exe')

# install.bat 内容（GBK+CRLF）
bat = b'@echo off\r\nchcp 65001 >nul\r\n...安装引导...\r\n'
(BUILD / 'install.bat').write_bytes(bat)

shutil.make_archive('dist/xiaolongren-setup', 'zip', str(BUILD))

# 步骤3：通过Python urllib上传（curl在DGX-1上到api.github.com超时）
import urllib.request, json
# 先获取release ID
url = "https://api.github.com/repos/liuyong-pspai/PSPai/releases/tags/vX.Y.Z"
# 再上传
upload_url = f"https://uploads.github.com/repos/.../releases/{release_id}/assets?name=xiaolongren-setup.zip"
```

> 注意：DGX-1上curl到api.github.com超时，但Python urllib.request可达。详见父技能「DGX-1网络约束」。

**最终方案（v1.2.5重写后的make_installer.py）：**
```yaml
# CI中Windows构建步骤
- name: Build installer (Windows)
  if: matrix.platform == 'windows'
  shell: cmd                    # ← 必须用cmd！bash和PowerShell都有路径解析问题
  run: python installer/make_installer.py  # cmd里只有python，没有python3

- name: Build installer (macOS/Linux)
  if: matrix.platform != 'windows'
  run: python3 installer/make_installer.py
```

**根本原因：** GitHub Actions的`defaults.run.shell: bash`对Windows runner也生效，但bash on Windows (MINGW64)的路径系统与原生Windows完全不同。`shell: powershell`也有COM组件路径问题。**`shell: cmd`是最可靠的Windows构建环境。**

**架构决策变更：**
- ❌ 7z SFX自解压exe → 在CI上不可靠，放弃
- ✅ 便携zip + install.bat → 简单可靠，用户解压后双击bat即可安装
- bat内容用`bytes`写入（`b'...'`），避免GBK/UTF-8编码问题
- 安装目标从`C:\小龙人\`改为`C:\XiaoLongRen\`（纯ASCII，避免路径编码问题）

## 用户反馈导向

这个模式的建立源于用户（刘勇）的明确反馈：**"我看你这个下载安装也犯了OpenClaw安装的毛病。太复杂，一般的人根本搞不定。"**

关键要求：
- 一键安装，不是"下载两个文件+装Python+编辑.env"
- 在UI里配模型，不是编辑配置文件
- 桌面生成双击按钮
- 不需要任何技术知识
