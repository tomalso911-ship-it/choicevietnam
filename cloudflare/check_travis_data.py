# -*- coding: utf-8 -*-
"""用真实会话 token 验证 travis 能拉到多少数据，并打印其区块 decision"""
import sys, json, urllib.request, urllib.error
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

def login(user):
    req = urllib.request.Request(API + "/api/login",
        data=json.dumps({"username": user, "password": "66668888"}).encode(),
        headers={"User-Agent": UA, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))

def get(path, token):
    req = urllib.request.Request(API + path,
        headers={"User-Agent": UA, "Accept": "application/json",
                 "Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, json.loads(r.read().decode("utf-8"))

def cnt(d):
    if isinstance(d, list): return len(d)
    for k in ("projects","data","items","results"):
        if isinstance(d.get(k), list): return len(d[k])
    return d.get("error") if isinstance(d, dict) else d

for u in ["tom", "travis", "ali"]:
    print("\n========== %s ==========" % u)
    L = login(u)
    tok = L.get("token", "")
    print("  token长度:", len(tok))
    st, me = get("/api/me?username=" + u, tok)
    perms = (me.get("user", {}) or {}).get("perms", {}) if me.get("ok") else {}
    print("  vis_can_see_me =", me.get("user", {}).get("vis_can_see_me"))
    print("  vis_he_can_see =", me.get("user", {}).get("vis_he_can_see"))
    # 关键区块 decision
    for bid in ["CRM-L1","WON-L1","LOST-L1","CRM-D2","WON-D2","LOST-D2"]:
        v = perms.get(bid, {})
        print("    %-8s decision=%s" % (bid, v.get("decision") if isinstance(v, dict) else v))
    for ep in ["/api/crm-projects", "/api/won-projects", "/api/lost-projects"]:
        st2, d = get(ep, tok)
        print("  %-20s HTTP %s -> 条数 %s" % (ep, st2, cnt(d)))
