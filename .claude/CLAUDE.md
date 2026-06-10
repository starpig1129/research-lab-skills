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
