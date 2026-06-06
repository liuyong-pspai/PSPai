#!/usr/bin/env python3
"""
小龙人 Windows 安装器（PyInstaller stub）
被PyInstaller打包成单个setup.exe，内含：
  - Python embeddable
  - PSPAI引擎
  - 前端UI
  - 启动器
"""
import sys, os, shutil, subprocess, json, time, tempfile
from pathlib import Path

APP_NAME = "🐉 小龙人"
INSTALL_DIR = Path("C:/小龙人")


def get_data_dir():
    """PyInstaller打包后数据在 sys._MEIPASS"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / "payload"
    return Path(__file__).parent.parent / "BUILD_TEMP"


def install():
    print(f"\n  {APP_NAME} 安装中...\n")

    data = get_data_dir()

    # 1. 解压文件
    print("  [1/4] 安装文件到 C:\\小龙人\\ ...")
    if INSTALL_DIR.exists():
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    shutil.copytree(data, INSTALL_DIR, dirs_exist_ok=True)
    print("        完成")

    # 2. 配置Python环境
    print("  [2/4] 配置Python环境...")
    python_exe = INSTALL_DIR / "python" / "python.exe"
    if python_exe.exists():
        # 安装pip和依赖
        try:
            subprocess.run([str(python_exe), "-m", "ensurepip"],
                          capture_output=True, timeout=60)
            subprocess.run([str(python_exe), "-m", "pip", "install", "-q",
                          "PyYAML", "Pillow", "requests"],
                          capture_output=True, timeout=120)
        except Exception:
            pass
    print("        完成")

    # 3. 桌面快捷方式
    print("  [3/4] 创建桌面快捷方式...")
    try:
        ps_cmd = (
            f'$WshShell = New-Object -ComObject WScript.Shell;'
            f'$Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath("Desktop") + "\\{APP_NAME}.lnk");'
            f'$Shortcut.TargetPath = "{INSTITALL_DIR}\\python\\pythonw.exe";'
            f'$Shortcut.Arguments = "{INSTITALL_DIR}\\launcher.py";'
            f'$Shortcut.WorkingDirectory = "{INSTITALL_DIR}";'
            f'$Shortcut.Description = "{APP_NAME} XiaoLongRen";'
            f'$Shortcut.Save()'
        )
        # 转义$符号
        ps_cmd_escaped = ps_cmd.replace('"', '\\"')
        subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-Command", ps_cmd
        ], capture_output=True)
        print("        桌面快捷方式已创建")
    except Exception as e:
        print(f"        快捷方式创建失败: {e}")

    # 4. 启动
    print("  [4/4] 启动小龙人...")
    pythonw = INSTALL_DIR / "python" / "pythonw.exe"
    launcher = INSTALL_DIR / "launcher.py"
    if pythonw.exists():
        subprocess.Popen(
            [str(pythonw), str(launcher)],
            cwd=str(INSTALL_DIR),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

    print(f"\n  ✅ 安装完成！浏览器将自动打开配置向导。")
    print(f"  桌面已创建快捷方式，下次双击图标即可启动。")
    print()
    input("  按回车键退出安装程序...")


if __name__ == "__main__":
    install()
