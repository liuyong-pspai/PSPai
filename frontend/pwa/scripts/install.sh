#!/bin/bash
# 小龙人电脑版 — Linux安装脚本

cd "$(dirname "$0")"
INSTALL_DIR="$HOME/.xiaolongren"
DESKTOP_FILE="$HOME/Desktop/小龙人.desktop"
ICON_SRC="$PWD/icon-192.png"

echo "================================"
echo "   🐉 小龙人 电脑版 安装"
echo "================================"
echo ""

# 防止重复安装
if [ -f "$DESKTOP_FILE" ]; then
    echo "✅ 已安装，桌面已有 "小龙人" 图标"
    echo "🚀 正在启动..."
    xdg-open "$DESKTOP_FILE" 2>/dev/null || xdg-open "$INSTALL_DIR/index.html"
    exit 0
fi

# 创建安装目录
echo "📂 正在复制文件到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -r "$PWD"/* "$INSTALL_DIR/" 2>/dev/null
# 如果复制自身（脚本位置问题）则忽略
if [ -f "$INSTALL_DIR/install.sh" ]; then
    chmod +x "$INSTALL_DIR/install.sh"
fi

# 创建桌面快捷方式 (.desktop文件)
echo "🖥️ 正在创建桌面图标..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=小龙人
Comment=🐉 全功能AI助手
Exec=xdg-open "$INSTALL_DIR/index.html"
Icon=$INSTALL_DIR/icon-192.png
Terminal=false
Categories=Utility;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

# 也添加到应用程序菜单
mkdir -p "$HOME/.local/share/applications"
cp "$DESKTOP_FILE" "$HOME/.local/share/applications/xiaolongren.desktop"

if [ -f "$DESKTOP_FILE" ]; then
    echo "✅ 安装完成！"
    echo ""
    echo "================================"
    echo "   🐉 桌面已生成 "小龙人" 图标"
    echo "   双击图标即可启动"
    echo "================================"
    echo ""
    echo "🚀 正在启动小龙人..."
    xdg-open "$INSTALL_DIR/index.html" 2>/dev/null || echo "请手动打开 index.html"
    echo ""
    echo "💡 如需卸载：rm -rf $INSTALL_DIR $DESKTOP_FILE"
else
    echo "❌ 图标创建失败"
    echo "🚀 正在直接打开..."
    xdg-open "index.html" 2>/dev/null || echo "请手动打开 index.html"
fi
