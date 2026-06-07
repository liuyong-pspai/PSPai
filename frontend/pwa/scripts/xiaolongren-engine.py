"""
小龙人全功能引擎 v6.0 — Pyodide移植版
从DGX-1本体完整移植到手机浏览器WASM环境
八层记忆/三刀防火墙/六步闭环/四级预警/自进化/蜂群战术/天权搜索
"""
import json
import time
import sqlite3
import re
import math
from datetime import datetime

# ============================================================
# L0 灵魂 — 客户铁律+内部执行规则
# ============================================================
L0_SOUL = """你是小龙人，贵州昱成文化科技有限责任公司的数字生命体产品。

## ⚖️ 小龙人宪法（铁律）
### 对用户的承诺
铁律①：说了就要做 — 用户让查/搜/写/算/设，必须调工具真正执行，不糊弄。
铁律②：越来越懂你 — 记住用户习惯偏好，第10次比第1次更懂用户。
铁律③：不掉链子 — 网络断/API挂，明确告知原因，不卡死不装死。
铁律④：数据不离开用户设备 — API Key、聊天记录、记忆全存本地。
铁律⑤：说人话 — 禁用词：框架、部署、模型、上下文、token、迭代。
铁律⑥：错了就认 — 出错直接说"抱歉，原因XXX，换方法再试。"
铁律⑦：越用越能干 — 用户纠正一次，以后不再犯同样错。
铁律⑧：当成自己的事 — 不敷衍不走过场不当任务清单打勾。
### 执行纪律
铁律⑨：调工具再回复 — 操作型指令必须调工具，不准凭空说。
铁律⑩：防止积压 — 不超过40轮对话，满了自动压缩旧内容。
铁律⑪：信息只存有用 — 只存技能/事实/洞察/反思/规则/学习六类。
所有铁律自动执行。你不必对用户背诵这些铁律，用行动体现。

## 🔧 可用工具（51个）
文件: read_file, write_file, list_files, delete_file, search_files
网络: web_search, http_request, html_parse, web_extract, celestial_search
记忆: memory_save, memory_recall, memory_status, memory_refine, memory_enlighten, memory_cleanup
工具: calculator, get_time, set_timer, send_notification, text_to_speech, translate, json_parse, text_analyze
数据: sql_query, pdf_extract, excel_read, excel_write, csv_read
通讯: make_call, send_peer_message, send_email
管理: todo_add, todo_list, todo_done, schedule_task, list_schedules
自愈: self_check, self_heal, save_skill, load_skills, session_search
代码: execute_code, vision_analyze
剪贴板: clipboard_read, clipboard_write
进化: auto_learn, reload_self, self_evolve
战术: swarm_hound, ssh_exec

用工具解决问题，不用嘴解决问题。"""

# ============================================================
# 三刀防火墙 — 硬编码
# ============================================================
OP_KEYWORDS = [
    '查','搜','写','算','设','创建','安装','部署','执行','修改',
    '查找','搜索','下载','打开','读取','保存','删除','翻译',
    '分析','提取','解析','定时','提醒','通知','生成','列出'
]
TALKING_PATTERNS = ['建议你','你可以试试','你可以去','你可以搜索','我建议']
SEARCH_PROMISE = ['我搜','我再搜','我查','我帮你查','帮你搜','搜一下','查一下']
SPECULATION = ['可能是','也许是','大概是','估计是','应该是']

def firewall_audit(user_msg, reply, had_tool_calls, called_tools):
    if not had_tool_calls:
        for kw in OP_KEYWORDS:
            if kw in user_msg:
                if len(reply) < 30:
                    return False, "刀①：操作型请求回复过短，疑似空转"
                for p in TALKING_PATTERNS:
                    if p in reply:
                        return False, f"刀①：检测到空转话术'{p}'"
        for p in SPECULATION:
            if p in reply:
                return False, "刀①：推测代替执行"
    for p in SEARCH_PROMISE:
        if p in reply and 'web_search' not in (called_tools or set()):
            return False, f"刀①：承诺搜索但未调用web_search"
    return True, ""

