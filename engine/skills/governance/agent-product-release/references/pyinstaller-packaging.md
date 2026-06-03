# PyInstaller 打包闭源内核

> 2026-06-01 小龙人 pspai_server.py 实战

## 适用场景

当内核入口依赖框架运行时（如 pspai_server.py 依赖 `~/hermes-agent`），打包为独立二进制。客户需预装框架运行时，但 Python 源码不可见。

## 基础命令

```bash
cd <闭源核心目录>
pyinstaller --onefile --name <输出名> \
  --add-data "config.yaml:." \
  --add-data "skills:skills" \
  --add-data "scripts:scripts" \
  --add-data "local_module.py:." \
  --hidden-import yaml \
  --hidden-import <框架模块1> \
  --hidden-import <框架模块2> \
  <入口.py>
```

## 参数说明

| 参数 | 作用 |
|:---|:---|
| `--onefile` | 打包为单个ELF二进制 |
| `--name` | 输出文件名 |
| `--add-data "源:目标"` | 将数据目录/文件打包进二进制，运行时解压到临时目录 |
| `--hidden-import` | 显式声明隐式导入（框架依赖等） |

## 实战案例：小龙人

```bash
cd "/home/yongliu/桌面/小龙人闭源核心"
pyinstaller --onefile --name xiaolongren-engine \
  --add-data "config.yaml:." \
  --add-data "skills:skills" \
  --add-data "scripts:scripts" \
  --add-data "pspai_search.py:." \
  --hidden-import yaml \
  --hidden-import hermes_cli.env_loader \
  --hidden-import run_agent \
  pspai_server.py
```

结果：`dist/xiaolongren-engine`（8.5MB，ARM64 ELF）

## 注意事项

- `--hidden-import` 找不到的模块只会产生 WARNING，不会阻塞构建
- 框架依赖（如 Hermes）仍需客户预装，二进制不包含框架本体
- 构建后删除 `build/` 和 `.spec` 文件保持目录干净
- 分平台编译：ARM64/Linux 二进制不能在 x86_64 上运行
- **PyInstaller 不支持跨平台编译** — `--target-architecture` 仅限 macOS，Linux/Windows 必须各自原生环境编译
- **本地编译超时** — Hermes 终端超时限制会截断 PyInstaller（2-5分钟），走 CI 或让用户手动执行
- **config.yaml 不打包** — 代码必须实现 `CWD/config.yaml` 优先、`BASE_DIR/config.yaml` 兜底的加载模式

## config.yaml 外置加载模式

发布时 config.yaml 作为独立文件随二进制分发，客户可编辑：

```python
# pspai_server.py
BASE_DIR = Path(__file__).parent

# 优先当前目录（客户可编辑），兜底同目录（PyInstaller内）
_config_paths = [
    Path.cwd() / 'config.yaml',
    BASE_DIR / 'config.yaml',
]
CONFIG = {}
for _cp in _config_paths:
    if _cp.exists():
        with open(_cp) as f:
            CONFIG = yaml.safe_load(f)
        break
```

PyInstaller 构建时 **排除** config.yaml：
```bash
pyinstaller --onefile --name xiaolongren-engine \
  --add-data "skills:skills" \
  --add-data "scripts:scripts" \
  pspai_server.py
# 注意：没有 --add-data "config.yaml:."
```
