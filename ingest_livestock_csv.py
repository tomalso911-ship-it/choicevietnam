# -*- coding: utf-8 -*-
"""
畜禽历史价格 CSV 录入脚本（新架构版）
================================
你把整理好的历史价格填进 livestock_manual_prices.csv，然后运行：
    python ingest_livestock_csv.py

数据以「collected 真值」写入 livestock_retail + livestock_farmgate 并锁死：
任何自动抓取/推导流程都不会覆盖这些月份（页面曲线不跳）。
2026-08 起的月份继续由每日自动任务(行情宝/GREENFEED)维护。

CSV 格式（见模板文件顶部注释）：
    item,country,year_month,price_cny,source
    pig,CN,2024-01,14.85,农业农村部月度均价

价格单位固定：元/公斤 (CNY/kg)。脚本按最新 USDCNY 汇率自动换算成 USD/kg 落库。
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "livestock_manual_prices.csv")

VALID_ITEMS = ("pig", "egg", "chicken")
VALID_CC = ("CN", "VN", "TH", "PH")


def _usdcny_latest(conn):
    """取 fx_cache 里 USDCNY 最新汇率，取不到用 7.1 兜底。"""
    try:
        row = conn.execute(
            "SELECT rate FROM fx_cache WHERE pair='USDCNY' ORDER BY date DESC LIMIT 1").fetchone()
        if row and row[0] and 5 < float(row[0]) < 10:
            return float(row[0])
    except Exception:
        pass
    return 7.1


def ingest(csv_path=CSV_PATH):
    if not os.path.exists(csv_path):
        print("CSV not found: %s" % csv_path)
        return 0
    conn = app.get_db()
    rate = _usdcny_latest(conn)
    print("Using USDCNY = %.4f" % rate)
    inserted = 0
    skipped = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        # 预过滤：去掉以 # 开头的注释行（含表头前的说明行）
        lines = [ln for ln in f if not ln.lstrip().startswith("#")]
    import io
    for row in csv.DictReader(io.StringIO("".join(lines))):
            item = (row.get("item") or "").strip().lower()
            cc = (row.get("country") or "").strip().upper()
            ym = (row.get("year_month") or "").strip()
            pc = (row.get("price_cny") or "").strip()
            pud = (row.get("price_usd") or "").strip()
            src = (row.get("source") or "manual").strip()
            if not item or item.startswith("#"):
                continue
            if item not in VALID_ITEMS:
                print("  skip unknown item: %s" % item)
                skipped += 1
                continue
            if cc not in VALID_CC:
                print("  skip unknown country: %s" % cc)
                skipped += 1
                continue
            if not (len(ym) == 7 and ym[4] == "-"):
                print("  skip bad year_month: %s" % ym)
                skipped += 1
                continue
            try:
                if pud:
                    # 直接给定 USD/kg（用户已换算好的数据，原样锁死）
                    price_usd = float(pud)
                else:
                    price_cny = float(pc)
                    price_usd = round(price_cny / rate, 4)
            except Exception:
                print("  skip bad price: %s" % (pud or pc))
                skipped += 1
                continue
            if price_usd <= 0 or price_usd > 500:
                print("  skip out-of-range price: %s %s %s %s" % (item, cc, ym, pud or pc))
                skipped += 1
                continue
            # retail（真值，锁死）
            conn.execute("""INSERT OR REPLACE INTO livestock_retail
                (item,country,ym,price_usd,unit,source_name,source_url,note)
                VALUES(?,?,?,?,?,?,?,?)""",
                (item, cc, ym, price_usd, "kg", "manual:%s" % src, "", "collected"))
            # farmgate（collected 级真值，推导流程不会覆盖）
            conn.execute("""INSERT OR REPLACE INTO livestock_farmgate
                (item,country,ym,price_usd,method,formula,source_url)
                VALUES(?,?,?,?,?,?,?)""",
                (item, cc, ym, price_usd, "collected", "manual_input(%s)" % src, ""))
            inserted += 1
    conn.commit()
    print("ingest done: inserted %d, skipped %d" % (inserted, skipped))
    # 概况
    for tbl in ("livestock_retail", "livestock_farmgate"):
        n = conn.execute("SELECT COUNT(*) FROM %s WHERE price_usd IS NOT NULL" % tbl).fetchone()[0]
        m = conn.execute("SELECT MIN(ym),MAX(ym) FROM %s WHERE price_usd IS NOT NULL" % tbl).fetchone()
        print("  %s: %d rows, range %s ~ %s" % (tbl, n, m[0], m[1]))
    conn.close()
    return inserted


if __name__ == "__main__":
    ingest()
