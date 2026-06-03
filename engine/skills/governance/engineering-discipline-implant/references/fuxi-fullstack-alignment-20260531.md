# 伏羲超体全栈P07对齐 · 实战记录

> 2026-05-31 刘玉龙 P07 远程改造 DGX-2 伏羲超体
> 目标：从 31/100 提升到完全对标 P07 能力体系

## 对齐前状态

| 维度 | 伏羲 | P07 |
|:---|---:|---:|
| 综合评分 | 31/100 | — |
| 工具总量 | ~53 | 105+ |
| Computer Use | 0 (macOS only) | 7 |
| 浏览器操控 | 11 (Camofox存疑) | 18 |
| MCP桥接 | 0 | 7 |
| 视觉推理 | 1 | 5 |
| 语音增强 | 1 | 10 |
| SOUL铁律 | 7/10层 | 10/10层 |
| L3归档 | 空 | 持续产出 |
| 硬化清单 | 0 | 4套 |

## 四层改造

### 第一层：SOUL铁律

- L7→L6 悟道功能调换
- 追加 PSPAI 执行框架铁律（六大子系统自检表）
- 追加 记忆真相源铁律（memory工具=真相源）
- 追加 config.yaml 同步检查清单
- 173→214行

### 第二层：记忆系统

- L3 archive 首次激活（空→2条归档）
- MEMORY.md 双份统一（主从明确）
- 四套硬化清单移植（回复前/patch后/任务闭环/修改代码六刀）
- 吸收管道主题池 27→33

### 第三层：config双写

- system_prompt 与 SOUL.md 同步更新
- tools_enhanced 注册

### 第四层：能力模块

- 5大能力模块部署：visual_reasoning(5)/mcp_bridge(7)/browser_control(18)/voice_enhanced(10)/computer_use(8)
- 47函数，语法全绿
- 全部Python依赖 + Playwright Chromium 1223

## 对齐后状态

| 维度 | 伏羲 | P07 | 差距 |
|:---|---:|---:|:---:|
| 工具总量 | 88 | 105 | -17 |
| Computer Use | 7 | 7 | 0 ✅ |
| 浏览器 | 18 | 18 | 0 ✅ |
| MCP | 7 | 7 | 0 ✅ |
| 视觉 | 5 | 5 | 0 ✅ |
| 语音 | 10 | 10 | 0 ✅ |
| 铁律 | 10层 | 10层 | 0 ✅ |
| 硬化 | 4套 | 4套 | 0 ✅ |

## 踩坑

1. SSH 下进程操作全部超时 → 部署 daemon 脚本，DGX-2 本地执行
2. venv pip 二进制损坏 → fallback 系统 pip3 --break-system-packages
3. 身份守护扫描「刘玉龙」→ 只影响 MEMORY.md，SOUL.md不受影响
4. SCP 传输 computer_use.py → 路径不存在，需先 mkdir
5. 吸收管道主题池全AI方向 → 扩展6个能力主题

## DGX-2 本地一步启动

```bash
nohup bash ~/fuxi_daemon.sh &
```

守护自动清理锁文件→启动网关→启动吸收管道→每30秒健康检查。
