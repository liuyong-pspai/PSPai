#!/usr/bin/env python3
"""上传v2.0.0 zip到Gitee Release"""
import urllib.request, json, os

GITEE_TOKEN = "70b927d52f0f8970e14adfc57c4efb72"
auth = __import__('base64').b64encode(f'lii-the-unyielding:{GITEE_TOKEN}'.encode()).decode()
zip_path = os.path.expanduser("~/桌面/小龙人开源应用层/xiaolongren-desktop-v2.0.0.zip")

# 删除旧Release
try:
    check = urllib.request.Request(
        "https://gitee.com/api/v5/repos/lii-the-unyielding/xiaolongren/releases/tags/v2.0.0",
        headers={"Authorization": f"Basic {auth}"}
    )
    resp = urllib.request.urlopen(check, timeout=10)
    existing = json.loads(resp.read())
    if existing.get("id"):
        del_req = urllib.request.Request(
            f"https://gitee.com/api/v5/repos/lii-the-unyielding/xiaolongren/releases/{existing['id']}",
            data=b'', headers={"Authorization": f"Basic {auth}"}, method="DELETE"
        )
        urllib.request.urlopen(del_req, timeout=10)
        print(f"✅ 删除旧Release #{existing['id']}")
except:
    pass

# 创建Release
data = json.dumps({
    "tag_name": "v2.0.0",
    "name": "🐉 小龙人 v2.0.0 — 三系统电脑版",
    "body": "三系统一键安装：Windows/Linux/macOS 桌面图标+卸载脚本\n安全审计24个漏洞已修复",
}).encode()
req = urllib.request.Request(
    "https://gitee.com/api/v5/repos/lii-the-unyielding/xiaolongren/releases",
    data=data, headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req, timeout=15)
rel_id = json.loads(resp.read()).get("id","")
print(f"✅ Release #{rel_id} 已创建")

# 上传zip
import io
with open(zip_path, "rb") as f:
    zip_data = f.read()
boundary = "----Boundary"
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"xiaolongren-desktop-v2.0.0.zip\"\r\nContent-Type: application/zip\r\n\r\n").encode() + zip_data + f"\r\n--{boundary}--\r\n".encode()

a_req = urllib.request.Request(
    f"https://gitee.com/api/v5/repos/lii-the-unyielding/xiaolongren/releases/{rel_id}/attach_files",
    data=body, headers={"Authorization": f"Basic {auth}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
)
urllib.request.urlopen(a_req, timeout=600)
print("✅ Gitee上传完成!")
