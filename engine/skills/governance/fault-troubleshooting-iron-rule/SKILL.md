---
name: fault-troubleshooting-iron-rule
category: governance
description: 故障排查铁律——先确认底层链路再深入业务逻辑。从底层往上查：进程→网络→日志→代码逻辑→业务层，不准跳级。
version: 1.0.0
author: 刘昱欣
---

# 故障排查铁律

## 触发条件
当遇到任何系统级异常（崩溃、无法启动、API错误、消息不通）时，**先按此流程执行**，不要立即改业务代码。

## 核心原则

1. **从底层往上查**：进程→网络→日志→代码逻辑→业务层，不准跳级
2. **一证据一结论**：每条结论必须有日志行或命令输出支撑，不靠"我记得"
3. **改前备份，改后验证**

## 排查步骤

### 第0步：排查共享凭据导致的交叉干扰
如果进程被 SIGTERM 意外杀死、或出现消息串线、重复回复：检查飞书 Bot 是否独用。常见症状：Agent莫名被SIGTERM杀死、收到不属于自己的消息、回复重复内容。

### 第1步：确认"跑的是哪个版本"
```bash
ps aux | grep python3           # 找 PID
ls -la /proc/PID/cwd            # 工作目录
ls -la /proc/PID/fd/            # 打开的文件/日志
```
**常见陷阱**：日志行号与当前文件行号不一致 → 你修的文件和跑的文件不是同一个

### 第2步：确认底层链路
- 语法错误：`python3 -c "import ast; ast.parse(open('file.py').read())"`
- 导入错误：`python3 -c "from package import module"`
- API 连通性：`curl -s -o /dev/null -w '%{http_code}' https://api.example.com`

### 第3步：确认变量定义
```bash
grep -n '裸变量名' file.py
python3 -c "compile(open('file.py').read(), 'file.py', 'exec')"
```

### 第4步：隔离测试
核心链路隔离测试，构造mock逐个测试子方法

### 第5步：日志驱动排查
```bash
ls -lt /proc/PID/fd/  # 看输出写到了哪里
tail -f /proc/PID/fd/1  # 直接 tail stdout
```

### 第6步：Web前端404排查（页面白屏/加载失败）
当「服务在跑、端口监听、主页面200，但浏览器白屏或不正常」时——**静态资源路由缺失**是第一嫌疑：

```bash
# 1) 确认主页面可访问
curl -s --max-time 3 -o /dev/null -w "%{http_code} size:%{size_download}" http://IP:PORT/

# 2) 找出HTML引用的所有外部资源（CSS/JS/字体/图片）
grep -oP '(href|src)=["\x27](/[^"'\x27]+)' 页面.html | sort -u

# 3) 对照服务端路由——找出哪些路径没有被处理
# 在服务端代码中搜索静态文件路由（通常是路径前缀白名单）
grep -n 'path.startswith\|path in \[' serve_ui.py

# 4) 逐一验证每个资源路径返回200
curl -s --max-time 3 -o /dev/null -w "%{http_code} %{url}\n" http://IP:PORT/css/style.css
```

**典型陷阱**：新增了 `/themes/`、`/fonts/`、`/assets/images/` 等目录放CSS/JS，但服务端只路由了 `/css/`、`/js/`——浏览器请求新目录全部404，页面白屏。

**修复**：在服务端静态文件路由中加入新路径前缀，重启验证。

### 第7步：消息链路分层追查
当"进程活着但不回复消息"时：
```bash
# 1) 进程活着？
systemctl --user status <service> --no-pager | head -5
# 2) WS收到消息？
journalctl --user -u <service> -n 100 --no-pager | grep "飞书.*收到"
# 3) 被去重吞了？
journalctl --user -u <service> -n 100 --no-pager | grep "跳过重复"
# 4) 认知引擎处理了？
journalctl --user -u <service> -n 200 --no-pager | grep -E "推理轮次|回复成功|消息处理"
```
