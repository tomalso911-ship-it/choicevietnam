# -*- coding: utf-8 -*-
"""
把本地 agi_pm.db 的【核心业务表】导出成 SQL 文件，用于导入 Cloudflare D1。

只导出 8 张核心业务表（价格/汇率缓存表不迁，数据量大且可再生）。

用法：
    python cloudflare/dump_data.py

产物：
    cloudflare/data.sql   -- 可直接用 wrangler d1 execute 导入
"""
import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "agi_pm.db")
OUT = os.path.join(HERE, "data.sql")

# 只迁移这 8 张核心业务表
CORE_TABLES = [
    "users",
    "managers",
    "crm_projects",
    "won_projects",
    "lost_projects",
    "approval_requests",
    "login_history",
    "password_requests",
]


def esc(v):
    """把 Python 值转成 SQL 字面量"""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    # 字符串：单引号转义
    return "'" + str(v).replace("'", "''") + "'"


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    got_tables = [
        r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]

    lines = [
        "-- AGI-PM 核心业务数据导出",
        "-- 来源: agi_pm.db   目标: Cloudflare D1",
        "-- 导入命令: wrangler d1 execute agi-pm-db --remote --file=data.sql",
        "",
        "PRAGMA defer_foreign_keys = ON;",
        "",
    ]

    total = 0
    for t in CORE_TABLES:
        if t not in got_tables:
            lines.append("-- 跳过（本地不存在）: %s" % t)
            continue

        cols = [r[1] for r in cur.execute("PRAGMA table_info(%s)" % t)]
        rows = cur.execute("SELECT * FROM %s" % t).fetchall()

        lines.append("-- ---- %s (%d 行) ----" % (t, len(rows)))
        for r in rows:
            vals = ", ".join(esc(r[c]) for c in cols)
            lines.append("INSERT OR REPLACE INTO %s (%s) VALUES (%s);"
                         % (t, ", ".join(cols), vals))
        lines.append("")
        total += len(rows)
        print("  %-22s %5d 行" % (t, len(rows)))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n合计 %d 行 -> %s" % (total, OUT))
    print("大小: %.1f KB" % (os.path.getsize(OUT) / 1024))
    conn.close()


if __name__ == "__main__":
    main()
