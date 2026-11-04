"""波高・天候別の1コース1着率・万舟率・3連単中央値・逃げ率(直近1年、全国)"""
import os, sys, statistics
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
races = [r for r in races if r["date"] >= since]
by_race = defaultdict(list)
for e in entries:
    if e["date"] >= since:
        by_race[(e["date"], e["jcd"], e["rno"])].append(e)


def stats(rs):
    n = w = 0
    for r in rs:
        for e in by_race.get((r["date"], r["jcd"], r["rno"]), []):
            if e["course"] == "1":
                n += 1
                w += e["finish"] == "1"
    tri = [int(float(r["tri_pay"])) for r in rs if r["tri_pay"]]
    k = [r["kimarite"] for r in rs if r["kimarite"]]
    return {"races": len(rs), "c1_n": n, "c1_win": pct(w, n),
            "manshu": pct(sum(x >= 10000 for x in tri), len(tri)), "tri_n": len(tri),
            "tri_median": round(statistics.median(tri)) if tri else None,
            "nige": pct(sum(x == "逃げ" for x in k), len(k))}


print(f"期間 {since}〜{last} 全{len(races)}レース")
print("[波高別]")
for label, lo, hi in [("0〜2cm", 0, 2), ("3〜4cm", 3, 4), ("5〜9cm", 5, 9), ("10cm以上", 10, 999)]:
    rs = [r for r in races if r["wave_cm"] != "" and lo <= int(float(r["wave_cm"])) <= hi]
    print(label, stats(rs))
print("波高欠損", sum(1 for r in races if r["wave_cm"] == ""))
print("[天候別]")
from collections import Counter
for wx, c in Counter(r["weather"] for r in races).most_common():
    print(wx or "(空)", stats([r for r in races if r["weather"] == wx]))
print("[風速5m以上×波高]")
for label, lo, hi in [("0〜4cm", 0, 4), ("5cm以上", 5, 999)]:
    rs = [r for r in races if r["wind_m"] and int(float(r["wind_m"])) >= 5 and r["wave_cm"] != "" and lo <= int(float(r["wave_cm"])) <= hi]
    print(label, stats(rs))
print("[波高5cm以上が多い場 上位5 (割合, 件数)]")
vc, vt = Counter(), Counter()
for r in races:
    if r["wave_cm"] != "":
        vt[r["venue"]] += 1
        vc[r["venue"]] += int(float(r["wave_cm"])) >= 5
rank = sorted(vt, key=lambda v: -vc[v] / vt[v])
for v in rank[:5] + ["..."] + rank[-3:]:
    if v == "...":
        print("..."); continue
    print(v, pct(vc[v], vt[v]), vc[v], vt[v])
print("[江戸川の波高内訳]", Counter(r["wave_cm"] for r in races if r["venue"] == "江戸川"))
print("[江戸川を除く波高別]")
ex = [r for r in races if r["venue"] != "江戸川"]
print("対象", len(ex))
for label, lo, hi in [("0〜2cm", 0, 2), ("3〜4cm", 3, 4), ("5cm以上", 5, 999)]:
    rs = [r for r in ex if lo <= int(float(r["wave_cm"])) <= hi]
    print(label, stats(rs))
print("[江戸川の波高別]")
ed = [r for r in races if r["venue"] == "江戸川"]
for label, lo, hi in [("5cm", 5, 5), ("10cm以上", 10, 999)]:
    print(label, stats([r for r in ed if lo <= int(float(r["wave_cm"])) <= hi]))
print("[江戸川を除く 風速0〜4m に限った波高別]")
for label, lo, hi in [("0〜2cm", 0, 2), ("3〜4cm", 3, 4), ("5cm以上", 5, 999)]:
    rs = [r for r in ex if int(float(r["wind_m"] or 0)) <= 4 and r["wind_m"] != "" and lo <= int(float(r["wave_cm"])) <= hi]
    print(label, stats(rs))
