---
name: static-asset-integrity-check
description: >
  静态Web UI部署完整性验证。当用户说「页面打不开」「图片不显示」「按钮没反应」「CSS没加载」
  「部署后UI不对」时触发。涵盖HTML资产依赖提取、自定义路由匹配验证、HTTP可达性验证、
  CSS变量vs硬编码覆盖诊断。核心铁律：部署到新位置后，必须逐文件验证每个asset存在且可路由。
---

# 静态资产完整性验证 (Static Asset Integrity Check)

## 触发条件
- 用户反馈：页面打不开、图片不显示、按钮没反应、样式不对、JS功能失效
- 刚把HTML/UI从一处复制/部署到另一处
- 自定义HTTP服务器（非nginx/apache标准静态服务）

## 核心诊断模式

### 第一步：确认自定义路由覆盖全集
自定义HTTP服务器的静态文件路由通常是**白名单模式**——只服务明确列出的路径前缀。
新增资源目录（如 `/themes/` / `/assets/`）必须在路由代码中显式注册。

```python
# 典型问题：serve_ui.py 第847行
# 缺少 path.startswith("/themes/") → 所有主题CSS/JS返回404
```

**诊断命令**：
```bash
grep "path.startswith\|path in \[\]" serve_ui.py
# 对照实际目录结构，确保每个子目录都有对应前缀
```

### 第二步：从HTML提取全部资产依赖
扫描HTML中所有外部资源引用：
```bash
# 提取 src= href= url()
grep -oP '(src|href|url)\s*[=\(]\s*["'\'']?\K[^"'\'')\s>]+' page.html | sort -u
```

### 第三步：对照路由规则映射文件系统路径
将第二步提取的路径，按服务器的路由解析逻辑，映射到实际文件系统路径。

### 第四步：逐文件验证存在性
```bash
# 每个asset都要检查
for p in $(extracted_paths); do
  fspath = resolve_route_to_fs($p)  # 按路由逻辑转换
  test -f "$fspath" && echo "✓ $p" || echo "✗ MISSING: $p → $fspath"
done
```

### 第五步：HTTP可达性验证
```bash
for p in $(extracted_paths); do
  code=$(curl -s --max-time 3 -o /dev/null -w '%{http_code}' "http://HOST:PORT$p")
  [ "$code" != "200" ] && echo "✗ $p → HTTP $code"
done
```

## 本次会话验证清单（serve_ui.py + 龙宫UI）

已验证通过的全部资源路由：

| 路径前缀 | 对应目录 | 路由状态 |
|:---|:---|:---|
| `/` | p01_ui.html | ✅ |
| `/themes/` | themes/ | ⚠️ 初始缺少（2026-05-31），补 `path.startswith("/themes/")` |
| `/lang/` | lang/ | ✅ |
| `/css/` | css/ | ✅ |
| `/js/` | js/ | ✅ |
| `/assets/` | assets/ | ⚠️ 目录完全缺失，从原始项目 `cp -r` 复制 |
| `/mobile/` | mobile/ | ✅ |
| `/background.jpg` | background.jpg | ✅（7.8MB）|
| `/favicon.ico` | favicon.ico | ✅ |

### 新增目录路由修改模板
```python
# 在 serve_ui.py 第847行添加新目录前缀
elif path.startswith("/new-dir/") or ... # 添加新前缀
```

### assets/ 目录缺失的标准修复
```bash
# 从原始项目或备份中复制整个assets目录
cp -r /path/to/original/assets/* /path/to/deploy/assets/
# 验证子目录
ls assets/avatars/ assets/client_avatars/

## 常见根因速查

| 症状 | 常见根因 | 修复 |
|:---|:---|:---|
| 整个页面空白 | 路由缺少 `/themes/` 前缀，CSS/JS全部404 | 补路由 |
| Logo/图片不显示 | `assets/` 目录未复制到部署位置 | 复制+验证 |
| 主题切换无效果 | CSS变量被硬编码色覆盖，肉眼不可见 | 切换时直接改body背景色 |
| JS按钮无反应 | 外部脚本文件404或函数未定义 | 检查script src可达性 |
| 头像面板无图 | avatar文件未复制 | 检查 assets/avatars/ |
| 语言切换无反应 | lang.js加载失败或I18N对象未暴露 | 检查 /lang/lang.js 可达 |

## CSS变量主题切换的致命缺陷

仅靠CSS变量（`--bg-deep` / `--gold`）切换主题，在大量硬编码颜色的页面中**视觉变化几乎不可见**。
必须配合**直接属性修改**：

```javascript
// 不够：只设 data-theme，依赖CSS变量
document.documentElement.setAttribute('data-theme', name);

// 必须：同时直接改body背景等关键属性
document.body.style.background = BG_GRADIENTS[name];
```

激活按钮也要直接设box-shadow，不依赖CSS变量。

### 陷阱：`!important` CSS覆盖屏蔽背景图

```css
/* ❌ 这会永久覆盖 background.jpg */
#bg-layer {
  background: var(--bg-pattern) var(--bg-deep) !important;
  filter: none !important;
}

/* ✅ 让JS动态控制，不用 !important */
/* #bg-layer 的背景由 switchTheme() 直接操作 style 属性 */
```

**教训：** 所有视觉主题切换的关键属性（背景、字体、边框色），用JS直接操作 `element.style.*`，不用CSS变量+`!important`。变量只用于颜色、边框等辅助属性。

## JS功能失效诊断（按钮无反应）

当用户反馈"按钮没反应"时，按以下顺序排查：

### 第0步：外部脚本是否404
```bash
# 从HTML提取所有 src= 引用
grep -oP 'src="[^"]*"' page.html
# 逐条HTTP验证
for f in $extracted_srcs; do
  curl -s --max-time 2 -o /dev/null -w "%{http_code} $f\n" "http://HOST$f"
done
```

### 第1步：函数是否暴露为全局
```bash
# onclick="switchTheme('palace')" → 需要 window.switchTheme 存在
grep 'window\.switchTheme\|window\.I18N' theme-switcher.js lang.js
```

### 第2步：是否有IE11级语法错误
```javascript
// ❌ 箭头函数在旧浏览器报错（但现代浏览器OK）
// ✅ IIFE 模式兼容性最好
(function() { window.switchTheme = applyTheme; })();
```

### 第3步：CSS是否阻断了点击
```bash
# 检查是否有 pointer-events: none 或覆盖性 z-index
grep -n 'pointer-events\|z-index' page.html
```

## 多主题UI + 多语言I18N双轨协同

当页面同时有主题切换（🐉⚡🏭）和语言切换（🌐）时：

### 分工规则
| 属性 | 系统 | 作用 |
|:---|:---|:---|
| `data-theme-key` | theme-switcher.js | 风格化名称（门匾、状态栏口号）|
| `data-i18n` | lang.js | 通用标签（按钮、表单、关于页）|
| 两者都有 | I18N最后写入 | 语言切换后重刷主题 |

### 语言切换回调
```javascript
i18n.setLang(code).then(function() {
  window.switchTheme(window.getTheme()); // 回写主题文字
});
```


## 资产引用完整性自动检测脚本

参考 `scripts/check_asset_integrity.sh` — 从HTML提取所有引用路径并验证HTTP可达性。
