# claude-research-skills

Two Claude Code skills for research teams:

| Skill | Command | Purpose |
|-------|---------|---------|
| research-log | `/research-log` | Log, amend, and query experiment journal entries |
| report-slides | `/report-slides` | Generate SVG + PPTX progress presentations from the journal |

---

## Installation

```bash
claude /plugins add github:starpig1129/claude-research-skills
```

Restart Claude Code — `/research-log` and `/report-slides` will be available in every project.

---

## Dependencies

Install once per environment (only needed for `report-slides`):

```bash
pip install python-pptx cairosvg
# fallback converters if cairosvg fails on your system:
# sudo apt install inkscape         # inkscape fallback
# sudo apt install librsvg2-bin    # rsvg-convert fallback
```

Optional (Path B diagram slides):

```bash
npm install -g @mermaid-js/mermaid-cli
```

---

## `/research-log` — Experiment Journal

Manages a structured journal in `docs/research_log/` (one `.md` file per experiment).

| Command | Description |
|---------|-------------|
| `/research-log add` | Start quick (3 questions) or full (9 sections) guided entry |
| `/research-log amend` | Edit sections of an existing entry |
| `/research-log index` | Rebuild `docs/research_log/INDEX.md` from frontmatter |
| `/research-log show [n]` | Show compact summary of the last n entries (default 5) |

Each entry is a Markdown file with YAML frontmatter tracking `follows:` links between experiments, and `slide_decks:` updated automatically when slides are generated.

---

## `/report-slides` — Presentation Generator

Reads journal entries, proposes a slide outline for confirmation, then generates slides via three rendering paths:

- **[A] Python script** — data-driven slides: bar charts, tables, metric cards, timelines
- **[B] Mermaid** — diagram slides: flowcharts, architecture diagrams, state machines
- **[C] Claude SVG** — free-form slides: conceptual layouts, text-heavy content

Output: `docs/slides/reports/YYYY-MM-DD_<deck-name>/`
- `slide01_title.svg`, `slide02_bar_chart.svg`, … (editable SVG source)
- `deck.pptx` (16:9 PPTX, each slide embedded as a high-res PNG)
- `slide_data.json` (Path A source, use `--slide N` to re-render one slide)
- `chart_list.md` (list of existing plot files to insert manually)

**Note:** PPTX slides are embedded images — to edit a slide, modify the SVG then re-run `--to-pptx`.

### First-time project setup

On first use in a new project, the skill copies `generate_slides.py` to `scripts/` automatically. No manual setup needed.

---

## File Structure

```
docs/research_log/
  INDEX.md                              ← auto-generated index (do not edit)
  2026-05-15_backbone_v3.md
  2026-05-18_finetune_v3.md

docs/slides/reports/
  2026-05-19_weekly/
    slide01_title.svg
    slide02_bar_chart.svg
    deck.pptx
    slide_data.json
    chart_list.md

scripts/
  generate_slides.py                    ← copied from skill on first use
```

---

## License

MIT
