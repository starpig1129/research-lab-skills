# Research Mode Integration — Design Spec
**Date:** 2026-06-10  
**Status:** Approved  
**Approach:** Option B — Integration layer + extend existing skills  
**Version:** 2.0 (expanded to full gap coverage)

---

## Problem

Two independent skill systems exist with no bridge:
- **`research-log` + `report-slides`**: ML experiment tracking and slide generation
- **`academic-research-skills`** (deep-research, academic-paper, academic-paper-reviewer, academic-pipeline): full academic writing pipeline

Researchers need a unified workflow where all activity—experiments, reading, research exploration, paper writing—is automatically logged and reportable, and where the system adapts its behavior to the current work context.

Beyond this core gap, 7 additional integration gaps exist across the two systems (see Gap Inventory below).

---

## Goals

1. Introduce 5 work modes that shape which skills are active and how the system behaves
2. Semi-automatic log drafting: when a mode ends or a stage completes, the system auto-drafts a log entry for user review before saving
3. Close all 7 identified integration gaps across two implementation phases
4. Restructure the project folder layout to make the full system navigable
5. Zero breaking changes to existing skills and log format
6. All skill output text defaults to English

---

## Implementation Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | `research-mode` skill, `research-log` extension, CLAUDE.md routing | Implement now |
| **Phase 2** | Material Passport bridge, `report-slides` academic data support | Implement after Phase 1 |
| **Phase 3** | Score trajectory, deep-research sub-modes, ARS command hooks, AI self-reflection | TODO |
| **Phase 4** | Citation verification stats, Sprint Contract metrics, collaboration depth, cross-model results | TODO (backlog) |

---

## Gap Inventory

### Phase 1 (Implement now)

**Gap 1 — No work modes**  
The system has no concept of work context. Skills are called one-off with no continuity between sessions.  
Fix: `research-mode` skill + CLAUDE.md routing rules.

**Gap 2 — research-log has no academic templates**  
`research-log add` only supports ML experiment format. Academic pipeline outputs (research reports, paper drafts, reviewer feedback) cannot be logged.  
Fix: Extend `research-log` with `mode` field + 5 draft templates.

### Phase 2 (High priority)

**Gap 3 — Material Passport isolated from research-log**  
academic-pipeline maintains a Material Passport (Schema 9) with cross-session stage tracking and git-style hash lineage. This rich progress ledger has no connection to research-log, leaving a paper's journey invisible to the experiment journal.  
Fix: `bridge/scripts/passport_to_log.py` — extracts stage completion records from the Passport and drafts research-log entries; called automatically by `research-mode` in `publish` mode.

**Gap 4 — report-slides cannot read academic pipeline data**  
`report-slides` only reads research-log entries. Reviewer scores, revision round progression, and paper stage status—the most meaningful "research progress" data—cannot appear in slides.  
Fix: Extend `report-slides` with an `academic` data source that reads Passport stage records and reviewer score matrices.

### Phase 3 (TODO)

**Gap 5 — Reviewer score trajectory disappears after pipeline**  
academic-paper-reviewer produces per-dimension rubric scores (D1–D7) each review round. These scores could plot a "paper quality evolution curve" but are lost when the conversation ends.  
Fix: `bridge/scripts/score_extractor.py` — parses reviewer output and appends dimension scores to the log entry for that pipeline stage.

**Gap 6 — deep-research sub-modes have no distinct log templates**  
`explore` mode currently maps only to `full` / `socratic` deep-research. The `systematic-review`, `lit-review`, and `fact-check` sub-modes produce structurally different outputs and need their own draft templates.  
Fix: Add 3 sub-mode templates to `research-mode/references/mode_templates.md`; update mode selection to ask which deep-research sub-mode before drafting.

**Gap 7 — ARS slash commands are not mode-aware**  
The 10 `/ars-*` commands (`/ars-full`, `/ars-revision-coach`, etc.) bypass `research-mode` entirely. Entering these flows does not switch to `publish` mode and does not trigger log drafting on completion.  
Fix: `bridge/references/ars_command_hooks.md` — documents how each `/ars-*` command should register with `research-mode`; `CLAUDE.md` routing addition that maps `/ars-*` invocations to `publish` mode.

**Gap 8 — AI Self-Reflection Report is ephemeral**  
academic-pipeline Stage 6 produces an AI behavioral self-assessment (concession rate, sycophancy risk rating, health alerts). This disappears when the conversation ends.  
Fix: Optional `ai_reflection` section added to publish-mode log template; `research-mode` offers to append it after pipeline completion.

### Phase 4 (Backlog)

**Gap 9 — Collaboration Depth scores not tracked**  
The Collaboration Depth Observer (v3.5) scores human-AI collaboration on 4 dimensions at every pipeline checkpoint. No longitudinal tracking exists.  
Fix: `bridge/scripts/collab_depth_logger.py` — appends observer scores to log entries as structured YAML block.

