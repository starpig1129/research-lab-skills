# research-lab-skills

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/starpig1129/research-lab-skills/releases/tag/v1.0.0)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)

[简体中文版](README.zh-CN.md) | [繁體中文版](README.zh-TW.md) | [日本語版](README.ja-JP.md)

---

## Why this project exists

Research has two distinct lives that rarely speak to each other.

The first is the **daily process** — the experiment that ran overnight, the chart that finally made sense, the decision to pivot the architecture, the slide you made for Friday's lab meeting. This layer is invisible in most publications, yet it's where most of the actual thinking happens.

The second is the **formal output** — the systematic literature review, the paper draft that survives three rounds of peer review, the citation that actually supports the claim it's attached to. This layer is where the field accumulates knowledge, but it's often disconnected from the messy reality of how that knowledge was reached.

I originally built the **lab skills** (`research-log`, `report-slides`, `research-mode`) to capture the first layer: a structured experiment journal, a slide generator that turns those journal entries into progress presentations, and a session mode system that remembers what kind of work you're doing. The goal was to make the research *process* legible — to yourself, your advisor, your collaborators.

[Cheng-I Wu](https://github.com/Imbad0202) independently built **Academic Research Skills** (ARS) to systematise the second layer: a 13-agent deep research engine with PRISMA support and four-index citation verification, a 12-agent paper writing system with citation anchors and figure fidelity gates, a multi-perspective peer review system, and a 10-stage pipeline orchestrator that chains them all together.

When I found ARS, the complementarity was immediate. The lab skills record *where you've been*; ARS structures *where you're going*. The experiment journal feeds the paper's methodology section. The progress slides become the draft's figures. The session modes (`exp` → `explore` → `publish`) map directly onto the research lifecycle ARS was designed to handle. The `report-slides` skill even supports `--source academic` to pull directly from ARS's Material Passport.

These two systems don't just sit side by side — they're designed for the same researcher at different stages of the same project. Merging them into one repo with one install command is the natural conclusion.

This is that merged project.

---

| Skill | Command | Purpose |
|-------|---------|---------|
| `research-log` | `/research-log` | Structured experiment journal (daily logs, amendments, index) |
| `report-slides` | `/report-slides` | SVG + PPTX progress presentations from journal entries |
| `research-mode` | `/mode` | Session mode routing (exp / daily / explore / report / publish) |
| `deep-research` | `/ars-full`, `/ars-lit-review`, … | 13-agent research team with Socratic mode, PRISMA, fact-check |
| `academic-paper` | `/ars-plan`, `/ars-outline`, … | 12-agent paper writing with citation verification |
| `academic-paper-reviewer` | `/ars-review`, `/ars-re-review` | Multi-perspective peer review (EIC + 3 reviewers + DA) |
| `academic-pipeline` | `/ars-pipeline` | Full 10-stage pipeline orchestrator |

---

## The integrated research lifecycle

These skills are not a feature list — they're a workflow. Each one was designed for a specific phase of research and hands off naturally to the next.

**Phase 1 — Daily experiment work** (`/mode exp`)

```bash
/mode exp                       # start an experiment session
/research-log add               # log today's work (quick: 3 questions; full: 9 sections)
/report-slides                  # turn this week's journal into a progress presentation
/mode end                       # draft the next entry from today's git diff
```

The journal's `follows:` field links experiments into a traceable timeline. `amended:` records post-hoc corrections. `slide_decks:` updates automatically when slides are generated. These entries are the raw material for your methodology section when you eventually write the paper — capturing not just what worked, but why you tried it and what failed first.

**Phase 2 — Literature exploration** (`/mode explore`)

```bash
/mode explore
/ars-lit-review "your topic"    # 13-agent literature review with PRISMA support
/ars-socratic                   # Socratic dialogue to sharpen your research question
/mode end                       # extract RQ + key findings into the log
```

**Phase 3 — Writing and publication** (`/mode publish`)

```bash
/mode publish
/ars-plan                       # Socratic-guided chapter planning
/ars-full                       # 12-agent paper writing + citation verification
/ars-review                     # multi-perspective peer review (EIC + 3 reviewers + DA)
/ars-re-review                  # post-revision acceptance check
/ars-pipeline                   # full 10-stage orchestrated pipeline with integrity gates
```

**How the journal connects to the paper**

| Journal field | Paper section |
|--------------|--------------|
| `Goal` + `Setup` | Methodology |
| `Results` + `Charts` | Results & Figures |
| `Failures` + `Analysis` | Discussion / Limitations |
| `slide_decks:` links | Figure sources |
| `follows:` timeline | Research design narrative |

→ See **[examples/](examples/)** for a complete worked example: three journal entries showing the messy week-by-week process (failures, `amended:` corrections, unresolved problems), a 7-slide lab-meeting progress deck generated from those logs, and the JSON data file that drove the charts. The SVG slides also ship as a `deck.pptx` — every element editable in PowerPoint or Keynote.

---

## Installation

### Global install — all skills (recommended)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/research-lab-skills/main/install.sh)
```

### Project-local install

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/research-lab-skills/main/install.sh) --local
```

### Install only academic research skills

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/research-lab-skills/main/install.sh) --ars-only
```

### Install only lab skills (research-log, report-slides, research-mode)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/research-lab-skills/main/install.sh) --lab-only
```

