#!/usr/bin/env python3
"""小龙人静态文件服务器 — 多线程，支持CORS"""
import http.server
import socketserver
import os
import socket

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
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
