# 周易占筮 Claude 技能集 · I Ching Divination Skills for Claude

[中文](#中文) | [English](#english)

---

## 中文

本仓库收录一组配套的 Claude 技能（Agent Skills），围绕《周易》占筮分工协作：

| 技能 | 职责 |
|---|---|
| [`suangua/`](suangua/)（算卦） | **只起卦**：推演卦象，呈现本卦、动爻、之卦与经文原文 |
| [`jiegua/`](jiegua/)（解卦） | **只解卦**：接过已起出的卦，解读卦义并落到问卦人的事上 |

两者一起一解、首尾相接：算卦交出卦单与 JSON 档案，解卦以此为全部输入。也可各自单独安装使用。

### 算卦（suangua）——起卦专职

所有卦象推演均由 `scripts/` 下的确定性 Python 脚本完成，经文一律引自 `data/zhouyi.json` 的《周易》结构化文本——Claude 不心算卦象、不凭记忆背经文，每一卦可复现、可对账。支持两种起卦方式：

- **数字卦** —— 心中默想三个 000–999 的数字，取余法即刻成卦；
- **筹策卦（大衍筮法）** —— 完整模拟"大衍之数五十，其用四十有九"的十八变筮法，六爻六轮、每轮三变，用户以四元素抓阄参与每一变。内置 **SHA-256 承诺哈希机制**：元素映射在用户选择前已锁定，揭示后可复算对账，保证公平。

产出可读的 `.txt` 卦单与带校验和的 `.json` 档案。它只呈卦，不做任何吉凶解读。

### 解卦（jiegua）——解读专职

接过算卦的卦单（或用户自带的外来卦，用 `scripts/chagua.py` 查经文、推之卦、出朱子断例），以三件工具解读：**以辞为体**（从主断之辞出发）、**以象为境**（内外卦读作"我"与"世界"）、**以变为时**（之卦讲下一步，动爻位置估节奏）。

解读遵循四条心法：解卦给的是**视角而非判决**——每次必交付一个对方没想到的角度、一两个能使劲的方向、一个开放的问题；吉凶永远在流转，不铁口直断、不恐吓、不打包票；健康、法律、大额钱财之事明确以专业意见为准。

### 安装使用

**Claude Code：** 克隆仓库，把需要的技能目录放入技能目录（个人级 `~/.claude/skills/`，项目级 `.claude/skills/`）：

```bash
git clone https://github.com/SongJunxi2000/suangua.git
cp -R suangua/suangua ~/.claude/skills/suangua
cp -R suangua/jiegua  ~/.claude/skills/jiegua
```

**claude.ai：** 将某个技能目录（如 `suangua/`）单独打包为 zip 并改后缀为 `.skill`，在 Settings → Capabilities 中上传。

之后对 Claude 说"帮我算一卦"即可起卦；卦成之后追问"这卦什么意思 / 是吉是凶"，解卦技能自动接手。

> 依赖：Python 3，无第三方库。

---

## English

This repository hosts a pair of complementary Claude Agent Skills that divide the work of I Ching (Yijing / Book of Changes) divination:

| Skill | Role |
|---|---|
| [`suangua/`](suangua/) ("cast") | **Casting only**: derives the hexagram and presents the primary hexagram, moving lines, derived hexagram, and verbatim classical text |
| [`jiegua/`](jiegua/) ("interpret") | **Interpretation only**: takes an already-cast hexagram and reads it in the context of the querent's actual question |

They form a pipeline — suangua outputs a hexagram sheet and a JSON record, which is jiegua's complete input — but each can also be installed and used on its own.

### suangua — the caster

All hexagram derivation is done by deterministic Python scripts under `scripts/`; every quoted passage comes verbatim from the structured Zhouyi text in `data/zhouyi.json`. Claude never computes hexagrams mentally or recites the classics from memory, so every cast is reproducible and auditable. Two casting methods:

- **Number method (数字卦)** — silently pick three numbers between 000–999; a hexagram is derived instantly via modular arithmetic.
- **Yarrow-stalk method (大衍筮法)** — a full simulation of the classical 18-operation yarrow-stalk ritual: six rounds (one per line), three operations each, with the user participating by choosing among four elements. A built-in **SHA-256 commitment-hash scheme** locks each mapping *before* the user chooses; after the reveal anyone can recompute the hash to verify fairness.

Outputs a human-readable `.txt` hexagram sheet and a checksummed `.json` record. It presents the hexagram only — no judgment of fortune.

### jiegua — the interpreter

Takes suangua's hexagram sheet (or a hexagram cast elsewhere — `scripts/chagua.py` looks up the text, derives the changed hexagram, and applies Zhu Xi's line-selection rules) and interprets with three tools: **the text as skeleton** (start from the governing line statement), **the imagery as setting** (inner/outer trigrams read as "self" and "world"), and **the change as timing** (the derived hexagram is the next chapter; the moving line's position sets the tempo).

Its guiding principles: an interpretation offers **perspective, not verdict** — every reading must deliver an angle the querent hadn't considered, one or two concrete levers to act on, and an open question; fortune is always in flux, so no absolute pronouncements, no scaremongering, no guarantees; for health, legal, or major financial matters, professional advice explicitly comes first.

### Installation & usage

**Claude Code:** clone the repo and copy the skill directories you want into your skills directory (`~/.claude/skills/` for personal use, `.claude/skills/` for a project):

```bash
git clone https://github.com/SongJunxi2000/suangua.git
cp -R suangua/suangua ~/.claude/skills/suangua
cp -R suangua/jiegua  ~/.claude/skills/jiegua
```

**claude.ai:** zip an individual skill directory (e.g. `suangua/`), rename the archive to `.skill`, and upload it under Settings → Capabilities.

Then just ask Claude to cast a hexagram ("帮我算一卦" / "cast a hexagram for me"); once cast, ask what it means and the jiegua skill takes over.

> Requirements: Python 3, no third-party packages.
