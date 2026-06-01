# 测试污染隔离 — conftest.py 三阶段防护

> 问题：模块拆分后，module-scope fixture（tmpdir + os.chdir + sys.path.insert）
> 在全量测试中造成跨文件污染——sys.modules 缓存了从临时目录导入的模块，
> 后续测试引用同名模块时拿到错误版本，单独跑全绿但全量跑失败。

## 症状

- 单文件测试全绿（如 `pytest tests/test_soul.py` → 8/8）
- 全量跑时相同测试失败（soul 9 failed）
- 排除特定上游测试文件后下游恢复
- `conftest.py` 仅做 `autouse` cwd/sys.path 恢复不够

## 根因

1. `scope="module"` fixture 在 setup 中 `os.chdir(tmpdir)` + `sys.path.insert(0, tmpdir)`
2. 在 fixture 活动期间，Python import 了同名模块 → 缓存到 `sys.modules`
3. fixture teardown 恢复 cwd/sys.path，但 `sys.modules` 不清
4. 后续测试 `import soul` 命中缓存 → 拿到 tmpdir 副本 → 失败

## 方案：三阶段隔离

### 1. 启动快照（模块级，最先执行）

```python
_ORIGINAL_CWD = os.getcwd()
_ORIGINAL_SYS_PATH = list(sys.path)
```

### 2. 收集后恢复（`pytest_collection_modifyitems`）

```python
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    _restore_sys_path()
    os.chdir(_ORIGINAL_CWD)
```

### 3. 模块级清理（module-scope autouse fixture）

```python
def _purge_tmp_modules():
    """清除从 /tmp/ 路径导入的模块"""
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
    _purge_tmp_modules()
    _restore_sys_path()
    os.chdir(_ORIGINAL_CWD)
    yield
```

### 4. 函数级恢复（function-scope autouse fixture）

```python
@pytest.fixture(autouse=True)
def _isolate_per_test():
    cwd_before = os.getcwd()
    path_before = list(sys.path)
    yield
    os.chdir(cwd_before)
    # 移除新增 sys.path 条目
    for p in list(sys.path):
        if p not in path_before and p not in _ORIGINAL_SYS_PATH:
            sys.path.remove(p)
```

### 为什么需要 module-scope autouse

`function-scope autouse` 在 module fixture teardown **之前**执行。如果 module fixture 在 tmpdir 中 import 了模块，这些模块在 autouse 恢复时已经缓存了。module-scope autouse 在每个模块的**所有测试执行前**先清理，确保干净起点。

## 效果

会话实测：424 passed, 61 failed → 424 passed, 13 failed（soul 9 个污染清零，engine/kernel 全绿）

## 二分诊断法

找到污染源的快速方法：

```bash
# 1. 确认目标测试单独全绿
pytest tests/test_soul.py

# 2. 逐个加怀疑文件，找到首次出现失败的文件
for f in test_engine test_kernel test_tools; do
    echo "=== $f ==="
    pytest tests/test_soul.py tests/$f.py --tb=line -q | tail -3
done

# 3. 一旦定位到污染文件，检查其 module-scope fixture 的 sys.path 修改
grep -n 'sys\.path\.\(insert\|append\)\|os\.chdir' tests/$f.py
```
