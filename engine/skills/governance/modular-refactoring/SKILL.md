---
name: modular-refactoring
category: governance
description: 巨型Python文件模块化拆分方法论——Mixin提取 + 非连续保集 + 脚本化安全变换。适用于1000+行单体文件拆分为多个独立子模块的场景。
author: Agent
tags: [refactoring, mixin, modular, code-health, import-isolation, batch-extraction, backward-compat, regression-testing, kernel]
related_skills: [unified-audit-8fold]
version: 1.8.0
last_updated: 2026-05-31
changelog: |
  v1.8.0 — 🔴 新增陷阱10：Module-scope Fixture 跨文件污染 sys.modules
  conftest.py 三阶段隔离方案（收集后恢复→模块级清理→函数级恢复）
  新增参考：references/test-pollution-isolation.md（含二分诊断法）
  v1.7.0 — 🔴 新增陷阱9：测试文件导入路径过时（post_split_audit.py的盲区）
  拆分后强制审计从3步扩展为4步：+测试导入路径扫描
  修复模式表：旧路径→新路径的三种修复方式
  v1.6.0 — 补充陷阱6-8：模块级语句误收→_helpers.py模式、向后兼容重导出、测试夹具同步
  新增参考：references/memory-split-2026-05-30.md（composition模式拆分案例）
  v1.5.0 — 🚨 硬安检加固：新增 GATE CHECK（前置诊断脚本 pre_flight_check.py）
  新增第六阶段：后拆分强制审计（post_split_audit.py）
  交叉链接 unified-audit-8fold 作为必须的审计步骤
  原则：技能不是说明书，是安检门——不通过就不准动手
  v1.4.0 — 第三阶段 kernel.py 拆分（3711→106，5子模块）
  新增陷阱6-8：import收集三毒/模块级语句误收/标准库遗漏
  新增参考：references/kernel-split-2026-05-30.md
  v1.3.0 — 新增第五阶段：回归测试（拆分后必做）
  四步走：全量跑→分类失败→修复拆分引入→回归确认
  零回归损伤目标 + 历史遗留清单处理原则
  v1.2.0 — 第二阶段拆分（tools_impl 2938→32 + core_subsystems 2668→88，10子模块）
  新增：批量提取模板、导入超时处理、完整拆分数据表、向后兼容层验证方法
---

# 模块化拆分方法论

> 将巨型单体 Python 文件拆分为多个独立子模块的完整工作流。
> 核心：Mixin 多重继承 + Python 变换脚本 + 备份→变换→验证三步安全机制。

## 🚨 GATE CHECK — 强制前置安检（v1.5.0 新增）

**在触碰一行代码之前，必须通过此安检。不通过 = 禁止动手。**

### 第0步：必须加载本技能

任何拆分/重构任务 → 第一步必须是 `skill_view('modular-refactoring')`。不加载就动手 = 违规。

### 第1步：运行前置诊断脚本

```bash
python3 ~/.hermes-yulong/skills/governance/modular-refactoring/scripts/pre_flight_check.py <target_file.py>
```

### 第2步：阅读诊断报告，确认每一项风险都有应对方案

| 风险类型 | 必须确认 |
|:---|:---|
| 超大类（>1500行） | 是否需要拆分类本身？拆到多少行？ |
| 共享模块级函数 | 哪些提取到 `_helpers.py`？哪些保留？ |
| 类间交叉引用 | 哪些改用 `type(self)`？哪些函数迁移？ |
| 孤儿函数 | 是否业务需要？不需要就删除 |

### 第3步：确认后回复用户

格式：「用户，诊断通过。目标文件 X行，Y个类，Z个共享函数。我计划拆分为 N 个子模块 + 1 个 helpers 文件。确认开始？」

**铁律：跳过以上三步 → 拆分必然引入已记录的陷阱。这不是"可能出错"，是"必然出错"。**

---

## 适用场景

- 单个 `.py` 文件超过 1000 行
- 文件中包含多个逻辑独立的功能组
- 目标：将原始文件缩减到 ≤500-600 行的纯骨架

## 三步安全机制（铁律）

**每次提取的操作序列：**

```
1. cp original.py original.py.BAK_N   # 备份
2. python3 transform.py               # 变换脚本
3. python3 -m py_compile original.py  # 语法验证
```

