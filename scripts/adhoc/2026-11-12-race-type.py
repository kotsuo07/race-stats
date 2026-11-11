"""レース種別(予選・一般・準優勝戦・優勝戦・ドリーム戦)と進入固定の有無で見た1コース1着率・万舟率など(直近1年、全国)"""
import os, sys, statistics
from collections import defaultdict, Counter
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

FINAL = {"優勝戦", "GP優勝戦", "S戦優勝戦", "MD優勝戦", "団体・優勝戦"}


def category(t):
    base = t.replace("☆", "").replace("進入固定", "")
    if base in FINAL:
        return "優勝戦"
    if "準優勝戦" in base or "準優戦" in base:
        return "準優勝戦"
    if "ドリーム" in base:
        return "ドリーム戦"
    if "予選" in base:
        return "予選"
    if "一般" in base:
        return "一般"
    return "その他(愛称つきレースなど)"


def stats(rs):
    c1n = c1w = b1n = b1w = waku = wn = 0
    for r in rs:
        es = by_race.get((r["date"], r["jcd"], r["rno"]), [])
        for e in es:
            if e["course"] == "1":
                c1n += 1; c1w += e["finish"] == "1"
            if e["boat"] == "1":
                b1n += 1; b1w += e["finish"] == "1"
        es2 = [e for e in es if e["course"]]
        if es2:
            wn += 1
            waku += all(e["boat"] == e["course"] for e in es2)
    tri = [int(float(r["tri_pay"])) for r in rs if r["tri_pay"]]
    k = [r["kimarite"] for r in rs if r["kimarite"]]
    return {"races": len(rs), "c1_n": c1n, "c1_win": pct(c1w, c1n), "b1_win": pct(b1w, b1n),
            "wakunari": pct(waku, wn), "manshu": pct(sum(x >= 10000 for x in tri), len(tri)), "tri_n": len(tri),
            "tri_median": round(statistics.median(tri)) if tri else None,
            "nige": pct(sum(x == "逃げ" for x in k), len(k))}


print(f"期間 {since}〜{last} 全{len(races)}レース")
cats = defaultdict(list)
for r in races:
    cats[category(r["race_type"])].append(r)
print("[レース種別]")
for c in ["予選", "一般", "準優勝戦", "優勝戦", "ドリーム戦", "その他(愛称つきレースなど)"]:
    print(c, stats(cats[c]))
    print("   rno", Counter(r["rno"] for r in cats[c]).most_common(3), "day", Counter(r["day"] for r in cats[c]).most_common(3))
print("[進入固定の有無]")
fx = [r for r in races if "進入固定" in r["race_type"]]
nf = [r for r in races if "進入固定" not in r["race_type"]]
print("進入固定", stats(fx), "場数", len({r["venue"] for r in fx}), Counter(r["venue"] for r in fx).most_common(8))
print("通常", stats(nf))
fxv = {r["venue"] for r in fx}
print("[進入固定を実施した場の通常レース]", stats([r for r in nf if r["venue"] in fxv]))
print("[全体]", stats(races))
print("[予選の内訳]")
yo = cats["予選"]
plain = [r for r in yo if r["race_type"].replace("☆", "").replace("進入固定", "") == "予選"]
print("名称が「予選」のみ", stats(plain))
print("予選特賞・特選など", stats([r for r in yo if r not in plain]))
print("[1〜12R別 予選のみ]")
for lo, hi in [(1, 4), (5, 8), (9, 12)]:
    print(f"{lo}〜{hi}R", stats([r for r in yo if lo <= int(r["rno"]) <= hi]))
