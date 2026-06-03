# GitHub API 访问技巧（DGX-1 网络限制环境）

## 背景

DGX-1 (192.168.1.35) 的网络环境存在特殊性：
- `curl`/`wget` 访问 `api.github.com` 和 `github.com` 经常超时
- Git SSH 443 端口可用（`git@github.com:liuyong-pspai/PSPai.git`）
- `git push/pull/clone` 通过 SSH 正常
- HTTPS/Git 协议被阻断

## 技巧：Python urllib 替代 curl

当 `curl` 访问 GitHub API 超时时，**Python 的 `urllib.request` 可能成功**（2026-06-03 实战验证）。

```python
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
url = "https://api.github.com/repos/liuyong-pspai/PSPai/releases/tags/v1.2.7"

req = urllib.request.Request(url)
req.add_header("Accept", "application/vnd.github+json")
req.add_header("Authorization", "token ghp_...")
req.add_header("User-Agent", "Python")

with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    data = json.loads(resp.read())
    release_id = data['id']
    upload_url = data['upload_url']
```

**为什么有效：** Python urllib 使用不同的底层网络栈（基于 OpenSSL），不受 DGX-1 某些网络层面的限制影响。

## 技巧：手动上传 Release Asset

当 CI 无法构建某平台安装包时，可手动上传：

```python
upload_url = f"https://uploads.github.com/repos/liuyong-pspai/PSPai/releases/{release_id}/assets?name=xiaolongren-setup.zip"

with open(zip_path, 'rb') as f:
    data = f.read()

req = urllib.request.Request(upload_url, data=data, method='POST')
req.add_header("Authorization", "token ghp_...")
req.add_header("Content-Type", "application/zip")
req.add_header("Content-Length", str(len(data)))

with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
    result = json.loads(resp.read())
    # result['browser_download_url'] 是下载链接
```

## 注意事项

- `uploads.github.com` 域名独立于 `api.github.com`，需分别验证可达性
- 上传大文件（>10MB）时 timeout 设置 ≥ 120s
- 此方法仅作为 CI 失败时的兜底方案，不应替代 CI 自动构建
