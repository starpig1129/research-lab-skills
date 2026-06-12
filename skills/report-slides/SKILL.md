---
name: report-slides
description: Generate SVG presentation slides for research progress reports from research log entries, then optionally export to PPTX. Use when the user wants to make slides, create a presentation, or produce a visual report from experiment logs. Triggers on "make slides", "create presentation", "report slides", "generate deck", "export to pptx". Reads docs/research_log/ entries, proposes a slide outline for user confirmation, then generates files. Suggest /research-log add first if new experiments have not been logged yet.
metadata:
  data_access_level: raw
  task_type: open-ended
---

# Report Slides

Generates a slide deck from research log entries using three rendering paths:
- **[A]** `generate_slides.py` — data-driven slides (charts, tables, metrics)
- **[B]** Mermaid (`mmdc`) — diagram slides (flowcharts, architectures, state machines)
- **[C]** Claude SVG — free-form slides (conceptual layouts, text-heavy content)

After generation, slides can optionally be packaged into a PPTX with native SVG embedding.

---

## Setup (first use in a project)

**macOS / Linux / Git Bash:**
```bash
bash "$(find ~/.claude -path "*/report-slides/scripts/setup.sh" | head -1)"
```

**Windows (PowerShell):**
```powershell
& (Get-ChildItem $env:USERPROFILE\.claude -Recurse -Filter setup.ps1 |
    Where-Object FullName -like "*report-slides*" | Select-Object -First 1).FullName
```

This copies `generate_slides.py` into `scripts/` and creates `docs/slides/reports/`. `to_pptx.py` stays in the skill bundle and is invoked directly from there.

**Auto-setup:** if you invoke `/report-slides` and `scripts/generate_slides.py` is missing, run the appropriate setup command automatically before proceeding — no need to ask the user.

Check for Mermaid (optional, for diagram slides):
```bash
# macOS / Linux
which mmdc && echo "Mermaid OK" || echo "Mermaid missing (npm i -g @mermaid-js/mermaid-cli)"
# Windows
Get-Command mmdc -ErrorAction SilentlyContinue && "Mermaid OK" || "Mermaid missing (npm i -g @mermaid-js/mermaid-cli)"
```

---

## Style system

Slides inherit colors and fonts from a **style file** — a `.md` file with YAML frontmatter.
Three built-in styles ship with this skill: `default`, `minimal`, `dark`, `paper`.
Full schema and color role descriptions are in `references/styles/STYLES.md` (read it when resolving styles).

**Project default:** if `docs/slides/_style.md` exists it is applied automatically to every deck.

### set-style \<name\>

Copy a built-in style as the project default (one command):

```bash
# macOS / Linux / Git Bash:
bash "$(find ~/.claude -path "*/report-slides/scripts/set-style.sh" | head -1)" <name>
# Windows (PowerShell):
& (Get-ChildItem $env:USERPROFILE\.claude -Recurse -Filter set-style.ps1 |
    Where-Object FullName -like "*report-slides*" | Select-Object -First 1).FullName <name>
# built-in names: default  minimal  dark  paper
```

To **create a custom style**: make `docs/slides/styles/<name>.md` using the schema in
`references/styles/STYLES.md`, then copy it to `docs/slides/_style.md` to activate it as the project default.

---

## Workflow

### 1. Show available logs

```bash
cat docs/research_log/INDEX.md 2>/dev/null \
  || find docs/research_log -maxdepth 1 -name "*.md" ! -name "INDEX.md" | sort -r | head -20
```

Show the user which entries exist and which have already been made into slide decks.
If no log files exist, tell the user to run `/research-log add` first and stop.

---

### 1b. Academic data source (optional)

When the user passes `--source academic` or selects "academic pipeline" as source:

1. Check for a passport YAML file (default: `docs/passport.yaml`; override with `--passport <path>`)
2. Run the bridge script to extract stage data:
   ```bash
   BRIDGE="$(find ~/.claude -path "*/research-lab-skills/bridge/scripts/passport_to_log.py" 2>/dev/null | head -1)"
   python "$BRIDGE" --passport docs/passport.yaml
   ```
3. Use the extracted stage records as input for slide generation instead of research-log entries

If no passport file exists, fall back to research-log source and notify the user.

---

### 2. Ask (one message)

1. Source? (`research-log` = experiment logs (default) / `academic` = pipeline passport data)
   If research-log: which logs? (`all` / `recent-N` / by name / date range)
   If academic: passport file path? (default: `docs/passport.yaml`)
2. Audience? (advisor / team meeting / conference)
3. Charts? (`list` = output paths to `chart_list.md` / `embed` = base64 into SVG)
4. Language? (follow log language / force English / force another language)
5. Emphasis? (progression / final results / failure analysis / let Claude decide)
6. Style? (skip = use `docs/slides/_style.md` if present / name a built-in / `custom` to create one)

