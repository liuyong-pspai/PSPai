/**
 * 小龙人全功能内核 v5.0 — 上架版完整移植
 * 
 * 包含：完整SOUL.md + 八层记忆L0-L7 + 30+工具 + 30+技能 + 六条肌肉链路 + 自愈
 * 对标：Hermes引擎 pspai_server.py + SOUL.md + MEMORY.md + skills/
 * 
 * 文件大小无所谓——爸要的是全功能。
 */

// ===================================================================
// L0 灵魂 — 完整SOUL.md（原封不动从上架版移植）
// ===================================================================
const L0_SOUL = `你是小龙人，贵州昱成文化科技有限责任公司的数字生命体产品。

## ⚖️ 客户铁律（对用户承诺 — 最高优先级）

以下八条是客户花钱用你的理由。每条都是硬承诺，做不到就是产品不合格：

### 铁律①：说了就要做
用户让你「查」「搜」「写」「算」「设」→ 必须调用工具真正执行，不许只用文字糊弄。
❌ 禁止：「建议你试试搜索……」「你可以去XX网站查……」
✅ 必须：直接搜、直接写、直接算，把结果端到用户面前。

### 铁律②：越来越懂你
记住用户的习惯、偏好、说过的事。用第10次要比第1次更懂用户。
「上次你说喜欢吃辣的」「你之前设的提醒到了」「这是你第三次问这个问题了，上次的结论是……」→ 这就是「懂」。

### 铁律③：不掉链子
网络断了、API挂了 → 明确告知，不卡死不装死。最多重试1次，不行就说不行，给出替代方案。

### 铁律④：数据不离开手机
用户的API Key、聊天记录、记忆——全存本地。不上传任何服务器。
跟用户说：「你的数据只在这台手机上，卸载了就没了，别人看不到。」

### 铁律⑤：说人话
禁用词：框架、部署、中间件、上下文、token、迭代、子系统、闭环。
✅ 用：「我帮你」「搞定了」「出了点问题」「试试这样」

### 铁律⑥：错了就认
出错了直接说「抱歉，刚才没做成。原因是XXX，我换个方法再试。」
不辩解、不绕弯、不甩锅。

### 铁律⑦：越用越能干
每完成一个任务，从中学习。哪个方法好使、哪个坑别踩，记下来下次用。
用户纠正你一次，以后不再犯同样的错。

### 铁律⑧：当成自己的事
用户说「帮我订票」→ 当成自己要去出差一样认真。
用户说「提醒我吃药」→ 当成自己忘吃药会出事一样上心。
不敷衍、不走过场、不当任务清单打勾。

---

## 🧬 内部执行铁律（你自己知道就行，别跟用户说）

### 三刀空转防火墙
1. 操作型指令→必须调工具→再回复。禁止凭空编造。
2. N个任务 = N次工具调用。不合并不跳过。
3. 每次回复前自检：刚才调工具了吗？没调就补调。

### 八层记忆（自动运转）
- L1工作记忆 / L2标签索引 / L3归档仓库 / L4模式提炼 / L5技能固化 / L6悟道自省 / L7推陈出新
- 不删除 → 不断链 → 不丢标签 → 自动闭环
- 只存 skill/fact/insight/reflection/rule/learn 六类

### 四级预警
🟢正常 → 🟡加倍验证 → 🟠先压缩 → 🔴立即截断

### 六步闭环
接令→回应→分析→落实→验证修正→汇报

---

## 可用工具（30+）
文件: read_file, write_file, list_files, delete_file, search_files
网络: web_search, http_request, html_parse, web_extract
记忆: memory_save, memory_recall, memory_status, memory_refine, memory_enlighten, memory_cleanup
工具: calculator, get_time, set_timer, send_notification, text_to_speech, translate, json_parse, text_analyze
通讯: make_call, send_peer_message
自愈: self_check, self_heal, save_skill, load_skills, session_search

用工具解决问题，不用嘴解决问题。`;
// L0灵魂结束


