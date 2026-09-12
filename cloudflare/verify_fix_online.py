# -*- coding: utf-8 -*-
"""验证线上网页是否已包含卡顿修复"""
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


print("=" * 62)
print("  线上修复验证")
print("=" * 62)

print("\n[1] 导航卡顿修复")
check("已移除宽松锁定判定",
      "el.style.display!=='none') return true" not in html)
check("MutationObserver 忽略导航栏", "tgt.closest('#tbMenu')" in html)
check("fitTopbarFonts 节流", "_fitTopbarBusy" in html)
check("fitTopbarFonts 二分查找", "hi - lo > 0.5" in html)
check("导航锁 6 秒自愈", "_uiLockSince" in html)

print("\n[2] 语言切换修复")
check("setLangDebug 异常隔离",
      "[lang] updateLangSwitchUI failed" in html)
check("语言按钮存在",
      all(('id="dbgLang%s"' % x) in html for x in ["Zh", "En", "Vi"]))

print("\n[3] 之前的功能仍完好")
check("登录页横屏适配", "max-height: 560px" in html)
check("导航滚动条可见", "scrollbar-width: thin" in html)
check("自动滚动到激活标签", "function scrollActiveTabIntoView" in html)
check("云端 API 转发", "agi-gs.tomalso911.workers.dev" in html)

print("\n" + "=" * 62)
print("  结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 62)
sys.exit(0 if all(results) else 1)
