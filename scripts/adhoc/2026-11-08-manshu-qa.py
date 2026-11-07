"""Q&A「万舟はどのくらい出る?」用:直近1年(boat_stats.py と同じ期間)の3連単配当の分布、
人気別の決着割合、1コースの着順別の配当、レース番号別・優勝戦の万舟率、2連単・3連複の万舟率"""
import os, sys, statistics
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
rs = [r for r in races if r["date"] >= since]
print("期間", since, "〜", last, "レース", len(rs))
tri = [r for r in rs if r["tri_pay"]]
print("3連単払戻ありレース", len(tri))


def stat(sub, lab):
    p = [int(float(r["tri_pay"])) for r in sub if r["tri_pay"]]
    if not p:
        return
    m = sum(x >= 10000 for x in p)
    print(f" {lab}: n={len(p)} 中央値{round(statistics.median(p))} 平均{round(statistics.mean(p))}"
          f" 万舟{m} ({pct(m, len(p))}%) 10万以上{sum(x >= 100000 for x in p)}")


print("\n=== 全体")
stat(rs, "全体")
pays = [int(float(r["tri_pay"])) for r in tri]
print(" 最高", max(pays), " 最低", min(pays))
mean_all = statistics.mean(pays)
print(" 平均を下回るレースの割合", pct(sum(x < mean_all for x in pays), len(pays)))

print("\n=== 配当帯")
bands = [(0, 1000), (1000, 3000), (3000, 10000), (10000, 30000), (30000, 100000), (100000, 10**9)]
for a, b in bands:
    c = sum(a <= x < b for x in pays)
    print(f" {a}〜{b}: {c} ({pct(c, len(pays))}%)")

print("\n=== 3連単の人気(決着した組み合わせの人気順位)")
pops = [int(float(r["tri_pop"])) for r in rs if r["tri_pop"]]
print(" n", len(pops))
for a, b in [(1, 1), (1, 5), (1, 10), (1, 20), (21, 50), (51, 120)]:
    c = sum(a <= x <= b for x in pops)
    print(f" {a}〜{b}番人気: {c} ({pct(c, len(pops))}%)")
print(" 人気中央値", statistics.median(pops))

print("\n=== 1コースの艇の着順別")
ent = defaultdict(dict)
for e in entries:
    if e["date"] >= since:
        ent[(e["date"], e["jcd"], e["rno"])][e["course"]] = e
g = defaultdict(list)
for r in rs:
    c1 = ent.get((r["date"], r["jcd"], r["rno"]), {}).get("1")
    if not c1:
        continue
    f = c1["finish"]
    g["1着" if f == "1" else ("2〜3着" if f in ("2", "3") else "4着以下・その他")].append(r)
for k in ["1着", "2〜3着", "4着以下・その他"]:
    stat(g[k], k)

print("\n=== レース番号別")
for lo, hi in [(1, 3), (4, 6), (7, 9), (10, 12)]:
    stat([r for r in rs if lo <= int(r["rno"]) <= hi], f"{lo}〜{hi}R")
for n in (1, 12):
    stat([r for r in rs if int(r["rno"]) == n], f"{n}R")

print("\n=== 優勝戦")
stat([r for r in rs if r["race_type"] == "優勝戦"], "優勝戦")

print("\n=== 他の券種の万舟率(払戻1万円以上)")
for k in ["win", "ex", "qn", "trio"]:
    p = [int(float(r[f"{k}_pay"])) for r in rs if r[f"{k}_pay"]]
    print(f" {k}: n={len(p)} 中央値{round(statistics.median(p))} 1万以上{pct(sum(x >= 10000 for x in p), len(p))}%")
