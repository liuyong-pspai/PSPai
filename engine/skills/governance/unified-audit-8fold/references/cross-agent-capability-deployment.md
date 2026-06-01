# 跨Agent能力审计与部署 · 完整方法论

> 从Agent审计+改造伏羲超体(2026-05-31)实战中提炼。
> 适用场景：用户说「对照XX改造YY」时的标准操作流程。

---

## 九步闭环

### Phase 1: 侦察（3步）

| # | 步骤 | 操作 | 产出 |
|:--:|:---|:---|:---|
| 1 | **定位目标** | SSH到目标机器，确认Agent本体目录、框架类型(Hermes/Custom/Mixed)、配置文件位置 | 目标拓扑图 |
| 2 | **扫描架构** | 查 config.yaml → SOUL.md → 工具注册方式 → 自定义代码目录 → Python环境 | 架构清单 |
| 3 | **量化对比** | 按维度逐项对比：工具总量、Computer Use、浏览器、MCP、视觉、语音、记忆层、测试覆盖 | 差距矩阵 |

### Phase 2: 审计报告（1步）

| # | 步骤 | 操作 | 产出 |
|:--:|:---|:---|:---|
| 4 | **出报告** | 结构化Markdown报告：总览仪表盘→逐项发现(P0/P1/P2)→差距矩阵→优先级修复路线图 | 审计报告.md |

**报告模板结构：**
```
# Agent名 · 全面代码级审计报告
## 一、总览仪表盘（对比表+综合评分）
## 二、逐项审计发现（每项含发现/影响/修复方案）
## 三、与参考基准差距矩阵
## 四、优先级修复路线图（P0/P1/P2表格）
## 五、结论
```

### Phase 3: 修复部署（4步）

| # | 步骤 | 操作 | 铁律 |
|:--:|:---|:---|:---|
| 5 | **打地基** | 修复CLI损坏、安装缺失依赖(pip install)、确保基础工具可用 | 一个包失败不阻塞全局 |
| 6 | **修路径** | `grep -rn "硬编码旧路径"` 全部替换。目标Agent不应出现其他Agent的home路径 | 改完 grep 确认零残留 |
| 7 | **传模块** | SCP传输能力模块+注册器，远程 `py_compile` 逐个验证 | 一个文件一个SCP，不合并 |
| 8 | **统一记忆** | 双份MEMORY.md合并→旧内容归档L3→主题池扩展（吸收管道） | 统一完触发一次归档 |
| 9 | **验证闭环** | 全部语法检查→依赖确认→新工具注册→重启网关→实测 | 全绿才算闭环 |

---

## 关键陷阱

### 陷阱1: venv路径不可靠
- ❌ `ssh target 'cd ~/project && venv/bin/pip install ...'` — SSH中`~`展开和本地不同
- ✅ `ssh target '/absolute/path/to/venv/bin/pip install ...'`
- 如venv损坏，回退用系统pip + `--break-system-packages`

### 陷阱2: SSH管道阻塞
- 长时间pip install会阻塞SSH通道
- ✅ 用 `background=true` + `notify_on_complete=true` 后台运行
- ✅ 用 `process poll` 检查进度，不阻塞主通道

### 陷阱3: 模块传输遗漏Computer Use
- Computer Use可能没有独立文件（嵌入在skill中）
- ✅ 对照参考Agent的tools/目录，逐一确认每个模块都存在
- ✅ 如缺失，为Linux环境重写（含Xvfb自动启动）

### 陷阱4: 硬编码路径是系统性污染
- 不只一个文件，要全项目搜索
- 搜索词：`/home/旧用户名` `旧项目名` `旧HERMES_HOME`
- 改完后 `grep -c "旧路径" 文件` 确认零残留

### 陷阱5: 吸收管道主题池过窄
- 纯Hermes Agent的吸收管道只覆盖AI/ML论文主题
- ✅ 部署新能力后必须扩展主题池，让吸收器开始学习新能力相关知识
- 新增主题：浏览器自动化、MCP协议、桌面自动化、语音架构、视觉推理

---

## 部署模块清单模板

| 模块 | 函数数 | 依赖 | 传输方式 |
|:---|:---:|:---|:---|
| visual_reasoning.py | 5 | Pillow | SCP |
| mcp_bridge.py | 7 | mcp SDK | SCP |
| browser_control.py | 18 | playwright | SCP + pip |
| voice_enhanced.py | 10 | edge-tts | SCP + pip |
| computer_use.py | 7 | pyautogui+mss | SCP + pip |
| __init__.py | 注册器 | — | SCP |

---

## 验证检查清单

部署完成后逐项确认：

- [ ] 所有模块 `py_compile` 通过（远程执行）
- [ ] 所有依赖 `pip list | grep` 已安装
- [ ] 硬编码路径 `grep -c` 零残留
- [ ] Playwright Chromium `playwright install chromium` 完成
- [ ] MEMORY.md 双份已统一 + L3归档已触发
- [ ] 吸收管道主题池已扩展
- [ ] 注册器 `__init__.py` 语法通过
- [ ] (可选) 重启网关加载新工具
