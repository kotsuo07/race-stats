"""戸田(02)の場別データ:直近1年のレース番号帯別・季節別・1コースST帯別の1コース1着率、
コース別の決まり手、1コース敗戦時の勝者コース、3連単の頻出組み合わせ、レース種別、全国との比較"""
import os, sys, statistics
from collections import defaultdict, Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

JCD = "02"
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


def c1(r):
    ee = [e for e in by_race.get(key(r), []) if e["course"] == "1"]
    return ee[0] if ee else None


def c1win(rr):
    n = w = 0
    for r in rr:
        e = c1(r)
        if e:
            n += 1; w += e["finish"] == "1"
    return pct(w, n), n


def winner(r):
    w = [e for e in by_race.get(key(r), []) if e["finish"] == "1"]
    return w[0] if w else None


def isst(e):
    return e["st"] and e["flying"] == "0" and e["st"].replace(".", "").isdigit()


for lab, rr in (("戸田", rs), ("全国", allrs)):
    print(f"\n===== {lab} =====")
    print("1コース1着率", c1win(rr))
    print("レース番号帯別 1コース1着率 / 万舟率 / 3連単中央値")
    for l, lo, hi in [("1〜4R", 1, 4), ("5〜8R", 5, 8), ("9〜12R", 9, 12)]:
        sub = [r for r in rr if lo <= int(r["rno"]) <= hi]
        tri = [int(r["tri_pay"]) for r in sub if r["tri_pay"]]
        print("  ", l, c1win(sub), "万舟", pct(sum(x >= 10000 for x in tri), len(tri)), "中央値", statistics.median(tri), len(tri))
    print("季節別 1コース1着率")
    for l, ms in [("冬(12〜2月)", ("12", "01", "02")), ("春(3〜5月)", ("03", "04", "05")),
                  ("夏(6〜8月)", ("06", "07", "08")), ("秋(9〜11月)", ("09", "10", "11"))]:
        print("  ", l, c1win([r for r in rr if r["date"][5:7] in ms]))
    print("1コースのST帯別 1コース1着率(フライング除く)")
    bands = [("0.10未満", 0, 0.0999), ("0.10〜0.14", 0.10, 0.1499), ("0.15〜0.19", 0.15, 0.1999), ("0.20以上", 0.20, 9)]
    for l, lo, hi in bands:
        n = w = 0
        for r in rr:
            e = c1(r)
            if e and isst(e) and lo <= float(e["st"]) <= hi:
                n += 1; w += e["finish"] == "1"
        print("  ", l, pct(w, n), n)
    print("勝者コース別 決まり手の内訳")
    km = defaultdict(Counter)
    for r in rr:
        w = winner(r)
        if w and w["course"] and r["kimarite"]:
            km[w["course"]][r["kimarite"]] += 1
    for c in "1234":
        t = sum(km[c].values())
        print("  ", c, t, {k: (v, pct(v, t)) for k, v in km[c].most_common(4)})
    lose = Counter()
    for r in rr:
        w = winner(r)
        if w and w["course"] and w["course"] != "1":
            lose[w["course"]] += 1
    tot = sum(lose.values())
    print("1コース以外の勝利", tot, {c: (lose[c], pct(lose[c], tot)) for c in "23456"})
    tri = [r for r in rr if r["tri_combo"] and r["tri_pay"]]
    print("3連単 組み合わせ上位(件数, 割合)", len(tri))
    for combo, k in Counter(r["tri_combo"] for r in tri).most_common(8):
        print("  ", combo, k, pct(k, len(tri)))
    ex = [r for r in rr if r["ex_combo"]]
    print("2連単 上位", len(ex), [(c, k, pct(k, len(ex))) for c, k in Counter(r["ex_combo"] for r in ex).most_common(6)])
    print("1着艇番の分布", Counter(r["win_combo"] for r in rr if r["win_combo"]).most_common(6))

print("\n[戸田] レース種別 件数上位と1コース1着率・万舟率")
for t, k in Counter(r["race_type"] for r in rs).most_common(10):
    sub = [r for r in rs if r["race_type"] == t]
    tri = [int(r["tri_pay"]) for r in sub if r["tri_pay"]]
    print("  ", t, k, c1win(sub), "万舟", pct(sum(x >= 10000 for x in tri), len(tri)))
print("[戸田] 準優勝戦+優勝戦", c1win([r for r in rs if r["race_type"] in ("準優勝戦", "優勝戦")]))
print("[戸田] 風速5m以上の割合", pct(sum(1 for r in rs if r["wind_m"] and float(r["wind_m"]) >= 5), len(rs)))
print("[戸田] 1号艇1着率(艇番)", pct(sum(r["win_combo"] == "1" for r in rs), sum(1 for r in rs if r["win_combo"])))
print("[戸田] 開催日数", len({r['date'] for r in rs}))
