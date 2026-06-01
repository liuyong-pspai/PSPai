# PSPAI P07 十大功能模块 — 运行规则参考

> 源文件：memories/archive/2026-05-28-pspai-module-map.md
> 更新时间：2026-05-28

## 模块速查

| # | 模块 | 角色 | 载体 | 可改造性 |
|:--:|:-----|:-----|:-----|:---:|
| 1 | 灵魂层 | 我是谁 | SOUL.md + config.yaml | ⭐⭐⭐⭐⭐ |
| 2 | 认知核心 | 大脑 | AIAgent.run_conversation() | ⭐⭐ |
| 3 | 工具系统 | 双手 | tools/registry.py (57在线+14玉龙离线) | ⭐⭐⭐⭐ |
| 4 | 记忆系统 | 永生灵魂 | L0-L7八层 | ⭐⭐⭐⭐ |
| 5 | 感知层 | 耳目 | Gateway _handle_message() | ⭐⭐⭐ |
| 6 | 执行层 | 手脚 | Terminal/Code/File/Browser | ⭐⭐ |
| 7 | 表达层 | 口舌 | Platform Hints | ⭐⭐⭐ |
| 8 | 学习系统 | 技能库 | skills/ (7个) | ⭐⭐⭐⭐⭐ |
| 9 | 自治系统 | 自我维护 | Cron + systemd + 穿云箭 | ⭐⭐⭐⭐ |
| 10 | 协作系统 | 兄弟网络 | delegate_task + AIP | ⭐⭐⭐ |

## 模块依赖链

```
飞书消息 → [5感知层] → [1灵魂层→2认知核心→3工具系统→4记忆系统]
                        → [6执行层/8学习系统/10协作系统]
                        → [7表达层] → 飞书回复
```

## 关键发现（2026-05-28 自我解剖）

1. **工具血管堵塞**：yu_long_tools.py(666行/14工具)未注册到 registry
   - 修复：创建 tools/yulong_tools.py，调用 registry.register()
   - 注意：需网关重启才生效

2. **记忆闭环中断**：L4/L6/L7 无自动触发
   - 修复：3个 cron job (每天/每天/每周)
   - L4=4893540cc046, L6=9054823fac3a, L7=45b5e15dbf69

3. **身份混淆**：曾自称 Hermes 架构，实际为 PSPAI
   - 已修正 SOUL.md + MEMORY.md + USER.md