**Gap 10 — Citation verification statistics not logged**  
The v3.11 citation verification gate produces per-paper lookup results (true / false / unresolvable ratio). Not captured in any log.  
Fix: Add `citation_stats` optional block to publish-mode log template.

**Gap 11 — Sprint Contract quality metrics not logged**  
Schema 13.1 generator-evaluator contracts produce pre-commitment artifacts and disagreement handling records. Not accessible outside the pipeline session.  
Fix: Add `sprint_contract_summary` optional block to publish-mode log template.

---

## Project Folder Structure (Revised)

```
research-lab-skills/
│
├── skills/                          ← Custom skills (this project's work)
│   ├── research-mode/               ← NEW: mode dispatcher + log orchestrator
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── mode_templates.md    ← Draft templates for all 5 modes + sub-modes
│   │       └── routing_guide.md     ← Mode × skills routing table
│   │
│   ├── research-log/                ← EXTENDED
│   │   ├── SKILL.md                 ← +mode field, +5 templates, +INDEX Mode column
│   │   └── scripts/
│   │       └── git_context.py
│   │
│   └── report-slides/               ← EXTENDED (Phase 2: academic data source)
│       ├── SKILL.md                 ← +academic data source, +score trajectory slide type
│       ├── references/
│       │   └── styles/
│       └── scripts/
│           ├── generate_slides.py
│           ├── set-style.sh / .ps1
│           ├── setup.sh / .ps1
│           └── to_pptx.py
│
├── bridge/                          ← NEW: integration utilities (Phase 2+)
│   ├── scripts/
│   │   ├── passport_to_log.py       ← Phase 2: Passport → research-log bridge
│   │   ├── score_extractor.py       ← Phase 3: reviewer score → log
│   │   ├── collab_depth_logger.py   ← Phase 4: collaboration depth → log
│   │   └── ars_log_hook.py          ← Phase 3: ARS command completion → log
│   └── references/
│       ├── passport_log_schema.md   ← Schema for Passport-sourced log entries
│       ├── ars_slide_data.md        ← How ARS data maps to report-slides types
│       └── ars_command_hooks.md     ← ARS command → research-mode integration spec
│
├── docs/
│   ├── superpowers/
│   │   └── specs/                   ← Design specs (this file lives here)
│   └── design/                      ← Architectural decision records
│
├── academic-research-skills/        ← External dependency (NOT modified)
│
├── .claude/
│   └── CLAUDE.md                    ← NEW: Research Mode Routing rules
│
├── .claude-plugin/
│   └── marketplace.json
├── bin/
│   └── crs.js
├── install.sh
├── package.json
└── README.md
```

---

## Architecture

```
User input
     │
     ▼
┌─────────────────────────────────────┐
│      research-mode  (new skill)     │  ← mode declaration, switching, session-end log draft
│  /mode [exp|daily|explore|          │
│         report|publish|status|end]  │
└────────────┬────────────────────────┘
             │ dispatches
    ┌────────┴──────────────────────────────────┐
    │                                           │
    ▼                                           ▼
Existing skills                    academic-research-skills (called only)
  research-log  ◄─── bridge ────►   deep-research
  report-slides ◄─── bridge ────►   academic-paper
                                     academic-paper-reviewer
                                     academic-pipeline
                ▲
                │
          bridge/scripts/
          (Phase 2+ integration)
```

---

## Component 1: `research-mode` Skill (Phase 1)

### Commands

| Command | Description |
|---------|-------------|
| `/mode exp` | Experiment mode |
| `/mode daily` | Daily research mode |
| `/mode explore` | Exploration mode |
| `/mode report` | Report mode |
| `/mode publish` | Publication mode |
| `/mode status` | Show current mode + session activity summary |
| `/mode end` | End current mode, trigger auto-draft log |

### On Mode Activation (3 steps)

1. **Announce**: Print mode name + available tools
2. **Route**: Suggest priority skills for this mode
3. **Snapshot**: `exp` — silently run `git_context.py` for HEAD; others — record start timestamp

### Activation Output Example

```
═══════════════════════════════════════
  [EXP] Experiment Mode — Active
═══════════════════════════════════════
  git HEAD : a1b2c3d
  Tools    : /research-log add (Full mode)
  End      : /mode end → auto-draft log
═══════════════════════════════════════
```

### `/mode end` Flow

```
1. Collect session outputs per mode
   ├─ exp      → ask for result numbers
   ├─ daily    → ask "what did you read / key insights"
   ├─ explore  → extract summary from deep-research report
   ├─ report   → extract slide paths from report-slides output
   └─ publish  → extract current stage + pass/fail from academic-pipeline

2. Auto-draft log entry → present to user for confirmation / editing
3. User confirms → call /research-log add (pre-filled)
4. Ask if user wants to switch to another mode
```

### Mode × Log Draft Content

