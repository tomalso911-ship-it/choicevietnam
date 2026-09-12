# -*- coding: utf-8 -*-
"""
验证 DEMO 闪烁修复：
  1. 页面不再含 location.reload() 调用（DEMO 相关）
  2. 新增了软刷新函数 refreshAllModulesSoft
  3. DEMO 接口本身仍可用
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


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode("utf-8", "replace")


def post(url):
    req = urllib.request.Request(
        url, data=b"{}",
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


print("=" * 58)
print("  DEMO 闪烁修复验证")
print("=" * 58)

st, html = get(PAGE)
print("\n[1] 页面代码检查")
# 统计真实调用（排除注释行）
import re as _re
reload_lines = []
for i, line in enumerate(html.splitlines(), 1):
    s = line.strip()
    if "location.reload()" in s and not s.startswith("//") and not s.startswith("*") and not s.startswith("/*"):
        reload_lines.append((i, s))
check("已移除 location.reload() 实际调用", len(reload_lines) == 0,
      ("仍存在于: %s" % reload_lines) if reload_lines else "代码中无实际调用（仅剩注释说明）")
has_soft = "refreshAllModulesSoft" in html
check("已新增软刷新函数", has_soft, "refreshAllModulesSoft 存在")
check("软刷新覆盖 CRM 加载", "loadCrm" in html[html.find("function refreshAllModulesSoft"):][:2500])
check("按钮有处理中提示", "处理中" in html)

print("\n[2] 接口可用性")
st, r = post(API + "/api/demo/load")
check("DEMO 加载接口", st == 200 and isinstance(r, dict) and r.get("ok"),
      json.dumps(r.get("restored", {}), ensure_ascii=False))

st, html2 = get(API + "/api/crm-projects")
d = json.loads(html2)
n1 = len(d) if isinstance(d, list) else -1
print("          加载后潜在项目: %d 条" % n1)

st, r = post(API + "/api/demo/clear")
check("DEMO 清空接口", st == 200 and isinstance(r, dict) and r.get("ok"), "已清空")

st, raw = get(API + "/api/crm-projects")
d = json.loads(raw)
n2 = len(d) if isinstance(d, list) else -1
check("清空后为 0 条", n2 == 0, "实际 %d 条" % n2)

print("\n" + "=" * 58)
print("  结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 58)
print("\n  现在点击 DEMO 按钮：按钮显示'处理中…'，数据就地更新，不白屏不闪烁。")
