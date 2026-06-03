---
name: agent-product-release
category: governance
version: 1.8.0
author: 刘玉龙 P07
version: 2.0.0
last_updated: 2026-06-03
changelog: |
  v2.0.0 — 小龙人v1.2.7深度审计实战：9维审计+10大陷阱+前端容错+引擎重启+移动端连通性。详见 references/published-package-audit-checklist.md
  v1.8.0 — 发布后推广矩阵+账号注册提示+文档双语规范
description: PSPAI Agent产品发布全流程+发布后审计——内核闭源编译、体验层开源打包、冒烟验证、GitHub Release自动化、Topics/Homepage/CHANGELOG/CONTRIBUTING五项强制审计。适用场景：当爸说「把这个Agent发布出去」「做产品级交付」「向全世界发布」时触发。
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

## 文档双语规范（强制）

**所有公开文档必须是中英双注版** — 爸多次强调此要求。格式：

```
## 中文标题 · English Title

中文正文中文正文中文正文。
English content english content english content.

| 中文表头 | English Header |
|:--|:--|
| 中文内容 | English content |
```

**规则：**
- 标题：中文在前，英文在后，用 `·` 或 `|` 分隔
- 正文段：中英文各一段，中文先
- 表格：列名中英并列
- 按钮/标签/代码注释：中文保留，英文附加
- 不要求逐句对照，但要保证英文独立可读

**适用文件：** README.md / INSTALL.md / CHANGELOG.md / CONTRIBUTING.md

## 发布后推广矩阵（强制步骤）

> 发布完成后的推广不是可选项，是发布流程的一部分。2026-06-02 实战建立。

### 推广渠道优先级

| 优先级 | 平台 | 类型 | 注册门槛 | 发布时机 |
|:--:|:--|:--|:--|:--|
| 1 | Product Hunt | 英文产品发布 | 邮箱 | 周二15:00（北京时间） |
| 2 | Hacker News | Show HN 帖 | 无需注册 | 随时 |
| 3 | 知乎 | 中文长文回答 | 手机号 | 注册即发 |
| 4 | B站 | 专栏文章+视频 | 手机号 | 注册即发 |
| 5 | V2EX | 创意分享帖 | 手机号 | 注册满7天后 |
| 6 | 掘金 | 架构拆解文 | 手机号/微信 | 注册即发 |
| 7 | CSDN | 技术教程 | 手机号 | 注册即发 |
| 8 | 抖音 | 短视频 | 手机号 | 需录视频 |
| 9 | 小红书 | 图文帖 | 手机号 | 角色颜值展示 |

### 推广内容准备

每次发布时必须准备好：
1. **Product Hunt 英文帖** — Tagline (40-60字符) + Description + First Comment
2. **中文社区帖** — 一套核心文案适配各平台风格
3. **截图5张** — 聊天/角色/启动/语言/记忆
4. **视频素材** — B站5分钟演示脚本 + 抖音15秒脚本

### 推广执行模式

**自主发布原则** — 爸期望我能自己发布，不是让他手动操作。但实际情况：
- DGX-1 网络可能不通外部HTTPS网站
- 这些平台需要浏览器登录+验证码，API不可达
- 解决方案：**内容全部准备好（一键复制文件），爸只需登录+粘贴**

**发布内容文件规范：**
```
发布素材/
├── 全渠道宣传矩阵方案.md    # 完整策略文档
├── 发布内容-一键复制.md       # 三平台原文（面向爸直接使用）
├── 知乎-发布内容.md           # 单平台提取版
├── B站-发布内容.md            # 专栏+视频脚本
└── 三平台安装完全指南.md      # 给用户的安装教程
```

### 账号注册提示

当爸说"我没有账号"时：
1. 告诉他每个平台的注册链接（不是菜单路径！直接URL）
2. 按优先级排序，不是全部注册
3. 标注注册门槛：邮箱/手机号/无需注册

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
- **推荐 PyInstaller** → 打包为单二进制ELF，源码不可见，适合依赖框架运行时的场景
- **Cython** → 编译为 .so，性能↑ 破解成本高
- **备选 PyArmor** → 混淆加密，纯Python跨平台

