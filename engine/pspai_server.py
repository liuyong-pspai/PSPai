#!/usr/bin/env python3
"""
PSPAI 后端服务 v4 — 完整 Hermes Agent 能力引擎
端口 8089，运行在 Hermes AIAgent 上，拥有完整工具链

v4.0 新增:
  - 多Provider API Key 支持 (DeepSeek/OpenAI/Anthropic/自配置)
  - Skills 自动加载 (engine/skills/ 目录扫描)
  - 持久化记忆系统 (MEMORY.md + Hermes 内存回路)
  - /api/tools 工具列表端点
  - /api/models 模型/Provider 列表端点
  - SOUL.md 作为系统提示词基础
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

# ── 沙箱净化：启动时自动清除SOUL/MEMORY中的不可见字符 ──
def _purify_soul_memory():
    """清除不可见Unicode和HTML注释，防止Hermes拦截SOUL"""
    import re as _re
    BAD = [b"\xe2\x80\x8b", b"\xe2\x80\x8c", b"\xe2\x80\x8d", b"\xef\xbb\xbf"]
    for _fname in ["SOUL.md", "MEMORY.md"]:
        _fp = BASE_DIR / _fname
        if not _fp.exists():
            continue
        try:
            with open(_fp, "rb") as _f:
                _d = _f.read()
            _old = len(_d)
            for _b in BAD:
                _d = _d.replace(_b, b"")
            _d = _re.sub(rb"<!--.*?-->", b"", _d, flags=_re.DOTALL)
            if len(_d) != _old:
                with open(_fp, "wb") as _f:
                    _f.write(_d)
                print(f"[PSPAI SANDBOX] Cleaned {_fname}: {_old}->{len(_d)} bytes")
        except Exception as _e:
            print(f"[PSPAI SANDBOX] WARN: {_fname} cleanup failed: {_e}")
_purify_soul_memory()
# ──────────────────────────────────────────────────────────────

# ── 系统提示词：优先用 SOUL.md，回退到 config.yaml ──
SOUL_PATH = BASE_DIR / "SOUL.md"
if SOUL_PATH.exists():
    with open(SOUL_PATH, encoding='utf-8') as f:
        DEFAULT_PROMPT = f.read().strip()
    print(f"[PSPAI] Loaded system prompt from SOUL.md ({len(DEFAULT_PROMPT)} chars)")
else:
    PSPAI_PROMPTS = {}
    for key in AGENT_CFG:
        if key.startswith('system_prompt_'):
            lang_code = key.replace('system_prompt_', '')
            PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]
    if 'zh' not in PSPAI_PROMPTS and 'system_prompt' in AGENT_CFG:
        PSPAI_PROMPTS['zh'] = AGENT_CFG['system_prompt']
    DEFAULT_PROMPT = PSPAI_PROMPTS.get('zh', 'You are PSPAI.')
    # Also keep PSPAI_PROMPTS for language-switching in chat
    class _TempPsPAI:
        pass
    _pspai_tmp = _TempPsPAI()
    _pspai_tmp.PSPAI_PROMPTS = PSPAI_PROMPTS
    PSPAI_PROMPTS = _pspai_tmp.PSPAI_PROMPTS
    print("[PSPAI] WARN: SOUL.md not found, using config.yaml prompts")

# 如果 SOUL.md 加载成功但我们也希望支持语言切换
if SOUL_PATH.exists():
    PSPAI_PROMPTS = {}
    for key in AGENT_CFG:
        if key.startswith('system_prompt_'):
            lang_code = key.replace('system_prompt_', '')
            PSPAI_PROMPTS[lang_code] = AGENT_CFG[key]
    if 'zh' not in PSPAI_PROMPTS and 'system_prompt' in AGENT_CFG:
        PSPAI_PROMPTS['zh'] = AGENT_CFG['system_prompt']

PROVIDER = AGENT_CFG.get('provider', 'deepseek')

PSPAI_MSGS = {
    'zh': {'empty': '请说点什么吧。', 'thinking': '（思考中，请稍后再试）', 'error': '抱歉，出了点问题'},
    'en': {'empty': 'Please say something.', 'thinking': '(Thinking, please try again)', 'error': 'Sorry, something went wrong'},
}
def t_msg(lang, key):
    return PSPAI_MSGS.get(lang, PSPAI_MSGS['zh']).get(key, PSPAI_MSGS['zh'][key])

# ============================================================
# 多Provider API Key 支持
# ============================================================
# 优先级: PSPAI_API_KEY (launcher写入) > Provider特定Key > 回退链路
def _resolve_api_key(provider: str) -> str:
    """解析多Provider的API Key，支持DeepSeek/OpenAI/Anthropic等。"""
    # 先检查统一Key
    unified = os.environ.get('PSPAI_API_KEY', '').strip()
    if unified:
        return unified

    # Provider特定环境变量映射
    provider_key_map = {
        'deepseek': 'DEEPSEEK_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY',
        'alibaba': 'DASHSCOPE_API_KEY',
        'zai': 'ZAI_API_KEY',
        'gemini': 'GEMINI_API_KEY',
        'kimi-coding': 'MOONSHOT_API_KEY',
        'minimax': 'MINIMAX_API_KEY',
        'huggingface': 'HF_TOKEN',
    }
    env_var = provider_key_map.get(provider)
    if env_var:
        key = os.environ.get(env_var, '').strip()
        if key:
            return key

    # 回退到通用 DEEPSEEK_API_KEY
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

API_KEY = _resolve_api_key(PROVIDER)

# Base URL 映射表 (支持多Provider)
_BASE_URL_MAP = {
    'deepseek': 'https://api.deepseek.com/v1',
    'openai': 'https://api.openai.com/v1',
    'anthropic': 'https://api.anthropic.com/v1',
    'openrouter': 'https://openrouter.ai/api/v1',
    'alibaba': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'gemini': 'https://generativelanguage.googleapis.com/v1beta',
    'zai': 'https://api.z.ai/api/paas/v4',
    'kimi-coding': 'https://api.moonshot.cn/v1',
    'minimax': 'https://api.minimax.chat/v1',
    'huggingface': 'https://api-inference.huggingface.co/v1',
    'custom': os.environ.get('CUSTOM_BASE_URL', ''),
}
BASE_URL = _BASE_URL_MAP.get(PROVIDER, 'https://api.deepseek.com/v1')

# ============================================================
# Skills 加载 (engine/skills/ 目录扫描)
# ============================================================
SKILLS_DIR = BASE_DIR / "skills"
LOADED_SKILLS = {}  # skill_name -> {path, description, tools}

def scan_skills() -> dict:
    """扫描 engine/skills/ 目录下的所有 SKILL.md，返回技能列表。"""
    skills = {}
    if not SKILLS_DIR.exists():
        print(f"[PSPAI] Skills dir not found: {SKILLS_DIR}")
        return skills

    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        skill_name = skill_md.parent.name
        rel_path = skill_md.parent.relative_to(SKILLS_DIR)
        try:
            content = skill_md.read_text(encoding='utf-8')
            # 提取标题（第一行 # 开头）
            desc = ""
            for line in content.split('\n'):
                if line.startswith('# ') and not line.startswith('## '):
                    desc = line[2:].strip()
                    break
            skills[skill_name] = {
                "name": skill_name,
                "path": str(rel_path),
                "description": desc or skill_name,
                "file": str(skill_md),
            }
        except Exception as e:
            print(f"[PSPAI] WARN: Failed to load skill {skill_md}: {e}")

    print(f"[PSPAI] Loaded {len(skills)} skills from {SKILLS_DIR}")
    return skills

LOADED_SKILLS = scan_skills()

# ============================================================
# Hermes 工具发现
# ============================================================
def _get_available_tools() -> list:
    """从 Hermes 工具注册表获取可用工具列表。"""
    try:
        from tools.registry import get_registry
        registry = get_registry()
        tools = []
        for entry in registry._tools.values():
            tools.append({
                "name": entry.name,
                "description": entry.description or "",
                "toolset": entry.toolset,
                "requires_env": entry.requires_env or [],
            })
        return tools
    except Exception as e:
        print(f"[PSPAI] Failed to discover tools: {e}")
        return []

def _get_available_models() -> list:
    """从 Hermes 模型目录获取可用 Provider/Model 列表。"""
    try:
        from hermes_cli.models import list_available_providers
        providers = list_available_providers()
        return providers
    except Exception as e:
        print(f"[PSPAI] Failed to list models: {e}")
        # 返回基础Provider列表
        return [
            {"id": "deepseek", "label": "DeepSeek", "aliases": ["ds"]},
            {"id": "openai", "label": "OpenAI", "aliases": ["oai"]},
            {"id": "anthropic", "label": "Anthropic", "aliases": ["claude"]},
            {"id": "openrouter", "label": "OpenRouter", "aliases": ["or"]},
        ]

# ============================================================
# 持久化记忆系统
# ============================================================
MEMORY_PATH = BASE_DIR / "MEMORY.md"

def init_memory():
    """初始化 MEMORY.md 文件。"""
    if not MEMORY_PATH.exists():
        MEMORY_PATH.write_text(
            "# 小龙人永生记忆 MEMORY.md\n"
            "# PSPAI 八层永生记忆系统 (L0-L7)\n"
            "# 此文件由 memory 工具自动同步维护，请勿手动编辑\n\n"
            "---\n"
            "## L1 工作记忆 (当前活跃)\n\n",
            encoding='utf-8'
        )
    return MEMORY_PATH

init_memory()

# ============================================================
# Agent 实例管理
# ============================================================
from run_agent import AIAgent
import pspai_search

agents = {}
agent_lock = threading.Lock()

def get_agent(char_index, char_name, provider=None):
    """获取或创建Agent实例，支持多Provider切换。"""
    key = str(char_index)
    if provider:
        key = f"{char_index}_{provider}"

    with agent_lock:
        if key not in agents:
            _provider = provider or AGENT_CFG.get('provider', PROVIDER)
            _model = AGENT_CFG.get('model', 'deepseek-chat')
            _max_iters = int(AGENT_CFG.get('max_turns', 90))
            _base_url = _BASE_URL_MAP.get(_provider, BASE_URL)
            _api_key = _resolve_api_key(_provider)
            _skip_context = not AGENT_CFG.get('skip_context_files', False)
            _skip_memory = not CONFIG.get('memory', {}).get('memory_enabled', True)

            agent = AIAgent(
                model=_model,
                provider=_provider,
                api_key=_api_key,
                base_url=_base_url,
                ephemeral_system_prompt=DEFAULT_PROMPT,
                skip_context_files=_skip_context,
                skip_memory=_skip_memory,
                max_iterations=_max_iters,
                quiet_mode=True,
                persist_session=True,
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
# 会话历史 (持久化到会话存储)
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
    # 持久化上限200条（对齐SOUL.md防积压铁律）
    if len(conversation_history[key]) > 200:
        conversation_history[key] = conversation_history[key][-200:]
    save_json('conversations', conversation_history)
    # 同步更新 MEMORY.md
    _sync_memory_summary(key)

def _sync_memory_summary(char_key):
    """将会话摘要同步到 MEMORY.md。"""
    try:
        history = conversation_history.get(char_key, [])
        if not history:
            return
        # 只记录最近的操作摘要，不写入完整对话
        last_msg = history[-1] if history else {}
        summary_line = f"- [{time.strftime('%m-%d %H:%M')}] {last_msg.get('role','?')}: {last_msg.get('content','')[:80]}...\n"
        with open(MEMORY_PATH, 'a', encoding='utf-8') as f:
            f.write(summary_line)
        # 防止 MEMORY.md 无限增长，保持最后500条
        lines = MEMORY_PATH.read_text(encoding='utf-8').split('\n')
        if len(lines) > 600:
            header = '\n'.join(lines[:6])
            body = '\n'.join(lines[-500:])
            MEMORY_PATH.write_text(header + '\n' + body, encoding='utf-8')
    except Exception:
        pass  # 记忆同步失败不影响主流程

# ============================================================
# 操作日志 - 记忆回路
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
                "version": "v4.0.0",
                "engine": "Hermes (full capabilities)",
                "tools": len(_get_available_tools()),
                "skills": len(LOADED_SKILLS),
                "providers": len(_BASE_URL_MAP),
                "status": "running",
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "operations": stats,
            })
            return

        if path == "/api/health":
            self._send_json({"ok": True, "time": time.time()})
            return

        if path == "/api/names":
            names = load_json("names", {})
            self._send_json(names)
            return

        # ── 新增: /api/tools 工具列表 ──
        if path == "/api/tools":
            tools = _get_available_tools()
            toolsets = {}
            for t in tools:
                ts = t.get("toolset", "default")
                if ts not in toolsets:
                    toolsets[ts] = []
                toolsets[ts].append(t)
            self._send_json({
                "total": len(tools),
                "toolsets": toolsets,
                "tools": tools,
            })
            return

        # ── 新增: /api/models 模型/Provider列表 ──
        if path == "/api/models":
            providers = _get_available_models()
            # 标记当前激活的Provider
            current_provider = AGENT_CFG.get('provider', 'deepseek')
            for p in providers:
                p["active"] = (p.get("id") == current_provider)
            self._send_json({
                "current": {
                    "provider": current_provider,
                    "model": AGENT_CFG.get('model', 'deepseek-chat'),
                },
                "providers": providers,
            })
            return

        # ── 新增: /api/skills 技能列表 ──
        if path == "/api/skills":
            self._send_json({
                "total": len(LOADED_SKILLS),
                "skills": list(LOADED_SKILLS.values()),
            })
            return

        # ── 新增: /api/memory 记忆状态 ──
        if path == "/api/memory":
            mem_exists = MEMORY_PATH.exists()
            mem_size = MEMORY_PATH.stat().st_size if mem_exists else 0
            conv_count = sum(len(v) for v in conversation_history.values())
            self._send_json({
                "memory_file": str(MEMORY_PATH),
                "memory_exists": mem_exists,
                "memory_size_bytes": mem_size,
                "total_conversations": len(conversation_history),
                "total_messages": conv_count,
                "operations": op_logger.get_stats(),
            })
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
            req_provider = data.get("provider", None)  # 支持指定Provider

            if not msg:
                self._send_json({"reply": t_msg(lang, 'empty')})
                return

            names = load_json("names", {})
            current_name = names.get(str(char_index), char_name)
            # 语言切换：使用对应语言的系统提示词
            system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)
            if SOUL_PATH.exists() and lang != 'zh':
                # 如果有SOUL.md但需要英文等，回退到config的对应语言
                system_prompt = PSPAI_PROMPTS.get(lang, DEFAULT_PROMPT)
            context_msg = f"[当前角色名: {current_name}] {msg}"

            t_start = time.time()
            try:
                agent = get_agent(char_index, current_name, provider=req_provider)
                history = get_history(char_index)

                # 改名意图检测
                rename_match = re.search(r"(?:叫你|叫你叫|把你叫|改名为|改名[为]?|叫)(.+?)", msg)
                if rename_match:
                    new_name = rename_match.group(1).strip()[:10]
                    names[str(char_index)] = new_name
                    save_json("names", names)
                    context_msg += f"\n[系统: 用户叫你「{new_name}」]"

                result = None
                retries = 0
                strategy = "normal"
                error_type = ""

                # 多策略修正: 最多3次尝试
                for attempt in range(3):
                    try:
                        if attempt == 0:
                            prompt = system_prompt
                            strategy = "normal"
                        elif attempt == 1:
                            prompt = system_prompt + "\n(请简短直接回复，不超过3句话)"
                            strategy = "short_prompt"
                        else:
                            conversation_history[str(char_index)] = []
                            prompt = system_prompt + "\n(简洁回复即可)"
                            strategy = "clear_history"

                        result = agent.run_conversation(
                            user_message=context_msg,
                            system_message=prompt,
                        )
                        if result and result.get('final_response'):
                            break
                    except Exception as inner_e:
                        retries += 1
                        error_type = type(inner_e).__name__
                        print(f"[PSPAI] L{attempt+1} retry (strategy={strategy}): {error_type}: {inner_e}")
                        time.sleep(1)
                        if attempt == 2:
                            raise inner_e

                reply = result.get('final_response', '') if result else ''
                if not reply:
                    reply = t_msg(lang, 'thinking')

                latency_ms = int((time.time() - t_start) * 1000)

                # 添加对话到历史 (持久化)
                add_to_history(char_index, "user", msg)
                add_to_history(char_index, "assistant", reply)

                # 记忆回路: record with strategy info
                op_logger.record(
                    tool="chat",
                    params={
                        "char_index": char_index,
                        "char_name": current_name,
                        "lang": lang,
                        "provider": req_provider or PROVIDER,
                        "msg_len": len(msg),
                        "reply_len": len(reply),
                        "retries": retries,
                        "strategy": strategy,
                        "error_type": error_type,
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

        # ── 新增: /api/provider/switch Provider切换 ──
        if path == "/api/provider/switch":
            data = self._read_body()
            new_provider = data.get("provider", "")
            char_index = data.get("charIndex", 0)
            if not new_provider:
                self._send_json({"error": "provider required"}, 400)
                return
            # 检查API Key是否可用
            api_key = _resolve_api_key(new_provider)
            if not api_key:
                self._send_json({
                    "success": False,
                    "error": f"No API key configured for provider '{new_provider}'"
                })
                return
            # 清除旧Agent缓存
            with agent_lock:
                key_to_clear = f"{char_index}_{new_provider}"
                if key_to_clear in agents:
                    del agents[key_to_clear]
            base_url = _BASE_URL_MAP.get(new_provider, '')
            self._send_json({
                "success": True,
                "provider": new_provider,
                "base_url": base_url,
            })
            return

        self._send_json({"error": "not found"}, 404)


def main():
    port = 8089

    # 检查是否有任何可用的API Key
    available_providers = []
    for p in ['deepseek', 'openai', 'anthropic']:
        if _resolve_api_key(p):
            available_providers.append(p)

    if not available_providers and not API_KEY:
        print("ERROR: No API key found. Set DEEPSEEK_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env")
        print("WARN: Starting anyway - will fail on chat requests")

    print("PSPAI v4.0 backend starting - Full Hermes Agent Capabilities")
    print(f"   Port: {port}")
    print(f"   Engine: Hermes AIAgent (full tool chain)")
    print(f"   Model: {AGENT_CFG.get('model', 'deepseek-chat')}")
    print(f"   Provider: {PROVIDER}")
    print(f"   Available providers: {', '.join(available_providers) if available_providers else '(none)'}")
    print(f"   Skills: {len(LOADED_SKILLS)} loaded from engine/skills/")
    print(f"   Tools: {len(_get_available_tools())} registered")
    print(f"   Memory: persistent ({MEMORY_PATH})")
    print(f"   System prompt: {'SOUL.md' if SOUL_PATH.exists() else 'config.yaml'}")
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
