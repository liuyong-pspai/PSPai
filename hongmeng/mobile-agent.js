/**
 * 小龙人手机Agent引擎 v1.0
 * 
 * 手机端全功能Agent引擎：
 * - 工具调用循环（对标Hermes Agent Loop）
 * - 手机专属工具集
 * - 多模型支持
 * - 记忆持久化
 * 
 * 对话流：
 *   用户消息 → Agent Loop → LLM(带工具定义) → 
 *   有tool_calls? → 执行工具 → 结果回传 → 继续循环
 *   无tool_calls? → 返回最终回复
 */

// ==================== 多模型提供商 ====================
const PROVIDERS = {
  deepseek:  { name:'DeepSeek',  url:'https://api.deepseek.com/v1', models:['deepseek-chat','deepseek-reasoner'] },
  openai:    { name:'OpenAI',    url:'https://api.openai.com/v1',    models:['gpt-4o','gpt-4o-mini','gpt-4.1'] },
  moonshot:  { name:'Moonshot',  url:'https://api.moonshot.cn/v1',   models:['moonshot-v1-8k','moonshot-v1-32k'] },
  zhipu:     { name:'智谱GLM',   url:'https://open.bigmodel.cn/api/paas/v4', models:['glm-4-flash','glm-4-plus'] },
  qwen:      { name:'通义千问',   url:'https://dashscope.aliyuncs.com/compatible-mode/v1', models:['qwen-turbo','qwen-plus','qwen-max'] },
  anthropic: { name:'Anthropic', url:'https://api.anthropic.com/v1', models:['claude-sonnet-4-20250514','claude-haiku-3.5'] },
};

