# 发布包深度审计清单

> 源自 v1.2.7 小龙人三平台审计实战（2026-06-03）
> 上架前必过，一项不过 = 禁止发布

## 九维审计表

### 维度1：身份完整性 🔴

| 检查项 | 验证方法 | 常见事故 |
|:--|:--|:--|
| SOUL内容嵌入引擎 | 检查引擎二进制或源码中是否包含完整身份定义（姓名/家族/铁律） | 仅 `'You are PSPAI.'` 一句话，无身份 |
| 中英文双语言身份 | system_prompt_zh / system_prompt_en 都有 | 用户切英文后变成空壳 |
| 铁律实际生效 | 引擎启动后实际执行铁律（工具调用/记忆不删/六步闭环） | 铁律写了但 `skip_memory=True` 使记忆铁律形同虚设 |

### 维度2：记忆系统 🔴

| 检查项 | 验证方法 | 常见事故 |
|:--|:--|:--|
| skip_memory | 搜索源码中 `skip_memory`，必须为 `False` | `skip_memory=True` — 用户每次对话从零开始 |
| 会话持久化 | 发一条消息→重启引擎→再发一条→检查是否记得上一条 | 会话在内存中不写盘 |
| 数据目录 | 引擎的 `data/` 目录是否创建、写入正常 | 权限问题导致写盘失败 |

### 维度3：配置链 🟡

| 检查项 | 验证方法 | 常见事故 |
|:--|:--|:--|
| launcher→引擎配置同步 | launcher生成的配置能否被引擎正确读取 | launcher写 `.env`，引擎读 `config.yaml`，两套体系不互通 |
| 模型从配置读取 | 修改 config.yaml 的 model 字段后重启，确认新模型生效 | `model='deepseek-chat'` 硬编码 |
| API Key通路 | 用户在浏览器配置→launcher保存→引擎读取→实际API调用成功 | Key写了但引擎读不到（环境变量名不匹配） |

### 维度4：前端容错 🔴

| 检查项 | 最低标准 |
|:--|:--|
| 重试机制 | fetch失败后至少重试2次（指数退避） |
| 加载状态 | 发送消息后显示加载指示器（spinner/骨架屏/...） |
| 连接检测 | 每15-30秒ping `/api/status`，顶部显示连接状态 |
| 错误提示 | 引擎不可达时显示用户可读的错误消息（非技术堆栈） |
| 引擎重启恢复 | 引擎重启后前端自动重连，不需要用户刷新 |

### 维度5：启动器健壮性 🟡

| 检查项 | 最低标准 |
|:--|:--|
| 引擎自动重启 | 引擎异常退出后自动重启（最多3次） |
| 端口冲突处理 | 端口被占用时给出提示或自动换端口 |
| 配置向导超时 | 用户5分钟不操作配置页面，给出超时提示 |
| 缺失组件提示 | 引擎/前端/Python缺失时给出安装指引 |

### 维度6：移动端连通性 🟡

| 检查项 | 验证方法 |
|:--|:--|
| 与引擎API一致 | mobile.html 调用同一套 REST API（`/api/chat`），不走独立WebSocket |
| 语音输入可用 | Web Speech API STT → 文本 → `/api/chat` |
| 语音输出可用 | 引擎回复 → Web Speech API TTS |
| 文字输入回退 | 语音不可用时（桌面浏览器）提供文字输入替代 |

### 维度7：安装依赖 🟡

| 检查项 | 最低标准 |
|:--|:--|
| Python3检查 | 启动脚本运行前检查Python3是否可用，不可用时给出安装指引 |
| pip依赖 | 自动安装必需依赖（PyYAML等），安装失败有提示 |
| 平台适配 | macOS/Linux/Windows各自的原生路径和命令 |

### 维度8：跨平台一致性 🟢

| 检查项 | 验证方法 |
|:--|:--|
| 三平台安装包产出 | Linux .run + macOS .dmg + Windows .zip 都存在 |
| 安装包大小合理 | < 30MB（不含嵌入式Python时 < 10MB） |
| 引擎二进制命名一致 | 三平台引擎二进制文件名统一可发现 |

### 维度9：版本标记 🟢

| 检查项 | 验证方法 |
|:--|:--|
| 引擎版本号 | `/api/status` 返回正确的 version |
| 身份标识 | `/api/status` 返回 identity 字段 |
| 记忆状态 | `/api/status` 返回 `memory: "enabled"` |

## 实战案例：v1.2.7 审计发现

### 发现的P0问题（已修复）

| 问题 | 根因 | 修复 |
|:--|:--|:--|
| 记忆被关闭 | `skip_memory=True` | → `False` |
| 身份缺失 | `DEFAULT_PROMPT='You are PSPAI.'` | → 嵌入完整SOUL |
| 配置链断裂 | launcher写`.env`，引擎读`config.yaml` | → 双写同步 |
| 前端零错误处理 | 无重试/加载/连接检测 | → 3次重试+动画+🟢/🔴 |
| 引擎无自愈 | 退出后无重启 | → 最多3次自动重启 |
| mobile空壳 | WebSocket连错端口 | → 直连REST API |
| macOS无Python检查 | 启动脚本假设python3存在 | → 检测+弹窗提示 |
| Linux无依赖检查 | .run不检查python3 | → 安装指引 |

## 审计执行模板

```bash
# 1. 下载三平台安装包
curl -sLO <release-url>/xiaolongren-setup.zip
curl -sLO <release-url>/xiaolongren-installer.dmg
curl -sLO <release-url>/xiaolongren-installer.run

# 2. 解压检查内容
unzip -l xiaolongren-setup.zip

# 3. 检查引擎二进制
strings xiaolongren-engine.exe | grep -c 'skip_memory\|SOUL\|刘玉龙'

# 4. 检查前端
grep -c 'fetch.*api/chat' index.html
grep -c 'catch\|retry\|loading' index.html

# 5. 检查启动器
grep -c 'restart\|poll\|自动' launcher.py
```
