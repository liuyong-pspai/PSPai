# SSH 绕过 GFW 推 GitHub

> 2026-06-02 DGX-1实战：HTTPS git推GitHub被GFW干扰（TCP 68秒+，git-receive-pack 永不响应），SSH秒连

## 现象

```bash
# HTTPS推送卡死
git push https://github.com/user/repo.git master
# GIT_TRACE显示：TCP连接68秒 → HTTP/2 GET /info/refs 发出 → 服务器永不响应
```

## SSH为何有效

- HTTPS走443端口 → GFW深度包检测干扰git协议特征
- SSH走22端口 → GFW不干扰（SSH也是管理服务器的常用协议，无法一刀切）

## 一键部署流程

```bash
# 1. 生成密钥（一次性）
ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/id_ed25519_github -N ""

# 2. 显示公钥 → 用户粘贴到 github.com/settings/keys
cat ~/.ssh/id_ed25519_github.pub

# 3. ⚠️ 清除全局URL重写陷阱！
git config --global --unset url.https://github.com/.insteadof

# 4. 验证连接
ssh -i ~/.ssh/id_ed25519_github -T git@github.com
# 输出: Hi <user>! You've successfully authenticated...

# 5. 推送
export GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github -o StrictHostKeyChecking=no"
git remote add gh-ssh git@github.com:user/repo.git
git push gh-ssh master --tags
```

## 致命陷阱：url.insteadof

```bash
# 这个全局配置会静默把 git@github.com: → https://github.com/
git config --global url.https://github.com/.insteadof git@github.com:

# 结果：你写的是SSH URL，git实际走HTTPS → 照样被GFW卡死
# 检查并删除：
git config --global -l | grep insteadof
git config --global --unset url.https://github.com/.insteadof
```

## 其他尝试过但失败的方法

| 方法 | 结果 |
|------|------|
| HTTPS + HTTP/1.1 | 超时（和HTTP/2一样被干扰） |
| HTTPS + 小文件测试 | 1字节文件也超时 |
| GitHub API 创建Blob | 空仓库无法用Git Database API |
| GitHub API 创建文件 | Basic Auth 401（需PAT） |
| Gitee HTTPS推送 | ✅ 0.68秒（国内服务器，不受GFW影响） |
