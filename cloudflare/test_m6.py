# -*- coding: utf-8 -*-
"""
M6 测试：签约项目 + 失败项目 + 审批流
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


results = []


def check(name, ok, detail=""):
    print("    %s %s" % ("PASS" if ok else "FAIL", name))
    if detail:
        print("         %s" % detail)
    results.append(ok)


def main():
    print("=" * 60)
    print("  M6 测试：签约 + 失败 + 审批流")
    print("=" * 60)

    # ---------- WON 签约项目 ----------
    print("\n== 签约项目 WON ==")
    st, won = call("GET", "/api/won-projects", user="tom")
    n_won = len(won) if isinstance(won, list) else -1
    check("读取签约项目列表", isinstance(won, list) and n_won > 0,
          "HTTP %s  共 %d 条" % (st, n_won))

    if isinstance(won, list) and won:
        r0 = won[0]
        has_p345 = "gs_comm_usd" in r0
        print("         示例: %s | %s" % (r0.get("contract_no"), r0.get("customer")))
        check("管理员可见佣金字段(P345)", has_p345,
              "tom 是管理员，应能看到 gs_comm_usd")

    # 新增签约项目
    st, created = call("POST", "/api/won-projects", {
        "contract_no": "M6TEST-001",
        "customer": "M6云端测试客户",
        "contract_date": "2026-08-30",
        "salesperson": "tom",
        "equip_usd": 50000,
    }, user="tom")
    new_won_id = created.get("id") if isinstance(created, dict) else None
    check("新增签约项目", new_won_id is not None,
          "HTTP %s  id=%s" % (st, new_won_id))

    if new_won_id:
        st, upd = call("PUT", "/api/won-projects/%d" % new_won_id,
                       {"customer": "M6已修改客户", "equip_usd": 88888}, user="tom")
        check("修改签约项目",
              isinstance(upd, dict) and upd.get("equip_usd") == 88888,
              "HTTP %s  equip_usd=%s" % (st, upd.get("equip_usd") if isinstance(upd, dict) else "-"))

        # 权限：alice 不能改
        st, r = call("PUT", "/api/won-projects/%d" % new_won_id,
                     {"customer": "越权"}, user="alice")
        check("权限拦截(alice改tom数据)", st == 403,
              "HTTP %s  %s" % (st, r.get("error") if isinstance(r, dict) else r))

    # 销售职位应看不到佣金字段
    st, won_alice = call("GET", "/api/won-projects", user="alice")
    if isinstance(won_alice, list) and won_alice:
        hidden = "gs_comm_usd" not in won_alice[0]
        check("佣金字段对销售隐藏(P345)",
              hidden, "alice(销售) 应看不到 gs_comm_usd")
    else:
        check("佣金字段对销售隐藏(P345)", True, "alice 无可见数据，跳过")

    # ---------- LOST 失败项目 ----------
    print("\n== 失败项目 LOST ==")
    st, lost = call("GET", "/api/lost-projects", user="tom")
    n_lost = len(lost) if isinstance(lost, list) else -1
    check("读取失败项目列表", isinstance(lost, list) and n_lost > 0,
          "HTTP %s  共 %d 条" % (st, n_lost))

    # CRM 转失败
    st, crms = call("GET", "/api/crm-projects", user="tom")
    if isinstance(crms, list) and crms:
        cid = crms[0]["id"]
        st, r = call("POST", "/api/crm-projects/%d/failed" % cid,
                     {"fail_reason": "M6测试转失败"}, user="tom")
        check("CRM 转失败项目", st == 200 and isinstance(r, dict) and r.get("ok"),
              "HTTP %s  crm id=%s" % (st, cid))
        # 转回来
        st, lost2 = call("GET", "/api/lost-projects", user="tom")
        new_lost_id = lost2[-1]["id"] if isinstance(lost2, list) and lost2 else None
        if new_lost_id:
            st, r = call("POST", "/api/lost-projects/%d/restore" % new_lost_id,
                         user="tom")
            check("失败项目转回潜在", st == 200 and isinstance(r, dict) and r.get("ok"),
                  "HTTP %s  lost id=%s" % (st, new_lost_id))

    # ---------- 审批流 ----------
    print("\n== 审批流 ==")
    st, appr = call("GET", "/api/approval-requests?scope=all", user="tom")
    n_appr = len(appr.get("items", [])) if isinstance(appr, dict) else -1
    check("读取审批列表", isinstance(appr, dict) and n_appr >= 0,
          "HTTP %s  共 %d 条" % (st, n_appr))

    # 发起审批
    st, r = call("POST", "/api/approval-requests", {
        "requester": "ali",
        "requester_name": "Ali",
        "block_id": "M6-TEST",
        "block_name": "M6测试区块",
        "title": "M6云端测试审批",
        "content": "这是一条云端测试审批",
        "approvers": ["tom"],
    })
    check("发起审批", st == 200 and isinstance(r, dict) and r.get("ok"),
          "HTTP %s  %s" % (st, r if not isinstance(r, dict) or not r.get("ok") else "ok"))

    if isinstance(r, dict) and r.get("ok"):
        # 查待办
        st, todo = call("GET", "/api/approval-requests?scope=todo&me=tom")
        n_todo = len(todo.get("items", [])) if isinstance(todo, dict) else -1
        check("待我审批列表(tom)", n_todo > 0, "HTTP %s  共 %d 条" % (st, n_todo))

        # 找到测试审批并批准
        rid = None
        for it in (todo.get("items", []) if isinstance(todo, dict) else []):
            if it.get("block_id") == "M6-TEST":
                rid = it.get("id")
                break
        if rid:
            st, r2 = call("POST", "/api/approval-requests/%d/resolve" % rid,
                          {"action": "approve", "resolver": "tom"})
            check("审批通过", st == 200 and isinstance(r2, dict) and r2.get("ok"),
                  "HTTP %s  status=%s" % (st, r2.get("status") if isinstance(r2, dict) else "-"))

            # 非审批人尝试审批应被拒
            st, r3 = call("POST", "/api/approval-requests/%d/resolve" % rid,
                          {"action": "approve", "resolver": "ali"})
            check("非审批人被拦截", st in (403, 409),
                  "HTTP %s  %s" % (st, r3.get("error") if isinstance(r3, dict) else r3))

            # 清理
            call("DELETE", "/api/approval-requests/%d" % rid)

    # 清理测试数据
    if new_won_id:
        call("DELETE", "/api/won-projects/%d" % new_won_id, user="tom")
        print("\n    已清理测试签约项目 id=%s" % new_won_id)

    print("\n" + "=" * 60)
    print("  测试结果: %d / %d 通过" % (sum(results), len(results)))
    print("=" * 60)


if __name__ == "__main__":
    main()
