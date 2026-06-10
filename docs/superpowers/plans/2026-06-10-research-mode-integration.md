# Research Mode Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate academic-research-skills into the existing research skill system by adding a mode dispatcher, extending research-log with academic templates, creating a Material Passport bridge, and extending report-slides with academic data sources.

**Architecture:** A new `research-mode` skill acts as a lightweight dispatcher that declares work context and orchestrates session-end log drafting. A `bridge/` layer provides Python scripts to extract data from academic-pipeline outputs into the existing research-log format. All changes are backward-compatible; academic-research-skills is never modified.

**Tech Stack:** Bash/Markdown (SKILL.md files), Python 3.8+ (bridge scripts), PyYAML (`pip install pyyaml`), pytest (testing bridge scripts).

---

## File Map

| File | Action | Phase |
|------|--------|-------|
| `skills/research-mode/SKILL.md` | Create | 1 |
| `skills/research-mode/references/mode_templates.md` | Create | 1 |
| `skills/research-mode/references/routing_guide.md` | Create | 1 |
| `skills/research-log/SKILL.md` | Modify (add mode field + 5 templates + INDEX column) | 1 |
| `.claude/CLAUDE.md` | Create | 1 |
| `install.sh` | Modify (add research-mode to SKILLS array) | 1 |
| `bridge/__init__.py` | Create | 2 |
| `bridge/scripts/__init__.py` | Create | 2 |
| `bridge/scripts/passport_to_log.py` | Create | 2 |
| `bridge/scripts/tests/__init__.py` | Create | 2 |
| `bridge/scripts/tests/test_passport_to_log.py` | Create | 2 |
| `bridge/references/passport_log_schema.md` | Create | 2 |
| `bridge/references/ars_command_hooks.md` | Create (stub) | 2 |
| `skills/report-slides/SKILL.md` | Modify (add academic data source + 2 slide types) | 2 |

---

## Phase 1: Core Integration

---

### Task 1: Scaffold Directory Structure

**Files:**
- Create: `skills/research-mode/references/` (directory)
- Create: `bridge/scripts/tests/` (directory)
- Create: `bridge/references/` (directory)
- Create: `.claude/` (directory)

- [ ] **Step 1: Create all new directories**

```bash
mkdir -p skills/research-mode/references
mkdir -p bridge/scripts/tests
mkdir -p bridge/references
mkdir -p .claude
```

- [ ] **Step 2: Add .gitkeep to empty leaf directories**

```bash
touch bridge/scripts/tests/.gitkeep
touch bridge/references/.gitkeep
```

- [ ] **Step 3: Verify structure**

```bash
find skills/research-mode bridge .claude -type d | sort
```

Expected output:
```
.claude
bridge
bridge/references
bridge/scripts
bridge/scripts/tests
skills/research-mode
skills/research-mode/references
```

- [ ] **Step 4: Commit**

```bash
git add skills/research-mode/ bridge/ .claude/
git commit -m "chore: scaffold research-mode, bridge, and .claude directories"
```

---

### Task 2: Create `.claude/CLAUDE.md` (Routing Rules)

**Files:**
- Create: `.claude/CLAUDE.md`

- [ ] **Step 1: Write the routing rules file**

```bash
cat > .claude/CLAUDE.md << 'EOF'
# claude-research-skills — Project Routing Rules

## Research Mode Routing

Active mode is declared by `/mode <name>`. When a mode is active, use it to adjust
which skills to prioritize and how session endings are handled.

| Mode | Primary Skills | Do NOT auto-trigger |
|------|---------------|---------------------|
| `exp` | `research-log` (Full mode) | deep-research, academic-pipeline |
| `daily` | none (freeform) | deep-research, academic-pipeline |
| `explore` | `deep-research` | academic-pipeline |
| `report` | `report-slides` | academic-pipeline |
| `publish` | `academic-pipeline` | — |

**Rules:**

- **exp**: Run `git_context.py` silently at mode start. On `/mode end`, draft a Full-mode
  research-log entry pre-filled with git diff bullets and git HEAD.

- **daily**: Lightweight notes only. Do NOT invoke deep-research or academic-pipeline
  unless the user explicitly asks. On `/mode end`, draft a minimal log entry asking
  for reading topics and key insights.

- **explore**: Route first to `deep-research`. When deep-research produces a report,
  offer `/mode end` to draft a log entry extracting the Research Question and key findings.
  Sub-modes (systematic-review, lit-review, fact-check) get their own templates — see
  `skills/research-mode/references/mode_templates.md`.

- **report**: Route to `report-slides`. After deck generation, suggest `/mode end` to
  log the slide deck paths and audience.

- **publish**: Route to `academic-pipeline`. After each stage completes, offer `/mode end`
  to log the stage status. `/ars-*` commands automatically activate publish mode (Phase 3).

**If no mode is active:** apply default routing rules from academic-research-skills
`.claude/CLAUDE.md` (Routing Discipline v3.9.2) unchanged.

---

## Installation

Skills installed here are available globally after `bash install.sh`.
To install locally only: `bash install.sh --local`
EOF
```

- [ ] **Step 2: Verify file was written**

```bash
wc -l .claude/CLAUDE.md
```

Expected: at least 40 lines.

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "feat: add .claude/CLAUDE.md with Research Mode Routing rules"
```

---

### Task 3: Create `research-mode` SKILL.md

**Files:**
- Create: `skills/research-mode/SKILL.md`

- [ ] **Step 1: Write the skill file**

```bash
cat > skills/research-mode/SKILL.md << 'SKILLEOF'
---
name: research-mode
description: "Work mode dispatcher for research workflows. 5 modes: exp (running experiments), daily (reading/notes), explore (deep-research exploration), report (slide generation), publish (academic-pipeline). Commands: /mode exp|daily|explore|report|publish|status|end. All output in English. Triggers: /mode, switch mode, start experiment, begin research session, mode status, end session."
---

