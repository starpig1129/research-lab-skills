---
name: report-slides
description: Generate SVG presentation slides for research progress reports from research log entries, then optionally export to PPTX. Use when the user wants to make slides, create a presentation, or produce a visual report from experiment logs. Triggers on "make slides", "create presentation", "report slides", "generate deck", "export to pptx". Reads docs/research_log/ entries, proposes a slide outline for user confirmation, then generates files. Suggest /research-log add first if new experiments have not been logged yet.
---

# Report Slides

Generates a slide deck from research log entries using three rendering paths:
- **[A]** `generate_slides.py` — data-driven slides (charts, tables, metrics)
- **[B]** Mermaid (`mmdc`) — diagram slides (flowcharts, architectures, state machines)
- **[C]** Claude SVG — free-form slides (conceptual layouts, text-heavy content)

After generation, slides can optionally be packaged into a PPTX with native SVG embedding.

---

## Setup (first use in a project)

Copy scripts from the skill bundle:
```bash
mkdir -p scripts docs/slides/reports
find ~/.claude -path "*/report-slides/generate_slides.py" | head -1 | xargs -I{} cp {} scripts/
find ~/.claude -path "*/report-slides/to_pptx.py"        | head -1 | xargs -I{} cp {} scripts/
```

Check for Mermaid (optional):
```bash
which mmdc && echo "Mermaid OK" || echo "Mermaid missing (npm i -g @mermaid-js/mermaid-cli)"
```

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

### 2. Ask (one message)

1. Which logs to include? (`all` / `recent-N` / by name / date range)
2. Audience? (advisor / team meeting / conference)
3. Charts? (`list` = output paths to `chart_list.md` / `embed` = base64 into SVG)
4. Language? (follow log language / force English / force another language)
5. Emphasis? (progression / final results / failure analysis / let Claude decide)

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

### 4. Generate slides

Output directory: `docs/slides/reports/YYYY-MM-DD_<name>/`

---

#### [A] Python renderer

**Supported types:** `title` `bullet_list` `bar_chart` `table` `metric_cards` `two_column` `timeline` `conclusion`

Write `slide_data.json` then run:
```bash
python scripts/generate_slides.py --data <dir>/slide_data.json --out <dir>/
# Re-render one slide:
python scripts/generate_slides.py --data <dir>/slide_data.json --out <dir>/ --slide N
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
      "next_steps":  ["step 1", "step 2"] }
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

Write SVG directly. All [C] slides must follow this style:

| Element | Value |
|---------|-------|
| Canvas | `viewBox="0 0 1200 675"` |
| Background | `#ffffff` |
| Top bar | `<rect x="0" y="0" width="1200" height="6" fill="#1e3a5f"/>` |
| Title | `font-size="20" font-weight="700" fill="#1e3a5f"` at `x="600" y="44" text-anchor="middle"` |
| Divider | `<line x1="40" y1="54" x2="1160" y2="54" stroke="#e2e8f0" stroke-width="1.5"/>` |
| Footer | `font-size="10" fill="#64748b"` at `x="1160" y="660" text-anchor="end"` |
| Font | `font-family="'Helvetica Neue', Arial, sans-serif"` |
| Positive | `#059669` · Warn `#d97706` · Danger `#dc2626` · Body `#374151` · Muted `#64748b` |

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
```bash
python scripts/to_pptx.py \
    --slides docs/slides/reports/YYYY-MM-DD_<name>/ \
    --out    docs/slides/reports/YYYY-MM-DD_<name>/deck.pptx
```

SVG is embedded natively (PowerPoint 2016+/365). A minimal white PNG serves as fallback for older viewers. Only `python-pptx` required — no image converter needed.

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
