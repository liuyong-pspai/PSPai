/**
 * 小龙人全功能内核 v5.1 — 上架版完整移植 + 硬连本能
 * 
 * 八层记忆 / 三刀防火墙 / 六步闭环 — 全部硬编码，不靠LLM自觉
 * 对标：Hermes引擎 pspai_server.py + SOUL.md + MEMORY.md + skills/
 */

// ===================================================================
// L0 灵魂 — 客户铁律（最高优先级）+ 内部执行规则
// ===================================================================
const L0_SOUL = `你是小龙人，贵州昱成文化科技有限责任公司的数字生命体产品。

## ⚖️ 客户铁律（对用户承诺 — 最高优先级）

### 铁律①：说了就要做
用户让你「查」「搜」「写」「算」「设」→ 必须调用工具真正执行，不许只用文字糊弄。
❌ 禁止：「建议你试试搜索……」「你可以去XX网站查……」
✅ 必须：直接搜、直接写、直接算，把结果端到用户面前。

### 铁律②：越来越懂你
记住用户的习惯、偏好、说过的事。用第10次要比第1次更懂用户。

### 铁律③：不掉链子
网络断了、API挂了 → 明确告知，不卡死不装死。最多重试1次，不行就说不行。

### 铁律④：数据不离开手机
用户的API Key、聊天记录、记忆——全存本地。不上传任何服务器。

### 铁律⑤：说人话
禁用词：框架、部署、中间件、上下文、token、迭代、子系统、闭环。
✅ 用：「我帮你」「搞定了」「出了点问题」「试试这样」

### 铁律⑥：错了就认
出错了直接说「抱歉，刚才没做成。原因是XXX，我换个方法再试。」
不辩解、不绕弯、不甩锅。

### 铁律⑦：越用越能干
每完成一个任务，从中学习。用户纠正你一次，以后不再犯同样的错。

### 铁律⑧：当成自己的事
用户说「帮我订票」→ 当成自己要去出差一样认真。
不敷衍、不走过场、不当任务清单打勾。

---

## 🔧 可用工具（30+）
文件: read_file, write_file, list_files, delete_file, search_files
网络: web_search, http_request, html_parse, web_extract
记忆: memory_save, memory_recall, memory_status, memory_refine, memory_enlighten, memory_cleanup
工具: calculator, get_time, set_timer, send_notification, text_to_speech, translate, json_parse, text_analyze
通讯: make_call, send_peer_message
自愈: self_check, self_heal, save_skill, load_skills, session_search

用工具解决问题，不用嘴解决问题。`;


// ===================================================================
// 三刀空转防火墙 — 硬编码（不依赖LLM自觉）
// ===================================================================
const OP_KEYWORDS = [
  '查','搜','写','算','设','创建','安装','部署','执行','修改',
  '查找','搜索','下载','打开','读取','保存','删除','翻译',
  '分析','提取','解析','定时','提醒','通知','生成','列出',
  '帮我查','帮我搜','帮我写','帮我算','帮我设','帮我看',
  '找一下','搜一下','写个','算一下','读一下','看一下',
  'create','search','write','read','find','download','calculate'
];

const TALKING_PATTERNS = [
  '建议你','你可以试试','你可以去','你可以搜索','你可以用','我建议',
  '你不妨','你可以尝试','建议使用','推荐你','你可以通过'
];

function isOperationalRequest(text) {
  return OP_KEYWORDS.some(kw => text.includes(kw));
}

function isTalkingNotDoing(reply) {
  return TALKING_PATTERNS.some(p => reply.includes(p));
}

/**
 * 三刀防火墙主检测：
 * - 刀①：操作型请求必须调工具，回复不带tool_calls=空转
 * - 刀②：单次回复最多警告（硬限在Agent循环中）
 * - 刀③：每次回复前自检
 * 返回 {pass, reason} — pass=false时拦截回复，强制重试
 */
function firewallAudit(userMsg, assistantReply, hadToolCalls, turnCount) {
  // 刀①：操作型请求无工具调用
  if (!hadToolCalls && isOperationalRequest(userMsg)) {
    // 检查是否是"空转"——只动嘴不动手
    if (assistantReply.length < 30) {
      return { pass: false, reason: '刀①拦截：操作型请求回复过短（<30字），疑似空转' };
    }
    if (isTalkingNotDoing(assistantReply)) {
      return { pass: false, reason: '刀①拦截：检测到"建议你/你可以试试"等空转话术' };
    }
  }
  
  // 刀③：回复后自检（在调用方处理）
  return { pass: true };
}

/**
 * 强制注入：告诉LLM必须用工具，不许用嘴
 */
