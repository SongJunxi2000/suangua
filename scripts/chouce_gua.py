# -*- coding: utf-8 -*-
"""
chouce_gua.py — 筹策卦（大衍筮法·四元素抓阄）状态机。

子命令:
  start   [--question Q] [--force]   开新局，输出第一爻三变的选项（不含映射）
  pick    C1 C2 C3                   提交本爻三变选择（序号1-4或元素名），揭示并结算
  status                             查看进度
  commits                            出示当前未揭示轮次的承诺哈希（应质疑时用）
  reset                              作废当前局
  selftest [--n N]                   蒙特卡洛自检：三种选择策略下验证 6/7/8/9 分布
公共参数: [--state 状态文件] [--outdir 档案目录]

输出纪律（硬规则）:
  start / pick 打印下一轮选项时绝不包含映射与盐——映射只存状态文件，
  待用户选定后才随揭示打印。任何修改本文件者不得破坏此纪律。
"""
import argparse
import hashlib
import json
import os
import secrets
import sys
from random import SystemRandom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gua_core import (DATA_DIR, LAOSHAO, build_record, now_iso, render_guadan,
                      save_record, yao_title)

RNG = SystemRandom()
DEFAULT_STATE = "/home/claude/.chouce_state.json"
LABELS_PATH = os.path.join(DATA_DIR, "labels.json")

# 变次 → (合法取出集合)。第一变含挂一取 5/9，二三变取 4/8。
VALID_REMOVED = {1: (5, 9), 2: (4, 8), 3: (4, 8)}


# ------------------------------------------------------------ 标签抽取 --------
def load_labels():
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def draw_round(yao_pos, last_themes):
    """为某一爻抽三变的主题、元素、映射、盐、承诺。返回 pending 列表。"""
    lab = load_labels()
    themes = [(k, "恰四组") for k in lab["恰四组"]] + [(k, "开放池") for k in lab["开放池"]]
    pool = [t for t in themes if t[0] not in last_themes] or themes
    chosen = RNG.sample(pool, 3)
    pending = []
    for k, (theme, kind) in enumerate(chosen, start=1):
        items = list(lab[kind][theme]) if kind == "恰四组" else RNG.sample(lab[kind][theme], 4)
        residues = [0, 1, 2, 3]
        RNG.shuffle(residues)
        mapping = dict(zip(items, residues))
        salt = secrets.token_hex(8)
        payload = json.dumps({"爻": yao_pos, "变": k, "主题": theme, "选项": items,
                              "映射": mapping, "盐": salt},
                             ensure_ascii=False, sort_keys=True)
        pending.append({"变": k, "主题": theme, "选项": items, "映射": mapping,
                        "盐": salt, "承诺": hashlib.sha256(payload.encode()).hexdigest()})
    return pending


def public_round(yao_pos, pending):
    """pending 的可公开视图：只含主题/选项，绝不含映射与盐。"""
    return {"爻位": yao_pos,
            "三变选项": [{"变": p["变"], "主题": p["主题"], "选项": p["选项"]}
                        for p in pending]}


# ------------------------------------------------------------ 分揲结算 --------
def backfill_left(N, a):
    """在 [2, N-1] 中按余数类 (L-1) mod 4 == a 均匀回填左堆数。"""
    first = 5 if a == 0 else a + 1        # a==0 时最小合法 L-1 为 4
    count = ((N - 1) - first) // 4 + 1
    assert count >= 1, f"余数类为空: N={N} a={a}"
    return first + 4 * secrets.randbelow(count)


def resolve_bian(N, k, a):
    """执行第 k 变：余数类 a → 完整分揲明细。返回 (trace, 新的所余)。"""
    L = backfill_left(N, a)
    left_take = 4 if a == 0 else a
    R = N - L
    rr = R % 4
    right_take = 4 if rr == 0 else rr
    removed = 1 + left_take + right_take
    assert removed in VALID_REMOVED[k], f"第{k}变取出{removed}，违反不变量"
    assert L - 1 >= left_take and R >= right_take >= 1
    trace = {"变": k, "起手": N, "左堆": L, "挂一后左": L - 1,
             "左揲四取": left_take, "右堆": R, "右揲四取": right_take,
             "本变共取": removed, "所余": N - removed}
    return trace, N - removed


