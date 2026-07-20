# -*- coding: utf-8 -*-
"""
gua_core.py — 卦象确定性内核（唯一权威来源）
约定：六位二进制字符串，最左位为初爻（自下而上），1=阳爻，0=阴爻。
下卦 = 前三位，上卦 = 后三位。
本模块导入即自检：任何对照表被改错都会在 import 阶段抛出断言错误。
"""
import hashlib
import json
import os
from datetime import datetime

SCRIPT_VERSION = "0.2.1"
SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------- 八卦 --------
# 先天数 1-8 → 乾兑离震巽坎艮坤；bits 自下而上。
TRIGRAMS = {
    1: {"名": "乾", "象": "天", "符": "☰", "bits": "111"},
    2: {"名": "兑", "象": "泽", "符": "☱", "bits": "110"},
    3: {"名": "离", "象": "火", "符": "☲", "bits": "101"},
    4: {"名": "震", "象": "雷", "符": "☳", "bits": "100"},
    5: {"名": "巽", "象": "风", "符": "☴", "bits": "011"},
    6: {"名": "坎", "象": "水", "符": "☵", "bits": "010"},
    7: {"名": "艮", "象": "山", "符": "☶", "bits": "001"},
    8: {"名": "坤", "象": "地", "符": "☷", "bits": "000"},
}
# 结构性质互检：二进制值 == 8 - 先天数
for _n, _t in TRIGRAMS.items():
    assert _t["bits"] == format(8 - _n, "03b"), f"八卦编码错误: {_n} {_t}"

TRI_BY_NAME = {t["名"]: dict(t, 数=n) for n, t in TRIGRAMS.items()}
TRI_BY_BITS = {t["bits"]: dict(t, 数=n) for n, t in TRIGRAMS.items()}

# ------------------------------------------------------------ 六十四卦 --------
# (卦序, 卦名, 下卦, 上卦) —— 文王卦序
KING_WEN = [
    (1, "乾", "乾", "乾"), (2, "坤", "坤", "坤"), (3, "屯", "震", "坎"), (4, "蒙", "坎", "艮"),
    (5, "需", "乾", "坎"), (6, "讼", "坎", "乾"), (7, "师", "坎", "坤"), (8, "比", "坤", "坎"),
    (9, "小畜", "乾", "巽"), (10, "履", "兑", "乾"), (11, "泰", "乾", "坤"), (12, "否", "坤", "乾"),
    (13, "同人", "离", "乾"), (14, "大有", "乾", "离"), (15, "谦", "艮", "坤"), (16, "豫", "坤", "震"),
    (17, "随", "震", "兑"), (18, "蛊", "巽", "艮"), (19, "临", "兑", "坤"), (20, "观", "坤", "巽"),
    (21, "噬嗑", "震", "离"), (22, "贲", "离", "艮"), (23, "剥", "坤", "艮"), (24, "复", "震", "坤"),
    (25, "无妄", "震", "乾"), (26, "大畜", "乾", "艮"), (27, "颐", "震", "艮"), (28, "大过", "巽", "兑"),
    (29, "坎", "坎", "坎"), (30, "离", "离", "离"), (31, "咸", "艮", "兑"), (32, "恒", "巽", "震"),
    (33, "遁", "艮", "乾"), (34, "大壮", "乾", "震"), (35, "晋", "坤", "离"), (36, "明夷", "离", "坤"),
    (37, "家人", "离", "巽"), (38, "睽", "兑", "离"), (39, "蹇", "艮", "坎"), (40, "解", "坎", "震"),
    (41, "损", "兑", "艮"), (42, "益", "震", "巽"), (43, "夬", "乾", "兑"), (44, "姤", "巽", "乾"),
    (45, "萃", "坤", "兑"), (46, "升", "巽", "坤"), (47, "困", "坎", "兑"), (48, "井", "巽", "坎"),
    (49, "革", "离", "兑"), (50, "鼎", "巽", "离"), (51, "震", "震", "震"), (52, "艮", "艮", "艮"),
    (53, "渐", "艮", "巽"), (54, "归妹", "兑", "震"), (55, "丰", "离", "震"), (56, "旅", "艮", "离"),
    (57, "巽", "巽", "巽"), (58, "兑", "兑", "兑"), (59, "涣", "坎", "巽"), (60, "节", "兑", "坎"),
    (61, "中孚", "兑", "巽"), (62, "小过", "艮", "震"), (63, "既济", "离", "坎"), (64, "未济", "坎", "离"),
]


def _full_name(name, lower, upper):
    if lower == upper:
        return f"{name}为{TRI_BY_NAME[lower]['象']}"
    return f"{TRI_BY_NAME[upper]['象']}{TRI_BY_NAME[lower]['象']}{name}"


