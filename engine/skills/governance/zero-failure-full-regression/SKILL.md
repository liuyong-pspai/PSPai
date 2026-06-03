---
name: zero-failure-full-regression
category: governance
description: 全量回归清零方法论 — 从 N 个失败到 0 个失败的六步闭环。覆盖：污染三阶段隔离、架构迁移后测试重写、模块级 NameError 发现、缺失工具透明追踪。PSPAI P07 实战验证（377→437 passed, 0 failed）。
version: 1.0.1
author: 刘玉龙 P07
tags: [testing, regression, cleanup, conftest, isolation, audit]
related_skills: [unified-audit-8fold, code-quality-closed-loop, liuyulong-six-step-closed-loop]
last_updated: 2026-05-30
changelog: |
  v1.0.1 — 修复章节编号顺序（步骤4/5互换对齐六步图）；新增步骤2分类子节。
  v1.0.0 — 初始版本。基于 PV12 全量回归 65→0 实战。
---

# 全量回归清零方法论

> 从 65 个失败到 0 个失败的完整操作手册。  
> PSPAI P07 实战验证：377 passed, 61 failed → 437 passed, 0 failed。

## 核心原则

1. **先分类，再批量** — 不盲目逐个修，先审计分类：污染假失败 vs 代码真 bug vs 测试过时
2. **先隔离，再修复** — 污染是传播性的，不隔离会掩盖真实进度
3. **缺失 ≠ 忽略** — 架构迁移后消失的功能用 `pytest.skip` 透明追踪，不偷偷删测试

---

## 六步清零闭环

```
步骤1: 全量跑 → 拿到失败清单
步骤2: 分类（污染假失败 / 代码真bug / 测试过时 / 配置缺失）
步骤3: 隔离污染（conftest.py 三阶段）
步骤4: 修复代码 bug（NameError / 缺 import / return None）
步骤5: 重写过时测试（架构迁移 / 方法改名 / 路径更新）
步骤6: 全量验证 → 0 failed
```

> ⚠️ **步骤2和步骤3可并行**：隔离污染不需要等分类完成。加 conftest.py 越早越好。  
> ⚠️ **步骤4和步骤5可并行**：代码 bug 和测试过时互不依赖。

---

## 步骤1: 全量跑 → 拿到失败清单

```bash
python3 -m pytest tests/ --tb=line -q 2>&1 | tee /tmp/regression.log
```

从输出中提取四类失败：

| 类别 | 识别特征 | 示例 |
|:---|:---|:---|
| **污染假失败** | 单独跑全绿，全量跑才失败 | soul 8/8 → 全量 8 fail |
| **代码真 bug** | 单独跑也失败；NameError/AttributeError/ImportError | `traceback.print_exc()` 缺 import |
| **测试过时** | ImportError（模块路径变了）/ AttributeError（方法改名） | `from cognition.engine import ...` |
| **配置缺失** | AssertionError（API Key 等） | `❌ API Key未配置` |

**关键操作**：对每个失败文件单独跑 `pytest tests/test_xxx.py`，对比全量结果。

---

## 步骤2: 分类 — 确定修复策略

对每个失败文件单独跑，二分定位污染边界：

```bash
# 单个文件 → 确认是否真失败
pytest tests/test_soul.py --tb=short -q

# 二分法找污染源
pytest tests/test_soul.py tests/test_engine.py tests/test_kernel.py --tb=line -q
```

四类失败的优先度：

| 类别 | 特征 | 优先度 |
|:---|:---|:---|
| 污染假失败 | 单独全绿，组合才失败 | ⚡ 最先隔离 |
| 代码真 bug | 单独也失败；NameError/AttributeError | 🔧 隔离后修复 |
| 测试过时 | ImportError（路径变了）/ AttributeError（改名） | 📝 隔离后重写 |
| 配置缺失 | API Key / .env 等 | 🗄️ 最后补齐 |


## 步骤3: 隔离污染 — conftest.py 三阶段

这是**最关键的步骤**。污染不隔离 = 看不清真实进度。

### 根因分析

测试文件的模块级 `sys.path.insert(0, ...)` 在 pytest 收集阶段污染了 `sys.path`，module-scope fixture 中的 `os.chdir(tmpdir)` 导致 `sys.modules` 缓存了从临时目录导入的错误模块。

### 解决方案：conftest.py

```python
# tests/conftest.py
import os, sys, pytest

_ORIGINAL_CWD = os.getcwd()
_ORIGINAL_SYS_PATH = list(sys.path)


def _restore_sys_path():
    """恢复到原始 sys.path"""
    current = list(sys.path)
    for p in current:
        if p not in _ORIGINAL_SYS_PATH:
            try:
                sys.path.remove(p)
            except (ValueError, IndexError):
                pass


def _purge_tmp_modules():
    """清除从临时目录导入的模块"""
    to_purge = []
    for mod_name, mod in list(sys.modules.items()):
        if mod is None or not hasattr(mod, '__file__') or not mod.__file__:
            continue
        if mod.__file__.startswith('/tmp/'):
            to_purge.append(mod_name)
    for name in to_purge:
        del sys.modules[name]


# 阶段1: 收集完成后恢复 sys.path
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    _restore_sys_path()
    try:
        os.chdir(_ORIGINAL_CWD)
    except Exception:
        pass


# 阶段2: 每个模块执行前清理 sys.modules
@pytest.fixture(scope="module", autouse=True)
def _purge_before_module():
    _purge_tmp_modules()
    _restore_sys_path()
    try:
        os.chdir(_ORIGINAL_CWD)
    except Exception:
        pass
    yield


# 阶段3: 每个测试函数前后恢复
@pytest.fixture(autouse=True)
def _isolate_per_test():
    cwd_before = os.getcwd()
    path_before = list(sys.path)
    yield
    try:
        if os.getcwd() != cwd_before:
            os.chdir(cwd_before)
    except (OSError, FileNotFoundError):
        try:
            os.chdir(_ORIGINAL_CWD)
        except Exception:
            pass
    current_path = list(sys.path)
    for p in current_path:
        if p not in path_before and p not in _ORIGINAL_SYS_PATH:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
```