> PyInstaller 详细用法见 `references/pyinstaller-packaging.md`

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
- `LICENSE` — AGPLv3 + 品牌保护附加条款

> 双轨拆分详细映射见 `references/dual-track-split-mapping.md`

### 第4步：生成校验和

```bash
cd dist && sha256sum * > SHA256SUMS
```

### 第5步：创建 Release

**首选 GitHub + SSH 推送**（国内GFW环境）。Gitee 作为备选。

> GitHub Actions CI 支持三平台编译（Linux x86_64 / macOS / Windows），Gitee CI 目前仅支持 Linux。

### 第5步-B：GFW环境下的SSH推送（2026-06-02关键突破）

当国内机器 HTTPS git push 被 GFW 干扰（TCP握手68秒+、git-receive-pack 永不响应）时，**SSH 协议不受影响**。

**一键SSH推送流程：**

```bash
# 1. 生成SSH密钥（一次性）
ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/id_ed25519_github -N ""

# 2. 显示公钥，让用户在 github.com/settings/keys 添加
cat ~/.ssh/id_ed25519_github.pub

# 3. 清除全局HTTPS重写陷阱（关键！）
git config --global --unset url.https://github.com/.insteadof

# 4. 推送
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github -o StrictHostKeyChecking=no" \
  git push git@github.com:user/repo.git master --tags
```

> 详参 `references/ssh-github-gfw-bypass.md`

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

### 第7步：发布后审计（强制，v1.8.0修订）

**每次发布后必须过这5项，一项不过=发布未完成。**

| # | 检查项 | 验证方式 | 修复方式 |
|:--|:--|:--|:--|
| 1 | **Release正文不为空** | 打开 Releases 页面看是否有说明文字 | CI `softprops/action-gh-release` 加 `body:` 参数 |
| 2 | **Topics已设置** | 仓库首页右侧是否有标签（ai, chatbot等） | CI job 尝试，失败则给用户发直达链接手动添加 |
| 3 | **Homepage已设置** | 仓库首页右侧是否有 Website 链接 | 同上 |
| 4 | **CHANGELOG.md 存在** | `https://github.com/.../blob/master/CHANGELOG.md` | 写文件→push，含语义化版本格式 |
| 5 | **CONTRIBUTING.md 存在** | `https://github.com/.../blob/master/CONTRIBUTING.md` | 写文件→push，含Bug报告/PR规范/行为准则 |

### Topics/Homepage 设置策略（分级处理）

**🚨 `administration: write` 不是有效的 GitHub Actions 权限！** 2026-06-02 实战验证：此权限被 Actions 忽略，`set-repo-meta` job 不会触发。`GITHUB_TOKEN` 对 repo 设置类 API（topics/homepage）权限不足，需要 Personal Access Token。

**方案一：CI 自动设置（需提前配置 PAT Secret）**

```yaml
# release.yml 关键配置
permissions:
  contents: write
  # ❌ 不要写 administration: write — 无效权限

# 需要用户先在仓库 Settings → Secrets → Actions 中
# 添加 PERSONAL_ACCESS_TOKEN（classic, repo 权限）
set-repo-meta:
  needs: build-engine
  runs-on: ubuntu-22.04
  steps:
    - name: Set repo topics & homepage
      env:
        PAT: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
      run: |
        curl -X PUT -H "Authorization: token $PAT" \
          -d '{"names":["ai","chatbot","agent","digital-lifeform","xiaolongren"]}' \
          "https://api.github.com/repos/${{ github.repository }}/topics"
        curl -X PATCH -H "Authorization: token $PAT" \
          -d '{"homepage":"https://github.com/org/repo"}' \
          "https://api.github.com/repos/${{ github.repository }}"
```

**方案二：用户手动添加（30秒，无依赖）**

当 PAT 未配置或 CI 不可达时，给用户直达链接：

