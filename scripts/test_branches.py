# -*- coding: utf-8 -*-
"""test_branches.py — 稀有分支强制覆盖：不靠运气，逐一验证取断规则与经文汇集。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import build_record, render_guadan

CASES = [
    # (名称, 六爻营数自下而上, 期望断例, 期望应据数, 检查函数)
    ("乾六爻皆变→用九", [9] * 6, "六爻皆变（乾）", 1,
     lambda r: r["经文"]["特例"]["用九"] is not None and r["之卦"]["卦名"] == "坤"),
    ("坤六爻皆变→用六", [6] * 6, "六爻皆变（坤）", 1,
     lambda r: r["经文"]["特例"]["用六"] is not None and r["之卦"]["卦名"] == "乾"),
    ("他卦六爻皆变→之卦卦辞", [9, 9, 6, 6, 9, 6], "六爻皆变", 1,
     lambda r: r["取断"]["应据"][0] == {"卦": "之卦", "文本": "卦辞"}),
    ("二爻变→上动爻为主", [9, 7, 8, 9, 7, 8], "二爻变", 2,
     lambda r: r["取断"]["为主"]["爻位"] == 4),
    ("三爻变→贞悔", [9, 9, 9, 7, 8, 8], "三爻变", 2,
     lambda r: r["取断"]["为主"]["卦"] == "本卦"),
    ("四爻变→之卦二静爻,下者为主", [9, 9, 6, 6, 7, 8], "四爻变", 2,
     lambda r: r["取断"]["为主"] == {"卦": "之卦", "文本": "爻辞", "爻位": 5,
                                    "爻题": r["取断"]["为主"]["爻题"]}
     and len(r["经文"]["特例"]["之卦不变爻"]) == 2),
    ("五爻变→之卦独静爻", [9, 9, 6, 6, 9, 7], "五爻变", 1,
     lambda r: r["取断"]["为主"]["爻位"] == 6
     and len(r["经文"]["特例"]["之卦不变爻"]) == 1),
]


def run():
    fails = 0
    for name, values, want_case, want_refs, check in CASES:
        ben = "".join("1" if v in (7, 9) else "0" for v in values)
        mask = "".join("1" if v in (6, 9) else "0" for v in values)
        r = build_record("筹策卦（测试）", "强制路径", None,
                         {"测试": name}, ben, mask, values)
        qd = r["取断"]
        ok = qd["断例"] == want_case and len(qd["应据"]) == want_refs and check(r)
        # 卦单必须能渲染（覆盖静卦以外的所有渲染分支）
        render_guadan(r)
        status = "✓" if ok else "✗"
        if not ok:
            fails += 1
        zhi = r["之卦"]["卦名"] if r["之卦"] else "—"
        print(f" {status} {name:24s} 本卦{r['本卦']['卦名']} 之{zhi}  "
              f"断例[{qd['断例']}] {qd['说明']}")
    print("全部通过 ✓" if fails == 0 else f"{fails} 项失败 ✗")
    sys.exit(0 if fails == 0 else 1)


if __name__ == "__main__":
    run()
