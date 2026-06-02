#!/usr/bin/env python3
"""
小龙人 三平台一键安装包制作工具
   在CI上运行，自动检测当前系统，生成对应安装包

   Windows → xiaolongren-setup.exe (7z SFX)
   macOS   → xiaolongren-installer.dmg (.app bundle)
   Linux   → xiaolongren-installer.run (makeself 自解压)

   用户安装流程（三平台统一）:
   1. 双击安装包
   2. 自动装到系统目录 → 桌面/启动台出现图标
   3. 双击图标 → 浏览器打开配置向导
   4. 选模型填Key → 开始聊天
"""
import os
import sys
import shutil
import json
import zipfile
import subprocess
import tempfile
import urllib.request
from pathlib import Path

# ============================================================
# 配置
# ============================================================
APP_NAME = "XiaoLongRen"
APP_DISPLAY = "🐉 小龙人"
PYTHON_VERSION = "3.12.9"

REPO_ROOT = Path(__file__).parent.parent.resolve()
ENGINE_DIR = REPO_ROOT / "engine"
FRONTEND_DIR = REPO_ROOT / "UI原型"
OUTPUT_DIR = REPO_ROOT / "dist"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BUILD_DIR = Path(tempfile.mkdtemp(prefix="xlr_build_"))


# ============================================================
# 通用工具
# ============================================================
def step(msg):
    print(f"  [{msg}]", end=" ", flush=True)

def ok():
    print("✅")

def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)

def download(url, dest):
    print(f"    下载: {url.split('/')[-1]}")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"    下载失败: {e}")
        return False


# ============================================================
# 各平台共用：准备构建内容
# ============================================================
def prepare_build_dir():
    """准备构建目录——所有平台共用"""
    step("准备构建内容")

    # 前端
    front_dest = BUILD_DIR / "frontend"
    if FRONTEND_DIR.exists():
        shutil.copytree(FRONTEND_DIR, front_dest, dirs_exist_ok=True)
    else:
        fail(f"前端目录不存在: {FRONTEND_DIR}")

    # 启动器
    launcher_src = REPO_ROOT / "launcher.py"
    if launcher_src.exists():
        shutil.copy2(launcher_src, BUILD_DIR / "launcher.py")
    else:
        fail(f"启动器不存在: {launcher_src}")

    # 引擎
    engine = find_engine()
    if engine:
        shutil.copy2(engine, BUILD_DIR / "xiaolongren-engine")
        os.chmod(BUILD_DIR / "xiaolongren-engine", 0o755)
    else:
        print("    (未找到引擎，CI将补入)")

    # requirements
    req = REPO_ROOT / "requirements.txt"
    if req.exists():
        shutil.copy2(req, BUILD_DIR / "requirements.txt")

    file_count = sum(1 for _ in BUILD_DIR.rglob("*") if _.is_file())
    print(f"    ({file_count} 文件)")
    ok()


def find_engine():
    """查找当前平台引擎"""
    candidates = {
        "win32": ["engine/dist/xiaolongren-engine-windows.exe",
                   "xiaolongren-engine-windows.exe"],
        "darwin": ["engine/dist/xiaolongren-engine-macos",
                    "xiaolongren-engine-macos"],
        "linux": ["engine/dist/xiaolongren-engine-linux-x86_64",
                   "xiaolongren-engine-linux-x86_64"],
    }
    platform = sys.platform
    for name in candidates.get(platform, []):
        path = REPO_ROOT / name
        if path.exists():
            return path
    return None


# ============================================================
# Windows: 7z SFX → setup.exe
# ============================================================
def bundle_python_windows():
    """Windows: 下载嵌入式Python"""
    step("打包Python (Windows embeddable)")
    url = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
    py_zip = BUILD_DIR / "python-embed.zip"
    if not download(url, py_zip):
        fail("下载失败")
    with zipfile.ZipFile(py_zip) as zf:
        zf.extractall(BUILD_DIR / "python")
    py_zip.unlink()

    # 启用 pip
    pth = BUILD_DIR / "python" / "python312._pth"
    if pth.exists():
        content = pth.read_text()
        content = content.replace("#import site", "import site")
        if "Lib/site-packages" not in content:
            content += "\nLib/site-packages\n"
        pth.write_text(content)
    ok()


