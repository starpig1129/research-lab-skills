---
name: report-slides
description: Generate SVG presentation slides for research progress reports from research log entries. Use when the user wants to make slides, create a presentation, summarize experiments for a meeting, or produce a visual report ("做簡報", "製作投影片", "進度報告", "產生投影片", "report slides", "presentation"). Reads docs/research_log/ entries, proposes a slide outline for confirmation, then generates SVG files via three rendering paths. Always check whether unlogged experiments exist before starting — suggest /research-log add first if needed.
---

# Report Slides Skill

Generates a research presentation as a set of SVG files from research log entries,
then optionally packages them into a ready-to-use PPTX.
Three rendering paths are used depending on slide content:
- **[A] Python script** — data-driven slides (charts, tables, metrics)
- **[B] Mermaid** — diagram slides (flowcharts, architectures, state machines)
- **[C] Claude SVG** — free-form slides (conceptual layouts, text-heavy content)

**Note on PPTX**: each slide is embedded as a high-resolution PNG image (2400×1350).
Elements inside a slide cannot be individually edited in PowerPoint.
To revise a slide, edit its SVG source then re-run `--to-pptx`.

---

## Setup (run once per project)

**1. Ensure generate_slides.py is present:**
```bash
ls scripts/generate_slides.py 2>/dev/null || echo "MISSING"
```
If missing, locate and copy from the skill bundle:
```bash
mkdir -p scripts
SKILL_GEN=$(find ~/.claude -path "*/report-slides/generate_slides.py" | head -1)
cp "$SKILL_GEN" scripts/generate_slides.py
echo "✓ Copied generate_slides.py → scripts/"
```

**2. Check for Mermaid CLI (Path B):**
```bash
which mmdc 2>/dev/null && echo "MMDC_OK" || echo "MMDC_MISSING"
```
If missing, Path B slides automatically fall back to Path C. Optionally suggest:
`npm install -g @mermaid-js/mermaid-cli`

**3. Check PPTX dependencies (for Step 5):**
```bash
python3 -c "import cairosvg, pptx; print('PPTX deps OK')" 2>/dev/null || echo "PPTX_DEPS_MISSING"
```
If missing:
```bash
pip install python-pptx cairosvg
# fallback converters (if cairosvg fails on your system):
# sudo apt install inkscape       ← inkscape fallback
# sudo apt install librsvg2-bin  ← rsvg-convert fallback
```

---

## Workflow (5 Steps)

---

### Step 1 — Show available logs

```bash
cat docs/research_log/INDEX.md 2>/dev/null \
  || find docs/research_log -maxdepth 1 -name "*.md" ! -name "INDEX.md" | sort -r | head -20
```

Display a brief summary of available entries and which ones have already been made into slide decks.
If no log files exist at all, tell the user to run `/research-log add` first and stop.

---

### Step 2 — Q&A (ask all in one message)

```
1. 要包含哪些 log？
   - all（全部）
   - recent-N（最近 N 筆，例如 recent-3）
   - 指定實驗名稱（例如 backbone_v3, finetune_v3）
   - 日期範圍（YYYY-MM-DD:YYYY-MM-DD）

2. 報告對象？
   - 指導教授（深度、方法細節為主）
   - 組內週會（簡潔、重點結果）
   - 研討會投稿（背景清楚、貢獻突出）

3. 圖表處理？
   - list：在 chart_list.md 列出路徑，手動插入（預設）
   - embed：base64 嵌入 SVG <image> 標籤

4. 投影片語言？
   - auto：跟隨 log 語言
   - zh：強制繁體中文
   - en：強制英文

5. 強調重點？（可選，讓 Claude 自行決定則跳過）
   - 演進過程 / 最終結果 / 失敗分析 / 方法架構
```

---

### Step 3 — Read logs and propose outline

**Read selected log files:**
```bash
cat docs/research_log/YYYY-MM-DD_<name>.md
```

Also read `CLAUDE.md` (if exists) for project context, baseline benchmarks, and architecture overview.

**Analyze:**
- Build the `follows:` chain to understand experiment progression
- Identify key results, turning points, failures
- Determine narrative arc based on audience (Step 2 Q2)

