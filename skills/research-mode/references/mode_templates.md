# Mode Log Draft Templates

Used by `research-mode` during `/mode end` to pre-fill `research-log` entries.
Each template maps to a `mode:` value in the research-log frontmatter.

---

## exp — Experiment Mode Template

```
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

```
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

```
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

```
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

```
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

---
