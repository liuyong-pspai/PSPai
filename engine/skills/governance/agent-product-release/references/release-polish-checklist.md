# 发布前打磨清单

> 2026-06-01 小龙人v1.0电脑版发布实战验证

## 四步打磨（每次发布前强制执行）

### 1. 清垃圾 — 删运行时产物

```bash
# 必须删除的目录
rm -rf sessions/ logs/ memories/ cron/ bin/ data/
# 必须删除的文件
rm -f models_dev_cache.json .tirith-install-failed auth.lock
rm -f .skills_prompt_snapshot.json
# 清除所有Python缓存
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
```

**效果：** 10.4MB → 6.2MB（本例）

### 2. 压资源 — 图片Web优化

```python
from PIL import Image

for img_path in imgs:
    img = Image.open(img_path)
    # 目标高度=显示容器的2.4倍（Retina够用）
    target_h = 400
    ratio = target_h / img.height
    new_w = int(img.width * ratio)
    img = img.resize((new_w, target_h), Image.LANCZOS)
    img.save(img_path, 'JPEG', quality=78, optimize=True)
```

**先备份原图：**
```bash
mkdir -p backups/img_original && cp *.jpg backups/img_original/
```

**效果：** 6张图5.7MB → 170KB，97%压缩率

### 3. 升级服务器 — 多线程替代单线程

不用 `python3 -m http.server`（单线程，卡死）。改用：

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

class ThreadedServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=3600')
        super().end_headers()
```

### 4. 双语走查 — 逐面板检查

切语言后逐面板验证：

- [ ] 底栏5个按钮标签
- [ ] 4个面板全部文字（模型/备忘/角色/安全）
- [ ] 输入框placeholder
- [ ] 模型状态文字（已配置/需API Key）
- [ ] 操作按钮（取消/保存/添加/关闭）
- [ ] JS alert/prompt消息
- [ ] 角色标签（tag_en字段）
- [ ] 后端错误消息（t_msg字典）
- [ ] 视频页全部文字
- [ ] 示例卡片内容

## 交付物清单

- [ ] `requirements.txt` — Python依赖
- [ ] `start.sh` — 一键启动
- [ ] `.env.example` — 配置模板（无真实密钥）
- [ ] `README.md` — 中英双语使用说明
- [ ] `tar.gz` — 排除 .git/backups/__pycache__/*.pyc

## 安全红线

- [ ] `.env` 不在包内
- [ ] 无 `sk-` 开头的密钥残留
- [ ] MEMORY.md/USER.md/SOUL.md 已清空为模板
- [ ] 无个人身份信息
