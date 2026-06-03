# GitHub 认证故障排查

> 2026-06-02 实战：token 过期导致 push 失败，全流程诊断+修复。

## 常见错误

### 1. Git Push 认证失败

```
remote: Invalid username or token.
Password authentication is not supported for Git operations.
fatal: 鉴权失败
```

**原因**：GitHub 2021年起禁用密码认证，只能用 Personal Access Token (PAT)。旧 token 过期或被吊销后出现此错误。

**诊断**：
```bash
# 查看当前 remote URL（token 是否还在）
git remote get-url origin

# 测试 token 是否有效
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user
# 200=有效, 401=过期
```

### 2. GitHub API 401

```json
{"message": "Bad credentials", "status": "401"}
```

**原因**：
- Token 格式错误（从 git remote URL 提取时截断）
- Token 权限不足（需要 `repo` scope）
- Token 是密码而非 PAT（GitHub 不接受密码调用 API）

### 3. `gh` CLI 未登录

```bash
gh auth status
# → You are not logged into any GitHub hosts.
```

**修复**：
```bash
# 方式1：浏览器登录（需桌面环境）
gh auth login

# 方式2：token 登录（无浏览器可用）
echo "YOUR_PAT" | gh auth login --with-token
```

## Token 生成步骤（给非技术用户）

> ⚠️ 不要说「Settings → Developer settings → PAT → Generate」，
> 用户不是技术人员，给具体步骤：

1. 打开 https://github.com/settings/tokens
2. 点「Generate new token」→「Generate new token (classic)」
3. Note 填「PSPAI 发布」
4. Expiration 选「No expiration」
5. 勾选 **repo**（全部子项自动选中）
6. 点「Generate token」
7. **复制绿色那串字母数字**（离开页面后看不到第二次）
8. 发给我

## Token 更新到 Git Remote

收到新 token 后：
```bash
# 更新 remote URL
git remote set-url origin https://USERNAME:NEW_TOKEN@github.com/USERNAME/REPO.git

# 验证
git remote get-url origin
git push --dry-run
```

## 陷阱

- **git remote URL 中的 token 会被 `***` 遮蔽**，无法直接读取。`git remote get-url` 时 Hermes 会脱敏
- **`git credential fill` 需要交互式输入**，在非交互环境中不可用
- **不要用 `git credential approve` 缓存 token** — 多 Agent 共享环境时可能泄漏
- Token 过期后唯一的恢复方式是重新生成，无法续期
