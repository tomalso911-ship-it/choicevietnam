#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 培训结束后：彻底移除 DEMO 功能（按钮 + 接口 + 快照）
============================================================================

【什么时候用】
  只用一次 —— 培训结束、确认不再需要演示数据后。

【会做什么】
  1. 备份 index.html 与 app.py（.bak_remove_demo_时间戳）
  2. 从 index.html 移除：
       · DEMO 按钮 HTML（<button class="btn-demo" ...>DEMO</button>）
       · toggleDemoData() 函数整段
       · .btn-demo CSS 样式
  3. 从 app.py 移除：
       · /api/demo/load 与 /api/demo/clear 两个路由及其内部函数
       · clear_demo_data() / load_demo_data() 函数
  4. 删除演示数据快照 demo_snapshot.json

【不会做什么】
  · 不动数据库里的数据（如需清空数据请另跑 reset_demo_data.py）
  · 不动真实用户、权限配置、畜禽数据

【为什么用代码删而不是手删】
  DEMO 相关代码分散在 index.html（按钮+函数+CSS）与 app.py（接口+函数）
  多处，手工删容易漏，漏掉的接口会变成孤儿代码。脚本用锚点定位整段删除，
  删除前自动备份，可随时回滚。

【用法】
  python remove_demo.py --dry-run     # 预览将删除哪些片段（建议先跑）
  python remove_demo.py               # 真正移除（需输入 REMOVE 确认）

【回滚】
  把生成的 .bak_remove_demo_* 文件改回原名即可。
