"""江戸川(03)と平和島(04)の比較:直近1年の風速・波高の分布、波高別1コース1着率、
1号艇の1コース進入率、枠なり率、コース別平均ST、1コース以外が勝ったときの勝者コース、
3連単の配当帯と人気決着"""
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
    if e["date"] >= since and e["jcd"] in ("03", "04"):
        by_race[(e["date"], e["jcd"], e["rno"])].append(e)


def c1_win(rs):
    n = w = 0
    for r in rs:
        for e in by_race.get((r["date"], r["jcd"], r["rno"]), []):
            if e["course"] == "1":
                n += 1
                w += e["finish"] == "1"
    return pct(w, n), n


for jcd in ("03", "04"):
    rs = [r for r in races if r["date"] >= since and r["jcd"] == jcd]
    print(f"\n==== {rs[0]['venue']} {len(rs)}レース  開催日数 {len({r['date'] for r in rs})}")
    winds = [float(r["wind_m"]) for r in rs if r["wind_m"]]
    waves = [float(r["wave_cm"]) for r in rs if r["wave_cm"]]
    print("風速 平均", round(statistics.mean(winds), 2), "件数", len(winds),
          "5m以上", pct(sum(w >= 5 for w in winds), len(winds)))
    print("波高 平均", round(statistics.mean(waves), 2), "件数", len(waves))
    for lab, lo, hi in [("0〜2cm", 0, 2), ("3〜5cm", 3, 5), ("6cm以上", 6, 999)]:
        sub = [r for r in rs if r["wave_cm"] and lo <= float(r["wave_cm"]) <= hi]
        print(f"  波高{lab}: {len(sub)}レース ({pct(len(sub), len(rs))}%) 1コース1着率", c1_win(sub))
    print("全体 1コース1着率", c1_win(rs))
    es = [e for r in rs for e in by_race.get((r["date"], r["jcd"], r["rno"]), [])]
    b1 = [e for e in es if e["boat"] == "1" and e["course"]]
    print("1号艇の1コース進入率", pct(sum(e["course"] == "1" for e in b1), len(b1)), len(b1))
    full = nr = 0
    for r in rs:
        ee = by_race.get((r["date"], r["jcd"], r["rno"]), [])
        if len(ee) == 6 and all(e["course"] for e in ee):
            nr += 1
            full += all(e["boat"] == e["course"] for e in ee)
    print("枠なり率", pct(full, nr), nr)
    print("コース別平均ST(F除く)")
    for c in "123456":
        st = [float(e["st"]) for e in es if e["course"] == c and e["st"] and e["flying"] == "0"
              and e["st"].replace(".", "").isdigit()]
        print(" ", c, round(statistics.mean(st), 3) if st else None, len(st))
    lose = Counter()
    for r in rs:
        w = [e for e in by_race.get((r["date"], r["jcd"], r["rno"]), []) if e["finish"] == "1"]
        if w and w[0]["course"] and w[0]["course"] != "1":
            lose[w[0]["course"]] += 1
    tot = sum(lose.values())
    print("1コース以外が勝ったレース", tot, pct(tot, len(rs)), {c: (lose[c], pct(lose[c], tot)) for c in "23456"})
    tri = [int(r["tri_pay"]) for r in rs if r["tri_pay"]]
    print("3連単 件数", len(tri))
    for lab, lo, hi in [("1,000円未満", 0, 999), ("1,000〜2,999円", 1000, 2999), ("3,000〜9,999円", 3000, 9999),
                        ("1万〜4万9,999円", 10000, 49999), ("5万円以上", 50000, 10**9)]:
        k = sum(lo <= x <= hi for x in tri)
        print(" ", lab, k, pct(k, len(tri)))
    pops = [int(r["tri_pop"]) for r in rs if r["tri_pop"]]
    print("3連単 1〜3番人気決着", pct(sum(p <= 3 for p in pops), len(pops)), len(pops))
