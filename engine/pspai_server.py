#!/usr/bin/env python3
"""
PSPAI 后端服务 v2 — 基于 Hermes 引擎
端口 8089，运行在 Hermes AIAgent 上，拥有完整工具链

架构：
  UI(8088) → pspai_server.py(8089) → Hermes AIAgent → DeepSeek API + 31工具
                                            ↑
                                    和玉龙同一套引擎
                                    人格由PSPAI config控制
"""
import http.server
import json
import os
import sys
import re
import time
import urllib.parse
import threading
from pathlib import Path

# ============================================================
# Hermes 引擎初始化
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

os.environ['HERMES_HOME'] = str(BASE_DIR)
sys.path.insert(0, os.path.expanduser('~/hermes-agent'))

from hermes_cli.env_loader import load_hermes_dotenv
load_hermes_dotenv(hermes_home=str(BASE_DIR))

import yaml

# 加载PSPAI配置 — 优先当前目录（客户可编辑），兜底同目录（PyInstaller内）
_config_paths = [
    Path.cwd() / 'config.yaml',
    BASE_DIR / 'config.yaml',
]
_config_loaded = False
CONFIG = {}
for _cp in _config_paths:
    if _cp.exists():
        with open(_cp) as f:
            CONFIG = yaml.safe_load(f)
        _config_loaded = True
        break
if not _config_loaded:
    print("⚠ 未找到 config.yaml，使用默认配置")

# 多语言人格 — 从 config.yaml 加载，加语言=加配置
AGENT_CFG = CONFIG.get('agent', {})
PSPAI_PROMPTS = {}
for key in AGENT_CFG:
    if key.startswith('system_prompt_'):
        lang_code = key.replace('system_prompt_', '')
        PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]

# 兜底: system_prompt (旧命名兼容)
if 'zh' not in PSPAI_PROMPTS and 'system_prompt' in AGENT_CFG:
    PSPAI_PROMPTS['zh'] = AGENT_CFG['system_prompt']

DEFAULT_PROMPT = PSPAI_PROMPTS.get('zh', '你是PSPAI，平行时空AI。')
PROVIDER = AGENT_CFG.get('provider', 'deepseek')

# 多语言消息
PSPAI_MSGS = {
    'zh': {'empty': '请说点什么吧。', 'thinking': '（思考中，请稍后再试）', 'error': '抱歉，出了点问题'},
    'en': {'empty': 'Please say something.', 'thinking': '(Thinking, please try again)', 'error': 'Sorry, something went wrong'},
}
def t_msg(lang, key):
    return PSPAI_MSGS.get(lang, PSPAI_MSGS['zh']).get(key, PSPAI_MSGS['zh'][key])

API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
BASE_URL = 'https://api.deepseek.com/v1'

from run_agent import AIAgent

# 覆盖web_search — 用HN API + Google News，免API Key
import pspai_search  # noqa: F401 — side effect: 注册web_search工具

# ============================================================
# Agent 实例管理 — 每个角色一个Agent（保持对话上下文）
# ============================================================
agents = {}       # key: char_index -> AIAgent
agent_lock = threading.Lock()

def get_agent(char_index, char_name):
    """获取或创建角色的AIAgent实例"""
    key = str(char_index)
    with agent_lock:
        if key not in agents:
            agent = AIAgent(
                model='deepseek-chat',
                provider='deepseek',
                api_key=API_KEY,
                base_url=BASE_URL,
                ephemeral_system_prompt=DEFAULT_PROMPT,
                skip_context_files=True,
                skip_memory=True,
                max_iterations=5,
                quiet_mode=True,
            )
            agents[key] = agent
        return agents[key]

# ============================================================
# 数据层
# ============================================================
def load_json(name, default=None):
    path = DATA_DIR / f"{name}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(name, data):
    with open(DATA_DIR / f"{name}.json", 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 头像存储
# ============================================================
import base64

def save_avatar(slot, data_url):
    avatars_dir = DATA_DIR / "avatars"
    avatars_dir.mkdir(exist_ok=True)
    header, encoded = data_url.split(",", 1)
    ext = "png"
    if "jpeg" in header or "jpg" in header:
        ext = "jpg"
    elif "png" in header:
        ext = "png"
    elif "gif" in header:
        ext = "gif"
    filename = f"custom_{slot}.{ext}"
    filepath = avatars_dir / filename
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(encoded))
    return f"/api/avatars/{filename}"

# ============================================================
# 会话历史 — 持久化到JSON
# ============================================================
conversation_history = load_json('conversations', {})

def get_history(char_index):
    key = str(char_index)
    if key not in conversation_history:
        conversation_history[key] = []
    return conversation_history[key]

def add_to_history(char_index, role, content):
    key = str(char_index)
    if key not in conversation_history:
        conversation_history[key] = []
    conversation_history[key].append({"role": role, "content": content})
    # 最多保留40条
    if len(conversation_history[key]) > 40:
        conversation_history[key] = conversation_history[key][-40:]
    save_json('conversations', conversation_history)