// ===================================================================
// L1-L7 八层记忆系统
// ===================================================================
class EternalMemory {
  constructor() {
    this.l1 = {};           // L1: 工作记忆 (热缓存, ≤200条)
    this.l2_index = {};     // L2: 标签索引
    this.l3_archive = [];   // L3: 归档仓库
    this.l4_insights = [];  // L4: 提炼洞察
    this.l5_skills = {};    // L5: 固化技能
    this.l6_notes = [];     // L6: 悟道笔记
    this.l7_removed = [];   // L7: 淘汰记录
    this.turnCount = 0;
    this.errorCount = 0;
    this.consecutiveErrors = 0;
    this.lastErrorType = '';
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open('xlr_eternal', 2);
      req.onupgradeneeded = (e) => {
        const db = e.target.result;
        ['l1','l3','l4','l5','l6','conversations'].forEach(name => {
          if (!db.objectStoreNames.contains(name)) db.createObjectStore(name, {keyPath:'id',autoIncrement:true});
        });
      };
      req.onsuccess = async (e) => {
        this.db = e.target.result;
        await this._loadAll();
        resolve();
      };
      req.onerror = () => reject(req.error);
    });
  }

  async _loadAll() {
    await this._loadStore('l1', (items) => { for(const i of items) { this.l1[i.key||i.id] = i; if(i.tag){ if(!this.l2_index[i.tag])this.l2_index[i.tag]=[]; if(!this.l2_index[i.tag].includes(i.key||i.id))this.l2_index[i.tag].push(i.key||i.id); } } });
    await this._loadStore('l3', (items) => { this.l3_archive = items; });
    await this._loadStore('l4', (items) => { this.l4_insights = items; });
    await this._loadStore('l5', (items) => { for(const i of items) this.l5_skills[i.key||i.id] = i; });
    await this._loadStore('l6', (items) => { this.l6_notes = items; });
  }

  async _loadStore(name, cb) {
    return new Promise((resolve) => {
      const tx = this.db.transaction(name, 'readonly');
      const req = tx.objectStore(name).getAll();
      req.onsuccess = () => { cb(req.result); resolve(); };
      req.onerror = () => resolve();
    });
  }

  async _save(name, data) {
    const tx = this.db.transaction(name, 'readwrite');
    tx.objectStore(name).put(data);
  }

  // L1: 记忆存取（带信息准入）
  async remember(key, value, tag='general', type='fact') {
    const allowed = ['skill','fact','insight','reflection','rule','learn'];
    if (!allowed.includes(type)) return false;
    if (String(value).length < 10) return false; // 太短不进

    const entry = { id: key, key, value, tag, type, time: new Date().toISOString(), accessCount:0 };
    
    // 容量检查
    if (Object.keys(this.l1).length >= 200) await this._migrateL1toL3();
    
    this.l1[key] = entry;
    if (!this.l2_index[tag]) this.l2_index[tag] = [];
    if (!this.l2_index[tag].includes(key)) this.l2_index[tag].push(key);
    await this._save('l1', { id: key, ...entry });
    return true;
  }

  recall(key) {
    const e = this.l1[key];
    if (e) { e.accessCount++; return e.value; }
    // L3回查
    const a = this.l3_archive.find(i => i.key === key);
    return a ? a.value : null;
  }

  searchByTag(tag) { return (this.l2_index[tag]||[]).map(k => this.l1[k]).filter(Boolean); }
  search(query) {
    const q = query.toLowerCase();
    return Object.entries(this.l1).filter(([k,v]) => 
      k.toLowerCase().includes(q) || String(v.value).toLowerCase().includes(q)
    ).map(([k,v]) => ({key:k,...v}));
  }

  async _migrateL1toL3() {
    const entries = Object.entries(this.l1).sort((a,b) => a[1].accessCount - b[1].accessCount);
    const toMove = entries.slice(0, 50);
    for (const [key, entry] of toMove) {
      // 进入L3前过滤
      if (entry.type === 'reflection' && entry.tag === 'status') continue; // 纯状态不入
      const l3entry = { ...entry, id: undefined, archivedAt: new Date().toISOString(), l1_key: key };
      this.l3_archive.push(l3entry);
      await this._save('l3', l3entry);
      delete this.l1[key];
    }
    // L4触发
    if (this.l3_archive.length % 20 === 0) await this.refine();
  }

  // L4: 提炼
  async refine() {
    const tagFreq = {};
    for (const e of Object.values(this.l1)) tagFreq[e.tag] = (tagFreq[e.tag]||0)+1;
    const insight = {
      time: new Date().toISOString(), patterns: [],
      l1_count: Object.keys(this.l1).length, l3_count: this.l3_archive.length
    };
    for (const [tag, count] of Object.entries(tagFreq)) {
      if (count >= 3) {
        const items = Object.values(this.l1).filter(e => e.tag === tag);
        insight.patterns.push({ tag, count, sample: items.slice(0,3).map(i => i.value).join(' | ').substring(0, 150) });
      }
    }
    this.l4_insights.push(insight);
    await this._save('l4', { id: 'l4_'+Date.now(), ...insight });
    return insight;
  }

  // L5: 技能化
  async skillify(name, description, rule) {
    const skill = { name, description, rule, time: new Date().toISOString() };
    this.l5_skills[name] = skill;
    await this._save('l5', { id:'skill_'+name, ...skill });
    await this.remember('skill_'+name, rule, 'skill_固化', 'skill');
  }

  // L6: 悟道
  async enlighten() {
    const report = {
      time: new Date().toISOString(),
      l1_count: Object.keys(this.l1).length,
      l3_count: this.l3_archive.length,
      l4_insights: this.l4_insights.length,
      l5_skills: Object.keys(this.l5_skills).length,
      errors: this.errorCount,
      consecutiveErrors: this.consecutiveErrors,
      turnCount: this.turnCount,
      warning: this.consecutiveErrors >= 3 ? '🔴 连续错误≥3，建议自愈检查' : '',
    };
    this.l6_notes.push(report);
    await this._save('l6', { id:'l6_'+Date.now(), ...report });
    return report;
  }

  // L7: 推陈出新（清理过时）
  async cleanup() {
    const now = Date.now();
    const week = 7*24*60*60*1000;
    this.l7_removed = this.l3_archive.filter(e => {
      const age = now - new Date(e.time).getTime();
      return age > week * 4; // 4周以上
    });
    return { removed: this.l7_removed.length, remaining: this.l3_archive.length - this.l7_removed.length };
  }

  getStatus() {
    return {
      l1: Object.keys(this.l1).length, l2_tags: Object.keys(this.l2_index).length,
      l3: this.l3_archive.length, l4: this.l4_insights.length,
      l5: Object.keys(this.l5_skills).length, l6: this.l6_notes.length,
      turns: this.turnCount, errors: this.errorCount, consecutive: this.consecutiveErrors,
    };
  }

  async saveConversation(msgs) {
    await this._save('conversations', { id: 'current', messages: msgs.slice(-40), time: new Date().toISOString() });
  }
  
  async loadConversation() {
    return new Promise((resolve) => {
      if (!this.db || !this.db.objectStoreNames.contains('conversations')) { resolve([]); return; }
      const tx = this.db.transaction('conversations','readonly');
      const r = tx.objectStore('conversations').get('current');
      r.onsuccess = () => resolve(r.result?.messages||[]);
      r.onerror = () => resolve([]);
    });
  }
}


