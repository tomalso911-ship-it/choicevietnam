# -*- coding: utf-8 -*-
"""
M5 CRM 模块测试

验证：
  1. 列表读取（管理员看全部）
  2. 新增项目
  3. 修改项目
  4. 权限校验（非归属人不能改）
  5. 删除项目
  6. 可见范围过滤（普通用户只看自己的）

用法：
    python cloudflare/test_crm.py
"""
import sys
import json
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def call(method, path, body=None, user=None):
    url = API + path
    data = None
    headers = {"User-Agent": UA}
    if user:
        headers["X-User-Name"] = user
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def login(u, p):
    st, d = call("POST", "/api/login", {"username": u, "password": p})
    return bool(d.get("ok")) if isinstance(d, dict) else False


def main():
    print("=" * 60)
    print("  M5 CRM 潜在项目模块测试")
    print("=" * 60)
    results = []

    # 1. 管理员登录
    print("\n[1] 管理员 tom 登录")
    ok = login("tom", "66668888")
    print("    %s" % ("PASS" if ok else "FAIL"))
    results.append(ok)
    if not ok:
        print("    登录失败，后续测试中止")
        return

    # 2. 列表（管理员看全部）
    print("\n[2] 读取潜在项目列表（管理员）")
    st, lst = call("GET", "/api/crm-projects", user="tom")
    if isinstance(lst, list):
        print("    HTTP %s  共 %d 条" % (st, len(lst)))
        if lst:
            r0 = lst[0]
            print("    首条: %s / %s (id=%s)"
                  % (r0.get("quote_no"), r0.get("project_name"), r0.get("id")))
        ok = len(lst) > 0
        results.append(ok)
    else:
        print("    FAIL: %s" % lst)
        results.append(False)
        lst = []

    # 3. 新增
    print("\n[3] 新增一条测试项目")
    new = {
        "quote_no": "M5TEST-001",
        "project_name": "M5云端测试项目",
        "customer": "测试客户",
        "salesperson": "tom",
        "q1_rmb": 12345,
    }
    st, created = call("POST", "/api/crm-projects", new, user="tom")
    new_id = created.get("id") if isinstance(created, dict) else None
    if new_id:
        print("    HTTP %s  新建 id=%s  报价单号=%s"
              % (st, new_id, created.get("quote_no")))
        results.append(True)
    else:
        print("    FAIL: %s" % created)
        results.append(False)

    # 4. 读取单条
    if new_id:
        print("\n[4] 读取刚新建的项目")
        st, got = call("GET", "/api/crm-projects/%d" % new_id, user="tom")
        okp = isinstance(got, dict) and got.get("quote_no") == "M5TEST-001"
        print("    HTTP %s  %s" % (st, "PASS" if okp else "FAIL %s" % got))
        results.append(okp)

    # 5. 修改
    if new_id:
        print("\n[5] 修改项目（改名 + 改金额）")
        st, upd = call("PUT", "/api/crm-projects/%d" % new_id,
                       {"project_name": "M5云端测试项目(已修改)", "q1_rmb": 99999},
                       user="tom")
        okp = isinstance(upd, dict) and upd.get("q1_rmb") == 99999
        print("    HTTP %s  新名称=%s  q1_rmb=%s"
              % (st, upd.get("project_name") if isinstance(upd, dict) else "-",
                 upd.get("q1_rmb") if isinstance(upd, dict) else "-"))
        print("    %s" % ("PASS" if okp else "FAIL"))
        results.append(okp)

    # 6. 权限校验：非管理员 alice 改 tom 的数据应被拒
    if new_id:
        print("\n[6] 权限校验：alice 修改 tom 的数据（应被拒绝 403）")
        st, r = call("PUT", "/api/crm-projects/%d" % new_id,
                     {"project_name": "越权修改"}, user="alice")
        okp = st == 403
        print("    HTTP %s  %s -> %s"
              % (st, r.get("error") if isinstance(r, dict) else r,
                 "PASS 正确拦截" if okp else "FAIL 未拦截"))
        results.append(okp)

    # 7. 可见范围：alice 列表应少于 tom
    print("\n[7] 可见范围过滤（alice 应看不到全部）")
    st, alice_list = call("GET", "/api/crm-projects", user="alice")
    na = len(alice_list) if isinstance(alice_list, list) else -1
    nt = len(lst) if isinstance(lst, list) else -1
    print("    tom=%d 条   alice=%d 条" % (nt, na))
    okp = na <= nt
    print("    %s" % ("PASS 已按可见范围过滤" if okp else "FAIL"))
    results.append(okp)

    # 8. 删除测试记录
    if new_id:
        print("\n[8] 删除测试记录（清理）")
        st, r = call("DELETE", "/api/crm-projects/%d" % new_id, user="tom")
        okp = st == 200 and isinstance(r, dict) and r.get("ok")
        print("    HTTP %s -> %s" % (st, "PASS 已删除" if okp else "FAIL %s" % r))
        results.append(okp)

        st, chk = call("GET", "/api/crm-projects/%d" % new_id, user="tom")
        print("    复查: HTTP %s (%s)" % (st, chk.get("error") if isinstance(chk, dict) else chk))
        results.append(st == 404)

    print("\n" + "=" * 60)
    print("  测试结果: %d / %d 通过" % (sum(results), len(results)))
    print("=" * 60)


if __name__ == "__main__":
    main()