HEX_BY_BIN = {}
HEX_BY_NUM = {}
for _num, _name, _lo, _up in KING_WEN:
    _bin = TRI_BY_NAME[_lo]["bits"] + TRI_BY_NAME[_up]["bits"]
    info = {
        "卦序": _num,
        "卦名": _name,
        "全名": _full_name(_name, _lo, _up),
        "下卦": {"名": _lo, "象": TRI_BY_NAME[_lo]["象"], "符": TRI_BY_NAME[_lo]["符"]},
        "上卦": {"名": _up, "象": TRI_BY_NAME[_up]["象"], "符": TRI_BY_NAME[_up]["符"]},
        "二进制": _bin,
        "卦画符": chr(0x4DC0 + _num - 1),
    }
    HEX_BY_BIN[_bin] = info
    HEX_BY_NUM[_num] = info

# 结构互检：64 个卦、二进制两两不同且覆盖全部 6 位组合
assert len(HEX_BY_BIN) == 64, "六十四卦二进制存在重复"
assert set(HEX_BY_BIN) == {format(i, "06b") for i in range(64)}, "六十四卦未覆盖全部组合"
# 独立锚点抽检（凭已知常识硬编码，防整表错位）
_SPOT = {
    "111111": (1, "乾", "乾为天"), "000000": (2, "坤", "坤为地"),
    "100010": (3, "屯", "水雷屯"), "111000": (11, "泰", "地天泰"),
    "000111": (12, "否", "天地否"), "100000": (24, "复", "地雷复"),
    "101000": (36, "明夷", "地火明夷"), "001010": (39, "蹇", "水山蹇"),
    "101010": (63, "既济", "水火既济"), "010101": (64, "未济", "火水未济"),
}
for _b, (_n2, _nm, _fn) in _SPOT.items():
    _h = HEX_BY_BIN[_b]
    assert (_h["卦序"], _h["卦名"], _h["全名"]) == (_n2, _nm, _fn), f"卦表抽检失败: {_b} -> {_h}"

# ------------------------------------------------------------ 基本函数 --------
YINYANG = {"1": "阳", "0": "阴"}
LAOSHAO = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}
_POSNAME = ["初", "二", "三", "四", "五", "上"]


def hexagram(binary):
    """六位二进制 → 卦信息（复制一份，防调用方改动权威表）。"""
    assert isinstance(binary, str) and len(binary) == 6 and set(binary) <= {"0", "1"}, \
        f"非法卦码: {binary!r}"
    return json.loads(json.dumps(HEX_BY_BIN[binary], ensure_ascii=False))


def yao_title(pos, bit):
    """爻位(1-6) + 阴阳位 → 爻题（初九、六二、上六…）。"""
    num = "九" if bit == "1" else "六"
    if pos == 1:
        return f"初{num}"
    if pos == 6:
        return f"上{num}"
    return f"{num}{_POSNAME[pos - 1]}"


def lines_detail(binary, mask, values=None):
    """六爻明细（自下而上）。values 为筹策卦的营数列表，可为 None。"""
    out = []
    for i in range(6):
        item = {
            "爻位": i + 1,
            "爻题": yao_title(i + 1, binary[i]),
            "阴阳": YINYANG[binary[i]],
            "动": mask[i] == "1",
        }
        if values is not None:
            item["营数"] = values[i]
            item["老少"] = LAOSHAO[values[i]]
        out.append(item)
    return out


def xor(a, b):
    return "".join("1" if x != y else "0" for x, y in zip(a, b))


def hu_gua(b):
    """互卦：二三四爻为下，三四五爻为上。"""
    return b[1:4] + b[2:5]


def cuo_gua(b):
    """错卦：六爻皆反。"""
    return "".join("1" if c == "0" else "0" for c in b)


def zong_gua(b):
    """综卦：上下颠倒。"""
    return b[::-1]


