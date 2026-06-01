#!/usr/bin/env python3
"""
l1_migrate.py — L1→L3 迁移辅助脚本（四层架构 · 层4辅助）
=============================================================
负责文件系统侧操作：创建归档 → 更新指针 → 更新索引 → 验证完整性

标准执行顺序：
  第1步（LLM对话中）：memory.replace() 先释放空间
  第2步（本脚本）：write_file 创建 archive 归档
  第3步（本脚本）：patch MEMORY.md 加入短指针
  第4步（本脚本）：更新 MEMORY_INDEX.md
  第5步（本脚本）：验证全部完整性

为什么先memory.replace再写文件？
  如果先写文件后replace，replace失败=archive孤儿文件+指针悬空
  如果先replace后写文件，replace成功=空间已释放，写文件失败可重试

用法：
  python3 l1_migrate.py migrate <tag> <title> <<< "要归档的内容"
  python3 l1_migrate.py verify <tag>            # 验证指定标签的归档+指针完整性
  python3 l1_migrate.py list                    # 列出所有归档
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

BASE = Path("~/.hermes-agent")
ARCHIVE_DIR = BASE / "memories" / "archive"
INDEX_FILE = ARCHIVE_DIR / "MEMORY_INDEX.md"
MEMORY_FILE = BASE / "MEMORY.md"


def create_archive(tag: str, title: str, content: str) -> Path:
    """创建归档文件"""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_-]', '-', title)[:40]
    filename = f"{date_str}-{safe_title}.md"
    filepath = ARCHIVE_DIR / filename

    frontmatter = f"""---
date: {date_str}
tags: [{tag}]
source: L1→L3 迁移
migrated_at: {datetime.now().isoformat()}
---

