# 算卦 suangua

[中文](#中文) | [English](#english)

---

## 中文

### 这是什么

**suangua（算卦）** 是一个 Claude 技能（Agent Skill），专职为用户**起卦占筮**。所有卦象推演均由 `scripts/` 下的确定性 Python 脚本完成，经文一律引自 `data/zhouyi.json` 中的《周易》文本——Claude 不心算卦象、不凭记忆背诵经文，保证每一卦可复现、可对账。

本技能**只管起卦，不管解卦**：它呈现本卦、动爻、之卦、卦辞爻辞与朱子断例取断指引，但不做任何吉凶解读——解卦由另一专职 agent 负责。

### 功能

支持两种起卦方式：

- **数字卦** —— 用户心中默想三个 000–999 的数字，脚本按取余法即刻成卦；
- **筹策卦（大衍筮法）** —— 完整模拟"大衍之数五十，其用四十有九"的十八变筮法。六爻六轮，每轮三变，用户以四元素抓阄的方式参与每一变。脚本内置**承诺哈希（commitment hash）机制**：每变的元素映射在用户选择前已以 SHA-256 承诺锁定，揭示后可复算对账，保证公平、不可作弊。

每卦结束后输出可读的 `.txt` 卦单与完整的 `.json` 档案（含数据校验和），档案即后续解卦所需的全部输入。

### 仓库结构

```
SKILL.md          技能入口：触发条件与起卦流程规范
scripts/          确定性起卦脚本（数字卦、筹策卦、数据构建与校验）
data/zhouyi.json  《周易》全文结构化数据（卦辞、彖、象、爻辞等）
data/qa_report.md 文本勘误与版本差异记录
references/       系辞、说卦、序卦、杂卦等参考文献
```

### 如何使用

**Claude Code：** 克隆到技能目录即可（个人级用 `~/.claude/skills/`，项目级用 `.claude/skills/`）：

```bash
git clone https://github.com/SongJunxi2000/suangua.git ~/.claude/skills/suangua
```

**claude.ai：** 将本仓库内容打包为 zip 并改后缀为 `.skill`，在 Settings → Capabilities 中上传。

之后对 Claude 说"帮我算一卦"“占一占这件事”“起个卦"等即可触发。Claude 会先问所占何事（命辞，可不答），再让你选数字卦或筹策卦，随后按流程成卦并交付卦单。

> 依赖：Python 3，无第三方库。

---

## English

### What is this

**suangua** ("casting divination" in Chinese) is a Claude Agent Skill dedicated to **casting I Ching (Yijing / Book of Changes) hexagrams**. All hexagram derivation is done by deterministic Python scripts under `scripts/`, and every quoted passage comes verbatim from the structured Zhouyi text in `data/zhouyi.json` — Claude never computes hexagrams mentally or recites the classics from memory, so every cast is reproducible and auditable.

This skill **only casts the hexagram; it does not interpret it**. It presents the primary hexagram, moving lines, the derived hexagram, the relevant classical texts, and Zhu Xi's line-selection rules for reading — but offers no judgment of fortune. Interpretation is delegated to a separate agent.

### Features

Two casting methods are supported:

- **Number method (数字卦)** — the user silently picks three numbers between 000–999; the script derives a hexagram instantly via modular arithmetic.
- **Yarrow-stalk method (大衍筮法)** — a full simulation of the classical 18-operation yarrow-stalk ritual ("the great expansion number is fifty, of which forty-nine are used"). Six rounds (one per line), three operations per round, with the user participating in each operation by choosing among four elements. A built-in **commitment-hash scheme** locks each operation's element mapping with SHA-256 *before* the user chooses; after the reveal, anyone can recompute the hash to verify fairness — no cheating possible.

Each cast produces a human-readable `.txt` hexagram sheet and a complete `.json` record (with data checksums) — the record is the full input needed by any downstream interpretation agent.

### Repository layout

```
SKILL.md          Skill entry point: triggers and casting workflow
scripts/          Deterministic casting scripts (number method, yarrow-stalk method, data build & validation)
data/zhouyi.json  Full structured Zhouyi text (judgments, commentaries, line statements)
data/qa_report.md Text errata and edition-difference records
references/       Reference texts: Xici, Shuogua, Xugua, Zagua
```

### How to use

**Claude Code:** clone into your skills directory (`~/.claude/skills/` for personal use, `.claude/skills/` for a project):

```bash
git clone https://github.com/SongJunxi2000/suangua.git ~/.claude/skills/suangua
```

**claude.ai:** zip the repository contents, rename the archive to `.skill`, and upload it under Settings → Capabilities.

Then simply ask Claude for a divination (e.g. "cast a hexagram for me" / "帮我算一卦"). Claude will ask what your question is (optional), let you choose a casting method, walk you through the ritual, and deliver the hexagram sheet and record.

> Requirements: Python 3, no third-party packages.
