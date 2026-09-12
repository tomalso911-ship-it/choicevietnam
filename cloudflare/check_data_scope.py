# -*- coding: utf-8 -*-
"""对比不同用户能拉到的业务数据条数（定位 travis 页面空白根因）"""
import sys, json, urllib.request, urllib.error
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

def call(path, as_user=None):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if as_user:
        headers["X-User-Name"] = as_user
    req = urllib.request.Request(API + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, []
    except Exception as e:
        return 0, {"error": str(e)}

def count_list(d):
    if isinstance(d, list):
        return len(d)
    if isinstance(d, dict):
        for k in ("projects","data","items","results"):
            if isinstance(d.get(k), list):
                return len(d[k])
        if "error" in d:
            return "ERR:"+str(d["error"])
    return d

for u in ["tom", "travis", "ali", "khoa", "minh"]:
    print("\n=== 用户 %s ===" % u)
    for ep in ["/api/crm-projects", "/api/won-projects", "/api/lost-projects"]:
        st, d = call(ep, as_user=u)
        print("  %-22s HTTP %s -> 条数 %s" % (ep, st, count_list(d)))
    # 看 vis 范围
    st, me = call("/api/me?username=" + u, as_user=u)
    if isinstance(me, dict) and me.get("user"):
        uu = me["user"]
        print("  vis_can_see_me = %s" % uu.get("vis_can_see_me"))
        print("  vis_he_can_see = %s" % uu.get("vis_he_can_see"))
