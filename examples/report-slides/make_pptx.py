#!/usr/bin/env python3
"""make_pptx.py — Convert slide*.svg → native-shape PPTX (fully editable in PowerPoint 365).

Uses the svg_to_pptx package bundled with the report-slides skill.
Every rect, text, line, and path becomes an independently editable PowerPoint object.

Usage:
    # Find the skill scripts dir and run:
    SCRIPTS=$(find ~/.claude -path "*/report-slides/scripts" -type d | head -1)
    cd "$SCRIPTS"
    python3 -m svg_to_pptx --slides /path/to/report-slides/ --out /path/to/deck.pptx

    # Or directly via this helper (requires svg_to_pptx on the path):
    python3 make_pptx.py --slides . --out deck.pptx
"""
import sys
from pathlib import Path


def main(slides_dir: str, out_path: str) -> None:
    scripts_dir = next(
        (p for p in [
            Path.home() / ".claude" / "skills" / "report-slides" / "scripts",
            Path(__file__).parent.parent.parent / "skills" / "report-slides" / "scripts",
        ] if (p / "svg_to_pptx").is_dir()),
        None,
    )
    if scripts_dir is None:
        print("ERROR: svg_to_pptx package not found. Install the report-slides skill first.")
        print("  bash install.sh  (from the repo root)")
        sys.exit(1)

    sys.path.insert(0, str(scripts_dir))
    from svg_to_pptx.converter import convert_file  # noqa: E402

    svg_files = sorted(Path(slides_dir).glob("slide*.svg"))
    if not svg_files:
        print(f"No slide*.svg in {slides_dir}")
        sys.exit(1)

    print(f"Converting {len(svg_files)} slide(s) → native shapes …")
    convert_file(slides_dir, out_path, verbose=True)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build editable PPTX from SVG slides.")
    ap.add_argument("--slides", required=True, help="Directory containing slide*.svg")
    ap.add_argument("--out",    required=True, help="Output .pptx path")
    args = ap.parse_args()
    main(args.slides, args.out)
