# -*- coding: utf-8 -*-
"""
AGI-PM 系统垃圾清理工具
========================

用途：清掉删除记录后残留的垃圾，让系统不再"沉重"。

设计原则：
  · 默认只出报告，绝不自动删任何东西（--report，可省略）
  · 每个清理项都要显式指定开关
  · 涉及删除的操作都会先列清单，并二次确认（--yes 可跳过）
  · 畜禽历史表（livestock_history / livestock_update_log / livestock_farmgate /
    livestock_retail）按既定规则**永久保留**，本工具不碰

用法：
  python cleanup_junk.py                        # 只看报告（推荐先跑这个）
  python cleanup_junk.py --demo-commission      # 清佣金演示数据
  python cleanup_junk.py --caches               # 清各类价格缓存
  python cleanup_junk.py --orphan-files         # 清磁盘孤儿文件
  python cleanup_junk.py --stale-requests       # 清残留的佣金金额修改审批单
  python cleanup_junk.py --all                  # 以上全部
  python cleanup_junk.py --all --yes            # 全部清理，不再逐个确认
"""

import argparse
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = "agi_pm.db"
UPLOAD_DIR = "agi-pm-files"

# 畜禽历史数据表：按既定规则永久保留，任何清理项都不碰
PROTECTED_TABLES = (
    "livestock_history",
    "livestock_update_log",
    "livestock_farmgate",
    "livestock_retail",
)

# 纯缓存表：删掉会自动重新拉取，不影响业务
CACHE_TABLES = (
    "feed_cache",        # RSS 饲料价格缓存
    "fx_cache",          # 汇率缓存
    "metal_cache",       # 金属价格缓存
)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def count_of(cur, table):
    try:
        cur.execute("SELECT COUNT(*) FROM `%s`" % table)
        return cur.fetchone()[0]
    except Exception:
        return None


def report(cur):
    print("=" * 62)
    print(" AGI-PM 系统残留报告")
    print("=" * 62)

    print("\n[1] 佣金数据")
    try:
        cur.execute("SELECT is_demo, COUNT(*) n FROM commission_records GROUP BY is_demo")
        rows = cur.fetchall()
        if not rows:
            print("    (空)")
        for r in rows:
            tag = "演示数据(可安全清除)" if r["is_demo"] == 1 else "真实数据(保留)"
            print("    is_demo=%s : %s 条   %s" % (r["is_demo"], r["n"], tag))
        cur.execute("SELECT COUNT(*) FROM commission_beneficiaries")
        print("    受益人明细: %s 条" % cur.fetchone()[0])
        # 演示合同号
        cur.execute("SELECT contract FROM commission_records WHERE is_demo=1 LIMIT 6")
        demo = [r[0] for r in cur.fetchall()]
        if demo:
            print("    演示合同号样例: %s" % ", ".join(demo))
    except Exception as e:
        print("    查询失败:", e)

    print("\n[2] 缓存表（删掉会自动重建，不影响业务）")
    total = 0
    for t in CACHE_TABLES:
        n = count_of(cur, t)
        if n is None:
            print("    %-24s (表不存在)" % t)
        else:
            total += n
            print("    %-24s %6d 行" % (t, n))
    print("    %-24s %6d 行" % ("小计", total))

    print("\n[3] 残留审批单")
    for t, note in (("comm_amt_requests", "佣金金额修改审批单"),
                    ("approval_requests", "业务审批单"),
                    ("password_requests", "密码重置申请")):
        n = count_of(cur, t)
        if n is None:
            print("    %-24s (表不存在)" % t)
        else:
            print("    %-24s %6d 行   %s" % (t, n, note))

    print("\n[4] 登录记录")
    n = count_of(cur, "login_history")
    print("    login_history          %6d 行   (可按需清理旧记录)" % (n or 0))

    print("\n[5] 畜禽历史表（按规则永久保留，本工具不动）")
    for t in PROTECTED_TABLES:
        n = count_of(cur, t)
        if n is not None:
            print("    %-24s %6d 行   ← 保留" % (t, n))

    print("\n[6] 磁盘孤儿文件")
    refs, orphans, vault_n = scan_disk(cur)
    print("    受管文件总数: %d（其中私密空间 %d）" % (len(refs) + len(orphans) + vault_n, vault_n))
    print("    数据库引用  : %d" % len(refs))
    print("    孤儿文件    : %d" % len(orphans))
    for o in orphans[:20]:
        print("       " + o)


def scan_disk(cur):
    """扫描磁盘，返回 (被引用集合, 孤儿列表, vault 文件数)"""
    import json

    def norm(v):
        s = str(v or "").strip()
        if not s:
            return ""
        if "uploads/" in s:
            s = s.split("uploads/")[-1]
        return os.path.basename(s.strip())

    refs = set()
    for t in ("crm_projects", "lost_projects"):
        try:
            cur.execute("SELECT pdf_equip, pdf_install, pdf_both FROM `%s`" % t)
            for r in cur.fetchall():
                for f in ("pdf_equip", "pdf_install", "pdf_both"):
                    n = norm(r[f])
                    if n:
                        refs.add(n)
        except Exception:
            pass
    try:
        cur.execute("SELECT attachments FROM won_projects")
        for r in cur.fetchall():
            try:
                for a in json.loads(r[0] or "[]"):
                    n = norm((a or {}).get("filename") or (a or {}).get("url"))
                    if n:
                        refs.add(n)
            except Exception:
                pass
    except Exception:
        pass

    orphans, vault_n = [], 0
    if os.path.isdir(UPLOAD_DIR):
        for root, _d, names in os.walk(UPLOAD_DIR):
            for n in names:
                rel = os.path.relpath(os.path.join(root, n), UPLOAD_DIR).replace("\\", "/")
                if rel.startswith("vault/"):
                    vault_n += 1
                elif rel not in refs:
                    orphans.append(rel)
    return refs, orphans, vault_n


