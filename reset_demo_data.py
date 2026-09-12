#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 AGI-PM 演示数据清理工具 —— 培训结束后、正式上线前使用
============================================================================

【什么时候用】
  培训结束、团队正式使用系统前，运行本工具清空所有演示数据。
  现在不要运行。

【会做什么】
  清空演示数据：
    · 业务表：crm_projects / lost_projects / won_projects / approval_requests
    · 示例用户（14 个假账号，如 khoa / gm1 / gm2 / obs1 ...）
    · 示例管理员（gm1 / gm2）
  永久保留：
    · 真实用户 8 人：tom / alice / admin / cuong / james / travis / ali / linh
    · 畜禽价格数据、各类缓存（长期积累，删了要重抓）

【前置条件】
  app.py 中 DEMO_SEED 必须为 False（生产模式）。
  若为 True，脚本会拒绝执行 —— 因为那样清空后重启服务示例数据会"复活"。

【用法】
  python reset_demo_data.py --dry-run        # 预览，不修改任何数据（建议先跑）
  python reset_demo_data.py                  # 真正清理（需输入 DELETE 确认）
  python reset_demo_data.py --all            # 连登录历史/密码重置请求一起清
  python reset_demo_data.py --with-uploads   # 连上传的附件一起删

【配套：培训后彻底移除 DEMO 按钮】
  python remove_demo.py
  （移除前端 DEMO 按钮 + 后端 /api/demo/* 接口 + 快照数据，不可恢复）
============================================================================
"""
import sys, os, sqlite3, shutil, time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import app

CLEAR_TABLES = ["crm_projects", "lost_projects", "won_projects", "approval_requests"]
CLEAR_EXTRA = ["login_history", "password_requests"]      # 仅 --all
REAL_USERS = getattr(app, "REAL_USERS", [])
DEMO_USERNAMES = getattr(app, "DEMO_USERNAMES", [])


def line(ch="=", n=74):
    print(ch * n)


def main():
    args = set(sys.argv[1:])
    dry = "--dry-run" in args
    do_all = "--all" in args
    with_uploads = "--with-uploads" in args

    line()
    print("AGI-PM 演示数据清理工具")
    line()
    print("  模式:      %s" % ("预览(不修改任何数据)" if dry else "★ 真正执行清理 ★"))
    print("  数据库:    %s" % app.DB_PATH)
    print("  DEMO_SEED: %s" % getattr(app, "DEMO_SEED", "(未定义)"))
    print("  真实用户:  %s" % ", ".join(REAL_USERS))
    print()

    # ---- 演示模式检查 ----
    if getattr(app, "DEMO_SEED", True) and not dry:
        print("  " + "!" * 70)
        print("  !! 警告：app.py 中 DEMO_SEED 仍为 True（演示模式）")
        print("  !! 清空后只要重启服务，示例数据就会自动复活。")
        print("  !! 请先把 app.py 里的  DEMO_SEED = True  改为  DEMO_SEED = False")
        print("  !! 再重新运行本脚本。")
        print("  " + "!" * 70)
        line()
        return 1

    conn = sqlite3.connect(app.DB_PATH)
    conn.row_factory = sqlite3.Row

    # ---- 现状统计 ----
    print("【当前数据量】")
    line("-")
    targets = list(CLEAR_TABLES) + (list(CLEAR_EXTRA) if do_all else [])
    stats = {}
    for t in targets:
        try:
            n = conn.execute("SELECT COUNT(*) n FROM %s WHERE is_demo=1" % t).fetchone()["n"]
            stats[t] = n
            print("  将清空  %-24s %6d 行 (演示数据 is_demo=1)" % (t, n))
        except Exception as e:
            print("  跳过    %-24s %s" % (t, e))

    # 示例用户
    demo_existing = []
    if DEMO_USERNAMES:
        for u in DEMO_USERNAMES:
            r = conn.execute(
                "SELECT COUNT(*) n FROM users WHERE lower(username)=lower(?)",
                (u,)).fetchone()["n"]
            if r:
                demo_existing.append(u)
    real_n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    print()
    print("  将删除示例用户: %d 个 (当前库中共 %d 个用户)" % (len(demo_existing), real_n))
    print("      " + ", ".join(demo_existing) if demo_existing else "      (无)")
    print("  永久保留真实用户: %s" % ", ".join(REAL_USERS))

    # ---- 畜禽数据（保留）----
    print()
    print("【保留不动】")
    line("-")
    lv = 0
    for t in ["livestock_history", "livestock_retail", "livestock_update_log"]:
        try:
            lv += conn.execute("SELECT COUNT(*) n FROM %s" % t).fetchone()["n"]
        except Exception:
            pass
    print("  保留    %-24s %6d 行 (畜禽价格数据)" % ("livestock_*", lv))
    print("  保留    %-24s 各价格缓存" % "feed/fx/metal_cache")

    # ---- 附件 ----
    up_files = []
    try:
        up_files = [f for f in os.listdir(app.UPLOAD_DIR)
                    if os.path.isfile(os.path.join(app.UPLOAD_DIR, f))]
    except Exception:
        pass
    print()
    print("  上传附件: %d 个 %s" % (
        len(up_files),
        "(本次会删除)" if with_uploads else "(保留，加 --with-uploads 可删)"))

    total = sum(stats.values()) + len(demo_existing)
    if total == 0 and not (with_uploads and up_files):
        print("\n  没有需要清理的数据，脚本结束。")
        line()
        conn.close()
        return 0

    if dry:
        print("\n【预览模式】以上是将会执行的操作，未修改任何数据。")
        print("  确认无误后运行： python reset_demo_data.py")
        line()
        conn.close()
        return 0

    # ---- 二次确认 ----
    line()
    print("  即将删除 %d 条业务数据 + %d 个示例用户" % (sum(stats.values()), len(demo_existing)))
    print("  真实用户 %s 永久保留。" % ", ".join(REAL_USERS))
    print("  此操作不可撤销（虽有备份，恢复需手动操作）")
    line()
    ans = input("  确认请输入 DELETE（区分大小写），其它任意输入取消: ").strip()
    if ans != "DELETE":
        print("\n  已取消，未修改任何数据。")
        line()
        conn.close()
        return 0

    # ---- 备份 ----
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = "%s.backup_%s.db" % (app.DB_PATH[:-3], ts)
    try:
        shutil.copy2(app.DB_PATH, bak)
        print("\n  已备份: %s" % os.path.basename(bak))
    except Exception as e:
        print("\n  !! 备份失败: %s" % e)
        if input("  仍要继续？输入 YES: ").strip() != "YES":
            print("  已取消。"); conn.close(); return 1

    # ---- 执行清理 ----
    print("\n【执行清理】")
    line("-")
    for t in targets:
        try:
            n = conn.execute("SELECT COUNT(*) n FROM %s WHERE is_demo=1" % t).fetchone()["n"]
            conn.execute("DELETE FROM %s WHERE is_demo=1" % t)
            try:
                conn.execute("DELETE FROM sqlite_sequence WHERE name=?", (t,))
            except Exception:
                pass
            print("  已清空  %-24s (删除 %d 行 演示数据)" % (t, n))
        except Exception as e:
            print("  失败    %-24s %s" % (t, e))

    nu = 0
    for u in DEMO_USERNAMES:
        try:
            nu += conn.execute(
                "DELETE FROM users WHERE lower(username)=lower(?)", (u,)).rowcount or 0
        except Exception:
            pass
    print("  已删除示例用户 %d 个" % nu)

    nm = 0
    for u in DEMO_USERNAMES:
        try:
            nm += conn.execute(
                "DELETE FROM managers WHERE lower(username)=lower(?)", (u,)).rowcount or 0
        except Exception:
            pass
    if nm:
        print("  已删除示例管理员 %d 个" % nm)

    conn.commit()

    if with_uploads and up_files:
        ok = 0
        for f in up_files:
            try:
                os.remove(os.path.join(app.UPLOAD_DIR, f)); ok += 1
            except Exception:
                pass
        print("  已删除附件 %d 个" % ok)

    # ---- 结果 ----
    print()
    print("【清理后状态】")
    line("-")
    for t in targets:
        try:
            print("  %-26s %6d 行" % (t, conn.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]))
        except Exception:
            pass
    print("  %-26s %6d 个 (应=%d)" % (
        "users", conn.execute("SELECT COUNT(*) FROM users").fetchone()[0], len(REAL_USERS)))
    conn.close()

    line()
    print("清理完成！")
    print()
    print("下一步：")
    print("  1. 重启服务：python app.py")
    print("  2. 检查：CRM/签约/失败/审批 应均为空，8 个真实用户仍在")
    print("  3. 培训已结束？运行 python remove_demo.py 彻底移除 DEMO 按钮")
    print("  4. 如需恢复：把 %s 改回 agi_pm.db" % os.path.basename(bak))
    line()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已中断，未修改任何数据。")
        sys.exit(0)