============================================================================
"""
import sys, os, re, shutil, time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, "index.html")
APP = os.path.join(BASE, "app.py")
SNAP = os.path.join(BASE, "demo_snapshot.json")


def line(ch="=", n=74):
    print(ch * n)


def read(p):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def cut_block(text, start_marker, end_marker, label):
    """按起止锚点删除中间整块（含锚点行）。返回 (新文本, 删除行数)"""
    si = text.find(start_marker)
    if si < 0:
        return None, 0, "未找到起始锚点: %r" % start_marker[:40]
    ei = text.find(end_marker, si)
    if ei < 0:
        return None, 0, "未找到结束锚点: %r" % end_marker[:40]
    ei += len(end_marker)
    # 向后再吃掉一个空行，保持格式整洁
    if ei < len(text) and text[ei] == "\n":
        ei += 1
    removed = text[si:ei].count("\n")
    return text[:si] + text[ei:], removed, None


def cut_function(text, header, label):
    """从 header 起，按大括号配对删除整个函数（含前置注释块）。

    比 cut_block 的字符串锚点健壮：代码被格式化器换行/重排后，
    字符串锚点会失效导致函数残留（孤儿代码），而大括号配对不受影响。
    """
    si = text.find(header)
    if si < 0:
        return None, 0, "未找到起始标记: %r" % header[:40]

    # 跳过注释块，找到函数体的起始 {
    i = si
    in_block = False
    bi = -1
    while i < len(text) - 1:
        c = text[i]
        n = text[i + 1]
        if in_block:
            if c == "*" and n == "/":
                in_block = False
                i += 2
                continue
            i += 1
            continue
        if c == "/" and n == "*":
            in_block = True
            i += 2
            continue
        if c == "{":
            bi = i
            break
        i += 1
    if bi < 0:
        return None, 0, "未找到函数体的起始 {"

    # 大括号配对（跳过字符串与注释，避免把 '{' 字面量算进来）
    depth = 0
    i = bi
    in_str = None
    in_line = False
    in_blk = False
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if in_line:
            if c == "\n":
                in_line = False
            i += 1
            continue
        if in_blk:
            if c == "*" and n == "/":
                in_blk = False
                i += 2
                continue
            i += 1
            continue
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c == "/" and n == "/":
            in_line = True
            i += 2
            continue
        if c == "/" and n == "*":
            in_blk = True
            i += 2
            continue
        if c in "\"'`":
            in_str = c
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                ei = i + 1
                # 吃掉行尾空白与随后的一个空行
                while ei < len(text) and text[ei] in " \t\r":
                    ei += 1
                if ei < len(text) and text[ei] == "\n":
                    ei += 1
                removed = text[si:ei].count("\n")
                return text[:si] + text[ei:], removed, None
        i += 1
    return None, 0, "大括号未配对（函数可能不完整）"


def main():
    dry = "--dry-run" in sys.argv

    line()
    print("移除 DEMO 功能（培训后一次性操作）")
    line()
    print("  模式: %s" % ("预览（不修改任何文件）" if dry else "★ 真正移除 ★"))
    print()

    html = read(HTML)
    appy = read(APP)

    plan = []

    # ---------- index.html ----------
    # 1) DEMO 按钮（含其上注释行一起删）
    m = re.search(
        r"[ \t]*<!-- DEMO 按钮.*?-->\s*\n[ \t]*<button class=\"btn-demo\".*?</button>\s*\n",
        html, re.S)
    if m:
        plan.append(("index.html", "DEMO 按钮 HTML", m.group(0), len(m.group(0).split("\n")) - 1))
    else:
        # 退而求其次：只删 button 行
        m2 = re.search(r"[ \t]*<button class=\"btn-demo\".*?</button>\s*\n", html, re.S)
        if m2:
            plan.append(("index.html", "DEMO 按钮 HTML", m2.group(0),
                         len(m2.group(0).split("\n")) - 1))
        else:
            print("  [跳过] index.html 未找到 DEMO 按钮（可能已删除）")

    # 2) toggleDemoData 函数整段（连同其前置注释块）
    #    用大括号配对定位，避免代码格式化后字符串锚点失效导致函数残留
    DEMO_FN_MARK = "/* ===================== DEMO 演示数据开关 ====================="
    new_html, n, err = cut_function(html, DEMO_FN_MARK, "toggleDemoData")
    if err:
        print("  [跳过] index.html toggleDemoData: %s" % err)
    else:
        si = html.find(DEMO_FN_MARK)
        ei = html.find(DEMO_FN_MARK) + len(html[si:]) - len(new_html[si:])
        plan.append(("index.html", "toggleDemoData() 函数",
                     html[si:si + (len(html) - len(new_html))], n))

    # 3) .btn-demo CSS
    #    两条要求缺一不可：
    #    a) 规则会跨行（续行缩进更深），正则必须吃掉续行，否则只删一半；
    #    b) 续行必须"非贪婪地吃到本条规则的 }"为止 —— 若贪婪吃所有缩进行，
    #       会把后面无关的 CSS 规则全部吞掉（曾误删 255 行）。
    CSS_RULE = r"[ \t]*\.btn-demo[^\n]*\n(?:[ \t]+[^\n]*\n)*?[^\n]*\}\s*\n"
    m3 = re.search(
        r"[ \t]*/\* DEMO 按钮：黑底白字.*?\*/\s*\n(?:" + CSS_RULE + ")+",
        html, re.S)
    if m3:
        plan.append(("index.html", ".btn-demo CSS", m3.group(0),
                     len(m3.group(0).split("\n")) - 1))
    else:
        m3b = re.search(r"(?:" + CSS_RULE + ")+", html)
        if m3b:
            plan.append(("index.html", ".btn-demo CSS", m3b.group(0),
                         len(m3b.group(0).split("\n")) - 1))
        else:
            print("  [跳过] index.html 未找到 .btn-demo CSS")

    # ---------- app.py ----------
    new_appy, n4, err4 = cut_block(
        appy,
        "# ============================================================================\n"
        "# DEMO 演示数据机制（一键还原 / 一键清空）",
        '        return jsonify({"ok": False, "error": str(e)}), 500\n'
        '\n\n@app.route("/api/demo/clear"',
        "demo functions")
    # 上面切法不稳，改用更明确的范围：从 DEMO 机制注释 到 clear 路由结束
    new_appy, n4, err4 = cut_block(
        appy,
        "# DEMO 演示数据机制（一键还原 / 一键清空）",
        '@app.route("/api/demo/clear"',
        "demo")
    if err4:
        print("  [跳过] app.py: %s" % err4)
    else:
        # 需要继续切到 clear 路由函数体结束（下一段非空行开始）
        # 找 clear 路由后的 return 语句结束
        idx = new_appy.find('@app.route("/api/demo/clear"')
        # 此时 new_appy 已删掉 load 部分，clear 路由还在（因为我们切到它之前）
        # 重新完整处理：直接从原始 appy 切到 clear 路由函数体结束
        start = appy.find("# ============================================================================\n# DEMO 演示数据机制")
        end_marker = 'return jsonify({"ok": False, "error": str(e)}), 500'
        # 找最后一个该 marker（clear 路由的）
        last = appy.rfind(end_marker)
        # 确保 last 在 start 之后，且是 clear 路由内的
        if start >= 0 and last > start:
            # 从 start 到 last+len(marker)，再加一个空行
            end = last + len(end_marker)
            while end < len(appy) and appy[end] == "\n":
                end += 1
            seg = appy[start:end]
            plan.append(("app.py", "DEMO 机制（函数+两个接口）", seg,
                         seg.count("\n")))
        else:
            print("  [跳过] app.py 未能定位 DEMO 代码块")

    # ---------- 展示计划 ----------
    print("【将删除的内容】")
    line("-")
    for f, label, seg, n in plan:
        print("  %-12s %-32s %4d 行" % (f, label, n))
    if os.path.exists(SNAP):
        print("  %-12s %-32s %.1f KB" % (
            "demo_snapshot.json", "演示数据快照", os.path.getsize(SNAP) / 1024.0))
    print()

    if dry:
        print("【预览模式】未修改任何文件。")
        print("  确认后运行： python remove_demo.py")
        line()
        return 0

    if not plan:
        print("  没有找到需要移除的 DEMO 代码（可能已移除）。")
        line()
        return 0

    # ---------- 确认 ----------
    line()
    print("  即将从 index.html / app.py 中永久删除上述内容。")
    print("  删除前会自动备份（.bak_remove_demo_时间戳），可回滚。")
    print("  注意：本脚本【不会】清数据库，如需清空数据请另跑 reset_demo_data.py")
    line()
    ans = input("  确认请输入 REMOVE（区分大小写），其它取消: ").strip()
    if ans != "REMOVE":
        print("\n  已取消，未修改任何文件。")
        line()
        return 0

    # ---------- 备份 ----------
    ts = time.strftime("%Y%m%d_%H%M%S")
    for p in (HTML, APP):
        shutil.copy2(p, "%s.bak_remove_demo_%s" % (p, ts))
    print("\n  已备份:")
    print("     index.html.bak_remove_demo_%s" % ts)
    print("     app.py.bak_remove_demo_%s" % ts)

    # ---------- 执行删除 ----------
    print("\n【执行移除】")
    line("-")
    cur_html = read(HTML)
    for f, label, seg, n in plan:
        if f == "index.html":
            if seg in cur_html:
                cur_html = cur_html.replace(seg, "", 1)
                print("  已移除  %-32s (%d 行)" % (label, n))
            else:
                print("  [跳过]  %-32s 片段已不在文件中" % label)
    with open(HTML, "w", encoding="utf-8", newline="") as fp:
        fp.write(cur_html)

    cur_appy = read(APP)
    for f, label, seg, n in plan:
        if f == "app.py":
            if seg in cur_appy:
                cur_appy = cur_appy.replace(seg, "", 1)
                print("  已移除  %-32s (%d 行)" % (label, n))
            else:
                print("  [跳过]  %-32s 片段已不在文件中" % label)
    with open(APP, "w", encoding="utf-8", newline="") as fp:
        fp.write(cur_appy)

    if os.path.exists(SNAP):
        os.remove(SNAP)
        print("  已删除  %-32s" % "demo_snapshot.json")

    # ---------- 校验 ----------
    print("\n【校验】")
    line("-")
    h2, a2 = read(HTML), read(APP)
    left = []
    for k in ["btn-demo", "toggleDemoData", "/api/demo/load", "/api/demo/clear"]:
        c = h2.count(k) + a2.count(k)
        if c:
            left.append((k, c))
    if left:
        print("  [警告] 仍有残留（可能在注释中）:")
        for k, c in left:
            print("      %-24s %d 处" % (k, c))
    else:
        print("  [PASS] DEMO 相关代码已全部移除")

    line()
    print("完成！请重启服务：python app.py")
    print("回滚：把 .bak_remove_demo_%s 备份改回原名" % ts)
    line()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已中断，未修改任何文件。")
        sys.exit(0)