> 打开 https://github.com/liuyong-pspai/PSPai
> 仓库首页右侧 → Topics 区域 → 点击 **+** → 粘贴5个标签：
> `ai chatbot agent digital-lifeform xiaolongren`
> 保存，完成。

两种方案并行：CI 能在条件满足时自动处理，否则给用户最小摩擦的手动路径。

**Release 正文嵌入：**
```yaml
- uses: softprops/action-gh-release@v2
  with:
    body: |
      ## 🚀 发布说明
      ### 📦 下载
      | 文件 | 平台 |
      ...
    files: dist/*
```

> 2026-06-02 实战教训：v1.0.6 发布后5项全缺。v1.0.7 补齐了 Release 正文 + CHANGELOG + CONTRIBUTING。Topics/Homepage 因 `administration: write` 无效 + `GITHUB_TOKEN` 权限不足而失败，最终提供手动链接解决。

### 🚨 DGX-1 网络约束（2026-06-03 更新）

DGX-1 (192.168.1.35) 访问 GitHub HTTPS (443) **不稳定/部分可达**，SSH (22) 正常。关键发现：

| 操作 | 方式 | 状态 |
|:--|:--|:--|
| `git push/pull` via SSH | SSH:22 | ✅ 正常 |
| GitHub API via **curl** | HTTPS:443 | ❌ 超时 |
| GitHub API via **Python urllib** | HTTPS:443 | ✅ **可达**（2026-06-03验证） |
| GitHub Web (github.com) | HTTPS:443 | ⚠️ 部分页面可达 |
| `uploads.github.com` | HTTPS:443 | ✅ 可达 |

**应对策略（按优先级）：**
1. **首选 Python urllib** — 上传 Release 资产、查询 Release ID 等 API 操作，用 Python `urllib.request` 而非 curl。已验证：短超时即可获取 release 信息、上传文件到 uploads.github.com
2. 代码推送：SSH 正常，无影响
3. curl 到 GitHub API → 不可靠，避免使用
4. Web 页面验证 → 部分可达，优先用 Python API

> 此约束可能随时间变化，每次会话前应重新验证。`curl` 超时不代表 Python urllib 也超时。

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

- **体验层**：AGPLv3 + 品牌保护附加条款（推荐）
  - 传染性：修改UI必须继续开源
  - 品牌保护：商标/角色形象/PSPAI标识不得移除冒用
  - 客户可改皮换品牌，但不能偷魂
- **内核层**：PSPAI Core License（个人免费/商业授权/禁止反编译）

> 品牌保护条款的核心：「皮可以换，魂换不了」— UI开源，引擎闭源

## 产品身份边界（2026-06-01新增）

对外发布的Agent必须配置身份边界——绝不向终端客户暴露底层技术栈。详见 `references/product-identity-boundary.md`。

核心规则：客户问「你是谁」→ 回答「PSPAI，昱成科技集团的产品」，不是「基于Hermes框架构建的AI智能体」。

## 陷阱

