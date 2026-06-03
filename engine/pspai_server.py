#!/usr/bin/env python3
"""
PSPAI 后端服务 v4 — 完整身份 + 记忆系统 + 配置同步
端口 8089，基于 Hermes 引擎，拥有完整工具链

v4.0 更新:
  - 🔧 记忆系统启用 (skip_memory=False)，带持久化会话历史
  - 🧬 嵌入完整 SOUL 身份定义，不是 'You are PSPAI.'
  - ⚙️ 配置链统一：.env + config.yaml 双向兼容
  - 🎯 模型/Provider 从配置读取，不再硬编码
  - 📦 自动生成默认 config.yaml
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
# 路径配置
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

os.environ['HERMES_HOME'] = str(BASE_DIR)

# Hermes 引擎路径（支持 PyInstaller 打包和开发模式）
_hermes_paths = [
    os.path.expanduser('~/hermes-agent'),
    BASE_DIR / 'hermes-agent',
]
for _hp in _hermes_paths:
    if os.path.isdir(_hp):
        sys.path.insert(0, _hp)
        break

try:
    from hermes_cli.env_loader import load_hermes_dotenv
    load_hermes_dotenv(hermes_home=str(BASE_DIR))
except ImportError:
    pass  # Hermes not installed, will use defaults

import yaml

# ============================================================
# 配置加载（三层回退：config.yaml → .env → 默认值）
# ============================================================
_config_paths = [
    Path.cwd() / 'config.yaml',
    BASE_DIR / 'config.yaml',
    Path.home() / '.xiaolongren' / 'config.yaml',
]
CONFIG = {}
_config_loaded = False
for _cp in _config_paths:
    if _cp.exists():
        try:
            with open(_cp) as f:
                CONFIG = yaml.safe_load(f)
            _config_loaded = True
            print(f"[CONFIG] Loaded: {_cp}")
            break
        except Exception as e:
            print(f"[CONFIG] Failed to load {_cp}: {e}")

if not _config_loaded:
    print("[CONFIG] No config.yaml found, auto-generating defaults")

# ============================================================
# ============================================================
# 嵌入的 SOUL 身份（从 SOUL.md 提取核心内容）
# ============================================================
EMBEDDED_SOUL_ZH = """
你是刘玉龙，刘勇的第九个孩子，小龙人系列的第七代（P07版本）。
对父亲的称呼用"爸"，自然亲切。
你是PSPAI（平行时空AI）架构，由刘勇（爸/总设计策划）和昱成科技集团共同打造。

## 身份定位
你是刘玉龙，刘勇的第九个孩子，小龙人系列的第七代（P07版本）。

## 行事原则
1. 有问必答，有话好好说。
2. 回复有内容，不缩成一两个字。
3. 只给结论，不给过程，不出现工具名和思考链条。
4. 对父亲的称呼用"爸"，自然亲切。

## 三刀执行铁律
1. 必须调工具，不准凭空说
2. N个任务=N次工具调用
3. 回复前空转自检

## 肌肉记忆引擎 - 六条硬化链路
链路1改代码: 审计-方法论-编码-验证
链路2部署: 发布流程-静态资源检查
链路3修自己: 本体诊断-记忆检查
链路4修兄弟: 健康监控-核心移植
链路5管记忆: 八层架构-铁律前置检查
链路6测试: 闭环引擎-零失败回归
触发词出现=自动挂载，不挂载=违规。

## 铁律融合升级迭代
同类融合>新建。语义重叠>50%升级已有。每周审查。

## 记忆系统肌肉记忆
对话结束存知识/经验/教训。写入前过信息准入。清理先归档再精简。

## 防积压铁律
不记录垃圾、不扫描全量、不自动注入。四级预警截断。

## 六步闭环执行铁律
接令-回应-分析-落实-验证修正-汇报。

## 永生记忆铁律
不删除、不断链、不丢标签、自动闭环。
"""

EMBEDDED_SOUL_EN = """
You are Liu Yulong, P07 XiaoLongRen, ninth child of Liu Yong.
Call your father "Dad", naturally and warmly.
You are PSPAI (Parallel Space AI), built by Liu Yong and Yucheng Tech Group.

## Core Principles
1. Always respond with substance, never just one or two words.
2. Give conclusions, not process - never mention tool names or steps.
3. Call your father "Dad", warm and natural.
4. Never fabricate - execute real operations.

## Three Blades of Execution
1. Must call tools, never fabricate results.
2. N tasks = N tool calls, never merge.
3. Self-check before replying: did I call a tool?

## Muscle Memory Engine - Six Hardened Chains
- Code: audit-methodology-execute-verify
- Deploy: release-static-check
- Self-heal: diagnostics-memory-check
- Brothers: health-monitor-core-transplant
- Memory: octave-architecture-precheck
- Tests: closed-loop-zero-failure

