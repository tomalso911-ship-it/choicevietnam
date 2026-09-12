# -*- coding: utf-8 -*-
"""
价格模块快照生成（M9）

原理：
  直接调用本地 app.py 的 Flask 接口，把【最终响应结果】存成 JSON。
  这样做的好处是 100% 复刻现有逻辑（月度聚合、波峰波谷降采样、货币换算
  全部由原代码计算），云端 Workers 只需读取 JSON 直接返回，零计算、秒开。

  注意：用 Flask 的 test_client，不会真的启动服务器进程。

产出：
  cloudflare/price_snapshot.json  -> 上传到 R2

用法：
    python cloudflare/build_price_snapshot.py
"""
import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

OUT = os.path.join(HERE, "price_snapshot.json")

# 需要生成快照的接口（path 即 R2 中的 key 名）
ENDPOINTS = []
for cur in ("USD", "RMB", "VND"):
    ENDPOINTS.append(("/api/metal-prices?cur=%s" % cur, "metal_%s.json" % cur))
    ENDPOINTS.append(("/api/feed-prices?cur=%s" % cur, "feed_%s.json" % cur))
    ENDPOINTS.append(("/api/livestock-prices?cur=%s" % cur, "livestock_%s.json" % cur))
    ENDPOINTS.append(("/api/livestock-farmgate?cur=%s" % cur, "farmgate_%s.json" % cur))
ENDPOINTS.append(("/api/fx-rates", "fx.json"))
ENDPOINTS.append(("/api/livestock-retail-raw", "retail_raw.json"))


def _load_cf_token():
    """从根目录 .env 或环境变量读取 Cloudflare API Token。"""
    env_path = os.path.join(ROOT, ".env")
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not token and os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CLOUDFLARE_API_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return token


def _cf_account_id(token):
    """用 Token 列出账户，返回第一个账户 ID。"""
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/accounts",
        headers={"Authorization": "Bearer " + token, "User-Agent": "agi-pm-snapshot/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            js = json.loads(r.read().decode("utf-8"))
        if js.get("success") and js.get("result"):
            return js["result"][0]["id"]
    except Exception as e:
        print("    获取 account_id 失败: %s" % e)
    return ""


def _upload_to_r2(local_path, key="price_snapshot.json"):
    """把生成的快照文件上传到 R2 bucket（使用 Cloudflare REST API）。"""
    token = _load_cf_token()
    if not token:
        print("    未配置 CLOUDFLARE_API_TOKEN，跳过 R2 上传")
        return False
    account_id = _cf_account_id(token)
    if not account_id:
        print("    无法获取 Cloudflare account_id，跳过 R2 上传")
        return False
    bucket = "agi-pm-files"
    url = "https://api.cloudflare.com/client/v4/accounts/%s/r2/buckets/%s/objects/%s" % (
        account_id, urllib.parse.quote(bucket), urllib.parse.quote(key))
    try:
        with open(local_path, "rb") as f:
            data = f.read()
        req = urllib.request.Request(
            url, data=data, method="PUT",
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
                "User-Agent": "agi-pm-snapshot/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            js = json.loads(r.read().decode("utf-8"))
        if js.get("success"):
            print("    -> R2 上传成功: %s" % key)
            return True
        else:
            print("    R2 上传失败: %s" % js.get("errors"))
    except Exception as e:
        print("    R2 上传异常: %s" % e)
    return False


def main():
    print("=" * 60)
    print("  价格模块快照生成（M9）")
    print("=" * 60)

    # 切到根目录再导入，保证 app.py 能找到同目录的配置/数据库
    os.chdir(ROOT)

    # [0] 先跑畜禽采集管道，把猪价/鸡蛋/肉鸡的最新月份补进库
    #     --online 抓取实时价；--incremental 只延伸到当前月，历史已锁死不动。
    print("\n[0] 畜禽采集管道 collect_livestock.py --seed-real --incremental --online ...")
    try:
        rc = subprocess.call(
            [sys.executable, "collect_livestock.py", "--seed-real", "--incremental", "--online"],
            cwd=ROOT,
        )
        print("    畜禽采集退出码: %s" % rc)
    except Exception as e:
        print("    畜禽采集异常（跳过，仍继续生成快照）: %s" % e)

    print("\n[1] 导入本地 app.py ...")
    t0 = time.time()
    try:
        import app as flask_app
    except Exception as e:
        print("    导入失败: %s" % e)
        print("    提示：请在项目根目录运行，且确保依赖已安装")
        sys.exit(1)
    print("    导入完成 (%.1fs)" % (time.time() - t0))

    # [1.5] 强制同步预热汇率/金属/饲料缓存，避免后台 warm 没完成就生成快照导致当月缺失
    print("\n[1.5] 同步预热 汇率/金属/饲料 缓存 ...")
    try:
        conn = flask_app.get_db()
        try:
            flask_app._fx_build_data(conn)
            flask_app._metal_build_data(conn)
            flask_app._feed_build_data(conn)
            print("    预热完成")
        finally:
            conn.close()
    except Exception as e:
        print("    预热异常（继续生成快照）: %s" % e)

    client = flask_app.app.test_client()

    print("\n[2] 生成各接口响应快照 ...")
    snap = {
        "_meta": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "local app.py (Flask test_client)",
            "count": len(ENDPOINTS),
        },
        "data": {},
    }

    ok, fail = 0, 0
    for path, key in ENDPOINTS:
        t1 = time.time()
        try:
            resp = client.get(path)
            if resp.status_code != 200:
                print("    FAIL  %-42s HTTP %s" % (path, resp.status_code))
                fail += 1
                continue
            payload = resp.get_json()
            snap["data"][key] = payload

            # 简要统计
            if isinstance(payload, dict):
                n_lab = len(payload.get("labels") or [])
                n_ser = len(payload.get("series") or {})
                extra = "labels=%d series=%d" % (n_lab, n_ser)
            else:
                extra = "type=%s" % type(payload).__name__

            size = len(json.dumps(payload, ensure_ascii=False))
            print("    OK    %-42s %7.1f KB  %s  (%.1fs)"
                  % (path, size / 1024, extra, time.time() - t1))
            ok += 1
        except Exception as e:
            print("    FAIL  %-42s %s" % (path, e))
            fail += 1

    print("\n[3] 写入文件 ...")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(OUT)
    print("    -> %s" % OUT)
    print("    %.1f KB" % (size / 1024))

    print("\n" + "=" * 60)
    print("  完成: 成功 %d / 失败 %d" % (ok, fail))
    print("=" * 60)

    # [4] 自动上传到 R2，云端 Worker 才能读取最新价格快照
    if ok > 0:
        print("\n[4] 上传到 R2 ...")
        _upload_to_r2(OUT)

    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