- **不要先发布再验证** — 冒烟不过的发布 = 事故
- **README 必须含架构图 + 快速开始** — 这是用户第一眼
- **config.example.yaml 不能含任何密钥** — 哪怕测试密钥
- **内核 .so 分平台编译** — Linux/macOS/Windows 三个 .whl
- **发布先草稿** — 审核通过再公开
- **UI 需多主题** — 通过CSS变量驱动一键切换。详见 `references/three-realm-theme-system.md`
- **干净目录打包** — 当不编译内核时，直接发布源码+资源的打包方式。详见 `references/clean-directory-packaging.md`
- **PSPAI后端必须接入Hermes引擎** — 不能直接用裸HTTP调LLM（会丢工具链）。详见 `references/hermes-backend-integration.md`
- **config.yaml 必须启用对应工具集** — 加了工具但没加到 toolsets 列表里，工具不会出现。比如 web_search 需要 `toolsets: [..., web]`
- **发布前必须品牌审计** — 开源包中不得出现 DeepSeek/Hermes/OpenAI 等底层厂商名。详见 `references/pre-release-brand-audit.md`
- **改HTML model ID必须同步lang key** — model ID 从 `ds` 改为 `pspai` 时，zh.json/en.json 中的 `ds_desc` 必须同步改为 `pspai_desc`，否则翻译丢失
- **🚨 config.yaml 绝对不能打进 PyInstaller 二进制！** — 客户需要编辑 config.yaml（加平台/换模型/改人格），打进二进制 = 客户改不了 = 废了。用 `--add-data` 时排除 config.yaml，发布时作为并列外部文件
- **多平台是硬需求（爸选择B方案）** — 不做服务端部署妥协。PyInstaller **不支持跨平台编译**（`--target-architecture` 仅限 macOS）。Linux ARM64/x86_64、Windows、macOS 四个平台必须各自原生环境编译，**CI是唯一可行方案**。详见 `references/github-actions-ci-workflow.md`
- **🚨 PyInstaller 本地编译超时** — Hermes 终端对长时间命令有超时限制，PyInstaller 编译（2-5分钟）100%被拦截。**不要在 Hermes 终端里跑 PyInstaller**，走 GitHub Actions CI 或者让用户手动在终端执行
- **config.yaml 外置加载模式** — 代码应优先读 `CWD/config.yaml`（客户可编辑），兜底读 `BASE_DIR/config.yaml`（PyInstaller内）。这样发布时 config.yaml 不放 `--add-data`，作为独立文件随二进制分发
- **🚨 GitHub PAT 过期** — 令牌过期后 git push 报 `Invalid username or token. Password authentication is not supported`。需要用户重新生成 PAT（classic, repo 权限）。完整诊断+修复见 `references/github-auth-troubleshooting.md`
- **不要教用户技术操作** — 用户是董事长/设计师，不是技术人员。「Settings → Developer settings → PAT」这种菜单路径对他没用。给具体步骤：直接发链接+标注点哪个按钮+复制什么内容。能让CI自动化的一律自动化，不让用户手动做
- **单仓库兜底方案** — 当无法创建私有仓库（无API token）时，闭源引擎放公开仓库的 `engine/` 子目录，CI编译+打包时 `--exclude='engine'`。闭源保护依赖LICENSE而非隐藏代码
- **token 提取陷阱** — `git remote get-url` 中的 token 会被 Hermes 脱敏为 `***`，无法直接用。正确做法：让用户重新生成 PAT 后手动更新 remote URL
- **Gitee API vs Git 认证不同** — API 用私人令牌(token)，Git 推送可用密码。详见 `references/gitee-publishing-workflow.md`
- **🚨 `administration: write` 不是有效 GitHub Actions 权限** — 2026-06-02 实战验证：此权限名在 Actions YAML 中无效，GitHub 会静默忽略。Topics/Homepage API 需要 PAT（Personal Access Token，classic + repo 权限），不能用 `GITHUB_TOKEN`（权限不足）。替代方案：给用户直达链接手动添加（30秒完成）。
- **🚨 不要让用户手动编辑 .env！** — 用户是普通人不是技术员。API Key格式、环境变量语法、编码问题——任何一步卡住用户就流失了。**必须在浏览器UI里完成所有配置**，所见即所得。三平台统一：Windows .exe / macOS .dmg / Linux .run，双击安装→桌面图标→浏览器配模型→开始使用。详见 `references/one-click-installer-with-config-wizard.md`
- **一键安装是桌面产品的最低门槛（三平台）** — 下载→双击→桌面图标→浏览器配模型→开始使用。含Python embeddable + 引擎 + 前端 + 启动器 + 配置向导。三平台逻辑统一：Windows (7z SFX .exe)、macOS (.app/.dmg)、Linux (shell自解压 .run)。统一打包脚本 `installer/make_installer.py`，CI三平台并行构建。详见 `references/one-click-installer-with-config-wizard.md`
- **🚨 Windows CI安装包构建必须用 `shell: cmd`** — bash (MINGW64) 找不到Windows路径（`os.path.expandvars`/`shutil.which` 均失效），PowerShell也有COM路径问题。**唯一可靠的是 `shell: cmd`**，且用 `python`（cmd里无 `python3`）。v1.2.0→v1.2.7 共8次迭代才定位到根因。详见 `references/one-click-installer-with-config-wizard.md`
- **🚨 放弃7z SFX，改用zip** — 7z在CI上永远不可靠（路径/环境变量/7z.sfx模块位置均不稳定）。Windows安装包直接用 `shutil.make_archive('zip')` + install.bat，用户解压后双击bat即可
- **🚨 Windows CI安装包构建失败时的兜底方案（2026-06-03实战）** — `build-installer` job的Windows runner持续失败（v1.2.0→v1.2.7共8个版本shell切换无效），但引擎二进制(`xiaolongren-engine-windows.exe`)能正常编译。兜底流程：①从Release下载引擎exe → ②在Linux上手动构建zip（复制前端+launcher.py+引擎+写install.bat → shutil.make_archive）→ ③通过Python urllib上传到Release。zip内容结构：`frontend/` + `launcher.py` + `xiaolongren-engine.exe` + `install.bat`。未来修复CI后移除兜底
- **发布包深度审计** — 安装包上架前必须过7维度检查（身份/记忆/配置/模型/技能/通信/安装）。避免 `skip_memory=True`、身份缺失'You are PSPAI.'、配置链断裂等常见事故。详见 `references/published-package-audit-checklist.md`
- **GitHub API 读写分离** — Basic Auth (用户名:密码) 能读仓库信息（HTTP 200），但不能写 SSH Key、创建文件等（HTTP 401 Requires authentication）。写操作需要 Personal Access Token (PAT)

