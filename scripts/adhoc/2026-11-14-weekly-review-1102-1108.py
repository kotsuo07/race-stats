"""先週(2026-11-02〜11-08)の振り返り:レース数、1コース1着率(直近1年・前年同週との比較)、
日別の1コース1着率、3連単の中央値・万舟率、高配当トップ10、決まり手、場別1コース1着率"""
import os, sys, statistics
from collections import defaultdict, Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct, KIMARITE

WS, WE = "2026-11-02", "2026-11-08"
PS, PE = "2025-11-03", "2025-11-09"  # 前年同週(月〜日)
YS, YE = "2025-11-02", "2026-11-01"  # 先週より前の1年(比較用の平常値)

races, entries = load("races"), load("entries")
print("データ最終日", max(r["date"] for r in races))

def c1(es):
    c = [e for e in es if e["course"] == "1"]
    return sum(e["finish"] == "1" for e in c), len(c)

def pay(rs):
    tri = [int(r["tri_pay"]) for r in rs if r["tri_pay"]]
    pops = [int(r["tri_pop"]) for r in rs if r["tri_pop"]]
    return {"tri_n": len(tri), "median": round(statistics.median(tri)), "mean": round(statistics.mean(tri)),
            "manshu": sum(x >= 10000 for x in tri), "manshu_pct": pct(sum(x >= 10000 for x in tri), len(tri)),
            "10man": sum(x >= 100000 for x in tri), "pop1_pct": pct(sum(p == 1 for p in pops), len(pops))}

def kim(rs):
    k = Counter(r["kimarite"] for r in rs if r["kimarite"])
    t = sum(k.values())
    return {x: pct(k[x], t) for x in KIMARITE}, t

for lab, s, e in [("先週", WS, WE), ("前年同週", PS, PE), ("直前1年", YS, YE), ("前週", "2026-10-26", "2026-11-01")]:
    rs = [r for r in races if s <= r["date"] <= e]
    es = [x for x in entries if s <= x["date"] <= e]
    w, n = c1(es)
    print(f"\n=== {lab} {s}〜{e} レース{len(rs)} 開催日x場 {len({(r['date'], r['jcd']) for r in rs})}"
          f" 場数{len({r['jcd'] for r in rs})}")
    print(" 1コース1着率", pct(w, n), f"({w}/{n})")
    print(" 3連単", pay(rs))
    print(" 決まり手", kim(rs))

wk = [r for r in races if WS <= r["date"] <= WE]
wke = [x for x in entries if WS <= x["date"] <= WE]
print("\n=== 先週 日別")
for d in sorted({r["date"] for r in wk}):
    rs = [r for r in wk if r["date"] == d]
    w, n = c1([x for x in wke if x["date"] == d])
    p = pay(rs)
    print(f" {d} レース{len(rs)} 場{len({r['jcd'] for r in rs})} 1C {pct(w, n)} ({w}/{n}) 万舟{p['manshu']} ({p['manshu_pct']}%) 中央値{p['median']}")

print("\n=== 先週 3連単高配当トップ10")
ent = defaultdict(dict)
for x in wke:
    ent[(x["date"], x["jcd"], x["rno"])][x["boat"]] = x
top = sorted([r for r in wk if r["tri_pay"]], key=lambda r: -int(r["tri_pay"]))[:10]
for r in top:
    ee = ent[(r["date"], r["jcd"], r["rno"])]
    win = [x for x in ee.values() if x["finish"] == "1"]
    wc = win[0]["course"] if win else "?"
    b1 = ee.get("1", {})
    print(f" {r['date']} {r['venue']} {r['rno']}R {r['race_type']} 3連単{r['tri_combo']} {int(r['tri_pay']):,}円 "
          f"{r['tri_pop']}番人気 決まり手{r['kimarite']} 1着進入{wc}C 1号艇着順{b1.get('finish')} "
          f"風{r['wind_m']}m 波{r['wave_cm']}cm 天候{r['weather']}")

