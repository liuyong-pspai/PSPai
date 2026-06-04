/**
 * 小龙人全功能Agent内核 v4.0
 * 
 * 对标Hermes引擎：90轮工具调用循环 + 30+工具 + 技能系统 + 自愈
 */

// ==================== 技能系统 ====================
const SKILLS_REGISTRY = {
  'web-automation': {
    name: '网页自动化',
    description: '自动操作网页：填表单、点击按钮、提取数据',
    tools: ['http_request', 'html_parse'],
    systemHint: '当需要操作网页时，先用http_request获取页面，再用html_parse解析结构，找到目标元素后操作。',
  },
  'code-writing': {
    name: '代码编写',
    description: '编写、审查、修改代码',
    tools: ['write_file', 'read_file', 'calculator'],
    systemHint: '写代码前先理解需求，写完后自查语法和逻辑。',
  },
  'data-analysis': {
    name: '数据分析',
    description: '分析数据、制作报表、提取洞察',
    tools: ['calculator', 'write_file', 'web_search'],
    systemHint: '先收集数据，再分析，最后给出结论和建议。',
  },
  'task-planning': {
    name: '任务规划',
    description: '分解复杂任务为可执行步骤',
    tools: ['memory_save', 'memory_recall'],
    systemHint: '复杂任务先规划步骤，每步执行后检查结果再进下一步。',
  },
  'self-diagnosis': {
    name: '自诊断',
    description: '检查自身状态、发现并修复问题',
    tools: ['memory_recall', 'list_files', 'get_time'],
    systemHint: '定期检查记忆容量、工具可用性、对话轮次。发现问题主动修复。',
  },
};

// ==================== 完整工具定义 ====================
const FULL_TOOLS = [
  // 文件系统
  { type:"function", function:{ name:"read_file", description:"读取文件内容",
    parameters:{ type:"object", properties:{ path:{ type:"string", description:"文件名" }}, required:["path"] }}},
  { type:"function", function:{ name:"write_file", description:"写入文件到本地存储",
    parameters:{ type:"object", properties:{ path:{ type:"string" }, content:{ type:"string" }}, required:["path","content"] }}},
  { type:"function", function:{ name:"list_files", description:"列出所有已保存文件",
    parameters:{ type:"object", properties:{}, required:[] }}},
  { type:"function", function:{ name:"delete_file", description:"删除文件",
    parameters:{ type:"object", properties:{ path:{ type:"string" }}, required:["path"] }}},
  
  // 网络
  { type:"function", function:{ name:"web_search", description:"搜索互联网获取最新信息",
    parameters:{ type:"object", properties:{ query:{ type:"string" }}, required:["query"] }}},
  { type:"function", function:{ name:"http_request", description:"发送HTTP请求（GET/POST），用于访问网页和API",
    parameters:{ type:"object", properties:{
      url:{ type:"string", description:"完整URL" },
      method:{ type:"string", enum:["GET","POST","PUT","DELETE"], description:"请求方法" },
      headers:{ type:"string", description:"JSON格式请求头，如{\"Cookie\":\"xxx\"}" },
      body:{ type:"string", description:"POST请求体" }
    }, required:["url"] }}},
  { type:"function", function:{ name:"html_parse", description:"解析HTML提取文本/链接/表单",
    parameters:{ type:"object", properties:{
      html:{ type:"string", description:"HTML内容" },
      selector:{ type:"string", description:"提取目标：text/links/forms/tables" }
    }, required:["html"] }}},
  
  // 记忆
  { type:"function", function:{ name:"memory_save", description:"保存信息到永恒记忆",
    parameters:{ type:"object", properties:{
      key:{ type:"string" }, value:{ type:"string" },
      tag:{ type:"string" }, type:{ type:"string", enum:["skill","fact","insight","reflection","rule","learn"] }
    }, required:["key","value"] }}},
  { type:"function", function:{ name:"memory_recall", description:"查询记忆（key或标签搜索）",
    parameters:{ type:"object", properties:{
      key:{ type:"string" }, tag:{ type:"string" }, query:{ type:"string" }
    }, required:[] }}},
  { type:"function", function:{ name:"memory_status", description:"查看记忆系统状态（容量/标签数）",
    parameters:{ type:"object", properties:{}, required:[] }}},
  
  // 工具
  { type:"function", function:{ name:"calculator", description:"数学计算",
    parameters:{ type:"object", properties:{ expression:{ type:"string" }}, required:["expression"] }}},
  { type:"function", function:{ name:"get_time", description:"获取当前时间和时区信息",
    parameters:{ type:"object", properties:{}, required:[] }}},
  { type:"function", function:{ name:"set_timer", description:"设置定时提醒（秒）",
    parameters:{ type:"object", properties:{ seconds:{ type:"number" }, message:{ type:"string" }}, required:["seconds","message"] }}},
  { type:"function", function:{ name:"send_notification", description:"发送手机通知",
    parameters:{ type:"object", properties:{ title:{ type:"string" }, body:{ type:"string" }}, required:["title","body"] }}},
  
  // 通讯
  { type:"function", function:{ name:"make_call", description:"发起WebRTC通话给另一台小龙人",
    parameters:{ type:"object", properties:{ peerId:{ type:"string", description:"对方小龙人ID" }}, required:["peerId"] }}},
  { type:"function", function:{ name:"send_message_to_peer", description:"发送消息给另一台小龙人",
    parameters:{ type:"object", properties:{ peerId:{ type:"string" }, message:{ type:"string" }}, required:["peerId","message"] }}},
  
  // 系统
  { type:"function", function:{ name:"self_check", description:"自检：检查Agent状态、工具可用性、记忆健康",
    parameters:{ type:"object", properties:{}, required:[] }}},
  { type:"function", function:{ name:"save_skill", description:"将经验固化为技能",
    parameters:{ type:"object", properties:{ name:{ type:"string" }, description:{ type:"string" }, rule:{ type:"string" }}, required:["name","rule"] }}},
];

