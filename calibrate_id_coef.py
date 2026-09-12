#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校准印尼（ID）鸡蛋、肉鸡的逐月倒推系数：
  coef = 出场价 USD/kg / 同期终端零售价 USD/kg
数据：id_retail_for_calibration.csv（用户手填真值）
猪（ID pig）9月后改为预测虚线，这里只输出鸡和蛋的系数。
"""
import csv, json, os, sys

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "id_retail_for_calibration.csv")

def load_csv():
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        for r in rd:
            # 品类列形如 "鸡蛋(出场)" / "肉鸡(活重出栏)" / "生猪(活重出场)"
            item_raw = r["品类"].strip()
            if item_raw.startswith("鸡蛋"):
                item = "egg"
            elif item_raw.startswith("肉鸡"):
                item = "chicken"
            elif item_raw.startswith("生猪"):
                item = "pig"
            else:
                continue
            y, m = int(r["年份"]), int(r["月份"])
            ym = "%04d-%02d" % (y, m)
            fg = float(r["出场价 USD/kg"])
            ret = float(r["同期终端零售价 USD/kg"])
            rows.append((item, ym, fg, ret))
    return rows


def build_tables(rows):
    by_month = {}
    ratios = {}
    for item, ym, fg, ret in rows:
        if item == "pig":
            continue  # 猪不参与零售倒推，9月后改预测
        ratio = fg / ret if ret else None
        if ratio is None or ratio <= 0:
            continue
        by_month.setdefault(item, {})[ym] = round(ratio, 4)
        ratios.setdefault(item, []).append((ym, ratio))

    month_avg = {}
    for item, lst in ratios.items():
        by_m = {}
        for ym, r in lst:
            m = int(ym[5:7])
            by_m.setdefault(m, []).append(r)
        month_avg[item] = {m: round(sum(vals)/len(vals), 4) for m, vals in by_m.items()}
    return by_month, month_avg


def report():
    rows = load_csv()
    by_month, month_avg = build_tables(rows)
    print("=== ID inverse coef (egg/chicken) ===")
    print("BY_MONTH count: egg=%d, chicken=%d" % (len(by_month.get("egg",{})), len(by_month.get("chicken",{}))))
    print("MONTH_AVG:")
    for item, ma in month_avg.items():
        print("  %s: %s" % (item, {m: ma.get(m) for m in range(1,13)}))
    print("\nSample 2026-08 coef: egg=%s, chicken=%s" % (
        by_month.get("egg", {}).get("2026-08"),
        by_month.get("chicken", {}).get("2026-08")))
    return by_month, month_avg


def generate_py_module():
    rows = load_csv()
    by_month, month_avg = build_tables(rows)
    out = []
    out.append("# 印尼（ID）终端零售价 → 出场价 逐月倒推系数表")
    out.append("# 来源：用户手填真值 2021-01~2026-08，coef = 出场价 USD/kg / 零售价 USD/kg")
    out.append("# 只含 egg/chicken；ID pig 2026-09 起改为 forecast 虚线，不参与零售倒推。")
    out.append("ID_INVERSE_COEF_BY_MONTH = {")
    for item in ["chicken", "egg"]:
        out.append('    "%s": {' % item)
        for ym in sorted(by_month.get(item, {}).keys()):
            out.append('        "%s": %.4f,' % (ym, by_month[item][ym]))
        out.append("    },")
    out.append("}")
    out.append("")
    out.append("ID_INVERSE_COEF_MONTH_AVG = {")
    for item in ["chicken", "egg"]:
        out.append('    "%s": {' % item)
        for m in range(1, 13):
            out.append('        %d: %.4f,' % (m, month_avg.get(item, {}).get(m, 0.55)))
        out.append("    },")
    out.append("}")
    out.append("")
    out.append("def id_inverse_coef(item, ym):")
    out.append('    """印尼 egg/chicken 逐月倒推系数：优先真值，缺则同月历史均值，再缺 0.55 兜底。"""')
    out.append("    bm = ID_INVERSE_COEF_BY_MONTH.get(item, {})")
    out.append("    if ym in bm:")
    out.append("        return bm[ym]")
    out.append("    m = int(ym[5:7])")
    out.append("    ma = ID_INVERSE_COEF_MONTH_AVG.get(item, {})")
    out.append("    if m in ma:")
    out.append("        return ma[m]")
    out.append("    if str(m) in ma:")
    out.append("        return ma[str(m)]")
    out.append("    return 0.55")
    return "\n".join(out)


def write_to_module():
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "collect_livestock.py")
    with open(module_path, "r", encoding="utf-8") as f:
        src = f.read()

    marker = "# FAOSTAT 生产者价（≈出栏价）最佳努力开关"
    if marker not in src:
        print("[write] marker not found in collect_livestock.py")
        return False

    block = generate_py_module()
    new_src = src.replace(marker, block + "\n\n" + marker)
    with open(module_path, "w", encoding="utf-8") as f:
        f.write(new_src)
    print("[write] wrote ID inverse coef tables into collect_livestock.py")
    return True


if __name__ == "__main__":
    if "--write" in sys.argv:
        write_to_module()
    else:
        report()
