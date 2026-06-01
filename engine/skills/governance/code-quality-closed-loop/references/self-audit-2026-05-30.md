# 玉龙自审计记录

> 日期：2026-05-30
> 审计框架：unified-audit-8fold + 商业工程规范 + 六刀自检 + 客户交付验收标准
> 范围：~/.hermes-yulong/ 全覆盖

## 关键发现

### P0：SOUL.md vs config.yaml 压缩阈值矛盾
- SOUL.md 第75行：压缩触发 ≥80%（橙色级别）
- config.yaml system_prompt 第85行：压缩触发 ≥50%
- 根因：两套文本无自动同步，改一处忘改另一处
- 修复：config.yaml 50%→80%，对齐 SOUL.md
- 固化：诞生刀六「改SOUL必同步config.yaml」
- 护栏：SOUL.md 双写警告强化为四项同步检查清单

### 方法论创新：自审计 → 发现问题 → 固化护栏
这次自审计不是"审完修完就完了"，而是：
1. 审出 P0 配置矛盾
2. 修复阈值
3. 追问：为什么会出这个矛盾？→ 因为两套文本无同步机制
4. 固化刀六：以后改 SOUL 必须同步 config
5. 强化 SOUL 双写警告注释

这就是"修完固化，少出错"的闭环。

## 剩余待修项
| 优先级 | 问题 | 位置 |
|:--:|:--|:--|
| P1 | ssh_exec 远程路径无注入防护 | yu_long_tools.py |
| P1 | 六步闭环未体现 Spec-First | SOUL.md |
| P1 | API_SERVER 无认证 | config.yaml |
| P2 | workflow_decompose/decision_why 空壳 | yu_long_tools.py |
| P2 | cron L4/L6/L7 deliver=local | jobs.json |
| P2 | yu_long_tools.py 722行未拆分 | skills/ |

## 技术要点
- 自审计不仅要审代码，更要审配置一致性（SOUL vs config）
- 两套独立文本且无自动同步 = 矛盾的高发地带
- 修复一个 bug 后必须追问"为什么会出这个 bug"，然后加固护栏