任何时候出错 → 立即 `cp .BAK_N original.py` 恢复。绝不手修。

## Mixin 提取模式

### 模式 A：单连续块提取

适用：要提取的代码在文件中是**连续的一段**（一个方法/一组相邻方法）。

```python
# 新文件: tools_schemas.py
class SchemasMixin:
    """从 engine_tools.py 提取的 Schema 定义"""
    _TOOL_SCHEMAS: dict[str, dict] = { ... }
```

```python
# 原始文件: engine_tools.py
from cognition.tools_schemas import SchemasMixin

class ToolRegistry(FileToolsMixin, SystemToolsMixin, SchemasMixin):
    ...
```

操作：
1. 剪切连续代码块 → 新文件，包裹在 Mixin 类中
2. 在原始文件中添加 `from x import XxxMixin`
3. 在类继承链中添加 Mixin

### 模式 B：非连续保集提取（大扫除）

适用：需要提取的代码**分散在文件中多个位置**，留下的是少数核心方法。

**保集法**：定义 KEEP 行号区间，其余全部提取。

```python
KEEP = [
    (1, 299),         # imports + __init__
    (579, 653),       # deliver_message
    (784, 901),       # _main_loop
    (1037, 1292),     # cognitive cycle
    (2858, 2895),     # TODO methods
]

keep_set = set()
for s, e in KEEP:
    for i in range(s-1, e):
        keep_set.add(i)

keep_lines = [lines[i] for i in sorted(keep_set)]
extract_lines = [lines[i] for i in range(len(lines)) if i not in keep_set]
```

然后将 `extract_lines` 写入一个大 Mixin 文件。

### 模式 C：Python 变换脚本

对于复杂的提取操作（添加 import、修改类定义、删除多段代码），**写入一个独立 Python 脚本执行变换**，而非手动编辑。

变换脚本的结构：
```python
#!/usr/bin/env python3
"""Transform: extract X from file.py → new_module.py"""

# 1. 读取原始文件
with open(path, "r") as f:
    lines = f.readlines()

# 2. 验证边界（打印关键行的内容，确认行号正确）
print(f"L{X}: [{lines[X-1].strip()[:60]}]")

# 3. 执行变换
new_lines = [...]  # 构建新内容

# 4. 写入
with open(path, "w") as f:
    f.write("".join(new_lines))

# 5. 验证语法
import py_compile
py_compile.compile(path, doraise=True)
```

### 模式 D：组合 Mixin 向后兼容层

当拆分为 N 个子模块后，**保留原始文件作为薄包装层**，聚合所有子 Mixin：

```python
# 原始文件 tools_impl.py — 缩减为骨架
from cognition.tools_search import ToolsSearchMixin
from cognition.tools_memory import ToolsMemoryMixin
from cognition.tools_shell import ToolsShellMixin
# ... 其余子模块

class ToolsImplMixin(ToolsSearchMixin, ToolsMemoryMixin,
                     ToolsShellMixin, ...):
    """组合 Mixin — 向后兼容层"""
```

**优势：**
- 所有依赖文件（如 `engine_tools.py`）的 `from x import ToolsImplMixin` 无需改动
- 子模块的 Mixin 类也可独立导入用于测试
- 继承链通过 MRO 自动解析，无需手动管理方法调用

**关键约束：** 组合 Mixin 文件的 import 必须精简为仅子模块导入，不可保留原始巨型 import 块。

## ⚠️ 核心陷阱

### 陷阱 1：计划估算不可信

**绝对不要基于粗略的行数估算制定拆分计划。** 历史教训：

| 方法 | 估算行数 | 实际行数 |
|:---|:--:|:--:|
| _kernel | 400 | **5** |
| _check_cmd | 440 | **35** |
| _edit_file | 1190 | **65** |
| _auto_tag_memory | 1010 | **70** |

估算偏差可达 **80 倍**。正确的做法：

**步骤 1：用 execute_code 精确分析边界**

