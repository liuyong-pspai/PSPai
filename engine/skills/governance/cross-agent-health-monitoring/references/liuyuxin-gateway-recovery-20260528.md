# 刘昱欣网关恢复实录 (2026-05-28)

## 诊断过程

### 1. 进程检查
```bash
ps aux | grep -E 'hermes|gateway' | grep -v grep
```
结果：只有刘玉龙的gateway在跑（PID 1598023），刘昱欣的gateway不在。

### 2. HERMES_HOME检查
```bash
ls -d /home/yongliu/.hermes*
```
结果：
- /home/yongliu/.hermes
- /home/yongliu/.hermes-web-ui
- /home/yongliu/.hermes-yulong  ← 刘玉龙
- /home/yongliu/.hermes-yuxin   ← 刘昱欣（配置完好）

### 3. venv检查
```bash
ls /home/yongliu/hermes-agent-isolated/venv/bin/python*
```
结果：目录为空 — venv已被删除。

### 4. 日志分析
```bash
tail -30 ~/.hermes-yuxin/logs/agent.log
```
结果：最后一条日志 2026-05-20 07:36:34，已宕机8天。

```bash
tail -50 ~/.hermes-yuxin/logs/errors.log
```
根因：
```
ERROR: websockets not installed; websocket mode unavailable
```
以及多次 "Old gateway did not exit after SIGTERM, sending SIGKILL"。

### 5. 配置验证
.env 完整：DEEPSEEK_API_KEY、FEISHU_APP_ID、FEISHU_APP_SECRET 都在。
config.yaml 完整：agent.system_prompt 指向 ~/.hermes-yuxin/SOUL.md。

## 恢复动作

```bash
cd /home/yongliu && \
HERMES_HOME=/home/yongliu/.hermes-yuxin \
/home/yongliu/hermes-agent/venv/bin/hermes gateway run --replace &
```

## 恢复后验证

```
✓ feishu connected (websocket mode)
✓ Gateway running with 1 platform(s)
✓ Channel directory built: 2 target(s)
✓ 7 cron jobs fast-forwarded to next run
✓ kanban dispatcher enabled
```

进程确认：
```
yongliu  1598023  ... hermes gateway run --replace  ← 刘玉龙
yongliu  1600334  ... hermes gateway run --replace  ← 刘昱欣（已恢复）
```

## Cron Jobs 恢复列表
- 开创纪元档案巡检
- 每日8885聊天记录备份
- 每日飞书聊天记录备份
- 四妹记忆系统每日完整性校验
- 四妹·每日03:28知识库学习
- 记忆系统健康检查
- 四妹飞书Gateway保活
