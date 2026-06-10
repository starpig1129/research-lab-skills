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
