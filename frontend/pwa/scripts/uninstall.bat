@echo off
title 小龙人 卸载程序
echo ================================
echo    🐉 小龙人 卸载
echo ================================
echo.
set /p confirm="确定要卸载小龙人吗？(y/n): "
if /i not "%confirm%"=="y" goto :eof

echo 🗑️ 删除桌面图标...
if exist "%USERPROFILE%\Desktop\小龙人.lnk" del "%USERPROFILE%\Desktop\小龙人.lnk"

echo 🗑️ 删除程序文件...
if exist "%LOCALAPPDATA%\XiaoLongRen" rmdir /S /Q "%LOCALAPPDATA%\XiaoLongRen"

echo ✅ 已卸载完成。
echo.
echo 💡 您还可以手动删除下载的解压包。
pause
