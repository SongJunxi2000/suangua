# -*- coding: utf-8 -*-
"""生成占位版 zhouyi.json：结构与最终版完全一致，文本以【占位】标注，供脚本联调。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import HEX_BY_BIN, yao_title, ZHOUYI_PATH


def main():
    zy = {}
    for b, h in sorted(HEX_BY_BIN.items(), key=lambda kv: kv[1]["卦序"]):
        name = h["卦名"]
        entry = {
            "卦序": h["卦序"],
            "卦名": name,
            "卦辞": f"【占位·{name}卦辞】",
            "彖传": f"【占位·{name}彖传】",
            "大象": f"【占位·{name}大象】",
            "爻": [
                {
                    "爻题": yao_title(i + 1, b[i]),
                    "爻辞": f"【占位·{name}{yao_title(i + 1, b[i])}爻辞】",
                    "小象": f"【占位·{name}{yao_title(i + 1, b[i])}小象】",
                }
                for i in range(6)
            ],
        }
        if b == "111111":
            entry["用九"] = {"辞": "【占位·乾用九】", "小象": "【占位·乾用九小象】"}
        if b == "000000":
            entry["用六"] = {"辞": "【占位·坤用六】", "小象": "【占位·坤用六小象】"}
        zy[b] = entry
    with open(ZHOUYI_PATH, "w", encoding="utf-8") as f:
        json.dump(zy, f, ensure_ascii=False, indent=1)
    print(f"占位经文已写入 {ZHOUYI_PATH}（{len(zy)} 卦）")


if __name__ == "__main__":
    main()