---

### 3. Read logs and propose outline

Read the selected log files and any `CLAUDE.md` for project context and baselines.

Analyze: `follows:` chains for progression, key results, failures, narrative arc.

**Propose the outline — wait for confirmation before generating:**

```
Proposed slide structure (N slides):

#01  Title                   [C]
#02  Background & Goal       [C: two_column]
#03  Experiment Timeline     [B: Mermaid]
#04  Changes                 [A: bullet_list]
#05  Results                 [A: bar_chart]
#06  Comparison              [A: table]
#07  Architecture            [B: Mermaid]
#08  Conclusion & Next Steps [C: conclusion]

[A] Python  [B] Mermaid  [C] Claude SVG

Confirm? (say "ok" to proceed, or specify changes)
```

**Dynamic inclusion rules:**
- Timeline: only with ≥2 entries linked via `follows:`
- Architecture: only if logs describe structural/model changes
- Failure slide: only if logs have content under `## Failures`
- Fewer slides (4–5) for single-entry logs; more for conference talks

---

### 3.5 Resolve style

Before generating, determine which style file to use and export `STYLE_FILE`:

```bash
STYLE_FILE=""
[ -f docs/slides/_style.md ] && STYLE_FILE="docs/slides/_style.md"
```

If the user named a style in Q6, search in order:
1. `docs/slides/styles/<name>.md` (project-local)
2. Skill bundle `styles/<name>.md` (built-in)

Set `STYLE_FILE` to whichever path exists. If the user chose `custom`, read `references/styles/STYLES.md`
and ask for the required frontmatter values, then write `docs/slides/styles/<name>.md`.

---

### 4. Generate slides

Output directory: `docs/slides/reports/YYYY-MM-DD_<name>/`

---

#### [A] Python renderer

**Supported types:** `title` `bullet_list` `bar_chart` `table` `metric_cards` `two_column` `timeline` `conclusion` `score_trajectory` `pipeline_status`

Write `slide_data.json` then run:
```bash
python scripts/generate_slides.py --data <dir>/slide_data.json --out <dir>/ \
    ${STYLE_FILE:+--style "$STYLE_FILE"}
# Re-render one slide:
python scripts/generate_slides.py --data <dir>/slide_data.json --out <dir>/ --slide N \
    ${STYLE_FILE:+--style "$STYLE_FILE"}
```

**JSON format:**
```json
{
  "meta": {
    "experiment": "<deck-name>",
    "date": "YYYY-MM-DD",
    "footer": "<name> · YYYY-MM-DD"
  },
  "slides": [
    { "index": 1, "type": "title",
      "title": "...", "subtitle": "...", "author": "...", "date": "YYYY-MM-DD" },

    { "index": 2, "type": "bar_chart",
      "title": "...", "categories": ["A", "B"],
      "series": [
        { "label": "baseline", "color": "#d97706", "values": [72.1, 81.6] },
        { "label": "this run", "color": "#059669", "values": [98.4, 100.0] }
      ],
      "y_max": 100, "note": "n=..." },

    { "index": 3, "type": "table",
      "title": "...", "columns": ["Metric", "Before", "After", "Delta"],
      "rows": [["Accuracy", "81.6%", "100%", "+18.4%"]],
      "highlight_col": 3 },

    { "index": 4, "type": "metric_cards",
      "title": "...", "metrics": [
        { "label": "Overall", "value": "99.8%", "color": "#059669", "change": "+27%" }
      ]},

    { "index": 5, "type": "timeline",
      "title": "...", "events": [
        { "label": "v1 baseline", "date": "2024-10-01", "color": "#d97706", "detail": "72%" },
        { "label": "v2 final",    "date": "2024-11-02", "color": "#059669", "detail": "100%" }
      ]},

    { "index": 6, "type": "two_column",
      "title": "...",
      "left":  { "title": "Problem",      "content": ["point 1", "point 2"] },
      "right": { "title": "This Run",     "content": ["point 1", "point 2"] } },

    { "index": 7, "type": "bullet_list",
      "title": "...", "bullets": ["item 1", "item 2"], "numbered": true },

    { "index": 8, "type": "conclusion",
      "title": "...",
      "conclusions": ["finding 1", "finding 2"],
      "next_steps":  ["step 1", "step 2"] },

    { "index": 9, "type": "score_trajectory",
      "title": "Review Score Progression",
      "dimensions": ["Originality", "Methodology", "Clarity", "Citations", "Contribution"],
      "rounds": [
        { "label": "Round 1", "scores": [3, 4, 3, 2, 3] },
        { "label": "Round 2", "scores": [4, 4, 4, 4, 4] }
      ],
      "note": "D1-D5 rubric, scale 1-5" },

    { "index": 10, "type": "pipeline_status",
      "title": "Pipeline Progress",
      "stages": [
        { "number": 1, "name": "RESEARCH", "status": "PASS", "date": "2026-06-08" },
        { "number": 2, "name": "WRITE",    "status": "PASS", "date": "2026-06-10" },
        { "number": 2.5, "name": "INTEGRITY", "status": "PENDING", "date": null }
      ]}
  ]
}
```

