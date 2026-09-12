# -*- coding: utf-8 -*-
"""
逐个用户登录云端 WEB，检查其授权（能看到哪些页面）。

用法:
    python cloudflare/check_users_auth.py
"""
import sys, json, urllib.request, urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

USERS = ["cuong", "travis", "ali", "khoa", "minh"]
PW = "66668888"

# 视图名 -> 该视图可见所需的最少一个可见 perm 区块
VIEW_RULES = {
    "Dashboard(看板)": ["DB-S1","DB-P1","DB-B1","DB-C1","US-LH1","US-LH2",
                       "DB-MT1","DB-FD1","DB-LS1","DB-FX1"],
    "Potential(潜在项目 CRM)": ["CRM-L1"],
    "Won(签约项目)": ["WON-L1"],
    "Failed(失败项目 LOST)": ["LOST-L1"],
    "Approvals(审批)": ["APP-L1","APP-L2","APP-L3"],
    "Users&Auth(用户与授权)": ["USR-L1"],   # 且需 is_admin 或在白名单，下面特殊处理
}
COMMISSION_WHITELIST = ["tom", "cuong", "travis"]


def call(path, method="GET", body=None, as_user=None):
    url = API + path
    data = None
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if as_user:
        headers["X-User-Name"] = as_user
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {"ok": False, "error": str(e)}
    except Exception as e:
        return 0, {"ok": False, "error": str(e)}


def get_perms(user):
    """返回 (ok, info)  info: {role,is_admin,position,perms,status}"""
    # 先登录（触发密码加密升级）
    st, login = call("/api/login", "POST",
                     {"username": user, "password": PW})
    if not login.get("ok"):
        return False, {"login_error": login.get("error"), "http": st}
    u = login.get("user", {})
    # 再拉 /api/me 取完整 perms
    st2, me = call("/api/me?username=" + user, as_user=user)
    perms = {}
    if me.get("ok") and me.get("user", {}).get("perms"):
        perms = me["user"]["perms"]
    elif u.get("perms"):
        perms = u["perms"]
    return True, {
        "role": u.get("role"),
        "is_admin": u.get("is_admin"),
        "position": u.get("position"),
        "status": u.get("status"),
        "perms": perms,
    }


def visible_views(info):
    perms = info.get("perms", {})
    is_admin = bool(info.get("is_admin"))
    me = None  # 未知用户名（本函数通用）
    out = []
    for view, bids in VIEW_RULES.items():
        if view.startswith("Users"):
            ok = is_admin or any(perms.get(b, {}).get("decision") != "hide" for b in bids)
        else:
            ok = any(perms.get(b, {}).get("decision") != "hide" for b in bids)
        out.append((view, ok))
    return out


def main():
    for user in USERS:
        print("\n" + "=" * 64)
        print("  用户: %s" % user)
        print("=" * 64)
        ok, info = get_perms(user)
        if not ok:
            print("  !! 登录失败: %s (HTTP %s)" % (info.get("login_error"), info.get("http")))
            continue
        print("  角色: %s   职位: %s   管理员: %s   状态: %s"
              % (info["role"], info["position"], info["is_admin"], info["status"]))
        perms = info["perms"]
        # 隐藏的区块
        hidden = [b for b, v in perms.items()
                  if isinstance(v, dict) and v.get("decision") == "hide"]
        print("  被隐藏的区块 (%d): %s" % (len(hidden), ", ".join(hidden) or "无"))
        # 视图可见性
        print("  -- 可见页面 --")
        for view, vis in visible_views(info):
            print("     [%s] %s" % ("可看" if vis else "隐藏", view))
        # 佣金页
        comm = user.lower() in COMMISSION_WHITELIST
        print("     [%s] Personal Commission (白名单:%s)"
              % ("可看(暗门)" if comm else "不可看", ",".join(COMMISSION_WHITELIST)))


if __name__ == "__main__":
    main()