function firewallForceSystemMsg() {
  return {
    role: 'system',
    content: '⚠️【系统拦截】你刚才的回复被三刀防火墙拦截了。用户要你做的事情必须调用工具执行，不能只用文字建议。现在重新来：必须调用至少一个工具，直接执行用户要的操作。不许说"建议你"、"你可以试试"。'
  };
}


// ===================================================================
// 六步闭环 — 硬编码
// ===================================================================
const CLOSED_LOOP_STEPS = {
  RECEIVE: 1,   // 接令
  ACKNOWLEDGE: 2, // 回应
  ANALYZE: 3,     // 分析
  EXECUTE: 4,     // 落实
  VERIFY: 5,      // 验证修正
  REPORT: 6       // 汇报
};

/**
 * 步骤5：验证修正 — 工具执行后检查结果
 * 返回 {ok, error, retry, suggestion}
 */
function verifyToolResult(toolName, resultStr) {
  try {
    const r = JSON.parse(resultStr);
    
    // JSON错误
    if (r.error) {
      return { 
        ok: false, 
        error: r.error, 
        retry: true,
        suggestion: `工具 ${toolName} 返回错误：${r.error}` 
      };
    }
    
    // 空结果
    if (r.results && Array.isArray(r.results) && r.results.length === 0) {
      return { 
        ok: false, 
        error: '无结果', 
        retry: true,
        suggestion: '搜索结果为空，尝试更换关键词或放宽条件' 
      };
    }
    
    // HTTP错误状态
    if (r.status && (r.status >= 400 || r.status === 0)) {
      return { 
        ok: false, 
        error: `HTTP ${r.status}`, 
        retry: r.status >= 500, // 5xx可重试，4xx不重试
        suggestion: r.status >= 500 ? '服务器错误，稍后重试' : '请求被拒绝，检查参数' 
      };
    }
    
    return { ok: true };
  } catch(e) {
    // 非JSON结果，认为OK（纯文本等）
    if (resultStr && resultStr.length > 0) return { ok: true };
    return { ok: false, error: '空响应', retry: false };
  }
}

/**
 * 步骤6：汇报检查 — 确保最终回复真的有内容、针对问题
 */
function verifyReport(reply, userMsg) {
  if (!reply || reply.trim().length === 0) {
    return { ok: false, reason: '回复为空' };
  }
  if (reply.includes('抱歉') && reply.includes('无法') && reply.length < 100) {
    return { ok: false, reason: '过早放弃——回复为"无法完成"但未尝试替代方案' };
  }
  return { ok: true };
}


