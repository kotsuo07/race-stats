"""桐生(01)の場別データ:直近1年の進入・ST・1コース敗戦時の勝者コース・レース番号別・
月別の風速5m以上の割合・風向別1コース1着率・配当帯・全国との比較"""
import os, sys, statistics
from collections import defaultdict, Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

JCD = "01"
races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
print(f"期間 {since}〜{last}")
rs = [r for r in races if r["date"] >= since and r["jcd"] == JCD]
allrs = [r for r in races if r["date"] >= since]
by_race = defaultdict(list)
for e in entries:
    if e["date"] >= since:
        by_race[(e["date"], e["jcd"], e["rno"])].append(e)
key = lambda r: (r["date"], r["jcd"], r["rno"])
print(rs[0]["venue"], len(rs), "レース / 全国", len(allrs))

def c1win(rr):
    n = w = 0
    for r in rr:
        ee = by_race.get(key(r), [])
        c1 = [e for e in ee if e["course"] == "1"]
        if c1:
            n += 1; w += c1[0]["finish"] == "1"
    return pct(w, n), n

for lab, rr in (("桐生", rs), ("全国", allrs)):
    es = [e for r in rr for e in by_race.get(key(r), [])]
    b1 = [e for e in es if e["boat"] == "1" and e["course"]]
    print(f"\n[{lab}] 1号艇の1コース進入率", pct(sum(e["course"] == "1" for e in b1), len(b1)), len(b1))
    full = nr = 0
    for r in rr:
        ee = by_race.get(key(r), [])
        if len(ee) == 6 and all(e["course"] for e in ee):
            nr += 1; full += all(e["boat"] == e["course"] for e in ee)
    print(f"[{lab}] 枠なり率", pct(full, nr), nr)
    print(f"[{lab}] コース別平均ST(フライング除く)")
    for c in "123456":
        st = [float(e["st"]) for e in es if e["course"] == c and e["st"] and e["flying"] == "0"
              and e["st"].replace(".", "").isdigit()]
        print("  ", c, round(statistics.mean(st), 3) if st else None, len(st))
    lose = Counter()
    for r in rr:
        w = [e for e in by_race.get(key(r), []) if e["finish"] == "1"]
        if w and w[0]["course"] and w[0]["course"] != "1":
            lose[w[0]["course"]] += 1
    tot = sum(lose.values())
    print(f"[{lab}] 1コース以外が勝ったレース", tot, {c: (lose[c], pct(lose[c], tot)) for c in "23456"})
    tri = [int(r["tri_pay"]) for r in rr if r["tri_pay"]]
    print(f"[{lab}] 3連単配当帯 件数", len(tri))
    for l, lo, hi in [("1,000円未満", 0, 999), ("1,000〜2,999円", 1000, 2999), ("3,000〜9,999円", 3000, 9999),
                      ("1万〜4万9,999円", 10000, 49999), ("5万円以上", 50000, 10**9)]:
        k = sum(lo <= x <= hi for x in tri)
        print("  ", l, k, pct(k, len(tri)))
    print(f"[{lab}] 風速5m以上の割合", pct(sum(1 for r in rr if r["wind_m"] and float(r["wind_m"]) >= 5), len(rr)))

print("\n[桐生] レース番号帯別 1コース1着率")
for l, lo, hi in [("1〜4R", 1, 4), ("5〜8R", 5, 8), ("9〜12R", 9, 12)]:
    print("  ", l, c1win([r for r in rs if lo <= int(r["rno"]) <= hi]))
print("[桐生] レース種別 件数上位と1コース1着率")
for t, k in Counter(r["race_type"] for r in rs).most_common(8):
    print("  ", t, k, c1win([r for r in rs if r["race_type"] == t]))
print("[桐生] 月別 風速5m以上の割合(レース数)")
mon = defaultdict(list)
for r in rs: mon[r["date"][:7]].append(r)
for m in sorted(mon):
    rr = mon[m]
    print("  ", m, pct(sum(1 for r in rr if r["wind_m"] and float(r["wind_m"]) >= 5), len(rr)), len(rr))
print("[桐生] 風向別 件数と1コース1着率(上位)")
for d, k in Counter(r["wind_dir"] for r in rs).most_common(10):
    print("  ", d, k, c1win([r for r in rs if r["wind_dir"] == d]))
print("[桐生] 季節別 1コース1着率")
for l, ms in [("冬(12〜2月)", ("12", "01", "02")), ("春(3〜5月)", ("03", "04", "05")),
              ("夏(6〜8月)", ("06", "07", "08")), ("秋(9〜11月)", ("09", "10", "11"))]:
    print("  ", l, c1win([r for r in rs if r["date"][5:7] in ms]))
print("\n[確認] 桐生全体 1コース1着率", c1win(rs))
print("[全国] レース番号帯別 1コース1着率")
for l, lo, hi in [("1〜4R", 1, 4), ("5〜8R", 5, 8), ("9〜12R", 9, 12)]:
    print("  ", l, c1win([r for r in allrs if lo <= int(r["rno"]) <= hi]))
print("[桐生] 1〜4R の3連単万舟率・中央値")
for l, lo, hi in [("1〜4R", 1, 4), ("5〜8R", 5, 8), ("9〜12R", 9, 12)]:
    tri = [int(r["tri_pay"]) for r in rs if r["tri_pay"] and lo <= int(r["rno"]) <= hi]
    print("  ", l, len(tri), "万舟率", pct(sum(x >= 10000 for x in tri), len(tri)), "中央値", statistics.median(tri))