def resolve_yao(picks_residues, extra=None):
    """三变成一爻。picks_residues: [a1,a2,a3]。extra: 每变附加揭示信息。"""
    N, traces = 49, []
    for k, a in enumerate(picks_residues, start=1):
        t, N = resolve_bian(N, k, a)
        t["余数类"] = a
        if extra:
            t.update(extra[k - 1])
        traces.append(t)
    assert N in (24, 28, 32, 36), f"三变后所余 {N}，违反不变量"
    value = N // 4
    return value, traces


# ------------------------------------------------------------ 状态读写 --------
def load_state(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path, st):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def fail(msg):
    print(json.dumps({"错误": msg}, ensure_ascii=False))
    sys.exit(2)


# ------------------------------------------------------------ 子命令 ----------
def cmd_start(args):
    st = load_state(args.state)
    if st and st.get("状态") == "进行中" and not args.force:
        fail("已有一局进行中；用 status 查看，或 reset / start --force 重开。")
    pending = draw_round(1, [])
    st = {"命辞": args.question, "开始时间": now_iso(), "状态": "进行中",
          "当前爻": 1, "完成爻": [], "pending": pending,
          "上轮主题": [p["主题"] for p in pending]}
    save_state(args.state, st)
    print(json.dumps({"局": "已开",
                      "命辞": args.question,
                      "说明": "大衍之数五十，其用四十有九。每爻三变，凡十八变而成卦。"
                             "本爻三变映射已封存（可用 commits 出示承诺）。",
                      "本轮": public_round(1, pending)},
                     ensure_ascii=False, indent=1))


def resolve_choice(token, items):
    if token in items:
        return token
    if token.isdigit() and 1 <= int(token) <= 4:
        return items[int(token) - 1]
    fail(f"无法识别的选择 {token!r}；应为 1-4 或 {items} 之一。")


def cmd_pick(args):
    st = load_state(args.state)
    if not st or st.get("状态") != "进行中":
        fail("当前没有进行中的一局；先用 start 开局。")
    pending = st["pending"]
    yao_pos = st["当前爻"]

    residues, extra = [], []
    for p, token in zip(pending, args.choices):
        item = resolve_choice(token, p["选项"])
        residues.append(p["映射"][item])
        extra.append({"主题": p["主题"], "选项序": p["选项"], "所选": item,
                      "映射揭示": p["映射"], "盐": p["盐"], "承诺": p["承诺"]})

    value, traces = resolve_yao(residues, extra)
    st["完成爻"].append({"爻位": yao_pos, "营数": value, "老少": LAOSHAO[value],
                        "阴阳": "阳" if value in (7, 9) else "阴", "三变": traces})

    reveal = {"第几爻": yao_pos, "营数": value, "老少": LAOSHAO[value],
              "三变揭示": traces,
              "累计营数": [e["营数"] for e in st["完成爻"]]}

    if yao_pos < 6:
        st["当前爻"] = yao_pos + 1
        st["pending"] = draw_round(yao_pos + 1, st.get("上轮主题", []))
        st["上轮主题"] = [p["主题"] for p in st["pending"]]
        save_state(args.state, st)
        reveal["下一爻"] = public_round(yao_pos + 1, st["pending"])
        print(json.dumps(reveal, ensure_ascii=False, indent=1))
        return

    # 第六爻：成卦
    st["状态"] = "已完成"
    st["pending"] = []
    values = [e["营数"] for e in st["完成爻"]]
    ben_bin = "".join("1" if v in (7, 9) else "0" for v in values)
    mask = "".join("1" if v in (6, 9) else "0" for v in values)
    record = build_record(
        mode="筹策卦（大衍十八变·四元素抓阄）",
        elements_desc="六爻营数 " + "·".join(str(v) for v in values),
        question=st["命辞"],
        process={"开始时间": st["开始时间"], "十八变": st["完成爻"],
                 "承诺方式": "每变映射经 SHA-256 加盐封存于选前，揭示后可复验"},
        ben_bin=ben_bin, mask=mask, values=values,
    )
    jpath, tpath = save_record(record, args.outdir)
    save_state(args.state, st)
    print(render_guadan(record))
    print()
    print(f"档案已写入：{jpath}")
    print(f"卦单已写入：{tpath}")
    print("── 本爻揭示 ──")
    print(json.dumps(reveal, ensure_ascii=False, indent=1))
    print("── JSON ──")
    print(json.dumps(record, ensure_ascii=False, indent=1))


