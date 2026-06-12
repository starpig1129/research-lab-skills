# report-slides — Example Output

This directory shows what `/report-slides` produces from the two research-log entries in `../research-log/`.

## Input

| Log entry | Mode | Experiment |
|-----------|------|------------|
| `2026-05-15_backbone_v3_quick.md` | Quick | Initial backbone_v3 test, 87.4% CIFAR-10 |
| `2026-05-22_finetune_lr_sweep.md` | Full | LR sweep grid, best run 93.1% CIFAR-10 |

## Files in this directory

| File | Rendering path | Description |
|------|---------------|-------------|
| `slide_data_weekly_progress.json` | [A] Python | Input data for `generate_slides.py`; 7 slides covering the full progression |
| `slide01_title.svg` | [C] Claude SVG | Title slide — generated directly by Claude |
| `slide04_bar_chart.svg` | [A] Python (example render) | Bar chart of LR sweep results, rendered by `generate_slides.py` |

> Slides `#02` (two_column), `#03` (timeline), `#05` (table), `#06` (metric_cards), `#07` (conclusion)
> are defined in `slide_data_weekly_progress.json` and rendered when you run `generate_slides.py`.

## How to regenerate

**Step 1 — set up** (first time per project):
```bash
bash "$(find ~/.claude -path "*/report-slides/scripts/setup.sh" | head -1)"
```

**Step 2 — run the renderer**:
```bash
python scripts/generate_slides.py \
    --data examples/report-slides/slide_data_weekly_progress.json \
    --out  docs/slides/reports/2026-05-22_weekly-progress/
```

**Step 3 — optional PPTX export**:
```bash
cd "$(find ~/.claude -path "*/report-slides/scripts" -type d | head -1)"
python3 -m svg_to_pptx \
    --slides docs/slides/reports/2026-05-22_weekly-progress/ \
    --out    docs/slides/reports/2026-05-22_weekly-progress/deck.pptx
```

## Slide outline

```
#01  Title                   [C] Claude SVG
#02  Background & Goal       [A] two_column
#03  Experiment Timeline     [A] timeline
#04  LR Sweep Bar Chart      [A] bar_chart      ← slide04_bar_chart.svg shows this type
#05  Architecture Comparison [A] table
#06  Key Results             [A] metric_cards
#07  Conclusion & Next Steps [A] conclusion
```

## Invoking from the skill

From any project that has research-log entries, simply run:

```
/report-slides
```

Claude will:
1. Show the available log entries and which already have decks
2. Ask audience, chart mode, language, and style (one message)
3. Propose a slide outline and wait for confirmation
4. Generate SVG files + optionally export PPTX
