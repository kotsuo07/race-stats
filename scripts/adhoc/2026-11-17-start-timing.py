"""解説「スタートタイミング(ST)」用:直近1年(boat_stats.py と同じ期間)の
STの分布、コース別平均ST、ST帯別の1着率、レース最速STの艇の1着率、1コースのST順位別1着率、フライング件数"""
import os, sys, statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from boat_stats import load, pct

races, entries = load("races"), load("entries")
last = max(r["date"] for r in races)
since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
rs = [r for r in races if r["date"] >= since]
es = [e for e in entries if e["date"] >= since]
print("期間", since, "〜", last, "レース", len(rs), "出走エントリー", len(es))

def valid(e):
    return e["flying"] == "0" and e["st"] not in ("", None) and not e["finish"].startswith("L") and e["course"]

ok = [e for e in es if valid(e)]
st = [float(e["st"]) for e in ok]
print("\n=== ST分布(フライング・出遅れ・欠場除く) n=", len(st))
print(f" 平均{statistics.mean(st):.3f} 中央値{statistics.median(st):.2f}")
q = statistics.quantiles(st, n=10)
print(" 10%点", round(q[0], 2), "90%点", round(q[-1], 2))

BANDS = [(0, 0.10, "0.00〜0.09"), (0.10, 0.15, "0.10〜0.14"), (0.15, 0.20, "0.15〜0.19"), (0.20, 0.25, "0.20〜0.24"), (0.25, 9, "0.25以上")]
def band(x):
    for lo, hi, lab in BANDS:
        if lo <= x + 1e-9 < hi:
            return lab
print("\n=== ST帯の構成比")
bc = Counter(band(x) for x in st)
for _, _, lab in BANDS:
    print(f" {lab}: {bc[lab]} ({pct(bc[lab], len(st))}%)")

print("\n=== コース別 平均ST・中央値 (n)")
byc = defaultdict(list)
for e in ok:
    byc[int(float(e["course"]))].append(float(e["st"]))
for c in range(1, 7):
    v = byc[c]
    print(f" {c}コース 平均{statistics.mean(v):.3f} 中央値{statistics.median(v):.2f} n={len(v)}")

print("\n=== ST帯別 1着率(全コース / 1コース / 4コース)")
for target in (None, 1, 4):
    w, n = Counter(), Counter()
    for e in ok:
        if target and int(float(e["course"])) != target:
            continue
        b = band(float(e["st"]))
        n[b] += 1
        w[b] += e["finish"] == "1"
    lab = "全コース" if target is None else f"{target}コース"
    print(" " + lab + ": " + ", ".join(f"{l} {pct(w[l], n[l])}%(n={n[l]})" for _, _, l in BANDS))

# レースごと
byr = defaultdict(list)
for e in es:
    byr[(e["date"], e["jcd"], e["rno"])].append(e)

print("\n=== レース最速ST(単独)の艇の1着率、最速艇のコース内訳")
n_r = w_r = 0
fc, fw = Counter(), Counter()
for k, v in byr.items():
    vv = [e for e in v if valid(e)]
    if len(vv) < 6 or any(e["flying"] == "1" for e in v):
        continue
    m = min(float(e["st"]) for e in vv)
    top = [e for e in vv if abs(float(e["st"]) - m) < 1e-9]
    if len(top) != 1:
        continue
    t = top[0]
    c = int(float(t["course"]))
    n_r += 1; w_r += t["finish"] == "1"
    fc[c] += 1; fw[c] += t["finish"] == "1"
print(f" 対象レース{n_r} 最速艇の1着率 {pct(w_r, n_r)}%")
for c in range(1, 7):
    print(f"  最速が{c}コース: {fc[c]}レース({pct(fc[c], n_r)}%) その艇の1着率 {pct(fw[c], fc[c])}%")

print("\n=== 1コースのSTが内側から何番目か(全6艇の中の順位)別 1コース1着率")
rk_n, rk_w = Counter(), Counter()
for k, v in byr.items():
    vv = [e for e in v if valid(e)]
    if len(vv) < 6 or any(e["flying"] == "1" for e in v):
        continue
    c1 = [e for e in vv if int(float(e["course"])) == 1]
    if len(c1) != 1:
        continue
    s1 = float(c1[0]["st"])
    rank = 1 + sum(float(e["st"]) < s1 - 1e-9 for e in vv)
    g = "1位(同着含む)" if rank == 1 else ("2〜3位" if rank <= 3 else "4〜6位")
    rk_n[g] += 1; rk_w[g] += c1[0]["finish"] == "1"
for g in ("1位(同着含む)", "2〜3位", "4〜6位"):
    print(f" {g}: {pct(rk_w[g], rk_n[g])}% n={rk_n[g]}")
print(" 合計n", sum(rk_n.values()))

print("\n=== 1コースと隣の2コースのST差別 1コース1着率")
dn, dw = Counter(), Counter()
for k, v in byr.items():
    vv = {int(float(e["course"])): e for e in v if valid(e)}
    if 1 not in vv or 2 not in vv or any(e["flying"] == "1" for e in v):
        continue
    d = float(vv[1]["st"]) - float(vv[2]["st"])  # 正なら1コースが遅い
    g = "1コースが速い" if d < -1e-9 else ("同じ" if abs(d) < 1e-9 else ("0.01〜0.04遅い" if d < 0.05 - 1e-9 else "0.05以上遅い"))
    dn[g] += 1; dw[g] += vv[1]["finish"] == "1"
for g in ("1コースが速い", "同じ", "0.01〜0.04遅い", "0.05以上遅い"):
    print(f" {g}: {pct(dw[g], dn[g])}% n={dn[g]}")

print("\n=== フライング・出遅れ")
f = sum(e["flying"] == "1" for e in es)
l = sum(e["finish"].startswith("L") for e in es)
fr = len({(e["date"], e["jcd"], e["rno"]) for e in es if e["flying"] == "1"})
print(f" フライング艇 {f} (全エントリー{len(es)}の{pct(f, len(es), 2)}%) フライングがあったレース {fr}/{len(rs)} ({pct(fr, len(rs))}%)")
print(f" 出遅れ(L) {l}")
fcourse = Counter(int(float(e["course"])) for e in es if e["flying"] == "1" and e["course"])
print(" フライング艇のコース:", dict(sorted(fcourse.items())))
