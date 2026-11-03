"""ボートレースの集計。サイトと記事の数値はすべてここの出力(data/boat/summary.json)から取る。

使い方: python scripts/boat_stats.py            (summary.json を作り、要点を表示)
        python scripts/boat_stats.py --venue 01  (1場の詳細を表示)
"""
import csv
import glob
import gzip
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boat_parse import JCD  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIMARITE = ["逃げ", "差し", "まくり", "まくり差し", "抜き", "恵まれ"]


def load(kind):
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data/boat", kind, "*.csv.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            rows.extend(csv.DictReader(fh))
    return rows


def pct(a, b, nd=1):
    return round(100 * a / b, nd) if b else None


def course_table(entries):
    """進入コース別 1着率・2連対率・3連対率"""
    n = Counter()
    top = {k: Counter() for k in (1, 2, 3)}
    for e in entries:
        c = e["course"]
        if not c:
            continue
        c = int(c)
        n[c] += 1
        f = e["finish"]
        if f.isdigit():
            for k in (1, 2, 3):
                if int(f) <= k:
                    top[k][c] += 1
    return [{"course": c, "n": n[c], "win": pct(top[1][c], n[c]), "top2": pct(top[2][c], n[c]),
             "top3": pct(top[3][c], n[c])} for c in range(1, 7)]


def payout_stats(races):
    tri = [int(r["tri_pay"]) for r in races if r["tri_pay"]]
    pops = [int(r["tri_pop"]) for r in races if r["tri_pop"]]
    if not tri:
        return {}
    return {"races": len(races), "tri_n": len(tri), "tri_mean": round(statistics.mean(tri)),
            "tri_median": round(statistics.median(tri)), "manshu_pct": pct(sum(1 for x in tri if x >= 10000), len(tri)),
            "tri_pop1_pct": pct(sum(1 for p in pops if p == 1), len(pops)),
            "tri_max": max(tri)}


def kimarite_share(races):
    k = Counter(r["kimarite"] for r in races if r["kimarite"])
    total = sum(k.values())
    return {name: pct(k[name], total) for name in KIMARITE}


def wind_table(races, entries_by_race):
    """風速帯別の1コース1着率"""
    buckets = [("0〜2m", 0, 2), ("3〜4m", 3, 4), ("5m以上", 5, 99)]
    out = []
    for label, lo, hi in buckets:
        rs = [r for r in races if r["wind_m"] and lo <= int(r["wind_m"]) <= hi]
        n = w = 0
        for r in rs:
            for e in entries_by_race.get((r["date"], r["jcd"], r["rno"]), []):
                if e["course"] == "1":
                    n += 1
                    w += e["finish"] == "1"
        out.append({"wind": label, "races": len(rs), "c1_win": pct(w, n)})
    return out


def summarize(races, entries):
    by_race = defaultdict(list)
    for e in entries:
        by_race[(e["date"], e["jcd"], e["rno"])].append(e)
    return {"courses": course_table(entries), "payout": payout_stats(races), "kimarite": kimarite_share(races),
            "wind": wind_table(races, by_race)}


def monthly_c1(races, entries):
    n, w = Counter(), Counter()
    for e in entries:
        if e["course"] == "1":
            ym = e["date"][:7]
            n[ym] += 1
            w[ym] += e["finish"] == "1"
    return [{"month": ym, "c1_win": pct(w[ym], n[ym]), "n": n[ym]} for ym in sorted(n)]


def main():
    races, entries = load("races"), load("entries")
    if not races:
        print("データなし")
        return
    last = max(r["date"] for r in races)
    first = min(r["date"] for r in races)
    since = (date.fromisoformat(last) - timedelta(days=364)).isoformat()
    r1 = [r for r in races if r["date"] >= since]
    e1 = [e for e in entries if e["date"] >= since]
    out = {"first_date": first, "last_date": last, "year_since": since,
           "total_races": len(races), "year_races": len(r1),
           "national": {"year": summarize(r1, e1), "all": summarize(races, entries)},
           "monthly_c1": monthly_c1(races, entries), "venues": {}}
    for jcd, name in JCD.items():
        rv = [r for r in r1 if r["jcd"] == jcd]
        ev = [e for e in e1 if e["jcd"] == jcd]
        ra = [r for r in races if r["jcd"] == jcd]
        ea = [e for e in entries if e["jcd"] == jcd]
        out["venues"][jcd] = {"name": name, "year": summarize(rv, ev), "all": summarize(ra, ea),
                              "year_races": len(rv), "all_races": len(ra),
                              "monthly_c1": monthly_c1(ra, ea)[-24:]}
    # 1コース1着率の場別ランキング(直近1年)
    rank = []
    for jcd, v in out["venues"].items():
        c1 = v["year"]["courses"][0]
        if c1["n"]:
            rank.append({"jcd": jcd, "name": v["name"], "c1_win": c1["win"], "n": c1["n"],
                         "manshu_pct": v["year"]["payout"].get("manshu_pct")})
    out["venue_rank_c1"] = sorted(rank, key=lambda x: -x["c1_win"])
    with open(os.path.join(ROOT, "data/boat/summary.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    if "--venue" in sys.argv:
        jcd = sys.argv[sys.argv.index("--venue") + 1]
        print(json.dumps(out["venues"][jcd], ensure_ascii=False, indent=1))
        return
    y = out["national"]["year"]
    print(f"期間: {first}〜{last} 全{len(races)}レース / 直近1年({since}〜): {len(r1)}レース")
    print("[全国・直近1年] コース別 1着率/2連対率/3連対率 (件数)")
    for c in y["courses"]:
        print(f"  {c['course']}コース {c['win']}% / {c['top2']}% / {c['top3']}% ({c['n']})")
    print("[全国・直近1年] 3連単", y["payout"])
    print("[全国・直近1年] 決まり手%", y["kimarite"])
    print("[全国・直近1年] 風速別1コース1着率", y["wind"])
    print("[場別] 1コース1着率 直近1年 (万舟率)")
    for r in out["venue_rank_c1"]:
        print(f"  {r['name']}: {r['c1_win']}% ({r['manshu_pct']}%) n={r['n']}")
    print("直近の月別1コース1着率:", out["monthly_c1"][-6:])


if __name__ == "__main__":
    main()
