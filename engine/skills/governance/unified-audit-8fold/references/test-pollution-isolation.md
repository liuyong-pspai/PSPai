# 测试污染三阶段隔离法

> 来源：2026-05-30 P07 全量测试从 377/61 清零到 437/0 的实战经验

## 问题特征

测试单独跑全绿，全量跑就失败。常见原因：
- 多个测试文件的**模块级** `sys.path.insert(0, ...)` 污染全局 import 解析
- module-scope fixture 的 `os.chdir(tmpdir)` 导致后续测试从错误路径导入模块
- **被污染的不是 cwd/sys.path，而是 `sys.modules` 缓存**——即使 fixture teardown 恢复了路径，已导入的模块仍在缓存中

## 三阶段隔离方案

在 `tests/conftest.py` 中部署三层防护：

### 阶段1: 收集后恢复（`pytest_collection_modifyitems` 钩子）

```python
_ORIGINAL_CWD = os.getcwd()
_ORIGINAL_SYS_PATH = list(sys.path)

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    """收集完成 → 恢复 sys.path，清除模块级 import 污染"""
    current = list(sys.path)
    for p in current:
        if p not in _ORIGINAL_SYS_PATH:
            try:
                sys.path.remove(p)
            except (ValueError, IndexError):
                pass
    try:
        os.chdir(_ORIGINAL_CWD)
    except Exception:
        pass
```

### 阶段2: 模块执行前清理（module-scope autouse fixture）

这是关键——`sys.modules` 中缓存了从 `/tmp/` 导入的模块，必须清除：

```python
def _purge_tmp_modules():
    """清除从临时目录导入的模块"""
    to_purge = []
    for mod_name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        if not hasattr(mod, '__file__') or not mod.__file__:
            continue
        if mod.__file__.startswith('/tmp/'):
            to_purge.append(mod_name)
    for name in to_purge:
        del sys.modules[name]

@pytest.fixture(scope="module", autouse=True)
def _purge_before_module():
    """每个模块执行前清理 sys.modules 中的 tmp 模块"""
    _purge_tmp_modules()
    _restore_sys_path()
    try:
        os.chdir(_ORIGINAL_CWD)
    except Exception:
        pass
    yield
```

### 阶段3: 函数级恢复（function-scope autouse fixture）

兜底保护，每个测试函数前后恢复 cwd 和 sys.path。

## 污染诊断二分法

当全量失败但单独通过时，用二分法定位污染源：

```bash
# 从核心模块开始，逐个加文件
pytest tests/test_soul.py tests/test_A.py
pytest tests/test_soul.py tests/test_A.py tests/test_B.py
# ...直到 soul 再次失败 → 最后一个加的文件就是污染源
```

## 关键认知

1. **问题不在 pytest fixture teardown 顺序**——module-scope fixture 的 teardown 确实恢复了 cwd/sys.path，但 `sys.modules` 缓存不会自动清除
2. **收集阶段就已污染**——pytest 收集时需要 import 所有测试模块，模块级的 `sys.path.insert` 在此时执行
3. **`_purge_tmp_modules()` 只清除 `/tmp/` 路径**——不够彻底时可能需要扩大到所有临时目录前缀
