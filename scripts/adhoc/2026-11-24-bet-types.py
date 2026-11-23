"""解説「舟券の種類」用:直近1年(boat_stats.py と同じ期間)の
単勝・2連単・2連複・3連単・3連複の払戻金(100円あたり)の中央値・平均・分布、1番人気決着率、
単勝の艇番別の割合、1万円以上の割合"""
import os, sys, statistics
from collections import Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

races = load("races")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
rs = [r for r in races if r["date"] >= since]
print("期間", since, "〜", last, "レース", len(rs))

TYPES = [("win", "単勝", 6), ("ex", "2連単", 30), ("qn", "2連複", 15), ("tri", "3連単", 120), ("trio", "3連複", 20)]


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


print("\n=== 券種別 払戻金(100円あたり)")
for k, name, combos in TYPES:
    pays = [num(r[f"{k}_pay"]) for r in rs]
    pays = [p for p in pays if p]
    pops = [num(r[f"{k}_pop"]) for r in rs]
    pops = [p for p in pops if p]
    n = len(pays)
    q = statistics.quantiles(pays, n=4)
    print(f" {name}(組み合わせ{combos}通り) n={n} 中央値{statistics.median(pays):.0f}円 平均{statistics.mean(pays):.0f}円 "
          f"25%点{q[0]:.0f} 75%点{q[2]:.0f} 最高{max(pays):.0f} 最低{min(pays):.0f}")
    print(f"   100円(元返し)={pct(sum(p == 100 for p in pays), n)}% 200円未満={pct(sum(p < 200 for p in pays), n)}% "
          f"1000円以上={pct(sum(p >= 1000 for p in pays), n)}% 1万円以上={pct(sum(p >= 10000 for p in pays), n)}%")
    if pops:
        pc = Counter(int(p) for p in pops)
        print(f"   人気あり n={len(pops)} 1番人気決着={pct(pc[1], len(pops))}% 3番人気以内={pct(pc[1]+pc[2]+pc[3], len(pops))}% "
              f"人気中央値{statistics.median(pops):.0f}")

print("\n=== 単勝 艇番(枠番)別の的中割合・払戻中央値")
wc = Counter()
wp = {}
for r in rs:
    c = r["win_combo"]
    p = num(r["win_pay"])
    if not c or not p:
        continue
    b = int(float(c))
    wc[b] += 1
    wp.setdefault(b, []).append(p)
tot = sum(wc.values())
for b in range(1, 7):
    print(f" {b}号艇 {wc[b]} ({pct(wc[b], tot)}%) 中央値{statistics.median(wp[b]):.0f}円")

print("\n=== 2連単と2連複が同じ組み合わせで決まったときの払戻比較(同レース)")
ratio = []
for r in rs:
    a, b = num(r["ex_pay"]), num(r["qn_pay"])
    if a and b:
        ratio.append(a / b)
print(f" n={len(ratio)} 2連単/2連複の倍率 中央値{statistics.median(ratio):.2f}")
ratio = []
for r in rs:
    a, b = num(r["tri_pay"]), num(r["trio_pay"])
    if a and b:
        ratio.append(a / b)
print(f" n={len(ratio)} 3連単/3連複の倍率 中央値{statistics.median(ratio):.2f}")

print("\n=== 1号艇が1着のとき/それ以外の3連単中央値")
for lab, cond in (("1号艇1着", lambda r: r["win_combo"] and int(float(r["win_combo"])) == 1),
                  ("それ以外", lambda r: r["win_combo"] and int(float(r["win_combo"])) != 1)):
    v = [num(r["tri_pay"]) for r in rs if cond(r) and num(r["tri_pay"])]
    print(f" {lab} n={len(v)} 3連単中央値{statistics.median(v):.0f}円 万舟率{pct(sum(p >= 10000 for p in v), len(v))}%")