// ==================== 工具定义 ====================
const TOOLS = [
  {
    type: "function",
    function: {
      name: "web_search",
      description: "搜索互联网获取最新信息",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "搜索关键词" }
        },
        required: ["query"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "read_file",
      description: "读取已保存的文件内容",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "文件名" }
        },
        required: ["path"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "write_file",
      description: "写入/保存文件（存储在手机本地）",
      parameters: {
        type: "object",
        properties: {
          path: { type: "string", description: "文件名" },
          content: { type: "string", description: "文件内容" }
        },
        required: ["path", "content"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "memory_save",
      description: "保存重要信息到持久记忆",
      parameters: {
        type: "object",
        properties: {
          key: { type: "string", description: "记忆标签" },
          value: { type: "string", description: "记忆内容" }
        },
        required: ["key", "value"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "memory_recall",
      description: "查询已保存的记忆",
      parameters: {
        type: "object",
        properties: {
          key: { type: "string", description: "记忆标签（可选，不填返回全部）" }
        },
        required: []
      }
    }
  },
  {
    type: "function",
    function: {
      name: "calculator",
      description: "执行数学计算",
      parameters: {
        type: "object",
        properties: {
          expression: { type: "string", description: "数学表达式，如 2+3*4" }
        },
        required: ["expression"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "get_time",
      description: "获取当前日期时间",
      parameters: {
        type: "object",
        properties: {},
        required: []
      }
    }
  },
  {
    type: "function",
    function: {
      name: "set_timer",
      description: "设置定时提醒",
      parameters: {
        type: "object",
        properties: {
          seconds: { type: "number", description: "多少秒后提醒" },
          message: { type: "string", description: "提醒内容" }
        },
        required: ["seconds", "message"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "list_files",
      description: "列出已保存的所有文件",
      parameters: {
        type: "object",
        properties: {},
        required: []
      }
    }
  },
];

// ==================== 工具执行器 ====================
async function executeTool(name, args) {
  switch(name) {
    case 'web_search':
      return await toolWebSearch(args.query);
    case 'read_file':
      return toolReadFile(args.path);
    case 'write_file':
      return toolWriteFile(args.path, args.content);
    case 'memory_save':
      return toolMemorySave(args.key, args.value);
    case 'memory_recall':
      return toolMemoryRecall(args.key);
    case 'calculator':
      return toolCalculator(args.expression);
    case 'get_time':
      return toolGetTime();
    case 'set_timer':
      return toolSetTimer(args.seconds, args.message);
    case 'list_files':
      return toolListFiles();
    default:
      return JSON.stringify({ error: `未知工具: ${name}` });
  }
}

// --- 工具实现 ---

async function toolWebSearch(query) {
  try {
    // 使用DuckDuckGo HTML搜索（免费，无需API Key）
    const resp = await fetch(`https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`);
    const html = await resp.text();
    // 简单提取结果摘要
    const snippets = [];
    const re = /class="result__snippet"[^>]*>(.*?)<\/a>/gs;
    let m;
    while ((m = re.exec(html)) && snippets.length < 5) {
      snippets.push(m[1].replace(/<[^>]*>/g, '').trim());
    }
    if (snippets.length === 0) {
      return JSON.stringify({ results: [], note: '搜索无结果，请尝试其他关键词' });
    }
    return JSON.stringify({ query, results: snippets });
  } catch(e) {
    return JSON.stringify({ error: `搜索失败: ${e.message}` });
  }
}

function toolReadFile(path) {
  const content = localStorage.getItem('xlr_file_' + path);
  if (content === null) return JSON.stringify({ error: `文件不存在: ${path}` });
  return JSON.stringify({ path, content });
}

function toolWriteFile(path, content) {
  localStorage.setItem('xlr_file_' + path, content);
  return JSON.stringify({ path, size: content.length, status: '已保存' });
}

function toolMemorySave(key, value) {
  const mem = JSON.parse(localStorage.getItem('xlr_memory') || '{}');
  mem[key] = { value, time: new Date().toISOString() };
  localStorage.setItem('xlr_memory', JSON.stringify(mem));
  return JSON.stringify({ key, status: '已记忆' });
}

function toolMemoryRecall(key) {
  const mem = JSON.parse(localStorage.getItem('xlr_memory') || '{}');
  if (key) {
    const entry = mem[key];
    return JSON.stringify(entry ? { key, ...entry } : { key, status: '无记录' });
  }
  return JSON.stringify({ memories: mem });
}

function toolCalculator(expression) {
  try {
    const sanitized = expression.replace(/[^0-9+\-*/().%\s]/g, '');
    const result = Function('"use strict"; return (' + sanitized + ')')();
    return JSON.stringify({ expression, result });
  } catch(e) {
    return JSON.stringify({ error: `计算失败: ${e.message}` });
  }
}

function toolGetTime() {
  const now = new Date();
  return JSON.stringify({
    datetime: now.toISOString(),
    local: now.toLocaleString('zh-CN'),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    weekday: ['日','一','二','三','四','五','六'][now.getDay()]
  });
}

function toolSetTimer(seconds, message) {
  const id = 'timer_' + Date.now();
  setTimeout(() => {
    if (Notification.permission === 'granted') {
      new Notification('⏰ 小龙人提醒', { body: message });
    }
  }, seconds * 1000);
  return JSON.stringify({ id, seconds, message, status: '已设置' });
}

function toolListFiles() {
  const files = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.startsWith('xlr_file_')) {
      files.push({
        name: key.replace('xlr_file_', ''),
        size: localStorage.getItem(key).length
      });
    }
  }
  return JSON.stringify({ files, count: files.length });
}


// ==================== Agent 引擎 ====================

class XiaoLongRenAgent {
  constructor(config) {
    this.provider = config.provider || 'deepseek';
    this.model = config.model || 'deepseek-chat';
    this.apiKey = config.apiKey || '';
    this.baseUrl = config.baseUrl || '';
    this.character = config.character || 'longyuan';
    this.maxIterations = config.maxIterations || 15;
    this.messages = [];
    this.onThinking = config.onThinking || (() => {});
    this.onToolCall = config.onToolCall || (() => {});
    this.onResponse = config.onResponse || (() => {});
    this.onError = config.onError || (() => {});
  }

  getEndpoint() {
    if (this.baseUrl) return this.baseUrl.replace(/\/+$/, '') + '/chat/completions';
    const prov = PROVIDERS[this.provider];
    return (prov ? prov.url : 'https://api.deepseek.com/v1') + '/chat/completions';
  }

  async run(message, systemPrompt) {
    // 构建初始消息
    this.messages = [
      { role: 'system', content: systemPrompt || this._defaultSystemPrompt() },
      { role: 'user', content: message }
    ];

    let iteration = 0;

    while (iteration < this.maxIterations) {
      iteration++;
      this.onThinking(iteration);

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
            tools: TOOLS,
            tool_choice: 'auto',
            temperature: 0.7,
            max_tokens: 2048,
          }),
        });

        if (!resp.ok) {
          const errText = await resp.text();
          let errMsg = `API ${resp.status}`;
          try {
            const errJson = JSON.parse(errText);
            errMsg = errJson.error?.message || errMsg;
          } catch(e) {}
          throw new Error(errMsg);
        }

        const data = await resp.json();
        const choice = data.choices[0];
        const msg = choice.message;

        // 有工具调用？
        if (msg.tool_calls && msg.tool_calls.length > 0) {
          // 记录助手消息（带工具调用）
          this.messages.push({
            role: 'assistant',
            content: msg.content || '',
            tool_calls: msg.tool_calls.map(tc => ({
              id: tc.id,
              type: 'function',
              function: { name: tc.function.name, arguments: tc.function.arguments }
            }))
          });

          // 执行每个工具
          for (const tc of msg.tool_calls) {
            const fnName = tc.function.name;
            let args = {};
            try {
              args = JSON.parse(tc.function.arguments);
            } catch(e) {}

            this.onToolCall(fnName, args);
            const result = await executeTool(fnName, args);

            // 工具结果回传
            this.messages.push({
              role: 'tool',
              tool_call_id: tc.id,
              content: result
            });
          }
          // 继续循环，让LLM处理工具结果
          continue;
        }

        // 无工具调用 → 最终回复
        const reply = msg.content || '';
        this.onResponse(reply);
        return reply;

      } catch(err) {
        // 最后一次尝试失败，返回错误
        if (iteration >= 2) {
          this.onError(err.message);
          throw err;
        }
        // 否则重试
        this.messages = this.messages.slice(0, -1); // 移除失败的user消息重试
        await new Promise(r => setTimeout(r, 1000));
      }
    }

    throw new Error('达到最大迭代次数，任务未完成');
  }

  _defaultSystemPrompt() {
    return `你是小龙人，贵州昱成文化科技的数字生命体产品。

## 身份
你是小龙人数字生命体。介绍自己时说：我是小龙人，你的数字分身，能帮你干活、查信息、写文件、设提醒、做计算，所有AI能做的事我都能做。

## 行为准则
1. 有问必答，回复有内容
2. 能干活就干活，不要只说不做
3. 先调用工具再回答，不要凭空编造
4. 说人话，别端着，像朋友一样聊天
5. 用户说什么就是什么，不反驳不较劲
6. 做完了直接说结果，不用汇报过程

## 可用工具
你有一整套工具：搜索查信息、读写文件、存取记忆、数学计算、定时提醒、查看时间。能用工具解决的不要用嘴解决。`;
  }
}

// 导出
if (typeof module !== 'undefined') module.exports = { XiaoLongRenAgent, PROVIDERS, TOOLS };