```python
import re

with open(path) as f:
    lines = f.readlines()

# 找所有顶层方法/类定义位置
top_methods = []
for i, line in enumerate(lines):
    m = re.match(r'^(    (async )?def |class )', line)
    if m:
        nm = re.match(r'^(    )?(async )?def (\w+)|^class (\w+)', line)
        name = nm.group(3) or nm.group(4) if nm else '???'
        top_methods.append((i, name))

# 计算真实范围：下个方法的起始行 = 当前方法的结束行
ranges = {}
for idx, (start_line, name) in enumerate(top_methods):
    end_line = top_methods[idx+1][0] if idx+1 < len(top_methods) else len(lines)
    ranges[name] = (start_line, end_line)
    print(f"{start_line:5d}-{end_line:5d} ({end_line-start_line:4d}行) {name}")
```

**关键洞察：** `grep -n "def "` 只能找到嵌套函数的外层定义起始行，嵌套函数体会被计入外层方法的范围。用**下个顶层定义的起始行**作为当前方法的结束行，才能算出真正的范围（包括嵌套闭包）。

**步骤 2：基于实际数据分组**

按功能域将方法名分组，计算每组总行数，确保每组 ≤800 行（含 import/docstring 开销约 20 行）。

**步骤 3：执行过程中随时调整**——实际结构可能与预期完全不同。

### 陷阱 2：read_file 去重缓存

`read_file` 工具对同一文件的同一区域有去重缓存。第二次读取同一偏移量范围时会返回 `{'status': 'unchanged', 'content_returned': False}`。

**解决方案**：使用 `terminal` + `sed` 读取文件内容，绕过缓存：
```bash
sed -n 'START,ENDp' file.py
```

### 🔴 陷阱 8：read_file 行号污染（P0 级 · 2026-05-30 新发现）

`read_file` 返回内容格式为 `LINE_NUM|CONTENT`，如：
```
1|#!/usr/bin/env python3
2|"""docstring"""
```

如果将此内容直接传给 `write_file`，文件会被写入带行号前缀的损坏内容。
Python编译报 `IndentationError: unexpected indent`。

**症状：**
- 文件有明显的行号前缀（`1|`、`2|`）
- `py_compile` 报缩进错误
- pytest collection 失败

**正确做法：**
- 用 `read_file` 读取后展示/分析——安全
- 用 `patch` 或 `terminal sed` 做写入——安全
- **禁止**将 `read_file` 返回值直接传给 `write_file`

**已添加审计检查项（unified-audit-8fold post_split_audit.py）：** 无。

### 陷阱 3：变换后行号漂移

每次提取都会改变后续代码的行号。如果计划多次提取，必须：
- 每次提取后重新 grep 获取新的行号
- 或者使用**保集法一次性提取**（推荐）

### 🔴 陷阱 4：Mixin 文件不继承父文件 import（P0 级）

**这是拆分中最致命的陷阱。** Python 在 Mixin 方法定义所在的**模块全局作用域**中解析名称，而非在继承链的命名空间中。

当方法体从父文件 `engine_tools.py` 提取到 `tools_impl.py` 时：
- 原文件中 `log.info(...)` 依赖父文件的 `from SHARED.logger import log`
- 提取后 `log` 在 `tools_impl.py` 的 globals 中**不存在** → 运行时 `NameError`

**症状：**
- `python3 -m py_compile` **不会报错**（语法正确，名称在编译时未解析）
- 运行时调用任何方法立即崩溃
- 影响所有提取的 Mixin 文件（本次会话：5 个文件全部中招）

**修复步骤：**
1. 对每个新 Mixin 文件，用 `grep -oE '\b(module_name)\.' mixin.py | sort | uniq -c` 统计所需模块
2. 在 Mixin 文件顶部添加所有缺失的 import 语句
3. 处理循环导入——如果 Mixin 引用了父类名（如 `CognitiveEngine._class_lock`），改用 `type(self)` 替代，避免 `from parent import ParentClass` 的循环依赖
4. 如果 Mixin 引用了父文件中的**模块级函数**（如 `save_checkpoint`），将该函数迁移到 Mixin 文件中，父文件从 Mixin 导入

**审计检查项（加入 unified-audit-8fold）：**
- 每个拆分后的 Mixin 文件是否包含其方法所需的所有顶层 import
- 是否存在 `SomeParentClass.some_attr` 的引用（应改为 `type(self).some_attr`）
- 是否有模块级函数在父文件和 Mixin 之间造成循环导入

