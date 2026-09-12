# -*- coding: utf-8 -*-
"""
云端数据备份工具

从 Cloudflare D1 导出核心业务表到本地 JSON 文件，用于：
  - 清空数据前的安全备份
  - 数据迁移前的快照

用法：
    python cloudflare/backup_cloud.py
    python cloudflare/backup_cloud.py my_backup
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

TABLES = [
    "users", "managers", "crm_projects", "won_projects",
    "lost_projects", "approval_requests", "login_history",
    "password_requests",
]

HERE = os.path.dirname(os.path.abspath(__file__))


def fetch(path, user="tom"):
    req = urllib.request.Request(
        API + path,
        headers={"User-Agent": UA, "X-User-Name": user},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else None
    stamp = label or time.strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(HERE, "backup_cloud_%s.json" % stamp)

    print("=" * 52)
    print("  云端数据备份")
    print("=" * 52)

    data = {"_backup_at": time.strftime("%Y-%m-%d %H:%M:%S"), "tables": {}}

    # 业务表通过 API 拉取（带权限过滤，管理员可见全部）
    for path, key in [
        ("/api/crm-projects?scope=all", "crm_projects"),
        ("/api/won-projects", "won_projects"),
        ("/api/lost-projects", "lost_projects"),
    ]:
        try:
            rows = fetch(path)
            data["tables"][key] = rows if isinstance(rows, list) else []
            print("  %-20s %5d 行" % (key, len(data["tables"][key])))
        except Exception as e:
            print("  %-20s 失败: %s" % (key, e))
            data["tables"][key] = []

    # 审批
    try:
        d = fetch("/api/approval-requests?scope=all")
        items = d.get("items", []) if isinstance(d, dict) else []
        data["tables"]["approval_requests"] = items
        print("  %-20s %5d 行" % ("approval_requests", len(items)))
    except Exception as e:
        print("  %-20s 失败: %s" % ("approval_requests", e))
        data["tables"]["approval_requests"] = []

    # 用户（不含密码明文，仅账号信息）
    try:
        d = fetch("/api/users")
        users = d.get("users", []) if isinstance(d, dict) else []
        # 不导出密码字段
        for u in users:
            u.pop("password", None)
        data["tables"]["users"] = users
        data["managers"] = d.get("managers", []) if isinstance(d, dict) else []
        print("  %-20s %5d 行" % ("users", len(users)))
        print("  %-20s %s" % ("managers", ", ".join(data["managers"])))
    except Exception as e:
        print("  %-20s 失败: %s" % ("users", e))
        data["tables"]["users"] = []

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in data["tables"].values())
    print("\n  合计 %d 行 -> %s" % (total, out_path))
    print("  大小: %.1f KB" % (os.path.getsize(out_path) / 1024))
    print("=" * 52)


if __name__ == "__main__":
    main()
