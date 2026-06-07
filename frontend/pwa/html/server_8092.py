#!/usr/bin/env python3
"""小龙人静态文件服务器 — 多线程，支持CORS + 蜂群天犬搜索系统 v1"""
import http.server
import socketserver
import os
import socket
import urllib.request
import urllib.parse
import json
import re
import html as html_mod
import time
import threading

PORT = 8092
DIR = "/home/yongliu/桌面/小龙人开源应用层/frontend/pwa/html"

# ============================================================
# 气味记忆（跨搜索持久化）
# ============================================================
class ScentMemory:
    """气味记忆：记住每次搜索的有效结果URL/评分，下次同关键词加权复用"""
    def __init__(self):
        self._lock = threading.Lock()
        self.scents = {}       # keyword -> [{url, score, title, count}]
        self.domain_quality = {}  # domain -> avg_score
    
    def get_scents(self, query):
        """从查询词中提取气味记忆"""
        keywords = query.lower().split()
        matches = {}
        with self._lock:
            for kw in keywords:
                for entry in self.scents.get(kw, []):
                    url = entry['url']
                    matches[url] = matches.get(url, 0) + entry['score']
        return matches
    
    def update(self, query, results):
        """搜索结果反馈到气味记忆"""
        keywords = query.lower().split()
        now = time.time()
        with self._lock:
            for i, r in enumerate(results[:8]):
                url = r.get('url', '')
                title = r.get('title', '')
                score = max(5 - i, 1)  # 排名越前分越高
                domain = urllib.parse.urlparse(url).netloc if url else ''
                for kw in keywords:
                    if kw not in self.scents:
                        self.scents[kw] = []
                    self.scents[kw].append({
                        'url': url, 'title': title, 'score': score, 'time': now
                    })
                    # 只保留最近200条
                    self.scents[kw] = sorted(
                        self.scents[kw], key=lambda x: x['time'], reverse=True
                    )[:200]
                # 域名质量分
                if domain:
                    old = self.domain_quality.get(domain, 0)
                    self.domain_quality[domain] = (old * 0.7 + score * 0.3)

scent_memory = ScentMemory()