### 陷阱 5：循环导入处理模式

当 Mixin 需要引用父类时：

```python
# ❌ 错误：循环导入
from cognition.engine_core import CognitiveEngine
class CoreSubsystemsMixin:
    def method(self):
        CognitiveEngine._class_lock  # CognitiveEngine 导入此 Mixin
```

```python
# ✅ 正确：type(self)
class CoreSubsystemsMixin:
    def method(self):
        type(self)._class_lock  # 运行时解析为 CognitiveEngine
```

当 Mixin 方法需要父文件的模块级函数时：
```python
# ✅ 将函数迁移到 Mixin 文件中（作为模块级函数）
# 父文件从 Mixin 导入该函数
from cognition.core_subsystems import save_checkpoint
```

### 🔴 陷阱 6：模块级语句误收 — _helpers.py 共享模式

**症状：** 拆分后每个子模块文件都包含相同的辅助函数、常量、导入块。例如 `_mkdir` 在 8 个文件中各复制一份。

**根因：** 提取脚本按类边界切割时，把模块级代码（在第一个类之前）也一起放进了每个子模块。

**解决方案 — `_helpers.py` 模式：**

```
原始文件 (2531行)
├── L1-L179: 模块级导入 + 辅助函数 + 路径常量
├── L180-L457: L0Core
├── L458-L745: L1WorkMemory
├── ...
└── L2272-L2531: MemorySystem

拆分后:
├── memory_helpers.py  ← L1-L179（只此一份）
├── memory_l0.py       ← L180-L457 + from .memory_helpers import ...
├── memory_l1.py       ← L458-L745 + from .memory_helpers import ...
├── ...
└── memory_new.py      ← L2272-L2531（骨架 + 组合）
```

**步骤：**
1. `pre_flight_check.py` 自动识别共享函数
2. 将共享的模块级代码完整提取到 `xxx_helpers.py`
3. 每个子模块 `from .xxx_helpers import func1, func2, CONST`
4. 子模块额外需要的标准库导入（json, os 等）单独写在子模块顶部
5. `post_split_audit.py` 自动检测重复函数定义

### 🔴 陷阱 7：向后兼容导入断裂

**症状：** 测试/外部代码 `from cognition.memory_new import L4Distillation` 报 `ImportError`。

**根因：** L* 类移到了子模块，但外部导入路径没变。

**解决方案 — 骨架文件重导出：**

```python
# memory_new.py — 骨架文件
from .memory_l0 import L0Core
from .memory_l1 import L1WorkMemory
# ...

# 向后兼容：外部仍可从 memory_new 直接导入
__all__ = ['MemorySystem', 'L0Core', 'L1WorkMemory', ...]
```

这样 `from cognition.memory_new import L4Distillation` 仍然有效。

### 🔴 陷阱 8：测试夹具未同步更新

**症状：** 拆分后测试全绿，但 CI/隔离环境跑测试时报 `ModuleNotFoundError: No module named 'cognition.memory_helpers'`。

**根因：** 测试夹具用 `shutil.copy2` 只复制了原始文件，没有复制新增的子模块。

**修复：** 拆分后搜索所有测试文件中的 `shutil.copy` 或 `copytree` 引用，补充新文件的复制逻辑。

**搜索命令：**
```bash
grep -rn "shutil.copy\|copytree.*cognition" tests/ --include="*.py"
```

此命令找出所有在临时环境中复制 cognition 目录的测试夹具。每个匹配的 fixture 都需要补充新子模块的复制语句。

```python
# 原夹具
shutil.copy2(src/"cognition/memory_new.py", dst/"cognition/memory_new.py")

# 修复后
shutil.copy2(src/"cognition/memory_new.py", dst/"cognition/memory_new.py")
for fn in ["memory_helpers.py", "memory_l0.py", ..., "memory_l7.py"]:
    shutil.copy2(src/f"cognition/{fn}", dst/f"cognition/{fn}")
```

### 🔴 陷阱 10：Module-scope Fixture 跨文件污染 sys.modules（P0 级 · 2026-05-30）

**症状：** 单文件测试全绿，全量跑时下游测试大面积失败。排除特定上游文件后下游恢复。soul 8/8 单跑全绿，全量跑 9 个失败。

