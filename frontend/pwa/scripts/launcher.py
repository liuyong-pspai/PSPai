#!/usr/bin/env python3
"""
小龙人电脑版启动器 v1.0
- 启动后端引擎 + HTTP服务器(8089端口)
- 自动打开浏览器进入UI
- 用户直接在UI里配模型API

用法：python3 launcher.py
"""

import http.server
import json
import os
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path
from socketserver import ThreadingMixIn

ROOT = Path(__file__).parent.resolve()
PORT = 8089

# ── 引擎导入 ──
sys.path.insert(0, str(ROOT))
try:
    from xiaolongren_engine import XiaoLongRen
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    print("⚠️ xiaolongren-engine.py 未找到，引擎功能不可用")


class XiaoLongRenServer(ThreadingMixIn, http.server.HTTPServer):
    """多线程HTTP服务器"""
    daemon_threads = True


class Handler(http.server.SimpleHTTPRequestHandler):
    """处理API请求 + 静态文件"""

    engine = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path == '/api/chat':
            self._handle_chat()
        elif self.path == '/api/name':
            self._handle_name()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == '/api/health':
            self._handle_health()
        elif self.path == '/api/config-file':
            self._handle_config_check()
        else:
            # 检查是否有config，没有则重定向
            cfg = ROOT / 'config.json'
            if self.path == '/config.html' and not cfg.exists():
                # 返回配置页面
                super().do_GET()
            else:
                super().do_GET()

    def _ensure_engine(self):
        """延迟初始化引擎（等用户配置API Key后）"""
        if not ENGINE_AVAILABLE:
            return False
        try:
            cfg_file = ROOT / 'config.json'
            if cfg_file.exists():
                cfg = json.loads(cfg_file.read_text())
                api_key = cfg.get('api_key', '')
                provider = cfg.get('provider', 'deepseek')
                model = cfg.get('model', 'deepseek-chat')
                if api_key:
                    if not Handler.engine:
                        Handler.engine = XiaoLongRen(api_key, provider, model)
                        print(f"✅ 引擎已就绪: {provider}/{model}")
                    return True
            return False
        except Exception as e:
            print(f"引擎初始化失败: {e}")
            return False

    def _handle_chat(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))

            if not self._ensure_engine():
                self._json_response({
                    'reply': '请先配置API Key。\n\n点右上角 ⚙ 设置，选择模型提供商，填入API Key即可。'
                })
                return

            import asyncio
            msg = body.get('message', '')
            sys_prompt = body.get('charName', '龙渊')
            reply = asyncio.run(Handler.engine.run(msg, sys_prompt))
            self._json_response({'reply': reply})

        except Exception as e:
            self._json_response({'reply': f'引擎出错: {str(e)}'})

    def _handle_health(self):
        status = 'ok' if ENGINE_AVAILABLE else 'degraded'
        self._json_response({'status': status, 'engine': ENGINE_AVAILABLE, 'port': PORT})

    def _handle_name(self):
        self._json_response({'status': 'ok'})

    def _handle_config_check(self):
        cfg = ROOT / 'config.json'
        self._json_response({'exists': cfg.exists()})

    def _json_response(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # 精简日志
        if '/api/' in str(args):
            print(f"  {args[0]}")


def open_browser():
    url = f'http://localhost:{PORT}'
    print(f'🌐 打开浏览器: {url}')
    time.sleep(1)  # 等服务器就绪
    webbrowser.open(url)


def main():
    print(f'🐉 小龙人电脑版启动中...')
    print(f'   根目录: {ROOT}')
    print(f'   端口: {PORT}')

    # 检查config
    cfg = ROOT / 'config.json'
    if cfg.exists():
        print(f'   ✅ 配置文件已就绪')
    else:
        print(f'   📝 首次启动，请先在UI中配置API Key')

    # 创建多线程服务器
    server = XiaoLongRenServer(('0.0.0.0', PORT), Handler)

    print(f'   🚀 服务器已启动: http://localhost:{PORT}')
    print(f'   📱 局域网访问: http://{_get_ip()}:{PORT}')
    print(f'   按 Ctrl+C 退出\n')

    # 打开浏览器
    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 小龙人已退出')
        server.shutdown()


def _get_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


if __name__ == '__main__':
    main()
