// 小龙人核心引擎 v3.0 — 全功能版
// 含：八层永生记忆 + SmartRouter + Agent循环 + 工具调用
// 嫁接铁律：不定义 PROVIDERS/getConfig（mobile.html 内联已有）

// ============================================================
// 八层永生记忆 (IndexedDB + 内存降级)
// ============================================================
const memory = (function() {
  let db = null;
  let fallbackMode = false;
  const fallbackStore = new Map();
  const DB_NAME = 'xiaolongren_memory';
  const DB_VER = 7;
  const MEMORY_VERSION = 2;

  async function open() {
    if (db && db !== 'fallback') {
      try {
        if (db.version !== MEMORY_VERSION) {
          console.warn('[沙箱] 记忆版本不匹配，清空重建');
          indexedDB.deleteDatabase('XiaoLongRenMemory');
          db = null;
          fallbackMode = false;
        }
      } catch(e) {}
    }
    if (typeof indexedDB === 'undefined') {
      console.warn('[记忆] IndexedDB不可用，降级为内存存储');
      fallbackMode = true;
      return 'fallback';
    }
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VER);
      req.onupgradeneeded = (e) => {
        const d = e.target.result;
        if (!d.objectStoreNames.contains('l1')) d.createObjectStore('l1', {keyPath:'key'});
        if (!d.objectStoreNames.contains('l4')) d.createObjectStore('l4', {keyPath:'id',autoIncrement:true});
        if (!d.objectStoreNames.contains('l5')) d.createObjectStore('l5', {keyPath:'name'});
        if (!d.objectStoreNames.contains('l2')) d.createObjectStore('l2', {keyPath:'id',autoIncrement:true});
        if (!d.objectStoreNames.contains('l2_tags')) d.createObjectStore('l2_tags', {keyPath:'tag'});
      };
      req.onsuccess = (e) => { db = e.target.result; resolve(db); };
      req.onerror = (e) => {
        console.warn('[记忆] IndexedDB打开失败，降级为内存存储:', e.target.error?.message);
        fallbackMode = true;
        resolve('fallback');
      };
    });
  }

  function tx(store, mode='readwrite') {
    if (fallbackMode) return null;
    if (!db || typeof db === 'string') return null;
    return db.transaction(store, mode).objectStore(store);
  }

  async function getL1(key) {
    if (fallbackMode) return fallbackStore.get('l1_' + key) || null;
    if (!db || typeof db === 'string') return null;
    return new Promise(r => { const req=tx('l1','readonly').get(key); req.onsuccess=()=>r(req.result?.value); req.onerror=()=>r(null); });
  }
  async function setL1(key, value) {
    if (fallbackMode) { fallbackStore.set('l1_' + key, value); return true; }
    if (!db || typeof db === 'string') { fallbackStore.set('l1_' + key, value); return true; }
    return new Promise(r => { tx('l1').put({key,value,time:Date.now()}).onsuccess=()=>r(true); });
  }
  async function addL4(patterns) {
    if (fallbackMode) { const k='l4_'+Date.now(); fallbackStore.set(k,{patterns,time:Date.now()}); return true; }
    if (!db || typeof db === 'string') return true;
    return new Promise(r => { tx('l4').add({patterns,time:Date.now()}).onsuccess=()=>r(true); });
  }

  // ============================================================
  // L2 标签索引 — 给记忆打标签，按标签搜索
  // ============================================================
  async function tagL1(key, tag, desc) {
    // l2: 标签→记忆映射
    if (fallbackMode) { fallbackStore.set('l2_'+Date.now(),{key,tag,desc,time:Date.now()}); return true; }
    if (!db || typeof db === 'string') return true;
    return new Promise(r => { tx('l2').add({key,tag,desc:desc||'',time:Date.now()}).onsuccess=()=>r(true); });
  }
  async function searchByTag(tag) {
    if (fallbackMode) {
      const res=[]; fallbackStore.forEach((v,k)=>{if(k.startsWith('l2_')&&v.tag===tag)res.push(v);}); return res;
    }
    if (!db || typeof db === 'string') return [];
    return new Promise(r => {
      const all=[]; const req=tx('l2','readonly').openCursor();
      req.onsuccess=(e)=>{const c=e.target.result;if(c){if(c.value.tag===tag)all.push(c.value);c.continue();}else r(all);};
    });
  }
  async function listTags() {
    if (fallbackMode) {
      const tags=new Set(); fallbackStore.forEach((v,k)=>{if(k.startsWith('l2_'))tags.add(v.tag);}); return [...tags];
    }
    if (!db || typeof db === 'string') return [];
    return new Promise(r => {
      const tags=new Set(); const req=tx('l2','readonly').openCursor();
      req.onsuccess=(e)=>{const c=e.target.result;if(c){tags.add(c.value.tag);c.continue();}else r([...tags]);};
    });
  }
  async function removeTag(id) {
    if (fallbackMode) return true;
    if (!db || typeof db === 'string') return true;
    return new Promise(r => { tx('l2').delete(id).onsuccess=()=>r(true); });
  }
  async function saveSkill(name, desc, rule) {
    if (fallbackMode) { fallbackStore.set('l5_'+name,{name,description:desc,rule,time:Date.now()}); return true; }
    if (!db || typeof db === 'string') { fallbackStore.set('l5_'+name,{name,description:desc,rule,time:Date.now()}); return true; }
    return new Promise(r => { tx('l5').put({name,description:desc,rule,time:Date.now()}).onsuccess=()=>r(true); });
  }
  async function getSkills() {
    if (fallbackMode) { const r=[]; fallbackStore.forEach((v,k)=>{if(k.startsWith('l5_'))r.push(v);}); return r; }
    if (!db || typeof db === 'string') return [];
    return new Promise(r => { const req=tx('l5','readonly').getAll(); req.onsuccess=()=>r(req.result||[]); });
  }
  async function saveConversation(messages) {
    if (fallbackMode || !db || typeof db === 'string') {
      const arr = fallbackStore.get('conversations') || [];
      if (arr.length > 5) arr.shift();
      arr.push({messages,time:Date.now()});
      fallbackStore.set('conversations', arr);
      return true;
    }
    return new Promise(r => {
      const store=tx('conversations');
      const countReq=store.count();
      countReq.onsuccess=async()=>{if(countReq.result>5){const allReq=store.getAllKeys();allReq.onsuccess=()=>{for(let i=0;i<allReq.result.length-5;i++)store.delete(allReq.result[i]);}}};
      store.add({messages,time:Date.now()}).onsuccess=()=>r(true);
    });
  }
  async function loadConversation() {
    if (fallbackMode || !db || typeof db === 'string') {
      const arr=fallbackStore.get('conversations')||[];
      return arr.length?arr[arr.length-1].messages:[];
    }
    return new Promise(r => { const req=tx('conversations','readonly').getAll(); req.onsuccess=()=>{const all=req.result||[]; r(all.length?all[all.length-1].messages:[]);}; });
  }

  return {
    init: open,
    isFallback: ()=>fallbackMode,
    l1: {get:getL1, set:setL1},
    l2: {tag:tagL1, search:searchByTag, tags:listTags, remove:removeTag},
    l4: {add:addL4},
    l5: {save:saveSkill, getAll:getSkills},
    conversations: {save:saveConversation, load:loadConversation},
    l5_skills: {},
    consecutiveErrors: 0,
    async skillify(name,description,rule){await saveSkill(name,description,rule);this.l5_skills[name]={description,rule};return true;},
    async refine(){const s=await getSkills();for(const x of s)this.l5_skills[x.name]={description:x.description,rule:x.rule};return{l5_count:s.length};},
  };
})();