# Research Mode

Declares work context and orchestrates session-end log drafting.
Each mode activates a set of recommended skills and a log draft template.

## Commands

| Command | Description |
|---------|-------------|
| `/mode exp` | Experiment mode — running code, recording metrics |
| `/mode daily` | Daily research — reading papers, taking notes |
| `/mode explore` | Exploration mode — systematic literature search via deep-research |
| `/mode report` | Report mode — generating slides for group meetings |
| `/mode publish` | Publication mode — full academic-pipeline workflow |
| `/mode status` | Show current mode + session activity summary |
| `/mode end` | End current mode, trigger auto-draft log entry |

---

## Mode Activation

When a mode is activated, do three things in order:

**1. Print the activation banner** (English only):

For `/mode exp`:
```
═══════════════════════════════════════
  [EXP] Experiment Mode — Active
═══════════════════════════════════════
  git HEAD : <run git_context.py --head silently>
  Tools    : /research-log add (Full mode)
  End      : /mode end → auto-draft log
═══════════════════════════════════════
```

For `/mode daily`:
```
═══════════════════════════════════════
  [DAILY] Daily Research Mode — Active
═══════════════════════════════════════
  Tools    : freeform notes, /research-log add
  End      : /mode end → lightweight log entry
═══════════════════════════════════════
```

For `/mode explore`:
```
═══════════════════════════════════════
  [EXPLORE] Exploration Mode — Active
═══════════════════════════════════════
  Tools    : deep-research (full / socratic / systematic-review / lit-review / fact-check)
  End      : /mode end → auto-draft log from report
═══════════════════════════════════════
```

For `/mode report`:
```
═══════════════════════════════════════
  [REPORT] Report Mode — Active
═══════════════════════════════════════
  Tools    : /report-slides
  End      : /mode end → log slide deck paths
═══════════════════════════════════════
```

For `/mode publish`:
```
═══════════════════════════════════════
  [PUBLISH] Publication Mode — Active
═══════════════════════════════════════
  Tools    : academic-pipeline (/ars-full, /ars-revision-coach, etc.)
  End      : /mode end → log current pipeline stage
═══════════════════════════════════════
```

**2. Route:** after the banner, recommend the primary skill to use next (one sentence).

**3. Snapshot (exp mode only):** silently run git_context.py to capture HEAD before the
user starts work. Store the HEAD value to pre-fill the log entry at `/mode end`.

```bash
GIT_CTX="$(find ~/.claude -path "*/research-log/scripts/git_context.py" | head -1)"
GIT_HEAD=$(python "$GIT_CTX" --head 2>/dev/null || echo "")
```

---

## `/mode status`

Print a compact summary:

```
Current mode : [MODE]
Started      : HH:MM (or "unknown")
Session work : <1-2 sentence summary of what has been done this session>
Next action  : <suggested next step>
```

---

## `/mode end` — Auto-Draft Log

When the user runs `/mode end`, collect session outputs and draft a log entry.
Read `references/mode_templates.md` for the draft template for the active mode.

### Flow

1. Collect data (see per-mode rules below)
2. Fill in the template from `references/mode_templates.md`
3. Present the draft to the user:
   ```
   ─────────────────────────────────────────
    Draft log entry — review and confirm
   ─────────────────────────────────────────
   <draft content here>
   ─────────────────────────────────────────
   Confirm? (yes / edit / skip)
   ```
4. If confirmed → call `/research-log add` with the pre-filled content
5. If edit → let user modify inline, then confirm again
6. If skip → discard draft, offer to switch modes

### Per-Mode Data Collection

**exp:**
- git HEAD: from snapshot taken at mode start (or re-run git_context.py)
- Changes: run `git_context.py --since-log <last-log-file>` and use Suggested Changes bullets
- Ask: "What were the key results? (numbers, metrics)"
- Ask: "What are the next steps?"

**daily:**
- Ask: "What did you read or work on today? (title / topic)"
- Ask: "What was the key insight or takeaway?"
- Ask: "Any open questions or follow-up items?"

**explore:**
- Extract from deep-research report (if available in session):
  - Research Question → Goal section
  - Executive Summary bullets → Analysis section
- Ask: "What are the next steps based on this research?"

**report:**
- Collect slide deck output path from report-slides (if available in session)
- Ask: "Who was the intended audience?"
- Ask: "One-sentence conclusion from the presentation?"

**publish:**
- Ask: "Which pipeline stage did you complete? (1=Research, 2=Write, 2.5=Integrity, 3=Review, 4=Revise, 4.5=Final Integrity, 5=Finalize)"
- Ask: "Stage result? (PASS / PENDING / needs-revision)"
- Ask: "Key next step?"

---

## Notes

- Mode is session-scoped. Starting a new Claude Code session clears the active mode.
- Multiple `/mode end` calls in one session are allowed — each drafts a new log entry.
- If no mode is active when `/mode end` is called, ask which mode this session was.
- All output text is English. Never output Chinese characters in banners or prompts.
SKILLEOF
```

- [ ] **Step 2: Verify key sections are present**

```bash
grep -c "═══\|mode end\|Per-Mode\|snapshot\|banner" skills/research-mode/SKILL.md
```

Expected: at least 5 matches.

- [ ] **Step 3: Commit**

```bash
git add skills/research-mode/SKILL.md
git commit -m "feat: add research-mode SKILL.md with 5-mode dispatcher"
```

---

### Task 4: Create `mode_templates.md`

**Files:**
- Create: `skills/research-mode/references/mode_templates.md`

- [ ] **Step 1: Write the templates file**

```bash
cat > skills/research-mode/references/mode_templates.md << 'EOF'
# Mode Log Draft Templates

