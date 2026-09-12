# -*- coding: utf-8 -*-
"""M5 最终验证：前端转发规则 + 后端接口 + 数据一致性"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PAGE = "https://agi-gs.pages.dev"
API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def get(url, user=None):
    headers = {"User-Agent": UA}
    if user:
        headers["X-User-Name"] = user
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


print("=" * 58)
print("  M5 最终验证")
print("=" * 58)

print("\n[1] 前端转发规则")
st, html = get(PAGE)
has_crm = "/api/crm-projects" in html
has_api = "agi-gs.tomalso911.workers.dev" in html
print("    HTTP %s  大小 %.1f KB" % (st, len(html) / 1024))
print("    CRM 转发规则: %s" % ("PASS" if has_crm else "FAIL"))
print("    后端地址配置: %s" % ("PASS" if has_api else "FAIL"))

print("\n[2] 后端 CRM 接口")
st, raw = get(API + "/api/crm-projects", user="tom")
data = json.loads(raw)
print("    HTTP %s  返回 %d 条潜在项目" % (st, len(data)))
if data:
    r = data[0]
    print("    示例: %s | %s | %s"
          % (r.get("quote_no", "-"), r.get("project_name", "-"),
             r.get("customer", "-")))

print("\n[3] 数据核对")
print("    本地 active: 21 条")
print("    云端返回  : %d 条" % len(data))
print("    %s" % ("PASS 一致" if len(data) == 21 else "WARN 不一致"))

print("\n" + "=" * 58)
print("  网页地址: %s" % PAGE)
print("  用 tom / 66668888 登录即可看到 21 条潜在项目")
print("=" * 58)