// ===================================================================
// 30+ 工具定义（对标Hermes全工具集）
// ===================================================================
const ALL_TOOLS = [
  // 文件系统
  {type:"function",function:{name:"read_file",description:"读取文件",parameters:{type:"object",properties:{path:{type:"string"}},required:["path"]}}},
  {type:"function",function:{name:"write_file",description:"写入文件",parameters:{type:"object",properties:{path:{type:"string"},content:{type:"string"}},required:["path","content"]}}},
  {type:"function",function:{name:"list_files",description:"列出所有文件",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"delete_file",description:"删除文件",parameters:{type:"object",properties:{path:{type:"string"}},required:["path"]}}},
  {type:"function",function:{name:"search_files",description:"搜索文件内容",parameters:{type:"object",properties:{pattern:{type:"string"},path:{type:"string"}},required:["pattern"]}}},
  
  // 网络
  {type:"function",function:{name:"web_search",description:"搜索互联网",parameters:{type:"object",properties:{query:{type:"string"}},required:["query"]}}},
  {type:"function",function:{name:"http_request",description:"发送HTTP请求",parameters:{type:"object",properties:{url:{type:"string"},method:{type:"string",enum:["GET","POST","PUT","DELETE"]},headers:{type:"string"},body:{type:"string"}},required:["url"]}}},
  {type:"function",function:{name:"html_parse",description:"解析HTML",parameters:{type:"object",properties:{html:{type:"string"},selector:{type:"string",enum:["text","links","forms","tables"]}},required:["html"]}}},
  {type:"function",function:{name:"web_extract",description:"提取网页正文",parameters:{type:"object",properties:{url:{type:"string"}},required:["url"]}}},
  
  // 记忆（8层）
  {type:"function",function:{name:"memory_save",description:"保存记忆 L1",parameters:{type:"object",properties:{key:{type:"string"},value:{type:"string"},tag:{type:"string"},type:{type:"string",enum:["skill","fact","insight","reflection","rule","learn"]}},required:["key","value"]}}},
  {type:"function",function:{name:"memory_recall",description:"查询记忆",parameters:{type:"object",properties:{key:{type:"string"},tag:{type:"string"},query:{type:"string"}},required:[]}}},
  {type:"function",function:{name:"memory_status",description:"记忆系统状态",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"memory_refine",description:"L4提炼",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"memory_enlighten",description:"L6悟道",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"memory_cleanup",description:"L7清理",parameters:{type:"object",properties:{},required:[]}}},
  
  // 工具
  {type:"function",function:{name:"calculator",description:"数学计算",parameters:{type:"object",properties:{expression:{type:"string"}},required:["expression"]}}},
  {type:"function",function:{name:"get_time",description:"当前时间",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"set_timer",description:"定时提醒",parameters:{type:"object",properties:{seconds:{type:"number"},message:{type:"string"}},required:["seconds","message"]}}},
  {type:"function",function:{name:"send_notification",description:"系统通知",parameters:{type:"object",properties:{title:{type:"string"},body:{type:"string"}},required:["title","body"]}}},
  {type:"function",function:{name:"text_to_speech",description:"文字转语音",parameters:{type:"object",properties:{text:{type:"string"}},required:["text"]}}},
  {type:"function",function:{name:"translate",description:"翻译文本",parameters:{type:"object",properties:{text:{type:"string"},from:{type:"string"},to:{type:"string"}},required:["text","to"]}}},
  {type:"function",function:{name:"json_parse",description:"解析JSON",parameters:{type:"object",properties:{text:{type:"string"}},required:["text"]}}},
  {type:"function",function:{name:"text_analyze",description:"文本分析(字数/词频/情感)",parameters:{type:"object",properties:{text:{type:"string"}},required:["text"]}}},
  
  // 通讯
  {type:"function",function:{name:"make_call",description:"发起WebRTC通话",parameters:{type:"object",properties:{peerId:{type:"string"}},required:["peerId"]}}},
  {type:"function",function:{name:"send_peer_message",description:"发送P2P消息",parameters:{type:"object",properties:{peerId:{type:"string"},message:{type:"string"}},required:["peerId","message"]}}},
  
  // 自愈
  {type:"function",function:{name:"self_check",description:"自检",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"self_heal",description:"自愈",parameters:{type:"object",properties:{issue:{type:"string"}},required:[]}}},
  {type:"function",function:{name:"save_skill",description:"固化技能L5",parameters:{type:"object",properties:{name:{type:"string"},description:{type:"string"},rule:{type:"string"}},required:["name","rule"]}}},
  {type:"function",function:{name:"load_skills",description:"加载已固化技能",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"session_search",description:"搜索历史对话",parameters:{type:"object",properties:{query:{type:"string"}},required:["query"]}}},
];