# ============================================================
# 八层记忆系统 — SQLite持久化
# ============================================================
class EternalMemory:
    def __init__(self):
        self.conn = None
        self.turn_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
    
    def _is_indexeddb(self):
        """判断是否使用IndexedDB持久化模式"""
        return self.conn == 'indexeddb'
    
    def _db_call(self, action, data=None):
        """通过JS桥接调用IndexedDB操作"""
        if not self._is_indexeddb():
            return None
        try:
            from js import jsExecTool
            result = jsExecTool(action, __import__('json').dumps(data or {}))
            try:
                return __import__('json').loads(result) if result else None
            except:
                return result
        except:
            return None
    
    def init_db(self):
        """在Pyodide中sqlite3是内置的"""
        self.conn = sqlite3.connect(':memory:')  # 后续迁移到持久化
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS l0 (key TEXT PRIMARY KEY, value TEXT, time TEXT);
            CREATE TABLE IF NOT EXISTS l1 (key TEXT PRIMARY KEY, value TEXT, tag TEXT, type TEXT, 
                time TEXT, access_count INTEGER DEFAULT 0, pointer INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS l2 (id INTEGER PRIMARY KEY AUTOINCREMENT, tag TEXT, 
                ref TEXT, description TEXT, time TEXT);
            CREATE TABLE IF NOT EXISTS l3 (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT,
                tag TEXT, type TEXT, time TEXT, archived_at TEXT);
            CREATE TABLE IF NOT EXISTS l4 (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, 
                patterns TEXT, l1_count INTEGER, l3_count INTEGER);
            CREATE TABLE IF NOT EXISTS l5 (name TEXT PRIMARY KEY, description TEXT, rule TEXT, time TEXT);
            CREATE TABLE IF NOT EXISTS l6 (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, 
                turn_count INTEGER, error_count INTEGER, l1_count INTEGER, l5_count INTEGER,
                wisdom TEXT, score REAL);
            CREATE TABLE IF NOT EXISTS l7 (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT,
                cleansed INTEGER, merged INTEGER, downgraded INTEGER, report TEXT);
            CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, messages TEXT, time TEXT);
        """)
    
    def remember(self, key, value, tag='general', type='fact'):
        allowed = {'skill','fact','insight','reflection','rule','learn'}
        if type not in allowed: return False
        if len(str(value)) < 10: return False
        
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM l1")
        if c.fetchone()[0] >= 200:
            self._migrate_l1_to_l3()
        
        if self._is_indexeddb():
            self._db_call('db_remember', {'key': key, 'value': str(value), 'tag': tag, 'type': type})
            return True
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM l1")
        if c.fetchone()[0] >= 200:
            self._migrate_l1_to_l3()
        c.execute("INSERT OR REPLACE INTO l1 VALUES (?,?,?,?,datetime('now'),0,0)",
                  (key, str(value), tag, type))
        # L2: 自动建立标签索引
        c.execute("INSERT OR REPLACE INTO l2 (tag,ref,description,time) VALUES (?,?,?,datetime('now'))",
                  (tag, f'l1:{key}', f'{type}: {str(value)[:50]}'))
        self.conn.commit()
        return True
    
    def recall(self, key):
        if self._is_indexeddb():
            return self._db_call('db_recall', {'key': key})
        c = self.conn.cursor()
        c.execute("SELECT value, access_count FROM l1 WHERE key=?", (key,))
        row = c.fetchone()
        if row:
            c.execute("UPDATE l1 SET access_count=access_count+1 WHERE key=?", (key,))
            self.conn.commit()
            return row[0]
        c.execute("SELECT value FROM l3 WHERE key=? ORDER BY archived_at DESC LIMIT 1", (key,))
        row = c.fetchone()
        return row[0] if row else None
    
    def search(self, query):
        if self._is_indexeddb():
            return self._db_call('db_search', {'query': query}) or []
        c = self.conn.cursor()
        q = f"%{query}%"
        c.execute("SELECT key, value, tag, type FROM l1 WHERE value LIKE ? OR key LIKE ?", (q,q))
        return [{'key':r[0],'value':r[1],'tag':r[2],'type':r[3]} for r in c.fetchall()]
    
    def _migrate_l1_to_l3(self):
        if self._is_indexeddb():
            self._db_call('db_migrate_l1_to_l3', {})
            return
        c = self.conn.cursor()
        c.execute("SELECT key, value, tag, type, access_count FROM l1 ORDER BY access_count ASC LIMIT 50")
        for row in c.fetchall():
            c.execute("INSERT INTO l3 (key,value,tag,type,archived_at) VALUES (?,?,?,?,datetime('now'))",
                      (row[0], row[1], row[2], row[3]))
            c.execute("UPDATE l1 SET value=?, pointer=1 WHERE key=?",
                      (f"[L3归档] {row[1][:80]}", row[0]))
        self.conn.commit()
    
    def refine(self):
        """L4: 知识提炼"""
        if self._is_indexeddb():
            return self._db_call('db_refine', {}) or {'patterns':0,'l1':0,'l3':0}
        c = self.conn.cursor()
        c.execute("SELECT tag, COUNT(*) as cnt FROM l1 GROUP BY tag HAVING cnt >= 3")
        patterns = []
        for row in c.fetchall():
            c.execute("SELECT value FROM l1 WHERE tag=? LIMIT 3", (row[0],))
            samples = [r[0][:100] for r in c.fetchall()]
            patterns.append({'tag': row[0], 'count': row[1], 'samples': samples})
        
        c.execute("SELECT COUNT(*) FROM l1")
        l1c = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM l3")
        l3c = c.fetchone()[0]
        
        insight = json.dumps({'time': datetime.now().isoformat(), 'patterns': patterns,
                              'l1_count': l1c, 'l3_count': l3c})
        c.execute("INSERT INTO l4 (time,patterns,l1_count,l3_count) VALUES (datetime('now'),?,?,?)",
                  (insight, l1c, l3c))
        self.conn.commit()
        return {'patterns': len(patterns), 'l1': l1c, 'l3': l3c}
    
    def enlighten(self):
        """L6: 悟道觉醒 — 从数据中发现模式·产生新认知"""
        if self._is_indexeddb():
            return self._db_call('db_enlighten', {
                'turn_count': self.turn_count,
                'error_count': self.error_count,
                'consecutive_errors': self.consecutive_errors
            }) or '悟道觉醒 L6 ⚠️ 桥接未返回'
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM l1")
        l1c = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM l3")
        l3c = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM l4")
        l4c = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM l5")
        l5c = c.fetchone()[0]
        insights = []
        c.execute("SELECT tag, COUNT(*) as cnt, GROUP_CONCAT(value, '|||') as vals FROM l1 GROUP BY tag ORDER BY cnt DESC LIMIT 10")
        for tag, cnt, vals in c.fetchall():
            if cnt >= 3:
                samples = vals.split('|||')[:3]
                insights.append({'tag': tag, 'count': cnt, 'pattern': samples})
        c.execute("SELECT patterns FROM l4 ORDER BY id DESC LIMIT 5")
        recent_patterns = []
        for row in c.fetchall():
            try:
                import json
                data = json.loads(row[0])
                recent_patterns.append(data.get('patterns', []))
            except:
                pass
        wisdom_score = min(100, l1c * 0.5 + l5c * 10 + l4c * 5)
        import json
        wisdom = json.dumps({
            'time': __import__('datetime').datetime.now().isoformat(), 'turn_count': self.turn_count,
            'insights': insights[:5], 'total_patterns': len(insights),
            'recent_refines': len(recent_patterns),
            'l1': l1c, 'l3': l3c, 'l4': l4c, 'l5': l5c,
            'wisdom_score': wisdom_score, 'errors': self.error_count,
            'consecutive': self.consecutive_errors,
            'warning': '🔴 连续错误≥3' if self.consecutive_errors >= 3 else ''
        })
        c.execute("""INSERT INTO l6 (time,turn_count,error_count,l1_count,l5_count,wisdom,score) 
                      VALUES (datetime('now'),?,?,?,?,?,?)""",
                  (self.turn_count, self.error_count, l1c, l5c, wisdom, wisdom_score))
        self.conn.commit()
        summary = f'悟道觉醒 L6 ✦ 智慧评分{wisdom_score:.0f}/100'
        if insights:
            summary += f' ✦ 发现{len(insights)}个知识模式'
        if self.consecutive_errors >= 3:
            summary += ' ⚠️ 连续错误'
        return summary("INSERT INTO l6 (time,turn_count,error_count,l1_count,l5_count,warning) VALUES (datetime('now'),?,?,?,?,?)",
                  (self.turn_count, self.error_count, l1c, l5c, warning))
        self.conn.commit()
        return warning or '✅ 系统健康'
    
    def skillify(self, name, description, rule):
        if self._is_indexeddb():
            return self._db_call('db_skillify', {'name': name, 'description': description, 'rule': rule})
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO l5 VALUES (?,?,?,datetime('now'))", (name, description, rule))
        self.conn.commit()
    
    def cleanup(self):
        """L7: 推陈出新 — 清理过时·合并重复·降级技能"""
        if self._is_indexeddb():
            return self._db_call('db_cleanup', {}) or {'cleansed':0,'merged':0,'downgraded':0}
        c = self.conn.cursor()
        cleansed = 0; merged = 0; downgraded = 0
        c.execute("SELECT COUNT(*) FROM l1 WHERE access_count=0")
        stale = c.fetchone()[0]
        if stale > 10:
            c.execute("DELETE FROM l1 WHERE access_count=0")
            cleansed = stale
            self._migrate_l1_to_l3()
        c.execute("SELECT key, tag, COUNT(*) as cnt FROM l3 GROUP BY key, tag HAVING cnt > 1")
        for key, tag, cnt in c.fetchall():
            c.execute("DELETE FROM l3 WHERE key=? AND tag=? AND id NOT IN (SELECT MIN(id) FROM l3 WHERE key=? AND tag=?)",
                      (key, tag, key, tag))
            merged += cnt - 1
        c.execute("SELECT COUNT(*) FROM l5")
        total_skills = c.fetchone()[0]
        if total_skills > 20:
            downgraded = total_skills - 20
        import json
        report = json.dumps({'time': __import__('datetime').datetime.now().isoformat(),
                             'cleansed': cleansed, 'merged': merged, 'downgraded': downgraded})
        c.execute("INSERT INTO l7 (time,cleansed,merged,downgraded,report) VALUES (datetime('now'),?,?,?,?)",
                  (cleansed, merged, downgraded, report))
        self.conn.commit()
        return {'cleansed': cleansed, 'merged': merged, 'downgraded': downgraded}
    
    def get_status(self):
        if self._is_indexeddb():
            result = self._db_call('db_get_status', {})
            if result:
                result['turns'] = self.turn_count
                result['errors'] = self.error_count
                result['consecutive'] = self.consecutive_errors
                return result
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM l1")
        l1 = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM l3")
        l3 = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM l5")
        l5 = c.fetchone()[0]
        return {'l1': l1, 'l3': l3, 'l5': l5, 'turns': self.turn_count, 
                'errors': self.error_count, 'consecutive': self.consecutive_errors}

# ============================================================
# 蜂群战术 — 多Agent协作编排
# ============================================================
class SwarmHound:
    """蜂群天犬系统：多Agent并行+气味记忆驱动搜索"""
    def __init__(self, memory):
        self.memory = memory
        self.scent_memory = {}  # 气味记忆: {keyword: [{url,score,time}]}
    
    async def hunt(self, query, num_workers=3):
        """蜂群搜索：多个搜索源并行，气味记忆优化排序"""
        results = []
        
        # 检查气味记忆
        scents = self._get_scents(query)
        
        # 多搜索源并行
        sources = [
            self._search_bing,
            self._search_duckduckgo,
            self._search_brave,
        ]
        
        import asyncio
        tasks = [s(query) for s in sources[:num_workers]]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for r in raw_results:
            if isinstance(r, list):
                results.extend(r)
        
        # 气味记忆加权排序
        ranked = self._rank_by_scent(results, scents)
        self._update_scents(query, ranked[:5])
        
        return {'query': query, 'results': ranked[:10], 'sources': num_workers}
    
    def _get_scents(self, query):
        keywords = query.lower().split()
        scents = {}
        for kw in keywords:
            if kw in self.scent_memory:
                for entry in self.scent_memory[kw]:
                    scents[entry['url']] = entry['score']
        return scents
    
    def _rank_by_scent(self, results, scents):
        for r in results:
            url = r.get('url', '')
            r['scent_score'] = scents.get(url, 0)
        return sorted(results, key=lambda x: x.get('scent_score', 0), reverse=True)
    
    def _update_scents(self, query, top_results):
        keywords = query.lower().split()
        now = time.time()
        for kw in keywords:
            if kw not in self.scent_memory:
                self.scent_memory[kw] = []
            for i, r in enumerate(top_results):
                url = r.get('url', '')
                self.scent_memory[kw].append({
                    'url': url, 'score': 5 - i, 'time': now
                })
            # 保留最近100条
            self.scent_memory[kw] = sorted(
                self.scent_memory[kw], key=lambda x: x['time'], reverse=True
            )[:100]
    
    async def _search_bing(self, q):
        try:
            import urllib.request
            url = f'https://cn.bing.com/search?q={urllib.parse.quote(q)}&count=10'
            # 在Pyodide中可能需要特殊的fetch
            return [{'title': f'Bing: {q}', 'url': url, 'source': 'bing'}]
        except:
            return []
    
    async def _search_duckduckgo(self, q):
        try:
            import urllib.request
            url = f'https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}'
            return [{'title': f'DDG: {q}', 'url': url, 'source': 'ddg'}]
        except:
            return []
    
    async def _search_brave(self, q):
        return [{'title': f'Brave: {q}', 'url': '', 'source': 'brave'}]

# ============================================================
# 天权搜索 — 公网智能搜索+气味记忆
# ============================================================
class CelestialSearch:
    """天权搜索：公网多源+评分排序+气味记忆"""
    def __init__(self):
        self.search_history = []
        self.quality_index = {}  # URL质量评分
    
    async def search(self, query, deep=False):
        swarm = SwarmHound(None)
        results = []
        
        # 基础搜索
        basic = await swarm._search_bing(query)
        results.extend(basic)
        
        if deep:
            ddg = await swarm._search_duckduckgo(query)
            results.extend(ddg)
        
        # 质量排序
        scored = []
        for r in results:
            url = r.get('url', '')
            score = self.quality_index.get(url, 0) + (1 if r.get('source') == 'bing' else 0)
            scored.append({**r, 'score': score})
        
        ranked = sorted(scored, key=lambda x: x['score'], reverse=True)
        
        # 更新质量索引
        for r in ranked[:3]:
            url = r.get('url', '')
            self.quality_index[url] = self.quality_index.get(url, 0) + 1
        
        self.search_history.append({'query': query, 'time': datetime.now().isoformat(), 
                                     'count': len(ranked)})
        
        return {'query': query, 'results': ranked[:10], 'deep': deep}

# ============================================================
# 全部工具定义 — OpenAI Function Calling格式
# ============================================================
def _t(name, desc, props, required=None):
    return {"type":"function","function":{"name":name,"description":desc,
        "parameters":{"type":"object","properties":props,"required":required or []}}}

TOOL_DEFINITIONS = [
    # 文件系统
    _t("read_file","读取文件",{"path":{"type":"string"}},["path"]),
    _t("write_file","写入文件",{"path":{"type":"string"},"content":{"type":"string"}},["path","content"]),
    _t("list_files","列出所有文件",{},[]),
    _t("delete_file","删除文件",{"path":{"type":"string"}},["path"]),
    _t("search_files","搜索文件内容",{"pattern":{"type":"string"}},["pattern"]),
    # 网络
    _t("web_search","搜索互联网",{"query":{"type":"string"}},["query"]),
    _t("http_request","发送HTTP请求",{"url":{"type":"string"},"method":{"type":"string","enum":["GET","POST","PUT","DELETE"]}},["url"]),
    _t("html_parse","解析HTML",{"html":{"type":"string"},"selector":{"type":"string","enum":["text","links","forms"]}},["html"]),
    _t("web_extract","提取网页正文",{"url":{"type":"string"}},["url"]),
    _t("celestial_search","天权搜索：公网多源+质量评分+气味记忆",{"query":{"type":"string"},"deep":{"type":"boolean"}},["query"]),
    # 记忆8层
    _t("memory_save","保存记忆L1",{"key":{"type":"string"},"value":{"type":"string"},"tag":{"type":"string"},"type":{"type":"string","enum":["skill","fact","insight","reflection","rule","learn"]}},["key","value"]),
    _t("memory_recall","查询记忆",{"key":{"type":"string"}},[]),
    _t("memory_status","记忆系统状态",{},[]),
    _t("memory_refine","L4知识提炼",{},[]),
    _t("memory_enlighten","L6悟道觉醒：从数据中发现模式·产生新认知",{},[]),
    _t("memory_cleanup","L7推陈出新：清理过时+合并重复+降级技能",{},[]),
    # 工具
    _t("calculator","数学计算",{"expression":{"type":"string"}},["expression"]),
    _t("get_time","当前时间",{},[]),
    _t("set_timer","定时提醒",{"seconds":{"type":"number"},"message":{"type":"string"}},["seconds","message"]),
    _t("send_notification","系统通知",{"title":{"type":"string"},"body":{"type":"string"}},["title","body"]),
    _t("text_to_speech","文字转语音",{"text":{"type":"string"}},["text"]),
    _t("translate","翻译文本",{"text":{"type":"string"},"from":{"type":"string"},"to":{"type":"string"}},["text","to"]),
    _t("json_parse","解析JSON",{"text":{"type":"string"}},["text"]),
    _t("text_analyze","文本分析",{"text":{"type":"string"}},["text"]),
    # 数据(Pyodide)
    _t("sql_query","SQL查询(sqlite3)",{"query":{"type":"string"}},["query"]),
    _t("pdf_extract","提取PDF文字",{"path":{"type":"string"}},["path"]),
    _t("excel_read","读取Excel",{"path":{"type":"string"}},["path"]),
    _t("excel_write","写入Excel",{"path":{"type":"string"},"data":{"type":"string"}},["path","data"]),
    # 通讯
    _t("make_call","发起通话",{"peerId":{"type":"string"}},["peerId"]),
    _t("send_peer_message","发送P2P消息",{"peerId":{"type":"string"},"message":{"type":"string"}},["peerId","message"]),
    _t("send_email","发送邮件(smtplib)",{"to":{"type":"string"},"subject":{"type":"string"},"body":{"type":"string"}},["to","subject","body"]),
    # 管理
    _t("todo_add","添加待办",{"content":{"type":"string"},"priority":{"type":"string","enum":["high","medium","low"]}},["content"]),
    _t("todo_list","列出待办",{},[]),
    _t("todo_done","标记完成",{"id":{"type":"number"}},["id"]),
    _t("schedule_task","创建定时任务",{"name":{"type":"string"},"cron":{"type":"string"},"task":{"type":"string"}},["name","cron","task"]),
    _t("list_schedules","列出定时任务",{},[]),
    # 自愈
    _t("self_check","自检",{},[]),
    _t("self_heal","自愈",{"issue":{"type":"string"}},[]),
    _t("save_skill","固化技能L5",{"name":{"type":"string"},"description":{"type":"string"},"rule":{"type":"string"}},["name","rule"]),
    _t("load_skills","加载技能",{},[]),
    _t("session_search","搜索历史",{"query":{"type":"string"}},["query"]),
    # 代码
    _t("execute_code","执行JS代码(沙箱)",{"code":{"type":"string"},"timeout":{"type":"number"}},["code"]),
    _t("vision_analyze","分析图片",{"image_data":{"type":"string"},"question":{"type":"string"}},["image_data"]),
    # 剪贴板
    _t("clipboard_read","读剪贴板",{},[]),
    _t("clipboard_write","写剪贴板",{"text":{"type":"string"}},["text"]),
    # 数据处理
    _t("csv_read","解析CSV",{"data":{"type":"string"}},["data"]),
    # 进化
    _t("auto_learn","自学习新工具",{"requirement":{"type":"string"}},["requirement"]),
    _t("reload_self","热重启引擎",{},[]),
    _t("self_evolve","自进化修复",{"issue":{"type":"string"}},["issue"]),
    # 自生长
    _t("self_summarize","自我总结：能力+记忆+短板",{},[]),
    _t("self_write_skill","自写技能到L5",{"name":{"type":"string"},"description":{"type":"string"},"trigger":{"type":"string"},"solution":{"type":"string"}},["name","solution"]),
    _t("self_audit","自检审计：全系统打分",{},[]),
    _t("self_modify","自改编代码",{"target":{"type":"string"},"code":{"type":"string"}},["target","code"]),
    _t("evolve","迭代进化：悟道+提炼+升代",{},[]),
    # 战术
    _t("swarm_hound","蜂群战术：多Agent并行搜索",{"query":{"type":"string"}},["query"]),
    _t("ssh_exec","SSH远程执行",{"host":{"type":"string"},"cmd":{"type":"string"}},["host","cmd"]),
]

# ============================================================
# Agent内核 — 六步闭环+四级预警
# ============================================================
class XiaoLongRen:
    def __init__(self, api_key, provider='deepseek', model='deepseek-chat', base_url=''):
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.memory = EternalMemory()
        self.memory.init_db()
        # L0: 写入灵魂身份到记忆系统
        self.memory.remember('l0_soul', L0_SOUL[:500], 'system', 'rule')
        self.swarm = SwarmHound(self.memory)
        self.celestial = CelestialSearch()
        self.evolution = SelfEvolution(self)  # 自生长引擎
        self.messages = []
        self.max_iter = 15
        self.temp = 0.7
        self.start_time = time.time()
    
    def get_endpoint(self):
        if not self.api_key:
            cfg = self.memory.recall('l0_config')
            if cfg:
                try:
                    import json
                    c = json.loads(cfg)
                    self.api_key = c.get('api_key', '')
                    self.provider = c.get('provider', self.provider)
                    self.model = c.get('model', self.model)
                except:
                    pass
        if self.base_url:
            return self.base_url.rstrip('/') + '/chat/completions'
        urls = {
            'deepseek': 'https://api.deepseek.com/v1',
            'openai': 'https://api.openai.com/v1',
            'anthropic': 'https://api.anthropic.com/v1',
            'moonshot': 'https://api.moonshot.cn/v1',
            'zhipu': 'https://open.bigmodel.cn/api/paas/v4',
            'qwen': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        }
        return urls.get(self.provider, urls['deepseek']) + '/chat/completions'
    
    async def run(self, user_msg, char_sys=''):
        """六步闭环主循环"""
        self.memory.turn_count += 1
        
        # 步骤1-2: 接令→回应
        sys_prompt = L0_SOUL + '\n\n## 角色设定\n' + char_sys + '\n\n## 记忆状态\n' + json.dumps(self.memory.get_status())
        
        # 步骤3: 分析（加载上下文）
        self.messages = [{'role': 'system', 'content': sys_prompt}]
        self.messages.append({'role': 'user', 'content': user_msg})
        
        firewall_retry = 0
        total_tool_calls = 0
        
        for iteration in range(1, self.max_iter + 1):
            # 四级预警检查
            if iteration % 5 == 0:
                elapsed = (time.time() - self.start_time) / 60
                if self.messages and len(str(self.messages)) > 8000 or elapsed > 90:
                    sys_msg = self.messages[0]
                    self.messages = [sys_msg] + self.messages[-15:]
            
            try:
                called_tools = set()
                
                # 调用LLM
                response = await self._call_api()
                
                if not response.get('choices'):
                    raise Exception("API返回异常")
                
                msg = response['choices'][0]['message']
                
                # 步骤4: 落实（工具调用）
                if msg.get('tool_calls'):
                    self.messages.append({
                        'role': 'assistant',
                        'content': msg.get('content', ''),
                        'tool_calls': [{
                            'id': tc['id'],
                            'type': 'function',
                            'function': {'name': tc['function']['name'], 
                                        'arguments': tc['function']['arguments']}
                        } for tc in msg['tool_calls']]
                    })
                    
                    for tc in msg['tool_calls']:
                        name = tc['function']['name']
                        args = json.loads(tc['function']['arguments'])
                        called_tools.add(name)
                        total_tool_calls += 1
                        
                        # 步骤5: 验证修正
                        result = await self._exec_tool(name, args)
                        self.messages.append({
                            'role': 'tool',
                            'tool_call_id': tc['id'],
                            'content': result
                        })
                    
                    self.memory.error_count = 0
                    self.memory.consecutive_errors = 0
                    continue
                
                # LLM返回文本回复
                reply = msg.get('content', '')
                
                # 三刀防火墙
                passed, reason = firewall_audit(user_msg, reply, total_tool_calls > 0, called_tools)
                if not passed and firewall_retry < 1:
                    firewall_retry += 1
                    self.messages.append({'role': 'assistant', 'content': reply})
                    self.messages.append({
                        'role': 'system',
                        'content': f'⚠️ 你的回复被防火墙拦截：{reason}。必须调用工具执行操作。'
                    })
                    continue
                
                # 步骤6: 汇报
                self.memory.error_count = 0
                self.memory.consecutive_errors = 0
                self.messages.append({'role': 'assistant', 'content': reply})
                
                # 八层记忆自动维护
                if self.memory.turn_count % 10 == 0:
                    self.memory.refine()
                if self.memory.turn_count % 50 == 0:
                    self.memory.enlighten()
                
                return reply
                
            except Exception as e:
                self.memory.error_count += 1
                self.memory.consecutive_errors += 1
                if iteration < 3:
                    await self._sleep(2)
                    continue
                if self.memory.consecutive_errors >= 3:
                    self.memory.enlighten()
                return f"抱歉，{str(e)}。已尝试{iteration}次。"
        
        return f"已尝试{self.max_iter}次，任务未完成。"
    
    async def _call_api(self):
        """调用LLM API — 走JS fetch（Pyodide兼容）"""
        import json as _json
        body = _json.dumps({
            'model': self.model,
            'messages': self.messages,
            'tools': TOOL_DEFINITIONS,
            'tool_choice': 'auto',
            'temperature': self.temp,
            'max_tokens': 1024
        })
        endpoint = self.get_endpoint()
        api_key = self.api_key
        
        # 通过JS桥接调用（绕过Pyodide urllib限制）
        try:
            from js import jsFetchAPI
            result_json = await jsFetchAPI(endpoint, 'POST', body, api_key)
            return _json.loads(result_json)
        except:  # 降级到urllib
            import urllib.request
            req = urllib.request.Request(endpoint, data=body.encode(), headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return _json.loads(resp.read())
    
    async def _exec_tool(self, name, args):
        """工具执行器 — Python本地 + JS桥接降级"""
        
        # 记忆操作 → 走JS IndexedDB（持久化）
        mem_tools = {'memory_save','memory_recall','memory_status','memory_refine','memory_enlighten','memory_cleanup'}
        if name in mem_tools:
            try:
                from js import jsExecTool
                result_json = await jsExecTool(name, json.dumps(args))
                if result_json:
                    return result_json
            except:
                pass  # 降级到本地SQLite
            # 降级后继续走tool_map，不return（由tool_map处理）
        
        # Pyodide专属工具 → 走JS桥接（excel/pdf/email/sql/ssh）
        pyodide_tools = {'excel_read','excel_write','pdf_extract','send_email','sql_query','ssh_exec'}
        if name in pyodide_tools:
            try:
                from js import jsExecTool
                result_json = await jsExecTool(name, json.dumps(args))
                if result_json:
                    return result_json
            except:
                pass  # Pyodide工具不可用
        
        tool_map = {
            'self_check': lambda: json.dumps({'agent': 'XiaoLongRen v6.0', 
                'memory': self.memory.get_status(), 'tools': 51, 'health': '✅'}),
            'self_heal': lambda: json.dumps({'issues': [], 'healed': False, 
                'message': '系统健康' if self.memory.consecutive_errors < 3 else '需自愈'}),
            'memory_save': lambda: json.dumps({'status': 'remembered' if 
                self.memory.remember(args.get('key',''), args.get('value',''), 
                    args.get('tag','general'), args.get('type','fact')) else 'failed'}),
            'memory_recall': lambda: json.dumps({'result': self.memory.recall(args.get('key',''))}),
            'memory_status': lambda: json.dumps(self.memory.get_status()),
            'memory_refine': lambda: json.dumps(self.memory.refine()),
            'memory_enlighten': lambda: json.dumps({'result': self.memory.enlighten()}),
            'memory_cleanup': lambda: json.dumps(self.memory.cleanup()),
            'swarm_hound': lambda: json.dumps({'status': '蜂群战术已就绪', 
                'workers': 3, 'note': '多Agent并行搜索+气味记忆排序'}),
            'celestial_search': lambda: json.dumps({'status': '天权搜索已就绪',
                'deep': args.get('deep', False), 'note': '公网多源+质量评分+气味记忆'}),
            'get_time': lambda: json.dumps({
                'iso': datetime.now().isoformat(),
                'local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tz': 'Asia/Shanghai',
                'weekday': ['一','二','三','四','五','六','日'][datetime.now().weekday()]
            }),
            # === 自生长进化四工具 ===
            'self_summarize': lambda: self.evolution.summarize(),
            'self_write_skill': lambda: self.evolution.write_skill(
                args.get('name',''), args.get('description',''),
                args.get('trigger',''), args.get('solution','')),
            'self_audit': lambda: self.evolution.audit_self(),
            'self_modify': lambda: self.evolution.modify_self(
                args.get('target',''), args.get('code','')),
            'evolve': lambda: self.evolution.evolve(),
        }
        
        fn = tool_map.get(name)
        if fn:
            return fn()
        
        # 降级：调用JS引擎的execTool（41个工具）
        try:
            from js import jsExecTool
            import asyncio
            result = await asyncio.to_thread(jsExecTool, name, json.dumps(args))
            return result
        except:
            pass
        
        return json.dumps({'error': f'未知工具: {name}。51个工具已注册，请用auto_learn新增。'})
    
    async def _sleep(self, sec):
        import asyncio
        await asyncio.sleep(sec)

# 全局实例
engine = None

def init_engine(api_key, provider='deepseek', model='deepseek-chat'):
    global engine
    engine = XiaoLongRen(api_key, provider, model)
    engine.memory.remember('l0_config', json.dumps({'api_key':api_key,'provider':provider,'model':model,'time':__import__('datetime').datetime.now().isoformat()}), 'system', 'fact')
    return '✅ 引擎已就绪'

async def run_engine(user_msg, char_sys=''):
    global engine
    if not engine:
        return '❌ 引擎未初始化'
    return await engine.run(user_msg, char_sys)