Used by `research-mode` during `/mode end` to pre-fill `research-log` entries.
Each template maps to a `mode:` value in the research-log frontmatter.

---

## exp — Experiment Mode Template

```markdown
---
date: {{DATE}}
experiment: {{SLUG}}
mode: exp
tags: [experiment]
follows: {{PRIOR_LOG_OR_EMPTY}}
git_head: {{GIT_HEAD}}
slide_decks: []
amended: []
---

## Goal
{{USER_EXPERIMENT_GOAL}}

## Changes
{{GIT_CONTEXT_BULLETS}}

## Results
{{USER_RESULTS_NUMBERS}}

## Analysis
{{USER_KEY_OBSERVATIONS}}

## Next Steps
{{USER_NEXT_STEPS}}
```

**Auto-filled:** `date`, `git_head`, Changes section (from git_context.py)  
**User confirms:** `experiment` slug, Goal, Results, Analysis, Next Steps

---

## daily — Daily Research Mode Template

```markdown
---
date: {{DATE}}
experiment: daily-{{DATE}}
mode: daily
tags: [reading, notes]
follows:
git_head:
slide_decks: []
amended: []
---

## Goal
Daily research session.

## Analysis
**Read / Worked on:** {{USER_TOPIC}}

**Key Insight:** {{USER_KEY_INSIGHT}}

## Next Steps
**Open questions:** {{USER_OPEN_QUESTIONS}}
```

**Auto-filled:** `date`, `experiment` slug  
**User confirms:** topic, key insight, open questions

---

## explore — Exploration Mode Template

```markdown
---
date: {{DATE}}
experiment: explore-{{TOPIC_SLUG}}
mode: explore
tags: [deep-research, literature]
follows:
git_head:
slide_decks: []
amended: []
---

## Goal
{{DEEP_RESEARCH_QUESTION}}

## Analysis
{{DEEP_RESEARCH_EXECUTIVE_SUMMARY}}

## Conclusion
{{KEY_FINDINGS_BULLETS}}

## Next Steps
{{USER_NEXT_STEPS}}
```

**Auto-filled:** `date`, Goal (from RQ Brief), Analysis (from Executive Summary)  
**User confirms:** topic slug, Next Steps

### explore sub-modes

**systematic-review:** same template; Analysis section = PRISMA flow summary + inclusion/exclusion counts.  
**lit-review:** same template; Analysis section = thematic clusters from synthesis.  
**fact-check:** Analysis section = claim-by-claim verdict table (Supported / Unsupported / Inconclusive).

---

## report — Report Mode Template

```markdown
---
date: {{DATE}}
experiment: report-{{TOPIC_SLUG}}
mode: report
tags: [slides, presentation]
follows:
git_head:
slide_decks:
  - {{SLIDE_DECK_PATH}}
amended: []
---

## Goal
Generate presentation slides.

## Analysis
**Audience:** {{USER_AUDIENCE}}
**Slide deck:** {{SLIDE_DECK_PATH}}

## Conclusion
{{USER_CONCLUSION}}

## Next Steps
{{USER_NEXT_STEPS}}
```

**Auto-filled:** `date`, `slide_decks` path (from report-slides output)  
**User confirms:** topic slug, audience, conclusion, next steps

---

## publish — Publication Mode Template

```markdown
---
date: {{DATE}}
experiment: publish-{{PAPER_SLUG}}-stage{{STAGE_NUMBER}}
mode: publish
tags: [academic-pipeline, stage-{{STAGE_NUMBER}}]
follows: {{PRIOR_PUBLISH_LOG_OR_EMPTY}}
git_head:
slide_decks: []
amended: []
---

## Goal
Academic pipeline — Stage {{STAGE_NUMBER}}: {{STAGE_NAME}}

## Analysis
**Stage result:** {{STAGE_RESULT}}
**Key deliverables:** {{DELIVERABLES_LIST}}

## Next Steps
{{USER_NEXT_STEPS}}
```

**Stage name map:**
| Number | Name |
|--------|------|
| 1 | RESEARCH |
| 2 | WRITE |
| 2.5 | INTEGRITY CHECK |
| 3 | REVIEW |
| 4 | REVISE |
| 4.5 | FINAL INTEGRITY |
| 5 | FINALIZE |

**Auto-filled:** `date`, `experiment` slug (from stage number), Goal section  
**User confirms:** paper slug, stage result, deliverables, next steps
EOF
```

- [ ] **Step 2: Verify all 5 mode templates are present**

```bash
grep -c "^## exp\|^## daily\|^## explore\|^## report\|^## publish" skills/research-mode/references/mode_templates.md
```

Expected: `5`

- [ ] **Step 3: Commit**

```bash
git add skills/research-mode/references/mode_templates.md
git commit -m "feat: add mode_templates.md with 5 mode draft templates"
```

---

### Task 5: Create `routing_guide.md`

**Files:**
- Create: `skills/research-mode/references/routing_guide.md`

- [ ] **Step 1: Write the routing guide**

```bash
cat > skills/research-mode/references/routing_guide.md << 'EOF'
# Research Mode — Routing Guide

Maps each work mode to the skills it uses and the behaviors it expects.

