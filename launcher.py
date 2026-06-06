#!/usr/bin/env python3
"""
🐉 小龙人 一键启动器 — 内置HTTP服务器 + 配置API
   - 首次运行 → 打开配置向导 → 保存config.json → 重启
   - 已配置 → 启动引擎 → 打开聊天界面
   - 不依赖外部Python，自带HTTP服务器
"""
import json
import os
import re
import sys
import time
import socket
import subprocess
import webbrowser
import shutil
import signal
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# ============================================================
# 路径配置
# ============================================================
APP_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = APP_DIR / "config.json"
ENV_FILE = APP_DIR / ".env"
FRONTEND_DIR = APP_DIR / "frontend" / "pwa" / "html"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = APP_DIR / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = APP_DIR / "UI原型"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = APP_DIR / "pwa"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = APP_DIR / "hongmeng"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = APP_DIR

FRONTEND_PORT = 8088
ENGINE_PORT = 8089
VOICE_PORT = 8765
CONFIG_PORT = 8090  # 配置向导专用端口

ENGINE_CANDIDATES = [
    # === 生产模式：PyInstaller 二进制 ===
    # Windows
    "xiaolongren-engine-windows.exe",
    "engine/dist/xiaolongren-engine-windows.exe",
    # macOS
    "xiaolongren-engine-macos",
    "engine/dist/xiaolongren-engine-macos",
    # Linux
    "xiaolongren-engine-linux-x86_64",
    "engine/dist/xiaolongren-engine-linux-x86_64",
    # ARM
    "xiaolongren-engine-linux-arm64",
    "engine/dist/xiaolongren-engine-linux-arm64",
    # === 开发模式：Python 源码 ===
    "engine/pspai_server.py",
]


def find_engine():
    for name in ENGINE_CANDIDATES:
        path = APP_DIR / name
        if path.exists():
            return path
    return None