"""
    filepath.write_text(frontmatter + content)
    return filepath


def patch_memory_pointer(tag: str, archive_path: Path) -> bool:
    """在 MEMORY.md 中添加短指针（如果还不存在）"""
    if not MEMORY_FILE.exists():
        print("❌ MEMORY.md 不存在", file=sys.stderr)
        return False

    pointer = f"→ 详见 {archive_path.relative_to(BASE)}"
    content = MEMORY_FILE.read_text()

    # 检查指针是否已存在
    if pointer in content:
        print(f"⚠️ 指针已存在: {pointer}")
        return True

    # 添加到 L2 标签索引区域之后
    index_marker = "## L2 标签索引"
    idx = content.find(index_marker)
    if idx < 0:
        # fallback: 添加到文件末尾
        new_content = content.rstrip() + f"\n\n{pointer}\n"
    else:
        # 找到索引表格结束位置
        after_index = content.find("\n## ", idx + len(index_marker))
        if after_index < 0:
            after_index = len(content)
        new_content = content[:after_index] + f"\n{pointer}" + content[after_index:]

    MEMORY_FILE.write_text(new_content)
    return True


def update_index(tag: str, archive_filename: str, title: str) -> bool:
    """更新 MEMORY_INDEX.md"""
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not INDEX_FILE.exists():
        INDEX_FILE.write_text("# 记忆索引\n\n> L2 标签索引目录树\n\n")

    content = INDEX_FILE.read_text()

    # 查找对应标签区域
    tag_marker = f"## {tag}"
    idx = content.find(tag_marker)

    entry = f"- [{archive_filename}]({archive_filename})\n  {title}\n"

    if idx >= 0:
        # 在现有标签区域追加
        next_section = content.find("\n## ", idx + len(tag_marker))
        if next_section > 0:
            content = content[:next_section] + entry + content[next_section:]
        else:
            content = content.rstrip() + f"\n{entry}\n"
    else:
        # 新建标签区域
        content = content.rstrip() + f"\n\n{tag_marker}\n{entry}\n"

    INDEX_FILE.write_text(content)
    return True


def verify_archive(tag: str) -> dict:
    """验证归档+指针完整性"""
    result = {
        "tag": tag,
        "archive_files": [],
        "pointers_in_memory": [],
        "orphans": [],
        "dangling_pointers": [],
        "ok": True,
    }

    # 找所有该标签的归档文件
    for f in ARCHIVE_DIR.glob("*.md"):
        if f.name == "MEMORY_INDEX.md":
            continue
        content = f.read_text()
        if tag in content[:200]:  # 检查 frontmatter
            result["archive_files"].append(f.name)

    # 在 MEMORY.md 中找所有指向该标签的指针
    if MEMORY_FILE.exists():
        memory_content = MEMORY_FILE.read_text()
        pattern = rf'→ 详见.*?archive/.*?{tag}.*?\.md'
        for match in re.finditer(pattern, memory_content):
            result["pointers_in_memory"].append(match.group())

    # 检查孤儿归档（文件存在但索引无记录）
    if INDEX_FILE.exists():
        index_content = INDEX_FILE.read_text()
        for af in result["archive_files"]:
            if af not in index_content:
                result["orphans"].append(af)
                result["ok"] = False

    # 检查悬空指针（指针指向的文件不存在）
    for ptr in result["pointers_in_memory"]:
        # 提取文件名
        m = re.search(r'archive/([^)]+)', ptr)
        if m:
            filename = m.group(1)
            if filename not in result["archive_files"]:
                result["dangling_pointers"].append(ptr)
                result["ok"] = False

    return result


def list_archives() -> list:
    """列出所有归档"""
    archives = []
    for f in sorted(ARCHIVE_DIR.glob("*.md")):
        if f.name == "MEMORY_INDEX.md":
            continue
        first_line = ""
        content = f.read_text()
        for line in content.split("\n"):
            if line.startswith("tags:"):
                first_line = line.strip()
                break
        archives.append((f.name, first_line))
    return archives


# ─── CLI ───
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  l1_migrate.py migrate <tag> <title>  # 从stdin读取内容，创建归档+指针+索引")
        print("  l1_migrate.py verify <tag>            # 验证指定标签的完整性")
        print("  l1_migrate.py list                    # 列出所有归档")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        archives = list_archives()
        print(f"归档文件 ({len(archives)}):")
        for name, tags in archives:
            print(f"  {name}  {tags}")
        sys.exit(0)

    if cmd == "verify" and len(sys.argv) >= 3:
        tag = sys.argv[2]
        result = verify_archive(tag)
        print(f"标签 [{tag}] 验证:")
        print(f"  归档文件: {len(result['archive_files'])}个")
        print(f"  MEMORY指针: {len(result['pointers_in_memory'])}个")
        print(f"  孤儿归档(索引缺失): {len(result['orphans'])}个")
        print(f"  悬空指针(文件缺失): {len(result['dangling_pointers'])}个")
        if result["orphans"]:
            for o in result["orphans"]:
                print(f"    ⚠️ 孤儿: {o}")
        if result["dangling_pointers"]:
            for d in result["dangling_pointers"]:
                print(f"    ❌ 悬空: {d}")
        print(f"  结论: {'✅ 完整' if result['ok'] else '❌ 有断链'}")
        sys.exit(0 if result["ok"] else 1)

    if cmd == "migrate" and len(sys.argv) >= 4:
        tag = sys.argv[2]
        title = sys.argv[3]
        content = sys.stdin.read()

        if not content.strip():
            print("❌ 输入内容为空", file=sys.stderr)
            sys.exit(1)

        print(f"📦 迁移: [{tag}] {title}")
        print(f"   内容: {len(content)} 字符")

        # 第2步：创建归档
        archive_path = create_archive(tag, title, content)
        print(f"   ✅ 归档: {archive_path}")

        # 验证归档内容完整
        written = archive_path.read_text()
        if content not in written:
            print(f"   ❌ 归档内容验证失败！", file=sys.stderr)
            sys.exit(1)
        print(f"   ✅ 内容验证通过")

        # 第3步：更新指针（延迟——等 LLM 做 memory.replace 之后）
        # 这里只创建归档，指针更新留到下一步
        print(f"   📎 短指针: → 详见 {archive_path.relative_to(BASE)}")

        # 第4步：更新索引
        ok = update_index(tag, archive_path.name, title)
        if ok:
            print(f"   ✅ 索引已更新")
        else:
            print(f"   ❌ 索引更新失败", file=sys.stderr)
            sys.exit(1)

        # 第5步：全局验证
        result = verify_archive(tag)
        if result["ok"]:
            print(f"   ✅ 全局验证通过")
        else:
            print(f"   ⚠️ 验证有警告: {len(result['orphans'])}孤儿 {len(result['dangling_pointers'])}悬空")

        print(f"\n下一步（LLM对话中手动执行）：")
        print(f"  1. memory.replace() 将 MEMORY.md 中旧内容替换为短指针")
        print(f"  2. 运行 l1_migrate.py verify {tag} 验证完整")
        sys.exit(0)

    print(f"❌ 未知命令或参数不足", file=sys.stderr)
    sys.exit(1)
