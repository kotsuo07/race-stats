"""季節(月)別の1コース1着率・万舟率・3連単中央値・風速など(2024年11月〜2026年10月の2年間、全国・場別)"""
import os, sys, statistics
from collections import defaultdict, Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

SINCE, UNTIL = "2024-11-01", "2026-10-31"
races = [r for r in load("races") if SINCE <= r["date"] <= UNTIL]
keys = {(r["date"], r["jcd"], r["rno"]) for r in races}
c1 = {}
for e in load("entries"):
    k = (e["date"], e["jcd"], e["rno"])
    if k in keys and e["course"] == "1":
        c1[k] = e["finish"] == "1"

SEASON = {12: "冬", 1: "冬", 2: "冬", 3: "春", 4: "春", 5: "春", 6: "夏", 7: "夏", 8: "夏", 9: "秋", 10: "秋", 11: "秋"}


def stats(rs):
    ks = [(r["date"], r["jcd"], r["rno"]) for r in rs]
    w = [c1[k] for k in ks if k in c1]
    tri = [int(float(r["tri_pay"])) for r in rs if r["tri_pay"]]
    km = [r["kimarite"] for r in rs if r["kimarite"]]
    wind = [int(float(r["wind_m"])) for r in rs if r["wind_m"] != ""]
    wave = [int(float(r["wave_cm"])) for r in rs if r["wave_cm"] != ""]
    return {"races": len(rs), "c1_n": len(w), "c1_win": pct(sum(w), len(w)),
            "manshu": pct(sum(x >= 10000 for x in tri), len(tri)),
            "tri_median": round(statistics.median(tri)) if tri else None,
            "nige": pct(km.count("逃げ"), len(km)), "makuri": pct(km.count("まくり"), len(km)),
            "sashi": pct(km.count("差し"), len(km)), "makurizashi": pct(km.count("まくり差し"), len(km)),
            "wind_mean": round(statistics.mean(wind), 2) if wind else None,
            "wind5_pct": pct(sum(x >= 5 for x in wind), len(wind)),
            "wave_mean": round(statistics.mean(wave), 2) if wave else None,
            "rain_pct": pct(sum(r["weather"] == "雨" for r in rs), len(rs))}


print(f"期間 {SINCE}〜{UNTIL} 全{len(races)}レース")
print("[全体]", stats(races))
bym = defaultdict(list)
for r in races:
    bym[int(r["date"][5:7])].append(r)
print("[月別(2年分を合算)]")
for m in range(1, 13):
    print(m, "月", stats(bym[m]))
bys = defaultdict(list)
for r in races:
    bys[SEASON[int(r["date"][5:7])]].append(r)
print("[季節別] 春=3〜5月 夏=6〜8月 秋=9〜11月 冬=12〜2月")
for s in "春夏秋冬":
    print(s, stats(bys[s]))
print("[季節別・年度別(11月始まりの1年ごと)]")
for lo, hi in [("2024-11-01", "2025-10-31"), ("2025-11-01", "2026-10-31")]:
    for s in "春夏秋冬":
        rs = [r for r in bys[s] if lo <= r["date"] <= hi]
        st = stats(rs)
        print(lo[:7], "〜", hi[:7], s, st["races"], st["c1_win"], st["manshu"], st["tri_median"], st["wind_mean"])
print("[夏の1コース1着率が高い月] 風速別×季節")
for s in "春夏秋冬":
    for lo, hi, lab in [(0, 2, "0〜2m"), (3, 4, "3〜4m"), (5, 99, "5m以上")]:
        rs = [r for r in bys[s] if r["wind_m"] != "" and lo <= int(float(r["wind_m"])) <= hi]
        st = stats(rs)
        print(s, lab, st["races"], st["c1_win"], st["manshu"])
print("[場別 季節別1コース1着率] 夏-冬の差でソート")
venues = sorted({(r["jcd"], r["venue"]) for r in races})
rows = []
for jcd, v in venues:
    d = {s: stats([r for r in bys[s] if r["jcd"] == jcd]) for s in "春夏秋冬"}
    rows.append((jcd, v, d))
rows.sort(key=lambda x: x[2]["夏"]["c1_win"] - x[2]["冬"]["c1_win"], reverse=True)
for jcd, v, d in rows:
    print(jcd, v, " ".join(f"{s}:{d[s]['c1_win']}%(n={d[s]['c1_n']},風{d[s]['wind_mean']}m,5m+{d[s]['wind5_pct']}%)" for s in "春夏秋冬"),
          "夏-冬", round(d["夏"]["c1_win"] - d["冬"]["c1_win"], 1))
print("[注目場の夏・冬 年度別]")
for jcd in ["08", "15", "14", "12", "24"]:
    for lo, hi in [("2024-11-01", "2025-10-31"), ("2025-11-01", "2026-10-31")]:
        out = []
        for s in "夏冬":
            st = stats([r for r in bys[s] if r["jcd"] == jcd and lo <= r["date"] <= hi])
            out.append(f"{s}:{st['c1_win']}%(n={st['c1_n']})")
        print(jcd, lo[:7], " ".join(out))
