/**
 * 小龙人插件加载器 v1.0
 * 动态加载、注册、路由插件——加功能不改内核
 */

const XLR = (function() {
  'use strict';
  
  const plugins = {};
  const toolMap = {};       // tool_name → {plugin, handler}
  const allTools = [];      // 所有已注册工具定义
  let loadOrder = [];

  return {
    // ============================================================
    // 注册插件（插件文件调用此方法）
    // ============================================================
    registerPlugin(plugin) {
      const { name, version, tools, handlers, onLoad, onUnload } = plugin;
      
      if (plugins[name]) {
        console.warn(`[XLR] 插件 "${name}" 已注册，跳过重复加载`);
        return false;
      }

      // 注册工具
      const toolCount = (tools || []).length;
      for (const tool of (tools || [])) {
        const toolName = typeof tool === 'string' ? tool : tool.function?.name;
        if (!toolName) continue;
        
        if (toolMap[toolName]) {
          console.warn(`[XLR] 工具 "${toolName}" 已被插件 "${toolMap[toolName].plugin}" 注册，跳过`);
          continue;
        }
        
        toolMap[toolName] = { plugin: name, handler: handlers?.[toolName] };
        if (typeof tool === 'object') allTools.push(tool);
      }

      plugins[name] = {
        name, version: version || '0.1.0', toolCount,
        handlers: handlers || {},
        onLoad, onUnload,
        loaded: false,
      };
      
      loadOrder.push(name);
      console.log(`[XLR] ✅ 插件 "${name}" v${version} 已注册 (${toolCount}个工具)`);
      return true;
    },

    // ============================================================
    // 初始化所有插件（由内核启动时调用）
    // ============================================================
    async initAll(coreEngine) {
      const results = [];
      for (const name of loadOrder) {
        const p = plugins[name];
        try {
          if (p.onLoad) await p.onLoad(coreEngine);
          p.loaded = true;
          results.push({ name, status: 'ok' });
        } catch (e) {
          console.error(`[XLR] ❌ 插件 "${name}" 初始化失败:`, e);
          results.push({ name, status: 'error', error: e.message });
        }
      }
      return results;
    },

    // ============================================================
    // 执行工具调用（内核调用此方法分发到插件）
    // ============================================================
    async execute(toolName, args) {
      const entry = toolMap[toolName];
      if (!entry) {
        // 检查是否需要内核内置处理
        return null; // 返回null表示插件体系不处理，由内核fallback
      }
      
      try {
        const result = await entry.handler(args);
        return result;
      } catch (e) {
        console.error(`[XLR] 工具 "${toolName}" 执行失败:`, e);
        return JSON.stringify({ error: `${toolName}: ${e.message}` });
      }
    },

    // ============================================================
    // 查询接口
    // ============================================================
    getAllTools() {
      return allTools;
    },

    getToolCount() {
      return Object.keys(toolMap).length;
    },

    getPlugins() {
      return Object.entries(plugins).map(([name, p]) => ({
        name, version: p.version,
        tools: p.toolCount, loaded: p.loaded,
      }));
    },

    hasTool(name) {
      return name in toolMap;
    },

    getToolPlugin(name) {
      return toolMap[name]?.plugin || null;
    },

    // ============================================================
    // 动态加载外部插件文件
    // ============================================================
    async loadPluginFile(url) {
      try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const code = await resp.text();
        // 使用 Function 在隔离作用域执行插件代码
        const fn = new Function('XLR', code);
        fn(XLR);
        // 初始化最后一个加载的插件
        const lastName = loadOrder[loadOrder.length - 1];
        if (lastName && plugins[lastName]?.onLoad) {
          await plugins[lastName].onLoad();
          plugins[lastName].loaded = true;
        }
        return { status: 'ok', plugin: lastName };
      } catch (e) {
        return { status: 'error', error: e.message };
      }
    },

    // ============================================================
    // 插件状态报告
    // ============================================================
    report() {
      return {
        totalPlugins: Object.keys(plugins).length,
        totalTools: Object.keys(toolMap).length,
        plugins: Object.entries(plugins).map(([name, p]) => ({
          name, version: p.version,
          tools: p.toolCount,
          status: p.loaded ? '✅' : '⏳',
        })),
      };
    },
  };
})();
