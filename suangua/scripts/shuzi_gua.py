# -*- coding: utf-8 -*-
"""
shuzi_gua.py — 数字卦起卦。
用法: python3 shuzi_gua.py N1 N2 N3 [--question 所占何事] [--outdir 输出目录]
规则: N1 mod 8 → 下卦, N2 mod 8 → 上卦（余0作8）; N3 mod 6 → 动爻（余0作6）。
输入范围 000–999。输出: 卦单 + 完整 JSON 档案（双文件落盘并打印到标准输出）。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import (TRIGRAMS, build_record, render_guadan, save_record, xor)


def parse_num(s, label):
    if not s.isdigit() or not (1 <= len(s) <= 3):
        raise SystemExit(f"输入不合法：{label} 应为 000–999 的整数，收到 {s!r}")
    return int(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nums", nargs=3, help="三个 000–999 的数")
    ap.add_argument("--question", default=None, help="命辞（所占何事）")
    ap.add_argument("--outdir", default=".", help="档案输出目录")
    args = ap.parse_args()

    n1, n2, n3 = (parse_num(s, f"第{i+1}数") for i, s in enumerate(args.nums))

    r1, r2, r3 = n1 % 8, n2 % 8, n3 % 6
    lower = r1 if r1 != 0 else 8
    upper = r2 if r2 != 0 else 8
    moving = r3 if r3 != 0 else 6

    ben_bin = TRIGRAMS[lower]["bits"] + TRIGRAMS[upper]["bits"]
    mask = "".join("1" if i == moving - 1 else "0" for i in range(6))

    # 不变量断言：数字卦必为一爻动
    assert mask.count("1") == 1

    process = {
        "三数": [n1, n2, n3],
        "明细": [
            f"{n1} mod 8 = {r1}" + ("（余0作8）" if r1 == 0 else "")
            + f" → 下卦 {TRIGRAMS[lower]['名']}（{TRIGRAMS[lower]['bits']}）",
            f"{n2} mod 8 = {r2}" + ("（余0作8）" if r2 == 0 else "")
            + f" → 上卦 {TRIGRAMS[upper]['名']}（{TRIGRAMS[upper]['bits']}）",
            f"{n3} mod 6 = {r3}" + ("（余0作6）" if r3 == 0 else "")
            + f" → 第{moving}爻动",
            f"本卦 {ben_bin} XOR 掩码 {mask} = 之卦 {xor(ben_bin, mask)}",
        ],
    }

    record = build_record(
        mode="数字卦",
        elements_desc=f"三数 {n1:03d} · {n2:03d} · {n3:03d}",
        question=args.question,
        process=process,
        ben_bin=ben_bin,
        mask=mask,
    )
    jpath, tpath = save_record(record, args.outdir)

    print(render_guadan(record))
    print()
    print(f"档案已写入：{jpath}")
    print(f"卦单已写入：{tpath}")
    print("── JSON ──")
    print(json.dumps(record, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
