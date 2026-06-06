#!/bin/bash
# 小龙人 — macOS卸载脚本

INSTALL_DIR="$HOME/Library/Application Support/XiaoLongRen"
DESKTOP_DIR="$HOME/Desktop/小龙人.app"

echo "================================"
echo "   🐉 小龙人 卸载"
echo "================================"
echo ""
read -p "确定要卸载小龙人吗？(y/n): " confirm
if [ "$confirm" != "y" ]; then
    exit 0
fi

echo "🗑️ 删除桌面图标..."
rm -rf "$DESKTOP_DIR"

echo "🗑️ 删除程序文件..."
rm -rf "$INSTALL_DIR"

echo "✅ 已卸载完成。"
echo ""
echo "💡 您还可以手动删除下载的解压包。"
