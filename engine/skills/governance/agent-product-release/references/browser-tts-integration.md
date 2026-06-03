# 浏览器内置TTS集成 (Web Speech API)

> 2026-06-01 小龙人v1.0 实战。零依赖、零后端、零API Key的语音输出方案。

## 核心代码

```javascript
var SPEAKING_EL = null;

function speak(el) {
  if (!window.speechSynthesis) return;

  // 点了正在朗读的 → 停止
  if (SPEAKING_EL === el && speechSynthesis.speaking) {
    speechSynthesis.cancel();
    el.classList.remove('speaking');
    SPEAKING_EL = null;
    return;
  }

  // 停止之前朗读
  speechSynthesis.cancel();
  if (SPEAKING_EL) SPEAKING_EL.classList.remove('speaking');

  // 获取文本
  var text = el.parentElement.textContent.replace('🔊', '').trim();
  if (!text) return;

  var u = new SpeechSynthesisUtterance(text);
  var want = lang === 'zh' ? 'zh-CN' : 'en-US';
  var voices = speechSynthesis.getVoices();
  var candidates = voices.filter(function(x) {
    return x.lang === want || x.lang.startsWith(lang);
  });

  // 优先男声
  var male = candidates.find(function(x) {
    return /male|man|boy/i.test(x.name);
  });
  u.voice = male || candidates[0];
  u.lang = want; u.rate = 1.0; u.pitch = 1.0;

  SPEAKING_EL = el;
  el.classList.add('speaking');
  u.onend = u.onerror = function() {
    el.classList.remove('speaking');
    SPEAKING_EL = null;
  };
  speechSynthesis.speak(u);
}
```

## UI集成

每条AI回复气泡后挂一个 🔊 按钮：

```html
<div class="msg-bbl">
  回复内容...
  <span class="spk-btn" onclick="speak(this)">🔊</span>
</div>
```

CSS动画：朗读中脉冲闪烁。

## 关键决策

| 决策 | 理由 |
|:---|:---|
| 用Web Speech API | 浏览器内置，不调后端，不耗token |
| 不依赖外部TTS服务 | 零API Key，离线可用 |
| 男声优先 | 用户体验更好 |
| 再点停止 | 符合直觉 |
| 跟随语言包切语音 | 中文→zh-CN，英文→en-US |

## 陷阱

- **Linux默认只有女声** — 没装男声TTS包时降级用女声，不要降pitch（会变奇怪）
- **getVoices() 异步加载** — 首次调用可能返回空数组，需要延迟获取
- **Chrome需要用户交互后播放** — 点击按钮算交互，没问题
- **长文本可能被截断** — 部分浏览器有长度限制，超长文本分段
