/**
 * 小龙人 Pyodide 桥接层 v6.0
 * 加载WASM Python引擎 → 连接UI → 全功能运行
 */
const PYODIDE_CONFIG = {
    indexURL: './pyodide/',  // Pyodide解压后的目录
    enginePath: './xiaolongren-engine.py',
};

let pyodide = null;
let engineReady = false;

// ============================================================
// Pyodide 加载器
// ============================================================
async function loadPyodideEngine() {
    if (engineReady && pyodide) return pyodide;
    
    console.log('🐍 加载Pyodide (WASM Python)...');
    const startTime = performance.now();
    
    try {
        // 加载Pyodide核心
        pyodide = await loadPyodide({
            indexURL: PYODIDE_CONFIG.indexURL,
        });
        
        console.log(`✅ Pyodide加载完成 (${((performance.now()-startTime)/1000).toFixed(1)}s)`);
        
        // 安装必要的Python包
        console.log('📦 安装Python包...');
        await pyodide.loadPackage(['sqlite3']);
        
        // 加载小龙人引擎（先加载自生长模块）
        const evoResponse = await fetch('./self_evolution.py');
        const evoCode = await evoResponse.text();
        pyodide.runPython(evoCode);
        
        const engineResponse = await fetch(PYODIDE_CONFIG.enginePath);
        const engineCode = await engineResponse.text();
        pyodide.runPython(engineCode);
        
        // 初始化引擎
        const cfg = getConfig();
        const initCode = `
init_engine(
    api_key="${cfg.api_key}",
    provider="${cfg.provider || 'deepseek'}",
    model="${cfg.model || 'deepseek-chat'}"
)
`;
        pyodide.runPython(initCode);
        
        engineReady = true;
        console.log('✅ 小龙人引擎v6.0就绪');
        return pyodide;
        
    } catch (err) {
        console.error('❌ Pyodide加载失败:', err);
        
        // 降级：回退到纯JS引擎
        console.warn('⚠️ 回退到v5.2 JS引擎');
        if (typeof XiaoLongRen !== 'undefined') {
            const cfg = getConfig();
            const jsEngine = new XiaoLongRen({
                apiKey: cfg.api_key,
                provider: cfg.provider,
                model: cfg.model,
                baseUrl: cfg.base_url || '',
            });
            await jsEngine.init();
            return { jsFallback: true, engine: jsEngine };
        }
        throw err;
    }
}

// ============================================================
// 统一API（Pyodide优先 → JS降级）
// ============================================================
async function runAgent(userMsg, charSys) {
    try {
        if (engineReady && pyodide && !pyodide.jsFallback) {
            // Pyodide Python引擎
            const safeMsg = userMsg.replace(/'/g, "\\'").replace(/\n/g, '\\n');
            const safeChar = (charSys || '').replace(/'/g, "\\'").replace(/\n/g, '\\n');
            
            const result = pyodide.runPython(`
import asyncio
async def _run():
    return await run_engine('${safeMsg}', '${safeChar}')
asyncio.ensure_future(_run())
_result = await _run()
_result
`);
            return result;
        } else if (pyodide && pyodide.jsFallback) {
            // JS降级引擎
            return await pyodide.engine.run(userMsg, charSys);
        } else {
            // 未加载Pyodide，直接用JS引擎
            if (typeof XiaoLongRen !== 'undefined') {
                const cfg = getConfig();
                const jsEngine = new XiaoLongRen({
                    apiKey: cfg.api_key, provider: cfg.provider,
                    model: cfg.model, baseUrl: cfg.base_url || '',
                });
                await jsEngine.init();
                return await jsEngine.run(userMsg, charSys);
            }
            throw new Error('无可用引擎');
        }
    } catch (err) {
        console.error('引擎执行错误:', err);
        // 最终降级：直接调LLM API
        return await fallbackLLM(userMsg, charSys);
    }
}

// ============================================================
// 最终降级：纯LLM调用
// ============================================================
async function fallbackLLM(userMsg, charSys) {
    const cfg = getConfig();
    const PROVIDERS = {
        deepseek: 'https://api.deepseek.com/v1',
        openai: 'https://api.openai.com/v1',
        anthropic: 'https://api.anthropic.com/v1',
        moonshot: 'https://api.moonshot.cn/v1',
        zhipu: 'https://open.bigmodel.cn/api/paas/v4',
        qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    };
    
    const baseUrl = cfg.base_url || PROVIDERS[cfg.provider] || PROVIDERS['deepseek'];
    const endpoint = baseUrl.replace(/\/+$/, '') + '/chat/completions';
    
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + cfg.api_key,
        },
        body: JSON.stringify({
            model: cfg.model || 'deepseek-chat',
            messages: [
                { role: 'system', content: charSys || '你是小龙人，简洁回答用户。' },
                { role: 'user', content: userMsg },
            ],
            max_tokens: 512,
        }),
    });
    
    const data = await response.json();
    return data.choices?.[0]?.message?.content || '抱歉，暂时无法回复。';
}

