# 架构迁移桥接模式

> 来源：2026-05-30 P07 认知引擎重构——`engine.py` 拆分为 `engine_core.py` + `engine_tools.py`

## 问题

架构重构后旧 API（`CognitiveEngine._tool_XXX` 方法 → `ToolRegistry.register()` 动态注册）导致 32 个测试失败（ImportError + AssertionError）。测试期望的方法/路径已不存在。

## 三层桥接策略

### 层1: 模块导入别名

当 `cognition/engine.py` 拆分为 `engine_core.py` + `engine_tools.py` 时：

```python
# cognition/__init__.py
from cognition.engine_core import CognitiveEngine
from cognition.engine_tools import ToolRegistry
```

**不要**加 `sys.modules['cognition.engine'] = sys.modules['cognition.engine_core']`——这会制造隐藏依赖。直接改测试的 import 路径更干净。

### 层2: 桥接方法（向后兼容关键）

当旧 API 的 `register_tool`/`call_tool` 已从类中移除，但外部代码仍期待它们时：

```python
class CognitiveEngine:
    def register_tool(self, name, fn, description="", risk_level=0, params_schema=None):
        """桥接到 ToolRegistry.register()"""
        if hasattr(self, '_tools_obj') and self._tools_obj:
            self._tools_obj.register(name, fn, description=description,
                                     risk_level=risk_level, params_schema=params_schema)

    def call_tool(self, name, **kwargs):
        """桥接到 ToolRegistry.call()"""
        if not hasattr(self, '_tools_obj') or not self._tools_obj:
            raise RuntimeError("ToolRegistry 未初始化")
        fn = self._tools_obj._tools[name].get("fn")
        return asyncio.run(fn(**kwargs))

    def list_tools(self) -> list[str]:
        """桥接到 ToolRegistry.list_names()"""
        if hasattr(self, '_tools_obj') and self._tools_obj:
            return self._tools_obj.list_names()
        return []
```

### 层3: 测试重写（适配新架构）

旧测试检查 `hasattr(engine.CognitiveEngine, "_tool_web_search")`，新架构改为检查 `ToolRegistry._tools` 字典：

```python
# 旧 API（已废弃）
assert hasattr(engine.CognitiveEngine, "_tool_web_search")

# 新 API（ToolRegistry）
assert "web_search" in registry._tools
assert callable(registry._tools["web_search"]["fn"])
```

## 测试迁移检查清单

- [ ] 搜索所有 `from cognition.engine import` → 改为模块路径或类导入
- [ ] 搜索所有 `_tool_` → 改为工具注册名（去前缀）
- [ ] 搜索所有 `register_tool`/`call_tool` 调用 → 确认桥接方法存在
- [ ] 搜索所有 `importlib.util.find_spec("cognition.engine")` → 更新模块名
- [ ] 缺失工具用 `pytest.skip` 标记（附带原因），不掩盖
- [ ] 安全审计测试：`_tool_execute_shell` → `run_shell`（risk_level=3 检查）

## 反模式（禁止）

1. **不要**用 `sys.modules` 注入别名（如 `sys.modules['cognition.engine'] = ...`）来绕过导入错误——这是在制造隐藏依赖
2. **不要**为每个缺失的工具创建空壳——用 skip 透明标记
3. **不要**修改测试使其"总是通过"——要确保测试在检查有意义的属性
