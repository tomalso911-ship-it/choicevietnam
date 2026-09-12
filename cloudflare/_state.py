# -*- coding: utf-8 -*-
"""快速查看云端数据状态"""
import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "https://agi-gs.tomalso911.workers.dev"
UA = "Mozilla/5.0"


def g(path, user="tom"):
    req = urllib.request.Request(
        API + path, headers={"User-Agent": UA, "X-User-Name": user})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


print("=" * 46)
print("  Cloud data status")
print("=" * 46)
for path, name in [
    ("/api/crm-projects?scope=all", "CRM"),
    ("/api/won-projects", "WON"),
    ("/api/lost-projects", "LOST"),
]:
    d = g(path)
    print("  %-6s %d" % (name, len(d) if isinstance(d, list) else -1))

d = g("/api/users")
print("  users  %d" % len(d.get("users", [])))
print("  admins %s" % ", ".join(d.get("managers", [])))
print("=" * 46)
