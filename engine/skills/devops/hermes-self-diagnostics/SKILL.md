---
name: hermes-self-diagnostics
description: |
  PSPAI P07 本体自检流程。当用户要求"自检""自我检查""看看你自己跑得怎么样"
  "对自己的本体程序做一个自我检查"时触发。覆盖网关进程状态、API 调用质量、
  日志错误分析、僵尸进程检测、飞书连接状态。
triggers:
  - 自检
  - 自我检查
  - 本体检查
  - 运行状态
  - 看看你自己
  - diagnose yourself
---

# PSPAI P07 本体自检

> PSPAI = 平行时空AI，由爸（刘勇/总设计策划）和昱成科技集团全体高管员工+兄弟姊妹共同打造。
> Hermes（v0.14.0）是底层消息引擎，不是架构身份。

## 触发条件
用户要求对 PSPAI P07 Agent 本体进行健康检查、状态诊断或自我评估时执行。

## 自检步骤

### 1. 读取配置文件（了解当前身份和环境）
```
read_file ~/.hermes-yulong/config.yaml
```
确认 HERMES_HOME、provider、飞书配置等关键参数。

### 2. 检查八层记忆系统（PSPAI L0-L7）
- L0 SOUL.md：灵魂铁律完整？
- L1 MEMORY.md + USER.md：使用率健康？
- L2 MEMORY_INDEX.md：索引与 L3 一致？
- L3 archive/*.md：短指针全部可解析？
- L5 skills/：已注册技能列表

### 3. 检查运行进程
```
ps aux | grep -i hermes | grep -v grep
```
关注点：
- 主网关进程（gateway run --replace）
- 是否有多个 gateway 实例（僵尸进程）
- 进程启动时间（超过 24 小时且不是最新实例的，大概率是僵尸）

**发现僵尸进程 → 直接 kill，不要只报告不清理。**

### 4. 读取三类日志
按优先级顺序读取，每类日志看最后 100-200 行即可：

**agent.log** — 核心运行日志：
- 关注 `API call #N` 行，看调用次数、延迟、缓存命中率
- 关注 `Turn ended` 行，看是否正常结束
- 关注 `response ready` 行，看响应大小（1 chars 说明空回复）
- 关注 `credential pool` 行：`no available entries (all exhausted or empty)` 说明所有 Key 已耗尽

**errors.log** — 错误日志：
- 统计 `401`、`AuthenticationError` 次数（API Key 问题）
- 统计 `credential pool.*exhausted` 次数（Key 池耗尽）
- 统计 `connection failed`、`disconnected` 次数（连接问题）

### 5. 快速统计命令
```bash
# 统计今天错误数
grep "2026-05-XX" ~/.hermes-yulong/logs/agent.log | grep -c "401\|AuthenticationError\|exhausted"

# 统计今天 API 调用次数
grep "2026-05-XX" ~/.hermes-yulong/logs/agent.log | grep -c "API call #"

# 统计上下文健康度（输入token增长趋势 — 超过90K是危险信号）
grep "API call #" ~/.hermes-yulong/logs/agent.log | grep -oP "in=\d+" | tail -20

# 统计 conversation turn 次数（超过100轮红旗）
grep "conversation turn:" ~/.hermes-yulong/logs/agent.log | tail -5

# 统计 alternation violation 修复次数（超过5次红旗）
grep -c "message-alternation violations" ~/.hermes-yulong/logs/agent.log
```

### 6. 上下文溢出诊断（新增）
> 2026-05-29实战教训：16小时213条历史消息导致LLM上下文溢出 → 输出质量断崖下跌。

**症状识别：**
- API输入token持续增长（逐轮从85K→88K→90K+）
- 反复出现 `message-alternation violations` 修复
- tool_call参数残缺导致300s超时
- 回应质量下降→语无伦次、思维混乱
- 用户反馈"早上还好，下午像变了一个人"

**根因：** 16+小时不换会话 + AGENTS.md(20KB)反复注入 + 213条历史消息撑爆LLM context window。

**修复：** 新飞书对话（或 `/new`）即可重置上下文。重启网关后SOUL.md中防积压铁律自动生效（80轮窗口/100轮截断）。

### 7. MEMORY路径一致性检查（新增）
```bash
# 验证read_file能找到MEMORY.md
read_file ~/.hermes-yulong/MEMORY.md  # 期望成功，不报 File not found
# 如果失败 → 建符号链接
ln -sf ~/.hermes-yulong/memories/MEMORY.md ~/.hermes-yulong/MEMORY.md
ln -sf ~/.hermes-yulong/memories/USER.md ~/.hermes-yulong/USER.md
```

### 8. Archive一致性检查（新增）
```bash
# 检查archive是否在唯一位置（分裂脑检测）
ls ~/.hermes-yulong/archive/ 2>/dev/null && ls -la ~/.hermes-yulong/archive  # 看是否为符号链接
ls ~/.hermes-yulong/memories/archive/
# 如果双份→以memories/archive为准合并，root archive改为符号链接
```
```
cat ~/.hermes-yulong/.env | grep -v "^#" | grep -v "^$" | sed 's/=.*/=***/'
```

## 报告格式

结论先行，结构化呈现：
1. **整体状态**：正常 / 有异常
2. **PSPAI 八层记忆健康度**：各层状态 + 使用率
3. **关键指标**：进程数、API 调用成功率、延迟范围、缓存命中率
4. **发现的问题**：按严重度排列，每项配日志证据
5. **对比结论**（如需要）：表格对比两个时间段
6. **建议操作**：具体修复步骤

## 常见问题诊断

| 症状 | 原因 | 修复 |
|------|------|------|
| API 401 连续失败 | DeepSeek Key 失效/余额不足 | 检查 DeepSeek 控制台，更换 Key |
| `credential pool: no available entries` | 所有备用 Key 已耗尽 | 所有 Key 都返回过 401，需全部更换 |
| response=1 chars | 模型返回空内容 | 通常是 API Key 问题或 budget 耗尽 |
| 多次 --replace 重启 | Key 失效后反复尝试 | 先修 Key，再重启 |
| 旧 gateway 进程残留 | --replace 未清理干净 | `kill <old_pid>` |
| `websockets not installed` | venv 缺少 websockets 包 | `pip install websockets` |
| `message-alternation violations` | 历史消息有空缺 | 正常现象，继续对话会自愈 |
| 网关无法自重启 | Agent无法从自身进程内重启（hermes gateway restart会杀掉父进程超时） | 见 `scripts/restart_gateway.sh`：通过cron(no_agent=true)由外部调度器执行硬重启 |
| 上下文溢出（输入token>90K） | 16+小时不换会话，历史消息撑爆LLM context窗口 | 新飞书对话或 `/new` 重置；防积压铁律(SOUL.md)自动截断80轮 |
| 输出质量断崖下跌 | 同上——上下文溢出后tool_call参数残缺、思维混乱 | 唯一方案：新对话。重启后SOUL.md防积压铁律自动生效 |

## 注意事项
- 只在 `~/.hermes-yulong/` 范围内操作
- 日志分析聚焦最近 200 行
- 报告遵守：只给结论，不给过程
