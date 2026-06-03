---
name: multi-language-i18n-architecture
description: >
  产品多语言国际化完整架构——前端JSON语言包+后端字典查找，零代码加语言。
  触发：产品需要多语言支持、国际化/i18n、翻译系统、语言切换。
version: 1.0.0
last_updated: 2026-06-01
---

# 多语言国际化架构

## 设计原则

**加一种新语言=加配置，不动代码。** 前端加JSON文件，后端加配置段和字典条目。零 if/else 分支。

## 架构三层

### 第一层：前端 — JSON语言包 + 异步加载

```
UI原型/lang/
  zh.json   ← 中文
  en.json   ← 英文
  fr.json   ← 法文（未来加）
```

每个JSON文件是平铺的key-value对，79个key覆盖界面全部文本：

```json
{
  "memo": "备忘",
  "chat_ph": "跟小龙人说点什么…",
  "close": "关闭",
  ...
}
```

HTML中通过`data-i18n`、`data-i18n-ph`、`data-i18n-title`属性标记需要翻译的元素：

```html
<button data-i18n="close">关闭</button>
<input data-i18n-ph="chat_ph">
<div data-i18n-title="rename_hint">
```

JavaScript异步加载语言包（带缓存，切换不重复请求）：

```javascript
var I18N_CACHE = {};
var I18N_DATA = null;

function loadLang(l, callback) {
    if (I18N_CACHE[l]) { I18N_DATA = I18N_CACHE[l]; callback(); return; }
    fetch('lang/' + l + '.json')
        .then(r => r.json())
        .then(data => {
            I18N_CACHE[l] = data;
            I18N_DATA = data;
            callback();
        });
}

function t(key) { return (I18N_DATA && I18N_DATA[key]) || key; }

function applyI18n() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.getAttribute('data-i18n'));
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        el.placeholder = t(el.getAttribute('data-i18n-ph'));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        el.title = t(el.getAttribute('data-i18n-title'));
    });
}
```

语言切换按钮用`toggleLang()`触发，`lang`存储到localStorage。

### 第二层：配置 — 多语言人格

`config.yaml` 使用统一命名约定 `system_prompt_<lang>`：

```yaml
agent:
  system_prompt_zh: |
    你是小龙人，基于PSPAI架构的数字生命体...
  system_prompt_en: |
    You are XiaoLongRen, a digital lifeform based on PSPAI architecture...
  system_prompt_fr: |
    Vous êtes XiaoLongRen...  ← 未来加
```

### 第三层：后端 — 字典查找，无if/else

```python
# 自动扫描所有 system_prompt_* 配置
PSPAI_PROMPTS = {}
for key in AGENT_CFG:
    if key.startswith('system_prompt_'):
        lang_code = key.replace('system_prompt_', '')
        PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]

# 运行时一行查找
system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)
```

消息文本也走字典：

```python
PSPAI_MSGS = {
    'zh': {'empty': '请说点什么吧。', 'thinking': '（思考中，请稍后再试）', 'error': '抱歉，出了点问题'},
    'en': {'empty': 'Please say something.', 'thinking': '(Thinking...)', 'error': 'Sorry'},
}
reply = t_msg(lang, 'empty')
```

## 加新语言步骤（以法语为例）

1. **前端** — 复制 `lang/en.json` → `lang/fr.json`，翻译79个value
2. **配置** — `config.yaml` 加 `system_prompt_fr` 段
3. **后端** — `PSPAI_MSGS` 字典加一行 `'fr': {'empty':'...', 'thinking':'...', 'error':'...'}`
4. **语言切换** — 前端 `toggleLang()` 支持fr即可（改`langBtn`逻辑让用户选语言而非仅中英切换）

✅ 完成。HTML和核心代码零改动。

## 注意事项

- **JSON文件避免嵌套** — 平铺key最方便`t(key)`查找
- **语言包随产品发布** — 放在静态资源目录，fetch走相对路径
- **浏览器缓存** — JSON文件设置`Cache-Control: no-cache`方便调试，生产环境可加hash
- **RTL语言** — 阿拉伯文等需要额外处理CSS方向（`dir="rtl"`），本架构预留但未实现
- **图片资源** — 如果UI包含文字图片（如按钮背景），需要按语言准备多套图

## 避免的模式

❌ 在HTML里硬编码翻译（内联I18N对象）
❌ 后端用 if lang=='en' elif lang=='fr' 分支
❌ 每种语言打包一个独立安装包
❌ 系统提示词用拼接方式注入语言指令
