# -*- coding: utf-8 -*-
"""
清空云端业务数据，回到"干净空库"状态。

保留：用户账号（22 个真实账号）、管理员任命
清空：潜在项目 / 签约项目 / 失败项目 / 审批单

这样网页版登录后是空的，点击 DEMO 按钮才加载演示数据。

用法：
    python cloudflare/reset_empty.py
"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def post(path, body=None):
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(
        API + path, data=data,
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


print("=" * 52)
print("  清空云端业务数据（保留用户账号）")
print("=" * 52)

print("\n[1] 执行 DEMO 清空...")
r = post("/api/demo/clear")
if r.get("ok"):
    removed = r.get("removed", {})
    for k, v in removed.items():
        print("    %-22s %s" % (k, v))
else:
    print("    失败: %s" % r)

print("\n[2] 验证当前状态...")
counts = {}
for path, key in [
    ("/api/crm-projects?scope=all", "潜在项目"),
    ("/api/won-projects", "签约项目"),
    ("/api/lost-projects", "失败项目"),
]:
    try:
        d = get(path)
        counts[key] = len(d) if isinstance(d, list) else -1
    except Exception as e:
        counts[key] = "错误"
try:
    d = get("/api/approval-requests?scope=all")
    counts["审批单"] = len(d.get("items", [])) if isinstance(d, dict) else 0
except Exception:
    counts["审批单"] = "错误"

for k, v in counts.items():
    print("    %-10s %s 条" % (k, v))

try:
    d = get("/api/users")
    n = len(d.get("users", [])) if isinstance(d, dict) else 0
    mgrs = d.get("managers", []) if isinstance(d, dict) else []
    print("    %-10s %s 个（保留）" % ("用户账号", n))
    print("    %-10s %s（保留）" % ("管理员", ", ".join(mgrs)))
except Exception as e:
    print("    用户账号 读取失败: %s" % e)

ok = all(v == 0 for v in counts.values() if isinstance(v, int))
print("\n" + "=" * 52)
print("  %s" % ("完成：现在登录后是空库，点 DEMO 按钮加载演示数据" if ok else "部分数据未清空"))
print("=" * 52)
