#!/usr/bin/env python3
"""
post_split_audit.py — 拆分后审计脚本（Dimension 1 + 8 自动化版）
==============================================================

在模块化拆分完成后必须运行此脚本。检查:
  1. 重复类/函数定义 — 模块级代码误收
  2. 重复 import 块 — 每个子模块都复制了公共导入
  3. Mixin 文件缺少的 import — 方法所需的模块未导入 (Trap 4)
  4. ParentClass.static_attr 引用 — 循环导入风险 (Trap 5)
  5. 骨架文件 Mixin 组合完整性 — 是否遗漏子模块

用法:
    python3 post_split_audit.py <skeleton_file.py> <submodule_pattern>

示例:
    python3 post_split_audit.py cognition/memory_new.py "cognition/memory_l*.py"

铁律: 此脚本不通过 → 禁止提交/继续下一步。
"""

import re
import sys
import os
from collections import defaultdict
from pathlib import Path
import glob


class PostSplitAuditor:
    """拆分后审计器"""

    def __init__(self, skeleton_path: str, submodule_pattern: str):
        self.skeleton_path = Path(skeleton_path)
        self.submodule_files = sorted(glob.glob(submodule_pattern))

        if not self.skeleton_path.exists():
            print(f"❌ FATAL: 骨架文件不存在: {skeleton_path}")
            sys.exit(1)

        if not self.submodule_files:
            print(f"❌ FATAL: 未找到匹配的子模块: {submodule_pattern}")
            sys.exit(1)

        print(f"🔍 审计目标:")
        print(f"   骨架: {self.skeleton_path}")
        print(f"   子模块: {len(self.submodule_files)} 个文件")

        # 读取所有文件
        self.skeleton_lines = self._read_lines(self.skeleton_path)
        self.submodules = {}
        for f in self.submodule_files:
            self.submodules[f] = self._read_lines(f)

    def _read_lines(self, path):
        with open(path) as f:
            return f.readlines()

    def _find_definitions(self, lines, def_type='class'):
        """找所有顶层定义"""
        results = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if def_type == 'class':
                m = re.match(r'^class\s+(\w+)', stripped)
            else:
                m = re.match(r'^def\s+(\w+)', stripped)

            if m and (not line[0].isspace() or line.startswith(def_type + ' ')):
                results.append((i + 1, m.group(1)))
        return results

    def check_1_duplicated_classes(self):
        """
        检查 1: 重复类定义
        同一个类不应该出现在多个子模块中。
        """
        print(f"\n{'─'*70}")
        print(f"🔴 检查 1: 重复类定义")
        print(f"{'─'*70}")

        all_classes = defaultdict(list)
        for filepath, lines in self.submodules.items():
            fname = Path(filepath).name
            classes = self._find_definitions(lines, 'class')
            for line_no, cls_name in classes:
                all_classes[cls_name].append((fname, line_no))

        issues = []
        for cls_name, occurrences in all_classes.items():
            if len(occurrences) > 1:
                locs = ', '.join([f"{f}:L{ln}" for f, ln in occurrences])
                issues.append(f"  🔴 {cls_name} 出现在 {len(occurrences)} 个文件中: {locs}")

        if issues:
            print(f"  ❌ 发现 {len(issues)} 个重复类定义:")
            for issue in issues:
                print(issue)
            print(f"\n  💡 修复: 类应只出现在一个文件中。提取为 Mixin 后原始文件的类应变为组合骨架。")
            return False
        else:
            print(f"  ✅ 无重复类定义")
            return True

    def check_2_duplicated_functions(self):
        """
        检查 2: 重复模块级函数
        辅助函数如 _mkdir, mem_shanghai_now 不应被复制到每个子模块。
        """
        print(f"\n{'─'*70}")
        print(f"🔴 检查 2: 重复模块级函数")
        print(f"{'─'*70}")

        all_funcs = defaultdict(list)
        for filepath, lines in self.submodules.items():
            fname = Path(filepath).name
            funcs = self._find_definitions(lines, 'def')
            for line_no, func_name in funcs:
                all_funcs[func_name].append((fname, line_no))

        issues = []
        for func_name, occurrences in all_funcs.items():
            if len(occurrences) > 1 and not func_name.startswith('__'):
                locs = ', '.join([f"{f}:L{ln}" for f, ln in occurrences])
                issues.append(f"  🔴 {func_name} 出现 {len(occurrences)} 次: {locs}")

        if issues:
            print(f"  ❌ 发现 {len(issues)} 个重复函数定义:")
            for issue in issues[:10]:  # 只显示前10个
                print(issue)
            if len(issues) > 10:
                print(f"  ... 还有 {len(issues)-10} 个")
            print(f"\n  💡 修复: 共享函数提取到 xxx_helpers.py，各子模块从该文件导入。")
            return False
        else:
            print(f"  ✅ 无重复函数定义")
            return True

    def check_3_duplicated_imports(self):
        """
        检查 3: 重复 import 块
        相同的大段 import 出现在每个子模块中 = 模块级代码误收。
        """
        print(f"\n{'─'*70}")
        print(f"🟡 检查 3: 重复 import 块")
        print(f"{'─'*70}")

        # 从每个子模块收集 import 语句
        import_sets = {}
        for filepath, lines in self.submodules.items():
            fname = Path(filepath).name
            imports = tuple(
                l.strip() for l in lines
                if l.strip().startswith('from ') or l.strip().startswith('import ')
            )
            import_sets[fname] = imports

        # 检查是否有 ≥3 个文件共享相同的 import 集合
        if len(import_sets) < 2:
            print(f"  ✅ 只有一个子模块，无需检查重复导入")
            return True

        from collections import Counter
        import_counter = Counter(import_sets.values())
        issues = []
        for imports_tuple, count in import_counter.most_common():
            if count >= 3 and len(imports_tuple) >= 5:
                affected = [f for f, im in import_sets.items() if im == imports_tuple]
                issues.append(
                    f"  🟡 相同 import 块 ({len(imports_tuple)}条) 出现在 {count} 个文件中: "
                    f"{', '.join(affected[:3])}{'...' if len(affected) > 3 else ''}"
                )

        if issues:
            print(f"  ⚠️ 发现大段重复导入:")
            for issue in issues:
                print(issue)
            print(f"\n  💡 评估: 如果这些 import 是该子模块独有的依赖 → 可接受。")
            print(f"         如果多个子模块需要相同的共享函数 → 提取公共导入到 helpers 文件。")
            # 不阻塞，因为某些重复导入是合理的
            return True
        else:
            print(f"  ✅ 无明显的大段重复导入")
            return True

    def check_4_missing_imports(self):
        """
        检查 4: Mixin 文件缺少的 import (Trap 4)
        方法中使用了 logging.info / json.loads 等，但文件顶部没有对应 import。
        """
        print(f"\n{'─'*70}")
        print(f"🔴 检查 4: Mixin 文件 Import 完整性 (Trap 4)")
        print(f"{'─'*70}")

        # 标准库模块名 → 典型调用模式
        KNOWN_PATTERNS = {
            'logging': [r'\blogging\.', r'\blogger\.', r'\blog\.'],
            'json': [r'\bjson\.(loads|dumps|load|dump)\b'],
            'os': [r'\bos\.(path|environ|makedirs|listdir|remove|rename|getcwd)\b'],
            're': [r'\bre\.(match|search|sub|compile|findall|split)\b'],
            'time': [r'\btime\.(time|sleep|strftime|gmtime|localtime)\b'],
            'datetime': [r'\bdatetime\.(datetime|date|timedelta|timezone)\b', r'\btimedelta\b', r'\btimezone\b'],
            'shutil': [r'\bshutil\.(copy|move|rmtree|make_archive)\b'],
            'pathlib': [r'\bPath\b', r'\bpathlib\.'],
            'typing': [r'\b(Optional|Union|List|Dict|Tuple|Any|Callable|TypeVar)\b'],
            'collections': [r'\b(defaultdict|OrderedDict|Counter|deque|namedtuple)\b'],
            'subprocess': [r'\bsubprocess\.'],
            'hashlib': [r'\bhashlib\.'],
            'fnmatch': [r'\bfnmatch\.'],
            'glob': [r'\bglob\.'],
        }

        issues = []
        for filepath, lines in self.submodules.items():
            fname = Path(filepath).name
            full_text = ''.join(lines)

            # 找已导入的顶层模块
            imported_modules = set()
            for line in lines:
                stripped = line.strip()
                # from X import Y
                m = re.match(r'from\s+(\w+)', stripped)
                if m:
                    imported_modules.add(m.group(1))
                # import X
                m = re.match(r'^import\s+(\w+)', stripped)
                if m:
                    imported_modules.add(m.group(1))

            # 检查已知模式
            for module, patterns in KNOWN_PATTERNS.items():
                if module in imported_modules:
                    continue  # 已导入
                for pat in patterns:
                    if re.search(pat, full_text):
                        issues.append(
                            f"  🔴 {fname}: 使用了 {module} 相关功能但未导入"
                        )
                        break  # 一个模块只报一次

        if issues:
            print(f"  ❌ 发现 {len(issues)} 个缺失导入:")
            for issue in issues:
                print(issue)
            print(f"\n  💡 修复: 在每个子模块顶部添加缺失的 import。")
            return False
        else:
            print(f"  ✅ 所有子模块 import 完整")
            return True

    def check_5_cyclic_references(self):
        """
        检查 5: ParentClass.static_attr 引用 (Trap 5)
        子模块中引用了骨架文件中定义的类名 → 循环导入风险。
        """
        print(f"\n{'─'*70}")
        print(f"🔴 检查 5: 循环导入风险 (Trap 5)")
        print(f"{'─'*70}")

        # 从骨架文件找类名
        skeleton_classes = [name for _, name in self._find_definitions(self.skeleton_lines, 'class')]

        issues = []
        for filepath, lines in self.submodules.items():
            fname = Path(filepath).name
            full_text = ''.join(lines)

            for cls_name in skeleton_classes:
                # 找 ClassName.xxx 引用（但不是 self.xxx）
                pattern = r'\b' + re.escape(cls_name) + r'\.\w+'
                matches = re.findall(pattern, full_text)

                if matches:
                    # 过滤合法的：可能是同级 Mixin 类引用
                    # 真正的问题是：子模块中的方法引用了骨架文件的类
                    for match in matches[:3]:
                        issues.append(
                            f"  🟡 {fname}: '{match}' → 可能是循环依赖\n"
                            f"     如果 {cls_name} 是该子模块的父类/Mixin 组合类，"
                            f"改用 type(self).xxx"
                        )

        if issues:
            print(f"  ⚠️ 发现 {len(issues)} 个潜在循环引用:")
            for issue in issues:
                print(issue)
            # 不强制阻塞，因为可能是同层 Mixin
            return True
        else:
            print(f"  ✅ 未发现循环引用风险")
            return True

    def check_6_skeleton_completeness(self):
        """
        检查 6: 骨架文件 Mixin/组合 完整性
        骨架文件是否包含了所有子模块的类？
        支持两种模式：Mixin继承 和 组合实例化
        """
        print(f"\n{'─'*70}")
        print(f"🔴 检查 6: 骨架文件 Mixin/组合 完整性")
        print(f"{'─'*70}")

        # 从每个子模块收集类名（取最后一个 = 通常是该层的核心类）
        submodule_classes = {}
        for filepath, lines in self.submodules.items():
            fname = Path(filepath).name
            classes = self._find_definitions(lines, 'class')
            if classes:
                # 取最后一个类名
                submodule_classes[fname] = classes[-1][1]

        # 在骨架文件中找这些类名
        skeleton_text = ''.join(self.skeleton_lines)
        skeleton_imports = set()
        for line in self.skeleton_lines:
            stripped = line.strip()
            m = re.match(r'from\s+\S+\s+import\s+(.+)', stripped)
            if m:
                for name in re.split(r',\s*', m.group(1)):
                    skeleton_imports.add(name.strip())

        # 找骨架文件中定义的类
        skeleton_class = None
        for _, cls_name in self._find_definitions(self.skeleton_lines, 'class'):
            skeleton_class = cls_name

        issues = []
        for fname, cls_name in submodule_classes.items():
            if cls_name not in skeleton_imports:
                issues.append(f"  🔴 {cls_name} (来自 {fname}) 未被骨架文件导入")

        # 检查使用方式：继承链 或 组合实例化
        if skeleton_class:
            # 模式1：Mixin继承
            inherited = set()
            inherit_match = re.search(
                r'class\s+' + re.escape(skeleton_class) + r'\s*\(([^)]+)\)',
                skeleton_text
            )
            if inherit_match:
                inherited = set(re.split(r',\s*', inherit_match.group(1)))
                inherited = {x.strip() for x in inherited}
                missing_inherit = set(submodule_classes.values()) - inherited
                for cls in missing_inherit:
                    issues.append(f"  🔴 {cls} 未出现在 {skeleton_class} 的继承链中")

            # 模式2：组合实例化（检查是否在__init__中创建实例）
            # 如果继承链为空，检查组合模式
            if not inherited:
                composed = set()
                for cls_name in submodule_classes.values():
                    if re.search(r'\b' + re.escape(cls_name) + r'\s*\(', skeleton_text):
                        composed.add(cls_name)
                
                if composed:
                    missing_compose = set(submodule_classes.values()) - composed
                    for cls in missing_compose:
                        issues.append(f"  🔴 {cls} 未被 {skeleton_class}.__init__ 实例化（组合模式）")
                    
                    if not missing_compose:
                        print(f"  ℹ️  检测到组合模式：{skeleton_class} 通过实例化使用 {len(composed)} 个子模块类")
                        # 组合模式验证通过，重置 issues
                        issues = [i for i in issues if '未被骨架文件导入' in i]

        if issues:
            print(f"  ❌ 骨架文件不完整:")
            for issue in issues:
                print(issue)
            return False
        else:
            print(f"  ✅ 骨架文件完整，包含所有子模块的类（{'继承' if inherited else '组合'}模式）")
            return True

    def run(self):
        """运行完整审计"""
        print(f"{'='*70}")
        print(f"🔍 模块化拆分后审计")
        print(f"{'='*70}")

        checks = [
            ("重复类定义", self.check_1_duplicated_classes),
            ("重复函数定义", self.check_2_duplicated_functions),
            ("重复导入块", self.check_3_duplicated_imports),
            ("Import 完整性", self.check_4_missing_imports),
            ("循环引用", self.check_5_cyclic_references),
            ("骨架完整性", self.check_6_skeleton_completeness),
        ]

        results = {}
        for name, check_fn in checks:
            results[name] = check_fn()

        print(f"\n{'='*70}")
        print(f"🏁 审计总结")
        print(f"{'='*70}")

        passed = sum(1 for v in results.values() if v)
        total = len(results)
        for name, result in results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {name}")

        print(f"\n  通过: {passed}/{total}")

        if passed == total:
            print(f"  ✅ 全部通过，可以安全提交。")
        else:
            print(f"  ⛔ 有 {total - passed} 项未通过，必须在继续前修复。")

        return passed == total


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 post_split_audit.py <skeleton_file.py> <submodule_pattern>")
        print("示例: python3 post_split_audit.py cognition/memory_new.py 'cognition/memory_l*.py'")
        sys.exit(1)

    auditor = PostSplitAuditor(sys.argv[1], sys.argv[2])
    passed = auditor.run()
    sys.exit(0 if passed else 1)