**Propose outline** in this exact format — wait for confirmation before generating:

```
建議投影片結構（共 N 張）：

#01  標題                        [C: title]
#02  研究背景與目標               [C: two_column]
#03  實驗演進時間軸               [B: Mermaid flowchart]
#04  本次改動                     [A: bullet_list]
#05  量化結果比較                  [A: bar_chart]
#06  與 Baseline 對比              [A: table]
#07  系統架構                      [B: Mermaid flowchart]
#08  結論與下一步                  [C: conclusion]

[A] Python腳本（資料型） [B] Mermaid（圖表型） [C] Claude SVG（自由型）

確認以上結構？（說「ok」直接生成，或指出要修改的張次）
```

**Dynamic slide inclusion rules:**
- Include **timeline** only when ≥ 2 log entries are linked via `follows:`
- Include **architecture** only when logs mention structural model changes
- Include **failure analysis** only when logs have content under `## 失敗記錄`
- Include **world model / ablation** slides only when relevant CSVs are mentioned in logs
- **Merge or drop** slides if there is only 1 log entry (avoid stretching thin content)
- Minimum 3 slides; maximum ~10 slides for a weekly meeting, more for conference talks

---

### Step 4 — Generate slides

Determine output directory: `docs/slides/reports/YYYY-MM-DD_<deck-name>/`
```bash
mkdir -p docs/slides/reports/YYYY-MM-DD_<deck-name>
```

---

#### Path A — Python Script (data-driven slides)

Types: `title`, `bullet_list`, `bar_chart`, `table`, `metric_cards`, `two_column`, `timeline`, `conclusion`

**Step A1:** Produce `slide_data.json` in the output directory.

JSON structure:
```json
{
  "meta": {
    "experiment": "<deck-name>",
    "date": "YYYY-MM-DD",
    "footer": "<experiment> · YYYY-MM-DD"
  },
  "slides": [
    {
      "index": 1,
      "type": "title",
      "title": "...",
      "subtitle": "...",
      "author": "...",
      "date": "YYYY-MM-DD"
    },
    {
      "index": 4,
      "type": "bar_chart",
      "title": "...",
      "categories": ["cat1", "cat2"],
      "series": [
        {"label": "baseline", "color": "#d97706", "values": [87.6, 71.7]},
        {"label": "this run", "color": "#059669", "values": [100.0, 100.0]}
      ],
      "y_max": 100,
      "note": "n=13,087"
    },
    {
      "index": 5,
      "type": "table",
      "title": "...",
      "columns": ["Col1", "Col2", "Col3", "Delta"],
      "rows": [["A", "87.6%", "100%", "+12.4%"]],
      "highlight_col": 3
    },
    {
      "index": 6,
      "type": "metric_cards",
      "title": "...",
      "metrics": [
        {"label": "Overall", "value": "99.98%", "color": "#059669", "change": "+48%"}
      ]
    },
    {
      "index": 7,
      "type": "timeline",
      "title": "...",
      "events": [
        {"label": "v0314", "date": "2026-03-14", "color": "#d97706", "detail": "87.6%"},
        {"label": "finetune_v3", "date": "2026-05-18", "color": "#059669", "detail": "100%"}
      ]
    },
    {
      "index": 8,
      "type": "conclusion",
      "title": "結論與下一步",
      "conclusions": ["conclusion 1", "conclusion 2"],
      "next_steps": ["step 1", "step 2"]
    }
  ]
}
```

Only include Path A slides in this JSON.

**Step A2:** Run the script:
```bash
python scripts/generate_slides.py \
    --data docs/slides/reports/YYYY-MM-DD_<deck>/slide_data.json \
    --out  docs/slides/reports/YYYY-MM-DD_<deck>/
```

To re-render a single slide later:
```bash
python scripts/generate_slides.py \
    --data docs/slides/reports/YYYY-MM-DD_<deck>/slide_data.json \
    --out  docs/slides/reports/YYYY-MM-DD_<deck>/ \
    --slide 5
```

---

#### Path B — Mermaid (diagram slides)

