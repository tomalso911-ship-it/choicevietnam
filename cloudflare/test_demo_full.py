# -*- coding: utf-8 -*-
"""
M10 测试：DEMO 一次操作同时处理【用户 + 业务数据】
"""
import sys
import json
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

results = []


def call(method, path, body=None, user="tom"):
    url = API + path
    data = None
    headers = {"User-Agent": UA}
    if user:
        headers["X-User-Name"] = user
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))


def check(name, ok, detail=""):
    print("    %s  %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("          %s" % detail)
    results.append(ok)


print("=" * 66)
print("  M10 测试：DEMO 完整数据包（用户 + 业务）")
print("=" * 66)

# ---------- 1. 先清空 ----------
print("\n[1] 清空（回到空库）")
st, r = call("POST", "/api/demo/clear")
check("清空成功", st == 200 and r.get("ok"),
      json.dumps(r.get("removed", {}), ensure_ascii=False))

st, d = call("GET", "/api/users")
n_users_empty = len(d.get("users", [])) if isinstance(d, dict) else -1
print("          剩余用户: %d 个" % n_users_empty)

# ---------- 2. 加载 DEMO ----------
print("\n[2] 加载 DEMO")
st, r = call("POST", "/api/demo/load")
ok_load = st == 200 and isinstance(r, dict) and r.get("ok")
restored = r.get("restored", {}) if isinstance(r, dict) else {}
check("加载成功", ok_load, json.dumps(restored, ensure_ascii=False))

if not ok_load:
    print("    加载失败，中止")
    sys.exit(1)

# ---------- 3. 验证业务数据 ----------
print("\n[3] 业务数据")
# 注意：/api/crm-projects 只返回 active 的（failed 的不显示），
# 快照共 72 条其中 11 条 failed，所以 active 约 61 条
for path, key, expect in [
    ("/api/crm-projects?scope=all", "crm_projects", 55),
    ("/api/won-projects", "won_projects", 25),
    ("/api/lost-projects", "lost_projects", 35),
]:
    st, d = call("GET", path)
    n = len(d) if isinstance(d, list) else -1
    check("%s >= %d" % (key, expect), n >= expect, "实际 %d 条" % n)

st, d = call("GET", "/api/approval-requests?scope=all")
n_appr = len(d.get("items", [])) if isinstance(d, dict) else -1
check("审批单 >= 25", n_appr >= 25, "实际 %d 条" % n_appr)

# ---------- 4. 验证用户 ----------
print("\n[4] 用户与权限（核心需求）")
st, d = call("GET", "/api/users")
users = d.get("users", []) if isinstance(d, dict) else []
n_users = len(users)
check("用户总数 >= 20", n_users >= 20, "实际 %d 个" % n_users)

# 检查演示账号是否都在
demo_names = ["minh", "salesdir1", "salesdir2", "gm1", "gm2", "dgm1", "dgm2",
              "obs1", "obs2", "fin1", "fin2", "asst1", "hr1", "khoa"]
uname_set = {str(u.get("username", "")).lower() for u in users}
present = [n for n in demo_names if n in uname_set]
missing = [n for n in demo_names if n not in uname_set]
check("14 个演示账号全部存在", len(missing) == 0,
      "存在 %d 个%s" % (len(present), ("，缺失: " + ", ".join(missing)) if missing else ""))

# 职位分布
positions = {}
for u in users:
    p = u.get("position") or "(未设)"
    positions[p] = positions.get(p, 0) + 1
print("\n          职位分布:")
for p, c in sorted(positions.items(), key=lambda x: -x[1]):
    print("            %-12s %d 人" % (p, c))
check("职位种类 >= 6", len(positions) >= 6, "实际 %d 种" % len(positions))

# 真实账号仍在
real = {"tom", "alice", "admin", "cuong", "james", "travis", "ali", "linh"}
still = [x for x in real if x in uname_set]
check("真实账号未被破坏", len(still) >= 5,
      "保留 %d 个: %s" % (len(still), ", ".join(sorted(still))))

# ---------- 5. 演示账号能否登录 ----------
print("\n[5] 演示账号登录（培训要用）")
for u in ["minh", "gm1", "salesdir1", "khoa"]:
    st, d = call("POST", "/api/login", {"username": u, "password": "66668888"}, user=None)
    ok = st == 200 and isinstance(d, dict) and d.get("ok")
    check("%s 可用 66668888 登录" % u, ok,
          (d.get("user", {}).get("real_name") + " / " + d.get("user", {}).get("position"))
          if ok else (d.get("error") if isinstance(d, dict) else str(d)[:50]))

# ---------- 6. 数据范围过滤（核心培训点） ----------
print("\n[6] 数据范围过滤（销售只看自己的）")
st, all_crm = call("GET", "/api/crm-projects?scope=all")
n_all = len(all_crm) if isinstance(all_crm, list) else 0
st, khoa_crm = call("GET", "/api/crm-projects", user="khoa")
n_khoa = len(khoa_crm) if isinstance(khoa_crm, list) else -1
print("          管理员(tom) 看到: %d 条" % n_all)
print("          khoa 看到      : %d 条" % n_khoa)
check("普通用户数据被过滤", 0 <= n_khoa < n_all,
      "khoa=%d < 全部=%d" % (n_khoa, n_all))

# ---------- 7. 再次清空 ----------
print("\n[7] 再次清空（验证回到全新状态）")
st, r = call("POST", "/api/demo/clear")
check("清空成功", st == 200 and r.get("ok"),
      json.dumps(r.get("removed", {}), ensure_ascii=False))

st, d = call("GET", "/api/users")
n_final = len(d.get("users", [])) if isinstance(d, dict) else -1
check("演示账号已删除，只剩真实账号", n_final <= 10, "剩余 %d 个用户" % n_final)

st, d = call("GET", "/api/crm-projects?scope=all")
n_crm_final = len(d) if isinstance(d, list) else -1
check("业务数据已清空", n_crm_final == 0, "CRM 剩 %d 条" % n_crm_final)

print("\n" + "=" * 66)
print("  测试结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 66)