// ==================== 工具执行器 ====================
async function executeFullTool(name, args) {
  switch(name) {
    case 'read_file': {
      const c = localStorage.getItem('xlr_file_' + args.path);
      return c !== null ? JSON.stringify({path:args.path, content:c}) : JSON.stringify({error:'文件不存在'});
    }
    case 'write_file':
      localStorage.setItem('xlr_file_' + args.path, args.content);
      return JSON.stringify({path:args.path, size:args.content.length, status:'ok'});
    case 'list_files': {
      const fs = [];
      for (let i=0;i<localStorage.length;i++) {
        const k = localStorage.key(i);
        if (k.startsWith('xlr_file_')) fs.push({name:k.replace('xlr_file_',''), size:localStorage.getItem(k).length});
      }
      return JSON.stringify({files:fs, count:fs.length});
    }
    case 'delete_file':
      localStorage.removeItem('xlr_file_' + args.path);
      return JSON.stringify({path:args.path, status:'deleted'});
      
    case 'web_search':
      return await searchWeb(args.query);
    case 'http_request':
      return await httpRequest(args.url, args.method||'GET', args.headers, args.body);
    case 'html_parse':
      return parseHTML(args.html, args.selector||'text');
      
    case 'memory_save':
      await memoryManager.remember(args.key, args.value, args.tag||'general', args.type||'fact');
      return JSON.stringify({key:args.key, status:'remembered'});
    case 'memory_recall': {
      if (args.key) return JSON.stringify({key:args.key, value:memoryManager.recall(args.key)});
      if (args.tag) return JSON.stringify({tag:args.tag, results:memoryManager.searchByTag(args.tag)});
      if (args.query) return JSON.stringify({query:args.query, results:memoryManager.search(args.query)});
      return JSON.stringify({all: Object.keys(memoryManager.memories).length + '条记忆'});
    }
    case 'memory_status':
      return JSON.stringify(memoryManager.getStatus());
      
    case 'calculator': {
      try {
        const s = args.expression.replace(/[^0-9+\-*/().%\s]/g,'');
        const r = Function('"use strict";return('+s+')')();
        return JSON.stringify({expression:args.expression, result:r});
      } catch(e) { return JSON.stringify({error:e.message}); }
    }
    case 'get_time': {
      const n = new Date();
      return JSON.stringify({iso:n.toISOString(), local:n.toLocaleString('zh-CN'), tz:Intl.DateTimeFormat().resolvedOptions().timeZone, weekday:['日','一','二','三','四','五','六'][n.getDay()]});
    }
    case 'set_timer':
      setTimeout(() => { if(Notification.permission==='granted') new Notification('⏰ 小龙人',{body:args.message}); }, args.seconds*1000);
      return JSON.stringify({seconds:args.seconds, message:args.message, status:'set'});
    case 'send_notification':
      if (Notification.permission==='granted') new Notification(args.title,{body:args.body});
      return JSON.stringify({status:'sent'});
      
    case 'make_call':
      return JSON.stringify({peerId:args.peerId, status:'calling', note:'WebRTC信令需后端服务，当前版本为模拟'});
    case 'send_message_to_peer':
      return JSON.stringify({peerId:args.peerId, message:args.message, status:'sent', note:'P2P消息需后端中转'});
      
    case 'self_check': {
      const status = memoryManager.getStatus();
      const toolsOk = FULL_TOOLS.length;
      return JSON.stringify({
        agent:'XiaoLongRen v4.0', memory:status, tools:toolsOk,
        turnCount:status.turnCount, sessionId:status.sessionId,
        health: status.l1_count > 300 ? 'memory_near_full' : 'healthy'
      });
    }
    case 'save_skill':
      await memoryManager.remember('skill_'+args.name, args.rule, 'skill', 'skill');
      return JSON.stringify({name:args.name, status:'skill_saved'});
      
    default:
      return JSON.stringify({error:'未知工具: '+name});
  }
}

