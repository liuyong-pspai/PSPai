# 三界主题系统 — CSS变量驱动的多主题UI方案

> 伏羲超体 🐉 产品发布 UI 三大主题
> 设计原则：龙宫/科技/Loft 三种风格完全差异化，不雷同
> 2026-05-31 Agent 从伏羲FX龙宫版改造提炼

## 架构

```
data-theme="palace"    龙宫 — 中国古风·王者气
data-theme="cyber"     科技 — 极光蓝·赛博
data-theme="loft"      Loft — 工业朋克·个性
```

24个CSS变量驱动：`--bg-deep` `--bg-mid` `--bg-light` `--gold` `--gold-bright` `--gold-dark` `--red` `--text-primary` `--text-secondary` `--text-muted` `--border-color` `--border-glow` `--shadow-gold` `--font-display` `--font-body` `--btn-bg` `--btn-hover` `--panel-bg` `--input-bg` `--accent-glow` `--bg-pattern`

## 三主题规范

### 🐉 龙宫版 — 中国古风

| 元素 | 值 |
|:---|:---|
| 主色 | 琉璃金 `#C8A84E` / 朱砂 `#B5343A` |
| 底色 | 墨玉 `#0A0F14` + SVG云纹暗纹 |
| 字体 | `Palace`/宋体/`Noto Serif CJK SC` |
| 氛围 | 宫殿剪影、龙纹底纹、印章图标、金色描边发光 |

### ⚡ 科技版 — 纯科技风

| 元素 | 值 |
|:---|:---|
| 主色 | 极光青 `#00E5FF` / 深紫 `#6C3CF0` |
| 底色 | 深空 `#060B14` + SVG网格点阵 |
| 字体 | `Inter`/`SF Pro Display`（中文：阿里普惠体） |
| 氛围 | 玻璃态毛玻璃、霓虹边框、粒子连线、扫描线 |

### 🏭 Loft版 — 工业朋克

| 元素 | 值 |
|:---|:---|
| 主色 | 混凝土 `#8B8B83` / 铁锈 `#C2541E` |
| 底色 | 水泥 `#1A1A18` + SVG铆钉纹理 |
| 字体 | `JetBrains Mono`/`Fira Code`（中文：站酷高端黑） |
| 氛围 | 粗边框、铆钉阴影、金属反光 |

## 背景纹理

三套纯SVG内联暗纹（`data:image/svg+xml`），无外部图片依赖：

- **龙宫**：云纹 — 曲线路径模拟祥云
- **科技**：网格点阵 — 圆形点+对角线
- **Loft**：铆钉 — 矩形边框+中心点

## 集成方式

### HTML 引入（最小改动）

```html
<link rel="stylesheet" href="/themes/three-realms.css">
<script src="/themes/theme-switcher.js"></script>
```

### 顶部栏按钮

```html
<span class="theme-dot" data-theme="palace" onclick="switchTheme('palace')">🐉</span>
<span class="theme-dot" data-theme="cyber" onclick="switchTheme('cyber')">⚡</span>
<span class="theme-dot" data-theme="loft" onclick="switchTheme('loft')">🏭</span>
```

### JS API

```js
window.switchTheme('cyber')     // 切换
window.getTheme()               // 当前主题
localStorage.setItem('fuxi_theme', 'palace')  // 持久化
```

### CSS变量绑定

在现有style末尾注入覆盖规则，将硬编码颜色绑定到CSS变量：

```css
html, body { background: var(--bg-deep) !important; color: var(--text-primary) !important; }
#palace { background: transparent !important; }
.door:hover { border-color: var(--border-glow) !important; box-shadow: var(--shadow-gold) !important; }
/* ... 40+ 规则覆盖所有关键元素 */
```

## 已有UI资产（从伏羲FX继承）

- `p01_ui.html` 1957行完整龙宫版（六扇门+卷轴对话区+偏殿浮层）
- `mobile/index.html` 342行移动PWA版（龙宫主题+lang.js）
- `lang/` 30种语言包（ar→zh-CN全涵盖）
- `lang/lang.js` 多语言引擎（自动检测+data-i18n+手动切换）
- `serve_ui.py` 1542行Flask服务器（桌面+移动双路由）

## 三主题改造已有缺陷（需后续修复）

1. 六扇门名称是"一人公司"CxO功能（龙渊阁/玄剑台…），不是伏羲能力入口
2. 原style标签中仍有大量硬编码颜色，依赖`!important`覆盖（非最佳实践）
3. 精简版(168行)未同步改造
4. 桌面版未引入lang.js（移动版有），30语言包闲置
5. 底部状态栏"P01内核"残留
6. WebSocket URL硬编码 `ws://localhost:3000/ws`

## 文件位置

- `themes/three-realms.css` — CSS变量文件
- `themes/theme-switcher.js` — 切换引擎JS
- `/tmp/longgong/p01_ui.html` — 已集成三主题的龙宫完整版（70509字节）
- `prototypes/` — 原始伏羲FX项目
