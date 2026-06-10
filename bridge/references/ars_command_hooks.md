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
