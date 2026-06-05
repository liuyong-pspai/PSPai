#!/bin/bash
# 小龙人电脑版 — 直接在浏览器中打开
cd "$(dirname "$0")"
echo "================================="
echo "   🐉 小龙人 电脑版"
echo "================================="
echo "🚀 在浏览器中打开..."
if command -v xdg-open &>/dev/null; then
    xdg-open "index.html"
elif command -v open &>/dev/null; then
    open "index.html"
else
    echo "请手动在浏览器中打开 index.html"
fi
