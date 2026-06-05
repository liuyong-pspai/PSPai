#!/bin/bash
# 小龙人电脑版 — macOS安装脚本

cd "$(dirname "$0")"
INSTALL_DIR="$HOME/Library/Application Support/XiaoLongRen"
DESKTOP_DIR="$HOME/Desktop"

echo "================================"
echo "   🐉 小龙人 电脑版 安装"
echo "================================"
echo ""

# 防止重复安装
if [ -d "$DESKTOP_DIR/小龙人.app" ]; then
    echo "✅ 已安装，桌面已有 "小龙人" 图标"
    echo "🚀 正在启动..."
    open "$DESKTOP_DIR/小龙人.app"
    exit 0
fi

# 创建安装目录
echo "📂 正在复制文件到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -R "$PWD"/* "$INSTALL_DIR/" 2>/dev/null

# 创建 .app 包（真正的应用图标，不只是别名）
echo "🖥️ 正在创建桌面图标..."
APP_BUNDLE="$DESKTOP_DIR/小龙人.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Info.plist
cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.xiaolongren.app</string>
    <key>CFBundleName</key>
    <string>小龙人</string>
    <key>CFBundleIconFile</key>
    <string>appicon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
EOF

# 启动脚本（用open命令打开index.html）
cat > "$APP_BUNDLE/Contents/MacOS/launcher" << 'SCRIPT'
#!/bin/bash
open "$HOME/Library/Application Support/XiaoLongRen/index.html"
SCRIPT
chmod +x "$APP_BUNDLE/Contents/MacOS/launcher"

# 复制图标（macOS用icns格式，没icns的话用png也可以）
if [ -f "icon-512.png" ]; then
    cp "icon-512.png" "$APP_BUNDLE/Contents/Resources/appicon.png"
fi

# 设置图标（让Finder显示应用）
xattr -w com.apple.FinderInfo "$(printf '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')" "$APP_BUNDLE" 2>/dev/null || true

if [ -d "$APP_BUNDLE" ]; then
    echo "✅ 安装完成！"
    echo ""
    echo "================================"
    echo "   🐉 桌面已生成 "小龙人" 图标"
    echo "   双击图标即可启动"
    echo "================================"
    echo ""
    echo "🚀 正在启动小龙人..."
    open "$APP_BUNDLE"
    echo ""
    echo "💡 如需卸载：rm -rf $INSTALL_DIR $APP_BUNDLE"
else
    echo "❌ 图标创建失败"
    echo "🚀 正在直接打开..."
    open "index.html"
fi
