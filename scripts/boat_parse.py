"""ボートレース公式の競走成績テキスト(K ファイル、UTF-8 変換済み)を表形式に変換する。

parse_k(text) -> (races, entries)
  races   : 1レース1行(場・日付・レース番号・条件・決まり手・払戻)
  entries : 1艇1行(着順・艇番・登録番号・選手名・進入コース・スタートタイミング)
"""
import re
import unicodedata

JCD = {"01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川", "06": "浜名湖", "07": "蒲郡",
       "08": "常滑", "09": "津", "10": "三国", "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門",
       "15": "丸亀", "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松", "21": "芦屋",
       "22": "福岡", "23": "唐津", "24": "大村"}

RACE_HEAD = re.compile(r"^\s+(\d{1,2})R\s+(.+?)\s+H(\d+)m\s+(\S+)\s+風\s+(\S+)\s+(\d+)m\s+波\s+(\d+)cm")
DATE_LINE = re.compile(r"第\s*(\d+)日\s+(\d{4})/\s*(\d{1,2})/\s*(\d{1,2})")
ENTRY = re.compile(r"^  (\S{1,2})\s+([1-6]) (\d{4}) (.{8}) (.*)$")
PAY_LABELS = {"単勝": "win", "２連単": "ex", "２連複": "qn", "３連単": "tri", "３連複": "trio"}
PAY = re.compile(r"^\s+(単勝|複勝|２連単|２連複|拡連複|３連単|３連複)\s+(.*)$")

RACE_FIELDS = ["date", "jcd", "venue", "day", "rno", "race_type", "distance", "weather", "wind_dir", "wind_m",
               "wave_cm", "kimarite"] + [f"{k}_{x}" for k in PAY_LABELS.values() for x in ("combo", "pay", "pop")]
ENTRY_FIELDS = ["date", "jcd", "rno", "finish", "boat", "racer_id", "racer_name", "course", "st", "flying"]


def clean(s):
    return unicodedata.normalize("NFKC", s).replace(" ", "").strip()


def parse_pay(rest):
    """'1-5-2     7320  人気    25' -> (combo, pay, pop)。特払い・不成立などは pay=None"""
    toks = rest.split()
    if not toks or not re.match(r"^\d(-\d){0,2}$", toks[0]):
        return None, None, None
    combo = toks[0]
    pay = int(toks[1]) if len(toks) > 1 and toks[1].isdigit() else None
    pop = None
    if "人気" in toks:
        i = toks.index("人気")
        if i + 1 < len(toks) and toks[i + 1].isdigit():
            pop = int(toks[i + 1])
    return combo, pay, pop


def parse_entry_rest(finish, rest):
    """選手名より後ろ: モーター ボート 展示 進入 ST タイム"""
    toks = rest.split()
    course, st, flying = None, None, False
    if len(toks) >= 5 and toks[3].isdigit():
        course = int(toks[3])
        s = toks[4]
        if s.startswith("F"):
            flying, s = True, s[1:]
        elif s.startswith("L"):
            s = s[1:]
        try:
            st = float(s)
        except ValueError:
            st = None
    if finish.startswith("F"):
        flying = True
    return course, st, flying


def parse_k(text):
    races, entries = [], []
    jcd = venue = date = day = None
    race = None
    for line in text.splitlines():
        line = line.rstrip("\r")
        m = re.match(r"^(\d{2})KBGN", line)
        if m:
            jcd, race = m.group(1), None
            venue = JCD.get(jcd, jcd)
            continue
        if re.match(r"^\d{2}KEND", line):
            race = None
            continue
        m = DATE_LINE.search(line)
        if m and jcd:
            day = int(m.group(1))
            date = f"{int(m.group(2)):04d}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
            continue
        m = RACE_HEAD.match(line)
        if m and jcd and date:
            race = {"date": date, "jcd": jcd, "venue": venue, "day": day, "rno": int(m.group(1)),
                    "race_type": clean(m.group(2)), "distance": int(m.group(3)), "weather": clean(m.group(4)),
                    "wind_dir": clean(m.group(5)), "wind_m": int(m.group(6)), "wave_cm": int(m.group(7)),
                    "kimarite": None}
            races.append(race)
            continue
        if race is None:
            continue
        if "ﾚｰｽﾀｲﾑ" in line:
            tail = line.split("ﾚｰｽﾀｲﾑ", 1)[1]
            race["kimarite"] = clean(tail) or None
            continue
        m = ENTRY.match(line)
        if m:
            finish, boat, rid, name, rest = m.groups()
            course, st, flying = parse_entry_rest(finish, rest)
            entries.append({"date": race["date"], "jcd": race["jcd"], "rno": race["rno"],
                            "finish": int(finish) if finish.isdigit() else finish, "boat": int(boat),
                            "racer_id": rid, "racer_name": clean(name), "course": course, "st": st,
                            "flying": int(flying)})
            continue
        m = PAY.match(line)
        if m and m.group(1) in PAY_LABELS:
            key = PAY_LABELS[m.group(1)]
            if race.get(f"{key}_combo") is None:
                combo, pay, pop = parse_pay(m.group(2))
                race[f"{key}_combo"], race[f"{key}_pay"], race[f"{key}_pop"] = combo, pay, pop
    return races, entries


if __name__ == "__main__":
    import sys
    r, e = parse_k(open(sys.argv[1], encoding="utf-8").read())
    print(len(r), "races", len(e), "entries")
    for x in r[:2]:
        print(x)
    for x in e[:7]:
        print(x)
