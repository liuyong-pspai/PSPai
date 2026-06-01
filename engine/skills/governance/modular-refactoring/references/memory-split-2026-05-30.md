# memory_new.py 拆分实录 — 2026-05-30

## 背景

`cognition/memory_new.py` 2531行，包含 9 个独立类（L0-L7 + MemorySystem）和 6 个模块级辅助函数。

## 第一次拆分（失败）

按类边界切割，每个子模块包含 `class MemorySystem` + 对应 L* 类 + 全部辅助函数。结果：
- `MemorySystem` 类在 8 个文件中重复
- 辅助函数各复制 8 份
- 相同 import 块出现在多个文件中
- 审计脚本 `post_split_audit.py` 检出 3/6 项未通过

## 第二次拆分（成功）

### 关键决策

1. **识别架构模式**：`pre_flight_check.py` 显示 MemorySystem 在文件末尾，引用所有 L* 类——这是**组合模式**（创建实例），不是继承。
2. **helpers.py 独立**：共享的辅助函数（_mkdir, _now, _ts）和路径常量提取到 `memory_helpers.py`。
3. **每个 L* 类独立文件**：`memory_l0.py` ~ `memory_l7.py`，只包含对应类 + 最小导入。
4. **骨架保留 MemorySystem**：组合所有 L* 类实例。

### 拆分数据

| 文件 | 行数 | 内容 |
|:---|:--:|:---|
| memory_helpers.py | 179 | 导入/常量/辅助函数 |
| memory_l0.py | 297 | L0Core (278行代码) |
| memory_l1.py | 310 | L1WorkMemory (288行代码) |
| memory_l2.py | 414 | L2Index (388行代码) |
| memory_l3.py | 118 | L3Archive (99行代码) |
| memory_l4.py | 306 | L4Distillation (284行代码) |
| memory_l5.py | 304 | L5SkillMerge (284行代码) |
| memory_l6.py | 270 | L6Renewal (250行代码) |
| memory_l7.py | 240 | L7Sublimation (221行代码) |
| memory_new.py | 293 | MemorySystem 骨架 |

### 审计结果

`post_split_audit.py` 6/6 通过：
- ✅ 无重复类定义
- ✅ 无重复函数定义
- ✅ 无大段重复导入
- ✅ 所有子模块 import 完整
- ✅ 无循环引用风险
- ✅ 骨架完整（组合模式）

### 测试修复

1. 骨架文件添加 `Optional`/`json`/`time`/`uuid` 导入（MemorySystem.__init__ 需要）
2. 添加 `__all__` 重导出保持向后兼容
3. `test_memory.py` 和 `test_memory_deep.py` 夹具补充子模块文件复制

### 审计脚本增强

`post_split_audit.py` 原本只检测 Mixin 继承模式。本次新增**组合模式检测**：
- 如果继承链为空 → 检查 `__init__` 中是否实例化了子模块类
- 识别并正确标记组合模式，不再误报

## 教训总结

| # | 陷阱 | 解决方案 |
|:--|:---|:---|
| 6 | 模块级语句误收 | `_helpers.py` 独立文件 |
| 7 | 向后兼容导入断裂 | 骨架 `__all__` 重导出 |
| 8 | 测试夹具未同步 | 搜索所有 `shutil.copy` 并补充子模块 |
