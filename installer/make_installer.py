#!/usr/bin/env python3
"""
小龙人 三平台一键安装包制作工具
在CI上运行，自动检测当前系统，生成对应安装包

Windows → xiaolongren-setup.zip (解压→双击bat→桌面图标→浏览器配模型)
macOS   → xiaolongren-installer.dmg (.app拖到Applications→启动台打开)
Linux   → xiaolongren-installer.run (./运行→应用菜单图标)

用户流程统一: 下载→双击→浏览器选模型填Key→开始聊天
"""
import os, sys, shutil, zipfile, subprocess, tempfile, urllib.request
from pathlib import Path

APP_DISPLAY = "🐉 小龙人"
PYTHON_VER = "3.12.9"
REPO_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = REPO_ROOT / "UI原型"
OUTPUT_DIR = REPO_ROOT / "dist"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = Path(tempfile.mkdtemp(prefix="xlr_"))


def step(msg):
    print(f"  [{msg}]", end=" ", flush=True)

def ok():
    print("✅")

def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)

def download(url, dest):
    print(f"    下载 {url.split('/')[-1]}...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print("OK")
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False


# ============================================================
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
    for name in candidates.get(sys.platform, []):
        p = REPO_ROOT / name
        if p.exists():
            return p
    return None


def prepare_build():
    """准备构建内容（前端+启动器+引擎）——三平台共用"""
    step("准备构建内容")
    # 前端
    shutil.copytree(FRONTEND_DIR, BUILD_DIR / "frontend", dirs_exist_ok=True)
    # 启动器
    shutil.copy2(REPO_ROOT / "launcher.py", BUILD_DIR / "launcher.py")
    # 引擎
    engine = find_engine()
    if engine:
        name = "xiaolongren-engine.exe" if sys.platform == "win32" else "xiaolongren-engine"
        shutil.copy2(engine, BUILD_DIR / name)
        os.chmod(BUILD_DIR / name, 0o755)
    n = sum(1 for _ in BUILD_DIR.rglob("*") if _.is_file())
    print(f"({n} 文件)")
    ok()


# ============================================================
# Windows
# ============================================================
def build_windows():
    print("\n--- 🪟 Windows 安装包 ---")
    prepare_build()

    # 安装引导bat
    bat = BUILD_DIR / "install.bat"
    bat.write_bytes(b'@echo off\r\n'
        b'chcp 65001 >nul\r\n'
        b'title XiaoLongRen Setup\r\n'
        b'echo ======================================\r\n'
        b'echo   XiaoLongRen Setup\r\n'
        b'echo ======================================\r\n'
        b'echo.\r\n'
        b'set "D=C:\\XiaoLongRen"\r\n'
        b'echo [1/5] Copying files to %D%...\r\n'
        b'xcopy /E /I /Y /Q "%~dp0*" "%D%" >nul\r\n'
        b'cd /d "%D%"\r\n'
        b'echo [2/5] Creating desktop shortcut...\r\n'
        b'powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath(\'Desktop\')+\'\\XiaoLongRen.lnk\');$s.TargetPath=\'pythonw\';$s.Arguments=\'%D%\\launcher.py\';$s.WorkingDirectory=\'%D%\';$s.Save()"\r\n'
        b'echo [3/5] Checking Python...\r\n'
        b'python --version >nul 2>&1 || (echo Python not found! Please install Python 3.10+ from python.org && pause && exit /b 1)\r\n'
        b'echo [4/5] Installing dependencies...\r\n'
        b'python -m pip install -q PyYAML Pillow requests >nul 2>&1\r\n'
        b'echo [5/5] Launching...\r\n'
        b'start "" pythonw "%D%\\launcher.py"\r\n'
        b'echo.\r\n'
        b'echo   Done! Browser opens for model setup.\r\n'
        b'echo   Desktop shortcut created.\r\n'
        b'timeout /t 3 >nul\r\n'
        b'exit\r\n')

    # 打包zip
    step("创建安装包ZIP")
    output = OUTPUT_DIR / "xiaolongren-setup.zip"
    shutil.make_archive(str(output.with_suffix("")), "zip", str(BUILD_DIR))
    mb = output.stat().st_size / (1024*1024)
    print(f"({mb:.1f}MB)")
    ok()
    print(f"  -> {output}")
    return str(output)


# ============================================================
# macOS
# ============================================================
def build_macos():
    print("\n--- 🍎 macOS 安装包 ---")
    prepare_build()

    step("创建 .app bundle")
    app = BUILD_DIR / "XiaoLongRen.app"
    macos_dir = app / "Contents" / "MacOS"
    res_dir = app / "Contents" / "Resources"
    macos_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    # Info.plist
    (app / "Contents" / "Info.plist").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict>\n'
        '<key>CFBundleExecutable</key><string>launch</string>\n'
        '<key>CFBundleIdentifier</key><string>com.liuyong-pspai.xiaolongren</string>\n'
        '<key>CFBundleName</key><string>XiaoLongRen</string>\n'
        '<key>CFBundleDisplayName</key><string>XiaoLongRen</string>\n'
        '<key>CFBundleVersion</key><string>1.0</string>\n'
        '<key>CFBundleShortVersionString</key><string>1.0</string>\n'
        '<key>CFBundlePackageType</key><string>APPL</string>\n'
        '<key>LSMinimumSystemVersion</key><string>11.0</string>\n'
        '<key>NSHighResolutionCapable</key><true/>\n'
        '</dict></plist>')

    # 启动脚本
    launch = macos_dir / "launch"
    launch.write_text('#!/bin/bash\n'
        'DIR="$(cd "$(dirname "$0")" && pwd)/../Resources"\n'
        'mkdir -p "$HOME/.xiaolongren"\n'
        'cp -Rn "$DIR"/* "$HOME/.xiaolongren/" 2>/dev/null\n'
        'cd "$HOME/.xiaolongren"\n'
        'PYTHON="python3"\n'
        '[ -x /opt/homebrew/bin/python3 ] && PYTHON=/opt/homebrew/bin/python3\n'
        '[ -x /usr/local/bin/python3 ] && PYTHON=/usr/local/bin/python3\n'
        'exec "$PYTHON" launcher.py\n')
    os.chmod(launch, 0o755)

    # 复制资源
    for item in BUILD_DIR.iterdir():
        if item.name != "XiaoLongRen.app":
            dest = res_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    # 移到dist
    dist_app = OUTPUT_DIR / "XiaoLongRen.app"
    if dist_app.exists():
        shutil.rmtree(dist_app)
    shutil.copytree(app, dist_app)
    ok()

    # 创建DMG
    step("创建 DMG")
    dmg = OUTPUT_DIR / "xiaolongren-installer.dmg"
    if dmg.exists():
        dmg.unlink()
    r = subprocess.run(["hdiutil", "create", "-volname", "XiaoLongRen",
        "-srcfolder", str(dist_app), "-ov", "-format", "UDZO", str(dmg)],
        capture_output=True, text=True)
    if r.returncode == 0:
        mb = dmg.stat().st_size / (1024*1024)
        print(f"({mb:.1f}MB)")
        ok()
    else:
        print("(降级ZIP)")
        shutil.make_archive(str(OUTPUT_DIR / "xiaolongren-macos"), "zip",
                           str(dist_app))
        ok()
    print(f"  -> {OUTPUT_DIR}")
    return str(OUTPUT_DIR)


