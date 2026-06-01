---
name: agent-full-body-audit
category: governance
description: 对AI Agent/机器人项目做全面静态审计，不启动运行，仅靠代码扫描发现低级错误
trigger: 用户反馈机器人行为异常（如返回错误、不能执行基础功能），或要求全面检查
---

# Agent 全面静态审计

## 适用场景
- AI Agent 行为异常（"连时间都查不了"）
- 反复修同一个问题但找不到根因
- 需要从头到尾检查一个系统的完整性

## 第一步：别猜，先扫

不要凭经验猜问题在哪。按固定模板扫：

### 1. 基础环境
```bash
ls -la main.py kernel.py config.py .env .env.* 2>/dev/null
ps aux | grep python | grep -v grep
ss -tlnp | grep <PORT>
```

### 2. 所有注册工具逐一检查
对每个工具函数检查：
- import 是否完整
- 函数体内引用的每个名称是否有对应的 import 或定义
- 异步函数是否有 await
- try/except 是否吃了不该吃的错误

### 3. 思维链检查（perceive → decide → execute）
- 连接状态感知是否在技能匹配之前？
- 字段是否在匹配前填充？

### 4. 动力链检查（消息入口 → 处理 → 回复）
入口 → 队列 → 消费 → 处理 → 回复。每步确认活着。

### 5. 序列化检查
任何存到 memory/日志/文件的字典先做 json.dumps 测试

### 6. 错误掩盖检查
找所有 try/except 块，检查 except: pass 有没有吃掉了本应上报的错误

## 第二步：按优先级修

P0 - 启动crash | P1 - 基础功能失效 | P2 - 认知链不完整 | P3 - 非功能性

**铁律：P0 不解决，P1/P2 的修改无法验证**

## 常见低级错误清单

1. `time.time()` 没 `import time`
2. `await` 缺失 — coroutine 被当值存进 dict
3. 顺序错误 — 读消息队列在技能匹配之后
4. ACP 回复缺失
5. try/except 虚假成功
6. 记忆系统未实例化
7. L3记忆归档格式不兼容
8. 沙箱绕过
9. 合并版代码库重复定义
