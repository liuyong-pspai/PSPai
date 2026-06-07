#!/usr/bin/env python3
"""小龙人静态文件服务器 — 多线程，支持CORS + 搜索代理"""
import http.server
import socketserver
import os
import socket
import urllib.request
import urllib.parse
import json
import re
import html as html_mod

PORT = 8088
DIR = os.path.dirname(os.path.abspath(__file__))

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        # 搜索代理路由
        if self.path.startswith('/api/search?q='):
            self._handle_search()
            return
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/search':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                q = data.get('query', '')
            except Exception:
                q = ''
            self._do_search(q)
            return
        self.send_error(404)

    def _handle_search(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        q = params.get('q', [''])[0]
        self._do_search(q)

    def _do_search(self, query):
        if not query.strip():
            self._json_response({'error': 'empty query'})
            return
        results = self._search_bing(query) or self._search_duck(query) or []
        self._json_response({'engine': 'proxy', 'query': query, 'results': results})

    def _search_bing(self, query):
        """Bing国内版搜索"""
        try:
            url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query) + '&setlang=zh-cn&cc=cn'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
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
                    results.append({'title': title, 'snippet': snippet, 'url': href})
                if len(results) >= 5:
                    break
            return results
        except Exception:
            return None

    def _search_duck(self, query):
        """DuckDuckGo备用"""
        try:
            url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                h = resp.read().decode('utf-8', errors='replace')
            results = []
            for m in re.finditer(r'class="result__snippet"[^>]*>(.*?)</a>', h):
                snippet = html_mod.unescape(re.sub(r'<[^>]*>', '', m.group(1)).strip())
                if snippet:
                    results.append({'title': '', 'snippet': snippet, 'url': ''})
                if len(results) >= 5:
                    break
            return results
        except Exception:
            return None

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
        if not self.path.startswith('/api/'):
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
    print(f'🐉 小龙人已启动')
    print(f'📱 局域网: http://{lan_ip}:{PORT}/mobile.html')
    print(f'💻 桌面版: http://{lan_ip}:{PORT}/')
    print(f'🖥️  本机:   http://localhost:{PORT}/mobile.html')
    server.serve_forever()
