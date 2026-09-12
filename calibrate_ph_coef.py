# -*- coding: utf-8 -*-
"""
菲律宾 PH 倒推系数校准：生成「逐月系数表」
====================================================
输入：ph_retail_for_calibration.csv
      item,year,month,farmgate_usd,retail_usd (USD/kg，已含汇率)
算法：
  coef(ym) = farmgate_usd / retail_usd
  对每个自然月(1-12)计算历史同月均值 -> 作为未来无真值月的兜底。
输出：
  打印 PH_INVERSE_COEF_BY_MONTH（逐月）与 PH_INVERSE_COEF_MONTH_AVG（同月均值）。
  可选 --write 把这两张表 + 读取函数写入 collect_livestock.py（替换原单值 PH_INVERSE_COEF）。
"""
import os, csv, re, argparse, statistics as ST
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "ph_retail_for_calibration.csv")
TARGET = os.path.join(BASE_DIR, "collect_livestock.py")


def load_csv(path=CSV_PATH):
    out = defaultdict(dict)  # item -> {ym: coef}
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            it = r["item"].strip().lower()
            ym = "%04d-%02d" % (int(r["year"]), int(r["month"]))
            fg = float(r["farmgate_usd"]); ret = float(r["retail_usd"])
            if ret > 0:
                out[it][ym] = fg / ret
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    data = load_csv()
    by_month = {}   # item -> {ym: coef}
    month_avg = {} # item -> {m: avg_coef}
    for it, d in data.items():
        by_month[it] = dict(d)
        mvals = defaultdict(list)
        for ym, c in d.items():
            mvals[int(ym[5:7])].append(c)
        month_avg[it] = {m: round(ST.mean(v), 4) for m, v in sorted(mvals.items())}

    print("=" * 70)
    print("PH INVERSE COEF - BY MONTH (from your truth+retail data)")
    print("=" * 70)
    for it in ["pig", "chicken", "egg"]:
        print(f"\n# {it}: PH_INVERSE_COEF_BY_MONTH[{it}]")
        for ym in sorted(by_month[it]):
            print(f'    "{ym}": {by_month[it][ym]:.4f},')
        print(f"\n# {it}: PH_INVERSE_COEF_MONTH_AVG[{it}] (same-month historical mean)")
        print("   ", month_avg[it])

    print("\n" + "=" * 70)
    print("SUGGESTED default per-month coef (for 2026-09+):")
    print("=" * 70)
    for m in range(1, 13):
        print(f"  month {m:02d}: pig={month_avg['pig'].get(m):.4f}  "
              f"chicken={month_avg['chicken'].get(m):.4f}  egg={month_avg['egg'].get(m):.4f}")

    if args.write:
        _write_back(by_month, month_avg)


def _dump_dict(name, d):
    """把 {item:{ym:coef}} 写成 python 字面量"""
    lines = [f"{name} = {{"]
    for it in ["pig", "chicken", "egg"]:
        lines.append(f'    "{it}": {{')
        for ym in sorted(d.get(it, {})):
            lines.append(f'        "{ym}": {d[it][ym]:.4f},')
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


def _write_back(by_month, month_avg):
    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()

    # 移除旧的 PH_INVERSE_COEF 单值定义块（含其上方注释到 PH_EGG_PIECE_KG 之前）
    # 用正则删掉从 'PH_INVERSE_COEF = {' 到 '}' 的单值定义
    src = re.sub(r'\nPH_INVERSE_COEF\s*=\s*\{[^}]*\}', "", src, flags=re.S)

    # 在 PH_EGG_PIECE_KG 定义之后插入新表 + 读取函数
    anchor = "PH_EGG_PIECE_KG = 0.060  # 1 枚≈60g"
    if anchor not in src:
        print("[write] 未找到 anchor，跳过回写")
        return

    block = (
        "\n\n"
        "# 菲律宾倒推系数：逐月表（来自用户真值出场价 ÷ 同期终端零售价，USD/kg）\n"
        "#   2021-01~2026-08 为真实校准值；2026-09 起无真值，用同月历史均值兜底。\n"
        + _dump_dict("PH_INVERSE_COEF_BY_MONTH", by_month) + "\n\n"
        + _dump_dict("PH_INVERSE_COEF_MONTH_AVG", month_avg) + "\n\n"
        "def ph_inverse_coef(item, ym):\n"
        '    """返回某品种某月的倒推系数 coef = 出场价/零售价。\n'
        '       优先用逐月真值校准值；缺则回退该自然月历史均值；再缺则 0.6 兜底。"""\n'
        "    bm = PH_INVERSE_COEF_BY_MONTH.get(item, {})\n"
        "    if ym in bm:\n"
        "        return bm[ym]\n"
        "    m = int(ym[5:7])\n"
        "    ma = PH_INVERSE_COEF_MONTH_AVG.get(item, {})\n"
        "    if m in ma:\n"
        "        return ma[m]\n"
        "    return 0.60\n"
    )
    src = src.replace(anchor, anchor + block, 1)
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(src)
    print("\n[write] wrote monthly coef tables + ph_inverse_coef() into collect_livestock.py")


if __name__ == "__main__":
    main()
