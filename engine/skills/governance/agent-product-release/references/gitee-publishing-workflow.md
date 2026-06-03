# Gitee 发布工作流（GitHub替代方案）

> 当 GitHub 不可用（注册不了/登录不进/线路超时）时，Gitee（码云）是等效替代。
> Gitee Release 功能与 GitHub 完全对等，API 兼容。

## 为什么首选 Gitee

实测数据（DGX-1, 四川电信, 2026-06-02）：

| 操作 | Gitee | GitHub |
|------|-------|--------|
| HTTP 首页 | **0.68s** | 5.0s |
| Git push (12MB) | <5s（预估） | **TCP握手68s, 请求超时** |
| API | 稳定 | 间歇性超时 |

国内机器 `git push` 到 GitHub 基本不可用——TCP三次握手被QoS限速到68秒，后续HTTP请求永远等不到响应。**Gitee是唯一实用选择。**

## 前置条件

1. 注册 Gitee 账号（gitee.com），可能需要手机号/微信
2. 安全策略：低评级账号不能公开发布 → 需在「个人设置」绑定微信或完成2FA
3. 生成私人令牌：「设置 → 私人令牌」→ 勾选 projects 权限 → 复制 token

## 创建仓库+推送

```bash
# 1. 用 token 创建仓库
curl -X POST "https://gitee.com/api/v5/user/repos?access_token=TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"repo-name","description":"...","private":false,"auto_init":false}'

# 2. 推送代码
git remote add origin https://USERNAME:TOKEN@gitee.com/USERNAME/repo-name.git
git push -u origin master
```

## 创建 Release + 上传附件

Gitee Release API（Python urllib，无需额外依赖）：

```python
import urllib.request, json, http.client, os

TOKEN = "xxx"
USER = "username"
REPO = "repo-name"
BASE = "https://gitee.com/api/v5"

# 创建 Release
body = json.dumps({
    "tag_name": "v1.0.0",
    "name": "版本名称",
    "body": "Release Notes (Markdown)",
    "target_commitish": "master",
    "prerelease": False
}).encode()
req = urllib.request.Request(
    f"{BASE}/repos/{USER}/{REPO}/releases?access_token={TOKEN}",
    data=body,
    headers={"Content-Type": "application/json;charset=UTF-8"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=30) as resp:
    release = json.loads(resp.read())
    release_id = release['id']

# 上传附件（multipart form）
boundary = '----Boundary' + os.urandom(8).hex()
with open('file.tar.gz', 'rb') as f:
    file_data = f.read()
body = (f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="file.tar.gz"\r\n'
        f'Content-Type: application/gzip\r\n\r\n').encode()
body += file_data
body += f'\r\n--{boundary}--\r\n'.encode()

conn = http.client.HTTPSConnection('gitee.com', timeout=120)
conn.request('POST', 
    f'{BASE}/repos/{USER}/{REPO}/releases/{release_id}/attach_files?access_token={TOKEN}',
    body, {'Content-Type': f'multipart/form-data; boundary={boundary}'})
resp = conn.getresponse()
result = json.loads(resp.read())
print(f"Uploaded: id={result.get('id')}")
```

## 下载链接格式

```
https://gitee.com/USER/REPO/releases/download/v1.0.0/文件名.tar.gz
```

## 查Release列表+附件

```python
# 查 release
req = urllib.request.Request(f"{BASE}/repos/{USER}/{REPO}/releases?access_token={TOKEN}")

# 查附件
req = urllib.request.Request(
    f"{BASE}/repos/{USER}/{REPO}/releases/{release_id}/attach_files?access_token={TOKEN}")
```

附件返回字段：`id, name, size, uploader, browser_download_url`

## 陷阱

- API 用 token 认证，Git 推送可用密码。两者认证方式不同，不能互换
- 仓库默认创建为私有，需手动/API 设为公开才能让外部下载
- Gitee API 有时较慢，超时设 15-30 秒；大文件上传设 120 秒
- 低安全评级账号无法创建公开仓库 → 必须先完成实名/绑微信
- 私有仓库的 Release 附件需要认证才能下载（HTTP 403）