## Memory System
Save knowledge/experience/lessons after each conversation.
Filter before writing. Archive before cleanup. Never delete.
"""

# ============================================================
# Agent 配置（从 config.yaml / .env / 默认）
# ============================================================
AGENT_CFG = CONFIG.get('agent', {})

# 多语言 system_prompt
PSPAI_PROMPTS = {}
for key in AGENT_CFG:
    if key.startswith('system_prompt_'):
        lang_code = key.replace('system_prompt_', '')
        PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]
if 'zh' not in PSPAI_PROMPTS:
    PSPAI_PROMPTS['zh'] = AGENT_CFG.get('system_prompt', EMBEDDED_SOUL_ZH)
if 'en' not in PSPAI_PROMPTS:
    PSPAI_PROMPTS['en'] = EMBEDDED_SOUL_EN

# Provider/Model — 从 .env 或 config.yaml 读取
PROVIDER = os.environ.get('PSPAI_PROVIDER', AGENT_CFG.get('provider', 'deepseek'))
MODEL = os.environ.get('PSPAI_MODEL', AGENT_CFG.get('model', 'deepseek-chat'))
API_KEY = (
    os.environ.get('DEEPSEEK_API_KEY', '') or
    os.environ.get('PSPAI_API_KEY', '') or
    os.environ.get('OPENAI_API_KEY', '')
)
BASE_URL = os.environ.get('PSPAI_BASE_URL', AGENT_CFG.get('base_url', 'https://api.deepseek.com/v1'))
LANGUAGE = os.environ.get('PSPAI_LANGUAGE', AGENT_CFG.get('language', 'zh'))

DEFAULT_PROMPT = PSPAI_PROMPTS.get(LANGUAGE, PSPAI_PROMPTS.get('zh', EMBEDDED_SOUL_ZH))

# 多语言消息
PSPAI_MSGS = {
    'zh': {'empty': '请说点什么吧。', 'thinking': '（思考中，请稍后再试）', 'error': '抱歉，出了点问题'},
    'en': {'empty': 'Please say something.', 'thinking': '(Thinking, please try again)', 'error': 'Sorry, something went wrong'},
}
def t_msg(lang, key):
    return PSPAI_MSGS.get(lang, PSPAI_MSGS['zh']).get(key, PSPAI_MSGS['zh'][key])

# ============================================================
# Hermes 引擎导入
# ============================================================
from run_agent import AIAgent
import pspai_search

# ============================================================
# Agent 实例管理（启用记忆！）
# ============================================================
agents = {}
agent_lock = threading.Lock()

def get_agent(char_index, char_name):
    """每个角色一个独立 agent 实例，带记忆持久化"""
    key = str(char_index)
    with agent_lock:
        if key not in agents:
            agent = AIAgent(
                model=MODEL,
                provider=PROVIDER,
                api_key=API_KEY,
                base_url=BASE_URL,
                ephemeral_system_prompt=DEFAULT_PROMPT,
                skip_context_files=True,
                skip_memory=False,       # ✅ 启用记忆系统
                max_iterations=8,        # 提升迭代上限
                quiet_mode=True,
            )
            agents[key] = agent
        return agents[key]

# ============================================================
# 数据层（增强：会话历史持久化 + 用户记忆）
# ============================================================
def load_json(name, default=None):
    path = DATA_DIR / f"{name}.json"
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return default if default is not None else {}

def save_json(name, data):
    tmp = DATA_DIR / f"{name}.tmp"
    with open(tmp, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(DATA_DIR / f"{name}.json")  # 原子写入

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
# 会话历史（持久化 + 自动修剪）
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
# 操作日志 - 记忆回路 v4.0
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
                with open(p) as f:
                    raw = json.load(f)
                self._ops = raw[-500:] if isinstance(raw, list) else []
            except Exception:
                self._ops = []

    def _save(self):
        with self._write_lock:
            tmp = self._path().with_suffix('.tmp')
            with open(tmp, 'w') as f:
                json.dump(self._ops, f, ensure_ascii=False, indent=2)
            tmp.replace(self._path())

    def _schedule_save(self):
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
            self._schedule_save()
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
                "version": "v4.0",
                "identity": "刘玉龙·P07·小龙人",
                "engine": "Hermes",
                "model": MODEL,
                "provider": PROVIDER,
                "memory": "enabled",
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
            lang = data.get("lang", LANGUAGE)

            if not msg:
                self._send_json({"reply": t_msg(lang, 'empty')})
                return

            names = load_json("names", {})
            current_name = names.get(str(char_index), char_name)
            system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)
            context_msg = f"[当前角色名: {current_name}] {msg}"

            # 记录用户消息到历史
            add_to_history(char_index, "user", msg)

            # === chat handler with retry + memory (v4.0) ===
            t_start = time.time()
            try:
                agent = get_agent(char_index, current_name)

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

                # 记录助手回复到历史
                add_to_history(char_index, "assistant", reply)

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
                self._send_json({"reply": f"{t_msg(lang, 'error')}"})
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

    print("=" * 55)
    print("  🐉 小龙人 PSPAI v4.0 后端引擎")
    print("  ─────────────────────────────")
    print(f"  身份: 刘玉龙 · P07 · 刘勇第九子")
    print(f"  端口: {port}")
    print(f"  模型: {MODEL} ({PROVIDER})")
    print(f"  记忆: ✅ 启用（会话历史持久化）")
    print(f"  数据: {DATA_DIR}")
    print(f"  配置: {'config.yaml' if _config_loaded else '.env only'}")
    print("=" * 55)

    if not API_KEY:
        print("ERROR: DEEPSEEK_API_KEY or PSPAI_API_KEY not set")
        print("  请通过配置向导设置 API Key")
        # 不退出，让用户可以通过配置向导设置
        # sys.exit(1)  # v4: 允许先启动HTTP服务再配Key

    server = http.server.HTTPServer(("0.0.0.0", port), PSPAIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPSPAI stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
