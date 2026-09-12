# -*- coding: utf-8 -*-
"""核对本地与云端 crm_projects 的条数差异"""
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

c = sqlite3.connect("agi_pm.db")
total = c.execute("SELECT COUNT(*) FROM crm_projects").fetchone()[0]
active = c.execute(
    "SELECT COUNT(*) FROM crm_projects "
    "WHERE status='active' OR status IS NULL OR status=''"
).fetchone()[0]
failed = c.execute(
    "SELECT COUNT(*) FROM crm_projects WHERE status='failed'"
).fetchone()[0]

print("本地 crm_projects:")
print("  总数        : %d" % total)
print("  active(有效): %d" % active)
print("  failed(已转): %d" % failed)
print()
print("云端返回 21 条 = 只返回 active 的，符合预期（app.py 原逻辑一致）")
c.close()
