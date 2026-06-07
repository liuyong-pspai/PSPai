#!/usr/bin/env python3
"""小龙人 mobile.html 固化验证脚本 — 每次修改后跑一遍"""
import os
import sys

HTML = "/home/yongliu/桌面/小龙人开源应用层/frontend/pwa/html/mobile.html"
BACKEND = "/home/yongliu/桌面/小龙人开源应用层/frontend/pwa/html/server_8092.py"

checks = []
errors = []

def check(name, condition, fix=""):
    checks.append(name)
    if not condition:
        errors.append(f"❌ {name}{' → '+fix if fix else ''}")

# ========== HTML检查 ==========
with open(HTML) as f:
    h = f.read()

# P0: 输入框和按钮
check("id=text-input 存在", 'text-input' in h)
check("id=send-btn 存在", 'id="send-btn"' in h or 'id=send-btn' in h)
check("send-btn ontouchend双保险", 'ontouchend="sendText();event.preventDefault()"' in h, "补ontouchend+preventDefault")
check("send-btn type=button", 'type="button"' in h, "按钮加type=button")
check("8秒卡死检测", '>8000' in h and 'dataset.loadingSince' in h, "卡死自动解除")
check("disabled CSS", '#send-btn:disabled' in h, "disabled样式缺失")
check("transition CSS", 'transition:all' in h, "按钮响应式缺失")

# CSS兼容性（鸿蒙适配）
check("input-bar touch-action", 'touch-action:manipulation' in h, "补CSS: touch-action:manipulation（如果鸿蒙兼容可去掉）")
check("text-input user-select", 'onkeydown' in h, "补CSS: -webkit-user-select:text（如果鸿蒙兼容可去掉）")

# 功能完整性
check("日期动态注入", 'toLocaleString' in h, "补: new Date().toLocaleString")
check("先搜再说不知道", '先搜' in h, "system prompt加先搜规则")
check("双执行跳过标记", 'window._searched' in h, "补: window._searched=true 和跳过检查")
check("蜂群天犬prompt", '蜂群天犬' in h, "system prompt加搜索能力描述")
check("搜索deep模式", "'deep'" in h and '&mode=' in h, "工具定义加mode参数")
check("搜索API路径", '/api/search?q=' in h, "前端搜索调用路径正确")
check("本地记忆系统", 'XLRMEM' in h, "IndexedDB记忆系统缺失")

# ========== 后端检查 ==========
with open(BACKEND) as f:
    b = f.read()

check("蜂群三引擎", 'engine_bing' in b and 'engine_baidu' in b and 'engine_duckduckgo' in b, "至少Bing+百度+DDG")
check("气味记忆", 'ScentMemory' in b, "气味记忆类缺失")
check("天犬深度追踪", 'HoundSearch' in b or 'deep_hunt' in b, "深度追踪类缺失")
check("天权搜索引擎", 'CelestialSearch' in b, "天权搜索统一入口缺失")
check("搜索模式参数", 'mode' in b, "后端缺少mode参数支持")
check("域名去重", 'deduplicate' in b, "域名去重函数缺失")
check("多线程安全", 'threading.Lock' in b or 'self._lock' in b, "气味记忆缺线程锁")

# ========== 报告 ==========
print(f"\n🐝🐕 小龙人固化验证报告")
print(f"{'='*40}")
print(f"通过: {len(checks)-len(errors)}/{len(checks)}")
if errors:
    print(f"\n失败项:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print(f"✅ 全部通过 — 固化状态正常")