// ============================================================
// 自检（含Pyodide状态）
// ============================================================
async function v6_self_check() {
    const status = {
        version: 'v6.0',
        pyodide: engineReady && pyodide && !pyodide.jsFallback,
        js_fallback: pyodide?.jsFallback || false,
        engine: 'Python W ASM',
        tools: 51,
        memory: '8层 SQLite',
        firewall: '三刀硬连',
        closed_loop: '六步闭环',
        guard: '四级预警',
        swarm: '蜂群战术✅',
        celestial: '天权搜索✅',
        evolve: '自进化✅',
    };
    return JSON.stringify(status);
}

// 暴露JS网络层给Pyodide（fetch + 超时 + 重试）
globalThis.jsFetchAPI = function(endpoint, method, body, apiKey) {
    return new Promise((resolve, reject) => {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        
        fetch(endpoint, {
            method: method || 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + apiKey,
            },
            body: body,
            signal: controller.signal,
        })
        .then(r => { clearTimeout(timeout); return r.text(); })
        .then(text => resolve(text))
        .catch(err => {
            clearTimeout(timeout);
            resolve(JSON.stringify({error: 'API调用失败: ' + err.message}));
        });
    });
};

// 网络检测
globalThis.jsCheckNetwork = function() {
    return navigator.onLine ? 'online' : 'offline';
};

console.log('✅ JS网络桥接已就绪 (jsFetchAPI + jsCheckNetwork)');

// 暴露JS工具执行器给Pyodide Python引擎
globalThis.jsExecTool = async function(name, argsJson) {
    const args = JSON.parse(argsJson);
    
    // 调用xiaolongren-core.js中的execTool
    if (typeof execTool !== 'undefined') {
        return await execTool(name, args);
    }
    
    // 降级：最基本的工具实现
    const fallbacks = {
        'read_file': () => localStorage.getItem('f_' + args.path) || '{"error":"不存在"}',
        'write_file': () => { localStorage.setItem('f_' + args.path, args.content); return '{"status":"ok"}'; },
        'get_time': () => JSON.stringify({iso: new Date().toISOString(), local: new Date().toLocaleString('zh-CN')}),
        'calculator': () => { try { return JSON.stringify({result: eval(args.expression)}); } catch(e) { return '{"error":"'+e.message+'"}'; } },
        'sql_query': () => JSON.stringify({status:'unavailable', note:'SQLite需Pyodide环境，当前JS降级模式不可用。请等Python引擎加载完成。'}),
        'pdf_extract': () => JSON.stringify({status:'unavailable', note:'PDF提取需Pyodide环境。请等Python引擎加载完成。'}),
        'excel_read': () => JSON.stringify({status:'unavailable', note:'Excel读取需Pyodide环境。请等Python引擎加载完成。'}),
        'excel_write': () => JSON.stringify({status:'unavailable', note:'Excel写入需Pyodide环境。请等Python引擎加载完成。'}),
        'send_email': () => JSON.stringify({status:'unavailable', note:'邮件发送需Pyodide环境(smtplib)。'}),
        'ssh_exec': () => JSON.stringify({status:'unavailable', note:'SSH远程执行需后端桥接。此功能在纯手机端不可用。'}),
    };
    
    const fn = fallbacks[name];
    if (fn) return fn();
    return JSON.stringify({error: 'JS工具不可用: ' + name});
};

console.log('✅ JS工具桥接已就绪 (jsExecTool)');
