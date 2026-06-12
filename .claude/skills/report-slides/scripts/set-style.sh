#!/usr/bin/env bash
# set-style.sh <name> — copy a built-in style as the project default.
# Run from the project root:
#   bash "$(find ~/.claude -path "*/report-slides/scripts/set-style.sh" | head -1)" paper
set -e

STYLE="${1:-}"
if [ -z "$STYLE" ]; then
  echo "Usage: set-style.sh <name>"
  echo "Built-in styles: default  minimal  dark  paper"
  exit 1
fi

SRC="$(find ~/.claude -path "*/report-slides/references/styles/${STYLE}.md" | head -1)"
if [ -z "$SRC" ]; then
  echo "Error: style '${STYLE}' not found."
  echo "Built-in styles: default  minimal  dark  paper"
  exit 1
fi

mkdir -p docs/slides
cp "$SRC" docs/slides/_style.md
echo "Style set: docs/slides/_style.md  (${STYLE})"
