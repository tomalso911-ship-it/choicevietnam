# -*- coding: utf-8 -*-
"""
一键回归测试：依次运行所有已上云模块的测试脚本

流程：
  1. 检查云端数据
  2. 若为空库，先加载 DEMO 演示数据（多数测试依赖有数据）
  3. 依次运行各阶段测试
  4. 恢复初始状态（原本是空库就恢复为空库）

用法：python cloudflare/run_all_tests.py
      python cloudflare/run_all_tests.py --keep-data   (测完保留数据，不恢复)
"""
import os
import sys
import json
import time
import subprocess
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

TESTS = [
    ("M3 登录认证", "test_login.py"),
    ("M4 网页端到端", "test_pages.py"),
    ("M5 CRM 潜在项目", "test_crm.py"),
    ("M6 签约+失败+审批", "test_m6.py"),
    ("M7 用户+附件+DEMO", "test_m7.py"),
    ("M9 价格模块(R2)", "test_m9.py"),
]


def api_get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def api_post(path):
    req = urllib.request.Request(
        API + path, data=b"{}",
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def count_crm():
    try:
        d = api_get("/api/crm-projects?scope=all")
        return len(d) if isinstance(d, list) else -1
    except Exception:
        return -1


def main():
    keep = "--keep-data" in sys.argv

    print("=" * 62)
    print("  AGI-PM 云端回归测试")
    print("=" * 62)

    # ---- 准备：空库则加载 DEMO ----
    was_empty = False
    print("\n[准备] 检查云端数据状态 ...")
    n = count_crm()
    print("       当前潜在项目: %d 条" % n)
    if n == 0:
        was_empty = True
        print("       空库 -> 加载 DEMO 演示数据（多数测试依赖有数据）")
        try:
            r = api_post("/api/demo/load")
            if r.get("ok"):
                print("       已加载: %s" % json.dumps(r.get("restored", {}), ensure_ascii=False))
            else:
                print("       加载失败: %s" % r)
        except Exception as e:
            print("       加载异常: %s" % e)
    else:
        print("       已有数据，直接测试")

    summary = []
    for name, script in TESTS:
        path = os.path.join(HERE, script)
        if not os.path.isfile(path):
            print("\n[%s] 脚本缺失，跳过" % name)
            summary.append((name, "SKIP"))
            continue

        print("\n" + "-" * 62)
        print("  %s (%s)" % (name, script))
        print("-" * 62)
        try:
            r = subprocess.run(
                [sys.executable, path],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
            out = (r.stdout or "") + (r.stderr or "")
            for line in out.splitlines():
                s = line.strip()
                if s.startswith(("PASS", "FAIL")) or "测试结果" in s:
                    print("  " + s)
            if "测试结果" in out:
                line = [l for l in out.splitlines() if "测试结果" in l][-1]
                summary.append((name, line.strip()))
            else:
                summary.append((name, "异常退出 code=%s" % r.returncode))
                if r.returncode != 0:
                    print(out[-1200:])
        except Exception as e:
            print("  运行异常: %s" % e)
            summary.append((name, "ERROR"))

    # ---- 恢复初始状态 ----
    if was_empty and not keep:
        print("\n[恢复] 测试前是空库，正在还原为空库 ...")
        try:
            api_post("/api/demo/clear")
            print("       已清空")
        except Exception as e:
            print("       清空失败: %s" % e)
    elif keep:
        print("\n[恢复] --keep-data 已指定，保留当前数据")
    else:
        print("\n[恢复] 测试前已有数据，保持原状")

    print("\n" + "=" * 62)
    print("  汇总")
    print("=" * 62)
    total_p = total_t = 0
    for name, res in summary:
        print("  %-22s %s" % (name, res))
        # 累加 通过数/总数
        if "通过" in res:
            try:
                part = res.split("测试结果:")[-1].strip()
                a, b = part.split("/")
                total_p += int(a.strip())
                total_t += int(b.strip().replace("通过", "").strip())
            except Exception:
                pass
    print("  " + "-" * 40)
    print("  %-22s %d / %d 通过" % ("合计", total_p, total_t))
    print("=" * 62)


if __name__ == "__main__":
    main()