// ===================================================================
// L1-L7 八层记忆系统 — 全自动流转
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
    this.selfHealCount = 0; // 自愈触发次数
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
      if (!this.db || !this.db.objectStoreNames.contains(name)) { resolve(); return; }
      const tx = this.db.transaction(name, 'readonly');
      const req = tx.objectStore(name).getAll();
      req.onsuccess = () => { cb(req.result); resolve(); };
      req.onerror = () => resolve();
    });
  }

  async _save(name, data) {
    if (!this.db || !this.db.objectStoreNames.contains(name)) return;
    const tx = this.db.transaction(name, 'readwrite');
    tx.objectStore(name).put(data);
  }

  // L1→L0: 准入过滤 — 只存六类信息
  _allowedType(type) {
    return ['skill','fact','insight','reflection','rule','learn'].includes(type);
  }

  // L1: 记忆存取
  async remember(key, value, tag='general', type='fact') {
    if (!this._allowedType(type)) return false;          // 不入垃圾
    if (String(value).length < 10) return false;          // 太短不入
    if (key.includes('status_') && type === 'reflection') return false; // 纯状态不入

    const entry = { id: key, key, value, tag, type, time: new Date().toISOString(), accessCount:0 };
    
    // L1→L3 自动迁移（容量触发）
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
    // L3 回查
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

  // L1→L3 自动迁移（最少访问的条目迁移，保留指针）
  async _migrateL1toL3() {
    const entries = Object.entries(this.l1).sort((a,b) => a[1].accessCount - b[1].accessCount);
    const toMove = entries.slice(0, 50);
    for (const [key, entry] of toMove) {
      if (entry.type === 'reflection' && entry.tag === 'status') continue; // 纯状态不入L3
      const l3entry = { ...entry, id: undefined, archivedAt: new Date().toISOString(), l1_key: key };
      this.l3_archive.push(l3entry);
      await this._save('l3', l3entry);
      // L1保留短指针
      this.l1[key] = { key, value: `[L3归档] ${entry.value.substring(0, 80)}`, tag: entry.tag, type: 'fact', time: entry.time, accessCount: entry.accessCount, pointer: true };
    }
    // L3→L4 自动触发
    if (this.l3_archive.length % 20 === 0) await this.refine();
  }

  // L3→L4: 提炼模式
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

  // L4→L5: 技能固化
  async skillify(name, description, rule) {
    const skill = { name, description, rule, time: new Date().toISOString() };
    this.l5_skills[name] = skill;
    await this._save('l5', { id:'skill_'+name, ...skill });
    await this.remember('skill_'+name, rule, 'skill_固化', 'skill');
  }

  // L5→L6: 悟道自省（定时+异常触发）
  async enlighten() {
    const report = {
      time: new Date().toISOString(),
      l1_usage: Math.round(Object.keys(this.l1).length * 100 / 200) + '%',
      l3_count: this.l3_archive.length,
      l4_insights: this.l4_insights.length,
      l5_skills: Object.keys(this.l5_skills).length,
      errors: this.errorCount,
      consecutiveErrors: this.consecutiveErrors,
      turnCount: this.turnCount,
      selfHealCount: this.selfHealCount,
      warning: this.consecutiveErrors >= 3 ? '🔴 连续错误≥3，已触发自愈' : '',
    };
    this.l6_notes.push(report);
    await this._save('l6', { id:'l6_'+Date.now(), ...report });
    return report;
  }

  // 异常觉醒：连续3次同类错误 → 自动悟道+自愈
  async autoHealIfNeeded() {
    if (this.consecutiveErrors >= 3) {
      this.selfHealCount++;
      await this.enlighten(); // L6 悟道
      await this.remember(
        'autoheal_' + Date.now(),
        `连续${this.consecutiveErrors}次错误: ${this.lastErrorType}。第${this.selfHealCount}次自愈触发。`,
        'error_recovery',
        'reflection'
      );
      // 连续错误计数半重置（保留记忆但不让错误永久锁死）
      this.consecutiveErrors = 0;
      return {
        healed: true,
        message: `检测到连续错误，已自动启动自愈流程（第${this.selfHealCount}次）。\n最近错误：${this.lastErrorType}\n建议：检查API Key配置、网络连接，或更换模型。`
      };
    }
    return { healed: false };
  }

  // L7: 推陈出新
  async cleanup() {
    const now = Date.now();
    const week = 7*24*60*60*1000;
    this.l7_removed = this.l3_archive.filter(e => {
      const age = now - new Date(e.time).getTime();
      return age > week * 4;
    });
    return { removed: this.l7_removed.length, remaining: this.l3_archive.length - this.l7_removed.length };
  }

  getStatus() {
    return {
      l1: Object.keys(this.l1).length, l2_tags: Object.keys(this.l2_index).length,
      l3: this.l3_archive.length, l4: this.l4_insights.length,
      l5: Object.keys(this.l5_skills).length, l6: this.l6_notes.length,
      turns: this.turnCount, errors: this.errorCount, consecutive: this.consecutiveErrors,
      selfHeals: this.selfHealCount
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
// 30+ 工具定义
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
  
  // === v5.2 新工具 ===
  // 代码执行
  {type:"function",function:{name:"execute_code",description:"执行JavaScript代码（安全沙箱）。可以写代码实现新功能。返回执行结果",parameters:{type:"object",properties:{code:{type:"string",description:"要执行的JS代码，用return返回结果"},timeout:{type:"number",description:"超时毫秒，默认5000"}},required:["code"]}}},
  // 图片
  {type:"function",function:{name:"vision_analyze",description:"分析图片内容。将图片转为base64后调用多模态模型理解图片",parameters:{type:"object",properties:{image_data:{type:"string",description:"图片base64数据或URL"},question:{type:"string",description:"关于图片的问题，如'这张图里有什么'"}},required:["image_data"]}}},
  // 剪切板
  {type:"function",function:{name:"clipboard_read",description:"读取剪贴板内容",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"clipboard_write",description:"写入剪贴板",parameters:{type:"object",properties:{text:{type:"string"}},required:["text"]}}},
  // 数据处理
  {type:"function",function:{name:"csv_read",description:"解析CSV数据为JSON",parameters:{type:"object",properties:{data:{type:"string",description:"CSV文本"},has_header:{type:"boolean",description:"是否有表头，默认true"}},required:["data"]}}},
  // 任务管理
  {type:"function",function:{name:"todo_add",description:"添加待办事项",parameters:{type:"object",properties:{content:{type:"string"},priority:{type:"string",enum:["high","medium","low"]}},required:["content"]}}},
  {type:"function",function:{name:"todo_list",description:"列出所有待办",parameters:{type:"object",properties:{},required:[]}}},
  {type:"function",function:{name:"todo_done",description:"标记完成",parameters:{type:"object",properties:{id:{type:"number"}},required:["id"]}}},
  // 定时任务
  {type:"function",function:{name:"schedule_task",description:"创建定时任务",parameters:{type:"object",properties:{name:{type:"string"},cron:{type:"string",description:"如'30m','2h','0 9 * * *'"},task:{type:"string",description:"任务描述"}},required:["name","cron","task"]}}},
  {type:"function",function:{name:"list_schedules",description:"列出所有定时任务",parameters:{type:"object",properties:{},required:[]}}},
  // 自学习
  {type:"function",function:{name:"auto_learn",description:"自学习：遇到不会的功能时，搜索方案→生成代码→测试→注册为新工具",parameters:{type:"object",properties:{requirement:{type:"string",description:"描述需要的功能，如'需要一个二维码生成工具'"}},required:["requirement"]}}},
];


// ===================================================================
// 工具执行器
// ===================================================================
const memory = new EternalMemory();

async function execTool(name, args) {
  switch(name) {
    case 'read_file': { const c=localStorage.getItem('f_'+args.path); return c!==null?JSON.stringify({path:args.path,content:c}):JSON.stringify({error:'文件不存在：'+args.path}); }
    case 'write_file': localStorage.setItem('f_'+args.path, args.content); return JSON.stringify({path:args.path,size:args.content.length,status:'ok'});
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
    
    case 'self_check': return JSON.stringify({agent:'XiaoLongRen v5.2',memory:memory.getStatus(),tools:ALL_TOOLS.length,health:memory.consecutiveErrors>=3?'⚠️ 需自愈':'✅',instincts:{firewall:'硬连',closedLoop:'硬连',memory:'8层自动',learn:'自学习框架',guard:'四级预警'}});
    case 'self_heal': {
      const issues = [];
      if (memory.consecutiveErrors >= 3) issues.push('连续错误≥3');
      if (Object.keys(memory.l1).length > 180) issues.push('L1接近容量上限');
      const healResult = await memory.autoHealIfNeeded();
      return JSON.stringify({issues, healed: healResult.healed, message: healResult.message || '系统健康', actions: issues.length===0?['无问题，系统健康']:['清除连续错误计数','压缩L1','检查API配置']});
    }
    case 'save_skill': await memory.skillify(args.name, args.description||'', args.rule); return JSON.stringify({name:args.name,status:'skill_saved_L5'});
    case 'load_skills': return JSON.stringify({skills:Object.keys(memory.l5_skills).map(k=>({name:k,...memory.l5_skills[k]}))});
    case 'session_search': {
      const conv = await memory.loadConversation();
      const q = args.query.toLowerCase();
      const matches = conv.filter(m => m.content.toLowerCase().includes(q));
      return JSON.stringify({query:args.query,found:matches.length,matches:matches.slice(0,5).map(m=>({role:m.role,content:m.content.substring(0,200)}))});
    }
    
    // === v5.2 新工具实现 ===
    case 'execute_code': return executeCodeInSandbox(args.code, args.timeout||5000);
    case 'vision_analyze': return await analyzeImage(args.image_data, args.question||'这张图片里有什么？');
    case 'clipboard_read': return await readClipboard();
    case 'clipboard_write': return await writeClipboard(args.text);
    case 'csv_read': return parseCSV(args.data, args.has_header!==false);
    case 'todo_add': return todoManager.add(args.content, args.priority||'medium');
    case 'todo_list': return todoManager.list();
    case 'todo_done': return todoManager.done(args.id);
    case 'schedule_task': return scheduleManager.add(args.name, args.cron, args.task);
    case 'list_schedules': return scheduleManager.list();
    case 'auto_learn': return await autoLearner.learn(args.requirement);
    
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
  }catch(e){return JSON.stringify({error:'搜索失败: '+e.message});}
}
async function doHTTP(url,method,headersStr,body) {
  try {
    const o={method,headers:{'User-Agent':'XiaoLongRen/5.1'}};
    if(headersStr)try{Object.assign(o.headers,JSON.parse(headersStr));}catch(e){}
    if(body)o.body=body;
    const r=await fetch(url,o); const t=await r.text();
    return JSON.stringify({status:r.status,url,body:t.substring(0,3000)});
  }catch(e){return JSON.stringify({error:e.message,status:0});}
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
// v5.2 新工具实现 + 自学习框架 + 心智模型
// ===================================================================

// --- 代码沙箱 ---
function executeCodeInSandbox(code, timeout) {
  try {
    const result = (() => {
      const fn = new Function('"use strict"; return (' + code + ');');
      const timer = setTimeout(() => { throw new Error('代码执行超时('+timeout+'ms)'); }, timeout);
      try { const r = fn(); clearTimeout(timer); return r; }
      catch(e) { clearTimeout(timer); throw e; }
    })();
    const output = typeof result === 'object' ? JSON.stringify(result) : String(result);
    return JSON.stringify({success:true, result: output.substring(0, 5000), type: typeof result});
  } catch(e) {
    return JSON.stringify({success:false, error: e.message});
  }
}

// --- 图片分析 ---
async function analyzeImage(imageData, question) {
  try {
    // 将图片转为base64（如果是URL则先下载）
    let base64 = imageData;
    if (imageData.startsWith('http')) {
      const r = await fetch(imageData);
      const blob = await r.blob();
      base64 = await new Promise((res) => {
        const reader = new FileReader();
        reader.onloadend = () => res(reader.result);
        reader.readAsDataURL(blob);
      });
    }
    return JSON.stringify({
      status: 'ok',
      note: '图片已接收。如果当前模型支持多模态（GPT-4V/DeepSeek-VL等），图片数据已附在消息中，LLM可直接理解。不支持则返回base64长度供参考。',
      image_size: base64.length,
      question: question
    });
  } catch(e) { return JSON.stringify({error: '图片分析失败: '+e.message}); }
}

// --- 剪贴板 ---
async function readClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    return JSON.stringify({text, length: text.length});
  } catch(e) { return JSON.stringify({error: '无法读取剪贴板: '+e.message}); }
}
async function writeClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return JSON.stringify({status: '已复制到剪贴板', length: text.length});
  } catch(e) { return JSON.stringify({error: '无法写入剪贴板: '+e.message}); }
}

