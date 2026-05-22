# claude-research-skills

Two Claude Code skills for research teams:

| Skill | Command | Purpose |
|-------|---------|---------|
| research-log | `/research-log` | Log, amend, and query experiment journal entries |
| report-slides | `/report-slides` | Generate SVG + PPTX progress presentations from the journal |

---

## Installation

### Global install (all projects)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/claude-research-skills/main/install.sh)
```

### Project-local install

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/claude-research-skills/main/install.sh) --local
```

Restart Claude Code — `/research-log` and `/report-slides` will be available.

### Uninstall

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/claude-research-skills/main/install.sh) uninstall
```

---

## First-time project setup (report-slides only)

After installing the skills globally, run once per project to copy the helper scripts:

```bash
bash "$(find ~/.claude -path "*/report-slides/scripts/setup.sh" | head -1)"
```

Or just invoke `/report-slides` — it detects missing scripts and runs setup automatically.

---

## Dependencies

Install once per environment (only needed for `report-slides`):

```bash
pip install python-pptx
```

Optional (diagram slides via Mermaid):

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
- `deck.pptx` (16:9 PPTX with native SVG embedding)
- `slide_data.json` (Path A source, use `--slide N` to re-render one slide)
- `chart_list.md` (list of existing plot files to insert manually)

### Slide styles

Four built-in styles: `default`, `minimal`, `dark`, `paper`

```bash
# Set project default style (run from project root)
bash "$(find ~/.claude -path "*/report-slides/scripts/set-style.sh" | head -1)" paper
```

---

## File Structure

```
docs/research_log/
  INDEX.md                              ← auto-generated index (do not edit)
  2026-05-15_backbone_v3.md
  2026-05-18_finetune_v3.md

docs/slides/
  _style.md                             ← project default style (optional)
  reports/
    2026-05-19_weekly/
      slide01_title.svg
      slide02_bar_chart.svg
      deck.pptx
      slide_data.json
      chart_list.md

scripts/
  generate_slides.py                    ← copied from skill on first use
  to_pptx.py
```

---

## License

MIT
