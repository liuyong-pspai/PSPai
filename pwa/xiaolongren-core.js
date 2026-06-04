/**
 * 小龙人内核 v6.0 — 插件架构
 * 
 * 核心职责：Agent循环 + 记忆系统 + 配置管理
 * 工具系统：全部由插件提供（通过XLR plugin-loader动态加载）
 * 
 * 加载顺序：
 *   1. plugin-loader.js  → XLR全局对象
 *   2. plugins/*.js      → 注册工具+处理器
 *   3. xiaolongren-core.js（本文件） → 内核初始化
 */

// ============================================================
// 八层永生记忆 (IndexedDB)
// ============================================================
const memory = (function() {
  let db = null;
  const DB_NAME = 'xiaolongren_memory';
  const DB_VER = 6;

  async function open() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VER);
      req.onupgradeneeded = (e) => {
        const d = e.target.result;
        if (!d.objectStoreNames.contains('l1')) d.createObjectStore('l1', {keyPath:'key'});
        if (!d.objectStoreNames.contains('l4')) d.createObjectStore('l4', {keyPath:'id',autoIncrement:true});
        if (!d.objectStoreNames.contains('l5')) d.createObjectStore('l5', {keyPath:'name'});
        if (!d.objectStoreNames.contains('conversations')) d.createObjectStore('conversations', {keyPath:'id',autoIncrement:true});
      };
      req.onsuccess = (e) => { db = e.target.result; resolve(db); };
      req.onerror = (e) => reject(e.target.error);
    });
  }

  function tx(store, mode='readwrite') { return db.transaction(store, mode).objectStore(store); }

  async function getL1(key) {
    return new Promise(r => { const req = tx('l1','readonly').get(key); req.onsuccess=()=>r(req.result?.value); req.onerror=()=>r(null); });
  }
  async function setL1(key, value) {
    return new Promise(r => { tx('l1').put({key,value,time:Date.now()}).onsuccess=()=>r(true); });
  }
  async function addL4(patterns) {
    return new Promise(r => { tx('l4').add({patterns,time:Date.now()}).onsuccess=()=>r(true); });
  }
  async function saveSkill(name, desc, rule) {
    return new Promise(r => { tx('l5').put({name,description:desc,rule,time:Date.now()}).onsuccess=()=>r(true); });
  }
  async function getSkills() {
    return new Promise(r => { const req=tx('l5','readonly').getAll(); req.onsuccess=()=>r(req.result||[]); });
  }
  async function saveConversation(messages) {
    return new Promise(r => {
      const store = tx('conversations');
      // Keep last 5 conversations
      const countReq = store.count();
      countReq.onsuccess = async () => {
        if (countReq.result > 5) {
          const allReq = store.getAllKeys();
          allReq.onsuccess = () => {
            for (let i = 0; i < allReq.result.length - 5; i++) store.delete(allReq.result[i]);
          };
        }
      };
      store.add({messages,time:Date.now()}).onsuccess=()=>r(true);
    });
  }
  async function loadConversation() {
    return new Promise(r => {
      const req = tx('conversations','readonly').getAll();
      req.onsuccess = () => { const all = req.result||[]; r(all.length?all[all.length-1].messages:[]); };
    });
  }

  return {
    init: open,
    l1: { get: getL1, set: setL1 },
    l4: { add: addL4 },
    l5: { save: saveSkill, getAll: getSkills },
    conversations: { save: saveConversation, load: loadConversation },
    l5_skills: {},  // 内存缓存
    consecutiveErrors: 0,
    async getStatus() {
      await open();
      const convCount = await new Promise(r => { tx('conversations','readonly').count().onsuccess=e=>r(e.target.result); });
      const skillCount = await new Promise(r => { tx('l5','readonly').count().onsuccess=e=>r(e.target.result); });
      return { l1: 'ok', l4: 'ok', l5: skillCount, conversations: convCount };
    },
    async autoHealIfNeeded() {
      if (this.consecutiveErrors >= 3) {
        this.consecutiveErrors = 0;
        return { healed: true, message: '连续错误计数已清零' };
      }
      return { healed: false, message: '无需自愈' };
    },
    async skillify(name, description, rule) {
      await saveSkill(name, description, rule);
      this.l5_skills[name] = { description, rule };
      return true;
    },
    async refine() {
      // L4→L5 check
      const skills = await getSkills();
      for (const s of skills) this.l5_skills[s.name] = { description: s.description, rule: s.rule };
      return { l5_count: skills.length };
    },
    enlighten() {
      return this.consecutiveErrors >= 3 ? '⚠️ 连续错误≥3，建议自愈' : null;
    },
  };
})();