## Mode × Skills Matrix

| Mode | Primary Skill | Secondary Skills | Blocked Unless Asked |
|------|--------------|-----------------|----------------------|
| `exp` | research-log (Full) | report-slides | deep-research, academic-pipeline |
| `daily` | — (freeform) | research-log (Quick) | deep-research, academic-pipeline |
| `explore` | deep-research | research-log | academic-pipeline |
| `report` | report-slides | research-log | academic-pipeline |
| `publish` | academic-pipeline | research-log | — |

## Mode Transition Recommendations

| From | To | Trigger |
|------|----|---------|
| `explore` | `publish` | deep-research report complete, ready to write |
| `exp` | `report` | experiment results ready to present |
| `exp` | `publish` | experiment supports a paper submission |
| `publish` | `report` | paper milestone ready for group presentation |
| any | `daily` | no structured output goal, just reading |

## deep-research Sub-Mode Routing

When in `explore` mode, select the deep-research sub-mode based on intent:

| User intent | deep-research mode |
|------------|-------------------|
| "I want to explore / understand this topic" | `socratic` or `full` |
| "I need a systematic review with PRISMA" | `systematic-review` |
| "I need a literature review section" | `lit-review` |
| "I need to verify a specific claim" | `fact-check` |

## ARS Slash Command → Mode Mapping (Phase 3)

When these commands are invoked, auto-activate `publish` mode:

| Command | Pipeline entry point |
|---------|---------------------|
| `/ars-full` | Stage 1 (fresh start) |
| `/ars-plan` | Stage 2 (plan mode) |
| `/ars-outline` | Stage 2 (outline only) |
| `/ars-revision` | Stage 4 (revision) |
| `/ars-revision-coach` | Stage 4 (coached revision) |
| `/ars-abstract` | Stage 2 (abstract only) |
| `/ars-lit-review` | Stage 1 (lit-review mode) |
| `/ars-format` | Stage 5 (format convert) |
| `/ars-citation-check` | Stage 2.5 (citation only) |
| `/ars-disclosure` | Stage 5 (disclosure) |

Note: ARS command hooks are implemented in Phase 3. This file documents the intended mapping.
EOF
```

- [ ] **Step 2: Verify table rows**

```bash
grep -c "^|" skills/research-mode/references/routing_guide.md
```

Expected: at least 20 table rows.

- [ ] **Step 3: Commit**

```bash
git add skills/research-mode/references/routing_guide.md
git commit -m "feat: add routing_guide.md with mode × skills matrix"
```

---

### Task 6: Extend `research-log` SKILL.md

**Files:**
- Modify: `skills/research-log/SKILL.md`

The extension adds three things:
1. `mode:` field in the frontmatter template
2. Instructions for pre-filled `add` (when called from research-mode)
3. `Mode` column in the INDEX.md spec

- [ ] **Step 1: Add `mode:` field to the frontmatter template in SKILL.md**

Find the frontmatter block (around line 88–98) and add `mode:` after `experiment:`:

Old block:
```
---
date: YYYY-MM-DD
experiment: <slug>
tags: []
follows: <prior-filename-or-empty>
reason_follows: <one-line reason or empty>
git_head: <short SHA from git_context.py --head, or empty if not a git repo>
slide_decks: []
amended: []
---
```

New block:
```
---
date: YYYY-MM-DD
experiment: <slug>
mode: <exp|daily|explore|report|publish, or omit if unknown>
tags: []
follows: <prior-filename-or-empty>
reason_follows: <one-line reason or empty>
git_head: <short SHA from git_context.py --head, or empty if not a git repo>
slide_decks: []
amended: []
---
```

- [ ] **Step 2: Update INDEX.md column spec**

Find the INDEX.md table line (around line 175–183):

Old:
```
| Date | Experiment | Tags | Follows | HEAD | Slides |
|------|-----------|------|---------|------|--------|
| 2024-11-02 | run_v2 | training, ablation | run_v1 | a1b2c3d | ✅ reports/2024-11-05 |
| 2024-10-28 | run_v1 | baseline | — | e4f5g6h | ❌ |
```

New:
```
| Date | Experiment | Mode | Tags | Follows | HEAD | Slides |
|------|-----------|------|------|---------|------|--------|
| 2024-11-02 | run_v2 | exp | training, ablation | run_v1 | a1b2c3d | ✅ reports/2024-11-05 |
| 2024-10-28 | run_v1 | — | baseline | — | e4f5g6h | ❌ |
```

- [ ] **Step 3: Add pre-filled `add` instructions after the existing `add` command section**

After the "Rebuild INDEX.md after saving." line near the end of the `add` section, append:

```markdown
### Pre-filled add (called from research-mode)

