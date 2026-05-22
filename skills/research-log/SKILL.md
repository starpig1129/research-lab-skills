---
name: research-log
description: Record, manage, and query research experiment logs. Use when the user wants to log an experiment result, amend an existing entry, view recent logs, or rebuild the index. Triggers on phrases like "log this experiment", "record results", "add a log entry", "show recent experiments", "amend log". Each entry creates a structured Markdown file in docs/research_log/. Suggest running this before /report-slides when new results have not been logged yet.
---

# Research Log

Manages a structured experiment journal as individual Markdown files.
One file per experiment; INDEX.md is a derived view rebuilt on demand.

## Storage

All files in `docs/research_log/` (relative to project root). Create it if absent.

Filename: `YYYY-MM-DD_<experiment-slug>.md`
Index: `docs/research_log/INDEX.md` (auto-generated, never hand-edited)

## Commands

### add

Create a new log entry.

**Step 1 — Ask mode:**
Quick (3 questions, good for in-progress runs) or Full (all sections)?

**Quick questions:**
1. Experiment name (slug for filename, e.g. `run_v2`)
2. Goal of this experiment
3. Observations / preliminary results
4. Next steps

**Full questions** (ask section by section; user may skip any):
1. Experiment name
2. Changes made (bullet points)
3. Setup (checkpoint, dataset, key parameters)
4. Results (numbers, tables)
5. Failures / pitfalls
6. Analysis and observations
7. Chart paths (relative paths, one per line)
8. Conclusion
9. Next steps

**After answers:** ask if this experiment follows a prior one (list existing files to help).

**Write the file:**

```markdown
---
date: YYYY-MM-DD
experiment: <slug>
tags: []
follows: <prior-filename-or-empty>
reason_follows: <one-line reason or empty>
slide_decks: []
amended: []
---

## Goal
<content>

## Changes
<content, or omit if quick mode>

## Setup
<content, or omit>

## Results
<content, or omit>

## Failures
<content, or omit>

## Analysis
<content>

## Charts
<relative paths, one per line, or omit>

## Conclusion
<content, or omit>

## Next Steps
<content>
```

Omit any section that was skipped. Quick mode writes: Goal, Analysis, Next Steps.

Rebuild INDEX.md after saving.

Confirm: `✓ Created docs/research_log/YYYY-MM-DD_<slug>.md`

---

### amend [name-or-date]

Update an existing entry.

If no argument, list the 5 most recent files and ask which to edit:
```bash
ls -t docs/research_log/*.md | grep -v INDEX | head -5
```

Show current section headings. Ask which sections to update. Rewrite the file with new content. Append to `amended:` in frontmatter:
```yaml
amended:
  - date: YYYY-MM-DD
    summary: <one-line description of change>
```

Rebuild INDEX.md.

---

### index

Rebuild INDEX.md by scanning all `.md` files (excluding INDEX.md):

```bash
find docs/research_log -maxdepth 1 -name "*.md" ! -name "INDEX.md" | sort -r
```

Read frontmatter from each file. Write:

```markdown
# Research Log Index

_Last updated: YYYY-MM-DD_

| Date | Experiment | Tags | Follows | Slides |
|------|-----------|------|---------|--------|
| 2024-11-02 | run_v2 | training, ablation | run_v1 | ✅ reports/2024-11-05 |
| 2024-10-28 | run_v1 | baseline | — | ❌ |
```

Rules: newest first; `Slides` = ✅ with deck name if `slide_decks` non-empty, else ❌; `Follows` = experiment slug (not full filename), or `—`.

---

### show [n]

Show the n most recent entries (default 5). For each, print a compact summary: date, experiment, goal excerpt, next steps excerpt, slide status.

---

## Frontmatter reference

| Field | Description |
|-------|-------------|
| `date` | YYYY-MM-DD |
| `experiment` | slug used in filename |
| `tags` | free-form list |
| `follows` | filename of prior experiment (optional) |
| `reason_follows` | why this follows from the prior (optional) |
| `slide_decks` | paths added by /report-slides (do not edit manually) |
| `amended` | change records added by amend command |

## Notes

- If `docs/research_log/` does not exist, create it silently.
- If a `follows:` target file is not found, warn but continue.
- `slide_decks` and `amended` are managed by skills only — never ask the user to set them.
