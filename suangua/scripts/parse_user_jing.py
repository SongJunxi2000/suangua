# -*- coding: utf-8 -*-
"""parse_user_jing.py — 解析用户提供的卦辞爻辞原文 → data/user_jing.json，带三重交叉核验。"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import DATA_DIR, HEX_BY_BIN, yao_title

RAW = os.path.join(DATA_DIR, "user_jing_raw.txt")
OUT = os.path.join(DATA_DIR, "user_jing.json")
NAME2BIN = {h["卦名"]: b for b, h in HEX_BY_BIN.items()}
YAOTI = re.compile(r"^(初九|初六|九二|六二|九三|六三|九四|六四|九五|六五|上九|上六|用九|用六)\s*[：:，,]\s*(.*)$")
PINYIN = re.compile(r"[（(][a-zA-Zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+[)）]")


def main():
    text = open(RAW, encoding="utf-8").read().replace("\ufeff", "")
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if blocks and blocks[0] in ("易经", "周易"):
        blocks = blocks[1:]
    assert len(blocks) == 64, f"应有 64 卦块，实得 {len(blocks)}"

    notes, out = [], {}
    for order, block in enumerate(blocks, start=1):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        header = lines[0]
        glyphs = [c for c in header if 0x4DC0 <= ord(c) <= 0x4DFF]
        name = re.sub(r"[（(].*?[)）]", "", header)
        name = "".join(c for c in name if not (0x4DC0 <= ord(c) <= 0x4DFF)).strip()
        assert name in NAME2BIN, f"无法识别卦名: {header!r}"
        b = NAME2BIN[name]
        h = HEX_BY_BIN[b]
        assert h["卦序"] == order, f"{name} 出现在第 {order} 位，应为第 {h['卦序']} 卦"
        if glyphs:
            assert glyphs[0] == h["卦画符"], f"{name} 卦画符 {glyphs[0]} 与卦序不符"

        guaci_parts, yaos, extras = [], [], {}
        for ln in lines[1:]:
            m = YAOTI.match(ln)
            if not m:
                assert not yaos, f"{name}: 爻辞之后出现非爻题行: {ln!r}"
                guaci_parts.append(ln)
                continue
            title, body = m.group(1), m.group(2).strip()
            cleaned = PINYIN.sub("", body)
            if cleaned != body:
                notes.append(f"{name}{title}: 已剔除夹注 {body!r} → {cleaned!r}")
            if title in ("用九", "用六"):
                extras[title] = {"辞": cleaned}
            else:
                yaos.append({"爻题": title, "爻辞": cleaned})

        assert guaci_parts, f"{name}: 未解析到卦辞"
        assert len(yaos) == 6, f"{name}: 爻辞 {len(yaos)} 条，应为 6"
        want_titles = [yao_title(i + 1, b[i]) for i in range(6)]
        got_titles = [y["爻题"] for y in yaos]
        assert got_titles == want_titles, \
            f"{name}: 爻题序列 {got_titles} 与卦码应有的 {want_titles} 不符"
        if b == "111111":
            assert "用九" in extras, "乾缺用九"
        if b == "000000":
            assert "用六" in extras, "坤缺用六"
        assert not (extras and b not in ("111111", "000000")), f"{name} 不应有二用"

        out[b] = {"卦名": name, "卦辞": " ".join(guaci_parts), "爻": yaos, **extras}

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"解析完成：64 卦、384 爻、二用在位，爻题阴阳序列与卦码全部吻合。→ {OUT}")
    if notes:
        print("清理记录：")
        for n in notes:
            print(" -", n)


if __name__ == "__main__":
    main()