// ============================================================
// 配置管理
// ============================================================
const PROVIDERS = {
  deepseek:  { name:'DeepSeek',  url:'https://api.deepseek.com/v1' },
  openai:    { name:'OpenAI',    url:'https://api.openai.com/v1' },
  anthropic: { name:'Anthropic', url:'https://api.anthropic.com/v1' },
  moonshot:  { name:'Moonshot',  url:'https://api.moonshot.cn/v1' },
  zhipu:     { name:'智谱GLM',   url:'https://open.bigmodel.cn/api/paas/v4' },
  qwen:      { name:'通义千问',   url:'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  custom:    { name:'自定义',     url:'' },
};

function getConfig() {
  try {
    const raw = localStorage.getItem('xiaolongren_config');
    return raw ? JSON.parse(raw) : null;
  } catch(e) { return null; }
}

function getEndpoint(provider) {
  const cfg = getConfig();
  if (cfg?.base_url) return cfg.base_url;
  return (PROVIDERS[provider] || PROVIDERS.deepseek).url;
}


// ============================================================
// Agent 核心循环
// ============================================================
class XiaoLongRen {
  constructor(cfg = {}) {
    this.provider = cfg.provider || 'deepseek';
    this.model = cfg.model || 'deepseek-chat';
    this.apiKey = cfg.apiKey || '';
    this.baseUrl = cfg.baseUrl || '';
    this.maxIter = cfg.maxIter || 15;
    this.temp = cfg.temp || 0.7;
    this.messages = [];
    this.onThink = cfg.onThink || (()=>{});
    this.onTool = cfg.onTool || (()=>{});
    this.onReply = cfg.onReply || (()=>{});
    this.onErr = cfg.onErr || (()=>{});
  }

  async init() {
    await memory.init();
    await memory.refine();
    // 加载会话历史
    try {
      const hist = await memory.conversations.load();
      if (hist && hist.length) this.messages = hist.slice(-40);
    } catch(e) {}
    return true;
  }

  async chat(userMessage, systemPrompt) {
    this.messages.push({ role: 'user', content: userMessage });
    if (this.messages.length > 40) this.messages = this.messages.slice(-40);

    const apiMessages = [
      { role: 'system', content: systemPrompt || '你是小龙人，一个能干的AI助手。' },
      ...this.messages,
    ];

    const allToolDefs = XLR.getAllTools();
    const ep = this.baseUrl || getEndpoint(this.provider);
    const url = ep + '/chat/completions';
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + this.apiKey,
    };

    for (let iter = 0; iter < this.maxIter; iter++) {
      const body = JSON.stringify({
        model: this.model,
        messages: apiMessages,
        tools: allToolDefs.length ? allToolDefs : undefined,
        temperature: this.temp,
        max_tokens: 1024,
      });

      let resp;
      try {
        resp = await fetch(url, { method: 'POST', headers, body, signal: AbortSignal.timeout(30000) });
      } catch(e) {
        memory.consecutiveErrors++;
        return '网络不通：' + e.message;
      }

      if (!resp.ok) {
        const errText = await resp.text().catch(()=>'');
        memory.consecutiveErrors++;
        if (resp.status === 401) return 'API Key无效，请检查配置';
        if (resp.status === 429) return '请求太频繁，稍后再试';
        return 'API错误('+resp.status+'): ' + errText.substring(0,200);
      }

      const data = await resp.json();
      memory.consecutiveErrors = 0;
      const choice = data.choices?.[0];
      if (!choice) return '模型返回为空';

      const msg = choice.message;
      apiMessages.push(msg);

      // 如果有工具调用
      if (msg.tool_calls?.length) {
        for (const tc of msg.tool_calls) {
          const toolName = tc.function.name;
          let args = {};
          try { args = JSON.parse(tc.function.arguments); } catch(e) {}

          this.onTool(toolName, args);

          // 优先走插件体系
          let result;
          if (XLR.hasTool(toolName)) {
            result = await XLR.execute(toolName, args);
          } else {
            result = JSON.stringify({ error: '未知工具: ' + toolName });
          }

          apiMessages.push({
            role: 'tool',
            tool_call_id: tc.id,
            content: typeof result === 'string' ? result : JSON.stringify(result),
          });
        }
        continue; // 继续循环，让LLM处理工具结果
      }

      // 纯文本回复
      const reply = msg.content || '';
      this.messages.push({ role: 'assistant', content: reply });
      await memory.conversations.save(this.messages);
      this.onReply(reply);
      return reply;
    }

    return '思考轮次已达上限，请简化问题重试。';
  }
}


// ============================================================
// 内核初始化（由mobile.html调用）
// ============================================================
async function initKernel() {
  console.log('[内核] 初始化...');

  // 1. 初始化记忆
  await memory.init();

  // 2. 初始化插件体系
  const pluginResults = await XLR.initAll({ memory, getConfig });
  console.log('[内核] 插件加载完成:', pluginResults.map(p=>p.name+'='+p.status).join(', '));

  // 3. 报告
  const report = XLR.report();
  console.log(`[内核] ${report.totalPlugins}个插件, ${report.totalTools}个工具就绪`);
  console.log('[内核] 插件详情:', JSON.stringify(report.plugins));

  return report;
}


// ============================================================
// 便捷入口：简化版Agent调用（用于mobile.html）
// ============================================================
let globalAgent = null;

async function runAgent(userText, systemPrompt) {
  const cfg = getConfig();
  if (!cfg?.api_key) throw new Error('未配置API Key');

  if (!globalAgent) {
    globalAgent = new XiaoLongRen({
      provider: cfg.provider || 'deepseek',
      model: cfg.model || 'deepseek-chat',
      apiKey: cfg.api_key,
      baseUrl: cfg.base_url || '',
    });
    await globalAgent.init();
  }

  return await globalAgent.chat(userText, systemPrompt);
}

console.log('[内核] xiaolongren-core.js v6.0 加载完成（插件架构）');
