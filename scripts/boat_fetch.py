"""ボートレース公式の競走成績(K)ファイルを日付範囲でダウンロード・解析し、月別CSV(gzip)に保存する。

使い方: python scripts/boat_fetch.py 2024-01-01 2024-12-31
        python scripts/boat_fetch.py --recent 3     (直近3日分を取り直す)
lha コマンド(lhasa)が必要。
"""
import csv
import gzip
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boat_parse import ENTRY_FIELDS, RACE_FIELDS, parse_k  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (compatible; race-stats/0.1; +https://github.com/kotsuo07/race-stats)"


def download(d):
    url = f"https://www1.mbrace.or.jp/od2/K/{d:%Y%m}/k{d:%y%m%d}.lzh"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(5 * (attempt + 1))
        except Exception:  # noqa: BLE001
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"download failed: {url}")


def extract(blob):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "k.lzh")
        open(p, "wb").write(blob)
        subprocess.run(["lha", "xq", "k.lzh"], cwd=tmp, check=True)
        txts = [f for f in os.listdir(tmp) if f.lower().endswith(".txt")]
        return "".join(open(os.path.join(tmp, f), "rb").read().decode("cp932", "replace") for f in txts)


def path(kind, ym):
    return os.path.join(ROOT, "data", "boat", kind, f"{ym}.csv.gz")


def load(kind, ym):
    p = path(kind, ym)
    if not os.path.exists(p):
        return []
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(kind, ym, rows, fields):
    p = path(kind, ym)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    rows.sort(key=lambda r: (r["date"], r["jcd"], int(r["rno"]), str(r.get("boat", ""))))
    with gzip.open(p, "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


def main():
    if sys.argv[1] == "--recent":
        end = datetime.now(JST).date() - timedelta(days=1)
        start = end - timedelta(days=int(sys.argv[2]) - 1)
    else:
        start, end = date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])
    by_month = defaultdict(lambda: {"races": [], "entries": [], "dates": set()})
    d, n_days, n_races = start, 0, 0
    while d <= end:
        blob = download(d)
        if blob:
            races, entries = parse_k(extract(blob))
            m = by_month[f"{d:%Y-%m}"]
            m["races"] += races
            m["entries"] += entries
            m["dates"].add(d.isoformat())
            n_days += 1
            n_races += len(races)
            print(d, len(races), "races", flush=True)
        else:
            print(d, "no file", flush=True)
        d += timedelta(days=1)
        time.sleep(1)
    for ym, m in by_month.items():
        for kind, fields in (("races", RACE_FIELDS), ("entries", ENTRY_FIELDS)):
            old = [r for r in load(kind, ym) if r["date"] not in m["dates"]]
            save(kind, ym, old + m[kind], fields)
    print(f"done: {n_days} days, {n_races} races")


if __name__ == "__main__":
    main()