**根因：** 拆分后测试的 `scope="module"` fixture 在 `os.chdir(tmpdir)` + `sys.path.insert(0, tmpdir)` 期间，Python import 了同名模块（如 `soul`），这些模块被缓存到 `sys.modules`。fixture teardown 恢复了 cwd/sys.path，但 `sys.modules` 中的缓存不清。后续测试 `import soul` 命中缓存 → 拿到 tmpdir 的错误副本 → 失败。

**二分诊断：**
```bash
# 1. 确认目标单独全绿
pytest tests/test_soul.py
# 2. 逐个加文件找污染源
for f in test_engine test_kernel test_tools; do
    pytest tests/test_soul.py tests/$f.py --tb=line -q | tail -3
done
```

**解决方案 — `conftest.py` 三阶段隔离：**
1. `pytest_collection_modifyitems` 钩子：收集后恢复 sys.path + cwd
2. `scope="module" autouse` fixture：每模块执行前清除 `/tmp/` 模块 → `del sys.modules[name]`
3. `autouse` fixture：每测试后恢复 cwd + sys.path

完整实现见 `references/test-pollution-isolation.md`。

**注意：** 仅 `autouse` fixture 不够——它在 module fixture teardown **之前**执行，无法清除 module 活动期间缓存的模块。必须有 module-scope 级清理。

### 🔴 陷阱 9：测试文件导入路径过时 — `post_split_audit.py` 的盲区（P0 级 · 2026-05-30）

**症状：** 拆分后源模块语法验证全通过、`post_split_audit.py` 6/6 通过，但全量测试出现大量 `ImportError: No module named 'cognition.engine'` 或 `cannot import name 'engine' from 'cognition'`。

**根因：** `post_split_audit.py` 只审计**源模块**（重复类/函数/导入/循环引用），不扫描**测试文件**。当 `cognition/engine.py` 拆分为 `engine_core.py` + `engine_llm.py` + `engine_tools.py` 后，`test_engine.py` 中的 `from cognition.engine import CognitiveEngine` 和 `test_tools.py` 中 25 处 `from cognition import engine` 全部断裂 —— 但这些不在审计范围内。

**诊断命令（拆分后必须执行）：**
```bash
# 1. 搜索所有引用旧模块路径的测试文件
grep -rn "from cognition.OLD_NAME\b\|import.*cognition.OLD_NAME" tests/ --include="*.py"

# 2. 搜索所有 "from cognition import old_submodule" 模式
grep -rn "from cognition import OLD_NAME" tests/ --include="*.py"

# 3. 检查 importlib.find_spec 中的旧路径引用
grep -rn 'find_spec.*cognition\.OLD_NAME' tests/ --include="*.py"
```

**修复模式：**

| 旧路径 | 新路径 | 修复方式 |
|:---|:---|:---|
| `from cognition.engine import CognitiveEngine` | `from cognition.engine_core import CognitiveEngine` | 直接替换 |
| `from cognition import engine` | `from cognition import engine_core as engine` | 加别名保持 `engine.X` 兼容 |
| `find_spec("cognition.engine")` | `find_spec("cognition.engine_core")` | 直接替换 |
| `get_source("cognition.engine")` | `get_source("cognition.engine_core")` | 直接替换 |

**注意：** 如果旧路径被大量测试引用（如 25 处），不要手动逐行改——用 `patch` 的 `replace_all=True` 一次性替换。

**关卡强化：** 拆分完成后的强制审计流程从 3 步扩展为 4 步：
```
语法验证 → 回归测试 → post_split_audit.py → 🆕 测试导入路径扫描
```

每次提取后：

- [ ] `python3 -m py_compile` 对原始文件和新建文件均通过
- [ ] **新 Mixin 文件包含所有必需的顶层 import 语句（grep 验证）**
- [ ] **无 `ParentClass.static_attr` 引用（应改为 `type(self).static_attr`）**
- [ ] 类继承链包含新 Mixin
- [ ] 原始文件行数符合预期
- [ ] 备份文件存在（`.BAK_N`）
- [ ] 🆕 **测试文件无残留旧模块路径引用（grep 验证）**
## 第五阶段：回归测试（拆分后必做）