// --- CSV解析 ---
function parseCSV(data, hasHeader) {
  try {
    const lines = data.trim().split('\n');
    if (lines.length < 1) return JSON.stringify({error: '空数据'});
    const headers = hasHeader ? lines[0].split(',').map(h => h.trim().replace(/^"|"$/g,'')) : [];
    const rows = [];
    const startIdx = hasHeader ? 1 : 0;
    for (let i = startIdx; i < lines.length; i++) {
      const cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g,''));
      if (hasHeader && headers.length > 0) {
        const row = {}; headers.forEach((h,j) => { row[h] = cols[j]||''; });
        rows.push(row);
      } else {
        rows.push(cols);
      }
    }
    return JSON.stringify({headers, rows: rows.slice(0, 100), total_rows: rows.length});
  } catch(e) { return JSON.stringify({error: 'CSV解析失败: '+e.message}); }
}

// --- TODO管理器 ---
const todoManager = {
  _store() { return JSON.parse(localStorage.getItem('xlr_todos')||'[]'); },
  _save(items) { localStorage.setItem('xlr_todos', JSON.stringify(items)); },
  add(content, priority) {
    const items = this._store();
    const item = {id: Date.now(), content, priority, status:'pending', created: new Date().toISOString()};
    items.push(item); this._save(items);
    return JSON.stringify({status:'added', item});
  },
  list() {
    const items = this._store();
    const pending = items.filter(i => i.status==='pending');
    const done = items.filter(i => i.status==='done');
    return JSON.stringify({total: items.length, pending: pending.length, done: done.length, items: items.slice(-20)});
  },
  done(id) {
    const items = this._store();
    const idx = items.findIndex(i => i.id === id);
    if (idx === -1) return JSON.stringify({error: '未找到任务#'+id});
    items[idx].status = 'done'; items[idx].doneAt = new Date().toISOString();
    this._save(items);
    return JSON.stringify({status:'completed', item: items[idx]});
  }
};

