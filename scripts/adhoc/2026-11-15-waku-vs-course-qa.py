"""Q&A「1号艇と1コースは違う?」用:直近1年(boat_stats.py と同じ期間)の
号艇(枠番)別成績、枠なり進入の割合、1号艇の進入コース別成績、場別の枠なり率"""
import os, sys
from collections import Counter, defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct
from boat_parse import JCD

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
rs = {(r["date"], r["jcd"], r["rno"]): r for r in races if r["date"] >= since}
print("期間", since, "〜", last, "レース", len(rs))
es = [e for e in entries if e["date"] >= since]
by_race = defaultdict(list)
for e in es:
    by_race[(e["date"], e["jcd"], e["rno"])].append(e)


def rate(sub, k=1):
    n = len(sub)
    w = sum(1 for e in sub if e["finish"].isdigit() and int(e["finish"]) <= k)
    return n, pct(w, n)


print("\n=== 号艇別 / コース別 1着率・2連対率・3連対率")
for b in "123456":
    sb = [e for e in es if e["boat"] == b]
    sc = [e for e in es if e["course"] == b]
    print(f" {b}号艇: n={len(sb)} 1着{rate(sb)[1]} 2連{rate(sb,2)[1]} 3連{rate(sb,3)[1]}"
          f" | {b}コース: n={len(sc)} 1着{rate(sc)[1]} 2連{rate(sc,2)[1]} 3連{rate(sc,3)[1]}")

print("\n=== 号艇ごとの進入コース分布(コース記録あり)")
for b in "123456":
    sb = [e for e in es if e["boat"] == b and e["course"]]
    c = Counter(e["course"] for e in sb)
    print(f" {b}号艇 n={len(sb)} 同じコース{pct(c[b], len(sb))}% ",
          {k: pct(v, len(sb)) for k, v in sorted(c.items())})

print("\n=== 枠なり(全艇が号艇=コース)の割合")
full = [k for k, v in by_race.items() if k in rs and len(v) == 6 and all(e["course"] for e in v)]
wn = [k for k in full if all(e["course"] == e["boat"] for e in by_race[k])]
print(f" 6艇そろい・コース記録ありレース {len(full)} 枠なり {len(wn)} ({pct(len(wn), len(full))}%)")
c1b1 = [k for k in full if any(e["boat"] == "1" and e["course"] == "1" for e in by_race[k])]
print(f" 1号艇が1コース {len(c1b1)} ({pct(len(c1b1), len(full))}%)")

print("\n=== 1号艇の進入コース別 1着率")
b1 = [e for e in es if e["boat"] == "1" and e["course"]]
for c in "123456":
    s = [e for e in b1 if e["course"] == c]
    if s:
        print(f" 1号艇が{c}コース: n={len(s)} 1着{rate(s)[1]} 3連{rate(s,3)[1]}")
s = [e for e in b1 if e["course"] != "1"]
print(f" 1号艇が2コース以遠(計): n={len(s)} 1着{rate(s)[1]} 3連{rate(s,3)[1]}")

print("\n=== 1コースに入った艇の号艇別 1着率")
c1 = [e for e in es if e["course"] == "1"]
for b in "123456":
    s = [e for e in c1 if e["boat"] == b]
    print(f" {b}号艇が1コース: n={len(s)} ({pct(len(s), len(c1))}%) 1着{rate(s)[1]}")
s = [e for e in c1 if e["boat"] != "1"]
print(f" 2〜6号艇が1コース(計): n={len(s)} 1着{rate(s)[1]}")

print("\n=== 枠なり/非枠なり レースの1コース1着率と3連単")
import statistics
for lab, keys in [("枠なり", set(wn)), ("枠なり以外", set(full) - set(wn))]:
    c1w = [e for k in keys for e in by_race[k] if e["course"] == "1"]
    pays = [int(float(rs[k]["tri_pay"])) for k in keys if rs[k]["tri_pay"]]
    m = sum(x >= 10000 for x in pays)
    print(f" {lab}: レース{len(keys)} 1コース1着{rate(c1w)[1]} 3連単中央値{round(statistics.median(pays))}"
          f" 万舟{pct(m, len(pays))}% (n={len(pays)})")

print("\n=== 場別 枠なり率 / 1号艇の1コース率")
vs = defaultdict(lambda: [0, 0, 0])
for k in full:
    vs[k[1]][0] += 1
for k in wn:
    vs[k[1]][1] += 1
for k in c1b1:
    vs[k[1]][2] += 1
rows = sorted(((pct(v[1], v[0]), j, v) for j, v in vs.items()), reverse=True)
for p, j, v in rows:
    print(f" {j} {JCD.get(j, j)}: n={v[0]} 枠なり{p}% 1号艇1コース{pct(v[2], v[0])}%")
