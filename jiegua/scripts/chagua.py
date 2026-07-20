#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chagua.py — 外来卦查询（解卦技能配套，确定性脚本）

用途：用户自带在别处起的卦时，查经文、推之卦、按朱子断例出取断指引。
经文取自与算卦（suangua）技能同源的 data/zhouyi.json，不凭记忆、不改一字。

用法示例：
  python3 chagua.py 升 --dong 3          # 短卦名 + 第 3 爻动
  python3 chagua.py 地风升 --dong 九三    # 全名 + 爻题（爻题阴阳与实际不符会报错）
  python3 chagua.py 泽水 --dong 2 5      # 上卦象+下卦象（上在前），多爻动
  python3 chagua.py 困                   # 静卦（无动爻）
  python3 chagua.py 011000 --dong 3      # 六位二进制，自下而上，1 为阳
"""
import argparse, json, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "zhouyi.json"

TRI = {  # 自下而上三位，1 为阳
    "111": ("乾", "天"), "000": ("坤", "地"), "100": ("震", "雷"), "010": ("坎", "水"),
    "001": ("艮", "山"), "011": ("巽", "风"), "101": ("离", "火"), "110": ("兑", "泽"),
}
TRI_BY_WORD = {w: b for b, pair in TRI.items() for w in pair}
POS = {"初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6}
POS_NAME = {v: k for k, v in POS.items()}


def load():
    db = json.loads(DATA.read_text(encoding="utf-8"))
    assert len(db) == 64, "zhouyi.json 卦数异常"
    return db


def fullname(b):
    lo, hi = TRI[b[:3]], TRI[b[3:]]
    db_name = NAME_OF[b]
    return f"{db_name}为{lo[1]}" if lo == hi else f"{hi[1]}{lo[1]}{db_name}"


def resolve(token, db):
    """卦名 / 全名 / 上下卦象或名（上在前）/ 六位二进制 → binary key"""
    t = token.strip()
    if len(t) == 6 and set(t) <= {"0", "1"}:
        return t
    by_short = {v["卦名"]: k for k, v in db.items()}
    if t in by_short:
        return by_short[t]
    by_full = {fullname(k): k for k in db}
    if t in by_full:
        return by_full[t]
    # 形如 地风 / 坤巽 / 地风升：前两字为上、下卦
    if len(t) >= 2 and t[0] in TRI_BY_WORD and t[1] in TRI_BY_WORD:
        b = TRI_BY_WORD[t[1]] + TRI_BY_WORD[t[0]]  # 第一字是上卦
        if len(t) == 2 or t[2:] == db[b]["卦名"]:
            return b
        sys.exit(f"错误：上{t[0]}下{t[1]}之卦为「{fullname(b)}」，与所报「{t}」不符，请确认。")
    sys.exit(f"错误：无法识别卦「{t}」。可用短卦名（升）、全名（地风升）、上下卦（地风）或六位二进制。")


def parse_dong(specs, ben):
    """爻位（1-6）或爻题（九三/六四…）→ 位置集合；校验爻题阴阳。"""
    out = set()
    for s in specs:
        s = str(s).strip()
        if s.isdigit() and 1 <= int(s) <= 6:
            out.add(int(s)); continue
        if len(s) == 2:
            a, b = s[0], s[1]
            if a in ("九", "六") and b in POS:      # 九三
                p, yang = POS[b], a == "九"
            elif a in POS and b in ("九", "六"):    # 初九 / 上六
                p, yang = POS[a], b == "九"
            else:
                sys.exit(f"错误：无法识别动爻「{s}」。")
            actual = ben[p - 1] == "1"
            if actual != yang:
                right = ("九" if actual else "六")
                title = f"初{right}" if p == 1 else (f"上{right}" if p == 6 else f"{right}{POS_NAME[p]}")
                sys.exit(f"错误：本卦第{p}爻为{'阳' if actual else '阴'}爻，爻题应作「{title}」，与所报「{s}」不符，请与用户确认。")
            out.add(p); continue
        sys.exit(f"错误：无法识别动爻「{s}」。用 1–6 或爻题（如 九三、上六）。")
    return sorted(out)


def yao(db, b, p):
    return db[b]["爻"][p - 1]


def quduan(db, ben, dong):
    """朱子《易学启蒙》考变占。返回（说明文字, 需另列的之卦条目）。与算卦技能同一规则表。"""
    n = len(dong)
    zhi = "".join(c if i + 1 not in dong else ("0" if c == "1" else "1") for i, c in enumerate(ben)) if n else None
    if n == 0:
        return zhi, "六爻不变：占本卦卦辞。", []
    if n == 1:
        t = yao(db, ben, dong[0])["爻题"]
        return zhi, f"一爻变：以本卦{t}爻辞为断。", []
    if n == 2:
        ts = [yao(db, ben, p)["爻题"] for p in dong]
        return zhi, f"二爻变：占本卦{ts[0]}、{ts[1]}两爻辞，以居上之{ts[1]}为主。", []
    if n == 3:
        return zhi, "三爻变：占本卦及之卦卦辞，本卦为贞（现状、己方），之卦为悔（趋势、变方）。", []
    if n in (4, 5):
        still = [p for p in range(1, 7) if p not in dong]
        items = [yao(db, zhi, p) for p in still]
        if n == 4:
            note = f"四爻变：占之卦{items[0]['爻题']}、{items[1]['爻题']}两不变爻爻辞，以居下之{items[0]['爻题']}为主。"
        else:
            note = f"五爻变：占之卦不变爻{items[0]['爻题']}爻辞。"
        return zhi, note, [("之卦" + it["爻题"], it["爻辞"], it.get("小象", "")) for it in items]
    name = db[ben]["卦名"]
    if name == "乾":
        u = db[ben]["用九"]
        return zhi, "六爻皆变（乾）：以用九之辞为断。", [("本卦用九", u["辞"], u.get("小象", ""))]
    if name == "坤":
        u = db[ben]["用六"]
        return zhi, "六爻皆变（坤）：以用六之辞为断。", [("本卦用六", u["辞"], u.get("小象", ""))]
    return zhi, "六爻皆变：占之卦卦辞。", []


def main():
    ap = argparse.ArgumentParser(description="外来卦查询：经文、之卦、朱子断例。", epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gua", help="本卦：短卦名 / 全名 / 上下卦（上在前）/ 六位二进制")
    ap.add_argument("--dong", nargs="*", default=[], help="动爻：1–6 或爻题（九三、上六），可多个")
    a = ap.parse_args()

    db = load()
    global NAME_OF; NAME_OF = {k: v["卦名"] for k, v in db.items()}
    ben = resolve(a.gua, db)
    dong = parse_dong(a.dong, ben)
    zhi, note, extra = quduan(db, ben, dong)
    B = db[ben]

    bar = "─" * 34
    print(bar)
    print(f"本卦　{fullname(ben)}（第{B['卦序']}卦）　{TRI[ben[3:]][0]}上{TRI[ben[:3]][0]}下")
    print(f"卦辞　{B['卦辞']}")
    print(f"彖传　{B['彖传']}")
    print(f"大象　{B['大象']}")
    for p in dong:
        y = yao(db, ben, p)
        print(f"动爻　{y['爻题']}　{y['爻辞']}")
        if y.get("小象"):
            print(f"　小象　{y['小象']}")
    if zhi and dong:
        Z = db[zhi]
        print(f"之卦　{fullname(zhi)}（第{Z['卦序']}卦）　{TRI[zhi[3:]][0]}上{TRI[zhi[:3]][0]}下")
        print(f"卦辞　{Z['卦辞']}")
        print(f"大象　{Z['大象']}")
    else:
        print("之卦　无（六爻安静，静卦）")
    for title, ci, xiao in extra:
        print(f"{title}　{ci}")
        if xiao:
            print(f"　小象　{xiao}")
    print(f"取断　{note}")
    print(bar)
    print("（经文引自 data/zhouyi.json，与算卦技能同源；本脚本只查录，不解读。）")


if __name__ == "__main__":
    main()