def find_python():
    """查找可用的Python解释器（三平台）"""
    # 1. Windows: 检查内置Python
    bundled_win = APP_DIR / "python" / "python.exe"
    if bundled_win.exists():
        return str(bundled_win)

    # 2. macOS: 检查常见路径
    for path in [
        "/usr/bin/python3",
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
    ]:
        if os.path.exists(path):
            return path

    # 3. 系统PATH查找
    for cmd in ["python3", "python"]:
        p = shutil.which(cmd)
        if p:
            try:
                r = subprocess.run([p, "--version"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return p
            except Exception:
                continue
    return None


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_port(port, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_in_use(port):
            return True
        time.sleep(0.3)
    return False


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def config_to_env(cfg):
    provider = cfg.get("provider", "deepseek")
    api_key = cfg.get("api_key", "")
    model = cfg.get("model", "")
    base_url = cfg.get("base_url", "")
    language = cfg.get("language", "zh")
    character = cfg.get("character", "longyuan")

    lines = [
        "# 小龙人配置 - 自动生成",
        f"PSPAI_PROVIDER={provider}",
        f"PSPAI_API_KEY={api_key}",
        f"PSPAI_LANGUAGE={language}",
        f"PSPAI_CHARACTER={character}",
    ]
    if model:
        lines.append(f"PSPAI_MODEL={model}")
    if base_url:
        lines.append(f"PSPAI_BASE_URL={base_url}")

    if provider == "deepseek":
        lines.append(f"DEEPSEEK_API_KEY={api_key}")
    elif provider == "openai":
        lines.append(f"OPENAI_API_KEY={api_key}")
    elif provider == "anthropic":
        lines.append(f"ANTHROPIC_API_KEY={api_key}")

    with open(ENV_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    # === 同步写入 config.yaml（双写） ===
    _sync_config_yaml(cfg)


def _sync_config_yaml(cfg):
    """将config.json的模型配置同步到engine/config.yaml"""
    config_yaml_path = APP_DIR / "engine" / "config.yaml"
    if not config_yaml_path.exists():
        return
    try:
        with open(config_yaml_path) as f:
            content = f.read()

        provider = cfg.get("provider", "deepseek")
        model = cfg.get("model", "deepseek-chat")

        # 更新provider
        content = re.sub(
            r'^(\s*provider:\s*).*$',
            f'\\1{provider}',
            content, flags=re.MULTILINE
        )
        # 更新model（如果存在）
        if model:
            if 'model:' not in content:
                content = content.replace(
                    f'provider: {provider}',
                    f'provider: {provider}\n  model: {model}'
                )
            else:
                content = re.sub(
                    r'^(\s*model:\s*).*$',
                    f'\\1{model}',
                    content, flags=re.MULTILINE
                )

        with open(config_yaml_path, 'w') as f:
            f.write(content)
    except Exception as e:
        print(f"⚠️ config.yaml同步失败: {e}")


# ============================================================
# 内置HTTP服务器（静态文件 + 配置API）
# ============================================================
class XiaoLongRenHandler(SimpleHTTPRequestHandler):
    """静态文件 + POST /api/config"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/config-file":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            exists = CONFIG_FILE.exists()
            self.wfile.write(json.dumps({"exists": exists}).encode())
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                cfg = json.loads(body)
                save_config(cfg)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 静默


def start_http_server():
    """启动内置HTTP服务器（前端 + API）"""
    if port_in_use(FRONTEND_PORT):
        print(f"✅ 端口 {FRONTEND_PORT} 已在使用")
        return None

    server = HTTPServer(("127.0.0.1", FRONTEND_PORT), XiaoLongRenHandler)
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"🌐 HTTP服务器已启动 (端口 {FRONTEND_PORT})")
    return server


def start_engine():
    engine_path = find_engine()
    if not engine_path:
        print("❌ 未找到引擎文件")
        return None

    if port_in_use(ENGINE_PORT):
        print(f"✅ 引擎端口 {ENGINE_PORT} 已在使用")
        return None

    if not ENV_FILE.exists():
        print("❌ 未找到配置")
        return None

    ext = engine_path.suffix.lower()
    if ext == ".py":
        python = find_python()
        if not python:
            print("❌ 未找到Python")
            return None
        proc = subprocess.Popen(
            [python, str(engine_path)],
            cwd=str(engine_path.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc = subprocess.Popen(
            [str(engine_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    print(f"🚀 引擎已启动 (PID: {proc.pid})")
    return proc


def start_voice():
    """启动语音引擎（可选——需要websockets库）"""
    voice_path = APP_DIR / "voice_server.py"
    if not voice_path.exists():
        return None
    if port_in_use(VOICE_PORT):
        print(f"🎤 语音端口 {VOICE_PORT} 已在使用")
        return None
    # 检查websockets是否可用
    python = find_python()
    if not python:
        return None
    try:
        r = subprocess.run([python, "-c", "import websockets"], capture_output=True, timeout=5)
        if r.returncode != 0:
            print("🎤 语音引擎未启用 (需 pip install websockets)")
            return None
    except Exception:
        return None
    proc = subprocess.Popen(
        [python, str(voice_path)],
        cwd=str(APP_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"🎤 语音引擎已启动 (PID: {proc.pid}, 端口 {VOICE_PORT})")
    return proc


# ============================================================
# 桌面快捷方式（Windows）
# ============================================================
def create_desktop_shortcut():
    """在桌面创建快捷方式（仅在Windows首次运行时）"""
    if sys.platform != "win32":
        return

    import pythoncom
    from win32com.client import Dispatch

    try:
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        shortcut_path = desktop / "🐉 小龙人.lnk"

        if shortcut_path.exists():
            return shortcut_path

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        # 目标指向 launcher.exe （PyInstaller打包后）
        launcher_exe = APP_DIR / "launcher.exe"
        if launcher_exe.exists():
            shortcut.TargetPath = str(launcher_exe)
        else:
            python = find_python()
            if python:
                shortcut.TargetPath = python
                shortcut.Arguments = f'"{APP_DIR / "launcher.py"}"'
        shortcut.WorkingDirectory = str(APP_DIR)
        shortcut.IconLocation = str(APP_DIR / "frontend" / "icon.ico") if (APP_DIR / "frontend" / "icon.ico").exists() else ""
        shortcut.Description = "🐉 小龙人 XiaoLongRen"
        shortcut.Save()

        print(f"📌 桌面快捷方式已创建: {shortcut_path}")
        return shortcut_path
    except Exception as e:
        print(f"⚠️ 快捷方式创建失败: {e}")
        return None


# ============================================================
# 配置向导模式
# ============================================================
def run_config_wizard(http_server):
    """运行配置向导——等待用户通过浏览器完成配置"""
    config_url = f"http://127.0.0.1:{FRONTEND_PORT}/config.html"
    print(f"\n🔧 配置向导: {config_url}")
    webbrowser.open(config_url)

    print("⏳ 等待配置完成...")
    last_mtime = CONFIG_FILE.stat().st_mtime if CONFIG_FILE.exists() else 0

    # 等待config.json被写入或更新
    while True:
        time.sleep(0.5)
        if CONFIG_FILE.exists():
            mtime = CONFIG_FILE.stat().st_mtime
            if mtime > last_mtime:
                time.sleep(0.5)  # 确保文件写完
                print("✅ 配置已保存")
                break
        # 超时保护：5分钟后退出
        if last_mtime == 0 and time.time() - start_time > 300:
            print("⚠️ 配置超时，请重新启动")
            return None

    return load_config()


# ============================================================
# 主流程
# ============================================================
def main():
    global start_time
    start_time = time.time()

    print("🐉 小龙人 XiaoLongRen 启动器 v3.0")
    print("=" * 50)

    # 检查前端目录
    if not FRONTEND_DIR.exists():
        print(f"❌ 前端目录不存在: {FRONTEND_DIR}")
        input("按回车键退出...")
        return 1

    # 启动HTTP服务器
    httpd = start_http_server()
    if not httpd and not port_in_use(FRONTEND_PORT):
        print("❌ 无法启动HTTP服务器")
        input("按回车键退出...")
        return 1

    if not wait_for_port(FRONTEND_PORT, timeout=10):
        print("❌ HTTP服务器启动超时")
        return 1

    # 检查配置
    config = load_config()

    if not config:
        # 首次运行 → 配置向导
        config = run_config_wizard(httpd)
        if not config:
            return 1

        # 重新加载
        config = load_config()

    # 有配置 → 生成.env → 启动引擎
    if config:
        config_to_env(config)
        print(f"📋 配置: provider={config.get('provider')}, character={config.get('character', 'longyuan')}")

    engine_proc = start_engine()
    if engine_proc:
        if not wait_for_port(ENGINE_PORT, timeout=25):
            print("⚠️ 引擎启动较慢，请稍候...")
            wait_for_port(ENGINE_PORT, timeout=30)

    # 启动语音引擎（可选）
    voice_proc = start_voice()

    # 打开聊天界面
    chat_url = f"http://127.0.0.1:{FRONTEND_PORT}/"
    print(f"\n🌐 聊天界面: {chat_url}")
    webbrowser.open(chat_url)

    # 创建桌面快捷方式
    create_desktop_shortcut()

    print("\n" + "=" * 50)
    print("  🐉  小龙人 运行中！")
    print("  关闭此窗口可停止程序")
    print("=" * 50)
    print()

    restart_count = 0
    MAX_RESTARTS = 3
    last_health_check = time.time()
    try:
        while True:
            time.sleep(1)
            # 定期健康检查 (每15秒ping一次引擎)
            if time.time() - last_health_check > 15 and engine_proc and engine_proc.poll() is None:
                last_health_check = time.time()
                try:
                    import urllib.request
                    urllib.request.urlopen(f"http://127.0.0.1:{ENGINE_PORT}/api/health", timeout=3)
                except Exception:
                    pass  # 仅用于监控，不影响运行
            if engine_proc and engine_proc.poll() is not None:
                exit_code = engine_proc.returncode
                print(f"⚠️ 引擎已退出 (exit={exit_code})")
                if restart_count < MAX_RESTARTS:
                    restart_count += 1
                    print(f"🔄 第{restart_count}次自动重启引擎...")
                    # 等待端口释放
                    time.sleep(1)
                    engine_proc = start_engine()
                    if engine_proc:
                        wait_for_port(ENGINE_PORT, timeout=25)
                    else:
                        print("❌ 引擎重启失败")
                        break
                else:
                    print(f"❌ 引擎已崩溃{MAX_RESTARTS}次，停止重试")
                    break
    except KeyboardInterrupt:
        print("\n🛑 正在停止...")

    # 清理
    if httpd:
        httpd.shutdown()
    if engine_proc and engine_proc.poll() is None:
        engine_proc.terminate()
        try:
            engine_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            engine_proc.kill()
    if voice_proc and voice_proc.poll() is None:
        voice_proc.terminate()
        try:
            voice_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            voice_proc.kill()

    print("👋 再见！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