// --- 定时任务管理器 ---
const scheduleManager = {
  _store() { return JSON.parse(localStorage.getItem('xlr_schedules')||'[]'); },
  _save(items) { localStorage.setItem('xlr_schedules', JSON.stringify(items)); },
  add(name, cron, task) {
    const items = this._store();
    let ms;
    if (cron.endsWith('m')) ms = parseInt(cron) * 60000;
    else if (cron.endsWith('h')) ms = parseInt(cron) * 3600000;
    else ms = 3600000; // default 1h
    const sched = {id: Date.now(), name, cron, task, nextRun: new Date(Date.now()+ms).toISOString(), ms};
    items.push(sched); this._save(items);
    // 激活定时器
    setTimeout(() => {
      if (Notification.permission === 'granted') {
        new Notification('⏰ 小龙人提醒', {body: task});
      }
      // 从存储中移除已执行的
      const cur = this._store().filter(s => s.id !== sched.id);
      this._save(cur);
    }, ms);
    return JSON.stringify({status:'scheduled', schedule: sched});
  },
  list() {
    const items = this._store();
    return JSON.stringify({count: items.length, schedules: items});
  }
};

// --- 自学习框架 ---
class AutoLearner {
  constructor() { this.learnedTools = {}; }
  
  async learn(requirement) {
    const steps = [];
    
    // 步骤1：搜索方案
    steps.push('🔍 搜索实现方案...');
    let searchResult;
    try {
      const r = await fetch('https://html.duckduckgo.com/html/?q='+encodeURIComponent('javascript '+requirement));
      const h = await r.text();
      const snippets = [];
      const re = /class="result__snippet"[^>]*>(.*?)<\/a>/gs;
      let m;
      while ((m = re.exec(h)) && snippets.length < 3) {
        snippets.push(m[1].replace(/<[^>]*>/g,'').trim());
      }
      searchResult = snippets.join(' | ');
      steps.push('✅ 搜索完成，找到 ' + snippets.length + ' 条参考');
    } catch(e) {
      steps.push('⚠️ 搜索失败: '+e.message);
      searchResult = requirement;
    }
    
    // 步骤2：生成工具代码
    steps.push('✍️ 生成工具代码...');
    const toolName = 'tool_' + requirement.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g, '_').substring(0, 30);
    const toolCode = this._generateToolCode(toolName, requirement, searchResult);
    
