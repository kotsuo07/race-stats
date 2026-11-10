"""全国ランキング:場別の3連単配当中央値・万舟率・3連単1番人気決着率。
直近1年(boat_stats.py と同じ期間)と、その前の1年(前年同期間)を比較する。"""
import os, sys, statistics
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

races = load("races")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
prev_since = (date.fromisoformat(since) - timedelta(days=365)).isoformat()
prev_last = (date.fromisoformat(since) - timedelta(days=1)).isoformat()
print("直近1年", since, "〜", last, " 前年同期間", prev_since, "〜", prev_last)


def agg(sub):
    p = [int(float(r["tri_pay"])) for r in sub if r["tri_pay"]]
    pops = [int(float(r["tri_pop"])) for r in sub if r["tri_pay"] and r["tri_pop"]]
    return dict(n=len(p), med=statistics.median(p), mean=round(statistics.mean(p)),
                man=pct(sum(x >= 10000 for x in p), len(p)),
                pop1=pct(sum(x == 1 for x in pops), len(pops)), popn=len(pops))


cur = [r for r in races if since <= r["date"] <= last]
prv = [r for r in races if prev_since <= r["date"] <= prev_last]
print("全国 直近", agg(cur), "レース", len(cur))
print("全国 前年", agg(prv), "レース", len(prv))

byv = defaultdict(lambda: ([], []))
names = {}
for r in cur:
    byv[int(r["jcd"])][0].append(r); names[int(r["jcd"])] = r["venue"]
for r in prv:
    byv[int(r["jcd"])][1].append(r)

rows = []
for j, (c, p) in byv.items():
    a, b = agg(c), agg(p)
    rows.append((j, names[j], a, b))
rows.sort(key=lambda x: (-x[2]["med"], x[0]))
rank_prev = {j: i + 1 for i, (j, *_ ) in enumerate(sorted(rows, key=lambda x: (-x[3]["med"], x[0])))}
print("\n順位 jcd 場 | 直近: n 中央値 平均 万舟率 1番人気率 | 前年: n 中央値 万舟率 1番人気率 順位 | 中央値差")
for i, (j, nm, a, b) in enumerate(rows, 1):
    print(f"{i:2d} {j:02d} {nm} | {a['n']} {a['med']:.0f} {a['mean']} {a['man']} {a['pop1']} | "
          f"{b['n']} {b['med']:.0f} {b['man']} {b['pop1']} {rank_prev[j]} | {a['med']-b['med']:+.0f}")

print("\n1番人気決着率 順位(直近)")
for i, (j, nm, a, b) in enumerate(sorted(rows, key=lambda x: (-x[2]["pop1"], x[0])), 1):
    print(f"{i:2d} {nm} {a['pop1']}% (n={a['popn']}) 前年{b['pop1']}%")

# 1コース1着率(boat_stats の場別・直近1年)と中央値の相関
import json
summ = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "boat", "summary.json")))
c1 = {int(k): v["year"]["courses"][0]["win"] for k, v in summ["venues"].items()}
xs = [c1[j] for j, *_ in rows]; ys = [a["med"] for _, _, a, _ in rows]
mx, my = statistics.mean(xs), statistics.mean(ys)
r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5
print("\n1コース1着率と3連単中央値の相関係数 r =", round(r, 2))
up = sum(1 for _, _, a, b in rows if a["med"] > b["med"]); dn = sum(1 for _, _, a, b in rows if a["med"] < b["med"])
print("前年より中央値が上がった場", up, "下がった場", dn, "同じ", 24 - up - dn)
print("直近n範囲", min(a["n"] for *_, a, b in rows), max(a["n"] for *_, a, b in rows), " 前年n範囲", min(b["n"] for *_, b in rows), max(b["n"] for *_, b in rows))
