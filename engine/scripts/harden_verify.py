#!/usr/bin/env python3
"""
harden_verify.py — 硬化验证脚本框架
code-quality-closed-loop 关6 TDD原型

用法: python3 harden_verify.py <文件路径>
输出: [文件名]: [PASS/FAIL] 详细报告

七项检查:
  1. 语法: py_compile 通过
  2. 零裸except: 无 `except:` 或 `except Exception` 无日志
  3. 零print: 无裸 print 调用（除 `if __name__`）
  4. 零硬编码密钥: 无 sk- / api_key 明文
  5. 类型安全: 每个 def 有 type hints
  6. 防御性编程: 外部调用有 timeout
  7. 产出结构化: 函数返回 dict/DataClass
"""
import sys
import ast
import os
import re
import py_compile
from pathlib import Path
from datetime import datetime


CHECK_NAMES = [
    "语法验证",
    "零裸except",
    "零print残留",
    "零硬编码密钥",
    "类型安全",
    "防御性编程",
    "产出结构化",
]


def check_syntax(filepath: str) -> tuple[bool, str]:
    """检查1: py_compile（仅.py文件）"""
    if not filepath.endswith('.py'):
        return True, "跳过（非Python文件）"
    try:
        py_compile.compile(filepath, doraise=True)
        return True, "语法通过"
    except py_compile.PyCompileError as e:
        return False, str(e)


def check_bare_except(filepath: str) -> tuple[bool, str]:
    """检查2: 零裸except — 只抓真正的吞错（except: pass 或 except Exception: pass）"""
    import ast as ast_module
    issues = []
    with open(filepath) as f:
        source = f.read()
    try:
        tree = ast_module.parse(source)
        for node in ast_module.walk(tree):
            if isinstance(node, ast_module.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        issues.append(f"L{handler.lineno}: bare except:")
                    elif isinstance(handler.type, ast_module.Name) and handler.type.id == 'Exception':
                        # Check if body has return/yield/log — if so, error is surfaced
                        has_return = any(isinstance(s, (ast_module.Return, ast_module.Yield)) for s in handler.body)
                        has_log = any('logger' in ast_module.dump(s) for s in handler.body)
                        if not has_return and not has_log:
                            issues.append(f"L{handler.lineno}: except Exception吞错")
    except SyntaxError:
        return False, "语法错误，跳过检查"
    if issues:
        return False, "; ".join(issues[:5])
    return True, "通过"


def check_print(filepath: str) -> tuple[bool, str]:
    """检查3: 零print残留（排除 __main__ 块和注释）"""
    issues = []
    with open(filepath) as f:
        lines = f.readlines()
    in_main = False
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith('#'):
            continue
        if 'if __name__' in s and '__main__' in s:
            in_main = True
            continue
        if re.search(r'\bprint\s*\(', line) and not in_main:
            issues.append(f"L{i}: {line.strip()[:60]}")
    if issues:
        return False, f"{len(issues)}处print"
    return True, "通过"


def check_hardcoded_secret(filepath: str) -> tuple[bool, str]:
    """检查4: 零硬编码密钥"""
    issues = []
    with open(filepath) as f:
        for i, line in enumerate(f, 1):
            if re.search(r'(sk-[a-zA-Z0-9]{20,}|api_key\s*=\s*["\'][a-zA-Z0-9_-]{8,})', line, re.IGNORECASE):
                if '.env' not in line and 'environ' not in line and '${' not in line:
                    issues.append(f"L{i}: 疑似硬编码密钥")
    if issues:
        return False, "; ".join(issues[:3])
    return True, "通过"


def check_type_hints(filepath: str) -> tuple[bool, str]:
    """检查5: 类型安全"""
    no_hints = []
    with open(filepath) as f:
        for i, line in enumerate(f, 1):
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*:', line):
                if '->' not in line:
                    no_hints.append(f"L{i}: {line.strip()[:60]}")
    total = len(no_hints)
    if total > 0:
        return False, f"{total}个函数缺type hints"
    return True, "通过"


def check_defensive(filepath: str) -> tuple[bool, str]:
    """检查6: 防御性编程"""
    with open(filepath) as f:
        content = f.read()
    has_timeout = bool(re.search(r'timeout\s*=', content))
    has_try = bool(re.search(r'\btry\s*:', content))
    has_subprocess = 'subprocess' in content
    has_requests = 'requests' in content or 'httpx' in content
    if not has_timeout and (has_subprocess or has_requests):
        return False, "外部调用缺少timeout"
    return True, "通过" if has_timeout else "通过（无外部调用）"


def check_structured_return(filepath: str) -> tuple[bool, str]:
    """检查7: 产出结构化"""
    returns_dict = 0
    returns_str = 0
    with open(filepath) as f:
        for line in f:
            if re.match(r'\s*return\s*\{', line):
                returns_dict += 1
            if re.match(r'\s*return\s+f?["\']', line):
                returns_str += 1
    if returns_str > returns_dict and returns_str > 0:
        return False, f"返回字符串({returns_str}次)多于dict({returns_dict}次)"
    return True, "通过"


CHECKS = [
    check_syntax,
    check_bare_except,
    check_print,
    check_hardcoded_secret,
    check_type_hints,
    check_defensive,
    check_structured_return,
]


def verify(filepath: str) -> dict:
    """主验证函数"""
    results = {}
    passed = 0
    failed = 0

    for i, check_fn in enumerate(CHECKS):
        name = CHECK_NAMES[i]
        ok, detail = check_fn(filepath)
        results[name] = {"ok": ok, "detail": detail}
        if ok:
            passed += 1
        else:
            failed += 1

    return {
        "file": filepath,
        "passed": passed,
        "failed": failed,
        "total": len(CHECKS),
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }


def report(result: dict) -> str:
    """格式化报告"""
    lines = []
    status = "✅ PASS" if result["failed"] == 0 else f"❌ FAIL ({result['failed']}/{result['total']})"
    lines.append(f"[{os.path.basename(result['file'])}]: {status}")
    lines.append(f"  时间: {result['timestamp']}")
    lines.append(f"  通过: {result['passed']}/{result['total']}")
    lines.append("")

    for name in CHECK_NAMES:
        r = result["results"].get(name, {})
        icon = "✅" if r.get("ok") else "❌"
        lines.append(f"  {icon} {name}: {r.get('detail', 'N/A')}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 harden_verify.py <文件路径>")
        sys.exit(1)

    target = sys.argv[1]
    if not os.path.isfile(target):
        print(f"❌ 文件不存在: {target}")
        sys.exit(1)

    result = verify(target)
    print(report(result))
    sys.exit(0 if result["failed"] == 0 else 1)