def build_windows():
    """Windows: 生成 setup.exe"""
    print("\n--- 🪟 Windows 安装包 ---")
    prepare_build_dir()
    bundle_python_windows()

    # 创建安装引导
    install_bat = BUILD_DIR / "install.bat"
    install_bat.write_text(r'''@echo off & chcp 65001 >nul
title 🐉 小龙人 安装中...
echo   🐉 小龙人 正在安装...
set "D=C:\小龙人"
xcopy /E /I /Y /Q "%~dp0*" "%D%" >nul
cd /d "%D%"
if exist "python\python.exe" (
    python\python.exe -m ensurepip >nul 2>&1
    python\python.exe -m pip install -q -r requirements.txt >nul 2>&1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell=New-Object -ComObject WScript.Shell;$Shortcut=$WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\🐉 小龙人.lnk');$Shortcut.TargetPath='%D%\python\pythonw.exe';$Shortcut.Arguments='%D%\launcher.py';$Shortcut.WorkingDirectory='%D%';$Shortcut.Save()"
start "" "%D%\python\pythonw.exe" "%D%\launcher.py"
echo   安装完成！浏览器将自动打开配置向导。
timeout /t 3 >nul & exit
''', encoding="gbk")

    # 创建SFX
    # 多种方式查找7z（choco安装后路径 / 手动安装 / PATH）
    seven_zip = None
    for path in [
        os.path.expandvars(r"%ProgramFiles%\7-Zip\7z.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\7-Zip\7z.exe"),
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]:
        if os.path.exists(path):
            seven_zip = path
            break
    if not seven_zip:
        seven_zip = shutil.which("7z") or shutil.which("7za")
    
    output = OUTPUT_DIR / "xiaolongren-setup.exe"

    if seven_zip:
        step("7z SFX 打包")
        print(f"(7z={seven_zip})")
        archive = OUTPUT_DIR / "xlr_tmp.7z"
        subprocess.run([seven_zip, "a", "-mx=9", str(archive),
                        str(BUILD_DIR / "*")], cwd=str(BUILD_DIR),
                       check=True, capture_output=True)

        # 查找7z.sfx模块
        sfx_module = None
        for path in [
            os.path.expandvars(r"%ProgramFiles%\7-Zip\7z.sfx"),
            r"C:\Program Files\7-Zip\7z.sfx",
            r"C:\Program Files (x86)\7-Zip\7z.sfx",
        ]:
            if os.path.exists(path):
                sfx_module = Path(path)
                break
        
        if not sfx_module:
            fail("未找到7z.sfx，请安装7-Zip")

        with open(output, "wb") as out:
            out.write(sfx_module.read_bytes())

            config = (f';!@Install@!UTF-8!\n'
                      f'Title="{APP_DISPLAY} 安装"\n'
                      f'BeginPrompt="即将安装{APP_DISPLAY}到 C:\\\\小龙人\\\\，是否继续？"\n'
                      f'RunProgram="cmd /c install.bat"\n'
                      f'GUIMode="2"\n'
                      f';!@InstallEnd@!\n')
            out.write(config.encode("utf-8"))
            out.write(archive.read_bytes())
        archive.unlink()
        size_mb = output.stat().st_size / (1024*1024)
        print(f"({size_mb:.1f}MB)")
        ok()
    else:
        # 降级：创建便携版zip（用户可以解压后运行install.bat）
        step("创建便携版ZIP")
        zip_path = OUTPUT_DIR / "xiaolongren-windows-portable.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(BUILD_DIR))
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"({size_mb:.1f}MB)")
        ok()
        print(f"  ⚠️ 7z未找到，生成便携版zip代替setup.exe")
        print(f"  → {zip_path}")

    print(f"  → {output}")
    return str(output)


