#!/usr/bin/env python3
"""
平行时空 PSP — 启动器
端口 6337（冷门端口，不与现有服务冲突）
"""
import http.server
import json
import os
import sys
import urllib.request
import webbrowser
from pathlib import Path

PORT = 6337
BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"

# 后端API转发代理
API_TARGET = None  # 启动后由配置决定

class PSPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def do_POST(self):
        if self.path == '/v1/chat/completions':
            self._proxy_chat()
        elif self.path == '/api/chat':
            self._engine_chat()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def _engine_chat(self):
        """/api/chat 引擎接口 — 接收前端消息，转发到配置的大模型API"""
        content_len = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_len))
        
        message = body.get('message', '')
        provider = body.get('provider', 'deepseek')
        lang = body.get('lang', 'zh')
        
        # 从配置读取API地址和Key（暂时从headers或默认值）
        api_url = self.headers.get('X-API-URL', '')
        api_key = self.headers.get('X-API-Key', '')
        
        # 构建模型映射
        model_map = {
            'deepseek': 'deepseek-chat',
            'openai': 'gpt-4o',
            'anthropic': 'claude-sonnet-4',
            'openrouter': 'deepseek/deepseek-chat'
        }
        model = model_map.get(provider, 'deepseek-chat')
        
        if not api_url:
            # 默认走DeepSeek
            api_url = 'https://api.deepseek.com/v1/chat/completions'
            api_key = api_key or 'sk-bootstrapping'
        
        system_prompt = f"你叫小龙人，运行在平行时空PSP上。回答简洁直接有性格，不啰嗦。当前语言: {lang}"
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': message}
            ],
            'stream': False
        }
        
        try:
            req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode(),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}' if api_key else ''
                },
                method='POST'
            )
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read())
            reply = data.get('choices', [{}])[0].get('message', {}).get('content', '（无响应）')
            self._json_resp(200, {'reply': reply, 'tools': ['web_search', 'file_ops']})
        except Exception as e:
            self._json_resp(502, {'reply': f'引擎连接失败: {str(e)}'})

    def _proxy_chat(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        
        # 转发到用户配置的API地址
        target = self.headers.get('X-API-URL', '')
        api_key = self.headers.get('X-API-Key', '')
        
        if not target:
            self._json_resp(400, {"error": "未配置API地址"})
            return
        
        try:
            req = urllib.request.Request(
                target,
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}' if api_key else '',
                },
                method='POST'
            )
            resp = urllib.request.urlopen(req, timeout=60)
            self.send_response(resp.status)
            self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self._json_resp(e.code, {"error": str(e)})
        except urllib.error.URLError as e:
            self._json_resp(502, {"error": f"连接失败: {e.reason}"})
        except Exception as e:
            self._json_resp(500, {"error": str(e)})
    
    def _json_resp(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass  # 静默日志，不刷屏

def main():
    # 创建前端目录
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    
    # 检查index.html是否存在
    index_html = FRONTEND_DIR / "index.html"
    if not index_html.exists():
        print("❌ 未找到前端文件")
        return 1
    
    server = http.server.HTTPServer(('0.0.0.0', PORT), PSPHandler)
    
    print()
    print("=" * 50)
    print("  🐉 平行时空 PSP 已启动")
    print(f"  🌐 http://{_get_local_ip()}:{PORT}")
    print(f"  🌐 http://127.0.0.1:{PORT}")
    print("=" * 50)
    print()
    print("  浏览器打开后，点击⚙️配置你的API Key和模型")
    print("  按 Ctrl+C 停止")
    print()
    
    # 自动打开浏览器
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    except:
        pass
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 已停止")
        server.server_close()
    return 0

def _get_local_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

if __name__ == '__main__':
    sys.exit(main())
