#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AGI-PM 一键双备份：本地 SQLite + 云端 D1 SQL 导出。

用法：
    python backup_agipm.py           # 本地 + 云端一起备
    python backup_agipm.py --local   # 只备本地 SQLite
    python backup_agipm.py --cloud   # 只备云端 D1

产物（统一时间戳，便于配对恢复）：
    backups/agi_pm_dev_<TIMESTAMP>.db      开发调试库（python app.py）
    backups/agi_pm_desktop_<TIMESTAMP>.db  桌面版运行库（%APPDATA%\\AGI-PM）
    backups/d1_<TIMESTAMP>.sql             云端 D1 SQL 转储

恢复：
    本地：关闭服务后，用备份 .db 直接覆盖原 agi_pm.db 即可。
    云端：wrangler d1 execute agi-pm-db --remote --file backups/d1_<TIMESTAMP>.sql
          （会清空当前 D1 再灌入，谨慎操作）
"""
import os
import sys
import shutil
import subprocess
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(ROOT, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _find_node_bin():
    """定位 node.exe 所在目录，供 wrangler.cmd 调用（逻辑与 build_pages.py 一致）。"""
    try:
        from shutil import which
        n = which("node")
        if n:
            return os.path.dirname(os.path.abspath(n))
    except Exception:
        pass

    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "node"),
        r"C:\Program Files\nodejs",
        r"C:\Program Files (x86)\nodejs",
    ]
    wb = os.path.join(os.environ.get("USERPROFILE", ""), ".workbuddy", "binaries", "node", "versions")
    if os.path.isdir(wb):
        for d in sorted(os.listdir(wb), reverse=True):
            candidates.append(os.path.join(wb, d))
    for c in candidates:
        if os.path.isfile(os.path.join(c, "node.exe")):
            return c
    return ""


def _load_cf_token():
    """从环境变量或 cloudflare/.env 读取 CLOUDFLARE_API_TOKEN。"""
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if token:
        return token
    env_path = os.path.join(ROOT, "cloudflare", ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CLOUDFLARE_API_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def backup_local(ts):
    """备份本机 SQLite 数据库（开发目录 + 桌面版 APPDATA 目录）。"""
    appdata = os.environ.get("APPDATA", "")
    candidates = [
        ("dev", os.path.join(ROOT, "agi_pm.db")),
    ]
    if appdata:
        candidates.append(("desktop", os.path.join(appdata, "AGI-PM", "agi_pm.db")))

    saved = []
    for tag, src in candidates:
        if not os.path.isfile(src):
            continue
        dst = os.path.join(BACKUP_DIR, "agi_pm_%s_%s.db" % (tag, ts))
        try:
            shutil.copy2(src, dst)
            saved.append((src, dst))
        except Exception as e:
            print("[WARN] 复制 %s 失败: %s" % (src, e))
    return saved


def backup_cloud(ts):
    """使用 wrangler 导出远程 D1 为 SQL 文件（只读，不会修改云端数据）。"""
    token = _load_cf_token()
    if not token:
        print("[ERROR] 未找到 CLOUDFLARE_API_TOKEN（环境变量或 cloudflare/.env）")
        return None

    node_bin = _find_node_bin()
    wrangler = os.path.join(ROOT, "cloudflare", "node_modules", ".bin", "wrangler.cmd")
    if not os.path.isfile(wrangler):
        wrangler = "wrangler"

    out = os.path.join(BACKUP_DIR, "d1_%s.sql" % ts)
    env = dict(os.environ)
    env["CLOUDFLARE_API_TOKEN"] = token
    if node_bin:
        env["PATH"] = node_bin + os.pathsep + env.get("PATH", "")

    cmd = [wrangler, "d1", "export", "DB", "--remote", "--output", out]
    print("[RUN] %s" % " ".join(cmd))
    p = subprocess.run(
        cmd,
        cwd=os.path.join(ROOT, "cloudflare"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if p.returncode != 0:
        print("[ERROR] 云端 D1 导出失败：\n%s" % p.stdout)
        return None
    print("[OK] 云端 D1 导出完成：%s" % out)
    if p.stdout:
        for line in p.stdout.strip().splitlines():
            print("   %s" % line)
    return out


def main():
    do_local = "--cloud" not in sys.argv
    do_cloud = "--local" not in sys.argv

    ts = _ts()
    print("=" * 60)
    print("AGI-PM 备份开始：%s" % ts)
    print("备份目录：%s" % BACKUP_DIR)
    print("=" * 60)

    failed = False

    if do_local:
        saved = backup_local(ts)
        if saved:
            print("[OK] 本地数据库备份完成：")
            for src, dst in saved:
                mb = os.path.getsize(dst) / (1024 * 1024)
                print("   %-40s -> %s (%.2f MB)" % (src, os.path.basename(dst), mb))
        else:
            print("[WARN] 未找到本机 agi_pm.db（开发目录或 APPDATA\\AGI-PM）")

    if do_cloud:
        out = backup_cloud(ts)
        if not out:
            failed = True

    print("=" * 60)
    if failed:
        print("[FAIL] 备份存在失败项，请查看上方输出")
        print("=" * 60)
        sys.exit(1)
    print("[DONE] 全部备份完成：%s" % BACKUP_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