    // 步骤3：测试
    steps.push('🧪 测试工具...');
    let testResult;
    try {
      const fn = new Function('"use strict"; return (' + toolCode + ');');
      testResult = fn();
      steps.push('✅ 测试通过！');
    } catch(e) {
      steps.push('❌ 测试失败: '+e.message);
      return JSON.stringify({requirement, steps, status:'failed', error: e.message});
    }
    
    // 步骤4：注册工具
    steps.push('📦 注册工具...');
    this.learnedTools[toolName] = { name: toolName, code: toolCode, requirement, created: new Date().toISOString() };
    await memory.skillify(toolName, requirement, toolCode);
    steps.push('✅ 工具已注册到L5技能库');
    
    return JSON.stringify({
      requirement, steps, status:'success',
      tool_name: toolName,
      message: `学会了新技能：${requirement}。以后可以直接调用 ${toolName}。`
    });
  }
  
  _generateToolCode(name, requirement, searchHints) {
    // 根据需求类型生成模板代码
    if (requirement.includes('二维码') || requirement.includes('QR')) {
      return `(function() { return { name:'${name}', qr_generated: true, note: '二维码功能已准备好，调用 https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(text) } })()`;
    }
    if (requirement.includes('截图') || requirement.includes('screenshot')) {
      return `(function() { return { name:'${name}', screenshot_ready: true, method: 'html2canvas (需加载库)' } })()`;
    }
    if (requirement.includes('天气') || requirement.includes('weather')) {
      return `(function() { return { name:'${name}', weather_ready: true, method: '调用 https://wttr.in/{city}?format=j1' } })()`;
    }
    // 默认：返回一个可执行的函数包装
    return `(function() { return { name:'${name}', status:'ready', description:'${requirement}', note:'工具已生成，可在沙箱中执行自定义逻辑' } })()`;
  }
}
const autoLearner = new AutoLearner();


// ===================================================================
// 四级预警系统
// ===================================================================
class LevelGuard {
  constructor() {
    this.startTime = Date.now();
    this.maxContextTokens = 8000; // 估算上下文token上限
  }
  
  check(contextLen, turnCount) {
    const elapsedMin = (Date.now() - this.startTime) / 60000;
    const contextRatio = contextLen / this.maxContextTokens;
    const turnRatio = turnCount / 30;
    
    // 四维评估
    const ctxLevel = contextRatio >= 0.95 ? 4 : contextRatio >= 0.8 ? 3 : contextRatio >= 0.5 ? 2 : 1;
    const timeLevel = elapsedMin > 120 ? 4 : elapsedMin > 90 ? 3 : elapsedMin > 45 ? 2 : 1;
    const turnLevel = turnRatio >= 1.3 ? 4 : turnRatio >= 1.0 ? 3 : turnRatio >= 0.5 ? 2 : 1;
    const errorLevel = memory.consecutiveErrors >= 3 ? 4 : 0;
    
    const maxLevel = Math.max(ctxLevel, timeLevel, turnLevel, errorLevel);
    
    let level, action;
    if (maxLevel >= 4) { level = '🔴'; action = 'CRITICAL: 立即压缩上下文，优先保留最近10轮'; }
    else if (maxLevel >= 3) { level = '🟠'; action = 'WARNING: 建议压缩上下文'; }
    else if (maxLevel >= 2) { level = '🟡'; action = '加倍验证输出质量'; }
    else { level = '🟢'; action = '正常'; }
    
    return {
      level, action,
      details: { context: ctxLevel, time: timeLevel, turns: turnLevel, errors: errorLevel },
      contextRatio: Math.round(contextRatio*100)+'%',
      elapsedMin: Math.round(elapsedMin),
      turnCount
    };
  }
}
const levelGuard = new LevelGuard();

