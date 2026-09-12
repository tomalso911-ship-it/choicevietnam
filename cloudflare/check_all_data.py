# -*- coding: utf-8 -*-
"""逐个登录，打印关键区块 decision + 实际拉到的数据条数"""
import sys, json, urllib.request
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

def login(u):
    req = urllib.request.Request(API + "/api/login",
        data=json.dumps({"username": u, "password": "66668888"}).encode(),
        headers={"User-Agent": UA, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))

def get(path, tok):
    try:
        req = urllib.request.Request(API + path,
            headers={"User-Agent": UA, "Accept": "application/json",
                     "Authorization": "Bearer " + tok})
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cnt(d):
    if isinstance(d, list): return len(d)
    for k in ("projects","data","items","results"):
        if isinstance(d.get(k), list): return len(d[k])
    return d.get("error") if isinstance(d, dict) else d

def as_obj(x):
    if isinstance(x, str):
        try: return json.loads(x)
        except Exception: return {}
    return x or {}

KEYS = ["CRM-L1","CRM-D2","WON-L1","WON-D2","WON-P345","LOST-L1","LOST-D2","USR-L1","APP-L1"]
for u in ["cuong","travis","ali","khoa","minh"]:
    L = login(u); tok = L.get("token","")
    me = get("/api/me?username="+u, tok)
    if not isinstance(me, dict):
        me = {"ok": False, "error": str(me)}
    uu = as_obj(me.get("user")) if me.get("ok") else {}
    perms = as_obj(uu.get("perms"))
    print("\n===== %s (role=%s pos=%s) =====" % (u, uu.get("role"), uu.get("position")))
    for k in KEYS:
        v = perms.get(k,{})
        v = as_obj(v)
        print("   %-9s %s" % (k, v.get("decision") if isinstance(v,dict) else v))
    print("   vis_can_see_me=%s  vis_he_can_see=%s" % (uu.get("vis_can_see_me"), uu.get("vis_he_can_see")))
    for ep in ["/api/crm-projects","/api/won-projects","/api/lost-projects"]:
        d = get(ep, tok)
        print("   %-20s -> %s" % (ep, cnt(d)))