When `/research-log add` is invoked by `research-mode` with pre-filled data:
- Skip interactive questions for fields already provided in the pre-filled draft
- Only ask for fields that are empty or marked `{{PLACEHOLDER}}`
- The `mode:` field is always set by research-mode; do not ask the user for it
- After writing the file, update `slide_decks:` in the calling log entry if applicable
```

- [ ] **Step 4: Update INDEX rebuild rule for Mode column**

Find the INDEX rules section and add: `Mode` = `mode` frontmatter value, or `—` if absent.

- [ ] **Step 5: Verify the changes**

```bash
grep -n "mode:" skills/research-log/SKILL.md | head -10
grep -n "Mode" skills/research-log/SKILL.md | head -10
grep -n "Pre-filled" skills/research-log/SKILL.md
```

Expected: `mode:` appears in frontmatter template; `Mode` appears in INDEX table; `Pre-filled` appears once.

- [ ] **Step 6: Commit**

```bash
git add skills/research-log/SKILL.md
git commit -m "feat: extend research-log with mode field, INDEX Mode column, and pre-filled add support"
```

---

### Task 7: Update `install.sh`

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add `research-mode` to the SKILLS array**

Old line:
```bash
SKILLS=("research-log" "report-slides")
```

New line:
```bash
SKILLS=("research-log" "report-slides" "research-mode")
```

- [ ] **Step 2: Update the confirmation message**

Old:
```bash
echo "Restart Claude Code — /research-log and /report-slides will be available."
```

New:
```bash
echo "Restart Claude Code — /research-log, /report-slides, and /mode will be available."
```

- [ ] **Step 3: Verify dry run (no internet needed)**

```bash
bash -n install.sh && echo "Syntax OK"
```

Expected: `Syntax OK`

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "feat: add research-mode to install.sh SKILLS array"
```

---

## Phase 2: Bridge Layer

---

### Task 8: Write tests for `passport_to_log.py`

**Files:**
- Create: `bridge/scripts/__init__.py`
- Create: `bridge/scripts/tests/__init__.py`
- Create: `bridge/scripts/tests/test_passport_to_log.py`

- [ ] **Step 1: Create `__init__.py` files**

```bash
touch bridge/__init__.py bridge/scripts/__init__.py bridge/scripts/tests/__init__.py
```

- [ ] **Step 2: Write the test file**

```bash
cat > bridge/scripts/tests/test_passport_to_log.py << 'EOF'
"""Tests for passport_to_log.py — Material Passport → research-log bridge."""
import textwrap
from datetime import date
import pytest
import yaml

# Import will fail until passport_to_log.py is created — that's expected (TDD).
from bridge.scripts.passport_to_log import (
    parse_passport,
    extract_latest_stage,
    draft_log_entry,
    PassportParseError,
)

MINIMAL_PASSPORT = textwrap.dedent("""\
    material_passport:
      version: "9"
      paper_slug: test_paper
      stages:
        - stage: 1
          name: RESEARCH
          status: PASS
          completed_at: "2026-06-10"
          deliverables:
            - Research Question Brief
            - Methodology Blueprint
""")

MULTI_STAGE_PASSPORT = textwrap.dedent("""\
    material_passport:
      version: "9"
      paper_slug: my_hei_paper
      stages:
        - stage: 1
          name: RESEARCH
          status: PASS
          completed_at: "2026-06-08"
          deliverables:
            - Research Question Brief
        - stage: 2
          name: WRITE
          status: PASS
          completed_at: "2026-06-10"
          deliverables:
            - Full Draft
            - Bilingual Abstract
        - stage: 2.5
          name: INTEGRITY CHECK
          status: PENDING
          completed_at: null
          deliverables: []
""")

IN_PROGRESS_PASSPORT = textwrap.dedent("""\
    material_passport:
      version: "9"
      paper_slug: in_progress
      stages:
        - stage: 1
          name: RESEARCH
          status: IN_PROGRESS
          completed_at: null
          deliverables: []
""")


class TestParsePassport:
    def test_parses_valid_yaml(self):
        result = parse_passport(MINIMAL_PASSPORT)
        assert result["version"] == "9"
        assert result["paper_slug"] == "test_paper"
        assert len(result["stages"]) == 1

    def test_raises_on_missing_material_passport_key(self):
        with pytest.raises(PassportParseError, match="material_passport"):
            parse_passport("stages: []")

    def test_raises_on_invalid_yaml(self):
        with pytest.raises(PassportParseError):
            parse_passport("{bad: yaml: :")

    def test_raises_on_missing_stages(self):
        with pytest.raises(PassportParseError, match="stages"):
            parse_passport("material_passport:\n  version: '9'\n")


class TestExtractLatestStage:
    def test_returns_latest_completed_stage(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        assert stage["stage"] == 2
        assert stage["name"] == "WRITE"
        assert stage["status"] == "PASS"

    def test_returns_in_progress_stage_if_no_completed(self):
        passport = parse_passport(IN_PROGRESS_PASSPORT)
        stage = extract_latest_stage(passport)
        assert stage["stage"] == 1
        assert stage["status"] == "IN_PROGRESS"

    def test_prefers_latest_by_stage_number(self):
        passport = parse_passport(MINIMAL_PASSPORT)
        stage = extract_latest_stage(passport)
        assert stage["stage"] == 1

    def test_returns_pending_if_no_pass_or_in_progress(self):
        passport_yaml = textwrap.dedent("""\
            material_passport:
              version: "9"
              paper_slug: p
              stages:
                - stage: 2.5
                  name: INTEGRITY CHECK
                  status: PENDING
                  completed_at: null
                  deliverables: []
        """)
        passport = parse_passport(passport_yaml)
        stage = extract_latest_stage(passport)
        assert stage["name"] == "INTEGRITY CHECK"


class TestDraftLogEntry:
    def test_draft_contains_required_frontmatter_fields(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "date: 2026-06-10" in draft
        assert "mode: publish" in draft
        assert "experiment: publish-my_hei_paper-stage2" in draft

    def test_draft_contains_stage_name_in_goal(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "WRITE" in draft
        assert "Stage 2" in draft

    def test_draft_lists_deliverables(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "Full Draft" in draft
        assert "Bilingual Abstract" in draft

    def test_draft_shows_pass_status(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "PASS" in draft

    def test_draft_has_next_steps_placeholder(self):
        passport = parse_passport(MINIMAL_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "Next Steps" in draft
        assert "{{NEXT_STEPS}}" in draft
EOF
```

