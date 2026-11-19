"""住之江(12)と尼崎(13)の比較:直近1年のコース別成績、決まり手、風速・波高、風速別1コース1着率、
レース番号帯別1コース1着率、進入・ST、1コース以外の勝者コース、3連単の配当帯と人気決着"""
import os, sys, statistics
from collections import defaultdict, Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

JCDS = ("12", "13")
races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
print(f"期間 {since}〜{last}")
by_race = defaultdict(list)
for e in entries:
    if e["date"] >= since and e["jcd"] in JCDS:
        by_race[(e["date"], e["jcd"], e["rno"])].append(e)


def ents(r):
    return by_race.get((r["date"], r["jcd"], r["rno"]), [])


def c1_win(rs):
    n = w = 0
    for r in rs:
        for e in ents(r):
            if e["course"] == "1":
                n += 1
                w += e["finish"] == "1"
    return pct(w, n), n


for jcd in JCDS:
    rs = [r for r in races if r["date"] >= since and r["jcd"] == jcd]
    print(f"\n==== {rs[0]['venue']} {len(rs)}レース  開催日数 {len({r['date'] for r in rs})}")
    es = [e for r in rs for e in ents(r)]
    print("コース別 1着率/2連対率/3連対率 (件数)")
    for c in "123456":
        ce = [e for e in es if e["course"] == c]
        n = len(ce)
        print(" ", c, pct(sum(e["finish"] == "1" for e in ce), n),
              pct(sum(e["finish"] in ("1", "2") for e in ce), n),
              pct(sum(e["finish"] in ("1", "2", "3") for e in ce), n), n)
    km = Counter(r["kimarite"] for r in rs if r["kimarite"])
    tk = sum(km.values())
    print("決まり手", tk, {k: pct(v, tk) for k, v in km.most_common()})
    winds = [float(r["wind_m"]) for r in rs if r["wind_m"]]
    waves = [float(r["wave_cm"]) for r in rs if r["wave_cm"]]
    print("風速 平均", round(statistics.mean(winds), 2), "件数", len(winds),
          "5m以上", pct(sum(w >= 5 for w in winds), len(winds)))
    print("波高 平均", round(statistics.mean(waves), 2), "件数", len(waves),
          "値の種類", sorted(Counter(waves).items())[:12])
    for lab, lo, hi in [("0〜2m", 0, 2), ("3〜4m", 3, 4), ("5m以上", 5, 999)]:
        sub = [r for r in rs if r["wind_m"] and lo <= float(r["wind_m"]) <= hi]
        print(f"  風速{lab}: {len(sub)}レース 1コース1着率", c1_win(sub))
    for lab, lo, hi in [("1〜4R", 1, 4), ("5〜8R", 5, 8), ("9〜12R", 9, 12)]:
        sub = [r for r in rs if lo <= int(r["rno"]) <= hi]
        print(f"  {lab}: {len(sub)}レース 1コース1着率", c1_win(sub))
    print("全体 1コース1着率", c1_win(rs))
    b1 = [e for e in es if e["boat"] == "1" and e["course"]]
    print("1号艇の1コース進入率", pct(sum(e["course"] == "1" for e in b1), len(b1)), len(b1))
    full = nr = 0
    for r in rs:
        ee = ents(r)
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
        w = [e for e in ents(r) if e["finish"] == "1"]
        if w and w[0]["course"] and w[0]["course"] != "1":
            lose[w[0]["course"]] += 1
    tot = sum(lose.values())
    print("1コース以外が勝ったレース", tot, pct(tot, len(rs)), {c: (lose[c], pct(lose[c], tot)) for c in "23456"})
    tri = [int(r["tri_pay"]) for r in rs if r["tri_pay"]]
    print("3連単 件数", len(tri), "中央値", statistics.median(tri), "平均", round(statistics.mean(tri)),
          "最高", max(tri), "万舟", pct(sum(x >= 10000 for x in tri), len(tri)))
    for lab, lo, hi in [("1,000円未満", 0, 999), ("1,000〜2,999円", 1000, 2999), ("3,000〜9,999円", 3000, 9999),
                        ("1万〜4万9,999円", 10000, 49999), ("5万円以上", 50000, 10**9)]:
        k = sum(lo <= x <= hi for x in tri)
        print(" ", lab, k, pct(k, len(tri)))
    pops = [int(r["tri_pop"]) for r in rs if r["tri_pop"]]
    print("3連単 1番人気決着", pct(sum(p == 1 for p in pops), len(pops)),
          "1〜3番人気決着", pct(sum(p <= 3 for p in pops), len(pops)), len(pops))
    allr = [r for r in races if r["jcd"] == jcd]
    print("全期間", allr and min(r["date"] for r in allr), "1コース1着率(全期間)は boat_stats --venue を参照")

# 参考:全国のレース番号帯別1コース1着率(直近1年)
c1 = {}
for e in entries:
    if e["date"] >= since and e["course"] == "1":
        c1[(e["date"], e["jcd"], e["rno"])] = e["finish"] == "1"
print("\n全国 レース番号帯別 1コース1着率")
for lab, lo, hi in [("1〜4R", 1, 4), ("5〜8R", 5, 8), ("9〜12R", 9, 12)]:
    v = [w for k, w in c1.items() if lo <= int(k[2]) <= hi]
    print(f"  {lab}: {pct(sum(v), len(v))} n={len(v)}")
