# 工具注册诊断：为什么新工具不显示

## 问题
在 `tools/` 目录下新增工具 Python 文件后，工具在对话中不可用——框架似乎没有发现新工具。

## 根因：Hermes 框架使用硬编码白名单

Hermes 工具发现机制在 `model_tools.py` 第 138-161 行，使用**硬编码白名单**而非自动目录扫描：

```python
def _discover_tools():
    _modules = [
        "tools.web_tools",
        "tools.terminal_tool",
        "tools.file_tools",
        # ... 20+ 个明确列出的模块
    ]
    for mod_name in _modules:
        importlib.import_module(mod_name)
```

**任何不在白名单中的 `tools/*.py` 文件永远不会被加载。**

## 修复方法

### 步骤 1：在白名单中添加模块
```bash
# 编辑 model_tools.py 的 _modules 列表，添加一行：
"tools.yulong_tools",     # PSPAI P07: 玉龙14个专属工具
```

### 步骤 2：确保 import 不会超时
工具文件在导入时会被立即执行（包括 `registry.register()` 调用）。
如果导入阶段有耗时操作（如网络请求、SSH 连接），会导致框架启动超时。

**解决方案：延迟导入**
```python
# ❌ 错误：启动时就导入重的模块
from yu_long_tools import git_operations, ssh_exec, brother_watch

# ✅ 正确：handler 调用时才导入
_yulong_imports = None

def _get_yulong_fn(name):
    global _yulong_imports
    if _yulong_imports is None:
        from yu_long_tools import (...)
        _yulong_imports = {...}
    return _yulong_imports[name]

handler=lambda args, **kw: _get_yulong_fn("ssh_exec")(**args)
```

### 步骤 3：路径解析用绝对路径
`__file__` 在包导入场景下不可靠。使用 `os.path.expanduser()`：

```python
# ❌ 错误：__file__.parent.parent 在包内导入时可能指向错误位置
_skills_dir = Path(__file__).resolve().parent.parent / ".hermes-yulong" / "skills"

# ✅ 正确：显式使用绝对路径
_skills_dir = os.path.expanduser("~/.hermes-yulong/skills")
```

### 步骤 4：重启网关
工具注册发生在网关启动时。添加新工具后**必须重启**才生效。
由于网关内无法自重启，使用 cron 延迟重启（见 cross-agent-health-monitoring 技能的 `gateway-self-restart.md`）。

## 诊断流程

```text
新工具不显示？
  ├─ 检查 model_tools.py 白名单 → 包含了？ → 继续
  │                                     └→ 没包含 → 添加
  ├─ 检查 import 是否超时 → 超时了？ → 改为延迟导入
  └─ 重启了吗？ → 没重启 → 用 cron 延迟重启
                        └→ 重启了 → 检查 agent.log 是否有 import 报错
```

## 实战案例
2026-05-28：14 个玉龙工具不显示。根因分析：
1. `model_tools.py` 白名单未包含 `tools.yulong_tools` → 添加
2. `yu_long_tools.py` import 路径错误（`parent.parent` 指向 hermes-agent/ 而非 ~）→ 改为 `os.path.expanduser`
3. import 时 `brother_watch` 执行 ping 导致超时 → 改为 `_get_yulong_fn()` 延迟导入
4. 网关未重启 → 安排 cron 2 分钟后重启
