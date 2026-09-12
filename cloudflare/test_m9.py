# -*- coding: utf-8 -*-
"""
M9 测试：验证 6 个价格接口从云端 R2 正常返回
"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

results = []


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return 0, {"error": str(e)}


def check(name, ok, detail=""):
    print("    %s  %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("          %s" % detail)
    results.append(ok)


# 待测接口：(路径, 最少应有 labels 数, 最少应有 series 数)
CASES = [
    ("/api/metal-prices?cur=USD", 30, 4),
    ("/api/metal-prices?cur=RMB", 30, 4),
    ("/api/metal-prices?cur=VND", 30, 4),
    ("/api/feed-prices?cur=USD", 40, 4),
    ("/api/feed-prices?cur=RMB", 40, 4),
    ("/api/feed-prices?cur=VND", 40, 4),
    ("/api/livestock-prices?cur=RMB", 50, 3),
    ("/api/livestock-prices?cur=USD", 50, 3),
    ("/api/livestock-prices?cur=VND", 50, 3),
    ("/api/livestock-farmgate?cur=USD", 60, 3),
    ("/api/livestock-farmgate?cur=RMB", 60, 3),
    ("/api/livestock-farmgate?cur=VND", 60, 3),
]

print("=" * 62)
print("  M9 价格模块测试")
print("=" * 62)

print("\n== 图表类接口 ==")
for path, min_lab, min_ser in CASES:
    st, d = get(path)
    if not isinstance(d, dict) or d.get("error"):
        check(path, False, "HTTP %s  %s" % (st, d.get("error") if isinstance(d, dict) else d))
        continue
    labels = d.get("labels") or []
    series = d.get("series") or {}
    ok = st == 200 and len(labels) >= min_lab and len(series) >= min_ser
    check(path, ok, "labels=%d series=%d  更新于 %s"
          % (len(labels), len(series), d.get("_updated", "-")))

print("\n== 汇率接口 ==")
st, d = get("/api/fx-rates")
labels = d.get("labels") or [] if isinstance(d, dict) else []
series = d.get("series") or {} if isinstance(d, dict) else {}
check("/api/fx-rates", st == 200 and len(labels) >= 30 and len(series) >= 3,
      "labels=%d series=%d" % (len(labels), len(series)))

print("\n== 零售原始数据 ==")
st, d = get("/api/livestock-retail-raw")
if isinstance(d, dict) and d.get("error"):
    check("/api/livestock-retail-raw", False, str(d.get("error"))[:70])
elif isinstance(d, list):
    check("/api/livestock-retail-raw", st == 200 and len(d) > 0,
          "共 %d 条记录" % len(d))
else:
    check("/api/livestock-retail-raw", st == 200,
          "类型 %s，键: %s" % (type(d).__name__,
                            list(d.keys())[:6] if isinstance(d, dict) else "-"))

print("\n" + "=" * 62)
print("  测试结果: %d / %d 通过" % (sum(results), len(results)))
print("=" * 62)
