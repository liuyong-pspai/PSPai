# kernel.py 拆分实录（2026-05-30 · 第三阶段）

## 拆分数据

kernel.py: 3711行 → 106行骨架 + 5子模块

| 子模块 | Mixin类 | 定义数 | 行数 |
|:---|:---|:--:|:--:|
| kernel_providers.py | (模块级) | 11 | 652 |
| kernel_lifecycle.py | KernelLifecycleMixin | 17 | 960 |
| kernel_systems.py | KernelSystemsMixin | 15 | 476 |
| kernel_growth.py | KernelGrowthMixin | 23 | 745 |
| kernel_status.py | KernelStatusMixin | 15 | 945 |

组合类：`RuntimeKernel(KernelLifecycleMixin, KernelSystemsMixin, KernelGrowthMixin, KernelStatusMixin)`

## 新陷阱

**Import 收集三毒：**
1. 文档字符串伪代码（`from kernel import kernel`）→ 从docstring结束后扫描
2. 函数体内 import（`import os, yaml` 有缩进）→ 用 `line.startswith('import ')` 非 stripped
3. 多行括号截断 → 循环读到 `)` 闭合

**模块级语句误收：** `kernel = RuntimeKernel()` 在方法范围内，收入子模块 → grep 检查删除

**标准库遗漏：** `import asyncio` 在收集边界被跳过 → 子模块补回
