#!/usr/bin/env bash
# claude-research-skills installer
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/claude-research-skills/main/install.sh)
#   bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/claude-research-skills/main/install.sh) --local
#   bash <(curl -fsSL https://raw.githubusercontent.com/starpig1129/claude-research-skills/main/install.sh) uninstall
set -e

REPO="https://github.com/starpig1129/claude-research-skills.git"
SKILLS=("research-log" "report-slides" "research-mode")

# ── parse args ────────────────────────────────────────────────────────────────
CMD="install"
GLOBAL=true
for arg in "$@"; do
  case "$arg" in
    uninstall) CMD="uninstall" ;;
    --local)   GLOBAL=false ;;
  esac
done

if $GLOBAL; then
  DEST="$HOME/.claude/skills"
else
  DEST="$(pwd)/.claude/skills"
fi

# ── install ───────────────────────────────────────────────────────────────────
install_skills() {
  command -v git >/dev/null 2>&1 || { echo "Error: git is required"; exit 1; }

  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT

  echo "Downloading claude-research-skills..."
  git clone --depth 1 "$REPO" "$TMP/repo" -q

  mkdir -p "$DEST"
  for skill in "${SKILLS[@]}"; do
    cp -r "$TMP/repo/skills/$skill" "$DEST/"
    echo "  ✓ $skill"
  done

  echo ""
  echo "Installed to: $DEST"
  echo "Restart Claude Code — /research-log, /report-slides, and /mode will be available."
}

# ── uninstall ─────────────────────────────────────────────────────────────────
uninstall_skills() {
  for skill in "${SKILLS[@]}"; do
    target="$DEST/$skill"
    if [ -d "$target" ]; then
      rm -rf "$target"
      echo "  ✓ Removed: $target"
    else
      echo "  - Not found (skipped): $target"
    fi
  done
  echo "Done."
}

# ── main ──────────────────────────────────────────────────────────────────────
case "$CMD" in
  install)   install_skills ;;
  uninstall) uninstall_skills ;;
esac
