# -*- coding: utf-8 -*-
"""检查 DEMO 快照文件的内容结构"""
import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, "..", "demo_snapshot.json")

with open(path, "r", encoding="utf-8") as f:
    snap = json.load(f)

tables = snap.get("tables") or {}
print("=" * 46)
print("  DEMO 快照内容")
print("=" * 46)
if not tables:
    print("  (快照中没有 tables 字段)")
    print("  顶层字段:", list(snap.keys()))
else:
    total = 0
    for k, v in tables.items():
        n = len(v) if isinstance(v, list) else 0
        total += n
        print("  %-22s %4d 行" % (k, n))
    print("  " + "-" * 30)
    print("  %-22s %4d 行" % ("合计", total))

# 检查是否含用户表
has_users = "users" in tables
print()
print("  含 users 表(演示账号):", "是" if has_users else "否")
if not has_users:
    print("  -> DEMO 加载只恢复业务数据，不新增演示账号")
print("=" * 46)
