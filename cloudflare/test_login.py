# -*- coding: utf-8 -*-
"""
云端登录接口测试脚本（M3）

用法：
    python cloudflare/test_login.py
    python cloudflare/test_login.py tom 66668888

测试内容：
    1. 错误密码 -> 应拒绝
    2. 正确密码 -> 应成功，且首次登录自动把明文密码升级为加密
    3. 再次登录 -> 用加密密码验证，仍能成功
    4. /api/me   -> 取用户信息
"""
import os
import sys
import json
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://agi-gs.tomalso911.workers.dev"


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def call(path, method="GET", body=None):
    url = BASE + path
    data = None
    # Cloudflare 会拦截没有浏览器标识的请求（错误码 1010），必须伪装成浏览器
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))
    except Exception as e:
        return 0, {"ok": False, "error": str(e)}


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "tom"
    password = sys.argv[2] if len(sys.argv) > 2 else "66668888"

    print("=" * 56)
    print("  M3 登录接口测试")
    print("  目标: %s" % BASE)
    print("  账号: %s" % username)
    print("=" * 56)

    # 1. 错误密码
    print("\n[1] 错误密码测试（应失败）")
    st, r = call("/api/login", "POST", {"username": username, "password": "wrong_pw_123"})
    print("    HTTP %s -> %s" % (st, r.get("error") or r.get("ok")))
    ok1 = (not r.get("ok")) and st == 200
    print("    结果: %s" % ("PASS 正确拒绝" if ok1 else "FAIL"))

    # 2. 正确密码（首次，触发加密升级）
    print("\n[2] 正确密码登录（首次，应触发密码加密升级）")
    st, r = call("/api/login", "POST", {"username": username, "password": password})
    if r.get("ok"):
        u = r.get("user", {})
        print("    登录成功: %s (%s)" % (u.get("real_name"), u.get("role")))
        print("    管理员: %s" % u.get("is_admin"))
        print("    状态  : %s" % u.get("status"))
        print("    密码已升级为加密: %s" % r.get("password_upgraded"))
        ok2 = True
    else:
        print("    登录失败: %s" % r.get("error"))
        ok2 = False

    # 3. 再次登录（用加密后的密码验证）
    print("\n[3] 再次登录（验证加密密码可用）")
    st, r = call("/api/login", "POST", {"username": username, "password": password})
    if r.get("ok"):
        print("    登录成功，password_upgraded = %s（应为 False，已是加密）"
              % r.get("password_upgraded"))
        ok3 = True
    else:
        print("    登录失败: %s" % r.get("error"))
        ok3 = False

    # 4. /api/me
    print("\n[4] /api/me 取用户信息")
    st, r = call("/api/me?username=" + username)
    if r.get("ok"):
        print("    用户名: %s  角色: %s  管理员: %s"
              % (r["user"].get("username"), r["user"].get("role"),
                 r["user"].get("is_admin")))
        ok4 = True
    else:
        print("    失败: %s" % r.get("error"))
        ok4 = False

    # 5. 不存在的用户
    print("\n[5] 不存在的用户（应失败）")
    st, r = call("/api/login", "POST",
                 {"username": "no_such_user_xyz", "password": "123456"})
    ok5 = not r.get("ok")
    print("    结果: %s (%s)" % ("PASS 正确拒绝" if ok5 else "FAIL", r.get("error")))

    print("\n" + "=" * 56)
    passed = sum([ok1, ok2, ok3, ok4, ok5])
    print("  测试结果: %d / 5 通过" % passed)
    print("=" * 56)


if __name__ == "__main__":
    main()
