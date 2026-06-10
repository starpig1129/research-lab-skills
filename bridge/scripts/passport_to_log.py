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
    deliverables_md = (
        "\n".join("- {}".format(d) for d in deliverables)
        if deliverables
        else "- (none recorded)"
    )

    return (
        "---\n"
        "date: {date}\n"
        "experiment: publish-{slug}-stage{stage_num}\n"
        "mode: publish\n"
        "tags: [academic-pipeline, stage-{stage_num}]\n"
        "follows:\n"
        "git_head:\n"
        "slide_decks: []\n"
        "amended: []\n"
        "---\n"
        "\n"
        "## Goal\n"
        "Academic pipeline — Stage {stage_num_raw}: {stage_name}\n"
        "\n"
        "## Analysis\n"
        "**Stage result:** {stage_status}\n"
        "\n"
        "**Key deliverables:**\n"
        "{deliverables_md}\n"
        "\n"
        "## Next Steps\n"
        "{{{{NEXT_STEPS}}}}\n"
    ).format(
        date=today.isoformat(),
        slug=paper_slug,
        stage_num=stage_num,
        stage_num_raw=stage_num_raw,
        stage_name=stage_name,
        stage_status=stage_status,
        deliverables_md=deliverables_md,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Convert Material Passport to research-log draft."
    )
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
            print("Error: file not found: {}".format(args.passport), file=sys.stderr)
            sys.exit(1)

    try:
        passport = parse_passport(text)
    except PassportParseError as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        sys.exit(1)

    if args.paper_slug:
        passport["paper_slug"] = args.paper_slug

    stage = extract_latest_stage(passport)
    print(draft_log_entry(passport, stage))


if __name__ == "__main__":
    main()
