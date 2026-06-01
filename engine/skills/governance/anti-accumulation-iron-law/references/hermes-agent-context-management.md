# Hermes Agent 上下文管理机制研究（2026-05-29）

> 来源：Hermes Agent 官方文档和代码分析
> 对标结论：已全部抄入PSPAI SOUL.md和config.yaml

## 1. Compression 压缩机制

```yaml
compression = {
  enabled = true;
  threshold = 0.85;     # 上下文85%时触发自动压缩
  summary_model = "google/gemini-3-flash-preview";
};
```

**PSPAI 对标**：SOUL.md 上下文压缩机制——上下文≥80%时主动总结前20轮为要点
**差异**：Hermes用专用summary_model做压缩，PSPAI用主模型自压缩

## 2. max_turns

```yaml
agent = { max_turns = 60; };     # Agent级别
# server级别 max_turns = 100
```

**PSPAI 对标**：config.yaml max_turns: 60

## 3. 上下文颜色码

| 颜色 | 占比 | 含义 |
|:---|:---|:---|
| 🟢 绿色 | <50% | 充足 |
| 🟡 黄色 | 50-80% | 偏满 |
| 🟠 橙色 | 80-95% | 接近上限→建议/compress |
| 🔴 红色 | ≥95% | 即将溢出 |

**PSPAI 对标**：SOUL.md 四级预警表已加入上下文占比维度

## 4. 上下文可视化（TUI）

状态栏显示：Model名称 | Token数/最大窗口 | 上下文颜色条 | 压缩计数🗜️N | 耗时

**PSPAI 对标**：无法对标TUI，但在四级预警中融入颜色码

## 5. /compress 和 /usage 命令

- `/compress` — 手动触发上下文压缩
- `/usage` — 详细token/cost/context面板
- `/new` or `/reset` — 重置会话

**PSPAI 对标**：无需命令（飞书无TUI），由防积压铁律自动触发

## 6. 最低上下文要求

至少64K tokens。低于此的模型被启动时拒绝。

**PSPAI 对标**：DeepSeek 128K，远超要求