# ============================================================
# HTTP 请求处理
# ============================================================

class PSPAIHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[PSPAI] {args[0]}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 头像图片
        if path.startswith("/api/avatars/"):
            avatar_path = DATA_DIR / "avatars" / os.path.basename(path)
            if avatar_path.exists():
                with open(avatar_path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                ct = "image/jpeg" if path.endswith(".jpg") else "image/png"
                self.send_header("Content-Type", ct)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", len(data))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send_json({"error": "not found"}, 404)
            return

        # 状态
        if path == "/api/status":
            self._send_json({
                "name": "PSPAI",
                "version": "v2.0",
                "engine": "Hermes",
                "tools": 31,
                "status": "running",
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            return

        # 获取名字
        if path == "/api/names":
            names = load_json("names", {})
            self._send_json(names)
            return

        # 获取头像列表
        if path == "/api/avatars_list":
            avatars = []
            for i in range(3):
                for ext in ["jpg", "png", "gif"]:
                    apath = DATA_DIR / "avatars" / f"custom_{i}.{ext}"
                    if apath.exists():
                        avatars.append({
                            "slot": i,
                            "url": f"/api/avatars/custom_{i}.{ext}"
                        })
                        break
            self._send_json({"avatars": avatars})
            return

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 对话 — 通过 Hermes AIAgent 处理
        if path == "/api/chat":
            data = self._read_body()
            msg = data.get("message", "")
            char_index = data.get("charIndex", 0)
            char_name = data.get("charName", "PSPAI")
            lang = data.get("lang", "zh")

            if not msg:
                self._send_json({"reply": t_msg(lang, 'empty')})
                return

            # 加载名字
            names = load_json("names", {})
            current_name = names.get(str(char_index), char_name)

            # 语言选择 — 字典查找，加语言=加配置
            system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)

            # 添加上下文到消息
            context_msg = f"[当前角色名：{current_name}] {msg}"

            # 获取Agent并对话
            try:
                agent = get_agent(char_index, current_name)
                history = get_history(char_index)

                # 检测改名意图
                rename_match = re.search(r"(?:叫你|叫你叫|把你叫|改名为|改名[为]?|叫)(.+)", msg)
                if rename_match:
                    new_name = rename_match.group(1).strip()[:10]
                    names[str(char_index)] = new_name
                    save_json("names", names)
                    # 要求agent用新名字回复
                    context_msg = f"[当前角色名：{current_name}] 用户给你改名为「{new_name}」。请用新名字回应。用户说：{msg}"

                # 调用 Hermes AIAgent
                result = agent.run_conversation(
                    user_message=context_msg,
                    system_message=system_prompt,
                )
                reply = result.get('final_response', '') if result else ''

                if not reply:
                    reply = t_msg(lang, 'thinking')

                # 检测回复中的改名标记 [NAME:新名字]
                name_match = re.search(r'\[NAME:\s*([^\]]+)\]', reply)
                if name_match:
                    new_name = name_match.group(1).strip()[:10]
                    names[str(char_index)] = new_name
                    save_json("names", names)
                    reply = re.sub(r'\s*\[NAME:[^\]]+\]', '', reply)
                    self._send_json({
                        "reply": reply,
                        "nameChanged": True,
                        "newName": new_name,
                        "charIndex": char_index,
                    })
                    return

                self._send_json({"reply": reply, "nameChanged": False})

            except Exception as e:
                print(f"[PSPAI Chat Error] {e}")
                self._send_json({"reply": f"{t_msg(lang, 'error')}：{str(e)[:50]}"})
            return

        # 改名
        if path == "/api/name":
            data = self._read_body()
            char_index = data.get("charIndex", 0)
            new_name = data.get("name", "")
            if not new_name:
                self._send_json({"error": "name required"}, 400)
                return
            names = load_json("names", {})
            names[str(char_index)] = new_name
            save_json("names", names)
            self._send_json({"success": True, "name": new_name})
            return

        # 上传头像
        if path == "/api/avatar":
            data = self._read_body()
            slot = data.get("slot", 0)
            data_url = data.get("image", "")
            if not data_url:
                self._send_json({"error": "image required"}, 400)
                return
            url = save_avatar(slot, data_url)
            self._send_json({"success": True, "url": url, "slot": slot})
            return

        self._send_json({"error": "not found"}, 404)


def main():
    port = 8089

    if not API_KEY:
        print("❌ 未找到 DEEPSEEK_API_KEY，请在 .env 中配置")
        sys.exit(1)

    print("🟢 PSPAI v2 后端服务启动 — 基于 Hermes 引擎")
    print(f"   端口: {port}")
    print(f"   引擎: Hermes AIAgent")
    print(f"   工具: 31个（terminal/file/search/memory/git/ssh...）")
    print(f"   模型: DeepSeek Chat")
    print(f"   人格: PSPAI 数字生命体")
    print(f"   数据: {DATA_DIR}")

    server = http.server.HTTPServer(("0.0.0.0", port), PSPAIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🔴 PSPAI 已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
