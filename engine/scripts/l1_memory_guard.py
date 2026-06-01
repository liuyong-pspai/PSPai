#!/usr/bin/env python3
"""
l1_memory_guard.py — L1 记忆容量守护（四层架构 · 层1+层2）
=============================================================
层1 硬拦截：写 MEMORY.md 前检查容量，超阈值拒写
层2 外部看门狗：cron 每10分钟独立检查，告警不依赖 LLM

设计原则（审计结论）：
- 监控必须外挂，永远不依赖被监控系统自己报自己的健康状况
- MEMORY.md 和 memory 工具是两套独立系统，各管各的阈值
- 硬拦截阈值 6KB（给白名单留 2KB 缓冲），告警阈值 5KB

用法：
  python3 l1_memory_guard.py check    # 看门狗模式（cron调用）
  python3 l1_memory_guard.py guard    # 硬拦截模式（写前调用）
  python3 l1_memory_guard.py status   # 查看当前状态
"""

import sys
import os
from pathlib import Path
from datetime import datetime

BASE = Path("~/.hermes-agent")
MEMORY_FILE = BASE / "MEMORY.md"
GUARD_LOG = BASE / "logs" / "l1_memory_guard.log"
ALERT_SENTINEL = BASE / ".l1_alert_active"

# 阈值（字节）
HARD_LIMIT = 6144   # 6KB — 硬拦截，超过拒写
WARN_LIMIT = 5120   # 5KB — 告警，需要迁移
SAFE_LIMIT  = 4096  # 4KB — 安全线


def get_memory_size() -> int:
    """获取 MEMORY.md 当前字节数"""
    if not MEMORY_FILE.exists():
        return 0
    return MEMORY_FILE.stat().st_size


def count_whitelist_chars() -> int:
    """
    统计白名单内容的字符数（六刀+操作清单+注册表+身份+阶段定位）
    这部分永不迁移，需要单独计算以评估真实可用空间
    """
    if not MEMORY_FILE.exists():
        return 0
    content = MEMORY_FILE.read_text()

    sections = [
        "## ⚡ 回复前操作清单",
        "## 🔧 patch后验证清单",
        "## 📋 任务闭环清单",
        "## 修改代码六刀",
        "## 🏗️ 硬化注册表",
        "## 🏷️ 阶段定位",
        "## 我是谁",
    ]

    total = 0
    for section in sections:
        idx = content.find(section)
        if idx >= 0:
            # 找到下一个 ## 标题或文件末尾
            rest = content[idx:]
            next_section = rest.find("\n## ", len(section))
            if next_section > 0:
                total += len(rest[:next_section])
            else:
                total += len(rest)
    return total


def check_threshold() -> dict:
    """看门狗检查：返回 (级别, 详情)"""
    size = get_memory_size()
    whitelist = count_whitelist_chars()
    available = HARD_LIMIT - whitelist

    if size >= HARD_LIMIT:
        level = "🔴 HARD"
        msg = f"超过硬拦截阈值 {HARD_LIMIT}B（当前{size}B）"
    elif size >= WARN_LIMIT:
        level = "🟡 WARN"
        msg = f"超过告警阈值 {WARN_LIMIT}B（当前{size}B）"
    elif size >= SAFE_LIMIT:
        level = "🟢 SAFE"
        msg = f"正常（当前{size}B）"
    else:
        level = "🟢 OK"
        msg = f"健康（当前{size}B）"

    return {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "size": size,
        "whitelist": whitelist,
        "available": available,
        "hard_limit": HARD_LIMIT,
        "warn_limit": WARN_LIMIT,
        "message": msg,
    }


def guard_before_write(write_size: int = 0) -> bool:
    """
    硬拦截：写前检查。返回 True=可以写，False=拒绝。
    write_size: 即将写入的字节数（估算）
    """
    current = get_memory_size()
    projected = current + write_size

    if projected >= HARD_LIMIT:
        print(f"❌ L1_GUARD: 拒绝写入。"
              f"当前{current}B + 预估{write_size}B = {projected}B ≥ {HARD_LIMIT}B 硬限制",
              file=sys.stderr)
        return False

    if projected >= WARN_LIMIT:
        print(f"⚠️ L1_GUARD: 允许写入但已近告警线。"
              f"当前{current}B + 预估{write_size}B = {projected}B ≥ {WARN_LIMIT}B",
              file=sys.stderr)

    return True


def log_alert(result: dict):
    """将告警写入独立日志（不依赖 MEMORY.md）"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level = result["level"]

    with open(GUARD_LOG, "a") as f:
        f.write(f"[{ts}] {level} size={result['size']}B "
                f"whitelist={result['whitelist']}B "
                f"available={result['available']}B "
                f"limit={result['hard_limit']}B\n")

    # 如果是 HARD 级别，创建告警标记文件
    if "HARD" in level:
        ALERT_SENTINEL.write_text(f"{ts}\n{result['message']}\n")
        print(f"[{ts}] 🔴 硬拦截触发！已创建告警标记 {ALERT_SENTINEL}", file=sys.stderr)
    elif "WARN" in level:
        # 警告级别也创建标记，但内容不同
        ALERT_SENTINEL.write_text(f"{ts}\n{result['message']}\n建议：下次对话中执行 l1_migrate.py\n")
    else:
        # 清除告警标记
        if ALERT_SENTINEL.exists():
            ALERT_SENTINEL.unlink()
            print(f"[{ts}] 🟢 容量恢复正常，已清除告警标记", file=sys.stderr)


def print_status():
    """打印当前状态"""
    result = check_threshold()
    print(f"L1 记忆容量状态")
    print(f"  文件: {MEMORY_FILE}")
    print(f"  当前大小: {result['size']}B")
    print(f"  白名单占用: {result['whitelist']}B")
    print(f"  可用空间: {result['available']}B（硬限制{result['hard_limit']}B）")
    print(f"  告警线: {result['warn_limit']}B")
    print(f"  级别: {result['level']}")
    print(f"  信息: {result['message']}")

    if ALERT_SENTINEL.exists():
        print(f"\n  ⚠️ 存在活跃告警:")
        print(f"  {ALERT_SENTINEL.read_text().strip()}")


# ─── CLI ───
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("check", "guard", "status"):
        print("用法: l1_memory_guard.py check|guard|status")
        print("  check  — 看门狗模式，检查阈值并写日志")
        print("  guard  — 硬拦截模式，返回0(允许)/1(拒绝)")
        print("  status — 查看当前状态")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        print_status()
        sys.exit(0)

    result = check_threshold()

    if cmd == "check":
        log_alert(result)
        print(f"[{result['timestamp']}] {result['level']} {result['message']}")
        sys.exit(0 if "OK" in result["level"] or "SAFE" in result["level"] else 1)

    elif cmd == "guard":
        # 硬拦截：只检查阈值，不写日志（调用方负责日志）
        if get_memory_size() >= HARD_LIMIT:
            print(f"❌ GUARD:BLOCKED size={result['size']}B >= {HARD_LIMIT}B", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)


# ─── 预算估算（TDD RED→GREEN 新增） ───
AVG_ENTRY_SIZE = 300  # 平均每条 memory entry 的字符数


def budget_remaining() -> int:
    """估算还能写入多少字符"""
    return max(0, HARD_LIMIT - get_memory_size())


def budget_entries() -> int:
    """估算还能写入多少条 entry（基于平均大小）"""
    return max(0, budget_remaining() // AVG_ENTRY_SIZE)