// ============================================================
// Agent 核心循环
// ============================================================
class XiaoLongRen {
  constructor(cfg={}) {
    this.provider=cfg.provider||'deepseek';
    this.model=cfg.model||'deepseek-chat';
    this.apiKey=cfg.apiKey||'';
    this.baseUrl=cfg.baseUrl||'';
    this.maxIter=cfg.maxIter||15;
    this.temp=cfg.temp||0.7;
    this.messages=[];
    this.onThink=cfg.onThink||(()=>{});
    this.onTool=cfg.onTool||(()=>{});
    this.onReply=cfg.onReply||(()=>{});
  }

  async init() {
    await memory.init();
    await memory.refine();
    try{const h=await memory.conversations.load();if(h&&h.length){let clean=h.slice();while(clean.length&&clean[clean.length-1].role==='tool')clean.pop();clean=clean.filter((m,i,arr)=>{if(m.role==='tool'&&i>0){const p=arr[i-1];return p.role==='assistant'&&p.tool_calls;}return true;});this.messages=clean.slice(-40);}}catch(e){}
    return true;
  }

  async run(userMessage, systemPrompt) {
    this.messages.push({role:'user',content:userMessage});
    if(this.messages.length>40)this.messages=this.messages.slice(-40);
    const cleanMessages=this.messages.filter((m,i,arr)=>{if(m.role==='tool'){const p=arr[i-1];return p&&p.role==='assistant'&&p.tool_calls;}return true;});
    const apiMessages=[{role:'system',content:systemPrompt||'你是小龙人，一个能干的AI助手。'},...cleanMessages];
    const allToolDefs=typeof XLR!=='undefined'?XLR.getAllTools():(window._allToolDefs||[]);
    const ep=this.baseUrl||PROVIDERS[this.provider]?.url||'https://api.deepseek.com/v1';
    const url=ep+'/chat/completions';
    const headers={'Content-Type':'application/json','Authorization':'Bearer '+this.apiKey};

    for(let iter=0;iter<this.maxIter;iter++){
      const body=JSON.stringify({model:this.model,messages:apiMessages,tools:allToolDefs.length?allToolDefs:undefined,temperature:this.temp,max_tokens:1024});
      let resp;
      try{resp=await fetch(url,{method:'POST',headers,body,signal:AbortSignal.timeout(30000)});}catch(e){memory.consecutiveErrors++;return'网络不通：'+e.message;}
      if(!resp.ok){
        memory.consecutiveErrors++;
        if(memory.consecutiveErrors>=3){console.warn('[沙箱] 连续3次API错误，清空历史自愈');this.messages=[];memory.consecutiveErrors=0;apiMessages.length=0;apiMessages.push({role:'system',content:systemPrompt||'你是小龙人，一个能干的AI助手。'},{role:'user',content:userMessage});continue;}
        if(resp.status===401)return 'API Key无效，请检查配置';
        if(resp.status===429)return '请求太频繁，稍后再试';
        const errText=await resp.text().catch(()=>'');return 'API错误('+resp.status+'): '+errText.substring(0,200);
      }
      const data=await resp.json();memory.consecutiveErrors=0;
      const choice=data.choices?.[0];if(!choice)return '模型返回为空';
      const msg=choice.message;apiMessages.push(msg);
      if(msg.tool_calls?.length){
        for(const tc of msg.tool_calls){
          const toolName=tc.function.name;let args={};try{args=JSON.parse(tc.function.arguments);}catch(e){}
          this.onTool(toolName,args);
          let result;
          if(typeof XLR!=='undefined'&&XLR.hasTool(toolName)){result=await XLR.execute(toolName,args);}
          else if(window._toolHandlers&&window._toolHandlers[toolName]){result=await window._toolHandlers[toolName](args);}
          else{result=JSON.stringify({error:'未知工具: '+toolName});}
          apiMessages.push({role:'tool',tool_call_id:tc.id,content:typeof result==='string'?result:JSON.stringify(result)});
        }continue;
      }
      const reply=msg.content||'';
      this.messages.push({role:'assistant',content:reply});
      await memory.conversations.save(this.messages);
      this.onReply(reply);
      return reply;
    }
    return '思考轮次已达上限，请简化问题重试。';
  }
}

// 导出全局接口
if(typeof window!=='undefined'){
  window.XiaoLongRen=XiaoLongRen;
  window.memory=memory;
}
