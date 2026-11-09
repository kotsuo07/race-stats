"""解説「決まり手」用:直近1年(boat_stats.py と同じ期間)の決まり手の件数・割合、
決まり手ごとの1着艇の進入コース、3連単配当(中央値・万舟率)、1着艇のST、場別の逃げ率の上位・下位"""
import os, sys, statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

KIM = ["逃げ", "差し", "まくり", "まくり差し", "抜き", "恵まれ"]
races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
rs = [r for r in races if r["date"] >= since]
print("期間", since, "〜", last, "レース", len(rs))
kr = [r for r in rs if r["kimarite"]]
print("決まり手ありレース", len(kr))
c = Counter(r["kimarite"] for r in kr)
print("\n=== 決まり手 件数・割合")
for k in KIM:
    print(f" {k}: {c[k]} ({pct(c[k], len(kr))}%)")
others = {k: v for k, v in c.items() if k not in KIM}
print(" その他", others)

# 1着艇
win = {}
for e in entries:
    if e["date"] >= since and e["finish"] == "1":
        win[(e["date"], e["jcd"], e["rno"])] = e
def key(r):
    return (r["date"], r["jcd"], r["rno"])

print("\n=== 決まり手ごとの1着艇の進入コース(件数, 割合)")
for k in KIM:
    sub = [win[key(r)] for r in kr if r["kimarite"] == k and key(r) in win and win[key(r)]["course"]]
    cc = Counter(int(float(w["course"])) for w in sub)
    print(f" {k} n={len(sub)}: " + ", ".join(f"{i}C {cc[i]}({pct(cc[i], len(sub))}%)" for i in range(1, 7)))

print("\n=== 1着艇のコース別 決まり手内訳")
byc = defaultdict(Counter)
for r in kr:
    w = win.get(key(r))
    if w and w["course"]:
        byc[int(float(w["course"]))][r["kimarite"]] += 1
for i in range(1, 7):
    n = sum(byc[i].values())
    print(f" {i}コース n={n}: " + ", ".join(f"{k} {byc[i][k]}({pct(byc[i][k], n)}%)" for k in KIM if byc[i][k]))

print("\n=== 決まり手別 3連単配当")
for k in KIM:
    p = [int(float(r["tri_pay"])) for r in kr if r["kimarite"] == k and r["tri_pay"]]
    m = sum(x >= 10000 for x in p)
    print(f" {k}: n={len(p)} 中央値{round(statistics.median(p))} 万舟{m}({pct(m, len(p))}%)")

print("\n=== 決まり手別 1着艇の平均ST(フライング等除く、数値のみ)")
for k in KIM:
    st = [float(win[key(r)]["st"]) for r in kr if r["kimarite"] == k and key(r) in win
          and win[key(r)]["st"] not in ("", None) and float(win[key(r)]["st"]) >= 0]
    print(f" {k}: n={len(st)} 平均{statistics.mean(st):.3f}")

print("\n=== 場別 逃げ率(決まり手ありレース)")
v = defaultdict(Counter)
for r in kr:
    v[r["venue"]][r["kimarite"]] += 1
rows = sorted(((pct(cn["逃げ"], sum(cn.values())), name, sum(cn.values()),
                pct(cn["まくり"], sum(cn.values())), pct(cn["差し"], sum(cn.values()))) for name, cn in v.items()), reverse=True)
for x in rows:
    print(f" {x[1]}: 逃げ{x[0]}% まくり{x[3]}% 差し{x[4]}% n={x[2]}")