### Uninstall

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/research-lab-skills/main/install.sh) uninstall
```

Restart Claude Code after install.
Lab skills: `/research-log`, `/report-slides`, `/mode`
Academic skills: `/ars-plan`, `/ars-full`, `/ars-lit-review`, `/ars-review`, and more.

---

## Lab Skills

### `/research-log` — Experiment Journal

Manages a structured journal in `docs/research_log/` (one `.md` file per experiment).

| Command | Description |
|---------|-------------|
| `/research-log add` | Start quick (3 questions) or full (9 sections) guided entry |
| `/research-log amend` | Edit sections of an existing entry |
| `/research-log index` | Rebuild `docs/research_log/INDEX.md` from frontmatter |
| `/research-log show [n]` | Show compact summary of the last n entries (default 5) |

Each entry is a Markdown file with YAML frontmatter tracking `follows:` links between experiments and `slide_decks:` updated automatically when slides are generated.

---

### `/report-slides` — Presentation Generator

Reads journal entries, proposes a slide outline for confirmation, then generates slides via three rendering paths:

- **[A] Python script** — data-driven slides: bar charts, tables, metric cards, timelines
- **[B] Mermaid** — diagram slides: flowcharts, architecture diagrams, state machines
- **[C] Claude SVG** — free-form slides: conceptual layouts, text-heavy content

Output: `docs/slides/reports/YYYY-MM-DD_<deck-name>/`
- `slide01_title.svg`, `slide02_bar_chart.svg`, … (editable SVG source files)
- **`deck.pptx`** — 16:9 PPTX with native SVG embedding. Every title, number, colour, and layout element is directly editable in PowerPoint or Keynote — no roundtripping back to source code.
- `slide_data.json` (Path A source, use `--slide N` to re-render one slide)

**First-time project setup:**

```bash
bash "$(find ~/.claude -path "*/report-slides/scripts/setup.sh" | head -1)"
```

**Dependencies:**

```bash
pip install python-pptx
npm install -g @mermaid-js/mermaid-cli   # optional, Mermaid diagrams only
```

**Slide styles:** `default`, `minimal`, `dark`, `paper`

```bash
bash "$(find ~/.claude -path "*/report-slides/scripts/set-style.sh" | head -1)" paper
```

---

### `/mode` — Session Mode Routing

Declares active research mode to adjust which skills are prioritized and how sessions end:

| Mode | Primary Skills | Use when |
|------|---------------|----------|
| `exp` | `research-log` (Full) | Running experiments, want auto-log at session end |
| `daily` | none (freeform) | Lightweight notes, reading |
| `explore` | `deep-research` | Literature exploration |
| `report` | `report-slides` | Generating progress presentations |
| `publish` | `academic-pipeline` | Writing and submitting a paper |

End a session with `/mode end` to get a pre-filled journal entry draft.

---

## Academic Research Skills

> **AI is your copilot, not the pilot.** This tool won't write your paper for you. It handles the grunt work — hunting down references, formatting citations, verifying data, checking logical consistency — so you can focus on the parts that actually require your brain.

**👉 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — full pipeline view: flow diagram, stage-by-stage matrix, quality gates, and mode list.

**👉 [docs/SETUP.md](docs/SETUP.md)** — full setup guide: API keys, optional Pandoc/tectonic for DOCX/PDF, cross-model verification.

**👉 [docs/PERFORMANCE.md](docs/PERFORMANCE.md)** — per-mode token budgets, full-pipeline cost estimate (~$4–6 for a 15k-word paper).

### Features at a glance

- **Deep Research** (`/ars-full`, `/ars-lit-review`, `/ars-systematic-review`) — 13-agent research team. Socratic guided mode, PRISMA systematic review, four-index citation triangulation (Semantic Scholar + OpenAlex + Crossref + arXiv), cross-model DA critique.
- **Academic Paper** (`/ars-plan`, `/ars-outline`, `/ars-abstract`) — 12-agent paper writing. Style Calibration, Writing Quality Check, three-layer citation anchors, LaTeX hardening, VLM figure verification, revision coaching.
- **Academic Paper Reviewer** (`/ars-review`, `/ars-re-review`) — 7-agent peer review. EIC + 3 dynamic reviewers + Devil's Advocate, concession threshold protocol, opt-in calibration mode, R&R traceability matrix.
- **Academic Pipeline** (`/ars-pipeline`) — 10-stage end-to-end orchestrator. Integrity gates at Stage 2.5 + 4.5, Material Passport, citation existence gate, Collaboration Depth Observer, score trajectory tracking.

### Full pipeline

```
deep-research (socratic/full)
  → academic-paper (plan/full)
    → integrity check (Stage 2.5)
      → academic-paper-reviewer (full/guided)
        → academic-paper (revision)
          → academic-paper-reviewer (re-review, max 2 loops)
            → final integrity check (Stage 4.5)
              → academic-paper (format-convert → final output)
