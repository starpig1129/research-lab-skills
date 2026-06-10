# Research Mode Integration — Design Spec
**Date:** 2026-06-10  
**Status:** Approved  
**Approach:** Option B — Integration layer + extend existing skills

---

## Problem

Two independent skill systems exist with no bridge:
- **`research-log` + `report-slides`**: ML experiment tracking and slide generation
- **`academic-research-skills`** (deep-research, academic-paper, academic-paper-reviewer, academic-pipeline): full academic writing pipeline

Researchers need a unified workflow where all activity—experiments, reading, research exploration, paper writing—is automatically logged and reportable, and where the system adapts its behavior to the current work context.

---

## Goals

1. Introduce 5 work modes that shape which skills are active and how the system behaves
2. Semi-automatic log drafting: when a mode ends or a stage completes, the system auto-drafts a log entry for user review before saving
3. Zero breaking changes to existing skills and log format
4. All skill output text defaults to English

---

## Architecture

```
User input
     │
     ▼
┌─────────────────────────────────┐
│      research-mode  (new skill) │  ← mode declaration, switching, end-of-session log draft
│  /mode [exp|daily|explore|      │
│         report|publish|status   │
│         |end]                   │
└────────────┬────────────────────┘
             │ dispatches
    ┌────────┴──────────────────────────────┐
    │                                       │
    ▼                                       ▼
Existing skills (unchanged)     academic-research-skills (called only)
  research-log  ◄── extended ──►   deep-research
  report-slides                     academic-paper
                                    academic-paper-reviewer
                                    academic-pipeline
             │
             ▼
      Unified log format (backward-compatible)
      docs/research_log/YYYY-MM-DD_<slug>.md
```

### Component Responsibilities

| Component | Responsibility | Change Type |
|-----------|---------------|-------------|
| `research-mode` skill (new) | Mode switching, routing decisions, session-end log drafting | New |
| `research-log` skill (extended) | New `mode` frontmatter field + 5 mode-specific draft templates | Extend |
| CLAUDE.md routing (new rules) | Mode-aware routing that adjusts skill priority | Modify |

---

## Component 1: `research-mode` Skill

### File Structure

```
skills/research-mode/
  SKILL.md
  references/
    mode_templates.md    ← draft templates for all 5 modes
    routing_guide.md     ← mode × skills routing table
```

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

1. **Announce**: Print mode name + available tools for this mode
2. **Route**: Suggest which skills to use, in priority order
3. **Snapshot**: For `exp` mode — silently run `git_context.py` to capture HEAD; all other modes — record start timestamp

### Activation Output Example (exp mode)

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
1. Collect session outputs
   ├─ exp      → ask for experiment result numbers
   ├─ daily    → ask "what did you read / key insights"
   ├─ explore  → extract summary from deep-research report
   ├─ report   → extract slide paths from report-slides output
   └─ publish  → extract current stage + pass/fail from academic-pipeline

2. Auto-draft log entry
   → Present to user for confirmation / editing

3. User confirms → call /research-log add (pre-filled)
4. Ask if user wants to switch to another mode
```

### Mode × Log Draft Content

| Mode | Auto-filled fields | User confirms |
|------|--------------------|---------------|
| `exp` | Changes (git diff), git_head | Goal, Results, Next Steps |
| `daily` | date, mode | Reading topics, Key insights, Open questions |
| `explore` | Goal (RQ), Analysis (deep-research summary) | Next Steps |
| `report` | slide_decks paths, Audience | Conclusion |
| `publish` | Pipeline stage, Pass/Fail status | Next Steps |

---

## Component 2: `research-log` Extension

### New `mode` Frontmatter Field

Added to all log entries (optional, backward-compatible):

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

Add `Mode` column to the index table:

```markdown
| Date | Experiment | Mode | Tags | Follows | HEAD | Slides |
```

### New `add` Subcommand Behavior

When called from `research-mode` with a pre-filled draft, `research-log add` skips the interactive questions for already-filled fields and only asks for missing ones.

When called standalone (no mode active), behavior is unchanged.

---

## Component 3: CLAUDE.md Routing Rules

Add to `.claude/CLAUDE.md` (project-level) or `~/.claude/CLAUDE.md` (global):

```markdown
## Research Mode Routing

Active mode is declared by `/mode <name>`. When a mode is active:

- **exp**: Prioritize `/research-log add` (Full mode). Run git_context.py silently at start.
- **daily**: Lightweight note-taking. Do NOT trigger deep-research or academic-pipeline unless explicitly asked.
- **explore**: Route to `deep-research` first. On completion, offer `/mode end` to draft log.
- **report**: Route to `report-slides`. Suggest `/mode end` after deck is generated.
- **publish**: Route to `academic-pipeline`. Log each stage completion via `/mode end`.

If no mode is active, apply existing routing rules unchanged.
```

---

## Mode Behavior Summary

| Mode | Core Activity | Log Rigor | Primary Skills |
|------|--------------|-----------|----------------|
| `exp` | Run code experiments, record metrics | High (git HEAD + params + results) | research-log |
| `daily` | Read papers, take notes, organize ideas | Low (lightweight Markdown entry) | (none — freeform) |
| `explore` | Systematic literature exploration with a clear question | Medium (auto-generated APA report) | deep-research |
| `report` | Generate slides for group meetings | Medium (auto-collected from logs) | report-slides |
| `publish` | Full academic paper pipeline | Highest (academic-pipeline QC) | academic-pipeline |

---

## File Change Summary

| File | Change |
|------|--------|
| `skills/research-mode/SKILL.md` | Create new |
| `skills/research-mode/references/mode_templates.md` | Create new |
| `skills/research-mode/references/routing_guide.md` | Create new |
| `skills/research-log/SKILL.md` | Extend: `mode` field + 5 templates + INDEX column |
| `.claude/CLAUDE.md` (project) | Add Research Mode Routing section |

**Not modified:** `report-slides`, all `academic-research-skills`, log file format (backward-compatible).

---

## Non-Goals

- Not building a new orchestrator that replaces academic-pipeline
- Not modifying academic-research-skills internals
- Not enforcing mode selection (mode is always optional; all existing commands work without it)
- Not building a GUI or dashboard

---

## Success Criteria

1. `/mode exp` → system announces mode, captures git HEAD, guides to `/research-log add`
2. `/mode end` → system drafts a log entry pre-filled with session data, user edits and confirms
3. `research-log` INDEX shows `Mode` column
4. Existing `/research-log add` works identically when called without an active mode
5. CLAUDE.md routing rules steer the right skills for each mode without breaking existing routing