- [ ] **Step 3: Run tests to confirm they fail (expected)**

```bash
cd /path/to/project && python -m pytest bridge/scripts/tests/test_passport_to_log.py -v 2>&1 | head -30
```

Expected: `ImportError` or `ModuleNotFoundError` — passport_to_log.py does not exist yet.

- [ ] **Step 4: Commit the failing tests**

```bash
git add bridge/
git commit -m "test: add failing tests for passport_to_log.py (TDD)"
```

---

### Task 9: Implement `passport_to_log.py`

**Files:**
- Create: `bridge/scripts/passport_to_log.py`

- [ ] **Step 1: Write the implementation**

```bash
cat > bridge/scripts/passport_to_log.py << 'EOF'
#!/usr/bin/env python3
"""
passport_to_log.py — Material Passport → research-log bridge.

Usage:
    python passport_to_log.py --passport <path>   # read from file
    python passport_to_log.py --stdin             # read YAML from stdin
    python passport_to_log.py --passport <path> --paper-slug <slug>  # override slug

Output: pre-filled research-log Markdown entry (stdout).
"""
import argparse
import sys
from datetime import date
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


class PassportParseError(ValueError):
    pass


def parse_passport(text: str) -> Dict[str, Any]:
    """Parse Material Passport YAML text. Raises PassportParseError on bad input."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise PassportParseError("Invalid YAML: {}".format(exc)) from exc

    if not isinstance(data, dict) or "material_passport" not in data:
        raise PassportParseError(
            "Expected top-level key 'material_passport' not found."
        )

    passport = data["material_passport"]
    if "stages" not in passport:
        raise PassportParseError("Passport missing required 'stages' field.")

    return passport


# Status priority: higher = more "in progress / latest"
_STATUS_PRIORITY = {"PASS": 3, "IN_PROGRESS": 2, "PENDING": 1, "FAIL": 0}


def extract_latest_stage(passport: Dict[str, Any]) -> Dict[str, Any]:
    """Return the most recent meaningful stage from the passport."""
    stages = passport.get("stages", [])
    if not stages:
        raise PassportParseError("Passport has no stages.")

    # Sort by status priority (descending), then by stage number (descending)
    def sort_key(s):
        status_val = _STATUS_PRIORITY.get(str(s.get("status", "PENDING")).upper(), 0)
        stage_num = float(s.get("stage", 0))
        return (status_val, stage_num)

    return sorted(stages, key=sort_key, reverse=True)[0]


def _stage_num_str(stage: Dict[str, Any]) -> str:
    """Format stage number as string, e.g. 2 → '2', 2.5 → '2_5'."""
    num = stage.get("stage", 0)
    return str(num).replace(".", "_")


def draft_log_entry(
    passport: Dict[str, Any],
    stage: Dict[str, Any],
    today: Optional[date] = None,
) -> str:
    """Produce a pre-filled research-log Markdown draft for the given stage."""
    if today is None:
        today = date.today()

    paper_slug = passport.get("paper_slug", "paper")
    stage_num = _stage_num_str(stage)
    stage_name = stage.get("name", "UNKNOWN")
    stage_num_raw = stage.get("stage", "?")
    stage_status = str(stage.get("status", "PENDING")).upper()
    deliverables = stage.get("deliverables") or []
    deliverables_md = "\n".join(f"- {d}" for d in deliverables) if deliverables else "- (none recorded)"

    return f"""\
---
date: {today.isoformat()}
experiment: publish-{paper_slug}-stage{stage_num}
mode: publish
tags: [academic-pipeline, stage-{stage_num}]
follows:
git_head:
slide_decks: []
amended: []
---

## Goal
Academic pipeline — Stage {stage_num_raw}: {stage_name}

## Analysis
**Stage result:** {stage_status}

**Key deliverables:**
{deliverables_md}

## Next Steps
{{{{NEXT_STEPS}}}}
"""


def main():
    parser = argparse.ArgumentParser(description="Convert Material Passport to research-log draft.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--passport", metavar="PATH", help="Path to passport YAML file")
    group.add_argument("--stdin", action="store_true", help="Read YAML from stdin")
    parser.add_argument("--paper-slug", metavar="SLUG", help="Override paper slug")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    else:
        try:
            with open(args.passport, encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.passport}", file=sys.stderr)
            sys.exit(1)

    try:
        passport = parse_passport(text)
    except PassportParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.paper_slug:
        passport["paper_slug"] = args.paper_slug

    stage = extract_latest_stage(passport)
    print(draft_log_entry(passport, stage))


if __name__ == "__main__":
    main()
EOF
```

- [ ] **Step 2: Run tests — expect all to pass**

```bash
python -m pytest bridge/scripts/tests/test_passport_to_log.py -v
```

Expected output (all green):
```
test_passport_to_log.py::TestParsePassport::test_parses_valid_yaml PASSED
test_passport_to_log.py::TestParsePassport::test_raises_on_missing_material_passport_key PASSED
test_passport_to_log.py::TestParsePassport::test_raises_on_invalid_yaml PASSED
test_passport_to_log.py::TestParsePassport::test_raises_on_missing_stages PASSED
test_passport_to_log.py::TestExtractLatestStage::test_returns_latest_completed_stage PASSED
test_passport_to_log.py::TestExtractLatestStage::test_returns_in_progress_stage_if_no_completed PASSED
test_passport_to_log.py::TestExtractLatestStage::test_prefers_latest_by_stage_number PASSED
test_passport_to_log.py::TestExtractLatestStage::test_returns_pending_if_no_pass_or_in_progress PASSED
test_passport_to_log.py::TestDraftLogEntry::test_draft_contains_required_frontmatter_fields PASSED
test_passport_to_log.py::TestDraftLogEntry::test_draft_contains_stage_name_in_goal PASSED
test_passport_to_log.py::TestDraftLogEntry::test_draft_lists_deliverables PASSED
test_passport_to_log.py::TestDraftLogEntry::test_draft_shows_pass_status PASSED
test_passport_to_log.py::TestDraftLogEntry::test_draft_has_next_steps_placeholder PASSED
13 passed in 0.xxs
```

