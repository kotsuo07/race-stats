"""下関(19)と戸田(02)の比較:直近1年の1号艇の1コース進入率、コース別平均ST、
1コース1着時の内訳、1コースが負けたときの勝者コース、3連単人気別、配当帯の分布"""
import os, sys, statistics
from collections import defaultdict, Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
print(f"期間 {since}〜{last}")
by_race = defaultdict(list)
for e in entries:
    if e["date"] >= since and e["jcd"] in ("02", "19"):
        by_race[(e["date"], e["jcd"], e["rno"])].append(e)

for jcd in ("19", "02"):
    rs = [r for r in races if r["date"] >= since and r["jcd"] == jcd]
    print(f"\n==== {rs[0]['venue']} {len(rs)}レース")
    es = [e for r in rs for e in by_race.get((r["date"], r["jcd"], r["rno"]), [])]
    b1 = [e for e in es if e["boat"] == "1" and e["course"]]
    print("1号艇の1コース進入率", pct(sum(e["course"] == "1" for e in b1), len(b1)), len(b1))
    # 枠なり率(全艇が艇番=コース)
    full = 0; nr = 0
    for r in rs:
        ee = by_race.get((r["date"], r["jcd"], r["rno"]), [])
        if len(ee) == 6 and all(e["course"] for e in ee):
            nr += 1
            full += all(e["boat"] == e["course"] for e in ee)
    print("枠なり率", pct(full, nr), nr)
    print("コース別平均ST(F除く, 数値のみ)")
    for c in "123456":
        st = [float(e["st"]) for e in es if e["course"] == c and e["st"] and e["flying"] == "0"
              and e["st"].replace(".", "").isdigit()]
        print(" ", c, round(statistics.mean(st), 3) if st else None, len(st))
    # 1コースが1着でないときの勝者コース
    lose = Counter()
    for r in rs:
        ee = by_race.get((r["date"], r["jcd"], r["rno"]), [])
        w = [e for e in ee if e["finish"] == "1"]
        if w and w[0]["course"] and w[0]["course"] != "1":
            lose[w[0]["course"]] += 1
    tot = sum(lose.values())
    print("1コース以外が勝ったレース", tot, {c: (lose[c], pct(lose[c], tot)) for c in "23456"})
    tri = [int(r["tri_pay"]) for r in rs if r["tri_pay"]]
    print("3連単 件数", len(tri))
    for lab, lo, hi in [("1,000円未満", 0, 999), ("1,000〜2,999円", 1000, 2999), ("3,000〜9,999円", 3000, 9999),
                        ("1万〜4万9,999円", 10000, 49999), ("5万円以上", 50000, 10**9)]:
        k = sum(lo <= x <= hi for x in tri)
        print(" ", lab, k, pct(k, len(tri)))
    pops = [int(r["tri_pop"]) for r in rs if r["tri_pop"]]
    print("3連単 1〜3番人気決着", pct(sum(p <= 3 for p in pops), len(pops)), len(pops))
    print("風速5m以上の割合", pct(sum(1 for r in rs if r["wind_m"] and int(float(r["wind_m"])) >= 5), len(rs)))