def confirm(prompt, auto):
    if auto:
        return True
    try:
        ans = input("%s [y/N]: " % prompt).strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


def clear_demo_commission(cur, conn, auto):
    print("\n>>> 清理佣金演示数据")
    try:
        cur.execute("SELECT COUNT(*) FROM commission_records WHERE is_demo=1")
        n = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM commission_beneficiaries WHERE record_id IN "
            "(SELECT id FROM commission_records WHERE is_demo=1)"
        )
        nb = cur.fetchone()[0]
    except Exception as e:
        print("    跳过（表不存在或查询失败）:", e)
        return
    if not n:
        print("    没有演示数据，跳过")
        return
    print("    将删除佣金记录 %d 条、受益人明细 %d 条" % (n, nb))
    if not confirm("    确认删除？", auto):
        print("    已取消")
        return
    cur.execute(
        "DELETE FROM commission_beneficiaries WHERE record_id IN "
        "(SELECT id FROM commission_records WHERE is_demo=1)"
    )
    cur.execute("DELETE FROM commission_records WHERE is_demo=1")
    conn.commit()
    print("    已删除")


def clear_caches(cur, conn, auto):
    print("\n>>> 清理缓存表")
    todo = [(t, count_of(cur, t)) for t in CACHE_TABLES]
    todo = [(t, n) for t, n in todo if n]
    if not todo:
        print("    缓存都是空的，跳过")
        return
    for t, n in todo:
        print("    %-24s %6d 行" % (t, n))
    if not confirm("    确认清空以上缓存？（会自动重新拉取）", auto):
        print("    已取消")
        return
    for t, _n in todo:
        try:
            cur.execute("DELETE FROM `%s`" % t)
        except Exception as e:
            print("    %s 清理失败: %s" % (t, e))
    conn.commit()
    print("    已清空")


def clear_orphan_files(cur, auto):
    print("\n>>> 清理磁盘孤儿文件")
    _refs, orphans, _v = scan_disk(cur)
    if not orphans:
        print("    没有孤儿文件，跳过")
        return
    for o in orphans[:30]:
        print("    " + o)
    if len(orphans) > 30:
        print("    ...还有 %d 个" % (len(orphans) - 30))
    if not confirm("    确认删除以上 %d 个孤儿文件？" % len(orphans), auto):
        print("    已取消")
        return
    done = 0
    for o in orphans:
        try:
            os.remove(os.path.join(UPLOAD_DIR, o.replace("/", os.sep)))
            done += 1
        except OSError:
            pass
    print("    已删除 %d 个" % done)


def clear_stale_requests(cur, conn, auto):
    print("\n>>> 清理残留审批单")
    n = count_of(cur, "comm_amt_requests")
    if not n:
        print("    comm_amt_requests 为空，跳过")
        return
    print("    comm_amt_requests: %d 行（佣金金额修改审批单，合同号多为空）" % n)
    if not confirm("    确认清空？", auto):
        print("    已取消")
        return
    try:
        cur.execute("DELETE FROM comm_amt_requests")
        conn.commit()
        print("    已清空")
    except Exception as e:
        print("    失败:", e)


def main():
    ap = argparse.ArgumentParser(description="AGI-PM 系统垃圾清理工具")
    ap.add_argument("--demo-commission", action="store_true", help="清佣金演示数据")
    ap.add_argument("--caches", action="store_true", help="清价格/汇率缓存表")
    ap.add_argument("--orphan-files", action="store_true", help="清磁盘孤儿文件")
    ap.add_argument("--stale-requests", action="store_true", help="清残留审批单")
    ap.add_argument("--all", action="store_true", help="执行以上全部清理")
    ap.add_argument("--yes", action="store_true", help="跳过逐个确认")
    args = ap.parse_args()

    if not os.path.isfile(DB_PATH):
        print("找不到数据库:", DB_PATH)
        return 1

    conn = connect()
    cur = conn.cursor()

    do_all = args.all
    action = any([args.demo_commission, args.caches, args.orphan_files,
                  args.stale_requests, do_all])

    report(cur)

    if not action:
        print("\n" + "=" * 62)
        print(" 以上是只读报告。加参数才会真正清理，例如：")
        print("   python cleanup_junk.py --all         # 清理全部")
        print("   python cleanup_junk.py --caches      # 只清缓存")
        conn.close()
        return 0

    if do_all or args.demo_commission:
        clear_demo_commission(cur, conn, args.yes)
    if do_all or args.caches:
        clear_caches(cur, conn, args.yes)
    if do_all or args.orphan_files:
        clear_orphan_files(cur, args.yes)
    if do_all or args.stale_requests:
        clear_stale_requests(cur, conn, args.yes)

    print("\n" + "=" * 62)
    print(" 清理完成，当前残留情况：")
    report(cur)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
