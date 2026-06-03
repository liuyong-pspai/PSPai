# 发布前品牌审计（敏感词扫描）

> 发布前必须执行。开源包中不得出现底层技术栈名称。

## 禁止词清单

| 类别 | 禁止词 | 例外（闭源包内部可含） |
|---|---|---|
| 框架名 | Hermes, hermes | 闭源config.yaml/toolsets中功能引用 |
| 模型厂商 | DeepSeek, OpenAI, Anthropic, Claude | 闭源config.yaml中的provider/model配置 |
| 技术术语 | LLM, middleware, deployment, open-source ecosystem | 无 |
| 个人信息 | 真实姓名/路径/密钥/AppID | 无 |

## 五步流程

### 1. 解包扫描
```python
import tarfile, re
patterns = {
    'DeepSeek': r'(?i)\bdeepseek\b',
    'Hermes': r'(?i)\bhermes\b',
    'OpenAI': r'(?i)\bopenai\b',
    'Anthropic': r'(?i)\banthropic\b',
    'Claude': r'(?i)\bclaude\b',
    'LLM': r'\bLLM\b',
}
with tarfile.open('package.tar.gz') as tar:
    for m in tar.getmembers():
        content = tar.extractfile(m).read().decode('utf-8', errors='replace')
        for label, pat in patterns.items():
            if re.findall(pat, content):
                print(f'⚠️ [{label}] {m.name}')
```

### 2. 重点文件逐行检查
- `.env.example` → 变量名不能含 DEEPSEEK/OPENAI → 用 `PSPAI_API_KEY`
- `start.sh` → 提示文字不能含模型厂商名
- `index.html` → 模型选择器不能显示 "DeepSeek V4" → 显示 "PSPAI Engine"
- `lang/*.json` → 翻译中不能含示例厂商名（如 "例如：Claude 4"）
- `README.md` → 安装说明不能出现 "DeepSeek API Key"

### 3. 语言包key同步检查
HTML 引用 `pspai_desc` 但 JSON 中只有旧 `ds_desc` → 翻译显示空白。
改 model ID 或 descKey 时必须同步更新所有语言包的对应 key。

### 4. 平台连通验证
- 飞书 app_id/app_secret 不能硬编码在开源包中 → 全部用 `${ENV_VAR}`
- config.yaml 中外置平台的 secret 必须用环境变量引用

### 5. 修复后重新打包+复检
```python
# 修复 → 删除旧包 → 重新打包 → 重新扫描 → 零泄露才算通过
```

## .env.example 变量命名规范

| ❌ 旧命名 | ✅ 新命名 |
|---|---|
| `DEEPSEEK_API_KEY` | `PSPAI_API_KEY` |
| `OPENAI_API_KEY` | `PSPAI_API_KEY` |
| 注释"获取地址: https://platform.deepseek.com" | 注释"小龙人引擎需要一个API Key才能运行" |

## 常见修复案例

**index.html 模型名暴露：**
```javascript
// ❌
{id:'ds', name:'DeepSeek V4', descKey:'ds_desc', ...}
// ✅
{id:'pspai', name:'PSPAI Engine', descKey:'pspai_desc', ...}
```

**start.sh 提示泄露：**
```bash
# ❌
echo "请填入 DeepSeek API Key"
# ✅
echo "请填入 API Key"
```

**lang文件示例泄露：**
```json
// ❌
"addm_name": "模型名称（如：Claude 4）"
// ✅
"addm_name": "模型名称"
```
