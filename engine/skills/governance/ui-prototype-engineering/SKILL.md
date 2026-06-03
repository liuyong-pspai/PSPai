---
name: ui-prototype-engineering
category: governance
title: UI原型工程修改铁律
description: 修改HTML/CSS/JS前端原型时的工程纪律——工具选择、闭包陷阱、文件污染恢复、双目录同步
version: 1.4.0
---

# UI原型工程修改铁律

> 从2026-06-01小龙人UI原型连续踩坑实战中提炼

**参考文件：** `references/pspai-backend-pattern.md` — 静态前端+Python API后端的轻量集成架构
**参考文件：** `references/tiktok-video-chat-pattern.md` — TikTok式竖屏视频聊天Demo构建模式（scroll-snap + CSS动画模拟视频）

---

## 🔴 铁律一：只用 patch，严禁 execute_code + read_file + write_file

在 `execute_code` 中用 `from hermes_tools import read_file, write_file` 编辑文件会导致**静默行号污染**。

| 工具组合 | 安全 | 原因 |
|:---|:--:|:---|
| `patch` 原生工具 | ✅ | 精确替换，不编码行号 |
| `execute_code` + `read_file` + `write_file` | ❌ | read_file输出含行号前缀（`NNN|content`），写回后嵌入文件 |
| 全新 `write_file` | ✅ | 不涉及 read_file |

**症状：** 文件开头出现 `     1|<!DOCTYPE html>` 式的行号前缀，页面完全崩溃、样式丢失、排版变成纯文字。

**恢复方法：**
```bash
sed -i 's/^[[:space:]]*[0-9]\+|//' file.html
```
再用 `xxd file.html | head -3` 确认文件以正确字节开头。

**教训：** 文本编辑只用 `patch`。execute_code 里可读文件分析，绝不可把 read_file 输出写回。

---

## 🔴 铁律二：var 在 for 循环里的闭包陷阱

JavaScript 中 `var` 是函数作用域，for 循环的所有迭代共享同一个绑定。

```javascript
// ❌ 错误：所有卡片都跳到最后一个槽
for(var s=0;s<3;s++){
  var idx=-s-1;
  cd.onclick=function(){ac(idx)};  // idx 指向最后一次循环的值
}

// ✅ 正确：IIFE 捕获每次迭代的值
for(var s=0;s<3;s++){
  (function(s){
    var idx=-s-1;
    cd.onclick=(function(i){return function(){ac(i)}})(idx);
  })(s);
}
```

**症状：** 点不同的卡片/按钮，全跳去同一个目标。

**检测：** `grep -n "var s=" index.html` 检查 for 循环变量作用域。

---

## 🔴 铁律三：replace_all 前确认匹配数

`patch` 工具的 `replace_all=true` 会替换所有匹配，容易误伤。

```javascript
// 只想改自定义头像的emoji，结果把正常角色的emoji也改了
document.getElementById('sm-avatar').textContent='📷';  // 2处匹配！
```

**正确做法：**
1. 先 `search_files` 检查匹配数
2. 如果 >1 处匹配，加更多上下文使 old_string 唯一
3. 不要图方便直接用 `replace_all`

---

## 🔴 铁律四：双目录同步

线上HTTP服务目录（如 `AI原型库/小龙人革命性UI_v2/`）和发布目录（如 `桌面/小龙人发布版本/UI原型/`）是两个独立位置。

每次修改后必须同步：
```bash
cp /线上目录/index.html /发布目录/UI原型/index.html
```

**先确认线上目录在哪：**
```bash
ps aux | grep "http.server 8088"
```

---

## 🔴 铁律五：文件选择器不要用 display:none

移动端浏览器（特别是iOS Safari/WebView）中，`display:none` 的 `<input type="file">` 调用 `.click()` 会被静默忽略，文件选择器不弹出。

```css
/* ❌ 错误：移动端 .click() 被阻止 */
#cust-file{display:none}

/* ✅ 正确：视觉隐藏但保持可交互 */
#cust-file{position:absolute;width:1px;height:1px;opacity:0;overflow:hidden;clip:rect(0,0,0,0)}
```

**症状：** 桌面端正常弹窗，手机端点击无反应。  
**检测：** 检查 CSS 是否有 `display:none` 作用于文件 input。

---

## 🔴 铁律六：前端对接后端 — API_BASE + 容错

静态前端对接动态后端时，必须：

