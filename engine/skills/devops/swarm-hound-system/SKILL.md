---
name: swarm-hound-system
description: >
  蜂群天犬系统 v3 —— 多Agent协作编排 + 公网智能搜索（气味记忆驱动）。
  蜂群：任务分解→多角色并行→汇总（Architect/Coder/Tester/Auditor/Integrator）。
  天犬：气味记忆 + 多引擎搜索 + 相关性评分 + 域名黑名单。
  从M4-2旺财/旺夫系统移植到玉龙P07，经v3深度升级。
---

# 🐝🐕 蜂群天犬系统 v3

## 何时使用

### 蜂群模式（多角色协作）
- 复杂任务需要多视角：代码审计、架构设计、全栈开发
- 需要分解为 Architect → Coder → Tester → Auditor → Integrator 角色链
- 需要SQLite任务总线追踪状态

### 天犬模式（智能搜索）
- 需要深度公网搜索：新技术调研、竞品分析、论文检索
- 需要BFS链式追踪：从一个URL出发逐步追踪到答案
- 需要「越搜越聪明」：气味记忆跨任务复用搜索经验
- 需要高质量搜索结果：自动评分排序 + 品牌名冲突过滤

## 工具路径

所有工具在 `~/.hermes-agent/tools/` 下：

| 工具 | 版本 | 用途 |
|:---|:---|:---|
| 快速搜索 | **v3** | 多引擎搜索 + 气味记忆 + 评分排序 + 黑名单过滤 |
| 天犬追踪 | v1 | BFS级联追踪搜索（DDG起点，DGX-1可能超时） |
| 嗅探引擎 | v1 | 单URL抓取+评分 |
| 气味记忆 | **v3集成** | 搜索前查档案 + 搜索后存档，JSON持久化 |
| 蜂群总线 | v1 | SQLite任务状态管理 |
| 蜂群指挥 | v1 | 多角色编排 |

## v3 核心升级（vs v2旺福版）

| 维度 | v2 | v3 |
|:---|:---|:---|
| 速度 | 百度超时拖慢→90秒+ | Bing快速通道→~1秒 |
| 质量 | 加密关键词污染 + 品牌名混入 | 纯技术内容 + 评分排序 |
| 记忆 | 无 | 气味档案跨搜索复用 |
| 排序 | 无序 | 标题/摘要/URL三维评分 |
| 过滤 | 无 | 域名黑名单（hermes.com→爱马仕） |

## 蜂群角色链

```
总指挥(Orchestrator)
  ├── 架构师(Architect) → 设计方案
  ├── Coder → 编码实现
  ├── Tester → 测试验证
  ├── Auditor → 代码审查
  └── Integrator → 集成汇总
```

## 天犬搜索流程

```
目标主题 → 嗅气味档案(历史捷径) → BFS追踪(同站优先)
  → 每页抓取→评分→判断 → 高分命中 → 归档到气味档案
```

## 搜索集成模式

在Hermes框架中直接通过terminal调用：

```bash
# 快速公网搜索
python3 ~/.hermes-yulong/tools/web_search.py "PSPAI平行时空AI 架构" 5

# 天犬深度追踪
python3 ~/.hermes-yulong/tools/tianquan/tianquan.py "Agent Memory System架构"

# 查看历史搜索档案
cat ~/.hermes-yulong/tools/tianquan/memory/scent_map.json
```

## 已知限制

- hound_engine.py 需要 Docker + Playwright 真浏览器，DGX#1暂不可用
- inner_bus ZMQ通信依赖PSPAI内环基础设施，暂不移植
- **DGX-1网络环境：仅Bing可用**，百度/Google均超时（5-8秒timeout即可跳过）
- 天犬追踪默认从DuckDuckGo起步，DGX-1上DDG也不可达，优先用web_search.py

## 🚨 陷阱与教训（v2→v3）

1. **表面好 ≠ 深层好**（用户的核心训诫）：v2表面是多引擎搜索，深层被硬编码"crypto blockchain finance"污染所有查询，搜索任何东西都带上加密关键词
2. **命名冲突污染**：Hermes同时是AI框架和奢侈品牌，v2无过滤→搜索结果混入爱马仕官网。v3用域名黑名单解决
3. **引擎超时链式拖累**：v2逐个串行等12秒超时，百度不可达拖慢全局90秒+。v3改为Bing快速通道+短timeout(5-8秒)
4. **解析器脆弱性**：Bing/百度HTML解析依赖固定class名，DOM改版就挂。v3加入正则fallback
5. **搜索经验浪费**：每次从零开始不存档。v3集成气味记忆，搜索前查档案+搜索后存档

## 维护历史

- 2026-05-31：从M4-2旺财/旺夫系统首次移植到玉龙P07
- 2026-05-31：v3深度升级——移除加密污染、集成气味记忆、增加评分排序、域名黑名单、Bing快速通道。验证：3组搜索1秒出结果，结果全技术内容无品牌污染
- 测试数据详见 references/v2-v3-comparison.md
- 八维审计详见 references/web-search-v2-v3-audit.md