# ------------------------------------------------------------ 朱子断例 --------
def quduan(ben_bin, mask):
    """按《易学启蒙》考变占，由掩码给出取断指引（确定性规则表）。"""
    n = mask.count("1")
    zhi_bin = xor(ben_bin, mask)
    moving = [i + 1 for i, c in enumerate(mask) if c == "1"]
    still = [i + 1 for i, c in enumerate(mask) if c == "0"]

    def ref(gua, kind, pos=None):
        r = {"卦": gua, "文本": kind}
        if pos is not None:
            r["爻位"] = pos
            r["爻题"] = yao_title(pos, (ben_bin if gua == "本卦" else zhi_bin)[pos - 1])
        return r

    if n == 0:
        return {"动爻数": 0, "断例": "六爻不变", "应据": [ref("本卦", "卦辞")],
                "为主": None, "说明": "占本卦卦辞。"}
    if n == 1:
        p = moving[0]
        r = ref("本卦", "爻辞", p)
        return {"动爻数": 1, "断例": "一爻变", "应据": [r], "为主": r,
                "说明": f"以本卦{r['爻题']}爻辞为断。"}
    if n == 2:
        refs = [ref("本卦", "爻辞", p) for p in moving]
        return {"动爻数": 2, "断例": "二爻变", "应据": refs, "为主": refs[-1],
                "说明": f"占本卦两动爻爻辞，以居上之{refs[-1]['爻题']}为主。"}
    if n == 3:
        refs = [ref("本卦", "卦辞"), ref("之卦", "卦辞")]
        return {"动爻数": 3, "断例": "三爻变", "应据": refs, "为主": refs[0],
                "说明": "占本卦及之卦卦辞，本卦为贞、之卦为悔。"}
    if n == 4:
        refs = [ref("之卦", "爻辞", p) for p in still]
        return {"动爻数": 4, "断例": "四爻变", "应据": refs, "为主": refs[0],
                "说明": f"占之卦两不变爻爻辞，以居下之{refs[0]['爻题']}为主。"}
    if n == 5:
        p = still[0]
        r = ref("之卦", "爻辞", p)
        return {"动爻数": 5, "断例": "五爻变", "应据": [r], "为主": r,
                "说明": f"占之卦不变爻{r['爻题']}爻辞。"}
    # n == 6
    if ben_bin == "111111":
        r = ref("本卦", "用九")
        return {"动爻数": 6, "断例": "六爻皆变（乾）", "应据": [r], "为主": r,
                "说明": "乾之坤，以用九占。"}
    if ben_bin == "000000":
        r = ref("本卦", "用六")
        return {"动爻数": 6, "断例": "六爻皆变（坤）", "应据": [r], "为主": r,
                "说明": "坤之乾，以用六占。"}
    r = ref("之卦", "卦辞")
    return {"动爻数": 6, "断例": "六爻皆变", "应据": [r], "为主": r,
            "说明": "六爻皆变，占之卦卦辞。"}


# ------------------------------------------------------------ 经文数据 --------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
ZHOUYI_PATH = os.path.normpath(os.path.join(DATA_DIR, "zhouyi.json"))


