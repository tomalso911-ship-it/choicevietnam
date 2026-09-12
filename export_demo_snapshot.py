#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 导出【当前】演示数据快照 → demo_snapshot.json
============================================================================
用途：把此刻系统里的数据（CRM / LOST / WON / 审批 + 示例用户）完整保存下来，
      供「DEMO」按钮一键还原。相当于给当前演示状态拍一张照片。

只对【示例数据】拍照，真实用户（tom/alice/admin/cuong/james/travis/ali/linh）
会被排除在外 —— 他们永远保留，不进快照、也不被 DEMO 按钮删除。

用法：
    python export_demo_snapshot.py

输出到：demo_snapshot.json
============================================================================
"""
import sys, os, json, sqlite3, time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import app

# 真实用户：永远保留，不进快照、不被删除
REAL_USERS = ["tom", "alice", "admin", "cuong", "james", "travis", "ali", "linh"]
REAL_SET = set(u.lower() for u in REAL_USERS)

# 需要拍照的业务表
SNAPSHOT_TABLES = ["crm_projects", "lost_projects", "won_projects", "approval_requests"]


def main():
    conn = sqlite3.connect(app.DB_PATH)
    conn.row_factory = sqlite3.Row

    snap = {
        "_meta": {
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "AGI-PM 演示数据快照。由 export_demo_snapshot.py 生成，供 DEMO 按钮一键还原。",
            "real_users": REAL_USERS,
            "tables": SNAPSHOT_TABLES,
        },
        "tables": {},
        "demo_users": [],
        "demo_managers": [],
    }

    print("=" * 74)
    print("导出演示数据快照")
    print("=" * 74)

    # ---- 业务表 ----
    for t in SNAPSHOT_TABLES:
        try:
            rows = [dict(r) for r in conn.execute("SELECT * FROM %s" % t)]
            snap["tables"][t] = rows
            print("  表 %-22s %4d 行" % (t, len(rows)))
        except Exception as e:
            print("  表 %-22s 读取失败: %s" % (t, e))
            snap["tables"][t] = []

    # ---- 示例用户（排除真实用户）----
    all_users = [dict(r) for r in conn.execute("SELECT * FROM users")]
    demo_users = [u for u in all_users
                  if (u.get("username") or "").strip().lower() not in REAL_SET]
    real_kept = [u for u in all_users
                 if (u.get("username") or "").strip().lower() in REAL_SET]
    snap["demo_users"] = demo_users
    print()
    print("  示例用户（进快照，可被 DEMO 还原/删除）: %d 个" % len(demo_users))
    for u in demo_users:
        print("      %-14s %-14s %s" % (
            u.get("username"), u.get("real_name"), u.get("position") or "-"))
    print("  真实用户（不进快照，永久保留）        : %d 个" % len(real_kept))
    for u in real_kept:
        print("      %-14s %-14s %s" % (
            u.get("username"), u.get("real_name"), u.get("position") or "-"))

    # ---- managers 中的示例用户 ----
    try:
        mgrs = [dict(r) for r in conn.execute("SELECT * FROM managers")]
        demo_mgrs = [m for m in mgrs
                     if (m.get("username") or "").strip().lower() not in REAL_SET]
        snap["demo_managers"] = demo_mgrs
        print()
        print("  managers 中的示例管理员: %d 个" % len(demo_mgrs))
        for m in demo_mgrs:
            print("      ", m.get("username"))
    except Exception as e:
        print("  managers 读取失败:", e)

    conn.close()

    # ---- 写文件 ----
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_snapshot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)

    size = os.path.getsize(out)
    print()
    print("=" * 74)
    print("已导出: demo_snapshot.json  (%.1f KB)" % (size / 1024.0))
    print("=" * 74)


if __name__ == "__main__":
    main()