- [ ] **Step 3: Smoke test with sample input**

```bash
python bridge/scripts/passport_to_log.py --stdin << 'YAML'
material_passport:
  version: "9"
  paper_slug: hei_quality_ai
  stages:
    - stage: 1
      name: RESEARCH
      status: PASS
      completed_at: "2026-06-10"
      deliverables:
        - Research Question Brief
        - Methodology Blueprint
YAML
```

Expected: valid Markdown with `experiment: publish-hei_quality_ai-stage1`, `mode: publish`, `PASS`.

- [ ] **Step 4: Commit**

```bash
git add bridge/scripts/passport_to_log.py bridge/__init__.py bridge/scripts/__init__.py bridge/scripts/tests/__init__.py
git commit -m "feat: implement passport_to_log.py with full TDD test suite (13 tests)"
```

---

### Task 10: Create `passport_log_schema.md`

**Files:**
- Create: `bridge/references/passport_log_schema.md`

- [ ] **Step 1: Write the schema document**

```bash
cat > bridge/references/passport_log_schema.md << 'EOF'
# Passport Log Schema

Documents the expected YAML structure of a Material Passport (Schema 9)
that `bridge/scripts/passport_to_log.py` can parse.

## Minimum Required Structure

```yaml
material_passport:
  version: "9"          # string, must be present
  paper_slug: <slug>    # string, used in log filename slug
  stages:               # list, must have at least one entry
    - stage: <number>   # float or int (2.5 is valid for integrity check)
      name: <string>    # e.g. RESEARCH, WRITE, INTEGRITY CHECK, REVIEW, REVISE
      status: <enum>    # PASS | IN_PROGRESS | PENDING | FAIL
      completed_at: <YYYY-MM-DD or null>
      deliverables:     # list of strings, may be empty
        - <string>
```

## Stage Number Reference

| Stage | Name | Notes |
|-------|------|-------|
| 1 | RESEARCH | deep-research output |
| 2 | WRITE | academic-paper draft |
| 2.5 | INTEGRITY CHECK | mandatory; citation + data verification |
| 3 | REVIEW | academic-paper-reviewer output |
| 4 | REVISE | post-review revision |
| 4.5 | FINAL INTEGRITY | mandatory; final citation check |
| 5 | FINALIZE | formatting + output |

## Status Semantics

| Status | Meaning |
|--------|---------|
| `PASS` | Stage completed and passed all quality gates |
| `IN_PROGRESS` | Stage is currently active |
| `PENDING` | Stage not yet started |
| `FAIL` | Stage failed a hard gate (rare; usually requires manual resolution) |

## Optional Fields (ignored by bridge script)

```yaml
material_passport:
  reset_boundary: []      # Schema 9 cross-session resume (v3.6.3)
  compliance_history: []  # PRISMA-trAIce / RAISE audit trail (v3.4)
  literature_corpus: []   # User-provided bibliography corpus (v3.6.4)
```

## How to Save a Passport from academic-pipeline

In an academic-pipeline session, the orchestrator emits a YAML block labeled
`## Material Passport` at each FULL checkpoint. Copy that block to a `.yaml` file,
then run:

```bash
python bridge/scripts/passport_to_log.py --passport passport.yaml
```

The output is a pre-filled research-log entry. Pipe it to a file or copy-paste into
a `/research-log add` session.
EOF
```

- [ ] **Step 2: Verify file**

```bash
grep -c "^|" bridge/references/passport_log_schema.md
```

Expected: at least 10 table rows.

- [ ] **Step 3: Create Phase 3 stub for ARS command hooks**

```bash
cat > bridge/references/ars_command_hooks.md << 'EOF'
# ARS Command Hooks — Phase 3 Stub

This file documents the intended integration between `/ars-*` slash commands
and `research-mode`. Implementation is deferred to Phase 3.

## Planned Behavior

When any `/ars-*` command is invoked:
1. `research-mode` automatically activates `publish` mode (if not already active)
2. The command runs normally via academic-research-skills
3. On command completion, `research-mode` offers `/mode end` to log the stage

## Command → Stage Mapping

| Command | Pipeline stage |
|---------|---------------|
| `/ars-full` | Stage 1 (fresh start) |
| `/ars-plan` | Stage 2 (plan mode) |
| `/ars-outline` | Stage 2 (outline only) |
| `/ars-revision` | Stage 4 (revision) |
| `/ars-revision-coach` | Stage 4 (coached) |
| `/ars-abstract` | Stage 2 (abstract only) |
| `/ars-lit-review` | Stage 1 (lit-review) |
| `/ars-format` | Stage 5 (format convert) |
| `/ars-citation-check` | Stage 2.5 |
| `/ars-disclosure` | Stage 5 (disclosure) |

## Implementation Note (Phase 3)

