"""風速別(1m刻み)のコース別1着率・決まり手・万舟率・3連単中央値・平均ST(直近1年、全国)"""
import os, sys, statistics
from collections import Counter, defaultdict
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

BINS = [("0m", 0, 0), ("1m", 1, 1), ("2m", 2, 2), ("3m", 3, 3), ("4m", 4, 4),
        ("5m", 5, 5), ("6m", 6, 6), ("7m以上", 7, 99)]


def wind(r):
    return int(float(r["wind_m"])) if r["wind_m"] != "" else None


def stats(rs):
    n, w = Counter(), Counter()
    st = defaultdict(list)
    for r in rs:
        for e in by_race.get((r["date"], r["jcd"], r["rno"]), []):
            if e["course"] in ("1", "2", "3", "4", "5", "6"):
                c = int(e["course"])
                n[c] += 1
                w[c] += e["finish"] == "1"
                # ST はフライング・出遅れ(L)・空欄を除く(2026-11-17 の記事と同じ定義)
                if e["flying"] == "0" and e["st"] not in ("", None) and not e["finish"].startswith("L"):
                    st[c].append(float(e["st"]))
    tri = [int(float(r["tri_pay"])) for r in rs if r["tri_pay"]]
    k = [r["kimarite"] for r in rs if r["kimarite"]]
    kc = Counter(k)
    return {
        "races": len(rs),
        "win": {c: pct(w[c], n[c]) for c in range(1, 7)},
        "c1_n": n[1],
        "outer456": pct(w[4] + w[5] + w[6], len(rs)),
        "kimarite": {x: pct(kc[x], len(k)) for x in ["逃げ", "差し", "まくり", "まくり差し", "抜き", "恵まれ"]},
        "k_n": len(k),
        "manshu": pct(sum(x >= 10000 for x in tri), len(tri)), "tri_n": len(tri),
        "tri_median": round(statistics.median(tri)) if tri else None,
        "st_c1": round(statistics.mean(st[1]), 3) if st[1] else None,
        "fly_races": sum(1 for r in rs if any(e["flying"] == "1" for e in by_race.get((r["date"], r["jcd"], r["rno"]), []))),
        "st_all": round(statistics.mean([x for c in st for x in st[c]]), 3) if st else None,
    }


print(f"期間 {since}〜{last} 全{len(races)}レース 風速欠損 {sum(1 for r in races if r['wind_m'] == '')}")
print("[風速の分布]")
dist = Counter(wind(r) for r in races)
for k in sorted(x for x in dist if x is not None):
    print(k, dist[k], pct(dist[k], len(races)))
print("平均風速", round(statistics.mean(wind(r) for r in races if wind(r) is not None), 2))
print("[風速別 1m刻み]")
for label, lo, hi in BINS:
    rs = [r for r in races if wind(r) is not None and lo <= wind(r) <= hi]
    print(label, stats(rs))
print("[風速0〜2m / 3〜4m / 5m以上]")
for label, lo, hi in [("0〜2m", 0, 2), ("3〜4m", 3, 4), ("5m以上", 5, 99)]:
    rs = [r for r in races if wind(r) is not None and lo <= wind(r) <= hi]
    print(label, stats(rs))
print("[無風表記のレース]", stats([r for r in races if r["wind_dir"] == "無風"]))
print("[風速5m以上のレースの割合 場別 上位5・下位3]")
vt, vc = Counter(), Counter()
for r in races:
    if wind(r) is not None:
        vt[r["venue"]] += 1
        vc[r["venue"]] += wind(r) >= 5
rank = sorted(vt, key=lambda v: -vc[v] / vt[v])
for v in rank[:5] + rank[-3:]:
    print(v, pct(vc[v], vt[v]), vc[v], vt[v])
print("[江戸川を除く 0〜2m / 5m以上]")
ex = [r for r in races if r["venue"] != "江戸川"]
for label, lo, hi in [("0〜2m", 0, 2), ("3〜4m", 3, 4), ("5m以上", 5, 99)]:
    rs = [r for r in ex if wind(r) is not None and lo <= wind(r) <= hi]
    s = stats(rs)
    print(label, s["races"], s["win"][1], s["manshu"], s["kimarite"]["まくり"])
