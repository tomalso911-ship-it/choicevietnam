# -*- coding: utf-8 -*-
"""查看云端接口返回的原始内容（排错用）"""
import sys
import json
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://agi-gs.tomalso911.workers.dev"


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def raw(path, body=None):
    url = BASE + path
    data = None
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("HTTP %s" % r.status)
            print(r.read().decode("utf-8", "replace")[:2000])
    except urllib.error.HTTPError as e:
        print("HTTP %s (error)" % e.code)
        print(e.read().decode("utf-8", "replace")[:2000])
    except Exception as e:
        print("EXC: %s" % e)


print("===== /api/health =====")
raw("/api/health")

print("\n===== /api/login (tom / 66668888) =====")
raw("/api/login", {"username": "tom", "password": "66668888"})
