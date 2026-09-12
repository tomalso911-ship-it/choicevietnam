# -*- coding: utf-8 -*-
"""
验证三项修复：
  1. 导航：滚动条可见 + 自动滚动到激活标签
  2. 登录页：横屏矮屏适配（LOGO 缩小，内容不截断）
  3. 空库：登录后看板统计应为 0
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


def get(url, user=None):
    headers = {"User-Agent": UA}
    if user:
        headers["X-User-Name"] = user
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode("utf-8", "replace")


print("=" * 64)
print("  APP 三项修复验证")
print("=" * 64)

st, html = get(PAGE)

# ---------- 1. 导航滚动 ----------
print("\n[1] 导航标签横向滚动")
has_scrollbar_css = "scrollbar-width: thin" in html or "scrollbar-width:thin" in html
has_webkit = "::-webkit-scrollbar-thumb" in html
has_smooth = "scroll-behavior: smooth" in html
has_scroll_fn = "function scrollActiveTabIntoView" in html
has_call_switch = "setTimeout(scrollActiveTabIntoView" in html
has_orient = "orientationchange" in html

check("滚动条已显示（不再隐藏）", has_scrollbar_css or has_webkit,
      "scrollbar-width:thin / webkit-thumb")
check("平滑滚动", has_smooth, "scroll-behavior: smooth")
check("自动滚动到激活标签函数", has_scroll_fn, "scrollActiveTabIntoView()")
check("切换视图时调用该滚动", has_call_switch, "switchView 内已调用")
check("横竖屏切换时重算", has_orient, "orientationchange 监听")

# ---------- 2. 登录页横屏 ----------
print("\n[2] 登录页横屏适配")
has_ls_media = ("orientation: landscape" in html and "max-height: 560px" in html)
has_ls2 = "max-height: 380px" in html
has_logo_small = "width: 58px" in html
has_overflow = "overflow-y: auto" in html

check("横屏矮屏媒体查询存在", has_ls_media, "landscape + max-height:560px")
check("极矮屏二级适配", has_ls2, "max-height:380px")
check("LOGO 横屏缩小", has_logo_small, "150px -> 58px")
check("内容可纵向滚动兜底", has_overflow, "overflow-y:auto")

# ---------- 3. 空库看板 ----------
print("\n[3] 空库状态（登录即 0）")
for path, name in [
    ("/api/crm-projects?scope=all", "潜在项目"),
    ("/api/won-projects", "签约项目"),
    ("/api/lost-projects", "失败项目"),
]:
    st, raw = get(API + path, user="tom")
    d = json.loads(raw)
    n = len(d) if isinstance(d, list) else -1
    check("%s = 0" % name, n == 0, "实际 %d 条" % n)

st, raw = get(API + "/api/users", user="tom")
d = json.loads(raw)
n_users = len(d.get("users", []))
check("用户账号保留（8 个真实账号）", n_users == 8, "实际 %d 个" % n_users)
mgrs = d.get("managers", [])
check("管理员 4 人", len(mgrs) == 4, ", ".join(mgrs))

print("\n" + "=" * 64)
print("  结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 64)
print("\n  验证方式：")
print("   - 网页版：无痕窗口打开 %s" % PAGE)
print("   - APP：下拉刷新即可（无需重装）")
print("=" * 64)
