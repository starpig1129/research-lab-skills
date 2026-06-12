# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.0.0] - 2026-06-12

### Added

- **Unified `research-lab-skills` suite** — merged two independently-developed projects into a single repo with one install command. Lab-tools (experiment journal, slides, session mode routing) originally by ZI-YUE,CHAO; Academic Research Skills (deep research, paper writing, peer review, pipeline) originally by Cheng-I Wu. See [NOTICE.md](NOTICE.md) for full attribution.
- **7 skills in one install**: `research-log`, `report-slides`, `research-mode` (lab) + `deep-research`, `academic-paper`, `academic-paper-reviewer`, `academic-pipeline` (ARS).
- **Bash installer** (`install.sh`) with `--lab-only` / `--ars-only` / `uninstall` flags; works on macOS, Linux, and Git Bash.
- **npm package** (`crs` CLI) with `crs init` / `crs init --global` / `crs init --lab-only` / `crs init --ars-only`; supports Claude Code, Cursor, Windsurf, and Copilot targets.
- **Examples** for lab-tools skills: `examples/research-log/` (quick-mode + full-mode journal entries, INDEX.md) and `examples/report-slides/` (7-slide `slide_data.json`, rendered SVG samples, README).

---

*Academic Research Skills (ARS) upstream changelog: [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)*
