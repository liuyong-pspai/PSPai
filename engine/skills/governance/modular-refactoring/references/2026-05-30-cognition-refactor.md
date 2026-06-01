# Cognition 目录重构实录 — 2026-05-30

## 背景

`engine_tools.py`（4042行）和 `engine_core.py`（3287行）两个巨型文件需要拆分为独立子模块。

## 拆分结果总览

| 文件 | 拆分前 | 拆分后 | 新模块数 |
|:---|:--:|:--:|:--:|
| engine_tools.py | 4042 | **350** | 8 |
| engine_core.py | 3287 | **655** | 1 |
| **合计** | **7329** | **1005** | **9** |

## 产出的子模块

| 模块 | 行数 | 内容 |
|:---|:--:|:---|
| tools_file.py | 113 | 文件读写 Mixin |
| tools_system.py | 54 | 系统工具 Mixin |
| tools_health.py | 63 | 自检 Mixin |
| tools_state.py | 26 | 状态机（之前拆出） |
| tools_loader.py | 38 | 模块加载（之前拆出） |
| tools_schemas.py | 480 | 36工具 Schema Mixin |
| tools_registry.py | 234 | 工具注册 Mixin |
| tools_safety.py | 46 | 安全校验 Mixin |
| memory_tagger.py | 80 | 记忆提炼 Mixin |
| tools_impl.py | 2916 | 40+工具实现 Mixin |
| core_subsystems.py | 2594 | 引擎子系统 Mixin |

## 关键教训

### P0: Mixin 文件不继承父文件 import

拆分后 5 个 Mixin 文件完全缺少 import 语句。Python 在 Mixin 方法**定义所在模块**的 globals 中解析名称，而非在继承链命名空间中。`py_compile` 不报错但运行时 `NameError`。

**发现方式：** 八维审计的维度1检查发现所有 Mixin 文件零 import。

**修复：**
- tools_impl.py: 新增 14 个标准库 import
- core_subsystems.py: 新增所有导入 + CognitiveEngine→type(self) + checkpoint函数迁移
- tools_registry.py, memory_tagger.py: 各新增 log import
- engine_tools.py: _TOOL_SCHEMAS→self._TOOL_SCHEMAS

### 计划估算不可信

原始计划中的行数估算偏差最高 80 倍：
- _kernel: 估算 400 → 实际 5
- _check_cmd: 估算 440 → 实际 35
- _edit_file: 估算 1190 → 实际 65

**正确做法：** grep 获取精确方法边界后再制定计划，执行中随时调整。

### 保集法（KEEP set）是最有效的大规模提取方式

对于非连续代码提取，定义 KEEP 行号区间集合，其余全部提取到一个大 Mixin 中。

```python
KEEP = [(1,299), (784,901), (1037,1292), (2858,2895)]
keep_set = {i for s,e in KEEP for i in range(s-1,e)}
extract_lines = [l for i,l in enumerate(lines) if i not in keep_set]
```

## 变换脚本列表

按执行顺序：
1. `/tmp/transform_engine.py` — 提取 tools_schemas.py（#4）
2. `/tmp/transform_engine2.py` — 提取 tools_registry.py（#5）
3. `/tmp/transform_safety.py` — 提取 tools_safety.py（#6）
4. `/tmp/transform_tagger.py` — 提取 memory_tagger.py（#7）
5. `/tmp/transform_final.py` — 提取 tools_impl.py（#8）
6. `/tmp/transform_core_final.py` — 提取 core_subsystems.py
7. `/tmp/transform_core_tight.py` — 收紧 core_subsystems
8. `/tmp/transform_core_min.py` — 提取 deliver_message
9. `/tmp/fix_subsystems.py` — 审计后修复所有 import + checkpoint迁移 + CognitiveEngine→type(self)

## 备份节点

- PV9: `/集团公司/Agent/PV9_20260530/` — 拆分前快照
- PV10: `/集团公司/Agent/PV10_20260530/` — 拆分完成后快照
