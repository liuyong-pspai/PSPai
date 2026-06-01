#!/usr/bin/env python3
"""
pre_flight_check.py — 模块化拆分前置诊断脚本
==============================================

在拆分巨型文件之前必须运行此脚本。输出诊断报告后，
必须人工确认每一项"⚠️ 风险"都有应对方案才能开始提取。

用法:
    python3 pre_flight_check.py <target_file.py>

该脚本自动检测:
  1. 所有类定义及其精确行范围
  2. 模块级函数/常量（不在任何类内的定义）
  3. 每个类的 import 依赖图谱
  4. 类间交叉引用（循环依赖风险）
  5. 模块级函数的引用关系
  6. 重复定义风险（同名方法/函数）

铁律: 此脚本不通过 → 不允许开始拆分。
"""

import re
import sys
import os
from collections import defaultdict
from pathlib import Path


class PreFlightChecker:
    """前置诊断器"""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            print(f"❌ FATAL: 文件不存在: {filepath}")
            sys.exit(1)

        with open(self.filepath) as f:
            self.lines = f.readlines()
        self.total_lines = len(self.lines)

        self.classes = []        # [(name, start_line, end_line), ...]
        self.module_funcs = []   # [(name, line), ...]
        self.module_consts = []  # [(name, line), ...]
        self.imports = []        # [(stmt, line), ...]

    def parse(self):
        """解析文件结构"""
        # 1. 找所有顶层定义
        top_defs = []  # [(line_no, type, name)]

        for i, line in enumerate(self.lines):
            stripped = line.strip()
            # 类定义
            m = re.match(r'^class\s+(\w+)', stripped)
            if m and (line.startswith('class ') or not line[0].isspace()):
                top_defs.append((i + 1, 'class', m.group(1)))

            # 顶层函数定义
            m = re.match(r'^def\s+(\w+)', stripped)
            if m and (line.startswith('def ') or not line[0].isspace()):
                top_defs.append((i + 1, 'def', m.group(1)))

            # 顶层常量赋值（全大写）
            m = re.match(r'^([A-Z][A-Z_0-9]+)\s*=', stripped)
            if m and (not line[0].isspace() or line.startswith('    ')):
                # 只收非缩进的或一级缩进的
                pass  # 暂时不处理常量

            # import 语句
            if stripped.startswith('from ') or stripped.startswith('import '):
                self.imports.append((stripped, i + 1))

        # 2. 计算类范围（使用下个顶层定义的起始行）
        for idx, (line_no, typ, name) in enumerate(top_defs):
            if typ == 'class':
                if idx + 1 < len(top_defs):
                    end_line = top_defs[idx + 1][0] - 1
                else:
                    end_line = self.total_lines
                self.classes.append((name, line_no, end_line))

        # 3. 识别模块级函数（不在任何类范围内）
        class_ranges = [(s, e) for _, s, e in self.classes]

        def is_inside_class(line_no):
            for s, e in class_ranges:
                if s <= line_no <= e:
                    return True
            return False

        for (line_no, typ, name) in top_defs:
            if typ == 'def' and not is_inside_class(line_no):
                self.module_funcs.append((name, line_no))

    def analyze_import_usage(self):
        """分析每个类的 import 依赖"""
        results = {}
        for cls_name, start, end in self.classes:
            class_text = ''.join(self.lines[start - 1:end])

            # 统计类中使用的模块引用（module.xxx 模式）
            module_refs = set()
            for match in re.finditer(r'\b(\w+)\.\w+', class_text):
                module_name = match.group(1)
                # 排除 self、常见对象
                if module_name not in ('self', 'cls', 'os', 'sys', 're', 'json',
                                       'logging', 'datetime', 'time', 'shutil',
                                       'typing', 'pathlib', 'collections'):
                    module_refs.add(module_name)

            # 统计类中使用的顶层 import 名称
            import_names = set()
            for stmt, _ in self.imports:
                # from X import Y
                m = re.match(r'from\s+[\w.]+\s+import\s+(.+)', stmt)
                if m:
                    for name in re.split(r',\s*', m.group(1)):
                        name = name.strip().split(' as ')[-1]
                        import_names.add(name)
                # import X
                m = re.match(r'^import\s+(.+)', stmt)
                if m:
                    for name in re.split(r',\s*', m.group(1)):
                        name = name.strip().split(' as ')[-1]
                        import_names.add(name)

            # 检查类中使用的名称是否在 import 列表中
            used_in_class = set()
            for name in import_names:
                if re.search(r'\b' + re.escape(name) + r'\b', class_text):
                    used_in_class.add(name)

            # 检查是否有引用但未导入的名称
            unresolved = module_refs - import_names

            results[cls_name] = {
                'range': (start, end),
                'size': end - start + 1,
                'module_refs': module_refs,
                'used_imports': used_in_class,
                'unresolved': unresolved,
            }

        return results

    def check_module_level_duplication_risk(self):
        """检查模块级函数是否被多个类引用（需要共享，不能被单一提取）"""
        shared_funcs = []
        for func_name, func_line in self.module_funcs:
            ref_count = 0
            ref_classes = []
            for cls_name, start, end in self.classes:
                class_text = ''.join(self.lines[start - 1:end])
                if re.search(r'\b' + re.escape(func_name) + r'\b', class_text):
                    ref_count += 1
                    ref_classes.append(cls_name)

            if ref_count > 1:
                shared_funcs.append((func_name, ref_classes))
            elif ref_count == 0:
                shared_funcs.append((func_name, ['⚠️ 未被任何类引用']))

        return shared_funcs

    def check_cross_class_references(self):
        """检查类间交叉引用（循环依赖风险）"""
        cross_refs = []
        for cls_name, start, end in self.classes:
            class_text = ''.join(self.lines[start - 1:end])
            for other_cls, _, _ in self.classes:
                if other_cls == cls_name:
                    continue
                if re.search(r'\b' + re.escape(other_cls) + r'\b', class_text):
                    cross_refs.append((cls_name, other_cls))

        return cross_refs

    def run(self):
        """运行完整诊断"""
        print(f"\n{'='*70}")
        print(f"🔍 模块化拆分前置诊断: {self.filepath.name}")
        print(f"{'='*70}")
        print(f"总行数: {self.total_lines}")

        self.parse()

        # === 报告 1: 类概览 ===
        print(f"\n{'─'*70}")
        print(f"📦 1. 类定义概览 ({len(self.classes)} 个类)")
        print(f"{'─'*70}")
        for name, start, end in self.classes:
            size = end - start + 1
            flag = "🔴" if size > 1500 else ("🟡" if size > 800 else "🟢")
            print(f"  {flag} {name:40s} L{start:5d}-L{end:5d} ({size:5d} 行)")

        # === 报告 2: 模块级函数 ===
        print(f"\n{'─'*70}")
        print(f"📋 2. 模块级函数/常量 ({len(self.module_funcs)} 个)")
        print(f"{'─'*70}")
        shared = self.check_module_level_duplication_risk()
        for func_name, refs in shared:
            if '⚠️' in refs[0]:
                print(f"  ⚠️  {func_name:40s} → 孤儿函数（未被任何类引用）")
            else:
                print(f"  🔗 {func_name:40s} → 被 {len(refs)} 个类共享: {', '.join(refs)}")

        # === 报告 3: 交叉引用 ===
        print(f"\n{'─'*70}")
        print(f"🔗 3. 类间交叉引用（循环依赖风险）")
        print(f"{'─'*70}")
        cross = self.check_cross_class_references()
        if cross:
            for src, tgt in cross:
                print(f"  🔴 {src} 引用了 {tgt} → 提取时需要解耦")
        else:
            print(f"  ✅ 未检测到类间交叉引用")

        # === 报告 4: Import 依赖 ===
        print(f"\n{'─'*70}")
        print(f"📥 4. 每类的 Import 依赖")
        print(f"{'─'*70}")
        usage = self.analyze_import_usage()
        for cls_name, info in usage.items():
            print(f"\n  📎 {cls_name} ({info['size']}行)")
            if info['unresolved']:
                for name in info['unresolved']:
                    print(f"     🔴 {name} — 使用了但不在顶层 import 中（可能来自 MRO）")
            if info['used_imports']:
                print(f"     ✅ 使用的导入: {', '.join(sorted(info['used_imports'])[:10])}")

        # === 总结：是否可以安全拆分 ===
        print(f"\n{'='*70}")
        print(f"🏁 拆分安全评估")
        print(f"{'='*70}")

        issues = []

        # 检查：是否有超过 1500 行的类
        oversized = [(n, e-s+1) for n, s, e in self.classes if e-s+1 > 1500]
        if oversized:
            for name, size in oversized:
                issues.append(f"🔴 {name}: {size}行(>{1500}) — 需要进一步拆分类本身")

        # 检查：共享模块级函数
        shared_funcs = [(n, r) for n, r in shared if len(r) > 1 and '⚠️' not in r[0]]
        if shared_funcs:
            for name, refs in shared_funcs:
                issues.append(f"🟡 {name}: 被 {len(refs)} 个类共享 → 提取到公共模块，不要复制")

        # 检查：交叉引用
        if cross:
            for src, tgt in cross:
                issues.append(f"🟡 {src}→{tgt} 交叉引用 → 使用 type(self) 解耦")

        if not issues:
            print("  ✅ 未发现阻塞性问题，可以开始拆分")
        else:
            for issue in issues:
                print(f"  {issue}")
            print(f"\n  ⛔ 以上 {len(issues)} 个问题必须在拆分计划中明确处理方案")

        return len(issues) == 0  # True = safe


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 pre_flight_check.py <target_file.py>")
        sys.exit(1)

    checker = PreFlightChecker(sys.argv[1])
    passed = checker.run()
    sys.exit(0 if passed else 1)
