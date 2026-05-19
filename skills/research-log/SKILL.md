---
name: research-log
description: Record, manage, and query research experiment logs. Use when the user wants to log an experiment ("記錄實驗", "log this", "新增記錄"), amend an existing entry ("修改記錄", "補充結果"), view recent logs ("看最近的記錄"), or rebuild the index. Each entry creates a structured Markdown file in docs/research_log/. Always suggest using this skill before /report-slides when new experiment results exist but have not been logged yet.
---

# Research Log Skill

Manages a structured experiment journal stored as individual Markdown files.
Each invocation of `/research-log add` creates **one new file**; the index is a derived view, not a source of truth.

---

## Storage Convention

All files live in `docs/research_log/` (relative to project root).
Create the directory if it does not exist:
```bash
mkdir -p docs/research_log
```

File naming: `YYYY-MM-DD_<experiment>.md`
Index file:  `docs/research_log/INDEX.md` (auto-generated, never hand-edited)

---

## Commands

### `/research-log add`

**Step 1 — Ask mode (one question):**
> 「快速記錄」還是「完整記錄」？
> - 快速（Q）：3 個問題，適合實驗中途
> - 完整（F）：逐節填寫所有 sections

**Step 2 — Quick mode questions (Q):**
1. 實驗名稱？（英文 + 底線，用於檔名，例如 `finetune_v3`）
2. 本次目標是什麼？
3. 初步觀察 / 結果？（數字、現象）
4. 下一步？

**Step 2 — Full mode questions (F):**
詢問每個 section，使用者可回答「skip」跳過。順序：
1. 實驗名稱（同 Q）
2. 改動內容（列點描述，例如「新增 TemporalAggregator，window_size=3」）
3. 實驗設定（checkpoint 路徑、資料集、關鍵參數）
4. 結果（數字、表格，可直接貼文字）
5. 失敗 / 踩坑記錄（有就填，無則 skip）
6. 分析與觀察（為什麼結果如此）
7. 圖表路徑（相對路徑清單，一行一個）
8. 結論（1–2 句）
9. 下一步

**Step 3 — Infer `follows`:**
Ask: 「這個實驗是接續哪個前一個實驗？（可跳過，直接 Enter）」
If provided, verify the file exists:
```bash
ls docs/research_log/ | grep <name>
```

**Step 4 — Write the file:**
Filename: `YYYY-MM-DD_<experiment>.md` using today's date.

```markdown
---
date: YYYY-MM-DD
experiment: <experiment>
tags: []
follows: <filename-or-empty>
reason_follows: <one-line reason or empty>
slide_decks: []
amended: []
---

## 目標
<content>

## 改動內容
<content or omit if quick mode>

## 實驗設定
<content or omit>

## 結果
<content or omit>

## 失敗記錄
<content or omit>

## 分析與觀察
<content>

## 圖表路徑
<content or omit>

## 結論
<content or omit>

## 下一步
<content>
```

Omit sections that were skipped (don't write empty headers).
Quick mode writes: 目標, 分析與觀察, 下一步.

**Step 5 — Rebuild INDEX.md** (see INDEX section below).

Confirm to user:
```
✓ 記錄已建立：docs/research_log/YYYY-MM-DD_<experiment>.md
✓ INDEX.md 已更新
```

---

### `/research-log amend [name-or-date]`

1. If no argument given, list last 5 entries and ask which to edit:
   ```bash
   ls -t docs/research_log/*.md | grep -v INDEX | head -5
   ```
2. Read the target file and show current section headings.
3. Ask: 「要修改哪幾個 section？（列出名稱，或說「全部重填」）」
4. For each chosen section, ask the new content.
5. Rewrite the file preserving unchanged sections.
6. Append to `amended:` in frontmatter:
   ```yaml
   amended:
     - date: YYYY-MM-DD
       summary: <one-line description of what changed>
   ```
7. Rebuild INDEX.md.

---

### `/research-log index`

Scan all `.md` files (excluding INDEX.md), read frontmatter, write INDEX.md.

```bash
find docs/research_log -maxdepth 1 -name "*.md" ! -name "INDEX.md" | sort -r
```

For each file, extract with Python:
```python
import re, pathlib

def read_frontmatter(path):
    text = pathlib.Path(path).read_text()
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            fm[k.strip()] = v.strip()
    return fm
```

**INDEX.md format:**
```markdown
# Research Log Index

_Last updated: YYYY-MM-DD_

| 日期 | 實驗名稱 | Tags | Follows | 已製作簡報 |
|------|---------|------|---------|-----------|
| 2026-05-18 | finetune_v3 | embedding, siamese | backbone_v3 | ✅ reports/2026-05-20_weekly |
| 2026-05-15 | backbone_v3 | temporal | — | ❌ |
```

Rules:
- Sort newest first.
- `已製作簡報`: `✅ <deck-name>` if `slide_decks` is non-empty; `❌` otherwise.
- `Follows`: show the experiment name portion of the filename (strip date prefix and `.md`); `—` if empty.
- Tags: join list items with `, `; `—` if empty.

---

### `/research-log show [n]`

Default n = 5.

```bash
ls -t docs/research_log/*.md | grep -v INDEX | head -<n>
```

For each file, show a compact summary:
```
─────────────────────────────────────────
📄 2026-05-18_finetune_v3.md
   目標：embed_alpha=0.3 混合評分能否解決 spin_left 問題
   下一步：部署至 Jetson 進行實機測試
   簡報：❌
─────────────────────────────────────────
```

---

## File Format Reference

### Frontmatter fields

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | YYYY-MM-DD |
| `experiment` | string | short slug used in filename |
| `tags` | list | free-form topic tags |
| `follows` | string | filename of prior experiment (optional) |
| `reason_follows` | string | one-line reason for the follow (optional) |
| `slide_decks` | list | paths to generated slide decks (managed by report-slides) |
| `amended` | list | `{date, summary}` objects added by amend command |

### Sections (all optional except 目標)

```
## 目標
## 改動內容
## 實驗設定
## 結果
## 失敗記錄
## 分析與觀察
## 圖表路徑
## 結論
## 下一步
```

---

## Notes

- Never edit INDEX.md by hand — always regenerate via `/research-log index`.
- `slide_decks` and `amended` in frontmatter are managed by skills, not by the user.
- If `docs/research_log/` does not exist, create it silently before writing any file.
- If a `follows:` target file is not found, log a warning but still create the new entry.
