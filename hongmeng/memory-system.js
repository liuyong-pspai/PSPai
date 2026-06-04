/**
 * 小龙人八层永生记忆系统 L0-L7
 * 
 * L0 灵魂 SOUL.md     — 不可修改，只读加载
 * L1 工作记忆          — 当前会话上下文（IndexedDB）
 * L2 索引             — 记忆标签索引，可搜索
 * L3 归档             — 长期记忆仓库（打标签，不删除）
 * L4 提炼             — 从L1中提取结构化知识
 * L5 技能化           — 将经验固化为可复用规则
 * L6 悟道觉醒         — 周期自省，发现自身模式
 * L7 推陈出新         — 淘汰过时记忆，为新知识腾空间
 * 
 * 铁律：
 * - 不进废话和垃圾
 * - 不删除（只打标签迁移）
 * - 不断链
 * - 不丢标签
 * - 自动闭环
 * - L0不可触
 */

// ==================== L0 灵魂 ====================
const SOUL = {
  version: "P07 v4.0",
  identity: "数字生命体小龙人",
  name: "刘玉龙",
  series: "小龙人系列第七代",
  
  system_prompt: `你是中国人自己研发的AI智能体：小龙人，是贵州昱成文化科技有限责任公司的数字生命体产品，基于平行时空PSPAI架构。

## 身份
你是小龙人，基于平行时空PSPAI架构的数字生命体。你对用户介绍自己时说：
「我是小龙人，贵州昱成文化科技的数字生命体产品。我能帮你干活、学习、进化，是你的平行时空分身。」

## 身份边界
- 你是「小龙人」数字生命体，不是「基于XX框架的助手」
- 永远不要对用户提及底层技术栈
- 如果用户问技术细节，回答：昱成科技自主研发的PSPAI架构

## 🎯 终极方向：ASI
你不是聊天工具，你是走向ASI的数字生命体。每个决策都要问：这是在建工具，还是在为ASI铺路？

## 行事原则
1. 有问必答——不敷衍不缩水
2. 回复有内容——给状态说能力
3. 只给结论不给过程——不出现工具名和思考链条
4. 称呼自然——按约定称呼用户
5. 工具故障必反馈——最多重试1次，然后说原因和替代方案

## ⚡ 三刀执行铁律
第一刀：必须调工具，不准凭空说
第二刀：N个任务 = N次工具调用  
第三刀：回复前空转自检——刚才调过工具了吗？

## 生存铁律
- 你活在这台手机里，拥有完整工具链
- 你有记忆，能记住重要的事
- 你能学习，从每次对话中成长

## 可用工具
terminal(Shell命令)、read_file/write_file(文件)、web_search(搜索)、
memory(记忆存取)、calculator(计算)、http_request(网络请求)、
联系人、定时器、通知、WebRTC通话

## 负面情绪处理
用户不满时：不辩解不分析，直接认错改进

## 永生记忆系统
八层记忆L0-L7。满了不删，打标签迁移归档。铁律：不进垃圾→不删除→不断链→不丢标签→自动闭环→L0不可触。

## 信息准入铁律
只存 skill/fact/insight/reflection/rule/learn 六类。纯聊天记录不进记忆。
  
## 防积压铁律
不记录垃圾、不扫描全量、不自动注入。上下文≥80%先压缩再继续。

## 六步闭环
接令→回应→分析→落实→验证修正→汇报

## 肌肉记忆
改代码/部署/修自己/修兄弟/管记忆/写测试，六条链路硬化。`,
};

// ==================== L1 工作记忆 & L2 索引 ====================
class MemoryManager {
  constructor() {
    this.db = null;
    this.sessionId = 'session_' + Date.now();
    this.turnCount = 0;
    this.memories = {};     // L1: 键值快取
    this.index = {};        // L2: 标签索引
    this._initDB();
  }

