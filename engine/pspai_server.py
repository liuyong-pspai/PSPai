#!/usr/bin/env python3
"""
PSPAI 后端服务 v3 — 基于 Hermes 引擎 + 记忆回路 + 错误恢复
端口 8089，运行在 Hermes AIAgent 上，拥有完整工具链

v3.0 新增:
  - OperationLogger: 每次对话自动记录结构化日志
  - L1/L2/L3 错误恢复: 重试 + 降级提示 + 失败记录
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

# 加载PSPAI配置
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
    print("WARN: config.yaml not found, using defaults")

AGENT_CFG = CONFIG.get('agent', {})
PSPAI_PROMPTS = {}
for key in AGENT_CFG:
    if key.startswith('system_prompt_'):
        lang_code = key.replace('system_prompt_', '')
        PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]

if 'zh' not in PSPAI_PROMPTS and 'system_prompt' in AGENT_CFG:
    PSPAI_PROMPTS['zh'] = AGENT_CFG['system_prompt']

DEFAULT_PROMPT = PSPAI_PROMPTS.get('zh', 'You are PSPAI.')
PROVIDER = AGENT_CFG.get('provider', 'deepseek')

PSPAI_MSGS = {
    'zh': {'empty': '请说点什么吧。', 'thinking': '（思考中，请稍后再试）', 'error': '抱歉，出了点问题'},
    'en': {'empty': 'Please say something.', 'thinking': '(Thinking, please try again)', 'error': 'Sorry, something went wrong'},
}
def t_msg(lang, key):
    return PSPAI_MSGS.get(lang, PSPAI_MSGS['zh']).get(key, PSPAI_MSGS['zh'][key])

# 统一API Key读取：优先PSPAI_API_KEY（launcher写入），回退DEEPSEEK_API_KEY
API_KEY = os.environ.get('PSPAI_API_KEY') or os.environ.get('DEEPSEEK_API_KEY', '')
# Base URL: 根据provider从config读取，默认DeepSeek
_BASE_URL_MAP = {
    'deepseek': 'https://api.deepseek.com/v1',
    'openai': 'https://api.openai.com/v1',
    'anthropic': 'https://api.anthropic.com/v1',
}
BASE_URL = _BASE_URL_MAP.get(PROVIDER, 'https://api.deepseek.com/v1')

from run_agent import AIAgent
import pspai_search

# ============================================================
# Agent 实例管理
# ============================================================
agents = {}
agent_lock = threading.Lock()

def get_agent(char_index, char_name):
    key = str(char_index)
    with agent_lock:
        if key not in agents:
            # 从config.yaml读取provider/model/max_turns，不再硬编码
            _provider = AGENT_CFG.get('provider', PROVIDER)
            _model = AGENT_CFG.get('model', 'deepseek-chat')
            _max_iters = int(AGENT_CFG.get('max_turns', 8))
            _base_url = _BASE_URL_MAP.get(_provider, BASE_URL)
            agent = AIAgent(
                model=_model,
                provider=_provider,
                api_key=API_KEY,
                base_url=_base_url,
                ephemeral_system_prompt=DEFAULT_PROMPT,
                skip_context_files=True,
                skip_memory=False,
                max_iterations=_max_iters,
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
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(name, data):
    path = DATA_DIR / f"{name}.json"
    content = json.dumps(data, ensure_ascii=False, indent=2)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    # 写入验证：读回确认完整性
    with open(path, encoding='utf-8') as f:
        written = f.read()
    if len(written) < len(content) * 0.99:
        print(f"[PSPAI] WARN: save_json({name}) write verification size mismatch")

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
# 会话历史
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
    if len(conversation_history[key]) > 40:
        conversation_history[key] = conversation_history[key][-40:]
    save_json('conversations', conversation_history)

# ============================================================
# 操作日志 - 记忆回路 v3.0
# ============================================================
class OperationLogger:
    """每次对话自动记录结构化日志，供后续技能提炼使用"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._ops = []
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._save_timer = None
        self._load()
    
    def _path(self):
        return self.data_dir / "chat_operations.json"
    
    def _load(self):
        p = self._path()
        if p.exists():
            try:
                with open(p, encoding='utf-8') as f:
                    raw = json.load(f)
                self._ops = raw[-500:] if isinstance(raw, list) else []
            except (json.JSONDecodeError, OSError):
                self._ops = []
    
    def _save(self):
        """线程安全写入，使用写锁防止竞争"""
        with self._write_lock:
            tmp = self._path().with_suffix('.tmp')
            with open(tmp, 'w') as f:
                json.dump(self._ops, f, ensure_ascii=False, indent=2)
            tmp.replace(self._path())  # 原子替换

    def _schedule_save(self):
        """延迟保存，合并短时间内的多次写入"""
        if self._save_timer:
            self._save_timer.cancel()
        self._save_timer = threading.Timer(1.0, self._save)
        self._save_timer.daemon = True
        self._save_timer.start()
    
    def record(self, tool="chat", params=None, success=True, summary="", latency_ms=0):
        with self._lock:
            record = {
                "tool": tool,
                "params": params or {},
                "success": success,
                "summary": summary[:200],
                "latency_ms": latency_ms,
                "timestamp": time.time(),
            }
            self._ops.append(record)
            if len(self._ops) > 500:
                self._ops = self._ops[-500:]
            self._schedule_save()  # 延迟批量写入
            return record
    
    def get_stats(self):
        with self._lock:
            total = len(self._ops)
            if total == 0:
                return {"total": 0, "success_rate": 0, "avg_latency_ms": 0}
            success = sum(1 for r in self._ops if r.get("success"))
            avg_latency = sum(r.get("latency_ms", 0) for r in self._ops) / total
            return {
                "total": total,
                "success": success,
                "failed": total - success,
                "success_rate": round(success / total * 100, 1),
                "avg_latency_ms": round(avg_latency, 0),
            }

