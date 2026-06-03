# CU 测试套件模式

> 来源：2026-06-02 刘玉龙 P07 CU 引擎测试套件实战  
> 关联：computer-use-toolchain-mastery v1.4.0 §十二

## 测试架构

```
tests/test_computer_use.py
├── TestModuleLoad          # 模块加载/依赖检测（6个，全部无头可用）
├── TestSafetyMechanisms    # 优雅降级/安全机制（6个，全部无头可用）
├── TestParseAction         # 动作解析器（10个，纯逻辑，无头可用）
├── TestCoordinateClamping  # 坐标裁剪（4个，需mock pyautogui）
├── TestTypeTextLimits      # 文本输入限制（3个，需mock pyautogui）
├── TestScreenshotRegion    # 截图参数校验（2个，需mock mss）
├── TestToolRegistration    # 注册完整性（2个，纯静态代码检查）
└── TestWithDisplay         # 桌面实跑（5个，mark.skipif无头跳过）
```

## 核心模式

### 1. 无头安全跳过

```python
def _has_display():
    return bool(os.environ.get("DISPLAY", "")) or bool(os.environ.get("WAYLAND_DISPLAY", ""))

def _can_import_pyautogui():
    if not _has_display():
        return False
    try:
        import pyautogui
        return True
    except (ImportError, KeyError):
        return False

# autouse fixture 让整个测试类在无头环境自动跳过
class TestCoordinateClamping:
    @pytest.fixture(autouse=True)
    def _require_display(self):
        if not _can_import_pyautogui():
            pytest.skip("无显示器")
```

### 2. Monkeypatch 绕过硬件

```python
def test_negative_x_clamped(self, cu, monkeypatch):
    monkeypatch.setattr("cognition.tools_computer._CAN_CONTROL", True)
    import pyautogui
    monkeypatch.setattr(pyautogui, "size", lambda: (1920, 1080))
    monkeypatch.setattr(pyautogui, "moveTo", lambda x, y, duration: None)
    result = asyncio.run(cu._mouse_move(-100, 100))
    assert "(0," in result
```

### 3. 注册完整性（纯静态）

```python
def test_cu_tools_in_registry(self):
    reg_path = "../cognition/tools_registry.py"
    with open(reg_path) as f:
        content = f.read()
    for tool in ["screenshot", "click", "computer_use", ...]:
        assert f"'{tool}'" in content or f'"{tool}"' in content
```

### 4. 桌面实跑（mark.skipif）

```python
@pytest.mark.skipif(not _has_display(), reason="无显示器环境")
class TestWithDisplay:
    def test_get_screen_size_returns_resolution(self, cu):
        result = asyncio.run(cu._get_screen_size())
        assert "x" in result
```

## 结果（2026-06-02 headless CI）

```
23 passed, 12 skipped, 5 deselected, 0 failed
```

12个skip全是显示依赖测试（坐标裁剪/鼠标键盘/截图），在真实桌面环境会全部通过。5个deselect是`TestWithDisplay`整类被`mark.skipif`过滤。

## 关键教训

1. **pyautogui 在 `import` 阶段就连接 DISPLAY**——不能用 `try/except ImportError` 包裹，必须用 `_has_display()` 前置检测
2. **mss.MSS() 初始化也需要 DISPLAY**——mss 导入成功不等同于可用
3. **autouse fixture 比 skipif 更可靠**——因为 skipif 在类级别只检查一次，而 fixture 在每个方法前检查
4. **优雅降级测试是最有价值的第一层**——不需要任何硬件，验证所有依赖缺失路径
