# -*- coding: utf-8 -*-
"""
培训测试模式开关（可逆）

需求：测试阶段让 cuong / james / tom 拥有和 admin 一样的权限，能看到所有页面。
     tom 本来就是管理员，所以实际只需处理 cuong 和 james。

原理：把账号加入 managers 表 -> is_manager=True -> 走管理员豁免，
      所有权限闸门放行、可见范围返回全部，效果和 admin 一样。

为什么只改数据不改代码：
     前端和 APP 都是读后端返回的 is_manager 来决定显示什么，
     所以改一处数据，网页版和 APP 同时生效，不用改代码、不用重新打包。

用法：
    python cloudflare/set_test_mode.py on     开启培训模式
    python cloudflare/set_test_mode.py off    恢复正常
    python cloudflare/set_test_mode.py status 查看当前状态
"""
import os
import sys
import json
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DB_NAME = "agi-pm-db"

# 培训期间要提升为管理员的账号
TEST_ADMINS = ["cuong", "james"]
# tom 本来就是管理员，这里只是确保它在名单里
KEEP_ADMINS = ["tom", "admin"]

API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")


def find_wrangler():
    """在 Windows 上 wrangler 是 wrangler.cmd，Python 直接调 'wrangler' 找不到，
    需要定位到实际的可执行文件。"""
    import shutil

    # 1. PATH 里能找到就用
    for name in ("wrangler.cmd", "wrangler"):
        p = shutil.which(name)
        if p:
            return p

    # 2. npm 全局目录（最常见的位置）
    npm_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "npm")
    for name in ("wrangler.cmd", "wrangler"):
        p = os.path.join(npm_dir, name)
        if os.path.isfile(p):
            return p

    return None


WRANGLER = find_wrangler()


def d1_execute(sql):
    """通过 wrangler 在 D1 上执行 SQL"""
    if not WRANGLER:
        return None, "找不到 wrangler，请确认已执行 npm install -g wrangler"

    cmd = [
        WRANGLER, "d1", "execute", DB_NAME,
        "--remote", "--command", sql, "--json"
    ]
    env = os.environ.copy()
    if API_TOKEN:
        env["CLOUDFLARE_API_TOKEN"] = API_TOKEN

    r = subprocess.run(
        cmd, cwd=HERE, env=env,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=180
    )
    if r.returncode != 0:
        return None, (r.stdout or "") + (r.stderr or "")
    return (r.stdout or ""), None


def query(sql):
    """查询并返回结果行

    wrangler d1 execute --json 的返回结构：
        [ { "results": [ {...}, {...} ], "success": true, "meta": {...} } ]
    所以要取 [0].results
    """
    out, err = d1_execute(sql)
    if err:
        print("    执行失败: %s" % err[:300])
        return None
    try:
        txt = out.strip()
        start = txt.find("[")
        if start < 0:
            return None
        # 找到匹配的结尾括号
        depth = 0
        end = -1
        for i in range(start, len(txt)):
            if txt[i] == "[":
                depth += 1
            elif txt[i] == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end < 0:
            return None
        data = json.loads(txt[start:end + 1])
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict) and "results" in first:
                return first["results"]
            return data
        return data
    except Exception as e:
        print("    解析失败: %s" % e)
    return None


def show_status():
    print("=" * 62)
    print("  当前管理员状态")
    print("=" * 62)
    rows = query("SELECT username FROM managers ORDER BY username")
    mgrs = [r["username"] for r in rows] if rows else []
    print("\n  管理员名单 (%d 人): %s" % (len(mgrs), ", ".join(mgrs) or "(空)"))

    sql = ("SELECT username, real_name, role, position FROM users "
           "WHERE lower(username) IN ('tom','admin','cuong','james') "
           "ORDER BY username")
    rows = query(sql)
    if rows:
        print("\n  %-10s %-12s %-10s %-12s %s" % ("账号", "姓名", "role", "职位", "是否管理员"))
        print("  " + "-" * 58)
        for r in rows:
            is_m = r["username"].lower() in [m.lower() for m in mgrs]
            print("  %-10s %-12s %-10s %-12s %s" % (
                r["username"], r.get("real_name") or "-",
                r.get("role") or "-", r.get("position") or "-",
                "是" if is_m else "否"))
    print()


def mode_on():
    print("=" * 62)
    print("  开启培训测试模式")
    print("=" * 62)

    # 1. 加入管理员名单
    print("\n[1] 把 cuong / james 加入管理员名单")
    for u in TEST_ADMINS:
        out, err = d1_execute(
            "INSERT OR IGNORE INTO managers (username) VALUES ('%s')" % u)
        if err:
            print("    %-8s 失败: %s" % (u, err[:150]))
        else:
            print("    %-8s 已加入" % u)

    # 确保 tom / admin 在名单里
    for u in KEEP_ADMINS:
        d1_execute("INSERT OR IGNORE INTO managers (username) VALUES ('%s')" % u)

    # 2. role 设为管理员（与 admin / tom 一致）
    print("\n[2] 设置 role = 管理员")
    names = ",".join("'%s'" % u for u in TEST_ADMINS)
    out, err = d1_execute(
        "UPDATE users SET role='管理员' WHERE lower(username) IN (%s)" % names)
    if err:
        print("    失败: %s" % err[:200])
    else:
        print("    cuong / james 的 role 已设为 管理员")

    print("\n[3] 验证")
    show_status()
    print("  完成：cuong / james 现在与 admin 权限一致，能看到所有页面。")
    print("  网页版刷新、APP 下拉刷新即可生效。")
    print("=" * 62)


def mode_off():
    print("=" * 62)
    print("  恢复正常（撤销培训模式）")
    print("=" * 62)

    print("\n[1] 从管理员名单移除 cuong / james")
    names = ",".join("'%s'" % u for u in TEST_ADMINS)
    out, err = d1_execute(
        "DELETE FROM managers WHERE lower(username) IN (%s)" % names)
    if err:
        print("    失败: %s" % err[:200])
    else:
        print("    已移除")

    print("\n[2] role 恢复为 user")
    out, err = d1_execute(
        "UPDATE users SET role='user' WHERE lower(username) IN (%s)" % names)
    if err:
        print("    失败: %s" % err[:200])
    else:
        print("    已恢复")

    print("\n[3] 验证")
    show_status()
    print("  已恢复正常。")
    print("=" * 62)


def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if arg == "on":
        mode_on()
    elif arg == "off":
        mode_off()
    elif arg in ("status", ""):
        show_status()
    else:
        print("用法: python cloudflare/set_test_mode.py [on|off|status]")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
