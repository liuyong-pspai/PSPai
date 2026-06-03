"""
PSPAI 网络搜索工具 — 百度优先 + HN Algolia 备用
免API Key，直接可用
"""
import json
import urllib.request
import urllib.parse
import re
import html as html_mod


def web_search(query: str, limit: int = 5) -> str:
    """搜索网络，返回JSON结果。百度优先（中文快），HN备用。"""
    results = []

    # 1. 百度搜索
    try:
        url = f"https://www.baidu.com/s?wd={urllib.request.quote(query)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36",
            "Accept": "text/html",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode('utf-8', errors='ignore')

        # 提取所有结果链接（过滤导航/广告）
        links = re.findall(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', content, re.DOTALL)
        seen_urls = set()
        for href, text in links:
            # 跳过百度内部链接和导航
            if 'baidu.com' in href or 'bilibili.com' in href:
                continue
            text = re.sub(r'<[^>]+>', '', text).strip()
            text = html_mod.unescape(text)
            if text and len(text) > 6 and len(text) < 200 and text not in seen_urls:
                # 过滤明显广告/导航词
                skip_words = ['登录', '注册', '首页', '下一页', '百度', '地图', '视频', '图片', '更多', '设置']
                if any(text == w for w in skip_words):
                    continue
                seen_urls.add(text)
                results.append({
                    "title": text,
                    "url": href,
                    "description": f"来自 {href.split('/')[2]}",
                })
                if len(results) >= limit:
                    break

        # 补：h3标题
        if len(results) < 2:
            h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL)
            for block in h3s:
                text = re.sub(r'<[^>]+>', '', block).strip()
                text = html_mod.unescape(text)
                if text and len(text) > 5 and text not in seen_urls and '百度' not in text:
                    seen_urls.add(text)
                    results.append({
                        "title": text,
                        "url": f"https://www.baidu.com/s?wd={urllib.request.quote(text[:50])}",
                        "description": "百度搜索",
                    })
                    if len(results) >= limit:
                        break

    except Exception as e:
        print(f"[PSPAI Search] 百度搜索失败: {e}")

    # 2. Hacker News API（英文/技术类，备用）
    if len(results) < limit:
        try:
            url = f"https://hn.algolia.com/api/v1/search_by_date?query={urllib.request.quote(query)}&tags=story&hitsPerPage={limit - len(results)}"
            req = urllib.request.Request(url, headers={"User-Agent": "PSPAI/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
            for h in data.get('hits', []):
                results.append({
                    "title": h.get('title', ''),
                    "url": h.get('url', f"https://news.ycombinator.com/item?id={h.get('objectID', '')}"),
                    "description": f"HN · {h.get('points', 0)}pts",
                })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"[PSPAI Search] HN搜索失败: {e}")

    return json.dumps({"success": len(results) > 0, "data": {"web": results[:limit]}}, ensure_ascii=False)


# 注册到Hermes工具注册表
try:
    from tools.registry import registry
    registry.register(
        name="web_search",
        toolset="web",
        schema={
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for current information using Baidu (Chinese) and Hacker News (English). Returns URLs, titles, and descriptions. Use this to get real-time news and information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query (Chinese or English)"},
                        "limit": {"type": "integer", "description": "Max results (default 5)"}
                    },
                    "required": ["query"]
                }
            }
        },
        handler=lambda args, **kw: web_search(args.get("query", ""), args.get("limit", 5)),
        check_fn=lambda: True,
        emoji="🔍",
        max_result_size_chars=100_000,
    )
    print("PSPAI web_search registered successfully")
except Exception as e:
    print(f"Registration error: {e}")