Only include [A] slides in `slide_data.json`.

---

#### [B] Mermaid

Write a `.mmd` file then convert:
```bash
cat > <dir>/slideNN.mmd << 'EOF'
flowchart LR
  A["Input"] --> B["Model"] --> C["Output"]
EOF
mmdc -i <dir>/slideNN.mmd -o <dir>/slideNN_diagram.svg \
     --theme neutral --width 1200 --height 675
```

If `mmdc` is unavailable: fall back to [C] for that slide and note it in the summary.

Prefer `flowchart LR` for pipelines, `flowchart TD` for training stages, `stateDiagram-v2` for state machines.

---

#### [C] Claude SVG

Write SVG directly. If `STYLE_FILE` is set, read it and load `references/styles/STYLES.md` for the full
role descriptions; otherwise use the defaults in the table below.

| Style key | SVG usage | Default |
|-----------|-----------|---------|
| — | Canvas: `viewBox="0 0 1200 675"` | fixed |
| `bg` | Slide background `<rect fill="..."/>` | `#ffffff` |
| `primary` | Top bar, title text, bullet markers | `#1e3a5f` |
| `top_bar_h` | Top bar `height` in px | `6` |
| `border` | Divider line, card borders | `#e2e8f0` |
| `body` | Main paragraph text | `#374151` |
| `muted` | Footer, axis labels, captions | `#64748b` |
| `font` | `font-family` attribute | `'Helvetica Neue', Arial, sans-serif` |
| `positive` | Success / improvement values | `#059669` |
| `warn` | Caution values | `#d97706` |
| `danger` | Error / regression values | `#dc2626` |

Rules: no `<image>` tags; escape `&` `<` `>` in text; split long text with `<tspan dy="...">`.

---

#### Charts

**list:** Collect chart paths from `## Charts` sections in the selected log files. Write `chart_list.md` grouped by slide.

**embed:** Base64-encode each PNG and insert as `<image>` in the relevant SVG.

---

### 5. Update logs and rebuild index

Add the deck path to `slide_decks:` in each included log file's frontmatter. Rebuild INDEX.md.

---

## PPTX export (optional)

After slides are generated:

**Native shapes (recommended) — fully editable in PowerPoint:**
```bash
# macOS / Linux / Git Bash:
cd "$(find ~/.claude -path "*/report-slides/scripts" -type d | head -1)"
python3 -m svg_to_pptx \
    --slides docs/slides/reports/YYYY-MM-DD_<name>/ \
    --out    docs/slides/reports/YYYY-MM-DD_<name>/deck.pptx
```

Native mode converts every SVG element to editable shapes: rectangles, ovals, text boxes, connectors, and paths (including Bézier curves). Text labels inside shapes are embedded directly — double-click a shape in PowerPoint to edit its text. Connectors re-route when shapes are moved.

**SVG embed (backward-compatible, viewable but shapes are not individually editable):**
```bash
python3 -m svg_to_pptx --slides output/ --out deck.pptx --mode embed
# or equivalently:
python "" \
    --slides docs/slides/reports/YYYY-MM-DD_<name>/ \
    --out    docs/slides/reports/YYYY-MM-DD_<name>/deck.pptx
```

Only `python-pptx` and `lxml` required — no cairosvg, Pillow, or image converter needed.

---

## Summary output

After all slides are generated, print:
- Output directory and slide list with rendering path tags ([A] / [B] / [C])
- `slide_data.json` re-render tip for [A] slides
- `chart_list.md` note if applicable
- Updated log files
- PPTX path if exported
- Import tips: drag SVG into Keynote (macOS); LibreOffice Impress opens SVG natively

---

## Edge cases

| Situation | Handling |
|-----------|---------|
| No log files exist | Stop; instruct user to run `/research-log add` |
| No numeric data in logs | Use `bullet_list` or `two_column` instead of charts |
| No `follows:` chain | Skip timeline slide |
| `mmdc` not found | Fall back to [C]; note in summary |
| Only 1 log entry | Limit to 4–5 slides |
| Chart file paths missing | Mark with ⚠ in `chart_list.md` |
| No baseline data | Skip comparison table |