```

See **[examples/showcase/](examples/showcase/)** for artifacts from a complete 10-stage pipeline run (peer review reports, integrity checks, final papers).

---

## Examples

The [`examples/`](examples/) directory contains a complete worked scenario — an NLP researcher working on cross-lingual automated essay scoring across three weeks of experiments.

**Research journal** ([`examples/research-log/`](examples/research-log/)) — three entries showing the full arc: a quick baseline log on day one, a full entry mid-project with failures and a post-hoc `amended:` correction, and a final-week entry with two amendments and open questions. The `follows:` chain links them into a traceable timeline.

**Progress slides** ([`examples/report-slides/`](examples/report-slides/)) — a 7-slide weekly lab-meeting presentation generated from those journal entries. Slides cover: title, problem/approach, timeline (with `amended` badges), grouped bar chart, model comparison table (with DIF fairness markers), metric cards, and conclusion + next steps. All slides are SVG source files convertible to an editable `deck.pptx` — see [`examples/report-slides/README.md`](examples/report-slides/README.md) for the generation command.

---

## File Structure

```
docs/research_log/
  INDEX.md                              ← auto-generated (do not edit)
  2026-05-15_backbone_v3.md

docs/slides/
  _style.md                             ← project default style (optional)
  reports/
    2026-05-19_weekly/
      slide01_title.svg
      deck.pptx
      slide_data.json

scripts/
  generate_slides.py                    ← copied from skill on first use
  to_pptx.py
```

---

## Sources

- Lab skills (`research-log`, `report-slides`, `research-mode`) — [`starpig1129/research-lab-skills`](https://github.com/starpig1129/research-lab-skills) (CC BY-NC 4.0)
- Academic Research Skills (`deep-research`, `academic-paper`, `academic-paper-reviewer`, `academic-pipeline`) — originally [`Imbad0202/academic-research-skills`](https://github.com/Imbad0202/academic-research-skills) (CC BY-NC 4.0)

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for licensing details.
