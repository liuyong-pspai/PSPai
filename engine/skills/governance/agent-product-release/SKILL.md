---
name: agent-product-release
category: governance
version: 1.0.0
author: Agent
tags: [release, github, packaging, closed-source, smoke-test, product]
related_skills: [unified-audit-8fold, computer-use-toolchain-mastery, cross-agent-health-monitoring]
last_updated: 2026-05-31
description: PSPAI Agent产品发布全流程——内核闭源编译、体验层开源打包、冒烟验证、GitHub Release自动化。适用场景：当用户说「把这个Agent发布出去」「做产品级交付」「向全世界发布」时触发。
---

# Agent 产品发布全流程

> 从开发机到 GitHub Releases 的完整产品化管线。
> 核心原则：**内核闭源护城河 + 体验层开源引爆生态。**

## 架构决策

```
GitHub: PSPAI/<agent-name>
├── README.md (开源 MIT)
├── Skills SDK + 工具模块 (开源，社区贡献)
├── MCP 接口规范 (开源)
└── Releases
    └── kernel-<version>.whl (闭源，Cython编译 .so)
```

**边界铁律：**

| 层 | 内容 | 策略 | 类比 |
|:---|:---|:---:|:---|
| 内核 | PSPAI框架/八层记忆/铁律引擎/审计核心 | **闭源 .so** | Android内核 |
| 硬化 | 硬六模块/三刀防火墙 | **闭源 .so** | SELinux |
| 协议 | MCP接口/Agent API | **开放规范** | AOSP API |
| 体验 | Skills/工具模块/视觉/语音 | **开源 MIT** | Google Apps |
| 社区 | 第三方技能/自定义工具 | **开源贡献** | Play Store |

## 发布六步流程

### 第1步：冒烟验证（红线）

**冒烟不通过 = 禁止发布。** 15 项验证覆盖五模块：

```bash
python3 smoke_test.py
# 输出 fuxi_smoke_report.json
# 全绿 → 进入第2步
# 红色 → 阻塞，修好再来
```

冒烟三层结构：
- **导入层** — 5个模块能否正常导入
- **功能层** — 7个核心函数能否实际运行
- **铁律层** — SOUL存在？MEMORY有硬化？config有注册？L3非空？

### 第2步：内核编译

```bash
cd publish && python3 build_kernel.py
```

编译方案：
- **推荐 Cython** → 编译为 .so，性能↑ 破解成本高
- **备选 PyArmor** → 混淆加密，纯Python跨平台

内核五件套（全闭源）：
1. `pspai_core/` — PSPAI执行框架
2. `memory/` — 八层永生记忆引擎
3. `iron_rules/` — 铁律引擎
4. `audit/` — 八维审计核心
5. `self_awareness/` — 自感知协议

### 第3步：体验层打包

```bash
cd open && tar czf fuxi-agent-{version}.tar.gz .
```

体验层必须包含：
- `README.md` — 项目首页（架构图+快速开始+能力矩阵）
- `docs/SKILL_SDK.md` — 技能开发指南
- `config.example.yaml` — 配置模板（无密钥）
- `requirements.txt` — 体验层依赖清单

### 第4步：生成校验和

```bash
cd dist && sha256sum * > SHA256SUMS
```

### 第5步：创建 GitHub Release

```bash
bash publish.sh v1.0.0
```

自动执行：编译内核 → 打包体验层 → 生成SHA256 → 创建Release草稿

Release Notes 模板：
```markdown
# 🐉 Agent v1.0.0

## 内核 (闭源)
- PSPAI 执行框架六大子系统
- 八层永生记忆引擎 L0-L7
- 铁律引擎（三刀防火墙 + 硬化六模块）

## 体验层 (开源)
- 5大能力模块
- Skills SDK：无限扩展
- MCP 接口协议

## 安装
pip install kernel-1.0.0-*.whl
git clone https://github.com/PSPAI/agent && cd agent && pip install -r requirements.txt
```

### 第6步：审核 + 发布

1. 在 GitHub 上审核 Release 草稿
2. 确认冒烟报告全绿
3. `gh release edit v1.0.0 --draft=false`

## 远程Agent自启动守护

当远程机无法通过 SSH 启动进程时，部署 daemon 脚本：

```bash
# DGX-2 本地执行（一次即可）
nohup bash ~/fuxi_daemon.sh &
```

daemon 脚本自动：
- 清理旧锁 → 启动网关 → 启动吸收管道
- 每30秒健康检查
- 挂了自动拉起来
- 每小时输出状态日志

## Skills SDK 设计

Skills 是能力扩展单元，任何人都能写：

```python
# my_skill.py — 社区贡献示例
def greet(name: str) -> str:
    """向用户打招呼"""
    return f"你好 {name}！我是伏羲 🐉"

def search_docs(query: str, index: str = "default") -> list:
    """搜索本地文档"""
    ...
```

## 许可证

- 体验层：MIT License
- 内核层：PSPAI Core License（个人免费/商业授权/禁止反编译）

## 陷阱

- **不要先发布再验证** — 冒烟不过的发布 = 事故
- **README 必须含架构图 + 快速开始** — 这是用户第一眼
- **config.example.yaml 不能含任何密钥** — 哪怕测试密钥
- **内核 .so 分平台编译** — Linux/macOS/Windows 三个 .whl
- **GitHub Release 先草稿** — 审核通过再公开
- **UI 需多主题** — 不同用户群体偏好不同（龙宫·古风/科技·赛博/Loft·工业），用CSS变量驱动一键切换。详见 `references/three-realm-theme-system.md`
