#!/usr/bin/env python3
"""小龙人静态文件服务器 — 多线程，支持CORS，带缓存头"""
import http.server
import socketserver
import os

PORT = 8088
DIR = os.path.dirname(os.path.abspath(__file__))

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=3600')
        # JSON语言包禁止缓存（方便调试）
        if self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # 静默模式

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    os.chdir(DIR)
    server = ThreadedServer(('0.0.0.0', PORT), CORSHandler)
    print(f'🐉 小龙人静态服务器 → http://0.0.0.0:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