def cmd_status(args):
    st = load_state(args.state)
    if not st:
        fail("尚未开局。")
    pub = {"状态": st["状态"], "命辞": st["命辞"], "当前爻": st["当前爻"],
           "已成爻": [{"爻位": e["爻位"], "营数": e["营数"], "老少": e["老少"]}
                     for e in st["完成爻"]]}
    if st["状态"] == "进行中":
        pub["本轮"] = public_round(st["当前爻"], st["pending"])
    print(json.dumps(pub, ensure_ascii=False, indent=1))


def cmd_commits(args):
    st = load_state(args.state)
    if not st or st.get("状态") != "进行中":
        fail("当前没有进行中的一局。")
    print(json.dumps({"爻位": st["当前爻"],
                      "承诺": [{"变": p["变"], "主题": p["主题"], "选项": p["选项"],
                               "承诺哈希": p["承诺"]} for p in st["pending"]],
                      "说明": "揭示时将给出映射与盐；对 {爻,变,主题,选项,映射,盐} 的"
                             "规范 JSON 求 SHA-256 应等于此哈希。"},
                     ensure_ascii=False, indent=1))


def cmd_reset(args):
    if os.path.exists(args.state):
        os.remove(args.state)
    print(json.dumps({"局": "已作废"}, ensure_ascii=False))


def cmd_selftest(args):
    """三种选择策略 × N 次成卦：分布应同回经典概率 1/16·5/16·7/16·3/16。"""
    theory = {6: 1 / 16, 7: 5 / 16, 8: 7 / 16, 9: 3 / 16}
    strategies = {
        "永远选第一个": lambda k: 0,
        "均匀随机选": lambda k: RNG.randrange(4),
        "轮转固定选": lambda k: k % 4,
    }
    print(f"蒙特卡洛自检：每策略 {args.n} 次成卦（{args.n * 6} 爻）")
    ok = True
    for name, pickfn in strategies.items():
        tally = {6: 0, 7: 0, 8: 0, 9: 0}
        for i in range(args.n):
            for _ in range(6):
                residues = []
                for k in range(3):
                    residue_of = [0, 1, 2, 3]
                    RNG.shuffle(residue_of)      # 洗牌 = 映射
                    residues.append(residue_of[pickfn(k)])
                v, _tr = resolve_yao(residues)
                tally[v] += 1
        total = args.n * 6
        row = []
        for v in (6, 7, 8, 9):
            p = tally[v] / total
            diff = abs(p - theory[v])
            ok = ok and diff < 0.01
            row.append(f"{v}:{p:.4f}(理论{theory[v]:.4f})")
        print(f"  {name:8s} " + "  ".join(row))
    print("结论：", "通过——分布与选择策略无关，回归大衍经典概率。" if ok else "未通过！")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--outdir", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start"); p.add_argument("--question", default=None)
    p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_start)
    p = sub.add_parser("pick"); p.add_argument("choices", nargs=3)
    p.set_defaults(fn=cmd_pick)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("commits").set_defaults(fn=cmd_commits)
    sub.add_parser("reset").set_defaults(fn=cmd_reset)
    p = sub.add_parser("selftest"); p.add_argument("--n", type=int, default=20000)
    p.set_defaults(fn=cmd_selftest)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
