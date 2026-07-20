# -*- coding: utf-8 -*-
"""ingest_user_jing.py — 解析用户提供的经文（卦辞/爻辞/用九用六）→ data/int_user_jing.json"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import DATA_DIR, HEX_BY_BIN, HEX_BY_NUM, yao_title

SRC = os.path.join(DATA_DIR, "source_jingwen_user.txt")
OUT = os.path.join(DATA_DIR, "int_user_jing.json")
ALIAS = {"遯": "遁"}
YAO_RE = re.compile(r"^(初九|初六|九二|六二|九三|六三|九四|六四|九五|六五|上九|上六|用九|用六)[：:，]\s*(.+)$")
HDR_RE = re.compile(r"^(\S{1,3}?)\s*([\u4DC0-\u4DFF])\s*(（.*?）)?\s*$")
PINYIN_RE = re.compile(r"（[a-zA-Zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]+）")


def main():
    anomalies = []
    blocks = {}   # num -> {"名":.., "卦辞":[], "爻":{爻题:辞}}
    cur = None
    for raw in open(SRC, encoding="utf-8"):
        line = raw.strip()
        if not line or line == "易经":
            continue
        m = HDR_RE.match(line)
        if m and m.group(2):
            name, glyph, note = m.group(1), m.group(2), m.group(3)
            num = ord(glyph) - 0x4DC0 + 1
            auth = HEX_BY_NUM[num]["卦名"]
            if ALIAS.get(name, name) != auth:
                raise SystemExit(f"卦头名与卦画符不符: {line!r} → 符指第{num}卦{auth}")
            if note:
                anomalies.append(f"第{num}卦{auth}：卦头附注 {note} 已忽略")
            cur = {"名": auth, "卦辞": [], "爻": {}}
            blocks[num] = cur
            continue
        if cur is None:
            raise SystemExit(f"卦头之前出现正文: {line!r}")
        clean = PINYIN_RE.sub("", line)
        if clean != line:
            anomalies.append(f"第{max(blocks)}卦{cur['名']}：已剥离拼音夹注 → {line!r}")
        m = YAO_RE.match(clean)
        if m:
            cur["爻"][m.group(1)] = m.group(2).strip()
        else:
            cur["卦辞"].append(clean)

    assert len(blocks) == 64, f"仅解析到 {len(blocks)} 卦"
    out = {}
    for num in range(1, 65):
        b = blocks[num]
        info = HEX_BY_NUM[num]
        binary = info["二进制"]
        titles = [yao_title(i + 1, binary[i]) for i in range(6)]
        missing = [t for t in titles if t not in b["爻"]]
        assert not missing, f"第{num}卦{b['名']}缺爻: {missing}（爻题与卦码交叉校验失败）"
        entry = {"卦名": b["名"], "卦辞": "".join(b["卦辞"]),
                 "爻辞": [b["爻"][t] for t in titles]}
        assert entry["卦辞"], f"第{num}卦{b['名']}卦辞为空"
        if num == 1:
            assert "用九" in b["爻"], "乾缺用九"
            entry["用九"] = b["爻"]["用九"]
        if num == 2:
            assert "用六" in b["爻"], "坤缺用六"
            entry["用六"] = b["爻"]["用六"]
        extras = set(b["爻"]) - set(titles) - {"用九", "用六"}
        assert not extras, f"第{num}卦{b['名']}多出爻题: {extras}"
        out[binary] = entry

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"经文": out, "异常处理": anomalies}, f, ensure_ascii=False, indent=1)
    print(f"用户经文入库：64 卦全、爻题与卦码交叉校验通过 → {OUT}")
    for a in anomalies:
        print("  ·", a)


if __name__ == "__main__":
    main()