# ============================================================
# Linux
# ============================================================
def build_linux():
    print("\n--- 🐧 Linux 安装包 ---")
    prepare_build()

    step("创建自解压脚本")
    payload = BUILD_DIR.parent / "payload.tar.gz"
    subprocess.run(["tar", "czf", str(payload), "-C", str(BUILD_DIR), "."],
                   check=True)

    run_path = OUTPUT_DIR / "xiaolongren-installer.run"
    with open(run_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("set -e\n")
        f.write('APP="$HOME/.xiaolongren"\n')
        f.write('echo "Installing XiaoLongRen..."\n')
        f.write('mkdir -p "$APP"\n')
        f.write('ARCHIVE=$(mktemp)\n')
        f.write('sed "1,/^__PAYLOAD__$/d" "$0" > "$ARCHIVE"\n')
        f.write('tar xzf "$ARCHIVE" -C "$APP"\n')
        f.write('rm "$ARCHIVE"\n')
        f.write('cd "$APP"\n')
        f.write('python3 -m pip install -q PyYAML Pillow requests 2>/dev/null || true\n')
        f.write('mkdir -p "$HOME/.local/share/applications"\n')
        f.write('cat > "$HOME/.local/share/applications/xiaolongren.desktop" << DESKTOPEOF\n')
        f.write('[Desktop Entry]\n')
        f.write('Name=XiaoLongRen\n')
        f.write('Comment=AI Digital Companion\n')
        f.write('Exec=python3 $HOME/.xiaolongren/launcher.py\n')
        f.write('Path=$HOME/.xiaolongren\n')
        f.write('Terminal=false\n')
        f.write('Type=Application\n')
        f.write('Categories=Utility;\n')
        f.write('DESKTOPEOF\n')
        f.write('echo "Done! Starting..."\n')
        f.write('python3 launcher.py &\n')
        f.write('exit 0\n')
        f.write('__PAYLOAD__\n')
    os.chmod(run_path, 0o755)

    with open(run_path, "ab") as f:
        f.write(payload.read_bytes())
    payload.unlink()

    mb = run_path.stat().st_size / (1024*1024)
    print(f"({mb:.1f}MB)")
    ok()
    print(f"  -> {run_path}")
    return str(run_path)


# ============================================================
def main():
    builders = {
        "win32": ("Windows", build_windows),
        "darwin": ("macOS", build_macos),
        "linux": ("Linux", build_linux),
    }
    name, fn = builders.get(sys.platform, (None, None))
    if not fn:
        print(f"Unsupported: {sys.platform}")
        return 1

    print("=" * 60)
    print(f"  XiaoLongRen Installer Builder - {name}")
    print("=" * 60)

    try:
        result = fn()
        print(f"\nDone: {result}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
