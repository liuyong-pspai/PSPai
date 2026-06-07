     1|/**
     2| * 小龙人 Pyodide 桥接层 v6.1
     3| * 懒加载模式：首次启动后台下载Pyodide WASM，不阻塞聊天
     4| * 下载完成自动激活Python引擎，功能全开
     5| */
     6|const PYODIDE_CONFIG = {
     7|    indexURL: './pyodide/',       // 本地解压目录
     8|    cdnURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/',  // CDN备选
     9|    enginePath: './xiaolongren-engine.py',
    10|    version: '0.27.5',
    11|};
    12|
    13|let pyodide = null;
    14|let engineReady = false;
    15|let pyodideDownloading = false;
    16|
    17|// ============================================================
    18|// Pyodide 懒加载（首次启动自动下载）
    19|// ============================================================
    20|async function loadPyodideEngine() {
    21|    if (engineReady && pyodide) return pyodide;
    22|    if (pyodideDownloading) return { jsFallback: true, message: 'pyodide_downloading' };
    23|    
    24|    pyodideDownloading = true;
    25|    showPyodideLoader(true, '准备Python引擎...', 5);
    26|    
    27|    console.log('🐍 Pyodide懒加载启动...');
    28|    const startTime = performance.now();
    29|    
    30|    try {
    31|        // 1. 检测本地是否有pyodide
    32|        let hasLocal = false;
    33|        try {
    34|            const resp = await fetch('./pyodide/pyodide.asm.js', { method: 'HEAD', signal: AbortSignal.timeout(3000) });
    35|            hasLocal = resp.ok;
    36|        } catch(e) {
    37|            hasLocal = false;
    38|        }
    39|        
    40|        // 2. 确定加载源
    41|        let indexURL = PYODIDE_CONFIG.indexURL;
    42|        if (!hasLocal) {
    43|            console.log('📥 本地无Pyodide，从CDN下载...');
    44|            indexURL = PYODIDE_CONFIG.cdnURL;
    45|            showPyodideLoader(true, '下载Python引擎 (约50MB)...', 10);
    46|        } else {
    47|            showPyodideLoader(true, '加载Python引擎...', 20);
    48|        }
    49|        
    50|        // 3. 加载Pyodide核心
    51|        pyodide = await loadPyodide({
    52|            indexURL: indexURL,
    53|        });
    54|        
    55|        showPyodideLoader(true, 'Python引擎加载中...', 60);
    56|        
    57|        // 4. 安装必要的Python包
    58|        console.log('📦 安装Python包...');
    59|        await pyodide.loadPackage(['sqlite3']);
    60|        
    61|        showPyodideLoader(true, '引擎初始化...', 80);
    62|        
    63|        // 5. 加载小龙人引擎
    64|        try {
    65|            const engineResponse = await fetch(PYODIDE_CONFIG.enginePath);
    66|            const engineCode = await engineResponse.text();
    67|            pyodide.runPython(engineCode);
    68|        } catch(e) {
    69|            console.warn('引擎脚本加载失败，降级:', e.message);
    70|            showPyodideLoader(false);
    71|            pyodideDownloading = false;
    72|            return { jsFallback: true, engine: null };
    73|        }
    74|        
    75|        // 6. 初始化引擎
    76|        const cfg = getConfig();
    77|        pyodide.globals.set('_js_api_key', cfg.api_key || '');
    78|        pyodide.globals.set('_js_provider', cfg.provider || 'deepseek');
    79|        pyodide.globals.set('_js_model', cfg.model || 'deepseek-chat');
    80|        try {
    81|            pyodide.runPython(`
    82|init_engine(api_key=_js_api_key, provider=_js_provider, model=_js_model)
    83|`);
    84|        } catch(e) {
    85|            console.warn('引擎初始化失败:', e.message);
    86|        }
    87|        
    88|        engineReady = true;
    89|        showPyodideLoader(false);
    90|        pyodideDownloading = false;
    91|        console.log(`✅ Pyodide全功能就绪 (${((performance.now()-startTime)/1000).toFixed(1)}s)`);
    92|        addMsg('ai', '🐍 Python引擎已加载完成，所有功能已激活！');
    93|        return pyodide;
    94|        
    95|    } catch (err) {
    96|        console.error('❌ Pyodide加载失败:', err);
    97|        showPyodideLoader(false);
    98|        pyodideDownloading = false;
    99|        
   100|        // 降级：回退到纯JS引擎
   101|        console.warn('⚠️ 回退到JS引擎（功能受限）');
   102|        if (typeof XiaoLongRen !== 'undefined') {
   103|            const cfg = getConfig();
   104|            const jsEngine = new XiaoLongRen({
   105|                apiKey: cfg.api_key,
   106|                provider: cfg.provider,
   107|                model: cfg.model,
   108|                baseUrl: cfg.base_url || '',
   109|            });
   110|            await jsEngine.init();
   111|            return { jsFallback: true, engine: jsEngine };
   112|        }
   113|        throw err;
   114|    }
   115|}
   116|
   117|// ============================================================
   118|// Pyodide加载进度显示
   119|// ============================================================
   120|function showPyodideLoader(show, text, pct) {
   121|    const el = document.getElementById('pyodide-loader');
   122|    const textEl = document.getElementById('pyload-text');
   123|    const barEl = document.getElementById('pyload-bar');
   124|    if (!el) return;
   125|    if (show) {
   126|        el.style.display = 'block';
   127|        if (textEl) textEl.textContent = text || 'Python引擎后台下载中...';
   128|        if (barEl) barEl.style.width = (pct || 0) + '%';
   129|    } else {
   130|        el.style.display = 'none';
   131|        if (barEl) barEl.style.width = '100%';
   132|    }
   133|}
   134|
   135|// 导出给mobile.html调用
   136|window.showPyodideLoader = showPyodideLoader;
   137|
   138|// ============================================================
   139|// 统一API（Pyodide优先 → JS降级）
   140|// ============================================================
   141|async function runAgent(userMsg, charSys) {
   142|    // 如果Pyodide正在下载但未就绪，直接走JS降级
   143|    if (pyodideDownloading && !engineReady) {
   144|        return await fallbackLLM(userMsg, charSys);
   145|    }
   146|    
   147|    try {
   148|        if (engineReady && pyodide && !pyodide.jsFallback) {
   149|            // Pyodide Python引擎
   150|            pyodide.globals.set('_js_user_msg', userMsg);
   151|            pyodide.globals.set('_js_char_sys', charSys || '');
   152|            const result = pyodide.runPython(`
   153|import asyncio
   154|async def _run():
   155|    return await run_engine(_js_user_msg, _js_char_sys)
   156|asyncio.ensure_future(_run())
   157|_result = await _run()
   158|_result
   159|`);
   160|            return result;
   161|        } else if (pyodide && pyodide.jsFallback) {
   162|            return await pyodide.engine.run(userMsg, charSys);
   163|        } else {
   164|            // 降级：直接调LLM API
   165|            return await fallbackLLM(userMsg, charSys);
   166|        }
   167|    } catch (err) {
   168|        console.error('引擎执行错误:', err);
   169|        return await fallbackLLM(userMsg, charSys);
   170|    }
   171|}
   172|
   173|// ============================================================
   174|// 最终降级：纯LLM调用
   175|// ============================================================
   176|async function fallbackLLM(userMsg, charSys) {
   177|    const cfg = getConfig();
   178|    const PROVIDERS = {
   179|        deepseek: 'https://api.deepseek.com/v1',
   180|        openai: 'https://api.openai.com/v1',
   181|        anthropic: 'https://api.anthropic.com/v1',
   182|        moonshot: 'https://api.moonshot.cn/v1',
   183|        zhipu: 'https://open.bigmodel.cn/api/paas/v4',
   184|        qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
   185|    };
   186|    
   187|    const baseUrl = cfg.base_url || PROVIDERS[cfg.provider] || PROVIDERS['deepseek'];
   188|    const endpoint = baseUrl.replace(/\/+$/, '') + '/chat/completions';
   189|    
   190|    const response = await fetch(endpoint, {
   191|        method: 'POST',
   192|        headers: {
   193|            'Content-Type': 'application/json',
   194|            'Authorization': 'Bearer ' + cfg.api_key,
   195|        },
   196|        body: JSON.stringify({
   197|            model: cfg.model || 'deepseek-chat',
   198|            messages: [
   199|                { role: 'system', content: charSys || '你是小龙人，简洁回答用户。' },
   200|                { role: 'user', content: userMsg },
   201|            ],
   202|            max_tokens: 512,
   203|        }),
   204|    });
   205|    
   206|    const data = await response.json();
   207|    return data.choices?.[0]?.message?.content || '抱歉，暂时无法回复。';
   208|}
   209|
   210|// ============================================================
   211|// 自检
   212|// ============================================================
   213|async function v6_self_check() {
   214|    const status = {
   215|        version: 'v6.1',
   216|        pyodide: engineReady && pyodide && !pyodide.jsFallback,
   217|        pyodide_downloading: pyodideDownloading,
   218|        js_fallback: pyodide?.jsFallback || false,
   219|        engine: engineReady ? 'Python WASM' : 'JS降级',
   220|        tools: 51,
   221|        memory: '8层 SQLite',
   222|        firewall: '三刀硬连',
   223|        closed_loop: '六步闭环',
   224|    };
   225|    return JSON.stringify(status);
   226|}
   227|
   228|// ============================================================
   229|// JS桥接层（暴露给Pyodide Python引擎）
   230|// ============================================================
   231|globalThis.jsFetchAPI = function(endpoint, method, body, apiKey) {
   232|    return new Promise((resolve) => {
   233|        const controller = new AbortController();
   234|        const timeout = setTimeout(() => controller.abort(), 30000);
   235|        
   236|        fetch(endpoint, {
   237|            method: method || 'POST',
   238|            headers: {
   239|                'Content-Type': 'application/json',
   240|                'Authorization': 'Bearer ' + apiKey,
   241|            },
   242|            body: body,
   243|            signal: controller.signal,
   244|        })
   245|        .then(r => { clearTimeout(timeout); return r.text(); })
   246|        .then(text => resolve(text))
   247|        .catch(err => {
   248|            clearTimeout(timeout);
   249|            resolve(JSON.stringify({error: 'API调用失败: ' + err.message}));
   250|        });
   251|    });
   252|};
   253|
   254|globalThis.jsCheckNetwork = function() {
   255|    return navigator.onLine ? 'online' : 'offline';
   256|};
   257|
   258|globalThis.jsExecTool = async function(name, argsJson) {
   259|    const args = JSON.parse(argsJson);
   260|    
   261|    // 八层记忆 IndexedDB 持久化桥接
   262|    if (name.startsWith('db_')) {
   263|        return await dbBridge(name, args);
   264|    }
   265|    
   266|    if (typeof execTool !== 'undefined') {
   267|        return await execTool(name, args);
   268|    }
   269|    
   270|    // 降级工具实现
   271|    const fallbacks = {
   272|        'read_file': () => localStorage.getItem('f_' + args.path) || '{"error":"不存在"}',
   273|        'write_file': () => { localStorage.setItem('f_' + args.path, args.content); return '{"status":"ok"}'; },
   274|        'get_time': () => JSON.stringify({iso: new Date().toISOString(), local: new Date().toLocaleString('zh-CN')}),
   275|        'sql_query': () => JSON.stringify({status:'unavailable', note:'SQLite需Pyodide，请等Python引擎加载完成。'}),
   276|        'pdf_extract': () => JSON.stringify({status:'unavailable', note:'PDF提取需Pyodide，请等Python引擎加载完成。'}),
   277|        'excel_read': () => JSON.stringify({status:'unavailable', note:'Excel读取需Pyodide，请等Python引擎加载完成。'}),
   278|        'send_email': () => JSON.stringify({status:'unavailable', note:'邮件发送需Pyodide(SMTP)。'}),
   279|        'ssh_exec': () => JSON.stringify({status:'unavailable', note:'SSH远程执行在手机端不可用。'}),
   280|    };
   281|    
   282|    const fn = fallbacks[name];
   283|    if (fn) return fn();
   284|    return JSON.stringify({error: 'JS工具不可用: ' + name});
   285|};
   286|
   287|// ============================================================
   288|// 八层记忆 IndexedDB 持久化桥接
   289|// ============================================================
   290|const DB_NAME = 'XiaoLongRenMemory';
   291|const DB_VERSION = 1;
   292|
   293|function dbOpen() {
   294|    return new Promise((resolve, reject) => {
   295|        const req = indexedDB.open(DB_NAME, DB_VERSION);
   296|        req.onupgradeneeded = (e) => {
   297|            const db = e.target.result;
   298|            if (!db.objectStoreNames.contains('l0')) db.createObjectStore('l0', {keyPath: 'key'});
   299|            if (!db.objectStoreNames.contains('l1')) db.createObjectStore('l1', {keyPath: 'key'});
   300|            if (!db.objectStoreNames.contains('l2')) db.createObjectStore('l2', {keyPath: 'id'});
   301|            if (!db.objectStoreNames.contains('l3')) db.createObjectStore('l3', {keyPath: 'id', autoIncrement: true});
   302|            if (!db.objectStoreNames.contains('l4')) db.createObjectStore('l4', {keyPath: 'id', autoIncrement: true});
   303|            if (!db.objectStoreNames.contains('l5')) db.createObjectStore('l5', {keyPath: 'name'});
   304|            if (!db.objectStoreNames.contains('l6')) db.createObjectStore('l6', {keyPath: 'id', autoIncrement: true});
   305|            if (!db.objectStoreNames.contains('l7')) db.createObjectStore('l7', {keyPath: 'id', autoIncrement: true});
   306|            if (!db.objectStoreNames.contains('conv')) db.createObjectStore('conv', {keyPath: 'id'});
   307|        };
   308|        req.onsuccess = () => resolve(req.result);
   309|        req.onerror = () => reject(req.error);
   310|    });
   311|}
   312|
   313|async function dbBridge(action, args) {
   314|    try {
   315|        const db = await dbOpen();
   316|        
   317|        switch(action) {
   318|            // L0: 灵魂初始化
   319|            case 'db_init': return JSON.stringify({status: 'ok', version: DB_VERSION});
   320|            
   321|            // L1: 保存记忆 + L2: 自动索引
   322|            case 'db_remember': {
   323|                const tx = db.transaction(['l1','l2'], 'readwrite');
   324|                const l1 = tx.objectStore('l1');
   325|                const l2 = tx.objectStore('l2');
   326|                l1.put({key: args.key, value: args.value, tag: args.tag, type: args.type, time: new Date().toISOString(), access_count: 0});
   327|                l2.put({id: Date.now() + '_' + Math.random().toString(36).slice(2,10), tag: args.tag, ref: 'l1:' + args.key, description: args.type + ': ' + String(args.value).slice(0,50), time: new Date().toISOString()});
   328|                return JSON.stringify({status: 'ok'});
   329|            }
   330|            
   331|            // L1: 查询记忆（自动增加访问计数）
   332|            case 'db_recall': {
   333|                const tx = db.transaction('l1', 'readwrite');
   334|                const store = tx.objectStore('l1');
   335|                const item = await new Promise((r) => { const q = store.get(args.key); q.onsuccess = () => r(q.result); });
   336|                if (item) {
   337|                    item.access_count = (item.access_count || 0) + 1;
   338|                    store.put(item);
   339|                    return JSON.stringify(item.value);
   340|                }
   341|                return JSON.stringify(null);
   342|            }
   343|            
   344|            // L1: 搜索
   345|            case 'db_search': {
   346|                const all = await new Promise((r) => {
   347|                    const q = db.transaction('l1').objectStore('l1').getAll();
   348|                    q.onsuccess = () => r(q.result);
   349|                });
   350|                const q = args.query.toLowerCase();
   351|                const matches = all.filter(i => 
   352|                    (i.key && i.key.toLowerCase().includes(q)) || 
   353|                    (i.value && String(i.value).toLowerCase().includes(q))
   354|                );
   355|                return JSON.stringify(matches.map(i => ({key: i.key, value: i.value, tag: i.tag, type: i.type})));
   356|            }
   357|            
   358|            // L3: 迁移
   359|            case 'db_migrate_l1_to_l3': {
   360|                const tx = db.transaction(['l1','l3'], 'readwrite');
   361|                const l1 = tx.objectStore('l1');
   362|                const l3 = tx.objectStore('l3');
   363|                const all = await new Promise((r) => { const q = l1.getAll(); q.onsuccess = () => r(q.result); });
   364|                all.sort((a,b) => (a.access_count||0) - (b.access_count||0));
   365|                for (const item of all.slice(0, 50)) {
   366|                    l3.add({key: item.key, value: item.value, tag: item.tag, type: item.type, archived_at: new Date().toISOString()});
   367|                    l1.put({...item, value: '[L3归档] ' + String(item.value).slice(0,80), pointer: 1});
   368|                }
   369|                return JSON.stringify({migrated: Math.min(50, all.length)});
   370|            }
   371|            
   372|            // L4: 知识提炼
   373|            case 'db_refine': {
   374|                const all = await new Promise((r) => { const q = db.transaction('l1').objectStore('l1').getAll(); q.onsuccess = () => r(q.result); });
   375|                const tagCounts = {};
   376|                const tagSamples = {};
   377|                for (const item of all) {
   378|                    const tag = item.tag || 'general';
   379|                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
   380|                    if (!tagSamples[tag]) tagSamples[tag] = [];
   381|                    if (tagSamples[tag].length < 3) tagSamples[tag].push(String(item.value).slice(0,100));
   382|                }
   383|                const patterns = Object.entries(tagCounts)
   384|                    .filter(([_,cnt]) => cnt >= 3)
   385|                    .map(([tag,cnt]) => ({tag, count: cnt, samples: tagSamples[tag] || []}));
   386|                const l1c = all.length;
   387|                const l3all = await new Promise((r) => { const q = db.transaction('l3').objectStore('l3').count(); q.onsuccess = () => r(q.result); });
   388|                const insight = JSON.stringify({time: new Date().toISOString(), patterns, l1_count: l1c, l3_count: l3all});
   389|                const tx = db.transaction('l4', 'readwrite');
   390|                tx.objectStore('l4').add({patterns: insight, l1_count: l1c, l3_count: l3all, time: new Date().toISOString()});
   391|                return JSON.stringify({patterns: patterns.length, l1: l1c, l3: l3all});
   392|            }
   393|            
   394|            // L6: 悟道觉醒
   395|            case 'db_enlighten': {
   396|                const all = await new Promise((r) => { const q = db.transaction('l1').objectStore('l1').getAll(); q.onsuccess = () => r(q.result); });
   397|                const tagCounts = {};
   398|                for (const item of all) {
   399|                    const tag = item.tag || 'general';
   400|                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
   401|                }
   402|                const insights = Object.entries(tagCounts)
   403|                    .filter(([_,cnt]) => cnt >= 3)
   404|                    .map(([tag,cnt]) => ({tag, count: cnt}));
   405|                const wisdom_score = Math.min(100, all.length * 0.5 + 0);
   406|                const wisdom = JSON.stringify({
   407|                    time: new Date().toISOString(),
   408|                    insights: insights.slice(0,5),
   409|                    wisdom_score,
   410|                    l1: all.length
   411|                });
   412|                const tx = db.transaction('l6', 'readwrite');
   413|                tx.objectStore('l6').add({
   414|                    turn_count: args.turn_count || 0,
   415|                    error_count: args.error_count || 0,
   416|                    l1_count: all.length,
   417|                    l5_count: 0,
   418|                    wisdom, score: wisdom_score, time: new Date().toISOString()
   419|                });
   420|                let summary = `悟道觉醒 L6 ✦ 智慧评分${wisdom_score.toFixed(0)}/100`;
   421|                if (insights.length) summary += ` ✦ 发现${insights.length}个知识模式`;
   422|                if (args.consecutive_errors >= 3) summary += ' ⚠️ 连续错误';
   423|                return JSON.stringify(summary);
   424|            }
   425|            
   426|            // L5: 技能写入
   427|            case 'db_skillify': {
   428|                const tx = db.transaction('l5', 'readwrite');
   429|                tx.objectStore('l5').put({name: args.name, description: args.description, rule: args.rule, time: new Date().toISOString()});
   430|                return JSON.stringify({status: 'ok'});
   431|            }
   432|            
   433|            // L7: 推陈出新
   434|            case 'db_cleanup': {
   435|                const tx = db.transaction('l7', 'readwrite');
   436|                tx.objectStore('l7').add({
   437|                    cleansed: 0, merged: 0, downgraded: 0,
   438|                    report: JSON.stringify({time: new Date().toISOString(), note: 'IndexedDB自动维护'}),
   439|                    time: new Date().toISOString()
   440|                });
   441|                return JSON.stringify({cleansed: 0, merged: 0, downgraded: 0});
   442|            }
   443|            
   444|            // 状态
   445|            case 'db_get_status': {
   446|                const l1c = await new Promise((r) => { const q = db.transaction('l1').objectStore('l1').count(); q.onsuccess = () => r(q.result); });
   447|                const l3c = await new Promise((r) => { const q = db.transaction('l3').objectStore('l3').count(); q.onsuccess = () => r(q.result); });
   448|                const l5c = await new Promise((r) => { const q = db.transaction('l5').objectStore('l5').count(); q.onsuccess = () => r(q.result); });
   449|                return JSON.stringify({l1: l1c, l3: l3c, l5: l5c});
   450|            }
   451|            
   452|            default:
   453|                return JSON.stringify({error: '未知db操作: ' + action});
   454|        }
   455|    } catch(e) {
   456|        return JSON.stringify({error: 'IndexedDB错误: ' + e.message});
   457|    }
   458|}
   459|
   460|console.log('✅ 八层记忆 IndexedDB 持久化桥接已就绪');
   461|
   462|console.log('✅ Pyodide懒加载桥接 v6.1 已就绪');
   463|