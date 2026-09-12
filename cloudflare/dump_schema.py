# -*- coding: utf-8 -*-
"""
导出本机 agi_pm.db 的表结构 -> cloudflare/schema.sql

用途：Cloudflare D1 建表时用（D1 就是云上的 SQLite，语法几乎一样）。
什么时候重新跑：修改了本地数据库表结构之后。

用法（双击项目根目录的 cloudflare-dev.bat 也可以，但这是 Python 脚本）：
    python cloudflare/dump_schema.py
"""
import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "agi_pm.db")
OUT = os.path.join(HERE, "schema.sql")

# 这些是价格/汇率缓存表，数据量大且丢了可重新采集，不迁到 D1
CACHE_HINT = {
    "feed_cache", "fx_cache", "metal_cache", "livestock_price_cache",
    "livestock_history", "livestock_farmgate", "livestock_retail",
    "livestock_update_log", "livestock_meta",
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

tables = [
    r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
]

lines = [
    "-- 由 agi_pm.db 自动导出，用于 Cloudflare D1 建表",
    "-- 标注 [缓存表] 的表不迁移到 D1（数据量大、可重新采集）",
    "",
]

core, cache = [], []
for t in tables:
    row = cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)
    ).fetchone()
    cnt = cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    mark = "  [缓存表·不迁移]" if t in CACHE_HINT else ""
    block = "-- 表: %s | 行数: %d%s\n%s;\n" % (
        t, cnt, mark, row[0] if row and row[0] else "-- (无建表语句)"
    )
    (cache if t in CACHE_HINT else core).append(block)

lines.append("-- ============ 核心业务表（迁移到 D1） ============\n")
lines.extend(core)
lines.append("\n-- ============ 缓存表（不迁移） ============\n")
lines.extend(cache)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# 额外输出：只含核心业务表的建表文件，供 D1 建表直接用
CORE_ONLY = os.path.join(HERE, "schema-core.sql")
with open(CORE_ONLY, "w", encoding="utf-8") as f:
    f.write("\n".join([
        "-- AGI-PM 核心业务表建表语句（仅 8 张表）",
        "-- 用途: Cloudflare D1 建表",
        "-- 导入: wrangler d1 execute agi-pm-db --remote --file=schema-core.sql",
        "",
    ] + core))

print("已导出 -> %s" % OUT)
print("\n【核心业务表 · 要迁移】")
for t in sorted([x for x in tables if x not in CACHE_HINT]):
    print("  %-24s %5d 行" % (t, cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]))
print("\n【缓存表 · 不迁移】")
for t in sorted([x for x in tables if x in CACHE_HINT]):
    print("  %-24s %5d 行" % (t, cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]))
conn.close()