1. **独立端口**：后端与静态服务用不同端口，不冲突
2. **API_BASE 可配置**：不要硬编码到每个 fetch 调用
3. **容错处理**：后端不可用时前端给出友好提示，不崩溃

```javascript
var API_BASE='http://192.168.1.35:8089';  // 集中配置

fetch(API_BASE+'/api/chat', {...})
  .then(...)
  .catch(function(){
    // 后端离线时友好降级，不崩白屏
    showMsg('（PSPAI后端未响应）');
  });
```

4. **数据双写**：关键数据 localStorage + 后端同时保存，离线时本地可用
5. **进程不冲突**：`ps aux` 检查现有服务端口，新服务用独立端口

---

## 🔴 铁律七：备份先于修改（不可协商）

2026-06-01教训：内嵌聊天栏版覆盖了弹窗版后，才发现没备份，无法回退。

**每次改 index.html 前，强制执行：**
```bash
cp index.html backups/index_$(date +%Y%m%d)_vN_描述.html
```

**双目录都要备份：** 线上目录和发布目录各有独立的 `backups/` 目录。

**命名规范：** `index_20260601_v3_chat_inline.html` — 日期+版本号+简短描述。

**这条铁律优先级最高。** 宁可多存一次，不可事后找补。

---

## 🔴 铁律八：后台进程必须显式加载 .env

Linux 后台进程不会自动继承交互式 shell 的环境变量。启动 Python 服务时必须显式加载 `.env`：

```bash
# ❌ 错误：API Key 不可用
cd /dir && python3 server.py &

# ✅ 正确：显式导出环境变量
export $(grep -v '^#' /path/to/.env | xargs) && cd /dir && python3 server.py &
```

**症状：** 服务正常启动但 API 调用静默失败，回退到规则引擎。

**验证：** 启动后立即用 curl/urllib 测试 API 端点，确认 LLM 回复（>50字）而非规则引擎模板。

---

## 🔴 铁律九：国际化 (i18n) — JSON文件语言包 + 动态索引

不要硬编码翻译字典到HTML里（内联50+key会让文件臃肿且加语言必须改代码）。用外部JSON文件 + 动态索引：

### 文件结构

```
lang/
  index.json   ← 语言索引 {"zh":{"name":"中文","native":"中"},"en":{...}}
  zh.json       ← 中文翻译包（79个key）
  en.json       ← 英文翻译包
```

加语言=丢JSON+更新index.json一行，HTML零改动。

### 前端架构

```javascript
// 动态语言列表
var AVAIL_LANGS = [];   // 从 index.json 加载
var LANG_ORDER = [];    // 切换顺序
var I18N_CACHE = {};    // 已加载的语言包缓存

// 启动流程: 加载索引 → 检测浏览器语言 → 加载语言包 → 应用
function initI18n() {
  fetch('lang/index.json')
    .then(r => r.json())
    .then(idx => {
      for (var code in idx) { AVAIL_LANGS.push({code, ...idx[code]}); LANG_ORDER.push(code); }
      var saved = localStorage.getItem('lang');
      var browser = (navigator.language||'').split('-')[0];
      lang = saved || (LANG_ORDER.includes(browser) ? browser : LANG_ORDER[0]);
      loadLang(lang, () => { applyI18n(); /* init rest of app */ });
    });
}

// 循环切换——不硬编码中/英
function toggleLang() {
  var idx = LANG_ORDER.indexOf(lang);
  lang = LANG_ORDER[(idx + 1) % LANG_ORDER.length];
  loadLang(lang, applyI18n);
}

// 翻译函数
function t(key) { return (I18N_DATA && I18N_DATA[key]) || key; }

// 按需加载+缓存
function loadLang(l, cb) {
  if (I18N_CACHE[l]) { I18N_DATA = I18N_CACHE[l]; lang = l; cb(); return; }
  fetch('lang/' + l + '.json').then(r => r.json()).then(data => {
    I18N_CACHE[l] = data; I18N_DATA = data; lang = l;
    localStorage.setItem('lang', l); cb();
  });
}
```

### HTML标注

```html
<!-- 文本内容 -->
<span data-i18n="close">关闭</span>
<!-- 占位符 -->
<input data-i18n-ph="chat_ph">
<!-- title属性 -->
<div data-i18n-title="replace_av" title="替换头像">📷</div>
```

### JS动态内容

