# -*- coding: utf-8 -*-
"""build_final_zhouyi.py — 终装：经文取用户版，传文取参考版 → data/zhouyi.json + data/qa_report.md"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import DATA_DIR, HEX_BY_BIN, ZHOUYI_PATH, yao_title
import validate_zhouyi

PUNCT = "，。、；：？！“”‘’（）·—…《》〈〉「」『』\u3000 \"'(),.;:"


def sp(s):
    return "".join(c for c in (s or "") if c not in PUNCT)


def expand_dup(s):
    out = []
    for c in s or "":
        if c == "々":
            assert out, "叠字符前无可重之字"
            out.append(out[-1])
        else:
            out.append(c)
    return "".join(out)


def deep_fix(obj):
    if isinstance(obj, str):
        return expand_dup(obj)
    if isinstance(obj, list):
        return [deep_fix(x) for x in obj]
    if isinstance(obj, dict):
        return {k: deep_fix(v) for k, v in obj.items()}
    return obj


# 用户定夺的传文勘误（2026-07-19）：乾、屯彖传从通行诸本
REF_CORRECTIONS = [
    ("111111", "彖传", "万国威宁", "万国咸宁", "乾·彖传从通行诸本"),
    ("100010", "彖传", "宜寻建侯", "宜建侯", "屯·彖传从通行诸本"),
]


def main():
    user = json.load(open(os.path.join(DATA_DIR, "int_user_jing.json"), encoding="utf-8"))
    ref = json.load(open(os.path.join(DATA_DIR, "int_ref.json"), encoding="utf-8"))
    errata = json.load(open(os.path.join(DATA_DIR, "int_ref_errata.json"), encoding="utf-8"))
    ujing, uanom = user["经文"], user["异常处理"]

    applied = []
    for b, field, old, new, note in REF_CORRECTIONS:
        assert ref[b][field].count(old) == 1, f"勘误落空: {note} 未找到「{old}」"
        ref[b][field] = ref[b][field].replace(old, new)
        applied.append(f"{note}：「{old}」→「{new}」")
    if "々" in json.dumps(ref, ensure_ascii=False):
        applied.append("叠字符「々」已全部展开为重字（家人·九三小象「嗃々」→「嗃嗃」）")
    ref = deep_fix(ref)
    ujing = deep_fix(ujing)

    zy, diffs = {}, []
    for b in sorted(HEX_BY_BIN, key=lambda x: HEX_BY_BIN[x]["卦序"]):
        info, uj, rj = HEX_BY_BIN[b], ujing[b], ref[b]
        num, name = info["卦序"], info["卦名"]

        def cmp(label, a, r):
            if sp(a) != sp(r):
                diffs.append((num, name, label, a, r))

        cmp("卦辞", uj["卦辞"], rj["卦辞"])
        entry = {"卦序": num, "卦名": name, "卦辞": uj["卦辞"],
                 "彖传": rj["彖传"], "大象": rj["大象"], "爻": []}
        for i in range(6):
            t = yao_title(i + 1, b[i])
            cmp(t, uj["爻辞"][i], rj["爻辞"][t])
            entry["爻"].append({"爻题": t, "爻辞": uj["爻辞"][i], "小象": rj["小象"][t]})
        if num == 1:
            cmp("用九", uj["用九"], rj["爻辞"]["用九"])
            entry["用九"] = {"辞": uj["用九"], "小象": rj["小象"]["用九"]}
            entry["文言"] = rj["文言"]
        if num == 2:
            cmp("用六", uj["用六"], rj["爻辞"]["用六"])
            entry["用六"] = {"辞": uj["用六"], "小象": rj["小象"]["用六"]}
            entry["文言"] = rj["文言"]
        zy[b] = entry

    with open(ZHOUYI_PATH, "w", encoding="utf-8") as f:
        json.dump(zy, f, ensure_ascii=False, indent=1)
    errs = validate_zhouyi.validate(ZHOUYI_PATH)
    assert not errs, f"结构校验未通过: {errs[:5]}"

    # 定夺项落实自检
    assert "万国咸宁" in zy["111111"]["彖传"] and "万国威宁" not in zy["111111"]["彖传"]
    assert "宜建侯而不宁" in zy["100010"]["彖传"] and "宜寻建侯" not in zy["100010"]["彖传"]
    assert "々" not in json.dumps(zy, ensure_ascii=False)

    L = ["# zhouyi.json 质检报告", "",
         "## 一、结构校验",
         "64 卦、384 爻、二用、彖传、大象、小象、乾坤文言全部在位；"
         "爻题与卦码逐位核对通过；上下卦构成与权威表交叉核对通过。", "",
         "## 二、勘误与规范化（依据：卦画交叉校验 / 用户定夺）"]
    L += [f"- {e}" for e in errata]
    L += [f"- {a}" for a in applied]
    L += ["", "## 三、两版经文差异（经文按你提供的版本入库，右列为参考文件写法，供校勘）"]
    if diffs:
        L.append("| 卦 | 处 | 入库（你的版本） | 参考文件 |")
        L.append("|---|---|---|---|")
        for num, name, label, a, r in diffs:
            L.append(f"| {num} {name} | {label} | {a} | {r} |")
    else:
        L.append("- 标点归一后无差异")
    L += ["", "## 四、处理说明"]
    L += [f"- {a}" for a in uanom]
    L += ["- 参考文件卦名变体已归一：遯→遁、习坎→坎（仅名称，正文未动）",
          "- 参考文件卷末系辞上/下、说卦、序卦、杂卦已切分存入 references/",
          "", "## 五、人工复核建议"]
    L += ["- 无待决事项：乾、屯彖传已按通行诸本定夺，叠字符已展开为重字"]
    qa = os.path.join(DATA_DIR, "qa_report.md")
    with open(qa, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"终装完成：{ZHOUYI_PATH} 结构校验通过；经文差异 {len(diffs)} 处 → {qa}")


if __name__ == "__main__":
    main()
