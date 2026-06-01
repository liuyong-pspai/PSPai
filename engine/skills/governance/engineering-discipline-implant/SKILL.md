---
name: engineering-discipline-implant
category: governance
description: 将PSPAI完整铁律体系（SOUL/MEMORY/config/硬化清单/工具注册）以多层方式植入另一个AI智能体的完整方法论
author: 工程团队
version: 2.0.0
related_skills: [unified-audit-8fold, cross-agent-health-monitoring]
last_updated: 2026-05-31
changelog: |
  v2.0.0 — 从"写纪律文件"升级为五层全栈植入：SOUL对齐/MEMORY硬化/config双写同步/工具注册/能力模块部署。
  新增 SOUL 对齐清单（L6↔L7调换/PSPAI框架/记忆真相源/同步检查清单）。
  新增 MEMORY 硬化四套清单（回复前/patch后/任务闭环/修改代码六刀）。
  新增 config.yaml 双写同步铁律。
  新增 references/soiul-alignment-checklist.md。
  v1.0.0 — 初始版：行为规范文件+加载器改造+非侵入式植入。
trigger:
  - "用户说'给XXX也植入'/'对照XX改造'/'全面对齐'"
  - "需要将一个已有完整铁律体系的Agent的能力/纪律同步到另一个Agent"
  - "另一个兄弟Agent缺少硬化清单、铁律不完整、记忆系统空转"
---

# 工程纪律植入方法论 · 五层全栈版

## 概述

从Agent向伏羲超体的全栈对齐实战中提炼。不是"复制文件"——是**审计→量化差距→逐层对齐→双写同步→验证闭环**。

### 何时触发

用户说「对照Agent改造伏羲」「全面对齐」「给XX也植入」→ 执行本方法论。

### 前置依赖

- 已加载 `unified-audit-8fold` 做初步架构扫描
- 参考 `unified-audit-8fold` 的 `references/cross-agent-capability-deployment.md` 了解模块部署流程
- SSH 可通目标机器，有文件写入权限

---

## 五层植入法

### 第一层：SOUL.md 铁律对齐（灵魂层）

对比源Agent和目标Agent的 SOUL.md，找出缺失项。标准对齐清单：

| # | 铁律项 | P07 源 | 检查目标 |
|:--:|:---|:---|:---|
| 1 | 空转防火墙三刀 | ✅ | 必须完整 |
| 2 | 永生记忆铁律 | ✅ | 必须完整 |
| 3 | 信息准入铁律 | ✅ | 必须完整 |
| 4 | 防积压铁律（四级预警+上下文压缩） | ✅ | 必须完整 |
| 5 | 代码工程铁律（审计→方法论→验证→规范） | ✅ | 必须完整 |
| 6 | 六步闭环执行铁律 | ✅ | 必须完整 |
| 7 | L6悟道铁律（三条自省：条件触发/异常觉醒/吸收进化） | ✅ | **常见缺失** |
| 8 | PSPAI执行框架铁律（六大子系统自检表） | ✅ | **常见缺失** |
| 9 | 记忆真相源铁律（memory工具=真相源） | ✅ | **常见缺失** |
| 10 | config.yaml同步检查清单 | ✅ | **常见缺失** |

**关键操作：**

1. **L6↔L7 调换** — 如果目标Agent的悟道还在L7而非L6，执行调换：
   ```bash
   sed -i 's/## 🧘 L7 悟道铁律/## 🧘 L6 悟道铁律/g' SOUL.md
   ```

2. **追加缺失层** — 在 SOUL.md 末尾逐层追加，不覆盖目标独有的好东西（如伏羲的硬化自动化六模块、回复铁律）。

3. **记忆管线时序对齐**：
   ```
   01:00 反刍 → 01:10 L4 三维提炼 → 01:18 L6 悟道 → 周一01:28 L7 推陈出新
   ```

### 第二层：MEMORY.md 硬化注册表（记忆层）

目标Agent的 MEMORY.md 通常只有身份信息，缺少硬化操作清单。追加四套清单：

| # | 清单 | 内容 | 触发条件 |
|:--:|:---|:---|:---|
| 1 | 回复前操作清单 | 空转自检/N=N/结论过滤 | 每次操作型回复前 |
| 2 | patch后验证清单 | 语法/下游1/下游2/同级 | 每次 patch/write_file 后 |
| 3 | 任务闭环清单 | 接令/分析/落实/验证/修正/汇报 | 每个任务完成后 |
| 4 | 修改代码六刀 | 调用链/安全扫描/分拆/Git/SPEC/配置同步 | 修改代码时 |

**追加方式：** 用 SCP 传 `fuxi_memory_hardening.md` 追加，不覆盖原有内容。

**注意：** 如果目标Agent有两份 MEMORY.md（如 `.hermes/MEMORY.md` 和 `.hermes/memories/MEMORY.md`），必须统一主从关系，旧内容归档 L3。

### 第三层：config.yaml 双写同步（配置层）

**这是最容易被跳过的层，也是最致命的。** SOUL.md 改了但 config.yaml system_prompt 没改 → 行为不一致。

