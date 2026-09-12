# -*- coding: utf-8 -*-
"""
验证三个修复：
  1. 页面不再包含 _bust 跳转代码
  2. 首次加载不再重定向（HTTP 200，无跳转）
  3. 登录后是空库（0 条业务数据）
"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PAGE = "https://agi-gs.pages.dev"
API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

results = []


def check(name, ok, detail=""):
    print("    %s  %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("          %s" % detail)
    results.append(ok)


def get(url, user=None, follow=True):
    headers = {"User-Agent": UA}
    if user:
        headers["X-User-Name"] = user
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode("utf-8", "replace"), r.geturl()


print("=" * 58)
print("  修复验证")
print("=" * 58)

print("\n[1] 跳转代码已移除")
st, html, final_url = get(PAGE)
has_bust = "_bust=" in html and "location.replace" in html
check("页面不再含强制跳转", not has_bust,
      "HTTP %s  最终URL: %s" % (st, final_url))

print("\n[2] 首次加载无重定向")
redirected = final_url.rstrip("/") != PAGE.rstrip("/")
check("直接返回 200，无跳转", (not redirected) and st == 200,
      "请求: %s" % PAGE + "\n          实际: %s" % final_url)

print("\n[3] 空库状态（未点 DEMO 前）")
for path, key in [
    ("/api/crm-projects?scope=all", "潜在项目"),
    ("/api/won-projects", "签约项目"),
    ("/api/lost-projects", "失败项目"),
]:
    st, raw, _ = get(API + path, user="tom")
    d = json.loads(raw)
    n = len(d) if isinstance(d, list) else -1
    check("%s = 0 条" % key, n == 0, "HTTP %s  实际 %d 条" % (st, n))

st, raw, _ = get(API + "/api/approval-requests?scope=all", user="tom")
d = json.loads(raw)
n = len(d.get("items", [])) if isinstance(d, dict) else -1
check("审批单 = 0 条", n == 0, "HTTP %s  实际 %d 条" % (st, n))

print("\n[4] 用户账号保留")
st, raw, _ = get(API + "/api/users", user="tom")
d = json.loads(raw)
n = len(d.get("users", [])) if isinstance(d, dict) else 0
mgrs = d.get("managers", []) if isinstance(d, dict) else []
check("用户账号仍在", n > 0, "%d 个账号  管理员: %s" % (n, ", ".join(mgrs)))

print("\n[5] DEMO 按钮可用（模拟点击后应加载数据）")
data = json.dumps({}).encode()
req = urllib.request.Request(
    API + "/api/demo/load", data=data,
    headers={"User-Agent": UA, "Content-Type": "application/json"},
    method="POST")
with urllib.request.urlopen(req, timeout=90) as r:
    res = json.loads(r.read().decode("utf-8"))
restored = res.get("restored", {}) if isinstance(res, dict) else {}
check("DEMO 加载成功", bool(res.get("ok")),
      json.dumps(restored, ensure_ascii=False))

st, raw, _ = get(API + "/api/crm-projects?scope=all", user="tom")
d = json.loads(raw)
n = len(d) if isinstance(d, list) else -1
print("          加载后潜在项目: %d 条（effective active）" % n)

print("\n" + "=" * 58)
print("  结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 58)
print("\n  提示：验证会加载演示数据。要回到空库请运行：")
print("        python cloudflare/reset_empty.py")