op_logger = OperationLogger(DATA_DIR)

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

        if path == "/api/status":
            stats = op_logger.get_stats()
            self._send_json({
                "name": "PSPAI",
                "version": "v1.3.0",
                "engine": "Hermes",
                "tools": 31,
                "status": "running",
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "operations": stats,
            })
            return

        if path == "/api/names":
            names = load_json("names", {})
            self._send_json(names)
            return

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

        if path == "/api/chat":
            data = self._read_body()
            msg = data.get("message", "")
            char_index = data.get("charIndex", 0)
            char_name = data.get("charName", "PSPAI")
            lang = data.get("lang", "zh")

            if not msg:
                self._send_json({"reply": t_msg(lang, 'empty')})
                return

            names = load_json("names", {})
            current_name = names.get(str(char_index), char_name)
            system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)
            context_msg = f"[当前角色名: {current_name}] {msg}"

            # === chat handler with retry + memory (v3.0) ===
            t_start = time.time()
            try:
                agent = get_agent(char_index, current_name)
                history = get_history(char_index)

                # 改名意图检测
                rename_match = re.search(r"(?:叫你|叫你叫|把你叫|改名为|改名[为]?|叫)(.+)", msg)
                if rename_match:
                    new_name = rename_match.group(1).strip()[:10]
                    names[str(char_index)] = new_name
                    save_json("names", names)
                    context_msg = f"[当前角色名: {current_name}] 用户给你改名为「{new_name}」。请用新名字回应。用户说: {msg}"

                # L1+L2 retry
                result = None
                retries = 0
                prompt = system_prompt
                for attempt in range(2):
                    try:
                        result = agent.run_conversation(
                            user_message=context_msg,
                            system_message=prompt,
                        )
                        if result and result.get('final_response'):
                            break
                    except Exception as inner_e:
                        retries += 1
                        if attempt == 0:
                            print(f"[PSPAI] L1 retry: {inner_e}")
                            prompt = system_prompt + "\n(请简短回复)"
                            time.sleep(1)
                        else:
                            raise inner_e

                reply = result.get('final_response', '') if result else ''
                if not reply:
                    reply = t_msg(lang, 'thinking')

                latency_ms = int((time.time() - t_start) * 1000)

                # 记忆回路: record successful operation
                op_logger.record(
                    tool="chat",
                    params={
                        "char_index": char_index,
                        "char_name": current_name,
                        "lang": lang,
                        "msg_len": len(msg),
                        "reply_len": len(reply),
                        "retries": retries,
                    },
                    success=True,
                    summary=reply[:100],
                    latency_ms=latency_ms,
                )

                # NAME marker detection
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
                latency_ms = int((time.time() - t_start) * 1000)
                try:
                    op_logger.record(
                        tool="chat",
                        params={"char_index": char_index, "msg_len": len(msg)},
                        success=False,
                        summary=str(e)[:100],
                        latency_ms=latency_ms,
                    )
                except Exception:
                    pass
                self._send_json({"reply": f"{t_msg(lang, 'error')}: {str(e)[:50]}"})
            return

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
        print("ERROR: DEEPSEEK_API_KEY not set in .env")
        sys.exit(1)

    print("PSPAI v3.0 backend starting - Hermes engine + memory loop + error recovery")
    print(f"   Port: {port}")
    print(f"   Engine: Hermes AIAgent")
    print(f"   Tools: 31 (terminal/file/search/memory/git/ssh...)")
    print(f"   Model: DeepSeek Chat")
    print(f"   Memory: OperationLogger (500 records max)")
    print(f"   Recovery: L1 retry + L2 fallback + L3 graceful")
    print(f"   Data: {DATA_DIR}")

    server = http.server.HTTPServer(("0.0.0.0", port), PSPAIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPSPAI stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
