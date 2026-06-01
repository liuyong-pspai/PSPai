# web_search.py v2→v3 对比 + 八维审计发现

> 日期: 2026-05-31 | 审计者: Agent | 基准: code-writing-methodology + unified-audit-8fold

## v2 问题（旺福原版）

### 致命缺陷
1. **硬编码污染** `en_query = query + " crypto blockchain finance"` — 所有英文搜索被污染
2. **品牌名冲突** — hermes.com（爱马仕）混入Hermes Agent搜索结果
3. **无气味记忆** — 搜索经验不存档，每次从零开始
4. **链式超时** — 12秒timeout × 3引擎 = 36秒+，百度不可达拖死全局
5. **无评分排序** — 结果无序返回

### 八维审计评分（v2）
| 维度 | 分数 | 关键问题 |
|:---|:---:|:---|
| 代码符号 | 3/10 | 6个裸except、17函数无type hints |
| 逻辑闭环 | 2/10 | 无V/VF标记、无降级策略 |
| 系统架构 | 4/10 | 气味记忆与搜索耦合 |
| MCP对齐 | 1/10 | 工具非MCP Server |
| A2A对齐 | 1/10 | 无Agent Card |
| Agent Loop | 6/10 | 框架层正常 |
| 安全工程 | 3/10 | SSL关闭、无输出净化 |
| 工程纪律 | 4/10 | 无测试 |
| **总分** | **24/80 (30%)** | D级 |

## v3 修复

### P0阻塞（已修复）
- ✅ 6个裸except → `urllib.error.URLError, OSError, socket.timeout` / `json.JSONDecodeError, OSError` / `Exception`
- ✅ 硬编码污染 → 移除"crypto blockchain finance"
- ✅ 品牌污染 → 域名黑名单（hermes.com/.cn）

### P1高优（已修复）
- ✅ 引擎超时 → Bing快速通道（8秒timeout，够用就跳百度/Google）
- ✅ 无记忆 → 气味记忆集成（scent_map.json持久化）
- ✅ 无排序 → 三维评分（标题+2、摘要+1、URL+1、百科+2、黑名单清零）

### 验证数据
| 搜索 | v2结果 | v3结果 |
|:---|:---|:---|
| "AI Agent framework" | 90秒超时/加密污染 | 1秒/5条技术文章/14分 |
| "Hermes Agent 开源" | 爱马仕官网混入 | 5条技术内容/18分 |

## 待迭代（不阻塞使用）
- type hints补齐
- 单元测试
- 输出净化层
- MCP Server包装