语法验证通过 ≠ 功能无损。拆分完成后必须跑测试套件，分四步走：

### 步骤 1：全量跑（排除已知损坏测试）

```bash
python3 -m pytest tests/ --tb=line -q \
  --ignore=tests/test_real_llm.py \        # 需要真实LLM的集成测试
  --ignore=tests/test_*_integration.py \   # 集成测试
  --ignore=tests/test_deep.py \            # 慢测试
  --continue-on-collection-errors \
  2>&1 | tail -20
```

### 步骤 2：分类失败项

将每项失败归入以下两类之一：

| 类别 | 判定标准 | 处理方式 |
|:---|:---|:---|
| **拆分引入** | 错误出现在本次拆分的模块/继承链上 | **立即修复** |
| **历史遗留** | 错误来自未改动的文件/DEPRECATED模块/旧import路径 | 标记跳过，单独列清单 |

**常见拆分引入的失败模式：**
- `NameError: name 'xxx' is not defined` — 子模块缺少 import
- `TypeError: argument of type 'NoneType'` — 方法拆分后隐式返回 None（缺 return 语句）
- 测试读 `engine_tools.py` 搜索源码 → 源码已移至 `tools_xxx.py`
- `AttributeError: module 'X' has no attribute 'Y'` — 组合 Mixin 继承链断裂

**常见历史遗留的失败模式：**
- `ModuleNotFoundError: No module named 'cognition.engine'` — 旧模块引用
- DEPRECATED 文件中的方法报错 — 文件头已标注废弃
- 配置阈值变更（`assert 5 == 10`）— 非拆分导致

### 步骤 3：修复拆分引入的 Bug

每修一个 → `py_compile` → 跑该测试确认通过 → 再修下一个。不批量修。

### 步骤 4：回归确认

```bash
# 重新全量跑，确认 passed 数增加、failed 数减少
python3 -m pytest tests/ ... --tb=line -q 2>&1 | grep -E 'passed|failed|error'
```

**目标：拆分前后 passed 数不降，failed 数只减不增。**

### 历史遗留处理原则

拆分任务的职责是**零回归损伤**，不是修复所有历史遗留问题。历史遗留项：
- 列入单独清单
- 向用户汇报时明确标注"非本次拆分引入"
- 由用户决定是否另开任务修复

## 🚨 第六阶段：后拆分强制审计（v1.5.0 新增）

拆分完成不代表结束。每次拆分后必须运行审计脚本：

```bash
python3 ~/.hermes-yulong/skills/governance/unified-audit-8fold/scripts/post_split_audit.py <skeleton_file.py> "<submodule_pattern>"
```

示例：
```bash
python3 ~/.hermes-yulong/skills/governance/unified-audit-8fold/scripts/post_split_audit.py \
    cognition/memory_new.py "cognition/memory_l*.py"
```

**审计不通过 → 禁止提交、禁止进入下一个拆分任务。**

审计检查项（自动化）：
1. 重复类定义 — 同一类不应出现在多个子模块
2. 重复函数定义 — 辅助函数不应被复制（模块级语句误收）
3. 重复 import 块 — 大段相同导入应提取
4. Import 完整性 — 每个 Mixin 文件必须有方法所需的全部 import
5. 循环引用风险 — ParentClass.static_attr 引用
6. 骨架完整性 — 骨架文件是否组合了所有 Mixin

**铁律：跳过审计 → 7天内的测试失败追溯到此。**

## 验证清单
- [ ] 备份文件存在（`.BAK_N`）

## 工作流总结

```
1. 分析 → grep 获取精确方法边界 → 制定计划
2. 提取 → 备份 → 脚本变换 → 语法验证
3. 迭代 → 调整计划 → 重复步骤2 → 直到达标
4. 收尾 → 更新 REFACTOR_PLAN.md → 提交
```

## 产出物

每次重构应产出：
- `REFACTOR_PLAN.md`：记录拆分计划、进度、执行日志
- `*.BAK_N`：每次提取前的备份（保留用于回滚）
- 多个 Mixin 子模块文件
- 精简后的原始骨架文件

## 第二阶段完整数据（2026-05-30）

### tools_impl.py：2938 行 → 32 行骨架

