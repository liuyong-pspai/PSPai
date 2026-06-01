# TDD RED→GREEN→REFACTOR 实战记录

> 日期：2026-05-30 | 来源：第二阶段沙箱测试循环搭建

## 背景

在搭建 pytest 沙箱时，需要走一次真正的 TDD 循环来验证测试基础设施有效。

## RED 阶段（先写会失败的测试）

创建 `tests/test_tdd_memory_budget.py`，测试两个还不存在的函数：

```python
def test_budget_returns_int(self):
    budget = guard.budget_remaining()  # AttributeError! 函数不存在
    assert isinstance(budget, int)
```

运行结果：**5 failed, 1 passed**（5个测试因 `AttributeError: module has no attribute 'budget_remaining'` 失败）

## GREEN 阶段（最小实现让测试通过）

在 `l1_memory_guard.py` 中新增：

```python
AVG_ENTRY_SIZE = 300

def budget_remaining() -> int:
    return max(0, HARD_LIMIT - get_memory_size())

def budget_entries() -> int:
    return max(0, budget_remaining() // AVG_ENTRY_SIZE)
```

运行结果：**19 passed**（原有13个 + 新增6个全部通过）

## REFACTOR 阶段

无需重构——函数实现已经是最简形式。

## 关键教训

1. **RED 必须是真实的失败**：AttributeError 是最好的 RED——功能完全不存在
2. **GREEN 要最小化**：只写刚好让测试通过的代码，不提前优化
3. **TDD 在 AI Agent 中的价值**：不是防 bug，是**固化意图**——测试就是可执行的需求文档
4. **要有一个 test runner**：`python3 -m pytest tests/ -v` 是 TDD 的前提条件
