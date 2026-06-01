# Hermes Agent context_compressor.py 源码分析 — 2026-05-29

## 关键发现

context_compressor.py 默认阈值是 **0.50（50%）**，不是文档示例中的 85%。

```python
class ContextCompressor:
    def __init__(self,
        model: str,
        threshold_percent: float = 0.50,    # ← 默认50%！
        protect_first_n: int = 3,            # 保护前3条消息
        protect_last_n: int = 20,            # 保护后20条消息
        summary_target_ratio: float = 0.20,  # 摘要占压缩内容20%
        ...
    ):
```

## 压缩算法（五步）

1. **裁剪旧工具结果**（cheap，无需LLM）— 替换为 `[Old tool output cleared]`
2. **保护头消息** — system prompt + 首轮交换不动
3. **保护尾消息** — 最近 ~20K tokens 不动
4. **结构化摘要中间轮次** — 用辅助模型生成摘要（Goal/Progress/Decisions/Files/Next Steps）
5. **迭代更新** — 后续压缩时更新之前的摘要而非重新生成

## 辅助客户端依赖

压缩需要 auxiliary_client 调用另一个模型写摘要。如果 auxiliary_client 不可用（OpenRouter/Nous 无 Key），压缩功能降级为截断。

## PSPAI 对标

| 参数 | Hermes 默认 | PSPAI 配置 |
|:-----|:----------:|:---------:|
| 压缩阈值 | 50% | 50% ✅ |
| 保护首N条 | 3 | 前20轮要点 |
| 保护尾N条 | 20 | 最近操作结果 |
| 摘要比例 | 20% | 要点摘要 |
| max_turns | 60 | 60 ✅ |

## 教训

抄配置时不能只看文档示例值——必须读源码默认值。85% 是某个 NixOS 配置的自定义值，50% 才是框架基因。