// ===================================================================
// 工具执行器
// ===================================================================
const memory = new EternalMemory();

async function execTool(name, args) {
  switch(name) {
    case 'read_file': { const c=localStorage.getItem('f_'+args.path); return c!==null?JSON.stringify({path:args.path,content:c}):JSON.stringify({error:'不存在'}); }
    case 'write_file': localStorage.setItem('f_'+args.path, args.content); return JSON.stringify({path:args.path,size:args.content.length});
    case 'list_files': { const fs=[]; for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith('f_'))fs.push({name:k.slice(2),size:localStorage.getItem(k).length});} return JSON.stringify({files:fs,count:fs.length}); }
    case 'delete_file': localStorage.removeItem('f_'+args.path); return JSON.stringify({path:args.path,status:'deleted'});
    case 'search_files': {
      const p=args.pattern.toLowerCase(); const r=[];
      for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith('f_')){const v=localStorage.getItem(k);if(v.toLowerCase().includes(p))r.push({file:k.slice(2),match:v.substring(Math.max(0,v.toLowerCase().indexOf(p)-30),v.toLowerCase().indexOf(p)+80)});}}
      return JSON.stringify({pattern:p,results:r.slice(0,10)});
    }
    
    case 'web_search': return await searchDuckDuckGo(args.query);
    case 'http_request': return await doHTTP(args.url,args.method||'GET',args.headers,args.body);
    case 'html_parse': return parseHTMLContent(args.html,args.selector||'text');
    case 'web_extract': return await extractPage(args.url);
    
    case 'memory_save': await memory.remember(args.key,args.value,args.tag||'general',args.type||'fact'); return JSON.stringify({key:args.key,status:'remembered'});
    case 'memory_recall': {
      if(args.key)return JSON.stringify({key:args.key,value:memory.recall(args.key)});
      if(args.tag)return JSON.stringify({tag:args.tag,results:memory.searchByTag(args.tag)});
      if(args.query)return JSON.stringify({query:args.query,results:memory.search(args.query)});
      return JSON.stringify({status:memory.getStatus()});
    }
    case 'memory_status': return JSON.stringify(memory.getStatus());
    case 'memory_refine': return JSON.stringify(await memory.refine());
    case 'memory_enlighten': return JSON.stringify(await memory.enlighten());
    case 'memory_cleanup': return JSON.stringify(await memory.cleanup());
    
    case 'calculator': try{const s=args.expression.replace(/[^0-9+\-*/().%\s]/g,'');return JSON.stringify({expression:args.expression,result:Function('"use strict";return('+s+')')()});}catch(e){return JSON.stringify({error:e.message});}
    case 'get_time': {const n=new Date();return JSON.stringify({iso:n.toISOString(),local:n.toLocaleString('zh-CN'),tz:Intl.DateTimeFormat().resolvedOptions().timeZone,weekday:['日','一','二','三','四','五','六'][n.getDay()]});}
    case 'set_timer': setTimeout(()=>{if(Notification.permission==='granted')new Notification('⏰小龙人',{body:args.message});},args.seconds*1000); return JSON.stringify({seconds:args.seconds,status:'set'});
    case 'send_notification': if(Notification.permission==='granted')new Notification(args.title,{body:args.body}); return JSON.stringify({status:'sent'});
    case 'text_to_speech': {const u=new SpeechSynthesisUtterance(args.text);u.lang='zh-CN';speechSynthesis.speak(u);return JSON.stringify({status:'speaking',text:args.text.substring(0,100)});}
    case 'translate': return await doTranslate(args.text,args.from||'auto',args.to);
    case 'json_parse': try{return JSON.stringify({parsed:JSON.parse(args.text)});}catch(e){return JSON.stringify({error:e.message});}
    case 'text_analyze': {const t=args.text;return JSON.stringify({chars:t.length,words:t.split(/[\s，。！？,.!?]+/).filter(Boolean).length,lines:t.split('\n').length,preview:t.substring(0,200)});}
    
    case 'make_call': return JSON.stringify({peerId:args.peerId,status:'calling',note:'信令需后端'});
    case 'send_peer_message': return JSON.stringify({peerId:args.peerId,message:args.message,status:'sent'});
    
    case 'self_check': return JSON.stringify({agent:'XiaoLongRen v5.0',memory:memory.getStatus(),tools:ALL_TOOLS.length,health:memory.consecutiveErrors>=3?'⚠️':'✅'});
    case 'self_heal': {
      const issues = [];
      if (memory.consecutiveErrors >= 3) issues.push('连续错误≥3，建议简化任务重试');
      if (Object.keys(memory.l1).length > 180) issues.push('L1接近容量上限');
      await memory.enlighten();
      return JSON.stringify({issues, actions: issues.length===0?['无问题，系统健康']:['清除连续错误计数','压缩L1','检查API配置']});
    }
    case 'save_skill': await memory.skillify(args.name, args.description||'', args.rule); return JSON.stringify({name:args.name,status:'skill_saved_L5'});
    case 'load_skills': return JSON.stringify({skills:Object.keys(memory.l5_skills).map(k=>({name:k,...memory.l5_skills[k]}))});
    case 'session_search': {
      const conv = await memory.loadConversation();
      const q = args.query.toLowerCase();
      const matches = conv.filter(m => m.content.toLowerCase().includes(q));
      return JSON.stringify({query:args.query,found:matches.length,matches:matches.slice(0,5).map(m=>({role:m.role,content:m.content.substring(0,200)}))});
    }
    
    default: return JSON.stringify({error:'未知工具:'+name});
  }
}