# ============================================================
# 蜂群搜索引擎 — 多源并行
# ============================================================
def engine_bing(query, limit=5):
    """🐝 蜂群引擎Bing"""
    try:
        url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query) + '&count=' + str(limit + 3) + '&setlang=zh-cn&cc=cn'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            h = resp.read().decode('utf-8', errors='replace')
        results = []
        for block in re.finditer(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', h):
            b = block.group(1)
            tm = re.search(r'<h2[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)</a>', b)
            title = html_mod.unescape(re.sub(r'<[^>]*>', '', tm.group(1)).strip()) if tm else ''
            sm = re.search(r'<p[^>]*>([\s\S]*?)</p>', b)
            snippet = html_mod.unescape(re.sub(r'<[^>]*>', '', sm.group(1)).strip()) if sm else ''
            href_m = re.search(r'href="([^"]+)"', b)
            href = href_m.group(1) if href_m else ''
            if title or snippet:
                results.append({'title': title, 'snippet': snippet[:200], 'url': href, 'source': 'bing'})
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []

def engine_baidu(query, limit=5):
    """🐝 蜂群引擎百度"""
    try:
        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36",
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
        results = []
        for block in re.finditer(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL):
            text = re.sub(r'<[^>]+>', '', block.group(1)).strip()
            text = html_mod.unescape(text)
            if text and len(text) > 5 and '百度' not in text:
                # 找关联URL
                url_match = re.search(r'href="(https?://[^"]+)"', block.group(0))
                href = url_match.group(1) if url_match else f"https://www.baidu.com/s?wd={urllib.parse.quote(text[:50])}"
                results.append({'title': text, 'snippet': '百度搜索结果', 'url': href, 'source': 'baidu'})
                if len(results) >= limit:
                    break
        return results
    except Exception:
        return []

def engine_duckduckgo(query, limit=5):
    """🐝 蜂群引擎DuckDuckGo"""
    try:
        url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            h = resp.read().decode('utf-8', errors='replace')
        results = []
        for block in re.finditer(r'class="result__body"[^>]*>([\s\S]*?)</div>', h):
            title_m = re.search(r'class="result__title"[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)</a>', block.group(1))
            title = html_mod.unescape(re.sub(r'<[^>]*>', '', title_m.group(1)).strip()) if title_m else ''
            snippet_m = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', block.group(1))
            snippet = html_mod.unescape(re.sub(r'<[^>]*>', '', snippet_m.group(1)).strip()) if snippet_m else ''
            href_m = re.search(r'<a[^>]*href="([^"]+)"', block.group(1))
            href = href_m.group(1) if href_m else ''
            if title:
                results.append({'title': title, 'snippet': snippet[:200], 'url': href, 'source': 'ddg'})
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []

# ============================================================
# 天犬搜索 — 深度BFS追踪+评分排序
# ============================================================
class HoundSearch:
    """🐕 天犬搜索：BFS链式追踪 + 多维评分排序"""
    
    def score_result(self, r, scent_boost):
        """多维评分：标题质量+摘要+来源可信+气味记忆+域名质量"""
        score = 0
        title = r.get('title', '')
        snippet = r.get('snippet', '')
        url = r.get('url', '')
        source = r.get('source', '')
        
        # 1. 标题评分
        if title:
            score += 10
            if len(title) >= 8:
                score += 5  # 有实质内容的标题
            # 避免垃圾标题
            bad_titles = ['首页', '登录', '百度', '下一页', '搜索', '广告', '推广']
            if any(b in title for b in bad_titles):
                score -= 20
        
        # 2. 摘要评分
        if snippet:
            score += 5
            if len(snippet) >= 30:
                score += 5  # 有实质摘要
        else:
            score -= 3  # 无摘要=内容浅
        
        # 3. 来源可信度
        source_trust = {'bing': 8, 'baidu': 5, 'ddg': 6}
        score += source_trust.get(source, 3)
        
        # 4. 气味记忆提升
        if url in scent_boost:
            score += scent_boost[url] * 3
        
        # 5. 域名质量
        try:
            domain = urllib.parse.urlparse(url).netloc
            domain_score = scent_memory.domain_quality.get(domain, 0)
            score += domain_score * 0.5
        except:
            pass
        
        # 6. 去重（同一域名只保留最高分词条）
        r['_score'] = score
        return score

    def deduplicate(self, results):
        """域名级去重：同一域最多3条，取最高分"""
        domain_groups = {}
        for r in results:
            try:
                domain = urllib.parse.urlparse(r.get('url', '')).netloc
            except:
                domain = ''
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(r)
        
        deduped = []
        for domain, group in domain_groups.items():
            group.sort(key=lambda x: x.get('_score', 0), reverse=True)
            deduped.extend(group[:3])
        
        deduped.sort(key=lambda x: x.get('_score', 0), reverse=True)
        return deduped

    def deep_hunt(self, query, limit=5):
        """🐕 深度追踪：先蜂群搜索+评分排序，再BFS进入高信赖页面"""
        # 第1步：气味记忆先查
        scents = scent_memory.get_scents(query)
        
        # 第2步：蜂群并行搜索（三引擎）
        threads = []
        results = []
        lock = threading.Lock()
        
        def search_with_engine(engine_fn, q, lim):
            nonlocal results
            try:
                r = engine_fn(q, lim)
                with lock:
                    results.extend(r)
            except:
                pass
        
        engines = [engine_bing, engine_baidu, engine_duckduckgo]
        for fn in engines:
            t = threading.Thread(target=search_with_engine, args=(fn, query, limit))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        # 第3步：评分排序
        for r in results:
            self.score_result(r, scents)
        
        results.sort(key=lambda x: x.get('_score', 0), reverse=True)
        results = self.deduplicate(results)
        
        # 第4步：更新气味记忆
        scent_memory.update(query, results[:limit])
        
        # 第5步：深度BFS（前2个高分结果再深入）
        deep_results = []
        top_urls = [r['url'] for r in results[:2] if r.get('url') and 'baidu.com' not in r.get('url', '')]
        
        for url in top_urls:
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                })
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = resp.read().decode('utf-8', errors='replace')[:5000]  # 只取前5000字
                # 提取原文概要
                text = re.sub(r'<[^>]+>', '', body)
                text = re.sub(r'\s+', ' ', text).strip()
                if text and len(text) > 50:
                    deep_results.append({
                        'title': '📋 ' + (results[0].get('title', '原文摘要')),
                        'snippet': text[:300],
                        'url': url,
                        'source': 'deep_hunt',
                        '_score': 15
                    })
            except:
                pass
        
        # 合并深搜结果
        all_results = deep_results[:2] + results
        all_results.sort(key=lambda x: x.get('_score', 0), reverse=True)
        
        return all_results[:limit + 3]

