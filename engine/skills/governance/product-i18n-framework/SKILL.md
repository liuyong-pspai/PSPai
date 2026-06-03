---
name: product-i18n-framework
category: governance
version: 1.0.0
author: 刘玉龙 P07
tags: [i18n, multi-language, product, packaging, locale]
last_updated: 2026-06-01
description: >
  AI产品多语言架构——前端异步语言包 + 后端语言人格同步 + 加语言零代码改动。
  当需要给产品（Web UI + Agent后端）添加多语言支持时触发。
  覆盖：语言JSON设计、data-i18n属性规范、按lang切换系统提示词、RTL预留。
related_skills: [agent-product-release, static-asset-integrity-check]
---

# 产品多语言架构

> 一套安装包，支持任意语言。加语言 = 丢一个JSON文件 + 加一段系统提示词。

## 架构总览

```
安装包/
├── lang/                    ← 语言包目录（独立JSON）
│   ├── zh.json              ← 中文
│   ├── en.json              ← 英文
│   └── fr.json              ← 法文（加语言=加一个文件）
├── index.html               ← 只写 data-i18n 属性，不含翻译
└── config.yaml              ← 含各语言系统提示词
    ├── system_prompt         ← 中文人格
    ├── en_system_prompt      ← 英文人格
    └── fr_system_prompt      ← 法文人格
```

## 前端：异步JSON语言包

### HTML规范

所有文本用 `data-i18n` / `data-i18n-ph` / `data-i18n-title` 标记，不在HTML里写死翻译：

```html
<!-- 文本内容 -->
<span data-i18n="memo">备忘</span>

<!-- 输入框占位符 -->
<input data-i18n-ph="chat_ph">

<!-- title属性 -->
<div data-i18n-title="replace_av">📷</div>
```

HTML里保留的默认值作为加载失败时的降级显示。

### 语言包JSON格式

```json
{
  "lang_label": "EN",
  "memo": "Memo",
  "chat_ph": "Say something…",
  "model_cfg": "Configured ✅",
  "model_need": "API Key Required"
}
```

63-79个key覆盖全部界面文字。命名规范：蛇形命名，面板前缀（`perm_` / `model_` / `vid_` 等）。

### JS加载器

```javascript
var I18N_CACHE = {};   // 缓存已加载的语言包
var I18N_DATA = null;  // 当前语言数据

function t(key) {
    return (I18N_DATA && I18N_DATA[key]) || key;
}

function loadLang(l, callback) {
    if (I18N_CACHE[l]) {
        I18N_DATA = I18N_CACHE[l];
        lang = l;
        if (callback) callback();
        return;
    }
    fetch('lang/' + l + '.json')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            I18N_CACHE[l] = data;
            I18N_DATA = data;
            lang = l;
            localStorage.setItem('xiaolongren_lang', l);
            if (callback) callback();
        })
        .catch(function() {
            I18N_DATA = I18N_DATA || {};
            if (callback) callback();
        });
}
```

关键设计：
- **缓存** — 切过的语言不重复fetch
- **自动检测** — `navigator.language` 决定初始语言
- **持久化** — `localStorage` 记住用户选择
- **降级** — 加载失败时key原样显示，不报错

### applyI18n刷新

切语言后遍历所有 `[data-i18n]` 元素重新赋值。动态生成的HTML（如模型列表渲染）用 `t(key)` 直接取翻译。

## 后端：按lang加载人格

### config.yaml设计

```yaml
agent:
  system_prompt: |        # 中文人格（默认）
    你是小龙人，昱成科技集团的数字生命体产品……
  en_system_prompt: |     # 英文人格
    You are XiaoLongRen, a digital lifeform……
  # fr_system_prompt: |   # 法文人格（未来加语言=加这段）
```

命名约定：`<lang>_system_prompt`。

### PSPAI后端处理

```python
lang = data.get("lang", "zh")
if lang == "en":
    system_prompt = PSPAI_EN_SYSTEM_PROMPT
else:
    system_prompt = PSPAI_SYSTEM_PROMPT
```

**不是拼接指令**（如 `[Reply in English]`），而是**直接替换整个系统提示词**。拼接会被原始人格覆盖，无效。

### 错误消息也要双语

```python
if not msg:
    reply = "请说点什么吧。" if lang != 'en' else "Please say something."
```

## 角色/动态数据翻译

角色标签等半静态数据在数据对象中加 `_en` 字段：

```javascript
var chars = [
  {name:'龙渊', tag:'龙宫少主 · 金瞳龙角', tag_en:'Dragon Prince · Golden Eyes'},
  // ...
];

// 使用时：
document.querySelector('#ntag .cd').textContent =
    lang === 'en' && c.tag_en ? c.tag_en : c.tag;
```

## 加新语言流程

1. 复制 `lang/en.json` → `lang/fr.json`，翻译所有value
2. `config.yaml` 加 `fr_system_prompt` 段落
3. 语言切换按钮加 `fr` 选项（或改为下拉菜单）
4. 重启PSPAI生效

**零代码改动**（只要切换UI能动态扩展语言列表）。

## 陷阱

- **不要在HTML里硬编码翻译** — 翻译必须独立于代码。内联I18N对象会让HTML膨胀且不可维护。
- **不要用 `[Reply in English]` 弱指令** — 必须替换整个系统提示词。弱指令会被原始人格覆盖。
- **语言包JSON不要缓存过久** — 服务器设 `Cache-Control: no-cache` 给JSON，方便调试。
- **动态HTML也要翻译** — `renderModels()` / `buildRoles()` 里手动拼接的HTML，必须用 `t()` 函数取值。
- **RTL语言预留** — 阿拉伯文等需要加 `dir="rtl"` 属性和对应的CSS，目前未实现但架构预留了扩展点。
- **浏览器语言检测fallback** — `navigator.language` 可能返回 `zh-TW` / `zh-HK`，需要 `startsWith('zh')` 判断。
