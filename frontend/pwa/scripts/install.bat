@echo off
title 小龙人 安装程序
cd /d "%~dp0"

echo ================================
echo    🐉 小龙人 电脑版 安装
echo ================================
echo.

:: 检查是否已经有快捷方式（防止重复安装）
if exist "%USERPROFILE%\Desktop\小龙人.lnk" (
    echo ✅ 已安装，桌面已有 "小龙人" 图标
    echo 🚀 正在启动...
    start "" "%USERPROFILE%\Desktop\小龙人.lnk"
    goto :eof
)

echo 📂 正在复制文件到安装目录...
:: 创建安装目录（如果不存在）
if not exist "%LOCALAPPDATA%\XiaoLongRen" mkdir "%LOCALAPPDATA%\XiaoLongRen"

:: 复制所有文件
xcopy /E /I /Y "%~dp0*" "%LOCALAPPDATA%\XiaoLongRen\" >nul 2>&1

echo 🖥️ 正在创建桌面快捷方式...
:: 用PowerShell创建快捷方式（兼容Win7+）
powershell -Command ^
    $WS = New-Object -ComObject WScript.Shell; ^
    $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\小龙人.lnk'); ^
    $SC.TargetPath = '%LOCALAPPDATA%\XiaoLongRen\index.html'; ^
    $SC.WorkingDirectory = '%LOCALAPPDATA%\XiaoLongRen'; ^
    $SC.Description = '🐉 小龙人 — 全功能AI助手'; ^
    $SC.Save();

if exist "%USERPROFILE%\Desktop\小龙人.lnk" (
    echo ✅ 安装完成！
    echo.
    echo ================================
    echo   🐉 桌面已生成 "小龙人" 图标
    echo   双击图标即可启动
    echo ================================
    echo.
    echo 🚀 正在启动小龙人...
    start "" "%USERPROFILE%\Desktop\小龙人.lnk"
    echo.
    echo 💡 如需卸载，运行卸载程序即可
) else (
    echo ❌ 快捷方式创建失败，请手动运行 index.html
    start "" "index.html"
)

pause
