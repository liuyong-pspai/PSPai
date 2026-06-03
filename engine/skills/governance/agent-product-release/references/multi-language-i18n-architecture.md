# 多语言包架构 (i18n Architecture)

> 2026-06-01 小龙人v1.0 实战沉淀。从HTML内联翻译→独立JSON文件→动态语言索引的完整演进。

## 架构设计

```
UI原型/
  lang/
    index.json    ← 语言索引（定义有哪些语言）
    zh.json       ← 中文翻译包（79 keys）
    en.json       ← 英文翻译包（79 keys）
    fr.json       ← 法语（加语言=加这个文件）
```

**三层分离**：
1. **语言索引** (`index.json`): `{"zh":{"name":"中文","native":"中"},"en":{...}}` — UI启动时读取，动态生成语言切换按钮
2. **翻译包** (`xx.json`): 纯key-value，如 `{"memo":"备忘","chat_ph":"跟小龙人说点什么…"}`
3. **代码层**: `data-i18n="key"` 属性标记 + `t(key)` 函数查找 + `applyI18n()` 批量刷新

## 前端加载流程

```
页面启动
  → fetch('lang/index.json')   // 读语言索引
  → 检测: localStorage → 浏览器语言 → 默认第一个
  → fetch('lang/'+lang+'.json')  // 加载翻译包
  → applyI18n()                  // 刷新所有 [data-i18n] 元素
  → 缓存到 I18N_CACHE            // 切语言秒切
```

## 前端关键代码

```javascript
// 动态切换（不写死中/英）
function toggleLang() {
    var idx = LANG_ORDER.indexOf(lang);
    var next = LANG_ORDER[(idx + 1) % LANG_ORDER.length];
    loadLang(next, applyI18n);
}

// 刷新全部界面
function applyI18n() {
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
        el.textContent = t(el.getAttribute('data-i18n'));
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(function(el) {
        el.placeholder = t(el.getAttribute('data-i18n-ph'));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(function(el) {
        el.title = t(el.getAttribute('data-i18n-title'));
    });
    // 刷新动态面板
    if (curPanel === 'model') renderModels();
    if (curPanel === 'role') buildRoles();
}
```

## 后端多人格

`config.yaml` 按语言配置完整系统提示词：

```yaml
agent:
  system_prompt_zh: |
    你是小龙人，基于PSPAI架构的数字生命体...
  system_prompt_en: |
    You are XiaoLongRen, a digital lifeform based on PSPAI...
  system_prompt_fr: |
    ...（加语言=加这一段）
```

PSPAI后端自动扫描 `system_prompt_*` 键，构建字典：

```python
PSPAI_PROMPTS = {}
for key in AGENT_CFG:
    if key.startswith('system_prompt_'):
        lang_code = key.replace('system_prompt_', '')
        PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]

# 使用: system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)
```

## 加新语言步骤

1. `lang/fr.json` — 复制en.json，翻译79个value
2. `lang/index.json` — 加一行 `"fr":{"name":"Français","native":"FR"}`
3. `config.yaml` — 加 `system_prompt_fr` 段（法文人格）
4. 多语言消息字典加一行（可选）: `'fr':{'empty':'...','thinking':'...','error':'...'}`
5. 完成。HTML零改动，UI自动多一个 🇫🇷 FR 选项。

## 陷阱

- **不要内联翻译到HTML** — 代码和翻译耦合，加语言要改代码
- **不要写死切换逻辑** (`lang==='zh'?'en':'zh'`) — 用 `index.json` 动态读取
- **按钮文字跟着变** — `applyI18n()` 里要更新 `.lang-btn span` 文本
- **浏览器语言检测** — 用 `navigator.language` 自动选默认语言
- **JSON文件必须和HTML同源** — 用相对路径 `fetch('lang/'+l+'.json')`，不能用绝对路径
