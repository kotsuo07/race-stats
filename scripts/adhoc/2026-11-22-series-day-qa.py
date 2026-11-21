"""Q&A「初日と最終日で何が違う?」用:直近1年(boat_stats.py と同じ期間)の
開催(節)ごとの日数、開催日目別・初日/中日/最終日別の1コース1着率・万舟率・3連単中央値、
最終日のレース種別内訳、最終日の場別"""
import os, sys, statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
allr = sorted(races, key=lambda r: (r["jcd"], r["date"], int(r["rno"])))

# 開催(節)の組み立て:同じ場で、日付が1日ずつ進み開催日目も1ずつ増える日をつなげる
day_of = {}  # (jcd, date) -> day
for r in allr:
    day_of[(r["jcd"], r["date"])] = int(r["day"])
series = []  # list of list[(jcd,date,day)]
for jcd in sorted({k[0] for k in day_of}):
    ds = sorted((d, dy) for (j, d), dy in day_of.items() if j == jcd)
    cur = []
    for d, dy in ds:
        if cur:
            pd, pdy = cur[-1]
            if dy == pdy + 1 and (date.fromisoformat(d) - date.fromisoformat(pd)).days <= 2:
                cur.append((d, dy)); continue
            series.append((jcd, cur))
        cur = [(d, dy)]
    if cur:
        series.append((jcd, cur))

# 完全な節:初日が1日目、期間内に収まる、データ末尾で切れていない(最終日に優勝戦がある)
def is_yusho(t):
    """優勝戦(準優勝戦・準々優勝戦は除く)。「優勝戦進入固定」「GP優勝戦」なども含む"""
    return "優勝" in t and "準" not in t


yusho_days = {(r["jcd"], r["date"]) for r in races if is_yusho(r["race_type"])}
pos = {}  # (jcd,date) -> '初日'/'中日'/'最終日', length
complete = []
for jcd, s in series:
    if s[0][1] != 1 or s[0][0] < since:
        continue
    if (jcd, s[-1][0]) not in yusho_days:
        continue
    complete.append((jcd, s))
    L = len(s)
    for i, (d, dy) in enumerate(s):
        pos[(jcd, d)] = ("初日" if i == 0 else "最終日" if i == L - 1 else "中日", L, dy)

print("期間", since, "〜", last)
print("完全な節の数", len(complete))
lens = Counter(len(s) for _, s in complete)
print("節の日数分布", sorted(lens.items()), "中央値", statistics.median(len(s) for _, s in complete))

rs = [r for r in races if r["date"] >= since]
print("期間内レース", len(rs), "うち完全な節に属する", sum(1 for r in rs if (r["jcd"], r["date"]) in pos))
c1 = {}
for e in entries:
    if e["date"] >= since and e["course"] == "1":
        c1[(e["date"], e["jcd"], e["rno"])] = e["finish"] == "1"


def summ(sub, label):
    n = len(sub)
    w = [c1[(r["date"], r["jcd"], r["rno"])] for r in sub if (r["date"], r["jcd"], r["rno"]) in c1]
    tri = [int(r["tri_pay"]) for r in sub if r["tri_pay"]]
    pops = [int(r["tri_pop"]) for r in sub if r["tri_pop"]]
    nige = sum(1 for r in sub if r["kimarite"] == "逃げ")
    km = sum(1 for r in sub if r["kimarite"])
    print(f" {label}: レース{n} 1コース艇{len(w)} 1コース1着{pct(sum(w), len(w))}% "
          f"逃げ{pct(nige, km)}% 3連単n{len(tri)} 中央値{statistics.median(tri) if tri else None} "
          f"万舟{pct(sum(1 for x in tri if x >= 10000), len(tri))}% 1番人気{pct(sum(1 for p in pops if p == 1), len(pops))}%")


print("\n=== 初日/中日/最終日(完全な節のみ)")
for p in ["初日", "中日", "最終日"]:
    summ([r for r in rs if pos.get((r["jcd"], r["date"]), (None,))[0] == p], p)
summ([r for r in rs if (r["jcd"], r["date"]) in pos], "合計")

print("\n=== 開催日目別(期間内の全レース、day列)")
for dy in sorted({int(r["day"]) for r in rs}):
    summ([r for r in rs if int(r["day"]) == dy], f"{dy}日目")

print("\n=== 最終日のレース種別(完全な節)")
fin = [r for r in rs if pos.get((r["jcd"], r["date"]), (None,))[0] == "最終日"]
print(Counter(r["race_type"] for r in fin).most_common(12))
print("\n=== 初日のレース種別")
ini = [r for r in rs if pos.get((r["jcd"], r["date"]), (None,))[0] == "初日"]
print(Counter(r["race_type"] for r in ini).most_common(12))

print("\n=== 最終日:優勝戦以外 / 優勝戦")
summ([r for r in fin if not is_yusho(r["race_type"])], "最終日・優勝戦以外")
summ([r for r in fin if is_yusho(r["race_type"])], "最終日・優勝戦")
print("\n=== 初日:ドリーム等の特別レースを除く('予選'を含む種別のみ)")
summ([r for r in ini if "予選" in r["race_type"]], "初日・予選系")
summ([r for r in ini if "予選" not in r["race_type"]], "初日・予選以外")
print(Counter(r["race_type"] for r in ini if "予選" not in r["race_type"]).most_common(8))

print("\n=== 最終日のレース番号別(1-6R/7-11R/12R)")
for lab, lo, hi in [("1〜6R", 1, 6), ("7〜11R", 7, 11), ("12R", 12, 12)]:
    summ([r for r in fin if lo <= int(r["rno"]) <= hi], f"最終日{lab}")

print("\n=== 節の日数別:初日/最終日の1コース1着率")
for L in sorted(lens):
    if lens[L] < 30:
        continue
    for p in ["初日", "最終日"]:
        summ([r for r in rs if pos.get((r["jcd"], r["date"]), (None, 0))[:2] == (p, L)], f"{L}日間・{p}")

print("\n=== 6日間の節:開催日目別(完全な節)")
for dy in range(1, 7):
    sub = [r for r in rs if pos.get((r["jcd"], r["date"]), (None, 0, 0))[1:] == (6, dy)]
    summ(sub, f"6日間・{dy}日目")
    if dy == 5:
        jy = sum(1 for r in sub if "準優勝" in r["race_type"])
        print(f"   うち準優勝戦を含む種別 {jy} / 準優勝戦の1コース1着:")
        summ([r for r in sub if "準優勝" in r["race_type"]], "6日間・5日目・準優勝戦")
        summ([r for r in sub if "準優勝" not in r["race_type"]], "6日間・5日目・準優勝戦以外")

print("\n=== 節の日数の割合")
tot = len(complete)
for L, c in sorted(lens.items()):
    print(f" {L}日間 {c}節 {pct(c, tot)}%")
