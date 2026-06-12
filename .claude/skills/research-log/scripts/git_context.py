#!/usr/bin/env python3
"""git_context.py — Extract git history to assist research log entry creation.

Usage:
    # History since a date
    python git_context.py --since 2024-11-01

    # History since the date recorded in a prior log entry
    python git_context.py --since-log docs/research_log/2024-11-01_run_v1.md

    # Just print current HEAD SHA (for writing to git_head in frontmatter)
    python git_context.py --head
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


# ── Git helpers ───────────────────────────────────────────────────────────────

def _git(*args: str) -> str:
    result = subprocess.run(
        ["git"] + list(args), capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def is_git_repo() -> bool:
    return bool(_git("rev-parse", "--git-dir"))


def current_head() -> str:
    return _git("rev-parse", "--short", "HEAD")


# ── Log file helpers ───────────────────────────────────────────────────────────

def read_date_from_log(path: str) -> str:
    """Read the `date:` field from a research log file's YAML frontmatter."""
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^date:\s*(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    print(f"Error: no `date:` field found in {path}", file=sys.stderr)
    sys.exit(1)


# ── Git data extraction ───────────────────────────────────────────────────────

def get_commits(since: str) -> list:
    raw = _git(
        "log", f"--since={since} 00:00:00",
        "--format=%H|%ad|%an|%s", "--date=short"
    )
    commits = []
    for line in raw.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash":    parts[0][:7],
                "date":    parts[1],
                "author":  parts[2],
                "message": parts[3],
            })
    return commits


def get_changed_files(since: str) -> list:
    raw = _git(
        "log", f"--since={since} 00:00:00",
        "--name-only", "--format=", "--diff-filter=ACMRD"
    )
    # Deduplicate while preserving order
    seen = set()
    files = []
    for f in raw.splitlines():
        f = f.strip()
        if f and f not in seen:
            seen.add(f)
            files.append(f)
    return files


def group_files(files: list) -> dict:
    groups: dict = {}
    for f in files:
        ext = Path(f).suffix.lower() or "(no ext)"
        groups.setdefault(ext, []).append(f)
    return groups


def strip_conventional(msg: str) -> str:
    """Remove conventional-commit prefix: 'feat(scope): msg' -> 'msg'"""
    return re.sub(r"^[a-z]+(\([^)]+\))?!?:\s*", "", msg, flags=re.IGNORECASE).strip()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extract git history to assist research log entry creation"
    )
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--since",     metavar="DATE",
                     help="Show commits since YYYY-MM-DD")
    grp.add_argument("--since-log", metavar="FILE",
                     help="Read start date from a research log file's frontmatter")
    grp.add_argument("--head",      action="store_true",
                     help="Print current HEAD short SHA and exit")
    args = ap.parse_args()

    if not is_git_repo():
        print("(not a git repository — skipping git context)")
        return

    if args.head:
        sha = current_head()
        print(sha if sha else "(no commits yet)")
        return

    since = args.since or read_date_from_log(args.since_log)

    commits     = get_commits(since)
    files       = get_changed_files(since)
    file_groups = group_files(files)
    head        = current_head()

    # ── Report ────────────────────────────────────────────────────────────────
    authors = {c["author"] for c in commits}
    print(f"Git context since {since}:")
    print(f"  {len(commits)} commit(s) · {len(files)} file(s) changed · {len(authors)} author(s)")
    print()

    if commits:
        print("Commits (newest first):")
        for c in commits:
            print(f"  {c['date']}  {c['hash']}  {c['message']}")
        print()

        bullets = [strip_conventional(c["message"]) for c in commits]
        print("Suggested Changes bullets:")
        for b in bullets:
            print(f"  - {b}")
        print()

    if file_groups:
        print(f"Changed files ({len(files)} unique):")
        for ext, flist in sorted(file_groups.items(), key=lambda x: -len(x[1])):
            preview = ", ".join(flist[:3])
            suffix  = f", +{len(flist) - 3} more" if len(flist) > 3 else ""
            print(f"  {ext:10s} {len(flist):3d}  {preview}{suffix}")
        print()

    print(f"Current HEAD: {head}")


if __name__ == "__main__":
    main()
