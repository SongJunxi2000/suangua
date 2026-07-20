# -*- coding: utf-8 -*-
"""
validate_zhouyi.py — 经文数据结构校验。
用法: python3 validate_zhouyi.py [path]   （缺省校验 data/zhouyi.json）
校验项：
  1. 恰好 64 个键，且为全部六位二进制；
  2. 每卦的 卦序/卦名 与权威对照表一致（拦截卦序错位、张冠李戴）；
  3. 每卦 卦辞/彖传/大象 非空；恰好六爻，爻题与卦码逐位核对，爻辞/小象非空；
  4. 乾有用九、坤有用六，其余卦不得出现二用。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import HEX_BY_BIN, yao_title, ZHOUYI_PATH


def validate(path):
    errors = []
    with open(path, "r", encoding="utf-8") as f:
        zy = json.load(f)

    want = {format(i, "06b") for i in range(64)}
    if set(zy.keys()) != want:
        missing = sorted(want - set(zy.keys()))
        extra = sorted(set(zy.keys()) - want)
        errors.append(f"键不齐: 缺 {missing} 多 {extra}")
        return errors

    for b, e in zy.items():
        auth = HEX_BY_BIN[b]
        tag = f"[{b} {auth['卦名']}]"
        if e.get("卦序") != auth["卦序"]:
            errors.append(f"{tag} 卦序不符: {e.get('卦序')} 应为 {auth['卦序']}")
        if e.get("卦名") != auth["卦名"]:
            errors.append(f"{tag} 卦名不符: {e.get('卦名')}")
        for field in ("卦辞", "彖传", "大象"):
            if not str(e.get(field, "")).strip():
                errors.append(f"{tag} {field} 为空")
        yaos = e.get("爻", [])
        if len(yaos) != 6:
            errors.append(f"{tag} 爻数为 {len(yaos)}，应为 6")
        else:
            for i, y in enumerate(yaos):
                want_title = yao_title(i + 1, b[i])
                if y.get("爻题") != want_title:
                    errors.append(f"{tag} 第{i+1}爻爻题 {y.get('爻题')} 应为 {want_title}")
                for field in ("爻辞", "小象"):
                    if not str(y.get(field, "")).strip():
                        errors.append(f"{tag} {want_title} {field} 为空")
        if b == "111111" and "用九" not in e:
            errors.append(f"{tag} 缺用九")
        if b == "000000" and "用六" not in e:
            errors.append(f"{tag} 缺用六")
        if b not in ("111111", "000000") and ("用九" in e or "用六" in e):
            errors.append(f"{tag} 不应有二用")
    return errors


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ZHOUYI_PATH
    errs = validate(path)
    if errs:
        print(f"校验未通过，共 {len(errs)} 处问题：")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print(f"校验通过：{path} 结构完好（64 卦、384 爻、二用在位）。")
