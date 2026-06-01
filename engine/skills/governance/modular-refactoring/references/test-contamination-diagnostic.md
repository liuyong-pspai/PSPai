# 测试污染诊断：sys.path / os.chdir 全局副作用扫描

> 2026-05-30 — 全量测试 `kernel 13/13 ✅` 但 `pytest tests/` 失败时的诊断实录

## 问题模式

测试文件单独跑全绿，全量跑部分失败。通常是上游测试的模块级副作用污染了下游测试的环境。

## 诊断命令

### 1. 扫描所有 os.chdir 调用

```bash
grep -rn 'os\.chdir\|chdir' tests/ --include='*.py' | grep -v '__pycache__'
```

重点关注：`os.chdir` 后**没有对应恢复**（无 `os.chdir(old_cwd)`）的文件。

### 2. 扫描所有 sys.path 修改

```bash
grep -rn 'sys\.path\.\(insert\|append\|remove\)' tests/ --include='*.py' | grep -v '__pycache__'
```

分类：
- **模块级 `sys.path.insert`（无 remove）** → 永久污染，pytest 收集阶段就已生效
- **fixture 内 `sys.path.insert` + teardown `sys.path.remove`** → 安全，但 scope="module" 时持续整个文件
- 模块级污染是主要根因——约 25+ 个测试文件有模块级 `sys.path.insert(0, ...)` 未清理

### 3. 排查特定模块污染

如果怀疑特定测试被污染，用 `pytest --co` 查看收集顺序，确认上游测试：

```bash
python3 -m pytest tests/ --collect-only -q 2>&1 | head -40
```

## 修复策略

| 污染类型 | 修复方式 |
|:---|:---|
| 模块级 `os.chdir` 无恢复 | 移到 `conftest.py` 的 `session` fixture 或改为相对路径 |
| 模块级 `sys.path.insert` | 改为 fixture 内 insert + teardown remove |
| fixture `os.chdir` scope="module" 影响后续文件 | 改为 scope="function" |
| archive.dead 导入失败 | `try/except ImportError: pytest.skip(allow_module_level=True)` |

## 本会话案例

- 污染源：25+ 个测试文件在模块级做 `sys.path.insert(0, ...)` 无清理
- 受害者：kernel 测试的 `full_kernel_env` fixture 用 `os.chdir(tmpdir)` 改路径，teardown 恢复的 `old_cwd` 可能已被上游污染
- 最终状态：kernel 单独跑 13/13 ✅，全量跑因 sys.path 污染导致 module 导入混乱