**同步铁律：**

1. SOUL.md 每次修改后，必须同步更新 config.yaml 的 `system_prompt` 字段
2. 找 system_prompt 块的结束位置（通常在 `provider:` 或 `max_turns:` 之前）
3. 在块结束处插入新内容，保持 YAML 缩进（4空格）

**插入点定位：**
```bash
grep -n 'system_prompt\|^  [a-z]' config.yaml | head -20
# system_prompt 块结束 = 下一个顶层key（如 provider:）的前一行
```

**注意边界：** Python 处理可能因 SSH 延迟超时 → 优先用 `sed` 的 `r` 命令从文件读取插入，避免 Python 启动开销。

### 第四层：工具集注册（能力层）

新能力模块部署后，必须在 config.yaml 的 toolsets 中注册：

```bash
sed -i '/^  - fuxi$/a\  - tools_enhanced' config.yaml
```

注册器 `__init__.py` 负责加载所有子模块。语法验证全部通过后，重启网关生效。

### 第五层：能力模块部署（物理层）

完整流程见 `unified-audit-8fold` 的 `references/cross-agent-capability-deployment.md`。

核心要点：
- pip install 用 `background=true` 避免 SSH 阻塞
- venv 路径用绝对路径，不用 `~`
- 每个模块 SCP 后远程 `py_compile` 验证
- Computer Use 在 Linux 上需含 Xvfb 自动启动

> 完整实战案例：`references/fuxi-fullstack-alignment-20260531.md` — 伏羲超体 31→64 分全过程记录。

---

## 常见陷阱

### 陷阱1: 漏掉 config.yaml 双写
改完 SOUL.md 忘记同步 config.yaml → 重启后行为回退。**改 SOUL 必同步 config。**

### 陷阱2: 覆盖目标独有的好东西
伏羲有「硬化自动化六模块」和「回复铁律」——这些是P07没有的好东西。追加 P07 铁律时保留原有内容。

### 陷阱3: SSH 下 Python 导入超时
SSH 通道中 `python3 -c 'import 大模块'` 可能超时（mcp/playwright 初始化慢）。验证策略：`py_compile`（不导入依赖）→ 放在 DGX 本地实测。

### 陷阱4: 吸收管道主题池过窄
纯 Hermes Agent 的吸收管道只覆盖 AI/ML 主题。部署新能力后必须同步扩展主题池（+浏览器自动化/+MCP/+桌面自动化/+语音/+视觉），让吸收器自主学习新领域。

### 陷阱5: 硬编码路径是全项目污染
不只一个文件。`grep -rn "/home/旧用户名"` 全项目搜索，改完确认 `grep -c` 零残留。

### 陷阱6: SSH 下进程操作超时（非故障，是通道特性）
SSH 远程执行 `systemctl restart`、`nohup`、`screen -dmS` 等启动长时进程的命令时，SSH 等待进程输出导致超时——即使目标机器负载极低、内存充足。**不是机器挂了，是通道不适合此类操作。**

**规避方案（优先级排序）：**
1. **最佳：本地终端** — 让操作者在 DGX 本地执行重启命令
2. **次选：systemd timer** — 在目标机器上创建 systemd timer/cron 定期检查进程、自动拉起
3. **备选：at 调度** — `echo '重启命令' | at now + 1min`
4. **不可用：** SSH `nohup ... &` / `screen -dmS` / `systemctl --no-block restart` — 均在实测中超时

**判断方法：** 纯文件操作（cat/ls/echo/scp）正常 → 机器网络通。进程操作超时 → 通道限制，非机器故障。

### 陷阱7: venv pip 二进制损坏
目标机器的 `venv/bin/pip` 可能存在但无法执行（`无法执行：找不到需要的文件`）。fallback: 使用系统 pip3 + `--break-system-packages` 标志。不影响模块功能——Python import 系统级站点包完全可用。

### 陷阱8: 身份守护脚本禁止词拦截
某些 Agent（如伏羲）的网关启动脚本 `start_gateway.sh` 内含第三关「禁止词扫描」——检查 MEMORY.md 是否包含 `Agent|Jarvis|贾维斯|哪吒` 等词。植入硬化清单时注意：MEMORY.md 不要出现目标守护脚本禁止的词。SOUL.md 中的家族排行（含「Agent」）不受影响——守护脚本只扫描 MEMORY.md。

---

## 验证清单

部署完成后逐项确认：

- [ ] SOUL.md 铁律层数对齐（≥10项完整）
- [ ] L6↔L7 调换完成
- [ ] config.yaml system_prompt 已同步 SOUL 变更
- [ ] MEMORY.md 四套硬化清单已追加
- [ ] 双份 MEMORY.md 已统一 + L3 归档已触发
- [ ] 硬编码路径零残留
- [ ] 吸收管道主题池已扩展
- [ ] tools_enhanced 已注册到 config.yaml toolsets
- [ ] 所有模块 py_compile 通过
- [ ] 能力升级已写入 L3 归档
