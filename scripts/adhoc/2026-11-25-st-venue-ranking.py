"""全国ランキング:場別の平均スタートタイミング(ST)。
直近1年(boat_stats.py と同じ期間)と前年同期間を比較。
STの扱いは 2026-11-17-start-timing.py と同じ(フライング・出遅れ・欠場・コース不明を除く)。
あわせて1コースの平均ST、0.09以下の割合、フライング率(フライング艇のあったレースの割合)、
1コース1着率との相関を出す。"""
import os, sys, statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct, course_table

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
prev_since = (date.fromisoformat(since) - timedelta(days=365)).isoformat()
prev_last = (date.fromisoformat(since) - timedelta(days=1)).isoformat()
print("直近1年", since, "〜", last, " 前年同期間", prev_since, "〜", prev_last)
names = {r["jcd"]: r["venue"] for r in races}


def valid(e):
    return e["flying"] == "0" and e["st"] not in ("", None) and not e["finish"].startswith("L") and e["course"]


def stats(es, rs):
    ok = [e for e in es if valid(e)]
    st = [float(e["st"]) for e in ok]
    c1 = [float(e["st"]) for e in ok if int(float(e["course"])) == 1]
    c6 = [float(e["st"]) for e in ok if int(float(e["course"])) == 6]
    fast = sum(x <= 0.09 + 1e-9 for x in st)
    fr = len({(e["date"], e["jcd"], e["rno"]) for e in es if e["flying"] == "1"})
    fb = sum(e["flying"] == "1" for e in es)
    return dict(n=len(st), mean=statistics.mean(st), med=statistics.median(st),
                c1=statistics.mean(c1), c1n=len(c1), c6=statistics.mean(c6),
                fast=pct(fast, len(st)), fr=pct(fr, len(rs), 2), frn=fr, fb=fb, races=len(rs))


cur_r = [r for r in races if since <= r["date"] <= last]
prv_r = [r for r in races if prev_since <= r["date"] <= prev_last]
cur_e = [e for e in entries if since <= e["date"] <= last]
prv_e = [e for e in entries if prev_since <= e["date"] <= prev_last]

for lab, es, rs in (("直近", cur_e, cur_r), ("前年", prv_e, prv_r)):
    s = stats(es, rs)
    print(f"\n全国 {lab}: レース{s['races']} ST艇数{s['n']} 平均{s['mean']:.3f} 中央値{s['med']:.2f} "
          f"1C平均{s['c1']:.3f} 6C平均{s['c6']:.3f} 0.09以下{s['fast']}% フライングレース{s['frn']}({s['fr']}%) F艇{s['fb']}")

ve_c, ve_p, vr_c, vr_p = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
for e in cur_e: ve_c[e["jcd"]].append(e)
for e in prv_e: ve_p[e["jcd"]].append(e)
for r in cur_r: vr_c[r["jcd"]].append(r)
for r in prv_r: vr_p[r["jcd"]].append(r)

S = {j: stats(ve_c[j], vr_c[j]) for j in sorted(ve_c)}
P = {j: stats(ve_p[j], vr_p[j]) for j in sorted(ve_p)}
C1W = {j: course_table(ve_c[j])[0]["win"] for j in S}

order = sorted(S, key=lambda j: (round(S[j]["mean"], 3), j))
prk = {j: i + 1 for i, j in enumerate(sorted(P, key=lambda j: (round(P[j]["mean"], 3), j)))}
print("\n=== 平均ST 早い順(直近) | 中央値 | 0.09以下 | 1C平均 | 6C平均 | フライングレース率 | 1C1着率 | 前年平均 | 前年順位 | 差")
for i, j in enumerate(order, 1):
    s, p = S[j], P[j]
    print(f"{i:2d} {j} {names[j]} {s['mean']:.3f} (n={s['n']}, races={s['races']}) | {s['med']:.2f} | {s['fast']}% | "
          f"{s['c1']:.3f} (n={s['c1n']}) | {s['c6']:.3f} | {s['fr']}% ({s['frn']}) | {C1W[j]}% | "
          f"{p['mean']:.3f} (races={p['races']}) | {prk[j]} | {s['mean'] - p['mean']:+.3f}")
print("ST艇数範囲", min(s["n"] for s in S.values()), max(s["n"] for s in S.values()),
      " 前年レース数範囲", min(p["races"] for p in P.values()), max(p["races"] for p in P.values()))

print("\n=== 1コース平均ST 早い順")
for i, j in enumerate(sorted(S, key=lambda j: (round(S[j]["c1"], 3), j)), 1):
    print(f"{i:2d} {names[j]} {S[j]['c1']:.3f} (n={S[j]['c1n']}) 1C1着率 {C1W[j]}%")

print("\n=== フライングレース率 高い順")
for i, j in enumerate(sorted(S, key=lambda j: (-S[j]["fr"], j)), 1):
    print(f"{i:2d} {names[j]} {S[j]['fr']}% ({S[j]['frn']}/{S[j]['races']}) 前年 {P[j]['fr']}% ({P[j]['frn']}/{P[j]['races']})")


def corr(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (
        sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5

js = list(S)
print("\n相関 平均ST vs 1C1着率 r =", round(corr([S[j]["mean"] for j in js], [C1W[j] for j in js]), 2))
print("相関 1C平均ST vs 1C1着率 r =", round(corr([S[j]["c1"] for j in js], [C1W[j] for j in js]), 2))
print("相関 平均ST 直近 vs 前年 r =", round(corr([S[j]["mean"] for j in js], [P[j]["mean"] for j in js]), 2))