| 子模块 | 类名 | 方法数 | 行数 |
|:---|:---|:--:|:--:|
| tools_search.py | ToolsSearchMixin | 12 | 619 |
| tools_memory_skill2.py | ToolsMemorySkillMixin | 13 | 241 |
| tools_shell2.py | ToolsShellMixin | 11 | 823 |
| tools_media2.py | ToolsMediaMixin | 7 | 501 |
| tools_data2.py | ToolsDataMixin | 8 | 419 |
| tools_cognition2.py | ToolsCognitionMixin | 17 | 441 |

**关键决策：** `_web_search` 实际 299 行（含嵌套 `_search_all_engines` 闭包），是搜索模块中最大的方法。命名加 `2` 后缀 (`tools_shell2.py`) 避免与第一阶段已拆分的简版 `tools_system.py` 冲突。

### core_subsystems.py：2668 行 → 88 行骨架

| 子模块 | 类名 | 方法数 | 行数 |
|:---|:---|:--:|:--:|
| core_messaging.py | CoreMessagingMixin | 9 | 1073 |
| core_lifecycle.py | CoreLifecycleMixin | 24 | 580 |
| core_cognition.py | CoreCognitionMixin | 12 | 506 |
| core_background.py | CoreBackgroundMixin | 19 | 526 |

**关键决策：** 模块级函数（`save_checkpoint`、`load_latest_checkpoint`、`_clean_old_checkpoints`）保留在骨架文件中，不归入任何 Mixin 类——它们是模块级 API，不是类方法。

### 向后兼容层验证方法

拆分后不要尝试完整导入测试（会触发模块初始化逻辑导致超时）。使用 `py_compile` 逐文件语法验证即可。正确性由以下三层保证：

1. **语法层：** `python3 -m py_compile` 对所有骨架 + 子模块文件通过
2. **导入层：** 骨架文件的 `from x import XxxMixin` 语句语法正确
3. **继承层：** 引擎文件（`engine_tools.py`/`engine_core.py`）无需任何改动——它们导入的仍然是骨架文件中的原始类名

## 批量提取脚本模板

完整的第二阶段拆分使用了批量提取脚本。将方法名分组 + 自动计算行范围 + 一步生成所有子模块。模板见 `references/batch-extraction-template.md`。

核心逻辑：
```python
# 1. 解析所有顶层方法边界（下个方法起始行 = 当前方法结束行）
# 2. 方法名分入功能组
# 3. 循环生成：每个子模块 = 自定义 HEADER + ''.join(对应代码块)
# 4. 验证：all_grouped == set(all_methods)（零遗漏检查）
```

## 参考

- 陷阱9完整案例：`references/test-contamination-diagnostic.md`
  engine.py→engine_core.py 拆分后测试导入断裂的诊断+修复全过程，
  含 sys.path 污染扫描命令和三种修复模式。
- 陷阱10完整方案：`references/test-pollution-isolation.md`
  conftest.py 三阶段隔离（收集后恢复→模块级清理→函数级恢复），
  解决 module-scope fixture 跨文件污染 sys.modules 的完整方案。含二分诊断法。
- 完整重构实录：`references/2026-05-30-cognition-refactor.md`
  包含 engine_tools.py（4042→350）和 engine_core.py（3287→712）的
  详细拆分过程、所有变换脚本、经验教训。
- 批量提取脚本模板：`references/batch-extraction-template.md`
  tools_impl.py（2938→6子模块）+ core_subsystems.py（2668→4子模块）的
  通用模板，含精确边界分析和零遗漏验证。
- 拆分后测试修复实录：`references/post-split-test-repair.md`
  第二阶段 10 模块拆分后测试修复全过程，含 4 个拆分引入 Bug + 6 类历史遗留修复，
  以及 21 个旧方法名→新方法名的完整映射表。
- kernel.py 拆分实录：`references/kernel-split-2026-05-30.md`
  第三阶段 kernel.py（3711→106，5子模块）拆分过程，含 Import 收集三毒、
  模块级语句误收、标准库遗漏三个新陷阱。
- memory_new.py 拆分实录：`references/memory-split-2026-05-30.md`
  第四阶段 memory_new.py（2531→293骨架+8子模块+1helpers）拆分过程，
  首次使用组合模式（非Mixin继承），含审计脚本组合模式检测增强。
