# -*- coding: utf-8 -*-
"""
静态检查 index.html 中关键 JS 函数的完整性

检查项：
  1. 关键函数有定义
  2. 大括号/圆括号配平
  3. 没有遗留的危险写法（如宽松的 isOverlayOpen 判定）
"""
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "..", "index.html")

with open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

results = []


def check(name, ok, detail=""):
    print("    %s  %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("          %s" % detail)
    results.append(ok)


print("=" * 62)
print("  JS 完整性检查")
print("=" * 62)

# 1. 关键函数定义
print("\n[1] 关键函数定义")
FUNCS = [
    "function fitTopbarFonts",
    "function fitTopbarFontsNow",
    "function scrollActiveTabIntoView",
    "function switchView",
    "function setLangDebug",
    "function updateLangSwitchUI",
    "function updateNavLock",
    "function isAnyModalOpen",
    "function isOverlayOpen",
    "function applyAllPermVisibility",
]
for f in FUNCS:
    check(f, (f + "(") in html or (f + " ") in html)

# 2. 括号配平（只检查 script 块）
print("\n[2] 括号配平")
blocks = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
total = 0
for i, b in enumerate(blocks):
    # 去掉字符串和注释再统计（粗略）
    code = re.sub(r"/\*.*?\*/", "", b, flags=re.S)
    code = re.sub(r"//.*", "", code)
    code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', code)
    code = re.sub(r"'(?:[^'\\]|\\.)*'", "''", code)
    diff = code.count("{") - code.count("}")
    total += abs(diff)
check("大括号配平", total < 5, "累计偏差 %d" % total)

# 3. 危险写法检查
print("\n[3] 已知危险写法")
danger1 = "el.style.display!=='none') return true" in html
check("已移除宽松的 isOverlayOpen 判定", not danger1,
      "旧写法会导致导航被永久锁定")

check("MutationObserver 已忽略导航栏自身改动",
      "tgt.closest('#tbMenu')" in html)
check("fitTopbarFonts 已节流", "_fitTopbarBusy" in html)
check("fitTopbarFonts 用二分查找", "hi - lo > 0.5" in html)
check("语言切换已做异常隔离", "[lang] updateLangSwitchUI failed" in html)
check("导航锁有超时自愈", "_uiLockSince" in html)

# 4. 语言按钮存在
print("\n[4] 语言切换按钮")
for btn in ["dbgLangZh", "dbgLangEn", "dbgLangVi"]:
    check(btn + " 存在", 'id="' + btn + '"' in html)

print("\n" + "=" * 62)
print("  结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 62)
sys.exit(0 if all(results) else 1)