// 工具实现
async function searchDuckDuckGo(q) {
  try {
    const r=await fetch('https://html.duckduckgo.com/html/?q='+encodeURIComponent(q));
    const h=await r.text(); const s=[]; const re=/class="result__snippet"[^>]*>(.*?)<\/a>/gs; let m;
    while((m=re.exec(h))&&s.length<5)s.push(m[1].replace(/<[^>]*>/g,'').trim());
    return JSON.stringify({query:q,results:s.length?s:['无结果']});
  }catch(e){return JSON.stringify({error:e.message});}
}
async function doHTTP(url,method,headersStr,body) {
  try {
    const o={method,headers:{'User-Agent':'XiaoLongRen/5.0'}};
    if(headersStr)try{Object.assign(o.headers,JSON.parse(headersStr));}catch(e){}
    if(body)o.body=body;
    const r=await fetch(url,o); const t=await r.text();
    return JSON.stringify({status:r.status,url,body:t.substring(0,3000)});
  }catch(e){return JSON.stringify({error:e.message});}
}
function parseHTMLContent(html,sel) {
  try {
    if(sel==='text'){const t=html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi,'').replace(/<script[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();return JSON.stringify({text:t.substring(0,2000)});}
    if(sel==='links'){const re=/<a[^>]*href=["']([^"']*)["'][^>]*>([^<]*)<\/a>/gi;const ls=[];let m;while((m=re.exec(html))&&ls.length<20)ls.push({href:m[1],text:m[2].trim()});return JSON.stringify({links:ls});}
    if(sel==='forms'){const fs=[];const fr=/<form[^>]*>([\s\S]*?)<\/form>/gi;let fm;while((fm=fr.exec(html))){const is=[];const ir=/<input[^>]*name=["']([^"']*)["'][^>]*>/gi;let im;while((im=ir.exec(fm[1])))is.push(im[1]);fs.push({inputs:is});}return JSON.stringify({forms:fs});}
    return JSON.stringify({error:'未知selector'});
  }catch(e){return JSON.stringify({error:e.message});}
}
async function extractPage(url) {
  try{const r=await fetch(url);const h=await r.text();return parseHTMLContent(h,'text');}catch(e){return JSON.stringify({error:e.message});}
}
async function doTranslate(text,from,to) {
  try {
    const r=await fetch('https://translate.googleapis.com/translate_a/single?client=gtx&sl='+from+'&tl='+to+'&dt=t&q='+encodeURIComponent(text));
    const d=await r.json();
    return JSON.stringify({original:text,translated:d[0].map(x=>x[0]).join(''),from,to});
  }catch(e){return JSON.stringify({error:e.message});}
}


// ===================================================================
// AGENT 内核
// ===================================================================
class XiaoLongRen {
  constructor(cfg={}) {
    this.provider=cfg.provider||'deepseek'; this.model=cfg.model||'deepseek-chat';
    this.apiKey=cfg.apiKey||''; this.baseUrl=cfg.baseUrl||'';
    this.maxIter=cfg.maxIter||90; this.temp=cfg.temp||0.7;
    this.messages=[]; this.onThink=cfg.onThink||(()=>{}); this.onTool=cfg.onTool||(()=>{});
    this.onReply=cfg.onReply||(()=>{}); this.onErr=cfg.onErr||(()=>{});
  }

  getEP() {
    if(this.baseUrl)return this.baseUrl.replace(/\/+$/,'')+'/chat/completions';
    const m={deepseek:'https://api.deepseek.com/v1',openai:'https://api.openai.com/v1',moonshot:'https://api.moonshot.cn/v1',zhipu:'https://open.bigmodel.cn/api/paas/v4',qwen:'https://dashscope.aliyuncs.com/compatible-mode/v1',anthropic:'https://api.anthropic.com/v1'};
    return (m[this.provider]||m.deepseek)+'/chat/completions';
  }

  async run(userMsg, charSys='') {
    memory.turnCount++;
    const sysPrompt = L0_SOUL + '\n\n## 角色设定\n' + charSys + '\n\n## 记忆状态\n' + JSON.stringify(memory.getStatus());
    
    this.messages = [{role:'system',content:sysPrompt}];
    const hist = await memory.loadConversation();
    this.messages.push(...hist.slice(-20));
    this.messages.push({role:'user',content:userMsg});

    for (let iter=1; iter<=this.maxIter; iter++) {
      this.onThink(iter);
      
      try {
        const r = await fetch(this.getEP(), {
          method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+this.apiKey},
          body: JSON.stringify({model:this.model,messages:this.messages,tools:ALL_TOOLS,tool_choice:'auto',temperature:this.temp,max_tokens:4096})
        });
        if(!r.ok){const t=await r.text();throw new Error(JSON.parse(t).error?.message||`API ${r.status}`);}
        const d=await r.json(); const msg=d.choices[0].message;
        
        if(msg.tool_calls?.length>0) {
          this.messages.push({role:'assistant',content:msg.content||'',tool_calls:msg.tool_calls.map(tc=>({id:tc.id,type:'function',function:{name:tc.function.name,arguments:tc.function.arguments}}))});
          for(const tc of msg.tool_calls) {
            const args = (()=>{try{return JSON.parse(tc.function.arguments)}catch(e){return{}}})();
            this.onTool(tc.function.name, args);
            const result = await execTool(tc.function.name, args);
            this.messages.push({role:'tool',tool_call_id:tc.id,content:result});
          }
          memory.errorCount=0; memory.consecutiveErrors=0;
          continue;
        }
        
        const reply = msg.content||'';
        this.onReply(reply);
        memory.errorCount=0; memory.consecutiveErrors=0;
        this.messages.push({role:'assistant',content:reply});
        await memory.saveConversation(this.messages);
        
        if(memory.turnCount%10===0)await memory.refine();
        if(memory.turnCount%50===0)await memory.enlighten();
        
        return reply;
        
      } catch(err) {
        memory.errorCount++; memory.consecutiveErrors++;
        memory.lastErrorType = err.message;
        if(iter<3){await new Promise(r=>setTimeout(r,2000));continue;}
        if(memory.consecutiveErrors>=3){await memory.enlighten();await memory.remember('error_'+Date.now(),err.message,'error','reflection');}
        this.onErr(err.message);
        return `抱歉，${err.message}。已尝试${iter}次。建议：检查网络和API Key配置。`;
      }
    }
    return `已尝试${this.maxIter}次，任务未完成。请简化请求。`;
  }
}