### 发布前打磨清单（2026-06-01新增）

每次发布前过一遍四步打磨，确保产品干净、轻量、稳定：

1. **清垃圾** — 删 `sessions/` `logs/` `memories/` `cron/` `bin/` `models_dev_cache.json` `__pycache__/` 等运行时产物
2. **压资源** — 图片用PIL resize到显示尺寸的2x + JPEG quality 78，原图备份到 `backups/img_original/`
3. **服务器升级** — 不用 `python3 -m http.server`（单线程卡死），改用 `ThreadingMixIn + HTTPServer` 多线程
4. **双语走查** — 切语言后逐面板检查：按钮/占位符/标签/角色描述是否都翻译了；后端错误消息也要中英双语

> 详参 `references/release-polish-checklist.md`

### 发布前品牌审计（2026-06-01新增，强制步骤）

打磨完成后、打包前，**必须执行品牌敏感词扫描**：

```bash
# 扫描开源包中所有文本文件
# 禁止词：DeepSeek / Hermes / OpenAI / 个人路径 / 密钥残留
```

五步走：解包扫描 → 重点文件逐行检查 → 语言包key同步 → 平台连通验证 → 修复后重新打包+复检。零泄露才算通过。

> 完整清单+修复脚本见 `references/pre-release-brand-audit.md`

### 语言包key同步陷阱（2026-06-01教训）

修改 HTML 中的 model ID 或 descKey 后，**必须同步更新** lang/*.json 中的对应 key。HTML 引用 `pspai_desc` 但 JSON 里只有旧 `ds_desc` → 翻译显示空白，客户看到的是 key 名而不是中文描述。

完整发布六步流程（配置脱敏→清垃圾→压资源→升级服务器→双语走查→交付物打包）详见 `references/release-polish-checklist.md`。

### 多语言包架构（2026-06-01新增）

独立JSON文件 + 动态语言索引 + 后端字典查找，加语言=丢文件+改配置，零代码改动。详见 `references/multi-language-i18n-architecture.md`。

### 浏览器内置TTS（2026-06-01新增）

Web Speech API + 语音语言匹配 + 男声优先 + 再点停止，零依赖零API Key。详见 `references/browser-tts-integration.md`。