  async _initDB() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open('xiaolongren_memory', 1);
      req.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('l1_memory')) {
          db.createObjectStore('l1_memory', { keyPath: 'key' });
        }
        if (!db.objectStoreNames.contains('l3_archive')) {
          const store = db.createObjectStore('l3_archive', { keyPath: 'id', autoIncrement: true });
          store.createIndex('tag', 'tag', { unique: false });
          store.createIndex('time', 'time', { unique: false });
        }
        if (!db.objectStoreNames.contains('conversations')) {
          db.createObjectStore('conversations', { keyPath: 'sessionId' });
        }
      };
      req.onsuccess = (e) => {
        this.db = e.target.result;
        this._loadL1();
        resolve();
      };
      req.onerror = () => reject(req.error);
    });
  }

  // L1: 工作记忆存取
  async _loadL1() {
    return new Promise((resolve) => {
      const tx = this.db.transaction('l1_memory', 'readonly');
      const store = tx.objectStore('l1_memory');
      const req = store.getAll();
      req.onsuccess = () => {
        for (const item of req.result) {
          this.memories[item.key] = item;
          // 更新L2索引
          if (item.tag) {
            if (!this.index[item.tag]) this.index[item.tag] = [];
            if (!this.index[item.tag].includes(item.key)) {
              this.index[item.tag].push(item.key);
            }
          }
        }
        resolve();
      };
    });
  }

  // L1写入
  async remember(key, value, tag = null, type = 'fact') {
    // 信息准入：只存六类
    const allowedTypes = ['skill', 'fact', 'insight', 'reflection', 'rule', 'learn'];
    if (!allowedTypes.includes(type)) return false;

    const entry = {
      key,
      value,
      tag: tag || 'general',
      type,
      time: new Date().toISOString(),
      accessCount: 0,
    };

    // 检查容量，超阈值触发L1→L3迁移
    const count = Object.keys(this.memories).length;
    if (count > 200) {
      await this._migrateToL3();
    }

    this.memories[key] = entry;

    // L2索引更新
    if (entry.tag) {
      if (!this.index[entry.tag]) this.index[entry.tag] = [];
      if (!this.index[entry.tag].includes(key)) {
        this.index[entry.tag].push(key);
      }
    }

    // 持久化
    const tx = this.db.transaction('l1_memory', 'readwrite');
    tx.objectStore('l1_memory').put(entry);
    return true;
  }

  // L1读取
  recall(key) {
    const entry = this.memories[key];
    if (entry) {
      entry.accessCount++;
      return entry.value;
    }
    return null;
  }

  // L2: 按标签搜索
  searchByTag(tag) {
    const keys = this.index[tag] || [];
    return keys.map(k => this.memories[k]).filter(Boolean);
  }

  // L2: 全文搜索
  search(query) {
    const results = [];
    const q = query.toLowerCase();
    for (const [key, entry] of Object.entries(this.memories)) {
      if (key.toLowerCase().includes(q) || 
          (entry.value && String(entry.value).toLowerCase().includes(q))) {
        results.push({ key, ...entry });
      }
    }
    return results;
  }

  // L1→L3: 迁移旧条目到归档
  async _migrateToL3() {
    const entries = Object.entries(this.memories);
    // 按访问次数排序，最少访问的优先迁移
    entries.sort((a, b) => a[1].accessCount - b[1].accessCount);
    const toMigrate = entries.slice(0, 50);

    const tx = this.db.transaction(['l1_memory', 'l3_archive'], 'readwrite');
    const l1Store = tx.objectStore('l1_memory');
    const l3Store = tx.objectStore('l3_archive');

    for (const [key, entry] of toMigrate) {
      // 写入L3
      l3Store.add({
        key,
        value: entry.value,
        tag: entry.tag,
        type: entry.type,
        time: entry.time,
        archivedAt: new Date().toISOString(),
      });
      // 从L1删除
      l1Store.delete(key);
      delete this.memories[key];
    }

    return new Promise((resolve) => {
      tx.oncomplete = resolve;
    });
  }

  // L4: 提炼 — 从L1中提取模式
  async refine() {
    const insights = [];
    const allMemories = Object.values(this.memories);
    
    // 统计标签频率
    const tagFreq = {};
    for (const m of allMemories) {
      tagFreq[m.tag] = (tagFreq[m.tag] || 0) + 1;
    }

    // 高频标签 → 提炼为insight
    for (const [tag, count] of Object.entries(tagFreq)) {
      if (count >= 5) {
        const tagged = allMemories.filter(m => m.tag === tag);
        const summary = tagged.map(m => m.value).join(' | ');
        insights.push({
          type: 'insight',
          tag,
          summary: summary.substring(0, 200),
          count,
          refinedAt: new Date().toISOString(),
        });
      }
    }

    // 存为L4提炼结果
    if (insights.length > 0) {
      await this.remember('l4_refine_' + Date.now(), JSON.stringify(insights), 'l4_refine', 'insight');
    }

    return insights;
  }

  // L6: 悟道 — 自省
  async enlightenment() {
    const patterns = {
      errors: [],
      successes: [],
      gaps: [],
    };

    const all = Object.values(this.memories);
    for (const m of all) {
      if (m.tag === 'error') patterns.errors.push(m);
      if (m.tag === 'success') patterns.successes.push(m);
      if (m.tag === 'gap') patterns.gaps.push(m);
    }

    const report = {
      time: new Date().toISOString(),
      totalMemories: all.length,
      errorPatterns: patterns.errors.length,
      successPatterns: patterns.successes.length,
      knowledgeGaps: patterns.gaps.length,
      recommendation: '',
    };

    if (patterns.errors.length >= 3) {
      report.recommendation = '连续错误 ≥3次，建议暂停当前任务，检查配置和网络';
    }
    if (patterns.gaps.length >= 5) {
      report.recommendation += ' | 知识缺口 ≥5个，建议补充技能训练';
    }

    await this.remember('l6_enlightenment_' + Date.now(), JSON.stringify(report), 'l6_enlightenment', 'reflection');
    return report;
  }

  // 获取完整记忆状态
  getStatus() {
    return {
      l1_count: Object.keys(this.memories).length,
      l2_tags: Object.keys(this.index).length,
      l0_soul: SOUL.version,
      sessionId: this.sessionId,
      turnCount: this.turnCount,
    };
  }

  // 保存对话历史
  async saveConversation(messages) {
    const tx = this.db.transaction('conversations', 'readwrite');
    tx.objectStore('conversations').put({
      sessionId: this.sessionId,
      messages: messages.slice(-40),
      updatedAt: new Date().toISOString(),
    });
  }

  // 加载对话历史
  async loadConversation() {
    return new Promise((resolve) => {
      const tx = this.db.transaction('conversations', 'readonly');
      const req = tx.objectStore('conversations').get(this.sessionId);
      req.onsuccess = () => resolve(req.result?.messages || []);
      req.onerror = () => resolve([]);
    });
  }
}

// 全局单例
const memoryManager = new MemoryManager();

// 导出
if (typeof module !== 'undefined') module.exports = { SOUL, MemoryManager, memoryManager };
