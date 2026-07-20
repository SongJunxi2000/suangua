# -*- coding: utf-8 -*-
"""
ingest_reference.py — 解析上传的通行本《周易》（经传合编）
产出: data/int_ref.json（每卦: 卦辞/彖传/大象/爻辞[6]/小象[6]/用九用六(辞+小象)/文言）
     references/{xici_shang,xici_xia,shuogua,xugua,zagua}.txt
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import DATA_DIR, HEX_BY_NUM, yao_title

SRC = "/mnt/user-data/uploads/1784468415271_I_Ching.txt"
OUT = os.path.join(DATA_DIR, "int_ref.json")
REF_DIR = os.path.normpath(os.path.join(DATA_DIR, "..", "references"))

HDR_RE = re.compile(r"^(\d{1,2})[\.．、]\s*(\S{1,3})（卦[一二三四五六七八九十百]+）$")
YAO_RE = re.compile(r"^(初九|初六|九二|六二|九三|六三|九四|六四|九五|六五|上九|上六|用九|用六)[：:，]\s*(.+)$")
COMP_RE = re.compile(r"（(.)下(.)上）")
SECTIONS = {"系辞": "xici_shang", "系辞上": "xici_shang", "系辞下": "xici_xia",
            "说卦": "shuogua", "序卦": "xugua", "杂卦": "zagua"}
PUNCT = "，。、；：？！“”‘’（）·—…《》〈〉\u3000 \"'(),.;:"


def strip_punct(s):
    return "".join(c for c in s if c not in PUNCT)


def parse_units(lines, gua_name, allowed_names):
    """把一个卦块的物理行拼成逻辑单元 [(type, text)]。硬换行接到上一单元。"""
    units = []
    m_shu = re.compile(r"^《(\S{1,4})》[：:]?\s*(.*)$")
    m_bare = re.compile(r"^(\S{1,4})[：:]\s*(.*)$")
    inline = re.compile(r"(《彖》曰[：:]?|《象》曰[：:]?|《文言》曰[：:]?|彖曰[：:]|象曰[：:]|文言曰[：:])")
    def mkind(m):
        return "文言" if "文言" in m else ("彖" if "彖" in m else "象")

    def push(typ, text):
        units.append((typ, text.strip()))

    def append_cont(text):
        if units:
            units[-1] = (units[-1][0], units[-1][1] + text.strip())
        elif text.strip():
            raise SystemExit(f"[{gua_name}] 无处安放的行: {text!r}")

    for line in lines:
        if not line:
            continue
        if COMP_RE.search(line) and len(line) <= 10:
            push("构成", COMP_RE.search(line).group(0))
            continue
        if len(line) <= 3 and re.fullmatch(r"[ⅰ-ⅻⅠ-Ⅻ]+", line):
            continue
        # 行内可能混排多个传文标记，先切段
        parts = inline.split(line)
        head, rest = parts[0], parts[1:]
        # 段首处理
        no_content_yet = not any(t != "构成" for t, _ in units)
        if no_content_yet and head.strip():
            m = m_shu.match(head) or m_bare.match(head)
            if not (m and m.group(1) in allowed_names):
                raise SystemExit(f"[{gua_name}] 块首卦辞前缀无法识别: {head!r}")
            push("卦辞", m.group(2))
        else:
            m = YAO_RE.match(head)
            if m:
                push("爻:" + m.group(1), m.group(2))
            elif head.strip():
                append_cont(head)
        # 行内后续标记逐段成单元
        for marker, text in zip(rest[0::2], rest[1::2]):
            push(mkind(marker), text)
    return units


def split_merged_xiang(text, anchors):
    """乾式合段象传：按“引文”锚点拆成 大象 + 逐爻小象。
    anchors: [(爻题, 爻辞净文)]，按序消耗。"""
    pieces = re.split(r"(?=“)", text)
    daxiang, buckets, idx = pieces[0].strip(), [], 0
    for piece in pieces[1:]:
        q = re.match(r"“([^”]*)”", piece)
        quoted = strip_punct(q.group(1)) if q else ""
        matched = False
        if idx < len(anchors):
            title, jing = anchors[idx]
            if quoted and (quoted in jing or quoted in title or title in quoted):
                buckets.append(piece.strip())
                idx += 1
                matched = True
        if not matched:
            if not buckets:
                daxiang += piece.strip()
            else:
                buckets[-1] += piece.strip()
    assert idx == len(anchors), \
        f"合段象传拆分失败：匹配 {idx}/{len(anchors)} 个锚点"
    return daxiang, buckets


def assemble(num, units):
    info = HEX_BY_NUM[num]
    name, binary = info["卦名"], info["二进制"]
    titles = [yao_title(i + 1, binary[i]) for i in range(6)]
    extra_title = "用九" if num == 1 else ("用六" if num == 2 else None)
    order = titles + ([extra_title] if extra_title else [])

    entry = {"卦名": name, "卦辞": None, "彖传": None, "大象": None,
             "爻辞": {}, "小象": {}, "文言": None}
    errata = []
    yao_seq = []          # 按出现顺序: {"label","辞","小象"}

    seq = [t for t, _ in units]
    first_yao = next((i for i, t in enumerate(seq) if t.startswith("爻:")), None)
    first_xiang = next((i for i, t in enumerate(seq) if t == "象"), None)
    assert "彖" in seq, f"第{num}卦{name} 未找到《彖》曰"
    merged_style = first_yao is not None and first_xiang is not None \
        and first_yao < first_xiang
    if merged_style:
        assert seq.count("象") == 1, \
            f"第{num}卦{name} 判为合段但有 {seq.count('象')} 个象单元"
    merged_xiang = None

    for typ, text in units:
        if typ == "构成":
            lo, up = COMP_RE.match(text).group(1), COMP_RE.match(text).group(2)
            assert (lo, up) == (info["下卦"]["名"], info["上卦"]["名"]), \
                f"第{num}卦{name} 构成不符: 文件{text} vs 表({info['下卦']['名']}下{info['上卦']['名']}上)"
        elif typ == "卦辞":
            entry["卦辞"] = text
        elif typ.startswith("爻:"):
            yao_seq.append({"label": typ[2:], "辞": text, "小象": None})
        elif typ == "彖":
            entry["彖传"] = text
        elif typ == "象":
            if merged_style:
                merged_xiang = text
            elif entry["大象"] is None:
                entry["大象"] = text
            else:
                assert yao_seq and yao_seq[-1]["小象"] is None, \
                    f"第{num}卦{name} 出现无所系的小象"
                yao_seq[-1]["小象"] = text
        elif typ == "文言":
            entry["文言"] = text

    assert len(yao_seq) == len(order), \
        f"第{num}卦{name} 爻数 {len(yao_seq)}，应为 {len(order)}"
    for pos, (want, got) in enumerate(zip(order, yao_seq), start=1):
        if got["label"] != want:
            errata.append(f"第{num}卦{name} 第{pos}爻爻题勘误: 文件作「{got['label']}」，据卦画应为「{want}」")

    if merged_style:
        anchors = [(want, strip_punct(got["辞"]))
                   for want, got in zip(order, yao_seq)]
        daxiang, buckets = split_merged_xiang(merged_xiang, anchors)
        entry["大象"] = daxiang
        for got, x in zip(yao_seq, buckets):
            got["小象"] = x

    for want, got in zip(order, yao_seq):
        entry["爻辞"][want] = got["辞"]
        entry["小象"][want] = got["小象"]

    # 完整性校验
    assert entry["卦辞"] and entry["彖传"] and entry["大象"], \
        f"第{num}卦{name} 卦辞/彖/大象不全"
    for t in order:
        assert entry["爻辞"].get(t), f"第{num}卦{name} 缺{t}爻辞"
        assert entry["小象"].get(t), f"第{num}卦{name} 缺{t}小象"
    if extra_title:
        assert entry["文言"], f"第{num}卦{name} 缺文言"
    return binary, entry, errata


def main():
    lines = [l.strip().replace("\u3000", "") for l in open(SRC, encoding="utf-8")]
    lines = [l.strip() for l in lines]

    # 定位 64 个卦头与卷末分节
    marks = []
    for i, l in enumerate(lines):
        m = HDR_RE.match(l)
        if m:
            marks.append((i, int(m.group(1)), m.group(2)))
    assert len(marks) == 64, f"卦头 {len(marks)} 个，应为 64"
    assert [n for _, n, _ in marks] == list(range(1, 65)), "卦序不连续"

    sec_marks = [(i, SECTIONS[l]) for i, l in enumerate(lines)
                 if l in SECTIONS and i > marks[-1][0]]
    end_of_gua = sec_marks[0][0] if sec_marks else len(lines)

    ref = {}
    all_errata = []
    for k, (start, num, _) in enumerate(marks):
        stop = marks[k + 1][0] if k + 1 < 64 else end_of_gua
        name = HEX_BY_NUM[num]["卦名"]
        allowed = {name} | ({"遯"} if num == 33 else set()) | ({"习坎"} if num == 29 else set())
        units = parse_units(lines[start + 1:stop], name, allowed)
        binary, entry, errata = assemble(num, units)
        all_errata.extend(errata)
        ref[binary] = entry

    os.makedirs(REF_DIR, exist_ok=True)
    for j, (i, fn) in enumerate(sec_marks):
        stop = sec_marks[j + 1][0] if j + 1 < len(sec_marks) else len(lines)
        body = "\n".join(l for l in lines[i:stop] if l)
        with open(os.path.join(REF_DIR, fn + ".txt"), "w", encoding="utf-8") as f:
            f.write(body + "\n")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ref, f, ensure_ascii=False, indent=1)
    print(f"参考文本入库：64 卦经传齐全，构成交叉校验通过 → {OUT}")
    for e in all_errata:
        print("  · 勘误:", e)
    json.dump(all_errata, open(os.path.join(DATA_DIR, "int_ref_errata.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"卷末分节：{[fn for _, fn in sec_marks]} → {REF_DIR}/")


if __name__ == "__main__":
    main()
