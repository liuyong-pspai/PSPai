# 2026-05-30 八维全身审计修复完整日志

> 审计范围：Hermes 引擎 v0.14.0 + Agent 自有代码  
> 审计发现：159 项（P0=20, P1=43, P2=53, P3=43）  
> 抽样验证：7/7 属实（85.7% 估计属实率），2 项描述需修正  
> 修复完成：55 项，17 个文件

## 反馈（描述精度修正）

| P0# | 原描述 | 问题 | 修正 |
|:---:|--------|------|------|
| 4 | "write_file_tool 无路径穿越防护" | `_check_sensitive_path` 存在但只挡 `/etc/ /boot/` | 改"有防护但不全，缺 `..` 检查" |
| 12 | "self_check_gaps 负面报告" | 实际是永远全绿 | 改"正面假报告" |

**结论铁律：**
- 禁止绝对化否定——说"没有"前必须确认代码中完全不存在
- 描述方向不能反——假阳性≠假阴性
- 大规模审计提交前抽样核实 5-10 项

## 修复批次概览

### 批次 1-2：P0 安全+逻辑（11 项）
| 文件 | 修改 |
|------|------|
| `run_agent.py:857` | API Key `[:20]` → `[:8]...[-4:]` 掩码 |
| `run_agent.py:8034` | Token `[:12]` → `[:8]...[-4:]` 掩码 |
| `yu_long_tools.py:260` | self_check_gaps 从硬编码改为 TOOLS 注册表动态匹配 |
| `file_tools.py:573` | write_file_tool 加 `PurePath(path).parts` 检查 `..` |

### 批次 3-4：P0 安全+逻辑（7 项）
| 文件 | 修改 |
|------|------|
| `yu_long_tools.py:443` | ssh_exec `shell=True` → `shell=False + shlex.split` |
| `skills_tool.py:908` | 注入检测从"只记日志"→"直接阻止+返回 error" |
| `gateway/run.py:2213` | quick_commands `create_subprocess_shell` → `create_subprocess_exec + shlex.split` |
| `run_agent.py:2616` | 删除 `_hydrate_todo_store` 末尾误调用的 `_set_interrupt(False)` |
| `run_agent.py:2540` | `clear_interrupt()` 传播到所有子 Agent |
| `context_compressor.py:381` | `str(None)`→`""`，避免字面 "None" 污染摘要 |
| `context_compressor.py:553` | `.get("arguments","")` 在值为 None 时处理 |

### 批次 5-6：P0 数据+配置+P1 安全（6 项）
| 文件 | 修改 |
|------|------|
| `run_agent.py:7041` | Budget 加 `_budget_is_shared` 保护，共享时不重建 |
| `run_agent.py:8591` | `api_call_count` 加 `max(0, ...)` 防下溢 |
| `hermes_state.py:1287` | prune_sessions BFS 递归删除所有后代 |
| `hermes_state.py:252` | _init_schema 包裹显式事务 |
| `SOUL.md:72` | 压缩阈值 50%→80%（与表对齐） |
| `config.yaml:98` | max_turns 60→40（与 SOUL 红色截断对齐） |

### 批次 7-8：P1 高优安全+工具（5 项）
| 文件 | 修改 |
|------|------|
| `terminal_tool.py:1436` | 从 JSON 返回中移除 traceback，仅 logger.error |
| `delegate_tool.py:40` | DEFAULT_TOOLSETS `["terminal","file","web"]`→`["file","web"]` |
| `mcp_tool.py:1237` | MCP 参数加 100KB 上限+JSON 序列化校验 |
| `gateway/run.py:2906` | 回复引用文本加控制字符剥离 |
| `prompt_builder.py:481` | 技能描述 injection 扫描 |

### 批次 9-10：P2 竞态/TOCTOU/可靠性（8 项）
| 文件 | 修改 |
|------|------|
| `registry.py:166` | dispatch 异常只返类型名，不返完整消息 |
| `delegate_tool.py:327` | 子 Agent 注册始终用锁（创建不存在的锁） |
| `file_tools.py:359` | 读文件用 resolved 路径（消除 TOCTOU） |
| `model_tools.py:198` | `_last_resolved_tool_names` 标注并发竞态风险 |
| `cronjob_tools.py:169` | 脚本路径加符号链接逃逸检测 |
| `hermes_state.py:694` | sanitize_title 移入事务内 |
| `yu_long_tools.py:88` | sql_query 假值吞没修复 (`row[c] or ""`→`None` 检查) |
| `yu_long_tools.py:314` | tool_doctor 改用 inspect.signature 避免全线误报 |

