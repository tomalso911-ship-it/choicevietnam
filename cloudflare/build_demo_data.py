# -*- coding: utf-8 -*-
"""
构建完整演示数据包（M10）

目标：培训时一次点击 DEMO 就出来【用户 + 业务数据】，能完整演示：
  - 用户与授权（22 个账号，覆盖 8 种职位）
  - 数据范围分配（可见/授权给我/我授权给/离职代理）
  - 权限配置（每个职位的决策项）
  - CRM / WON / LOST 全流程
  - 审批流

内容：
  1. 14 个演示账号（从本地库还原，含完整权限配置）
  2. 现有业务数据（32 CRM + 26 WON + 18 LOST + 27 审批）
  3. 新增业务数据（分配给演示账号，让"数据范围过滤"能看出效果）

产物：
  cloudflare/demo_snapshot.json  -> 上传到 R2

用法：
    python cloudflare/build_demo_data.py
"""
import os
import sys
import json
import random
import shutil
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SNAP = os.path.join(ROOT, "demo_snapshot.json")
SRC_USERS = os.path.join(HERE, "_demo_users_source.json")
BACKUP = os.path.join(HERE, "demo_snapshot.backup_%s.json"
                      % datetime.now().strftime("%Y%m%d-%H%M%S"))

# 演示账号名单（DEMO 清空时会按这个名单精确删除）
DEMO_USERNAMES = [
    "minh", "salesdir1", "salesdir2", "gm1", "gm2", "dgm1", "dgm2",
    "obs1", "obs2", "fin1", "fin2", "asst1", "hr1", "khoa",
]

DEFAULT_PASSWORD = "66668888"

# 销售人员（用于分配新增业务数据）
SALES = ["tom", "ali", "james", "cuong", "travis", "khoa", "minh"]

# 客户方项目经理（越南人名，作为 manager 字段）
CUSTOMER_MANAGERS = [
    "Ngo Thanh Trung", "Tran Thi Binh", "Nguyen Van An", "Do Cong Thanh",
    "Le Van Cuong", "Le Quang Huy", "Hoang Van Long", "Vu Thi Mai",
    "Bui Tuan Kiet", "Pham Thi Dung", "Nguyen Thi Phuong", "Do Thi Huong",
    "Dang Xuan Phuc", "Vo Van Tam", "Ly Thi Hoa", "Phan Ngoc Son",
]

# 越南省份
PROVINCES = [
    "Dong Nai", "Binh Duong", "Ho Chi Minh", "Binh Phuoc", "Tay Ninh",
    "Long An", "Ba Ria - Vung Tau", "Can Tho", "Hai Phong", "Bac Ninh",
]


def rnd_amount(low, high):
    return random.randint(low, high) // 1000 * 1000


def rnd_date(start_days_ago=400, end_days_ago=30):
    d = datetime.now() - timedelta(days=random.randint(end_days_ago, start_days_ago))
    return d.strftime("%Y-%m-%d")


def make_crm_rows(base_id, n, start_no):
    """按 crm_projects 结构造数据"""
    rows = []
    for i in range(n):
        sp = SALES[i % len(SALES)]
        q = rnd_amount(80000, 900000)
        rmb = q
        usd = int(q / 7.1)
        vnd = int(q * 3500)
        rows.append({
            "quote_no": "QT-2026-%03d" % (start_no + i),
            "project_name": "%s Factory Phase %d" % (
                random.choice(["Binh Duong", "Dong Nai", "Long An", "Can Tho"]), i + 1),
            "province": random.choice(PROVINCES),
            "customer": "%s Co., Ltd." % random.choice([
                "Tan Phat", "Minh Long", "Hoang Gia", "Viet Thang", "Sai Gon"]),
            "bu": random.choice(["BU-1", "BU-2", "BU-3"]),
            "construction": random.choice(["新建厂房", "改造升级", "扩建"]),
            "startup_pct": random.randint(20, 90),
            "sign_pct": random.randint(10, 70),
            "manager": random.choice(CUSTOMER_MANAGERS),
            "manager_phone": "09%d" % random.randint(10000000, 99999999),
            "company_info": "越南本地制造企业",
            "initial_quote_date": rnd_date(),
            "est_purchase_date": rnd_date(-30, -300),
            "est_ship_date": rnd_date(-60, -400),
            "quote_version": "V%d" % random.randint(1, 3),
            "last_quote_date": rnd_date(),
            "rate_rmb_vnd": random.randint(3400, 3600),
            "rate_usd_vnd": random.randint(24000, 25600),
            "incoterm": random.choice(["FOB", "CIF", "EXW"]),
            "install_quoted": random.choice(["是", "否"]),
            "salesperson": sp,
            "remark": "培训演示数据",
            "pdf_equip": "", "pdf_install": "", "pdf_both": "",
            "q1_rmb": rmb, "q1_usd": usd, "q1_vnd": vnd,
            "q2_rmb": int(rmb * 0.9), "q2_usd": int(usd * 0.9), "q2_vnd": int(vnd * 0.9),
            "q3_rmb": 0, "q3_usd": 0, "q3_vnd": 0,
            "q4_rmb": 0, "q4_usd": 0, "q4_vnd": 0,
            "q5_rmb": 0, "q5_usd": 0, "q5_vnd": 0,
            "q6_rmb": 0, "q6_usd": 0, "q6_vnd": 0,
            "q7_rmb": 0, "q7_usd": 0, "q7_vnd": 0,
            "status": "active",
            "owner_user_id": sp.lower(),
        })
    return rows


