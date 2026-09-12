# -*- coding: utf-8 -*-
"""
分析演示数据中出现的所有人员名字

从 CRM / WON / LOST 数据里提取 salesperson、manager、owner_user_id 等字段，
汇总成人员清单，用于生成配套的演示账号。
"""
import os
import sys
import json
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SNAP = os.path.join(ROOT, "demo_snapshot.json")

# 需要从业务数据里提取人员的字段
PERSON_FIELDS = ["salesperson", "manager", "owner_user_id", "requester", "approvers"]

with open(SNAP, "r", encoding="utf-8") as f:
    snap = json.load(f)

tables = snap.get("tables") or {}
people = Counter()
detail = {}   # name -> 出现在哪些表/字段

for tname in ["crm_projects", "won_projects", "lost_projects", "approval_requests"]:
    rows = tables.get(tname) or []
    for r in rows:
        if not isinstance(r, dict):
            continue
        for f in PERSON_FIELDS:
            v = r.get(f)
            if v is None:
                continue
            if isinstance(v, list):
                items = v
            else:
                items = [v]
            for it in items:
                s = str(it).strip()
                if not s:
                    continue
                # approvers 可能是 JSON 字符串
                if s.startswith("[") and s.endswith("]"):
                    try:
                        for x in json.loads(s):
                            xs = str(x).strip()
                            if xs:
                                people[xs] += 1
                                detail.setdefault(xs, set()).add("%s.%s" % (tname, f))
                    except Exception:
                        pass
                    continue
                people[s] += 1
                detail.setdefault(s, set()).add("%s.%s" % (tname, f))

print("=" * 66)
print("  演示数据中的人员清单")
print("=" * 66)
print("  共 %d 个不同名字\n" % len(people))

# 现有真实用户
existing = {"tom", "alice", "admin", "cuong", "james", "travis", "ali", "linh"}

print("  %-16s %6s  %-10s  %s" % ("名字", "出现次数", "是否已有账号", "出现位置"))
print("  " + "-" * 62)
for name, cnt in people.most_common():
    has = "是" if name.lower() in existing else "否"
    loc = ", ".join(sorted(detail.get(name, []))[:3])
    print("  %-16s %6d  %-10s  %s" % (name, cnt, has, loc))

# 缺失的（需要建演示账号的）
missing = [n for n in people if n.lower() not in existing]
print("\n" + "=" * 66)
print("  需要新建演示账号: %d 个" % len(missing))
for n in sorted(missing):
    print("    - %s" % n)
print("=" * 66)
