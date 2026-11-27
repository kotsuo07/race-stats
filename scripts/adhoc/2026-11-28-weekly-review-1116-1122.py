"""先週(2026-11-16〜11-22)の振り返り:レース数、1コース1着率(直近1年・前年同週との比較)、
日別の1コース1着率、3連単の中央値・万舟率、高配当トップ10、決まり手、場別1コース1着率"""
import os, sys, statistics
from collections import defaultdict, Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct, KIMARITE

WS, WE = "2026-11-16", "2026-11-22"
PS, PE = "2025-11-17", "2025-11-23"  # 前年同週(月〜日)
YS, YE = "2025-11-16", "2026-11-15"  # 先週より前の1年(比較用の平常値)

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

for lab, s, e in [("先週", WS, WE), ("前年同週", PS, PE), ("直前1年", YS, YE), ("前週", "2026-11-09", "2026-11-15")]:
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

print("\n=== 追加: 1コースが勝ったか否か別の万舟率(先週・直前1年)")
c1win = {(x["date"], x["jcd"], x["rno"]) for x in entries if x["course"] == "1" and x["finish"] == "1"}
for lab, s, e in [("先週", WS, WE), ("直前1年", YS, YE)]:
    rs = [r for r in races if s <= r["date"] <= e and r["tri_pay"]]
    for g, f in [("1コース1着", lambda r: (r["date"], r["jcd"], r["rno"]) in c1win),
                 ("1コース以外1着", lambda r: (r["date"], r["jcd"], r["rno"]) not in c1win)]:
        sub = [r for r in rs if f(r)]
        m = sum(int(r["tri_pay"]) >= 10000 for r in sub)
        med = round(statistics.median([int(r["tri_pay"]) for r in sub]))
        print(f" {lab} {g} {len(sub)}レース 万舟{m} ({pct(m, len(sub))}%) 中央値{med}")

print("\n=== 追加: 直前1年で先週最高配当以上の件数")
mx = max(int(r["tri_pay"]) for r in wk if r["tri_pay"])
yr = [r for r in races if YS <= r["date"] <= YE and r["tri_pay"]]
print(f" {YS}〜{YE} {len(yr)}レース中 {mx}円以上 {sum(int(r['tri_pay']) >= mx for r in yr)}")

print("\n=== 追加: 先週 10万円以上の件数と6コース(進入)1着数")
print(" 10万以上", sum(int(r["tri_pay"]) >= 100000 for r in wk if r["tri_pay"]))
w6 = sum(1 for x in wke if x["course"] == "6" and x["finish"] == "1")
n6 = sum(1 for x in wke if x["course"] == "6")
print(f" 6コース1着 {w6}/{n6} ({pct(w6, n6)}%)")
y6 = [x for x in entries if YS <= x["date"] <= YE and x["course"] == "6"]
print(f" 直前1年 6コース1着 {sum(x['finish']=='1' for x in y6)}/{len(y6)} ({pct(sum(x['finish']=='1' for x in y6), len(y6))}%)")

print("\n=== 追加: 先週 6コース(進入)1着のレース内訳")
c6 = [x for x in wke if x["course"] == "6" and x["finish"] == "1"]
rmap = {(r["date"], r["jcd"], r["rno"]): r for r in wk}
pays6 = [int(rmap[(x["date"], x["jcd"], x["rno"])]["tri_pay"]) for x in c6 if rmap[(x["date"], x["jcd"], x["rno"])]["tri_pay"]]
print(f" 6コース1着 {len(c6)}レース 3連単中央値 {round(statistics.median(pays6))} 万舟 {sum(p >= 10000 for p in pays6)}")
print(" 場別", Counter(rmap[(x['date'], x['jcd'], x['rno'])]['venue'] for x in c6).most_common())
print(" 決まり手", Counter(rmap[(x['date'], x['jcd'], x['rno'])]['kimarite'] for x in c6).most_common())
print(" トップ10のうち6コース1着", sum(1 for r in top if any(x['course'] == '6' and x['finish'] == '1' for x in ent[(r['date'], r['jcd'], r['rno'])].values())))
# 直前1年の週平均
yrs = [x for x in entries if YS <= x["date"] <= YE and x["course"] == "6" and x["finish"] == "1"]
print(f" 直前1年 6コース1着 {len(yrs)} 件 / 52週 = {round(len(yrs)/52.14, 1)} 件/週")

print("\n=== 追加: 強風の11/19・11/20 の風速別 1コース1着率")
for lab, f in [("風5m以上", lambda r: r["wind_m"] and float(r["wind_m"]) >= 5),
               ("風5m未満", lambda r: not (r["wind_m"] and float(r["wind_m"]) >= 5))]:
    keys = {k for k, r in rmap.items() if k[0] in ("2026-11-19", "2026-11-20") and f(r)}
    w, n = c1([x for x in wke if (x["date"], x["jcd"], x["rno"]) in keys])
    ms = [int(rmap[k]["tri_pay"]) for k in keys if rmap[k]["tri_pay"]]
    print(f" {lab} レース{len(keys)} 1C {pct(w, n)} ({w}/{n}) 万舟{sum(p>=10000 for p in ms)} ({pct(sum(p>=10000 for p in ms), len(ms))}%)")
mxw = max(float(r["wind_m"]) for r in wk if r["wind_m"])
print(" 先週最大風速", mxw, [(r["date"], r["venue"], r["rno"]) for r in wk if r["wind_m"] and float(r["wind_m"]) == mxw][:5])