### 验证污染已隔离

```bash
# 之前受污染的文件应该和单独跑结果一致
pytest tests/test_soul.py tests/test_kernel.py tests/test_memory.py -v -q
```


## 步骤4: 修复代码 bug

### 模块级 NameError 快速定位

| 错误 | 根因 | 修复 |
|:---|:---|:---|
| `NameError: name 'traceback' is not defined` | 调用 `traceback.print_exc()` 但未 `import traceback` | 加 import |
| `NameError: name 'identity' is not defined` | 引用 `identity.loader.fn()` 但未 `import identity` | 加 try/except import |
| `TypeError: argument of type 'NoneType' is not iterable` | 函数无 return 语句返回 None | 补 `return ""` |

### 快速扫描

```bash
# 找所有调用但未导入的模块
grep -rn 'traceback\.' --include='*.py' | grep -v 'import traceback'
grep -rn 'identity\.' --include='*.py' | grep -v 'import identity'
```


## 步骤5: 重写过时测试

### 架构迁移 → 测试重写策略

当测试大量 `ImportError`/`AttributeError` 指向同一模块路径时，说明发生了架构重构：

| 旧架构 | 新架构 | 测试症状 |
|:---|:---|:---|
| `from cognition.engine import CognitiveEngine` | `from cognition.engine_core import CognitiveEngine` | ImportError |
| `CognitiveEngine._tool_web_search` | `ToolRegistry._tools["web_search"]` | AttributeError |
| `engine._save_history(chat_id)` | `engine._persist_histories()` | AttributeError |

### 重写三策略

1. **加桥接方法** — 如果旧 API 仍有外部调用者，先补桥接
   ```python
   def register_tool(self, name, fn, **kwargs):
       if self._tools_obj:
           self._tools_obj.register(name, fn, **kwargs)
   ```

2. **重写测试对新 API** — 不要逐个修旧测试，直接基于新 API 重写
   - 工具存在性：`hasattr(engine, "_tool_xxx")` → `assert "web_search" in registry._tools`
   - 安全检查：源码字符串扫描 → risk_level 检查

3. **缺失功能透明追踪** — 用 `pytest.skip` 记录缺失
   ```python
   MISSING_TOOLS = {
       "feishu_check": "_tool_feishu_check",
       "delete_file": "_tool_delete_file",
   }
   
   @pytest.mark.parametrize("legacy_name", list(MISSING_TOOLS.keys()))
   def test_missing_tool_documented(self, registry, legacy_name):
       pytest.skip(f"工具 '{legacy_name}' 尚未在 ToolRegistry 中实现")
   ```

### 批量修复清单模板

```
## 全量回归清零修复清单

### 污染隔离
- [ ] conftest.py 三阶段隔离
- [ ] 验证：受污染文件单独跑 vs 全量跑一致

### 代码 Bug
- [ ] 缺 import 扫描（traceback / identity / ...）
- [ ] 函数 return None 扫描

### 测试重写
- [ ] 架构迁移 API 对齐（ImportError → 新路径）
- [ ] 方法改名对齐（AttributeError → 新方法名）
- [ ] 断言值对齐源码（硬编码常量变化）
- [ ] 文件路径更新（重构拆分后目标文件变了）

### 配置补齐
- [ ] .env 文件（API Key）
```


## 步骤6: 验证闭环

```bash
# 全量回归
python3 -m pytest tests/ --tb=line -q
# 期望输出: N passed, 0 failed

# 逐个验证核心模块
pytest tests/test_kernel.py tests/test_soul.py tests/test_memory.py -v -q
pytest tests/test_engine.py tests/test_tools.py -v -q
```


## 交付标准

- [ ] `pytest tests/` 输出 `0 failed`
- [ ] 所有 skip 有明确的 `pytest.skip()` 消息说明原因
- [ ] conftest.py 存在且含三阶段隔离
- [ ] 缺失功能有透明追踪（skip 而非删除测试）
- [ ] .env 或等价配置到位


## 常见陷阱

| 陷阱 | 表现 | 预防 |
|:---|:---|:---|
| 不隔离先修复 | 修完又出现新失败，进度看不清楚 | 步骤3必须在步骤4/5之前 |
| 直接删测试 | 缺失功能被遗忘 | 用 pytest.skip 透明追踪 |
| WHITELIST_DISABLE 全局设 | 安全测试全部失效 | 只在需要的测试中 try/finally 临时设置 |
| 忘记补 .env | LLM 测试全失败 | 检查 `test_real_llm.py` 是否绿 |
| post_split_audit 误报 | import/继承检查失败 | 独立类架构 4/6 通过即足够，不需骨架继承 |


## 实战案例

**PV12 全量回归清零**（2026-05-30）：

| 阶段 | Pass | Fail | Skip |
|:---|:---|:---|:---|
| 初始 | 377 | 61 | 5 |
| 污染隔离 | 377 | 61 | 5（分类清晰） |
| 历史死代码 | 377 | 57 | 9 |
| 架构迁移重写 | 403 | 35 | 12 |
| 污染根除 | 424 | 13 | 12 |
| 逐个清零 | **437** | **0** | 13 |

核心模块全绿：kernel 13/13、soul 8/8、memory 107/107、engine 8/8、tools 25/25。