### 批次 11-12：网关注入+提示构建防线（7 项）
| 文件 | 修改 |
|------|------|
| `gateway/run.py:2788` | sender name 去括号+控字符+截断 64 字符 |
| `gateway/run.py:2888` | 文件路径清洗控字符+截断 256 字符 |
| `gateway/run.py:6833` | 历史消息加载控字符剥离 |
| `prompt_builder.py:105` | `.hermes.md` 拒绝符号链接 |
| `prompt_builder.py:856` | SOUL.md `is_relative_to` 路径验证 |
| `prompt_builder.py:49-52` | Unicode 检测从 10 字符硬编码→`unicodedata.category()` 动态 |

### 批次 13-14：性能+完整性+代码质量（7 项）
| 文件 | 修改 |
|------|------|
| `model_tools.py:39` | 共享 ThreadPoolExecutor 替代每次创建销毁 |
| `gateway/run.py:220` | TERMINAL_CWD 默认 `Path.home()`→`~/.hermes/workspace` |
| `hermes_state.py:187` | `except BaseException`→`except Exception`（致命信号不回滚） |
| `gateway/run.py:1830` | 硬编码用户 ID→`os.environ.get("FEISHU_FORWARD_OPEN_ID", ...)` |
| `run_agent.py:6267` | verbose 工具参数 `_mask_sensitive_args()` 掩码敏感键 |
| `SOUL.md + config.yaml` | 双写警告注释 |

### 批次 15-16：收尾（4 项）
| 文件 | 修改 |
|------|------|
| `terminal_tool.py:1372` | 重试仅对 ConnectionError/TimeoutError/OSError 瞬态错误 |
| `hermes_state.py:556` | set_token_counts → 委托 update_token_counts(absolute=True) |
| `hermes_state.py:636` | resolve_session_id 歧义时 logger.debug |
| `run_agent.py:23` | import 顺序重整为标准库→第三方→本地 |

### 锦上添花
| 文件 | 修改 |
|------|------|
| `hermes_state.py:1267` | prune_sessions 加 logger.info |
| `cronjob_tools.py:526` | include_disabled 默认值 True→False 对齐 |
| `yu_long_tools.py:83` | sql_query 默认 db_path 去硬编码 |
| `prompt_builder.py:851` | 截断尾部 20% 内容加 injection 扫描 |

## 修改文件清单（17 个）

**Hermes 引擎（14 个）：**
run_agent.py, model_tools.py, context_compressor.py, prompt_builder.py,
file_tools.py, terminal_tool.py, delegate_tool.py, mcp_tool.py,
skills_tool.py, registry.py, cronjob_tools.py, gateway/run.py,
hermes_state.py

**玉龙自有（3 个）：**
yu_long_tools.py, SOUL.md, config.yaml

### 八姐追加审计：PSPAI 认知引擎 P0（4 项）

八姐兄弟Agent对 `/cognition/` 目录（engine_core.py 3343行 + engine_llm.py 896行 + engine_tools.py 4257行 + kernel.py 3711行）做了客户视角商业工程审计。评分 3.5/10。

| 文件 | P0# | 修改 |
|------|:---:|------|
| `engine_core.py:934` | 1 | 删除 `continue`——`_industrial_loop.tick()` 从死代码恢复 |
| `engine_core.py:2332` | 2 | 删除未定义的 `exec_result` 引用——消除 NameError |
| `engine_core.py:864` | 3 | spin 轮询 `asyncio.sleep(0.0001)` → `asyncio.Event.wait()` 事件驱动 |
| `engine_tools.py:546/557/569` | 4 | `execute_python`/`run_shell`/`ssh_exec` → `risk_level=3`；改造 tuple 注册循环支持可选 risk_level |

八姐诊断的三重致命弱点已写入 `code-writing-methodology`「防线三」子节：
1. 改完上游不检下游（continue 杀死工业流水线）
2. 安全认知盲区（接受 risk_level 修复但不给危险工具加标）
3. 单文件恐惧症（11200行三个文件，docstring 写"目标≤600行"但不拆）