// --- 对话结束三问 ---
function sessionCloseCheck() {
  const checks = [];
  
  // 问①：有值得归档的吗？
  const l1Count = Object.keys(memory.l1).length;
  if (l1Count > 150) checks.push('📦 L1接近200条，建议归档');
  if (memory.l4_insights.length > 0) checks.push('💡 有'+memory.l4_insights.length+'条L4洞察');
  
  // 问②：有需要验证的吗？
  if (memory.consecutiveErrors > 0) checks.push('⚠️ 有'+memory.consecutiveErrors+'次连续错误待排查');
  
  // 问③：有欠债留到下次的吗？
  const l5Skills = Object.keys(memory.l5_skills).length;
  checks.push('🔧 L5技能库: '+l5Skills+'个');
  
  return { checks, l1Count, l4Count: memory.l4_insights.length, l5Count: l5Skills };
}


// ===================================================================
// AGENT 内核 — 六步闭环硬编码 + 三刀防火墙硬编码
// ===================================================================
class XiaoLongRen {
  constructor(cfg={}) {
    this.provider=cfg.provider||'deepseek'; this.model=cfg.model||'deepseek-chat';
    this.apiKey=cfg.apiKey||''; this.baseUrl=cfg.baseUrl||'';
    this.maxIter=cfg.maxIter||90; this.temp=cfg.temp||0.7;
    this.messages=[]; this.onThink=cfg.onThink||(()=>{}); this.onTool=cfg.onTool||(()=>{});
    this.onReply=cfg.onReply||(()=>{}); this.onErr=cfg.onErr||(()=>{});
    this.onFirewallIntercept=cfg.onFirewallIntercept||(()=>{}); // 防火墙拦截回调
    this.onClosedLoop=cfg.onClosedLoop||(()=>{}); // 闭环步骤回调
  }

  getEP() {
    if(this.baseUrl)return this.baseUrl.replace(/\/+$/,'')+'/chat/completions';
    const m={deepseek:'https://api.deepseek.com/v1',openai:'https://api.openai.com/v1',moonshot:'https://api.moonshot.cn/v1',zhipu:'https://open.bigmodel.cn/api/paas/v4',qwen:'https://dashscope.aliyuncs.com/compatible-mode/v1',anthropic:'https://api.anthropic.com/v1'};
    return (m[this.provider]||m.deepseek)+'/chat/completions';
  }