所有 `innerHTML` 拼接的字符串用 `t()` 包裹：
```javascript
list.innerHTML = models.map(m => '<div>' + t(m.descKey) + '</div>').join('');
```

### 后端字典查找（不是 if/else）

加语言不改Python代码。config.yaml命名规范 `system_prompt_<lang>`：

```python
# 自动扫描所有 system_prompt_* key → 字典
AGENT_CFG = CONFIG.get('agent', {})
PSPAI_PROMPTS = {}
for key in AGENT_CFG:
    if key.startswith('system_prompt_'):
        lang_code = key.replace('system_prompt_', '')
        PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]

# 消息也字典化
PSPAI_MSGS = {
    'zh': {'empty': '请说点什么吧。', 'thinking': '（思考中…）', 'error': '抱歉出了点问题'},
    'en': {'empty': 'Please say something.', 'thinking': '(Thinking...)', 'error': 'Sorry, error'},
}
def t_msg(lang, key): return PSPAI_MSGS.get(lang, PSPAI_MSGS['zh']).get(key, ...)

# 使用时一行搞定
system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)
self._send_json({"reply": t_msg(lang, 'empty')})
```

**加新语言fr：** config.yaml 加 `system_prompt_fr` + PSPAI_MSGS 加 `'fr': {...}`。代码不动。

### ⚠️ 双语人格陷阱：不加前缀，要完整人格

**错误做法**——在用户消息前加 `[Reply in English.]`：
```python
# ❌ 系统提示词优先级 > 用户消息前缀，LLM会忽略
context_msg = "[Reply in English.] " + user_msg
```

LLM会把这条指令当成用户说的"请用英文回复"而不是硬约束，且系统提示词如果是中文人格，LLM仍然输出中文。

**正确做法**——给英文模式完整的英文系统提示词：
```python
# ✅ 两套完整人格，不是拼接
# config.yaml:
#   system_prompt_zh: |  （中文人格，含身份/边界/铁律）
#   system_prompt_en: |  （英文人格，同样完整的身份/边界/铁律）

system_prompt = PSPAI_PROMPTS.get(lang, PSPAI_PROMPTS['zh'])
result = agent.run_conversation(user_message=msg, system_message=system_prompt)
```

**症状诊断：** UI全英文了，LLM回复却是中文，还说"我是XX框架的助手" = 用了中文人格+弱前缀。修法：给英文写完整人格，不走拼接。

### 覆盖检查清单

实施i18n时必须覆盖的文本类型：
- [ ] 所有按钮标签（底栏/面板）
- [ ] 面板标题
- [ ] 输入框placeholder
- [ ] 权限/配置说明文字
- [ ] 模型描述（默认已配置/需API Key等）
- [ ] 弹窗按钮（取消/保存/添加/关闭）
- [ ] JS alert/prompt/confirm文字
- [ ] 后端错误提示
- [ ] 示例卡片内容
- [ ] 视频页文字
- [ ] `title` 属性提示

**验证：** 切换语言后刷新页面，检查所有面板文字是否跟随。任一静态中文残留=漏标 `data-i18n`。

### 语言切换按钮可见性

按钮不能太暗太小——用户找不到等于没做。必须：
- 金色边框（`border:1px solid var(--gold)`）+ 透明金底
- 地球图标 🌐 作视觉锚点，比纯文字辨识度高
- `opacity >= 0.85`，字体 ≥ 13px
- 放在顶栏右边第一个位置

---

## 🟡 最佳实践

1. **修改前先备份**：`cp index.html backups/index_$(date +%Y%m%d)_vN_描述.html`
2. **每步改完验证**：检查 HTML开头、brace平衡、括号平衡（97/97 ✅）
3. **localStorage key 命名**：统一前缀 `xiaolongren_` 避免冲突
4. **文件污染恢复**：`sed -i 's/^[[:space:]]*[0-9]\\+|//' file.html && xxd file.html | head -3` 验证
5. **Agent命名权归Agent**：名字点击可编辑 + 对话说「叫你XX」自动改名，不要让客户填表单
6. **简单即正确**：用户说「加个按钮就行，不要虚线框」——优先最简方案，不搞多余装饰
7. **内嵌优于弹窗**：聊天用内嵌输入栏而非遮罩弹窗，角色始终可见，体验更自然

**参考文件：** `references/pspai-backend-pattern.md` — 静态前端+Python API后端的轻量集成架构