The hook mechanism will use CLAUDE.md routing rules to detect `/ars-*` invocations
and auto-activate publish mode. No changes to academic-research-skills are needed.
EOF
```

- [ ] **Step 4: Commit**

```bash
git add bridge/references/
git commit -m "docs: add passport_log_schema.md and ars_command_hooks.md stub"
```

---

### Task 11: Extend `report-slides` SKILL.md

**Files:**
- Modify: `skills/report-slides/SKILL.md`

Add academic data source support: a new `--source academic` flag that reads from
`passport_to_log.py` output instead of `docs/research_log/`.

- [ ] **Step 1: Add `academic` data source section after the "Show available logs" section**

Find the `### 1. Show available logs` section (around line 72) and add after it:

```markdown
### 1b. Academic data source (optional)

When the user passes `--source academic` or selects "academic pipeline" as source:

1. Check for a passport YAML file (default: `docs/passport.yaml`; override with `--passport <path>`)
2. Run the bridge script to extract stage data:
   ```bash
   BRIDGE="$(find ~/.claude -path "*/research-skills/bridge/scripts/passport_to_log.py" \
             -o -path "*/claude-research-skills/bridge/scripts/passport_to_log.py" 2>/dev/null | head -1)"
   python "$BRIDGE" --passport docs/passport.yaml
   ```
3. Use the extracted stage records as input for slide generation instead of research-log entries

If no passport file exists, fall back to research-log source and notify the user.
```

- [ ] **Step 2: Add two new slide types to the Python renderer section**

Add after the existing `conclusion` type in the JSON format section:

```json
{ "index": 9, "type": "score_trajectory",
  "title": "Review Score Progression",
  "dimensions": ["Originality", "Methodology", "Clarity", "Citations", "Contribution"],
  "rounds": [
    { "label": "Round 1", "scores": [3, 4, 3, 2, 3] },
    { "label": "Round 2", "scores": [4, 4, 4, 4, 4] }
  ],
  "note": "D1–D5 rubric, scale 1–5" },

{ "index": 10, "type": "pipeline_status",
  "title": "Pipeline Progress",
  "stages": [
    { "number": 1, "name": "RESEARCH", "status": "PASS", "date": "2026-06-08" },
    { "number": 2, "name": "WRITE",    "status": "PASS", "date": "2026-06-10" },
    { "number": 2.5, "name": "INTEGRITY", "status": "PENDING", "date": null }
  ]}
```

- [ ] **Step 3: Add these types to the `generate_slides.py` supported types list**

Find the "Supported types:" line and add `score_trajectory` and `pipeline_status`:

Old:
```
**Supported types:** `title` `bullet_list` `bar_chart` `table` `metric_cards` `two_column` `timeline` `conclusion`
```

New:
```
**Supported types:** `title` `bullet_list` `bar_chart` `table` `metric_cards` `two_column` `timeline` `conclusion` `score_trajectory` `pipeline_status`
```

- [ ] **Step 4: Add academic source to the Ask section (question 1)**

Find `### 2. Ask (one message)` and update question 1:

Old:
```
1. Which logs to include? (`all` / `recent-N` / by name / date range)
```

New:
```
1. Source? (`research-log` = experiment logs (default) / `academic` = pipeline passport data)
   If research-log: which logs? (`all` / `recent-N` / by name / date range)
   If academic: passport file path? (default: `docs/passport.yaml`)
```

- [ ] **Step 5: Verify changes**

```bash
grep -n "score_trajectory\|pipeline_status\|academic.*source\|--source" skills/report-slides/SKILL.md | head -15
```

Expected: at least 4 matches.

- [ ] **Step 6: Commit**

```bash
git add skills/report-slides/SKILL.md
git commit -m "feat: extend report-slides with academic data source and score_trajectory/pipeline_status slide types"
```

---

### Task 12: Final Verification

- [ ] **Step 1: Run all tests**

```bash
python -m pytest bridge/ -v
```

Expected: 13 passed, 0 failed.

- [ ] **Step 2: Verify all planned files exist**

```bash
find skills/research-mode skills/research-log skills/report-slides bridge .claude -name "*.md" -o -name "*.py" -o -name "*.sh" | sort
```

Confirm these exist:
- `skills/research-mode/SKILL.md`
- `skills/research-mode/references/mode_templates.md`
- `skills/research-mode/references/routing_guide.md`
- `bridge/scripts/passport_to_log.py`
- `bridge/scripts/tests/test_passport_to_log.py`
- `bridge/references/passport_log_schema.md`
- `bridge/references/ars_command_hooks.md`
- `.claude/CLAUDE.md`

- [ ] **Step 3: Verify install.sh includes research-mode**

```bash
grep "research-mode" install.sh
```

Expected: `SKILLS=("research-log" "report-slides" "research-mode")`

- [ ] **Step 4: Verify research-log has mode field**

```bash
grep "^mode:" skills/research-log/SKILL.md
```

Expected: one match in the frontmatter template.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: final Phase 1+2 integration verification pass"
```

---

## Phase 3–4 TODO Items

These are tracked here for reference. Each will need its own implementation plan.

**Phase 3:**
- [ ] `bridge/scripts/score_extractor.py` — parse reviewer D1–D7 scores and append to publish-mode log
- [ ] `bridge/scripts/ars_log_hook.py` — CLAUDE.md routing hook for `/ars-*` auto-activating publish mode
- [ ] Add 3 deep-research sub-mode templates (systematic-review, lit-review, fact-check) to `mode_templates.md`
- [ ] `ai_reflection` optional section in publish-mode log template

**Phase 4:**
- [ ] `bridge/scripts/collab_depth_logger.py` — Collaboration Depth Observer → log
- [ ] `citation_stats` optional block in publish-mode log template
- [ ] `sprint_contract_summary` optional block in publish-mode log template
