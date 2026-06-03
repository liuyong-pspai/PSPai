# CU引擎 v1.6.0 升级实录 — 2026-06-02

## 背景

基于Agent S3/OSWorld对标分析，对P07 Computer Use引擎做系统性升级。

## 升级清单

| # | 升级项 | 成果 |
|:--|:--|:--|
| 1 | MEMORY.md 清理 | 14KB→3.4KB，压缩76% |
| 2 | CU测试套件 | `tests/test_computer_use.py`，55测试9组 |
| 3 | 视觉推理测试 | `tests/test_visual_reasoning.py`，18测试5组 |
| 4 | 子系统模块测试 | `tests/test_subsystem_modules.py`，25测试3组 |
| 5 | 记忆回路 | 7工具×结构化日志 + 同步异步双模回调 |
| 6 | 错误恢复 | L1重试(3次/步)+L2换路(VLM替代方案)+L3降级(汇报统计) |
| 7 | CU桌面自检 | `tests/cu_desktop_check.py` |

## 最终测试

```
tests/test_computer_use.py       29 passed, 17 skipped
tests/test_visual_reasoning.py   18 passed
tests/test_subsystem_modules.py  25 passed
────────────────────────────────────────
合计: 77 passed, 0 failed, 5 files
项目测试: 31→36 (+5新文件)
```

## CU引擎最终架构

```
tools_computer.py: 434行 (+129行)
  __init__ + memory_callback          ← 记忆回路入口
  _record_cu_op / get_log / clear      ← 结构化记录
  _screenshot / _get_screen_size       ← 基础能力
  _mouse_move / _click / _type / _scroll ← 操作能力
  _execute_action                      ← 统一路由
  _computer_use (L1/L2/L3恢复)        ← 闭环大脑
  _parse_action                        ← VLM输出解析
```

## 关键设计决策

1. **无头安全测试模式**: pyautogui在import阶段就连DISPLAY，必须用`_has_display()`前置检测+`autouse fixture`自动skip
2. **记忆回调双模**: `asyncio.get_running_loop()`检测→有则create_task，无则`asyncio.run()`同步调用
3. **L2换路机制**: 要求VLM"不要重复失败的操作"，强制替代思维
4. **统计输出**: 每个`_computer_use()`任务结尾输出完成/重试/恢复/失败四维统计