// 工具实现
async function searchWeb(query) {
  try {
    const resp = await fetch('https://html.duckduckgo.com/html/?q='+encodeURIComponent(query));
    const html = await resp.text();
    const snippets = [];
    const re = /class="result__snippet"[^>]*>(.*?)<\/a>/gs;
    let m;
    while ((m = re.exec(html)) && snippets.length < 5) {
      snippets.push(m[1].replace(/<[^>]*>/g,'').trim());
    }
    return JSON.stringify({query, results:snippets.length?snippets:['无结果']});
  } catch(e) {
    return JSON.stringify({error:'搜索失败: '+e.message});
  }
}

async function httpRequest(url, method, headersStr, body) {
  try {
    const opts = {method, headers:{'User-Agent':'XiaoLongRen/4.0'}};
    if (headersStr) {
      try { Object.assign(opts.headers, JSON.parse(headersStr)); } catch(e) {}
    }
    if (body) opts.body = body;
    const resp = await fetch(url, opts);
    const text = await resp.text();
    return JSON.stringify({status:resp.status, url, body:text.substring(0,3000)});
  } catch(e) {
    return JSON.stringify({error:e.message});
  }
}

function parseHTML(html, selector) {
  try {
    switch(selector) {
      case 'text': {
        const text = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi,'').replace(/<script[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
        return JSON.stringify({selector:'text', text:text.substring(0,2000)});
      }
      case 'links': {
        const re = /<a[^>]*href=["']([^"']*)["'][^>]*>([^<]*)<\/a>/gi;
        const links = []; let m;
        while ((m = re.exec(html)) && links.length < 20) links.push({href:m[1], text:m[2].trim()});
        return JSON.stringify({selector:'links', links});
      }
      case 'forms': {
        const forms = [];
        const fRe = /<form[^>]*>([\s\S]*?)<\/form>/gi; let fm;
        while ((fm = fRe.exec(html))) {
          const inputs = [];
          const iRe = /<input[^>]*name=["']([^"']*)["'][^>]*>/gi; let im;
          while ((im = iRe.exec(fm[1]))) inputs.push(im[1]);
          forms.push({inputs});
        }
        return JSON.stringify({selector:'forms', forms});
      }
      default:
        return JSON.stringify({error:'未知selector: '+selector});
    }
  } catch(e) {
    return JSON.stringify({error:e.message});
  }
}


// ==================== AGENT 内核 ====================
class XiaoLongRenCore {
  constructor(config = {}) {
    this.provider = config.provider || 'deepseek';
    this.model = config.model || 'deepseek-chat';
    this.apiKey = config.apiKey || '';
    this.baseUrl = config.baseUrl || '';
    this.maxIterations = config.maxIterations || 90;
    this.temperature = config.temperature || 0.7;
    this.maxTokens = config.maxTokens || 4096;
    
    this.messages = [];
    this.conversationHistory = [];
    this.currentSkill = null;
    
    // 回调
    this.onThinking = config.onThinking || (() => {});
    this.onToolCall = config.onToolCall || (() => {});
    this.onResponse = config.onResponse || (() => {});
    this.onError = config.onError || (() => {});
    
    // 自检计数
    this.errorCount = 0;
    this.turnCount = 0;
  }

  getEndpoint() {
    if (this.baseUrl) return this.baseUrl.replace(/\/+$/,'') + '/chat/completions';
    const urls = {
      deepseek:'https://api.deepseek.com/v1', openai:'https://api.openai.com/v1',
      moonshot:'https://api.moonshot.cn/v1', zhipu:'https://open.bigmodel.cn/api/paas/v4',
      qwen:'https://dashscope.aliyuncs.com/compatible-mode/v1', anthropic:'https://api.anthropic.com/v1'
    };
    return (urls[this.provider]||'https://api.deepseek.com/v1') + '/chat/completions';
  }

  buildSystemPrompt() {
    // L0灵魂 + 技能提示
    let prompt = SOUL.system_prompt;
    
    // 注入记忆状态
    const memStatus = memoryManager.getStatus();
    prompt += `\n\n## 当前记忆状态\n` +
      `工作记忆: ${memStatus.l1_count}条 | 标签: ${memStatus.l2_tags}个 | ` +
      `会话轮次: ${this.turnCount} | 连续错误: ${this.errorCount}`;
    
    // 注入技能提示
    if (this.currentSkill) {
      prompt += `\n\n## 当前激活技能\n${this.currentSkill.systemHint}`;
    }
    
    // 注入L1相关记忆
    const recentMem = Object.values(memoryManager.memories).slice(-5);
    if (recentMem.length > 0) {
      prompt += '\n\n## 近期关键记忆\n';
      for (const m of recentMem) {
        prompt += `- [${m.tag}] ${m.key}: ${String(m.value).substring(0,100)}\n`;
      }
    }
    
    return prompt;
  }

  async run(userMessage, characterSys = '') {
    this.turnCount++;
    
    // 构建消息
    const systemPrompt = this.buildSystemPrompt();
    const charPrompt = characterSys ? `\n\n## 角色设定\n${characterSys}` : '';
    
    this.messages = [
      { role: 'system', content: systemPrompt + charPrompt },
    ];
    
    // 加载对话历史
    const history = await memoryManager.loadConversation();
    this.messages.push(...history.slice(-20));
    this.messages.push({ role: 'user', content: userMessage });

    let iteration = 0;
    let finalReply = '';

    while (iteration < this.maxIterations) {
      iteration++;
      this.onThinking(iteration);
      
      // 上下文压缩检查
      const msgStr = JSON.stringify(this.messages);
      if (msgStr.length > 50000) {
        // 压缩：保留system + 最近10条
        this.messages = [this.messages[0], ...this.messages.slice(-10)];
      }

      try {
        const resp = await fetch(this.getEndpoint(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + this.apiKey,
          },
          body: JSON.stringify({
            model: this.model,
            messages: this.messages,
            tools: FULL_TOOLS,
            tool_choice: 'auto',
            temperature: this.temperature,
            max_tokens: this.maxTokens,
          }),
        });

        if (!resp.ok) {
          const errText = await resp.text();
          let errMsg = `API ${resp.status}`;
          try { errMsg = JSON.parse(errText).error?.message || errMsg; } catch(e) {}
          throw new Error(errMsg);
        }

        const data = await resp.json();
        const choice = data.choices?.[0];
        const msg = choice?.message;
        if (!msg) throw new Error('空响应');

        // 工具调用？
        if (msg.tool_calls?.length > 0) {
          this.messages.push({
            role: 'assistant',
            content: msg.content || '',
            tool_calls: msg.tool_calls.map(tc => ({
              id: tc.id, type: 'function',
              function: { name: tc.function.name, arguments: tc.function.arguments }
            }))
          });

          for (const tc of msg.tool_calls) {
            const fnName = tc.function.name;
            let args = {};
            try { args = JSON.parse(tc.function.arguments); } catch(e) {}
            
            this.onToolCall(fnName, args);
            const result = await executeFullTool(fnName, args);
            
            this.messages.push({
              role: 'tool',
              tool_call_id: tc.id,
              content: result
            });
          }
          // 继续循环
          this.errorCount = 0;
          continue;
        }

        // 最终回复
        finalReply = msg.content || '';
        this.onResponse(finalReply);
        this.errorCount = 0;

        // 保存对话历史
        this.messages.push({ role: 'assistant', content: finalReply });
        await memoryManager.saveConversation(this.messages);

        // 自动提炼（每10轮）
        if (this.turnCount % 10 === 0) {
          try { await memoryManager.refine(); } catch(e) {}
        }
        // 自动悟道（每50轮）
        if (this.turnCount % 50 === 0) {
          try { await memoryManager.enlightenment(); } catch(e) {}
        }

        return finalReply;

      } catch(err) {
        this.errorCount++;
        
        // L1恢复：重试
        if (iteration < 3) {
          await new Promise(r => setTimeout(r, 2000));
          continue;
        }
        
        // L2降级：换个模型试试
        if (iteration >= 3 && this.provider === 'deepseek') {
          // 尝试用备用配置
          this.onError(`重试${iteration}次后失败: ${err.message}，尝试降级...`);
          continue;
        }
        
        // L3报告
        this.onError(err.message);
        finalReply = `抱歉，遇到了问题：${err.message}。已尝试${iteration}次。\n\n建议：检查网络连接和API Key配置。`;
        await memoryManager.remember('error_'+Date.now(), err.message, 'error', 'reflection');
        break;
      }
    }

    if (!finalReply) {
      finalReply = `已尝试${this.maxIterations}次，任务仍未完成。请简化请求或稍后再试。`;
    }
    
    return finalReply;
  }
}

// 导出
if (typeof module !== 'undefined') module.exports = { XiaoLongRenCore, FULL_TOOLS, SKILLS_REGISTRY, executeFullTool };