def load_zhouyi():
    with open(ZHOUYI_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def zhouyi_checksum():
    with open(ZHOUYI_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def collect_texts(zy, ben_bin, mask):
    """按『宁滥勿缺』原则汇集经文：本卦全套、全部动爻、之卦全套、断例特需条目。"""
    zhi_bin = xor(ben_bin, mask)
    jing = zy[ben_bin]
    out = {"本卦": {"卦辞": jing["卦辞"], "彖传": jing["彖传"], "大象": jing["大象"]},
           "动爻": [], "之卦": None, "特例": {}}
    for i, c in enumerate(mask):
        if c == "1":
            y = jing["爻"][i]
            out["动爻"].append({"爻题": y["爻题"], "爻辞": y["爻辞"], "小象": y["小象"]})
    if mask != "000000":
        zj = zy[zhi_bin]
        out["之卦"] = {"卦辞": zj["卦辞"], "彖传": zj["彖传"], "大象": zj["大象"]}
    qd = quduan(ben_bin, mask)
    for r in qd["应据"]:
        if r["文本"] == "用九":
            out["特例"]["用九"] = jing.get("用九")
        elif r["文本"] == "用六":
            out["特例"]["用六"] = jing.get("用六")
        elif r["文本"] == "爻辞" and r["卦"] == "之卦":
            y = zy[zhi_bin]["爻"][r["爻位"] - 1]
            out["特例"].setdefault("之卦不变爻", []).append(
                {"爻题": y["爻题"], "爻辞": y["爻辞"], "小象": y["小象"]})
    return out


# ------------------------------------------------------------ 卦单渲染 --------
_BAR = {"1": "▅▅▅▅▅", "0": "▅▅　▅▅"}


def render_lines(binary, mask, values=None):
    """自上而下的六爻图（列表），动阳标○、动阴标×。"""
    rows = []
    for i in range(5, -1, -1):
        mark = ""
        if mask[i] == "1":
            mark = "  ○ 动" if binary[i] == "1" else "  × 动"
        tail = f"（{values[i]}·{LAOSHAO[values[i]]}）" if values is not None else ""
        rows.append(f"{yao_title(i + 1, binary[i])} {_BAR[binary[i]]}{mark}{tail}")
    return rows


def render_guadan(record):
    """由完整档案渲染人读卦单。"""
    ben, zhi, dong = record["本卦"], record["之卦"], record["动爻"]
    texts = record["经文"]
    values = None
    if record["meta"]["起卦方式"].startswith("筹策卦"):
        values = [y["营数"] for y in ben["六爻"]]
    L = []
    L.append("═" * 34)
    L.append("　　　　　　　卦　单")
    L.append("═" * 34)
    if dong["是否静卦"]:
        L.append(f"{ben['卦名']} {ben['卦画符']}　（六爻安静）")
    else:
        L.append(f"{ben['卦名']} {ben['卦画符']} 之 {zhi['卦名']} {zhi['卦画符']}")
    L.append(f"起卦　{record['meta']['起卦方式']}")
    if record["meta"].get("起卦要素"):
        L.append(f"　　　{record['meta']['起卦要素']}")
    L.append(f"时间　{record['meta']['时间戳']}")
    L.append(f"所占　{record['meta']['命辞'] or '（未具）'}")
    L.append("─" * 34)
    binary = ben["二进制"]
    mask = dong["掩码"]
    L.extend(render_lines(binary, mask, values))
    L.append("─" * 34)
    L.append(f"本卦　{ben['全名']}（第{ben['卦序']}卦）　{ben['上卦']['名']}上{ben['下卦']['名']}下")
    L.append(f"卦辞　{texts['本卦']['卦辞']}")
    for y in texts["动爻"]:
        L.append(f"{y['爻题']}　{y['爻辞']}")
    if zhi is not None:
        L.append(f"之卦　{zhi['全名']}（第{zhi['卦序']}卦）　{zhi['上卦']['名']}上{zhi['下卦']['名']}下")
        L.append(f"卦辞　{texts['之卦']['卦辞']}")
    for k, v in texts["特例"].items():
        if k in ("用九", "用六") and v:
            L.append(f"{k}　{v['辞']}")
        elif k == "之卦不变爻":
            for y in v:
                L.append(f"之卦{y['爻题']}　{y['爻辞']}")
    sh = record["衍生"]
    L.append(f"互卦　{sh['互卦']['全名']}　错卦　{sh['错卦']['全名']}　综卦　{sh['综卦']['全名']}")
    L.append(f"取断　{record['取断']['断例']}：{record['取断']['说明']}")
    L.append("═" * 34)
    return "\n".join(L)


# ------------------------------------------------------------ 档案组装 --------
def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def build_record(mode, elements_desc, question, process, ben_bin, mask, values=None):
    """统一档案组装：数字卦与筹策卦共用。"""
    zhi_bin = xor(ben_bin, mask)
    is_still = mask == "000000"
    zy = load_zhouyi()
    ben = hexagram(ben_bin)
    ben["六爻"] = lines_detail(ben_bin, mask, values)
    zhi = None
    if not is_still:
        zhi = hexagram(zhi_bin)
        zhi["六爻"] = lines_detail(zhi_bin, "000000")
    record = {
        "meta": {
            "档案版本": SCHEMA_VERSION,
            "脚本版本": SCRIPT_VERSION,
            "起卦方式": mode,
            "起卦要素": elements_desc,
            "时间戳": now_iso(),
            "命辞": question,
            "数据校验和": zhouyi_checksum(),
        },
        "过程": process,
        "本卦": ben,
        "动爻": {
            "数目": mask.count("1"),
            "爻位": [i + 1 for i, c in enumerate(mask) if c == "1"],
            "掩码": mask,
            "是否静卦": is_still,
        },
        "之卦": zhi,
        "衍生": {
            "互卦": hexagram(hu_gua(ben_bin)),
            "错卦": hexagram(cuo_gua(ben_bin)),
            "综卦": hexagram(zong_gua(ben_bin)),
        },
        "取断": quduan(ben_bin, mask),
        "经文": collect_texts(zy, ben_bin, mask),
        "断言": {"通过": True},
    }
    return record


def save_record(record, outdir):
    os.makedirs(outdir, exist_ok=True)
    ben = record["本卦"]["卦名"]
    tail = "静" if record["动爻"]["是否静卦"] else f"之{record['之卦']['卦名']}"
    stamp = record["meta"]["时间戳"].replace(":", "").replace("-", "").replace("+", "p")
    base = f"gua_{stamp}_{ben}{tail}"
    jpath = os.path.join(outdir, base + ".json")
    tpath = os.path.join(outdir, base + ".txt")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=1)
    with open(tpath, "w", encoding="utf-8") as f:
        f.write(render_guadan(record))
    return jpath, tpath


if __name__ == "__main__":
    print(f"gua_core {SCRIPT_VERSION}：对照表自检通过（64卦、8卦、锚点抽检均正常）。")
    print("示例：", HEX_BY_BIN["101000"]["全名"], HEX_BY_BIN["101000"]["卦画符"],
          "互卦→", HEX_BY_BIN[hu_gua("101000")]["全名"])
