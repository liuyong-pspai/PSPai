# serve_ui.py 静态路由白名单审计

> 来源：2026-05-31 龙宫UI三主题部署故障

## 路由匹配代码（第847行）

```python
elif path.startswith("/css/") or path.startswith("/js/") or \
     path.startswith("/assets/") or path.startswith("/lang/") or \
     path.startswith("/themes/") or \
     path.startswith("/mobile/css/") or path.startswith("/mobile/js/") or \
     path.startswith("/mobile/") or \
     path in ["/background.jpg", "/favicon.ico", "/sw.js", "/manifest.json"]:
```

## 路由规则

每个 `path.startswith(X)` 将请求路径映射到 `PROJECT_ROOT/X`（去掉前导斜杠）。
单独文件（background.jpg等）用 `path in [...]` 精确匹配。

## 新增资源目录时的操作清单

1. 创建目录放在 PROJECT_ROOT 下
2. 在路由代码中添加对应的 `path.startswith("/新目录/")`
3. 重启 serve_ui.py
4. curl 验证每个新资源返回 200

## 本次故障链

1. 创建 `/tmp/longgong/themes/` 目录 → ✅
2. 写入 `three-realms.css` 和 `theme-switcher.js` → ✅
3. HTML 引用 `/themes/three-realms.css` → ✅
4. **忘记在 serve_ui.py 中添加 `/themes/` 路由** → ❌ 所有主题资源 404
5. 页面加载时CSS 404 → 主题变量未定义 → 按钮无视觉反馈

后续又发现：
6. `assets/` 整个目录未复制 → logo.png、avatars/*.png、client_avatars/*.png 全部404
7. CSS变量被硬编码色覆盖 → 主题切换肉眼不可见