**Step B1:** Write `.mmd` source file:
```bash
cat > docs/slides/reports/YYYY-MM-DD_<deck>/slideNN_diagram.mmd << 'EOF'
flowchart LR
  Camera["📷 Camera"] --> Encoder["CNN Encoder"]
  LiDAR["📡 LiDAR"]  --> LidarEnc["LiDAR Encoder"]
  Encoder   --> ResBlock["ResBlock × N"]
  LidarEnc  --> ResBlock
  ResBlock  --> Planner["Command Planner"]
  Memory["🧠 Memory"] --> Planner
  Planner   --> Robot["🤖 Robot"]
EOF
```

**Step B2:** Convert to SVG:
```bash
mmdc \
  -i docs/slides/reports/YYYY-MM-DD_<deck>/slideNN_diagram.mmd \
  -o docs/slides/reports/YYYY-MM-DD_<deck>/slideNN_diagram.svg \
  --theme neutral --width 1200 --height 675
```

**If mmdc is unavailable:** Fall back to Path C for that slide. Add a note in the summary:
`⚠ slideNN: mmdc not found, rendered via Path C. Install: npm i -g @mermaid-js/mermaid-cli`

Mermaid diagram types to prefer by content:
- System pipeline / data flow → `flowchart LR`
- Experiment progression → `flowchart TD`
- State transitions → `stateDiagram-v2`
- Training stages → `flowchart TD` with subgraph blocks

---

#### Path C — Claude SVG (free-form slides)

Write the SVG file directly. **All Path C slides must follow this style system:**

| Element | Value |
|---------|-------|
| Canvas | `viewBox="0 0 1200 675"` |
| Background | `fill="#ffffff"` |
| Top accent bar | `<rect x="0" y="0" width="1200" height="6" fill="#1e3a5f"/>` |
| Title text | `font-size="20" font-weight="700" fill="#1e3a5f" text-anchor="middle"` at `x="600" y="44"` |
| Divider | `<line x1="40" y1="54" x2="1160" y2="54" stroke="#e2e8f0" stroke-width="1.5"/>` |
| Footer | `font-size="10" fill="#64748b" text-anchor="end"` at `x="1160" y="660"` |
| Body text | `fill="#374151"` |
| Muted text | `fill="#64748b"` |
| Card background | `fill="#f8fafc" stroke="#e2e8f0"` |
| Font | `font-family="'Helvetica Neue', Arial, sans-serif"` |
| Good/positive | `#059669` |
| Baseline/warn | `#d97706` |
| Danger/negative | `#dc2626` |

**Rules:**
- Never use `<image>` tags (charts are listed separately unless embed mode)
- Always escape `&`, `<`, `>` in text content as `&amp;`, `&lt;`, `&gt;`
- Long text → split into `<tspan x="..." dy="...">` elements
- For arrows between boxes: use `<line>` + `<polygon>` for arrowhead, or `<path>`
- Geometric shapes: `<rect rx="6">` for rounded cards, `<circle>` for nodes

---

#### Chart handling

**If `--charts list` (default):**

Create `chart_list.md`:
```markdown
# 圖表清單

請將以下圖表手動插入對應投影片：

## Slide 05 — 量化結果
- `exp/v0418/analysis_plots/analysis_finetune_v3/command_confusion_matrix.png`
- `exp/v0418/analysis_plots/analysis_finetune_v3/turn_error_breakdown.png`

## Slide 07 — 世界模型
- `exp/v0418/analysis_plots/world_model_eval_all/compare_all.png`
```

Collect chart paths from `## 圖表路徑` sections in each log file.

**If `--charts embed`:**

For each chart PNG referenced in the logs, base64-encode and insert into the relevant SVG:
```python
import base64, pathlib

def embed_image(svg_path, img_path, x, y, w, h):
    data = base64.b64encode(pathlib.Path(img_path).read_bytes()).decode()
    tag  = f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{data}"/>'
    # Insert before </svg>
    svg  = pathlib.Path(svg_path).read_text()
    svg  = svg.replace("</svg>", f"  {tag}\n</svg>")
    pathlib.Path(svg_path).write_text(svg)
```