print("\n=== 先週 場別 1コース1着率(全レース数)")
rows = []
for j in sorted({r["jcd"] for r in wk}):
    rs = [r for r in wk if r["jcd"] == j]
    w, n = c1([x for x in wke if x["jcd"] == j])
    yr = c1([x for x in entries if YS <= x["date"] <= YE and x["jcd"] == j])
    p = pay(rs)
    rows.append((pct(w, n), rs[0]["venue"], j, w, n, pct(*yr), yr[1], p["manshu"], p["manshu_pct"]))
for r in sorted(rows, reverse=True):
    print(f" {r[1]}({r[2]}) 先週{r[0]}% ({r[3]}/{r[4]}) 直前1年{r[5]}% (n={r[6]}) 差{round(r[0]-r[5],1)} 万舟{r[7]} ({r[8]}%)")

print("\n=== 先週 優勝戦")
for r in wk:
    if "優勝" in r["race_type"]:
        ee = ent[(r["date"], r["jcd"], r["rno"])]
        win = [x for x in ee.values() if x["finish"] == "1"]
        print(f" {r['date']} {r['venue']} {r['race_type']} 1着{win[0]['boat'] if win else '?'}号艇 進入{win[0]['course'] if win else '?'} "
              f"{r['kimarite']} 3連単{r['tri_combo']} {r['tri_pay']}円 {r['tri_pop']}番人気")

print("\n=== 先週 優勝戦のみ(準優勝戦を除く)集計")
fin = [r for r in wk if r["race_type"] == "優勝戦"]
c1w = 0
for r in fin:
    ee = ent[(r["date"], r["jcd"], r["rno"])]
    c1w += any(x["course"] == "1" and x["finish"] == "1" for x in ee.values())
print(f" 優勝戦 {len(fin)}レース うち1コース1着 {c1w} ({pct(c1w, len(fin))}%)")
print(" 3連単", pay(fin))

print("\n=== 先週 日別 風速5m以上・波高5cm以上の割合")
for d in sorted({r["date"] for r in wk}):
    rs = [r for r in wk if r["date"] == d]
    w5 = sum(1 for r in rs if r["wind_m"] and float(r["wind_m"]) >= 5)
    v5 = sum(1 for r in rs if r["wave_cm"] and float(r["wave_cm"]) >= 5)
    print(f" {d} 風5m以上 {w5}/{len(rs)} ({pct(w5, len(rs))}%) 波5cm以上 {v5}/{len(rs)} ({pct(v5, len(rs))}%) 場:{','.join(sorted({r['venue'] for r in rs}))}")

print("\n=== 追加: 先週の最高配当の位置づけ")
mx = max(int(r["tri_pay"]) for r in wk if r["tri_pay"])
allp = [r for r in races if r["tri_pay"]]
print(f" 全期間 {min(r['date'] for r in races)}〜{max(r['date'] for r in races)} 3連単払戻あり{len(allp)}レース")
print(" 先週最高", mx, "以上の件数(全期間)", sum(int(r["tri_pay"]) >= mx for r in allp))
yr = [r for r in allp if YS <= r["date"] <= WE]
print(f" {YS}〜{WE} {len(yr)}レース中 {mx}以上", sum(int(r["tri_pay"]) >= mx for r in yr))
for r in sorted(allp, key=lambda r: -int(r["tri_pay"]))[:5]:
    print("  ", r["date"], r["venue"], r["rno"], r["tri_combo"], r["tri_pay"], r["tri_pop"])

print("\n=== 追加: 先週 風速5m以上とそれ以外の1コース1着率")
idx = {(r["date"], r["jcd"], r["rno"]): r for r in wk}
for lab, f in [("風5m以上", lambda r: r["wind_m"] and float(r["wind_m"]) >= 5),
               ("風5m未満", lambda r: not (r["wind_m"] and float(r["wind_m"]) >= 5))]:
    keys = {k for k, r in idx.items() if f(r)}
    w, n = c1([x for x in wke if (x["date"], x["jcd"], x["rno"]) in keys])
    print(f" {lab} レース{len(keys)} 1C {pct(w, n)} ({w}/{n})")
