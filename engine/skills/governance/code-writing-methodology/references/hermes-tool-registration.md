# Hermes 工具注册范式 — 将离线工具接入框架

> 源：2026-05-28 注册 yu_long_tools.py 的 14 个工具

## 必要步骤

### 1. 确认 registry API 签名

```python
# tools/registry.py
registry.register(
    name="tool_name",       # 工具名（LLM 调用时使用的名称）
    toolset="yulong",       # 工具集名称（用于分组和启用/禁用）
    schema={                # OpenAI function 格式的 schema
        "name": "tool_name",
        "description": "...",
        "parameters": {...},
    },
    handler=lambda args, **kw: actual_function(**args),
    emoji="🔧",             # 可选：CLI 显示图标
)
```

### 2. 创建 tools/ 目录下的注册文件

文件路径：`tools/{toolset}_tools.py`
- 导入原始函数（可以用 sys.path 技巧从外部目录导入）
- 逐个调用 `registry.register()`
- 不需要 `if __name__` 块——框架在 import 阶段自动触发

### 3. 关键陷阱

- **网关重启才生效**：工具在模块 import 时注册，而模块只在网关启动时加载。新增/修改工具后必须重启网关。重启会杀死当前会话（systemd 自动恢复）。
- **schema 的 name 字段**必须与 `registry.register()` 的 `name` 参数一致
- **handler 签名**：`lambda args, **kw: fn(**args)` — args 是 LLM 传入的参数字典，kw 是框架注入的额外上下文
- **无需 `if __name__`**：不要用 `if __name__ == "__main__"` 包裹注册代码

### 4. 验证

```bash
# 语法验证
python3 -m py_compile tools/{toolset}_tools.py

# 重启后验证（在 agent 中）
# 用相应的工具名测试是否可用
```

## 示例：14 工具注册模板

见 `tools/yulong_tools.py`（本次会话创建，8979 字节，14 个工具）
