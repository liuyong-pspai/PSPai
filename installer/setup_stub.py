#!/usr/bin/env python3
r"""
PyInstaller stub — 自解压安装器
当7z SFX不可用时使用PyInstaller打包
运行后解压文件到 C:\小龙人\ 并启动安装
"""
import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    print("🐉 小龙人 XiaoLongRen 安装中...")
    print()

    # PyInstaller打包的数据在 sys._MEIPASS/app_data/
    if getattr(sys, 'frozen', False):
        app_data = Path(sys._MEIPASS) / "app_data"
    else:
        app_data = Path(__file__).parent.parent / "BUILD_TEMP"

    install_dir = Path("C:/小龙人")

    # 1. 复制文件
    print("[1/3] 安装文件...")
    if install_dir.exists():
        shutil.rmtree(install_dir, ignore_errors=True)
    shutil.copytree(app_data, install_dir, dirs_exist_ok=True)

    # 2. 创建快捷方式
    print("[2/3] 创建桌面快捷方式...")
    try:
        import pythoncom
        from win32com.client import Dispatch
        pythoncom.CoInitialize()

        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(desktop / "🐉 小龙人.lnk"))

        python_exe = install_dir / "python" / "pythonw.exe"
        if python_exe.exists():
            shortcut.TargetPath = str(python_exe)
            shortcut.Arguments = str(install_dir / "launcher.py")
        else:
            shortcut.TargetPath = "pythonw"
            shortcut.Arguments = str(install_dir / "launcher.py")

        shortcut.WorkingDirectory = str(install_dir)
        shortcut.Description = "🐉 小龙人 XiaoLongRen"
        shortcut.Save()
        print("   桌面快捷方式已创建")
    except Exception as e:
        print(f"   快捷方式创建失败: {e}")
        print("   请手动将 C:\\小龙人\\launcher.py 发送到桌面")

    # 3. 启动
    print("[3/3] 启动小龙人...")
    python_exe = install_dir / "python" / "pythonw.exe"
    launcher = install_dir / "launcher.py"

    if python_exe.exists():
        subprocess.Popen(
            [str(python_exe), str(launcher)],
            cwd=str(install_dir),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(
            ["pythonw", str(launcher)],
            cwd=str(install_dir),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    print()
    print("✅ 安装完成！浏览器将自动打开配置向导。")
    print("   桌面已创建快捷方式，下次双击图标即可启动。")
    input("按回车键退出...")


if __name__ == "__main__":
    main()
