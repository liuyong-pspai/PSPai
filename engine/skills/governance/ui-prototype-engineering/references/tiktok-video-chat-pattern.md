# TikTok式视频聊天Demo构建模式

> 2026-06-02 小龙人视频聊天Demo实战总结

## 用途

需要快速构建一个"刷抖音式聊天"Demo时，单HTML文件即可完成——CSS动画模拟视频，预置对话数据，零后端依赖。

## 核心架构

```
单HTML文件 = 滚动容器 + 视频卡片 × N + 底部操作栏
              (scroll-snap)   (全屏卡片)    (录音/切换)
```

## 关键CSS技巧

### 1. 竖屏滑动（scroll-snap）

```css
#stream {
  flex: 1;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scroll-behavior: smooth;
  scrollbar-width: none;
}

.vcard {
  scroll-snap-align: start;
  scroll-snap-stop: always;
  height: 100%;           /* 必须 100% 才能逐卡片停下 */
  width: 100%;
}
```

### 2. CSS动画模拟"视频播放"

**呼吸感基础动画：**
```css
.char-img {
  animation: breathe 4s ease-in-out infinite;
}
@keyframes breathe {
  0%,100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}
```

**说话时加速+脉冲光：**
```css
.char-ring.speaking .char-img {
  animation: speaking 0.4s ease-in-out infinite;
}
@keyframes speaking {
  0%,100% { transform: scale(1); }
  25% { transform: scale(1.04); }
  75% { transform: scale(0.98); }
}

.char-ring.speaking {
  animation: ringpulse 0.6s ease-in-out infinite;
}
@keyframes ringpulse {
  0%,100% { box-shadow: 0 0 15px var(--gold-dim); }
  50% { box-shadow: 0 0 45px var(--gold), 0 0 80px var(--gold-dim); }
}
```

### 3. 粒子漂浮背景

```javascript
// 每个卡片生成20个随机粒子
for (let i = 0; i < 20; i++) {
  const el = document.createElement('div');
  el.className = 'particle';
  el.style.cssText = `
    left: ${Math.random()*100}%;
    bottom: ${Math.random()*100}%;
    width: ${1+Math.random()*3}px;
    height: ${1+Math.random()*3}px;
    background: rgba(200,168,78,${0.3+Math.random()*0.5});
    animation-duration: ${4+Math.random()*10}s;
    animation-delay: ${Math.random()*5}s;
  `;
  card.appendChild(el);
}
```

### 4. 录音按钮动画

```css
#record-btn.recording {
  animation: recpulse 1s ease-in-out infinite;
}
@keyframes recpulse {
  0%,100% { box-shadow: 0 0 25px var(--gold-dim); }
  50% { box-shadow: 0 0 55px var(--gold), 0 0 90px var(--gold-dim); }
}
```

## JS交互逻辑

### 滚动监听（IntersectionObserver）

```javascript
const obs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const idx = parseInt(e.target.id.replace('vcard-', ''));
      curMsgIdx = idx;
      updateDots(idx);  // 更新右侧圆点
      // AI消息：触发说话动画
      if (MESSAGES[idx].from === 'ai') {
        document.getElementById('ring-' + idx).classList.add('speaking');
      }
    } else {
      // 滑走：停止说话动画
      const idx = parseInt(e.target.id.replace('vcard-', ''));
      const ring = document.getElementById('ring-' + idx);
      if (ring) ring.classList.remove('speaking');
    }
  });
}, { threshold: 0.6 });  // 60%露出即触发

document.querySelectorAll('.vcard').forEach(c => obs.observe(c));
```

### 模拟新消息

```javascript
function stopRecord() {
  btn.classList.remove('recording');
  // 随机选一条AI回复
  const replies = [
    { from: 'ai', text: '收到！<span class="highlight">我已明白</span>～', char: curChar },
    { from: 'ai', text: '嗯嗯，记下来了📝', char: (curChar+2) % 6 },
  ];
  const m = replies[Math.floor(Math.random() * replies.length)];
  MESSAGES.push(m);
  // 动态构建卡片 → appendChild → scrollIntoView
}
```

## 消息卡片结构

```html
<div class="vcard">
  <!-- 渐变背景（每角色不同） -->
  <div class="bg g1"></div>
  <!-- 漂浮粒子 -->
  <div class="particles"></div>
  <!-- 角色区（居中） -->
  <div class="char-zone">
    <div class="char-ring" id="ring-N">
      <img class="char-img" src="角色头像.jpg">
    </div>
    <div class="char-name">角色名</div>
    <div class="char-tag">标签</div>
  </div>
  <!-- 消息字幕（底部） -->
  <div class="vtext">
    <div class="msg-txt">消息内容</div>
    <div class="msg-time">10:23</div>
  </div>
  <!-- 操作按钮（右侧，抖音式） -->
  <div class="actions">
    <div class="act">❤️ 点赞</div>
    <div class="act">💬 回复</div>
    <div class="act">↗️ 分享</div>
  </div>
</div>
```

## 角色数据规范

```javascript
const CHARS = [
  {
    id: 'longyuan',
    name: '龙渊',
    tag: '小龙人AI',
    img: 'img_longyuan.jpg',
    gradient: 'g1'  // 对应CSS背景class
  },
  // ... 6个角色，每个有独立渐变背景色
];
```

## 对话数据规范

```javascript
const MESSAGES = [
  { from: 'user', text: '用户说的话', time: '10:23' },
  { from: 'ai', text: 'AI回复（支持<span class="highlight">高亮</span>）', time: '10:24', char: 0 },
  // char: 0 = 使用 CHARS[0] 的角色形象
];
```

## 部署

静态HTTP服务器即可，零后端：

```bash
python3 server.py  # SimpleHTTPRequestHandler + ThreadingMixIn
# 浏览器打开 http://IP:8088/video-chat.html
```

## 已验证效果

- 6角色切换（底部左右箭头）
- 竖屏滑动逐卡片停靠
- 角色"说话"动画（滑到该卡片自动触发）
- 粒子漂浮（金色光点）
- 右侧圆点进度指示器
- 长按录音模拟发送
- 点赞动画（红心切换+数字跳动）
- 手机端适配（safe-area-inset + 触摸优化）
- 宽屏居中限制（max-width:430px）
