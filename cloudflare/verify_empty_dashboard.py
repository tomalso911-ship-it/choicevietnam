# -*- coding: utf-8 -*-
"""
验证空库状态下看板 CRM/WON/LOST 图表区域不残留旧数据。

注意：只检查 API 和响应头，浏览器端的 Chart 渲染是否残留需要人工验证。
"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
PAGE = "https://agi-gs.pages.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def req(url, head=False):
    r = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD" if head else "GET")
    return urllib.request.urlopen(r, timeout=60)


print("=" * 62)
print("  空库 + 缓存控制验证")
print("=" * 62)

# 1. 确认云端为空
print("\n[1] 云端业务数据")
for path, name in [
    ("/api/crm-projects?scope=all", "潜在项目"),
    ("/api/won-projects", "签约项目"),
    ("/api/lost-projects", "失败项目"),
]:
    with req(API + path) as r:
        d = json.loads(r.read().decode("utf-8"))
        n = len(d) if isinstance(d, list) else -1
        cache = r.headers.get("Cache-Control", "")
        print("    %-10s %2d 条   Cache-Control: %s" % (name, n, cache))

# 2. 检查响应头是否禁止缓存
print("\n[2] 缓存控制头")
for path in ["/api/crm-projects", "/api/won-projects", "/api/lost-projects", "/api/users"]:
    with req(API + path) as r:
        cc = r.headers.get("Cache-Control", "")
        ok = "no-store" in cc or "no-cache" in cc
        print("    %-32s %s" % (path, "PASS" if ok else "FAIL - %s" % cc))

# 3. 检查网页中是否包含隐藏 section 的逻辑
print("\n[3] 前端看板空数据隐藏逻辑")
with req(PAGE) as r:
    html = r.read().decode("utf-8", "replace")
    has_crm_hide = "dashCrmSection" in html and "sec.style.display = 'none'" in html
    has_cache = "init.cache = init.cache || 'no-store'" in html
    print("    CRM section 空数据隐藏代码: %s" % ("存在" if has_crm_hide else "未找到"))
    print("    fetch 禁用缓存代码          : %s" % ("存在" if has_cache else "未找到"))

print("\n" + "=" * 62)
print("  请手动验证：用无痕窗口打开 %s" % PAGE)
print("  登录后看板应只有顶部 6 张卡片为 0，CRM/WON/LOST 图表区域不显示。")
print("=" * 62)