| Mode | Auto-filled | User confirms |
|------|-------------|---------------|
| `exp` | Changes (git diff), git_head | Goal, Results, Next Steps |
| `daily` | date, mode | Reading topics, Key insights, Open questions |
| `explore` | Goal (RQ), Analysis (deep-research summary) | Next Steps |
| `report` | slide_decks paths, Audience | Conclusion |
| `publish` | Pipeline stage, Pass/Fail | Next Steps |

---

## Component 2: `research-log` Extension (Phase 1)

### New `mode` Frontmatter Field

```markdown
---
date: YYYY-MM-DD
experiment: <slug>
mode: exp | daily | explore | report | publish   # NEW — optional
tags: []
follows: <prior-or-empty>
git_head: <sha-or-empty>
slide_decks: []
amended: []
---
```

### INDEX.md Column Update

```markdown
| Date | Experiment | Mode | Tags | Follows | HEAD | Slides |
```

### Pre-filled `add` Behavior

When called from `research-mode` with pre-filled data, skip interactive questions for already-filled fields.  
When called standalone (no active mode), behavior is unchanged.

---

## Component 3: CLAUDE.md Routing (Phase 1)

```markdown
## Research Mode Routing

Active mode is declared by `/mode <name>`. When a mode is active:

- **exp**: Prioritize `/research-log add` (Full mode). Run git_context.py silently at start.
- **daily**: Lightweight note-taking. Do NOT trigger deep-research or academic-pipeline unless explicitly asked.
- **explore**: Route to `deep-research` first. On completion, offer `/mode end` to draft log.
- **report**: Route to `report-slides`. Suggest `/mode end` after deck is generated.
- **publish**: Route to `academic-pipeline`. On each stage completion, offer `/mode end` to log progress.
  - `/ars-*` commands automatically activate publish mode (Phase 3).

If no mode is active, apply existing routing rules unchanged.
```

---

## Component 4: Material Passport Bridge (Phase 2)

`bridge/scripts/passport_to_log.py` — reads Material Passport YAML from the active academic-pipeline session and produces a pre-filled research-log draft for publish mode.

Extracted fields:
- Current stage name and number
- Stage pass/fail status
- Key deliverables list
- Checkpoint hash (for cross-session resume linkage)

---

## Component 5: `report-slides` Academic Data Source (Phase 2)

New `academic` data source alongside the existing `research-log` source.

Reads:
- Material Passport stage completion records (via `passport_to_log.py`)
- Reviewer score matrices (D1–D7 per round)
- Pipeline status timeline

New slide types:
- `score_trajectory` — line chart of reviewer dimension scores across revision rounds
- `pipeline_status` — timeline of stage completions with pass/fail markers
- `academic_summary` — combined paper progress + key findings

---

## Mode Behavior Summary

| Mode | Core Activity | Log Rigor | Primary Skills |
|------|--------------|-----------|----------------|
| `exp` | Run code experiments, record metrics | High (git HEAD + params + results) | research-log |
| `daily` | Read papers, take notes, organize ideas | Low (lightweight Markdown) | — |
| `explore` | Systematic literature exploration | Medium (APA report summary) | deep-research |
| `report` | Generate slides for group meetings | Medium (auto-collected from logs) | report-slides |
| `publish` | Full academic paper pipeline | Highest (academic-pipeline QC) | academic-pipeline |

---

## Non-Goals

- Not building a new orchestrator that replaces academic-pipeline
- Not modifying academic-research-skills internals
- Not enforcing mode selection (mode is always optional)
- Not building a GUI or dashboard

---

## Success Criteria

### Phase 1
1. `/mode exp` → announces mode, captures git HEAD, guides to `/research-log add`
2. `/mode end` → drafts pre-filled log entry, user edits and confirms
3. `research-log` INDEX shows `Mode` column
4. Existing `/research-log add` works identically without active mode
5. CLAUDE.md routing steers correct skills per mode

### Phase 2
6. `publish` mode log entry includes Passport stage data
7. `report-slides` can generate a `score_trajectory` slide from reviewer rounds
8. `report-slides` can generate a `pipeline_status` timeline slide

---

## File Change Summary

| File | Change | Phase |
|------|--------|-------|
| `skills/research-mode/SKILL.md` | Create | 1 |
| `skills/research-mode/references/mode_templates.md` | Create | 1 |
| `skills/research-mode/references/routing_guide.md` | Create | 1 |
| `skills/research-log/SKILL.md` | Extend: mode field + templates + INDEX column | 1 |
| `.claude/CLAUDE.md` | Create: Research Mode Routing section | 1 |
| `bridge/scripts/passport_to_log.py` | Create | 2 |
| `bridge/references/passport_log_schema.md` | Create | 2 |
| `skills/report-slides/SKILL.md` | Extend: academic data source + 2 slide types | 2 |
| `bridge/scripts/score_extractor.py` | Create | 3 |
| `bridge/references/ars_command_hooks.md` | Create | 3 |
| `bridge/scripts/ars_log_hook.py` | Create | 3 |
| `bridge/scripts/collab_depth_logger.py` | Create | 4 |

**Not modified (ever):** `academic-research-skills/` (external dependency)