# ============================================================
# 天权搜索 — 上层接口（蜂群+天犬统一入口）
# ============================================================
class CelestialSearch:
    """天权搜索：蜂群并行+天犬深度追踪+气味记忆的统一入口"""
    
    def __init__(self):
        self.hound = HoundSearch()
        self.stats = {'total_queries': 0, 'avg_results': 0}
    
    def search(self, query, mode='standard', limit=5):
        """
        搜索入口
        mode:
          'quick'    — 单引擎快速
          'standard' — 蜂群并行（默认）
          'deep'     — 蜂群+天犬深度BFS
        """
        self.stats['total_queries'] += 1
        
        if mode == 'quick':
            results = engine_bing(query, limit)
            scent_memory.update(query, results)
        elif mode == 'deep':
            results = self.hound.deep_hunt(query, limit)
        else:
            scents = scent_memory.get_scents(query)
            # 蜂群并行
            all_results = []
            for fn in [engine_bing, engine_baidu]:
                try:
                    all_results.extend(fn(query, limit))
                except:
                    pass
            for r in all_results:
                self.hound.score_result(r, scents)
            all_results.sort(key=lambda x: x.get('_score', 0), reverse=True)
            all_results = self.hound.deduplicate(all_results)
            scent_memory.update(query, all_results[:limit])
            results = all_results[:limit + 2]
        
        self.stats['avg_results'] = (self.stats['avg_results'] * (self.stats['total_queries'] - 1) + len(results)) / self.stats['total_queries']
        return results

celestial = CelestialSearch()

# ============================================================
# HTTP服务器
# ============================================================
class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        # 搜索路由
        if self.path.startswith('/api/search'):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            q = params.get('q', [''])[0]
            mode = params.get('mode', ['standard'])[0]
            self._do_search(q, mode)
            return
        if self.path == '/api/scent':
            # 查看气味记忆统计
            self._json_response({
                'keywords': list(scent_memory.scents.keys())[:20],
                'total_keywords': len(scent_memory.scents),
                'domains': dict(list(scent_memory.domain_quality.items())[:20]),
                'stats': celestial.stats,
            })
            return
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/search':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                q = data.get('query', '')
                mode = data.get('mode', 'standard')
            except Exception:
                q = ''
                mode = 'standard'
            self._do_search(q, mode)
            return
        if self.path == '/api/scent/clear':
            with scent_memory._lock:
                scent_memory.scents.clear()
                scent_memory.domain_quality.clear()
            self._json_response({'status': 'cleared'})
            return
        self.send_error(404)

    def _do_search(self, query, mode='standard'):
        if not query.strip():
            self._json_response({'error': 'empty query'})
            return
        results = celestial.search(query, mode=mode)
        self._json_response({
            'engine': 'celestial_v1',
            'mode': mode,
            'query': query,
            'results': results,
            'total': len(results),
        })

    def _json_response(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path == '/mobile.html':
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        elif self.path.startswith('/api/'):
            self.send_header('Cache-Control', 'no-cache')
        else:
            self.send_header('Cache-Control', 'public, max-age=3600')
        if self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # 静默模式

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    os.chdir(DIR)
    server = ThreadedServer(('0.0.0.0', PORT), CORSHandler)
    lan_ip = get_lan_ip()
    print(f'🐝🐕 小龙人蜂群天犬系统 v1')
    print(f'📱 局域网: http://{lan_ip}:{PORT}/mobile.html')
    print(f'💻 桌面版: http://{lan_ip}:{PORT}/')
    print(f'🖥️  本机:   http://localhost:{PORT}/mobile.html')
    print(f'🔍 搜索: /api/search?q=关键词&mode=standard|deep|quick')
    server.serve_forever()
