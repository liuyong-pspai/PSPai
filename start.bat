@echo off
chcp 65001 >nul
title 小龙人 XiaoLongRen
echo 🐉 小龙人 XiaoLongRen 启动中...
echo.

REM 1. Check .env
if not exist .env (
    echo ❌ 未找到 .env 文件
    echo    请先复制: copy .env.example .env
    echo    然后用记事本编辑 .env，填入 PSPAI_API_KEY
    pause
    exit /b 1
)

REM 2. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python，请先安装 Python 3.10+
    echo    https://www.python.org/downloads/
    echo    ⚠️ 安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo ✅ Python 就绪

REM 3. Find engine
set ENGINE=xiaolongren-engine-windows.exe
if not exist "%ENGINE%" (
    echo ❌ 未找到引擎文件: %ENGINE%
    echo.
    echo    请从 GitHub Releases 下载 Windows 引擎:
    echo    https://github.com/liuyong-pspai/PSPai/releases
    echo.
    echo    下载后把 %ENGINE% 放到当前目录
    pause
    exit /b 1
)
echo ✅ 引擎: %ENGINE%

REM 4. Install Python deps
if not exist .deps_installed (
    echo 📦 安装 Python 依赖...
    pip install -q PyYAML Pillow requests
    if %errorlevel% neq 0 (
        echo ⚠️ pip 安装失败，尝试 python -m pip ...
        python -m pip install -q PyYAML Pillow requests
    )
    type nul > .deps_installed
    echo ✅ 依赖安装完成
)

REM 5. Start engine
echo 🚀 启动 PSPAI 引擎 (8089)...
start "PSPAI Engine" "%ENGINE%"

REM 6. Start frontend
echo 🚀 启动前端界面 (8088)...
cd "UI原型"
start "XiaoLongRen UI" /B python server.py
cd ..

REM 7. Wait and open browser
timeout /t 3 /nobreak >nul
echo.
echo ═══════════════════════════════════════
echo   🐉  小龙人 已启动！
echo   🌐  打开浏览器访问: http://localhost:8088
echo ═══════════════════════════════════════
echo.
start http://localhost:8088
echo 按任意键停止...
pause >nul

REM Cleanup
taskkill /f /im xiaolongren-engine-windows.exe >nul 2>&1
echo 🛑 已停止
