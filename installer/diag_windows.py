#!/usr/bin/env python3
"""Windows构建诊断——最小化测试"""
import os, sys, shutil
from pathlib import Path

print(f"Python: {sys.executable}")
print(f"Platform: {sys.platform}")
print(f"CWD: {os.getcwd()}")
print(f"PATH: {os.environ.get('PATH', '')[:200]}")

# Test 1: 检查文件
repo = Path(".")
print(f"\n=== 文件检查 ===")
for f in ["UI原型", "launcher.py", "installer/make_installer.py", "engine/dist"]:
    p = repo / f
    print(f"  {f}: exists={p.exists()}, is_dir={p.is_dir() if p.exists() else 'N/A'}")

# Test 2: 检查引擎
engine_candidates = [
    "engine/dist/xiaolongren-engine-windows.exe",
    "xiaolongren-engine-windows.exe",
]
for c in engine_candidates:
    p = repo / c
    print(f"  Engine {c}: exists={p.exists()}, size={p.stat().st_size if p.exists() else 0}")

# Test 3: 复制测试
print(f"\n=== 复制测试 ===")
try:
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    src = repo / "UI原型"
    if src.exists():
        shutil.copytree(src, tmp / "frontend", dirs_exist_ok=True)
        count = sum(1 for _ in (tmp / "frontend").rglob("*") if _.is_file())
        print(f"  UI原型 -> frontend: OK ({count} files)")
    else:
        print(f"  UI原型: NOT FOUND")
    shutil.rmtree(tmp)
except Exception as e:
    print(f"  复制失败: {e}")

# Test 4: launcher.py
launcher = repo / "launcher.py"
if launcher.exists():
    print(f"  launcher.py: OK ({launcher.stat().st_size}B)")
else:
    print(f"  launcher.py: NOT FOUND")

# Test 5: 创建zip
print(f"\n=== ZIP测试 ===")
try:
    import tempfile, zipfile
    tmp = Path(tempfile.mkdtemp())
    (tmp / "test.txt").write_text("hello")
    zip_path = repo / "dist" / "test.zip"
    zip_path.parent.mkdir(exist_ok=True)
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(tmp))
    print(f"  ZIP created: {zip_path.stat().st_size}B")
    shutil.rmtree(tmp)
    zip_path.unlink()
except Exception as e:
    print(f"  ZIP失败: {e}")

print(f"\n=== 诊断完成 ===")
