# -*- coding: utf-8 -*-
"""
M4 端到端测试：验证 Pages 网页 + 云端登录是否真的跑通

用法：
    python cloudflare/test_pages.py
    python cloudflare/test_pages.py tom 66668888
"""
import sys
import json
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PAGE = "https://agi-gs.pages.dev"
API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()


def post(url, body, origin=None):
    data = json.dumps(body).encode("utf-8")
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    if origin:
        headers["Origin"] = origin
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8")), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, {}, dict(e.headers)


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "tom"
    password = sys.argv[2] if len(sys.argv) > 2 else "66668888"

    print("=" * 58)
    print("  M4 端到端测试")
    print("=" * 58)
    results = []

    # 1. Pages 网页可访问
    print("\n[1] Pages 网页访问")
    try:
        st, body = get(PAGE)
        html = body.decode("utf-8", "replace")
        ok = st == 200 and len(html) > 100000
        print("    HTTP %s  大小 %.1f KB -> %s" % (st, len(body) / 1024,
                                                  "PASS" if ok else "FAIL"))
        results.append(ok)
    except Exception as e:
        print("    FAIL: %s" % e)
        results.append(False)

    # 2. 网页内含云端转发脚本
    print("\n[2] 网页已注入云端 API 转发脚本")
    try:
        has = "__CLOUD_API__" in html
        print("    %s" % ("PASS 脚本存在" if has else "FAIL 脚本缺失"))
        results.append(has)
    except Exception as e:
        print("    FAIL: %s" % e)
        results.append(False)

    # 3. 跨域登录（模拟浏览器从 Pages 页面调用 Workers 接口）
    print("\n[3] 浏览器跨域登录（Origin = Pages 域名）")
    st, d, hdrs = post(API + "/api/login",
                       {"username": username, "password": password},
                       origin=PAGE)
    acao = hdrs.get("Access-Control-Allow-Origin", "(无)")
    if d.get("ok"):
        u = d["user"]
        print("    HTTP %s 登录成功: %s (%s) 管理员=%s"
              % (st, u.get("real_name"), u.get("role"), u.get("is_admin")))
        print("    CORS 允许来源: %s" % acao)
        ok = acao == PAGE
        print("    跨域头正确: %s" % ("PASS" if ok else "FAIL"))
        results.append(ok)
    else:
        print("    FAIL 登录失败: %s (HTTP %s)" % (d.get("error"), st))
        results.append(False)

    # 4. /api/me 跨域
    print("\n[4] /api/me 跨域取用户信息")
    try:
        req = urllib.request.Request(API + "/api/me?username=" + username,
                                     headers={"User-Agent": UA, "Origin": PAGE})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
            acao = r.headers.get("Access-Control-Allow-Origin", "(无)")
        if d.get("ok"):
            print("    用户名=%s 角色=%s" % (d["user"].get("username"),
                                          d["user"].get("role")))
            print("    CORS: %s -> %s" % (acao, "PASS" if acao == PAGE else "FAIL"))
            results.append(acao == PAGE)
        else:
            print("    FAIL: %s" % d.get("error"))
            results.append(False)
    except Exception as e:
        print("    FAIL: %s" % e)
        results.append(False)

    print("\n" + "=" * 58)
    print("  测试结果: %d / %d 通过" % (sum(results), len(results)))
    print("=" * 58)
    print("\n  网页地址: %s" % PAGE)
    print("  用浏览器打开，账号 %s 即可登录" % username)


if __name__ == "__main__":
    main()
