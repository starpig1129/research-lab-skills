"""__main__.py — CLI entry point for svg_to_pptx package."""
import argparse
import sys
from pathlib import Path

from .converter import convert_file


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert SVG slides to PPTX (native shapes or SVG embed)"
    )
    ap.add_argument("--slides", required=True,
                    help="Directory containing slide*.svg files")
    ap.add_argument("--out", required=True, help="Output .pptx file path")
    ap.add_argument("--mode", choices=["native", "embed"], default="native",
                    help="native: editable shapes (default); embed: SVG blip (old behavior)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    slide_dir = Path(args.slides)
    svg_files = sorted(slide_dir.glob("slide*.svg"))
    if not svg_files:
        print(f"No slide*.svg files found in {slide_dir}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "embed":
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from to_pptx import pack_slides
        pack_slides(svg_files, Path(args.out))
        print(f"\n{len(svg_files)} slide(s) → {args.out} (embed mode)")
    else:
        convert_file(args.slides, args.out, verbose=args.verbose)


if __name__ == "__main__":
    main()