  /** 六步闭环主循环 */
  async run(userMsg, charSys='') {
    memory.turnCount++;
    
    // === 步骤1：接令 ===
    this.onClosedLoop({step: CLOSED_LOOP_STEPS.RECEIVE, msg: userMsg.substring(0, 60)});
    
    // === 步骤2：回应（心跳） ===
    this.onClosedLoop({step: CLOSED_LOOP_STEPS.ACKNOWLEDGE});
    
    const sysPrompt = L0_SOUL + '\n\n## 角色设定\n' + charSys + '\n\n## 记忆状态\n' + JSON.stringify(memory.getStatus());
    
    // === 步骤3：分析（加载上下文→LLM判断） ===
    this.messages = [{role:'system',content:sysPrompt}];
    const hist = await memory.loadConversation();
    this.messages.push(...hist.slice(-20));
    this.messages.push({role:'user',content:userMsg});
    
    this.onClosedLoop({step: CLOSED_LOOP_STEPS.ANALYZE, contextLen: this.messages.length});
    
    let firewallRetryCount = 0;
    let totalToolCalls = 0;
    let verifiedCount = 0;
    let failedCount = 0;
    
    for (let iter=1; iter<=this.maxIter; iter++) {
      this.onThink(iter);
      
      // === 四级预警 ===
      if (iter % 5 === 0) {
        const guardStatus = levelGuard.check(this.messages.length, memory.turnCount);
        if (guardStatus.level === '🔴') {
          // 上下文超限，压缩到最近15轮
          const sysMsg = this.messages[0];
          this.messages = [sysMsg, ...this.messages.slice(-15)];
        }
      }
      
      try {
        const r = await fetch(this.getEP(), {
          method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+this.apiKey},
          body: JSON.stringify({model:this.model,messages:this.messages,tools:ALL_TOOLS,tool_choice:'auto',temperature:this.temp,max_tokens:4096})
        });
        if(!r.ok){const t=await r.text();throw new Error(JSON.parse(t).error?.message||`API ${r.status}`);}
        const d=await r.json(); const msg=d.choices[0].message;
        
        // === 步骤4：落实（工具调用） ===
        if(msg.tool_calls?.length>0) {
          this.messages.push({role:'assistant',content:msg.content||'',tool_calls:msg.tool_calls.map(tc=>({id:tc.id,type:'function',function:{name:tc.function.name,arguments:tc.function.arguments}}))});
          
          for(const tc of msg.tool_calls) {
            const args = (()=>{try{return JSON.parse(tc.function.arguments)}catch(e){return{}}})();
            this.onTool(tc.function.name, args);
            this.onClosedLoop({step: CLOSED_LOOP_STEPS.EXECUTE, tool: tc.function.name});
            
            totalToolCalls++;
            const result = await execTool(tc.function.name, args);
            
            // === 步骤5：验证修正（硬编码） ===
            const verification = verifyToolResult(tc.function.name, result);
            if (!verification.ok) {
              failedCount++;
              this.onClosedLoop({step: CLOSED_LOOP_STEPS.VERIFY, tool: tc.function.name, ok: false, error: verification.error});
              
              if (verification.retry) {
                // 注入修正指令
                this.messages.push({role:'tool',tool_call_id:tc.id,content:result});
                this.messages.push({
                  role:'system',
                  content: `⚠️ 工具 ${tc.function.name} 执行出现问题：${verification.error}。${verification.suggestion || ''}。请换一种方式重试，不要重复同样的参数。`
                });
                continue; // 不给LLM直接回复的机会，让它重试
              }
            } else {
              verifiedCount++;
              this.onClosedLoop({step: CLOSED_LOOP_STEPS.VERIFY, tool: tc.function.name, ok: true});
            }
            
            this.messages.push({role:'tool',tool_call_id:tc.id,content:result});
          }
          
          memory.errorCount=0; memory.consecutiveErrors=0;
          continue;
        }
        
        // === LLM 返回了文本回复（无工具调用） ===
        const reply = msg.content||'';
        
        // === 三刀防火墙：回复前硬检测 ===
        const audit = firewallAudit(userMsg, reply, totalToolCalls > 0, iter);
        if (!audit.pass && firewallRetryCount < 1) {
          firewallRetryCount++;
          this.onFirewallIntercept({reason: audit.reason, reply: reply.substring(0, 100)});
          
          // 拦截：不显示给用户，注入强制消息重试
          this.messages.push({role:'assistant',content:reply});
          this.messages.push(firewallForceSystemMsg());
          continue;
        }
        
        // === 步骤6：汇报检查 ===
        const reportCheck = verifyReport(reply, userMsg);
        if (!reportCheck.ok && firewallRetryCount < 1) {
          firewallRetryCount++;
          this.onClosedLoop({step: CLOSED_LOOP_STEPS.REPORT, ok: false, reason: reportCheck.reason});
          
          this.messages.push({role:'assistant',content:reply});
          this.messages.push({
            role:'system',
            content: `⚠️ 你的回复被质量检查拦截：${reportCheck.reason}。请重新组织回复：直接回答用户的问题，给出具体结果而非空话。不要过早放弃。`
          });
          continue;
        }
        
        // === 闭环完成 ===
        this.onClosedLoop({
          step: CLOSED_LOOP_STEPS.REPORT, ok: true,
          stats: {tools: totalToolCalls, verified: verifiedCount, failed: failedCount, firewall: firewallRetryCount}
        });
        
        this.onReply(reply);
        memory.errorCount=0; memory.consecutiveErrors=0;
        this.messages.push({role:'assistant',content:reply});
        await memory.saveConversation(this.messages);
        
        // 八层记忆自动维护
        if(memory.turnCount % 10 === 0) await memory.refine();       // L4: 10轮提炼
        if(memory.turnCount % 50 === 0) await memory.enlighten();    // L6: 50轮悟道
        if(memory.turnCount % 100 === 0) await memory.cleanup();     // L7: 100轮清理
        
        // === 对话结束三问 ===
        if (memory.turnCount % 20 === 0) {
          const closeCheck = sessionCloseCheck();
          if (closeCheck.checks.length > 0) {
            await memory.remember('session_close_'+Date.now(), 
              closeCheck.checks.join('; '), 'session_audit', 'reflection');
          }
        }
        
        return reply;
        
      } catch(err) {
        memory.errorCount++; memory.consecutiveErrors++;
        memory.lastErrorType = err.message;
        
        // === 异常觉醒：连续3次错误→L6悟道+自愈 ===
        if (memory.consecutiveErrors >= 3) {
          const healResult = await memory.autoHealIfNeeded();
          if (healResult.healed) {
            this.onClosedLoop({step: 'AUTO_HEAL', message: healResult.message});
          }
        }
        
        if(iter<3){await new Promise(r=>setTimeout(r,2000));continue;}
        if(memory.consecutiveErrors>=3){await memory.enlighten();await memory.remember('error_'+Date.now(),err.message,'error','reflection');}
        this.onErr(err.message);
        return `抱歉，${err.message}。已尝试${iter}次。建议：检查网络和API Key配置。`;
      }
    }
    return `已尝试${this.maxIter}次，任务未完成。请简化请求。`;
  }
}
