"""全国ランキング:2〜6コースの1着率の場別順位。
直近1年(boat_stats.py と同じ期間・同じ計算方法 course_table)と、その前の1年(前年同期間)を比較する。"""
import os, sys
from collections import defaultdict, Counter
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct, course_table

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
prev_since = (date.fromisoformat(since) - timedelta(days=365)).isoformat()
prev_last = (date.fromisoformat(since) - timedelta(days=1)).isoformat()
print("直近1年", since, "〜", last, " 前年同期間", prev_since, "〜", prev_last)
names = {r["jcd"]: r["venue"] for r in races}

cur = [e for e in entries if since <= e["date"] <= last]
prv = [e for e in entries if prev_since <= e["date"] <= prev_last]
rc = Counter(r["jcd"] for r in races if since <= r["date"] <= last)
rp = Counter(r["jcd"] for r in races if prev_since <= r["date"] <= prev_last)
print("レース数 直近", sum(rc.values()), "前年", sum(rp.values()))


def outer(tab):
    """4〜6コースの1着数/出走数 → 1着率"""
    n = sum(t["n"] for t in tab[3:])
    w = sum(round(t["win"] * t["n"] / 100) for t in tab[3:] if t["n"])
    return pct(w, n), n


def wins_by_course(es):
    w = Counter(int(e["course"]) for e in es if e["course"] and e["finish"] == "1")
    tot = sum(w.values())
    return {c: pct(w[c], tot) for c in range(1, 7)}, tot


for lab, es in (("直近", cur), ("前年", prv)):
    t = course_table(es)
    print(f"\n全国 {lab}: " + " ".join(f"{x['course']}C {x['win']}%(n={x['n']})" for x in t))
    print(f"  4〜6コース1着率 {outer(t)}")
    sh, tot = wins_by_course(es)
    print(f"  1着艇のコース構成 (1着数{tot})", sh)
    nb1 = {c: v for c, v in sh.items() if c != 1}
    s = sum(nb1.values())
    print("  1コース以外が勝ったときの内訳%", {c: round(100 * v / s, 1) for c, v in nb1.items()})

bv_c, bv_p = defaultdict(list), defaultdict(list)
for e in cur: bv_c[e["jcd"]].append(e)
for e in prv: bv_p[e["jcd"]].append(e)
rows = []
for j in sorted(bv_c):
    a, b = course_table(bv_c[j]), course_table(bv_p[j])
    rows.append(dict(j=j, nm=names[j], a=a, b=b, ao=outer(a), bo=outer(b), rc=rc[j], rp=rp[j]))

def rank(key):
    s = sorted(rows, key=lambda r: (-key(r), r["j"]))
    return {r["j"]: i + 1 for i, r in enumerate(s)}

for c in (2, 3, 4):
    print(f"\n=== {c}コース1着率 順位(直近) | 前年 | 前年順位")
    rk_p = rank(lambda r: r["b"][c - 1]["win"])
    for i, r in enumerate(sorted(rows, key=lambda r: (-r["a"][c - 1]["win"], r["j"])), 1):
        print(f"{i:2d} {r['j']} {r['nm']} {r['a'][c-1]['win']}% (n={r['a'][c-1]['n']}) | {r['b'][c-1]['win']}% | {rk_p[r['j']]}")

print("\n=== 4〜6コース1着率 順位(直近) | 前年 | 前年順位 | 差 | 1コース1着率 | 2C 3C 5C 6C")
rk_p = rank(lambda r: r["bo"][0])
for i, r in enumerate(sorted(rows, key=lambda r: (-r["ao"][0], r["j"])), 1):
    a = r["a"]
    print(f"{i:2d} {r['j']} {r['nm']} {r['ao'][0]}% (n={r['ao'][1]}, races={r['rc']}) | {r['bo'][0]}% (races={r['rp']}) | {rk_p[r['j']]} | {r['ao'][0]-r['bo'][0]:+.1f} | C1 {a[0]['win']}% | {a[1]['win']} {a[2]['win']} {a[4]['win']} {a[5]['win']}")


def outer_share(es):
    """1着艇の進入コースが4〜6だったレースの割合(分母=1着艇のコースが記録されたレース数)"""
    w = Counter(int(e["course"]) for e in es if e["course"] and e["finish"] == "1")
    tot = sum(w.values())
    return pct(w[4] + w[5] + w[6], tot), pct(w[2] + w[3], tot), tot, {c: w[c] for c in range(1, 7)}

print("\n=== 4〜6コースが1着のレースの割合 順位(直近) | 2・3コース | 分母 | 前年 | 前年順位 | 差")
nc, np_ = outer_share(cur), outer_share(prv)
print("全国 直近", nc[:3], "前年", np_[:3])
sh_c = {r["j"]: outer_share(bv_c[r["j"]]) for r in rows}
sh_p = {r["j"]: outer_share(bv_p[r["j"]]) for r in rows}
rk_p = {j: i + 1 for i, j in enumerate(sorted(sh_p, key=lambda j: (-sh_p[j][0], j)))}
order = sorted(sh_c, key=lambda j: (-sh_c[j][0], j))
for i, j in enumerate(order, 1):
    a, b = sh_c[j], sh_p[j]
    print(f"{i:2d} {j} {names[j]} {a[0]}% | 2・3C {a[1]}% | n={a[2]} | 前年 {b[0]}% n={b[2]} | {rk_p[j]} | {a[0]-b[0]:+.1f}")
print("分母範囲 直近", min(v[2] for v in sh_c.values()), max(v[2] for v in sh_c.values()),
      "前年", min(v[2] for v in sh_p.values()), max(v[2] for v in sh_p.values()))
import statistics
c1 = {r["j"]: r["a"][0]["win"] for r in rows}
xs = [c1[j] for j in order]; ys = [sh_c[j][0] for j in order]
mx, my = statistics.mean(xs), statistics.mean(ys)
rr = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / (sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**.5
print("1コース1着率と4〜6コース1着割合の相関 r =", round(rr, 2))

print("\n=== 1着艇のコース別割合(直近、分母=1着艇のコースが記録されたレース数)")
for lab, w in (("全国直近", nc[3]), ("全国前年", np_[3])):
    t = sum(w.values()); print(lab, {c: pct(w[c], t) for c in w}, "計", t)
for i, j in enumerate(order, 1):
    w = sh_c[j][3]; t = sh_c[j][2]
    print(f"{i:2d} {names[j]} " + " ".join(f"{c}C {pct(w[c], t)}" for c in range(1, 7)) + f" | 4〜6計 {sh_c[j][0]}")