# ============================================================
# macOS: .app bundle → .dmg
# ============================================================
def build_macos():
    """macOS: 生成 .dmg"""
    print("\n--- 🍎 macOS 安装包 ---")
    prepare_build_dir()

    app_name = f"{APP_DISPLAY}.app"
    app_dir = BUILD_DIR / app_name
    contents = app_dir / "Contents"
    macos_dir = contents / "MacOS"
    resources_dir = contents / "Resources"

    for d in [macos_dir, resources_dir]:
        d.mkdir(parents=True, exist_ok=True)

    step("创建 .app bundle")

    # Info.plist
    plist = contents / "Info.plist"
    plist.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>xiaolongren</string>
    <key>CFBundleIdentifier</key>
    <string>com.liuyong-pspai.xiaolongren</string>
    <key>CFBundleName</key>
    <string>{APP_DISPLAY}</string>
    <key>CFBundleDisplayName</key>
    <string>{APP_DISPLAY}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>''')

    # 启动脚本
    launcher_script = macos_dir / "xiaolongren"
    launcher_script.write_text(f'''#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
RES="$DIR/../Resources"
APP_DATA="$HOME/.xiaolongren"

# 首次运行：复制文件
if [ ! -f "$APP_DATA/config.json" ]; then
    mkdir -p "$APP_DATA"
    cp -R "$RES"/* "$APP_DATA/" 2>/dev/null
fi

cd "$APP_DATA"

# 优先用系统Python3
PYTHON=""
for p in /usr/bin/python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
    if [ -x "$p" ]; then PYTHON="$p"; break; fi
done
[ -z "$PYTHON" ] && PYTHON="python3"

exec "$PYTHON" launcher.py
''')
    os.chmod(launcher_script, 0o755)

    # 复制资源
    for item in (BUILD_DIR / "frontend").iterdir():
        dest = resources_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    engine = BUILD_DIR / "xiaolongren-engine"
    if engine.exists():
        shutil.copy2(engine, resources_dir / "xiaolongren-engine")

    launcher = BUILD_DIR / "launcher.py"
    if launcher.exists():
        shutil.copy2(launcher, resources_dir / "launcher.py")

    # 复制 .app 到 dist
    dist_app = OUTPUT_DIR / app_name
    if dist_app.exists():
        shutil.rmtree(dist_app)
    shutil.copytree(app_dir, dist_app)
    ok()

    # 创建 DMG
    step("创建 DMG")
    dmg_path = OUTPUT_DIR / "xiaolongren-installer.dmg"
    if dmg_path.exists():
        dmg_path.unlink()

    result = subprocess.run([
        "hdiutil", "create",
        "-volname", APP_DISPLAY,
        "-srcfolder", str(dist_app),
        "-ov", "-format", "UDZO",
        str(dmg_path)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        size_mb = dmg_path.stat().st_size / (1024*1024)
        print(f"({size_mb:.1f}MB)")
        ok()
    else:
        # 降级：ZIP
        print("(降级为ZIP)")
        shutil.make_archive(str(OUTPUT_DIR / "xiaolongren-macos"),
                            "zip", str(dist_app))
        ok()

    print(f"  → {OUTPUT_DIR}")
    return str(OUTPUT_DIR)


# ============================================================
# Linux: makeself → .run
# ============================================================
def build_linux():
    """Linux: 生成自解压 .run"""
    print("\n--- 🐧 Linux 安装包 ---")
    prepare_build_dir()

    step("创建自解压脚本")

    # 把所有内容打包成内嵌tar.gz
    payload_tar = BUILD_DIR.parent / "payload.tar.gz"
    subprocess.run(["tar", "czf", str(payload_tar),
                    "-C", str(BUILD_DIR), "."], check=True)

    # 创建自解压脚本
    run_path = OUTPUT_DIR / "xiaolongren-installer.run"

    with open(run_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# 🐉 小龙人 Linux 一键安装\n")
        f.write('set -e\n')
        f.write(f'APP_DIR="$HOME/.xiaolongren"\n')
        f.write(f'echo "🐉 {APP_DISPLAY} 安装中..."\n')
        f.write(f'mkdir -p "$APP_DIR"\n')
        f.write(f'echo "[1/3] 解压文件..."\n')
        f.write(f'ARCHIVE=$(mktemp)\n')
        f.write(f'sed "1,/^__PAYLOAD__$/d" "$0" > "$ARCHIVE"\n')
        f.write(f'tar xzf "$ARCHIVE" -C "$APP_DIR"\n')
        f.write(f'rm "$ARCHIVE"\n')
        f.write(f'echo "[2/3] 安装依赖..."\n')
        f.write(f'cd "$APP_DIR"\n')
        f.write(f'if command -v python3 &>/dev/null; then\n')
        f.write(f'    python3 -m pip install -q -r requirements.txt 2>/dev/null || true\n')
        f.write(f'fi\n')
        f.write(f'echo "[3/3] 创建桌面快捷方式..."\n')
        f.write(f'mkdir -p "$HOME/.local/share/applications"\n')
        f.write(f'cat > "$HOME/.local/share/applications/xiaolongren.desktop" << EOF\n')
        f.write(f'[Desktop Entry]\n')
        f.write(f'Name={APP_DISPLAY}\n')
        f.write(f'Comment=一个有灵魂的数字生命体\n')
        f.write(f'Exec=python3 {{{{APP_DIR}}}}/launcher.py\n')
        f.write(f'Path={{{{APP_DIR}}}}\n')
        f.write(f'Icon={{{{APP_DIR}}}}/frontend/img_longyuan.jpg\n')
        f.write(f'Terminal=false\n')
        f.write(f'Type=Application\n')
        f.write(f'Categories=Utility;AI;\n')
        f.write(f'EOF\n')
        # 替换双花括号为单花括号
        f.write(f'sed -i "s|{{{{APP_DIR}}}}|$APP_DIR|g" \\\n')
        f.write(f'    "$HOME/.local/share/applications/xiaolongren.desktop"\n')
        f.write(f'update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true\n')
        f.write(f'echo ""\n')
        f.write(f'echo "✅ 安装完成！正在启动..."\n')
        f.write(f'cd "$APP_DIR" && python3 launcher.py &\n')
        f.write(f'exit 0\n')
        f.write(f'__PAYLOAD__\n')

    os.chmod(run_path, 0o755)

    # 追加payload
    with open(run_path, "ab") as f:
        f.write(payload_tar.read_bytes())

    payload_tar.unlink()

    size_mb = run_path.stat().st_size / (1024*1024)
    print(f"({size_mb:.1f}MB)")
    ok()

    print(f"  → {run_path}")
    return str(run_path)


# ============================================================
# 主入口：自动检测平台 → 调用对应构建函数
# ============================================================
def main():
    print("=" * 60)
    print(f"  🐉 小龙人 安装包制作工具")
    print(f"  当前平台: {sys.platform}")
    print("=" * 60)

    builders = {
        "win32": ("Windows", build_windows),
        "darwin": ("macOS", build_macos),
        "linux": ("Linux", build_linux),
    }

    platform_name, builder = builders.get(sys.platform, (None, None))

    if builder is None:
        print(f"\n⚠️ 不支持的平台: {sys.platform}")
        print("  可用: " + ", ".join(builders.keys()))
        return 1

    print(f"\n🎯 目标: {platform_name} 安装包\n")

    try:
        result = builder()
        print(f"\n✅ {platform_name} 安装包已生成")
        print(f"   📦 {result}")
        return 0
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ 构建失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
