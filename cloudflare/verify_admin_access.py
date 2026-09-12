# -*- coding: utf-8 -*-
"""
验证 cuong / james / tom 是否真的拥有和 admin 一样的权限

检查项：
  1. /api/me 返回 is_admin = true
  2. 能看到全部业务数据（不被可见范围过滤）
  3. 能读取用户列表（用户管理权限）
"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

TEST_USERS = ["admin", "tom", "cuong", "james"]
results = []


def get(path, user=None):
    headers = {"User-Agent": UA}
    if user:
        headers["X-User-Name"] = user
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def check(name, ok, detail=""):
    print("    %s  %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("          %s" % detail)
    results.append(ok)


print("=" * 66)
print("  管理员权限验证")
print("=" * 66)

print("\n[1] is_admin 标记")
print("    %-10s %-8s %-10s %s" % ("账号", "is_admin", "role", "职位"))
print("    " + "-" * 52)
admin_flags = {}
for u in TEST_USERS:
    st, d = get("/api/me?username=" + u)
    user = d.get("user", {}) if isinstance(d, dict) else {}
    is_admin = user.get("is_admin")
    admin_flags[u] = is_admin
    print("    %-10s %-8s %-10s %s" % (
        u, is_admin, user.get("role"), user.get("position")))

for u in TEST_USERS:
    check("%s is_admin=True" % u, admin_flags.get(u) is True,
          "实际: %s" % admin_flags.get(u))

print("\n[2] 可见数据范围（管理员应看全部）")
counts = {}
for u in TEST_USERS:
    st, d = get("/api/crm-projects", user=u)
    n = len(d) if isinstance(d, list) else -1
    counts[u] = n
    print("    %-10s 看到 %d 条潜在项目" % (u, n))

base = counts.get("admin", 0)
for u in TEST_USERS:
    check("%s 与 admin 看到相同数量" % u, counts.get(u) == base,
          "%d vs admin %d" % (counts.get(u, -1), base))

print("\n[3] 用户管理权限（管理员可读取用户列表）")
for u in TEST_USERS:
    st, d = get("/api/users", user=u)
    users = d.get("users", []) if isinstance(d, dict) else []
    ok = st == 200 and len(users) > 0
    check("%s 可读取用户列表" % u, ok, "HTTP %s  %d 个用户" % (st, len(users)))

print("\n" + "=" * 66)
print("  测试结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 66)
