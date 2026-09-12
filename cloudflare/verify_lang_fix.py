# -*- coding: utf-8 -*-
"""验证语言切换性能优化是否已上线"""
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
print("  语言切换性能优化验证")
print("=" * 64)

print("\n[1] 消除全表重建（主要瓶颈）")
check("WON 表格只在可见时重建",
      "var wonSec = document.getElementById('view-won');" in html
      and "if (wonVisible) {" in html)
check("审批列表只在可见时重建",
      "var apprSec = document.getElementById('view-approvals');" in html
      and "if (!apprSec || apprSec.classList.contains('active'))" in html)

print("\n[2] 立即反馈 + 重活延后")
check("先高亮按钮（立即反馈）",
      "try { updateLangSwitchUI(); } catch(e) { console.warn('[lang] updateLangSwitchUI failed:', e); }" in html)
check("重活延后到下一帧",
      "requestAnimationFrame || window.setTimeout" in html)
check("图表只在看板可见时重绘",
      "var dashVisible = !dashSec || dashSec.classList.contains('active');" in html)

print("\n[3] 数据一致性保证")
check("语言切换标记视图失效",
      "if (typeof markAllViewsDirty === 'function') markAllViewsDirty();" in html)

print("\n[4] 之前修复仍保留")
check("导航误锁修复", "_overlayIgnored" in html)
check("视图缓存机制", "function needReloadView" in html)
check("异常隔离", "[lang] updateLangSwitchUI failed" in html)
check("记住登录", "saveAuthKeep" in html)
check("横屏登录适配", "max-height: 560px" in html)

print("\n" + "=" * 64)
print("  结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 64)
sys.exit(0 if all(results) else 1)
