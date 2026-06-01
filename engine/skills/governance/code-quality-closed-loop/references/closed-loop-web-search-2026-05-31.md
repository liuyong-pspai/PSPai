# 闭环审计实战：web_search.py v3

> 日期: 2026-05-31 | 阶段: 阶段3交付自审→阶段4深度审计→阶段5进化吸收

## 阶段3：交付自审发现

```bash
# 关1：语法
python3 -m py_compile web_search.py → ✅ 通过

# 关2：裸except扫描
grep -n 'except:' web_search.py → 🔴 6处：
  L37: 气味加载    → fix: json.JSONDecodeError, OSError
  L70: URL解析     → fix: ValueError, Exception
  L196: Bing抓取   → fix: urllib.error.URLError, OSError, socket.timeout
  L281: 百度抓取   → fix: 同上
  L310: Google     → fix: 同上
  L340: 主搜索循环 → fix: Exception

# 关3：硬编码密钥
grep -n 'sk-\|api_key' web_search.py | grep -v '.env' → ✅ 0处
```

## 阶段4：八维审计打分

总分24→43（D→C），P0全部清零。

## 阶段5：进化吸收

### 注入到 swarm-hound-system skill:
- "表面好 ≠ 深层好" 陷阱
- 硬编码污染检查（搜索核心关键词是否被篡改）
- 品牌名冲突黑名单机制
- DGX-1网络限制（仅Bing可用）

### 通用审计规则（可复用）：
- 搜索引擎类代码必过：ⓐ 域名黑名单检查 ⓑ 查询参数完整性 ⓒ 超时策略合理性
- 裸except→具体异常的转换模板：网络类→URLError/OSError/timeout、文件类→OSError/JSONDecodeError、通用兜底→Exception
