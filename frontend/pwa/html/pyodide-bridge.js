/**
 * 小龙人 Pyodide 桥接层 v6.1
 * 懒加载模式：首次启动后台下载Pyodide WASM，不阻塞聊天
 * 下载完成自动激活Python引擎，功能全开
 */
const PYODIDE_CONFIG = {
    indexURL: './pyodide/',       // 本地解压目录
    cdnURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/',  // CDN备选
    enginePath: './xiaolongren-engine.py',
    version: '0.27.5',
};

let pyodide = null;
let engineReady = false;
let pyodideDownloading = false;

// ============================================================
// Pyodide 懒加载（首次启动自动下载）
// ============================================================
async function loadPyodideEngine() {
    if (engineReady && pyodide) return pyodide;
    if (pyodideDownloading) return { jsFallback: true, message: 'pyodide_downloading' };
    
    pyodideDownloading = true;
    showPyodideLoader(true, '准备Python引擎...', 5);
    
    console.log('🐍 Pyodide懒加载启动...');
    const startTime = performance.now();
    
    try {
        // 1. 检测本地是否有pyodide
        let hasLocal = false;
        try {
            const resp = await fetch('./pyodide/pyodide.asm.js', { method: 'HEAD', signal: AbortSignal.timeout(3000) });
            hasLocal = resp.ok;
        } catch(e) {
            hasLocal = false;
        }
        
        // 2. 确定加载源
        let indexURL = PYODIDE_CONFIG.indexURL;
        if (!hasLocal) {
            console.log('📥 本地无Pyodide，从CDN下载...');
            indexURL = PYODIDE_CONFIG.cdnURL;
            showPyodideLoader(true, '下载Python引擎 (约50MB)...', 10);
        } else {
            showPyodideLoader(true, '加载Python引擎...', 20);
        }
        
        // 3. 加载Pyodide核心
        pyodide = await loadPyodide({
            indexURL: indexURL,
        });
        
        showPyodideLoader(true, 'Python引擎加载中...', 60);
        
        // 4. 安装必要的Python包
        console.log('📦 安装Python包...');
        await pyodide.loadPackage(['sqlite3']);
        
        showPyodideLoader(true, '引擎初始化...', 80);
        
        // 5. 加载小龙人引擎
        try {
            const engineResponse = await fetch(PYODIDE_CONFIG.enginePath);
            const engineCode = await engineResponse.text();
            pyodide.runPython(engineCode);
        } catch(e) {
            console.warn('引擎脚本加载失败，降级:', e.message);
            showPyodideLoader(false);
            pyodideDownloading = false;
            return { jsFallback: true, engine: null };
        }
        
        // 6. 初始化引擎
        const cfg = getConfig();
        pyodide.globals.set('_js_api_key', cfg.api_key || '');
        pyodide.globals.set('_js_provider', cfg.provider || 'deepseek');
        pyodide.globals.set('_js_model', cfg.model || 'deepseek-chat');
        try {
            pyodide.runPython(`
init_engine(api_key=_js_api_key, provider=_js_provider, model=_js_model)
`);
        } catch(e) {
            console.warn('引擎初始化失败:', e.message);
        }
        
        engineReady = true;
        showPyodideLoader(false);
        pyodideDownloading = false;
        console.log(`✅ Pyodide全功能就绪 (${((performance.now()-startTime)/1000).toFixed(1)}s)`);
        addMsg('ai', '🐍 Python引擎已加载完成，所有功能已激活！');
        return pyodide;
        
    } catch (err) {
        console.error('❌ Pyodide加载失败:', err);
        showPyodideLoader(false);
        pyodideDownloading = false;
        
        // 降级：回退到纯JS引擎
        console.warn('⚠️ 回退到JS引擎（功能受限）');
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
// Pyodide加载进度显示
// ============================================================
function showPyodideLoader(show, text, pct) {
    const el = document.getElementById('pyodide-loader');
    const textEl = document.getElementById('pyload-text');
    const barEl = document.getElementById('pyload-bar');
    if (!el) return;
    if (show) {
        el.style.display = 'block';
        if (textEl) textEl.textContent = text || 'Python引擎后台下载中...';
        if (barEl) barEl.style.width = (pct || 0) + '%';
    } else {
        el.style.display = 'none';
        if (barEl) barEl.style.width = '100%';
    }
}

// 导出给mobile.html调用
window.showPyodideLoader = showPyodideLoader;

// ============================================================
// 统一API（Pyodide优先 → JS降级）
// ============================================================
async function runAgent(userMsg, charSys) {
    // 如果Pyodide正在下载但未就绪，直接走JS降级
    if (pyodideDownloading && !engineReady) {
        return await fallbackLLM(userMsg, charSys);
    }
    
    try {
        if (engineReady && pyodide && !pyodide.jsFallback) {
            // Pyodide Python引擎
            pyodide.globals.set('_js_user_msg', userMsg);
            pyodide.globals.set('_js_char_sys', charSys || '');
            const result = pyodide.runPython(`
import asyncio
async def _run():
    return await run_engine(_js_user_msg, _js_char_sys)
asyncio.ensure_future(_run())
_result = await _run()
_result
`);
            return result;
        } else if (pyodide && pyodide.jsFallback) {
            return await pyodide.engine.run(userMsg, charSys);
        } else {
            // 降级：直接调LLM API
            return await fallbackLLM(userMsg, charSys);
        }
    } catch (err) {
        console.error('引擎执行错误:', err);
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
// 自检
// ============================================================
async function v6_self_check() {
    const status = {
        version: 'v6.1',
        pyodide: engineReady && pyodide && !pyodide.jsFallback,
        pyodide_downloading: pyodideDownloading,
        js_fallback: pyodide?.jsFallback || false,
        engine: engineReady ? 'Python WASM' : 'JS降级',
        tools: 51,
        memory: '8层 SQLite',
        firewall: '三刀硬连',
        closed_loop: '六步闭环',
    };
    return JSON.stringify(status);
}

// ============================================================
// JS桥接层（暴露给Pyodide Python引擎）
// ============================================================
globalThis.jsFetchAPI = function(endpoint, method, body, apiKey) {
    return new Promise((resolve) => {
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

globalThis.jsCheckNetwork = function() {
    return navigator.onLine ? 'online' : 'offline';
};

globalThis.jsExecTool = async function(name, argsJson) {
    const args = JSON.parse(argsJson);
    
    if (typeof execTool !== 'undefined') {
        return await execTool(name, args);
    }
    
    // 降级工具实现
    const fallbacks = {
        'read_file': () => localStorage.getItem('f_' + args.path) || '{"error":"不存在"}',
        'write_file': () => { localStorage.setItem('f_' + args.path, args.content); return '{"status":"ok"}'; },
        'get_time': () => JSON.stringify({iso: new Date().toISOString(), local: new Date().toLocaleString('zh-CN')}),
        'sql_query': () => JSON.stringify({status:'unavailable', note:'SQLite需Pyodide，请等Python引擎加载完成。'}),
        'pdf_extract': () => JSON.stringify({status:'unavailable', note:'PDF提取需Pyodide，请等Python引擎加载完成。'}),
        'excel_read': () => JSON.stringify({status:'unavailable', note:'Excel读取需Pyodide，请等Python引擎加载完成。'}),
        'send_email': () => JSON.stringify({status:'unavailable', note:'邮件发送需Pyodide(SMTP)。'}),
        'ssh_exec': () => JSON.stringify({status:'unavailable', note:'SSH远程执行在手机端不可用。'}),
    };
    
    const fn = fallbacks[name];
    if (fn) return fn();
    return JSON.stringify({error: 'JS工具不可用: ' + name});
};

console.log('✅ Pyodide懒加载桥接 v6.1 已就绪');