def make_lost_rows(n, start_no):
    rows = []
    reasons = ["价格过高", "客户选择竞争对手", "项目取消", "预算不足", "技术规格不符"]
    for i in range(n):
        sp = SALES[i % len(SALES)]
        q = rnd_amount(80000, 900000)
        rows.append({
            "quote_no": "QT-2025-L%03d" % (start_no + i),
            "project_name": "%s Workshop %d" % (
                random.choice(["Tay Ninh", "Binh Phuoc", "Hai Phong"]), i + 1),
            "province": random.choice(PROVINCES),
            "customer": "%s JSC" % random.choice([
                "An Phat", "Thanh Cong", "Vinh Phu", "Dai Nam"]),
            "bu": random.choice(["BU-1", "BU-2"]),
            "construction": random.choice(["新建厂房", "改造升级"]),
            "startup_pct": 0, "sign_pct": 0,
            "manager": random.choice(CUSTOMER_MANAGERS),
            "manager_phone": "09%d" % random.randint(10000000, 99999999),
            "company_info": "越南本地制造企业",
            "initial_quote_date": rnd_date(),
            "est_purchase_date": "", "est_ship_date": "",
            "quote_version": "V1", "last_quote_date": rnd_date(),
            "rate_rmb_vnd": random.randint(3400, 3600),
            "rate_usd_vnd": random.randint(24000, 25600),
            "incoterm": random.choice(["FOB", "CIF"]),
            "install_quoted": random.choice(["是", "否"]),
            "salesperson": sp,
            "remark": "培训演示数据",
            "pdf_equip": "", "pdf_install": "", "pdf_both": "",
            "q1_rmb": q, "q1_usd": int(q / 7.1), "q1_vnd": int(q * 3500),
            "q2_rmb": 0, "q2_usd": 0, "q2_vnd": 0,
            "q3_rmb": 0, "q3_usd": 0, "q3_vnd": 0,
            "q4_rmb": 0, "q4_usd": 0, "q4_vnd": 0,
            "q5_rmb": 0, "q5_usd": 0, "q5_vnd": 0,
            "q6_rmb": 0, "q6_usd": 0, "q6_vnd": 0,
            "q7_rmb": 0, "q7_usd": 0, "q7_vnd": 0,
            "fail_reason": random.choice(reasons),
            "fail_date": rnd_date(200, 10),
            # 注意：lost_projects 表没有 status 列，不要加
            "owner_user_id": sp.lower(),
        })
    return rows


def main():
    print("=" * 68)
    print("  构建完整演示数据包")
    print("=" * 68)

    if not os.path.isfile(SNAP):
        print("  找不到 %s" % SNAP)
        return 1

    # 备份原快照
    shutil.copy2(SNAP, BACKUP)
    print("\n[0] 已备份原快照")
    print("    %s" % os.path.basename(BACKUP))

    with open(SNAP, "r", encoding="utf-8") as f:
        snap = json.load(f)

    tables = snap.setdefault("tables", {})

    # ---------- 1. 加入演示账号 ----------
    print("\n[1] 加入演示账号")
    if not os.path.isfile(SRC_USERS):
        print("    缺少 %s" % SRC_USERS)
        print("    请先运行 _get_demo_users.py")
        return 1

    with open(SRC_USERS, "r", encoding="utf-8") as f:
        demo_users = json.load(f)

    # 密码统一设为初始密码 66668888（培训时好用）
    for u in demo_users:
        u["password"] = DEFAULT_PASSWORD
        u.pop("id", None)   # 让 D1 自增分配

    existing_users = tables.get("users") or []
    existing_names = {str(u.get("username", "")).lower() for u in existing_users}

    added = 0
    for u in demo_users:
        name = str(u.get("username", "")).lower()
        if name in existing_names:
            continue
        existing_users.append(u)
        existing_names.add(name)
        added += 1
        print("    + %-12s %-14s %s" % (
            u.get("username"), u.get("real_name"), u.get("position")))

    tables["users"] = existing_users
    print("    新增 %d 个演示账号，用户表合计 %d 个" % (added, len(existing_users)))

    # 记录演示账号名单，供 DEMO 清空时精确删除
    snap["_demo_usernames"] = DEMO_USERNAMES

    # ---------- 2. 新增业务数据 ----------
    print("\n[2] 新增业务数据（分配给各销售，便于演示数据范围）")

    before = {k: len(tables.get(k) or []) for k in
              ["crm_projects", "won_projects", "lost_projects"]}
    print("    原有: CRM=%d WON=%d LOST=%d"
          % (before["crm_projects"], before["won_projects"], before["lost_projects"]))

    random.seed(20260830)   # 固定种子，保证每次生成一致

    # CRM +40
    crm = tables.get("crm_projects") or []
    new_crm = make_crm_rows(0, 40, start_no=200)
    crm.extend(new_crm)
    tables["crm_projects"] = crm

    # LOST +20
    lost = tables.get("lost_projects") or []
    new_lost = make_lost_rows(20, start_no=100)
    lost.extend(new_lost)
    tables["lost_projects"] = lost

    after = {k: len(tables.get(k) or []) for k in
             ["crm_projects", "won_projects", "lost_projects"]}
    print("    新增后: CRM=%d WON=%d LOST=%d"
          % (after["crm_projects"], after["won_projects"], after["lost_projects"]))

    # ---------- 3. 保存 ----------
    snap["_meta"] = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "note": "完整演示数据包：含演示账号 + 业务数据，用于培训",
        "demo_usernames": DEMO_USERNAMES,
        "counts": after,
    }

    with open(SNAP, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False)

    size = os.path.getsize(SNAP)
    print("\n[3] 保存")
    print("    %s" % SNAP)
    print("    %.1f KB" % (size / 1024))

    print("\n" + "=" * 68)
    print("  完成。下一步：上传到 R2")
    print("    wrangler r2 object put agi-pm-files/demo_snapshot.json \\")
    print("        --file=demo_snapshot.json --remote")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
