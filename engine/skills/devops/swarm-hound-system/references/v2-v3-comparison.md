# 蜂群天犬 v2 → v3 对比测试

> 2026-05-31，DGX#1（仅Bing可用，百度/Google超时）

## 测试1：Agent技术搜索

**查询：** "AI Agent framework 2026"

### v2结果（污染版）
```
1. 爱马仕官网
2. AI工具集导航站（泛化）
3. 知乎AI入门科普（2024年）
4. 智谱开放平台
5. 腾讯云AI概述（2025年）
```
- 混入奢侈品品牌，无一篇2026年技术文章
- 硬编码 "crypto blockchain finance" 污染

### v3结果（净化版）
```
1. [Bing][14分] 2026 AI Agent 框架实战对比：LangGraph/CrewAI/AG2
2. [Bing][14分] awesome-ai-agents-2026 - GitHub
3. [Bing][14分] 2026年AI Agent技术全景：12大主流框架
4. [Bing][11分] Agent Framework文档 | Microsoft Learn
5. [Bing][8分] AI Agent框架之争：8大框架核心技术
```
- 全部2026年技术文章，评分14-8分

## 测试2：Hermes搜索（品牌冲突）

**查询：** "Hermes Agent 开源 AI 智能体"

### v2结果
```
1. 爱马仕中国官网 ← 奢侈品！
2. Hermes Agent中文文档
3. 知乎：Hermes Agent指南
4. 爱马仕美国官网 ← 奢侈品！
5. Hermes Agent官网
```

### v3结果
```
1. [Bing][18分] Hermes Agent - 免费开源AI智能体框架 - AIHub
2. [Bing][17分] Hermes Agent — 有记忆的开源AI智能体
3. [Bing][16分] 2026最新Hermes Agent教程
4. [Bing][12分] Hermes Agent中文文档
5. [Bing][12分] GitHub: NousResearch/hermes-agent
```
- 零条爱马仕，全部技术内容

## 性能对比

| 指标 | v2 | v3 |
|:---|:---|:---|
| 首次搜索耗时 | 90秒+ | ~1秒 |
| 气味记忆 | 无 | 3次搜索后5个高价值域名 |
| 结果评分 | 无 | 三维评分(标题/摘要/URL) |
| 品牌污染 | hermes.com混入 | 黑名单过滤 |
