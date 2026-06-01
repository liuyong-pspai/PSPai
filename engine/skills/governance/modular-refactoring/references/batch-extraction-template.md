# 批量提取脚本模板

> tools_impl.py + core_subsystems.py 第二阶段拆分的通用模板。
> 适用于将巨型单文件一次性拆分为 N 个功能域子模块。

## 使用步骤

### 1. 精确分析边界

```python
import re

with open("target.py") as f:
    lines = f.readlines()

# 找所有顶层定义（类 + 方法）
top_items = []
for i, line in enumerate(lines):
    m = re.match(r'^(    (async )?def |async def |def |class )', line)
    if m:
        nm = re.match(r'^(    )?(async )?def (\w+)|^(async )?def (\w+)|^class (\w+)', line)
        name = nm.group(3) or nm.group(5) or nm.group(6) if nm else '???'
        top_items.append((i, name))

# 计算真实范围
ranges = {}
for idx, (start, name) in enumerate(top_items):
    end = top_items[idx+1][0] if idx+1 < len(top_items) else len(lines)
    ranges[name] = (start, end)
```

**注意：** 模块级函数（不在任何类中的 def）也会被捕捉到。需要从分组中排除。

### 2. 定义功能域分组

```python
GROUP_A = ['method1', 'method2', ...]  # 搜一搜类
GROUP_B = ['method3', 'method4', ...]  # 记忆类
# ... 按功能域分组所有方法名
```

### 3. 定义模块模板

```python
HEADER = """#!/usr/bin/env python3
\"\"\"
{title} — 描述（{desc}）

从 target.py 拆分。
\"\"\"

# 所有需要的 import（从原文件复制）
import os
...

from SHARED.logger import log


class {classname}:
    \"\"\"{desc}\"\"\"

"""
```

### 4. 批量生成

```python
GROUPS = [
    ("output_a.py", "MixinA", "描述A", GROUP_A),
    ("output_b.py", "MixinB", "描述B", GROUP_B),
    # ...
]

for filename, classname, desc, method_names in GROUPS:
    blocks = []
    for name in method_names:
        if name in ranges:
            start, end = ranges[name]
            blocks.append(''.join(lines[start:end]))

    with open(f"cognition/{filename}", 'w') as f:
        f.write(HEADER.format(title=filename, desc=desc, classname=classname))
        f.write(''.join(blocks))
```

### 5. 零遗漏检查

```python
all_grouped = set()
for _, _, _, methods in GROUPS:
    all_grouped.update(methods)

module_level = ['func1', 'func2']  # 模块级函数，排除
class_names = ['TargetClass']       # 类定义本身，排除

missing = [m for m in ranges if m not in all_grouped
           and m not in module_level and m not in class_names]
print(f"遗漏: {missing}")  # 必须为空
```

### 6. 验证

```bash
for f in output_*.py; do python3 -m py_compile "$f" && echo "$f OK" || echo "$f FAIL"; done
```

## 关键教训

1. **嵌套函数体被计入外层方法**：`_web_search` 用 `grep` 看起来只有 21 行，实际含嵌套闭包 299 行
2. **模块级函数不拆分**：如 `save_checkpoint` 是模块级 API，保留在骨架文件中
3. **命名冲突**：新子模块可能与第一阶段拆分的文件重名（如 `tools_system.py` vs 新 `tools_shell2.py`），需要加后缀区分
4. **import 全量复制**：每个子模块复制原文件的全部 import（以防遗漏），安全优先于精简
