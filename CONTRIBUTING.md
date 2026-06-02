# 贡献指南

感谢你对 **小龙人（XiaoLongRen）** 项目的关注！

## 🌟 如何贡献

### 报告Bug

1. 在 [Issues](https://github.com/liuyong-pspai/PSPai/issues) 中搜索，确认未有人报告过
2. 创建新 Issue，描述：
   - 操作系统与版本
   - 复现步骤
   - 期望行为 vs 实际行为
   - 截图/日志（如有）

### 提交代码

1. **Fork** 本仓库
2. 创建特性分支：`git checkout -b feature/你的特性`
3. 遵循现有代码风格（Python: PEP 8）
4. 确保 `python3 ci_preflight.sh` 通过
5. 提交 Pull Request，描述改动内容与原因

### Pull Request 规范

- 一个 PR 只做一件事
- 标题简洁清晰（中英文均可）
- 关联对应 Issue（`Closes #123`）
- 包含必要的文档更新

## 📋 开发环境

```bash
# 克隆仓库
git clone https://github.com/liuyong-pspai/PSPai.git
cd PSPai

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python3 UI原型/server.py
# 浏览器打开 http://localhost:8088
```

## 🏗️ 项目结构

```
PSPai/
├── UI原型/         # 前端界面
│   ├── index.html  # 主页面
│   ├── server.py   # 开发服务器
│   └── lang/       # 语言包
├── engine/         # 开源引擎组件
├── README.md       # 项目说明
├── CHANGELOG.md    # 更新日志
└── start.sh        # 一键启动
```

## 🤝 行为准则

- 尊重每一位贡献者
- 建设性讨论，对事不对人
- 帮助新人融入项目
- 中文/English 均可交流

## 📄 协议

本项目采用 **AGPL-3.0** 协议。贡献代码即表示你同意在该协议下授权你的代码。
