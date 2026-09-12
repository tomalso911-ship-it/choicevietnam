# -*- coding: utf-8 -*-
"""查看指定用户在云端的权限状态"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

TARGETS = ["admin", "tom", "cuong", "james"]


def get(path, user="tom"):
    req = urllib.request.Request(API + path, headers={"User-Agent": UA, "X-User-Name": user})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


d = get("/api/users")
users = d.get("users", [])
managers = d.get("managers", [])

print("=" * 70)
print("  当前管理员名单")
print("=" * 70)
print("  " + ", ".join(managers))

print("\n" + "=" * 70)
print("  目标用户状态")
print("=" * 70)
print("  %-10s %-10s %-12s %-8s %-10s %s" % ("账号", "姓名", "职位", "role", "is_manager", "perms区块数"))
print("  " + "-" * 66)

for u in users:
    if u.get("username") in TARGETS:
        perms = u.get("perms") or {}
        n = len(perms) if isinstance(perms, dict) else 0
        print("  %-10s %-10s %-12s %-8s %-10s %d" % (
            u.get("username"), u.get("real_name") or "-",
            u.get("position") or "-", u.get("role") or "-",
            u.get("is_manager"), n))

# 打印 admin 的完整 perms 作为参考
adm = next((x for x in users if x.get("username") == "admin"), None)
if adm:
    print("\n" + "=" * 70)
    print("  admin 的权限配置（作为参照）")
    print("=" * 70)
    perms = adm.get("perms") or {}
    if isinstance(perms, dict) and perms:
        for k, v in sorted(perms.items()):
            print("    %-12s %s" % (k, json.dumps(v, ensure_ascii=False)))
    else:
        print("    (admin 未配置具体 perms，靠 is_manager 走管理员豁免)")
    print("\n  role=%s  is_manager=%s" % (adm.get("role"), adm.get("is_manager")))

print("\n" + "=" * 70)