---

### Step 5 — Generate PPTX (optional but recommended)

After all SVGs are generated (Paths A + B + C), package them into a PPTX:

```bash
python scripts/generate_slides.py \
    --to-pptx docs/slides/reports/YYYY-MM-DD_<deck>/ \
    --pptx-out docs/slides/reports/YYYY-MM-DD_<deck>/deck.pptx
```

The script scans all `slide*.svg` in the directory (sorted), converts each to PNG at 2400×1350,
and assembles a 16:9 PPTX (13.333" × 7.5").

**Fallback chain for SVG→PNG conversion** (tried in order):
1. `cairosvg` (pip) — preferred
2. `inkscape` (system)
3. `rsvg-convert` (librsvg)

If all three are unavailable, print an error with install instructions and skip PPTX generation.

**To regenerate PPTX after editing one SVG:**
```bash
# Edit the SVG (or re-render with --slide N), then:
python scripts/generate_slides.py \
    --to-pptx docs/slides/reports/YYYY-MM-DD_<deck>/ \
    --pptx-out docs/slides/reports/YYYY-MM-DD_<deck>/deck.pptx
```

---

### Step 6 — Update frontmatter and rebuild INDEX

**Update each included log file's `slide_decks:` field:**

```python
import re, pathlib

deck = "docs/slides/reports/YYYY-MM-DD_<deck>"

for log_path in included_log_files:
    text = pathlib.Path(log_path).read_text()
    if "slide_decks: []" in text:
        text = text.replace("slide_decks: []", f'slide_decks: ["{deck}"]')
    else:
        # Append to existing list
        text = re.sub(
            r'(slide_decks:\s*\[)([^\]]*?)(\])',
            lambda m: f'{m.group(1)}{m.group(2)}, "{deck}"{m.group(3)}'
            if m.group(2).strip() else f'{m.group(1)}"{deck}"{m.group(3)}',
            text
        )
    pathlib.Path(log_path).write_text(text)
```

**Rebuild INDEX.md:**
Run the same logic as `/research-log index` — scan all frontmatters, write the table.

---

## Output Summary

After all slides are generated, print:

```
✅ 投影片生成完成

輸出目錄：docs/slides/reports/YYYY-MM-DD_<deck>/

  slide01_title.svg           [C]
  slide02_two_column.svg      [C]
  slide03_diagram.svg         [B: Mermaid]   (source: slide03_diagram.mmd)
  slide04_bullet_list.svg     [A]
  slide05_bar_chart.svg       [A]
  slide06_table.svg           [A]
  slide07_conclusion.svg      [C]

  slide_data.json             ← Path A 來源（可用 --slide N 重新渲染單張）
  deck.pptx                   ← 7 slides，349 KB（可直接開啟 / 寄出）
  chart_list.md               ← N 個圖表待手動插入

已更新 research log：
  ✓ docs/research_log/2026-05-15_backbone_v3.md  → slide_decks 已標記
  ✓ docs/research_log/2026-05-18_finetune_v3.md  → slide_decks 已標記
✓ INDEX.md 已重建

注意：deck.pptx 中每張投影片為嵌入圖片，元素不可在 PowerPoint 內單獨編輯。
若需修改單張 → 編輯對應 SVG → 重新執行 --to-pptx 覆蓋 deck.pptx。
```

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| No log files exist | Stop, instruct user to run `/research-log add` first |
| Log file has no numeric results | Skip Path A chart slides; use bullet_list or two_column instead |
| No `follows:` chain | Skip timeline slide |
| `## 失敗記錄` is empty in all logs | Skip failure analysis slide |
| mmdc not found | Fall back to Path C, note in summary |
| Baseline not in logs or CLAUDE.md | Skip comparison table slide |
| Only 1 log entry | Limit to 4–5 slides; don't stretch thin content |
| Chart paths in log don't exist | Include in chart_list.md with a ⚠ marker |
| cairosvg / inkscape / rsvg all missing | Skip PPTX, print install instructions, SVG files still available |
| User wants to edit slide content later | Tell them to edit the SVG, then re-run `--to-pptx` to refresh deck.pptx |
