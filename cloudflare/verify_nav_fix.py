# -*- coding: utf-8 -*-
"""验证导航切换性能修复是否已上线"""
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PAGE = "https://agi-gs.pages.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

req = urllib.request.Request(PAGE, headers={"User-Agent": UA})
with urllib.request.urlopen(req, timeout=60) as r:
    html = r.read().decode("utf-8", "replace")

results = []


def check(name, ok, detail=""):
    print("    %s  %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("          %s" % detail)
    results.append(ok)


print("=" * 64)
print("  导航切换性能修复验证")
print("=" * 64)

print("\n[1] 消除导航误锁（点不动的根因）")
check("严格判定：不再用 getClientRects",
      "el.getClientRects().length > 0" not in html)
check("自适应忽略名单（10秒常驻自动忽略）",
      "_overlayIgnored" in html and "now - _overlayOpenSince[id] > 10000" in html)
check("导航点击坐标兜底",
      "_menu.addEventListener('click'" in html and "nav-locked" in html)

print("\n[2] 消除重复网络请求（慢的根因）")
check("视图数据缓存机制", "function needReloadView" in html)
check("缓存写入标记", "function markViewLoaded" in html)
check("写请求自动失效", "markAllViewsDirty();" in html)
check("DEMO 后全部失效", "if (typeof markAllViewsDirty === 'function') markAllViewsDirty();" in html)

print("\n[3] 减少重复渲染")
check("避免 applyAllPermVisibility 重复调用",
      "if (name !== 'dashboard') {\n    applyAllPermVisibility();" in html
      or "if (name !== 'dashboard') {" in html)

print("\n[4] 之前修复仍保留")
check("登录页横屏适配", "max-height: 560px" in html)
check("导航滚动条可见", "scrollbar-width: thin" in html)
check("记住登录(localStorage)", "saveAuthKeep" in html)
check("语言切换异常隔离", "[lang] updateLangSwitchUI failed" in html)
check("fitTopbarFonts 节流", "_fitTopbarBusy" in html)

print("\n" + "=" * 64)
print("  结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 64)
print("\n  验证方式：")
print("   网页版 - 无痕窗口打开 %s" % PAGE)
print("   APP    - 下拉刷新即可（无需重装）")
print("=" * 64)
sys.exit(0 if all(results) else 1)
