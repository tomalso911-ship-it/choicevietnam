# -*- coding: utf-8 -*-
"""
M7 测试：用户管理 + 管理员任命 + 附件(R2) + DEMO 演示数据
"""
import sys
import json
import uuid
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

results = []


def call(method, path, body=None, user=None, raw=False):
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
        with urllib.request.urlopen(req, timeout=40) as r:
            if raw:
                return r.status, r.read()
            rawb = r.read().decode("utf-8")
            try:
                return r.status, json.loads(rawb)
            except Exception:
                return r.status, rawb
    except urllib.error.HTTPError as e:
        rawb = e.read().decode("utf-8", "replace")
        if raw:
            return e.code, rawb.encode()
        try:
            return e.code, json.loads(rawb)
        except Exception:
            return e.code, rawb


def check(name, ok, detail=""):
    print("    %s  %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("          %s" % detail)
    results.append(ok)


def upload_file(pid, content, filename):
    """multipart 上传"""
    boundary = "----M7Test" + uuid.uuid4().hex
    body = []
    body.append(("--%s\r\n" % boundary).encode())
    body.append(('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode())
    body.append(b"Content-Type: application/pdf\r\n\r\n")
    body.append(content)
    body.append(("\r\n--%s--\r\n" % boundary).encode())
    data = b"".join(body)
    req = urllib.request.Request(
        API + "/api/won-projects/%d/attachments" % pid,
        data=data,
        headers={
            "User-Agent": UA,
            "X-User-Name": "tom",
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def main():
    print("=" * 62)
    print("  M7 测试：用户管理 + 附件(R2) + DEMO")
    print("=" * 62)

    # ---------------- 用户管理 ----------------
    print("\n== 用户与权限管理 ==")
    st, d = call("GET", "/api/users", user="tom")
    users = d.get("users", []) if isinstance(d, dict) else []
    managers = d.get("managers", []) if isinstance(d, dict) else []
    check("读取用户列表", isinstance(d, dict) and len(users) > 0,
          "HTTP %s  共 %d 个用户  管理员: %s" % (st, len(users), ", ".join(managers)))

    # 新增用户
    test_user = "m7test_" + uuid.uuid4().hex[:6]
    st, r = call("POST", "/api/users", {
        "username": test_user,
        "real_name": "M7测试用户",
        "position": "销售",
        "status": "active",
    }, user="tom")
    new_uid = r.get("id") if isinstance(r, dict) else None
    check("新增用户(管理员直达)", new_uid is not None,
          "HTTP %s  id=%s  账号=%s" % (st, new_uid, test_user))

    # 销售职位的 WON 权限应被锁死
    if new_uid:
        st, d2 = call("GET", "/api/users", user="tom")
        tgt = None
        for u in (d2.get("users", []) if isinstance(d2, dict) else []):
            if u.get("username") == test_user:
                tgt = u
                break
        if tgt:
            perms = tgt.get("perms") or {}
            locked = all(
                (perms.get(b) or {}).get("decision") == "hide"
                for b in ["WON-D2", "WON-D3", "WON-P345"]
            )
            check("销售职位 WON 权限自动锁死", locked,
                  "WON-D2/D3/P345 应为 hide")

    # 权限闸门：ali 无权限新增用户
    st, r = call("POST", "/api/users", {
        "username": "hacker_x", "real_name": "越权测试",
    }, user="ali")
    check("无权限用户被拦截(新增)", st == 403,
          "HTTP %s  %s" % (st, r.get("error") if isinstance(r, dict) else str(r)[:60]))

    # 修改用户
    if new_uid:
        st, r = call("PUT", "/api/users/%d" % new_uid, {
            "real_name": "M7测试用户(已改名)",
            "position": "销售",
            "status": "active",
            "perms": {},
        }, user="tom")
        check("修改用户", st == 200 and isinstance(r, dict) and r.get("ok"),
              "HTTP %s" % st)

    # 管理员约束：不能移除 tom
    st, r = call("PUT", "/api/managers", {"managers": ["admin"]}, user="tom")
    check("管理员约束(tom 不可移除)", st == 400,
          "HTTP %s  %s" % (st, r.get("error") if isinstance(r, dict) else str(r)[:60]))

    st, r = call("GET", "/api/managers", user="tom")
    check("读取管理员名单", st == 200 and isinstance(r, dict),
          "HTTP %s  %s" % (st, r.get("managers") if isinstance(r, dict) else "-"))

    # 删除测试用户
    if new_uid:
        st, r = call("DELETE", "/api/users/%d" % new_uid, user="tom")
        check("删除测试用户", st == 200 and isinstance(r, dict) and r.get("ok"),
              "HTTP %s" % st)

    # ---------------- 附件 R2 ----------------
    print("\n== 附件上传 (R2 文件柜) ==")
    st, won = call("GET", "/api/won-projects", user="tom")
    pid = won[0]["id"] if isinstance(won, list) and won else None
    if pid:
        # 最小合法 PDF
        pdf = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
               b"trailer<</Root 1 0 R>>\n%%EOF\n")
        st, r = upload_file(pid, pdf, "M7test.pdf")
        att_key = None
        if isinstance(r, dict) and r.get("attachments"):
            atts = r["attachments"]
            # 数据库里存的是 JSON 字符串
            if isinstance(atts, str):
                try:
                    atts = json.loads(atts)
                except Exception:
                    atts = []
            if atts:
                att_key = atts[-1].get("filename")
        check("上传附件到 R2", att_key is not None,
              "HTTP %s  key=%s" % (st, att_key))

        if att_key:
            st, content = call("GET", "/api/files/" + att_key, user="tom", raw=True)
            ok = st == 200 and isinstance(content, bytes) and content.startswith(b"%PDF")
            check("下载附件(从 R2)", ok,
                  "HTTP %s  大小 %d 字节" % (st, len(content) if isinstance(content, bytes) else 0))
    else:
        check("上传附件到 R2", False, "无签约项目可挂载")

    # ---------------- DEMO ----------------
    print("\n== DEMO 演示数据 ==")
    st, r = call("GET", "/api/crm-projects", user="tom")
    before = len(r) if isinstance(r, list) else -1
    print("          清空前 CRM 条数: %d" % before)

    st, r = call("POST", "/api/demo/clear")
    check("DEMO 清空", st == 200 and isinstance(r, dict) and r.get("ok"),
          "HTTP %s" % st)

    st, r = call("POST", "/api/demo/load")
    ok_load = st == 200 and isinstance(r, dict) and r.get("ok")
    restored = (r.get("restored") or {}) if isinstance(r, dict) else {}
    check("DEMO 还原(从 R2 快照)", ok_load,
          "HTTP %s  还原: %s" % (st, json.dumps(restored, ensure_ascii=False)))

    st, r = call("GET", "/api/crm-projects", user="tom")
    after = len(r) if isinstance(r, list) else -1
    print("          还原后 CRM 条数: %d" % after)
    check("还原后数据可读", after > 0, "共 %d 条" % after)

    print("\n" + "=" * 62)
    print("  测试结果: %d / %d 通过" % (sum(results), len(results)))
    print("=" * 62)


if __name__ == "__main__":
    main()
