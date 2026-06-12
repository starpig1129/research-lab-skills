"""__main__.py — CLI entry point for svg_to_pptx package."""
import argparse
import sys
from pathlib import Path

from .converter import convert_file

_MODE_HELP = """
SVG → PPTX conversion mode:

  [1] native  ← recommended
      每個 SVG 元素轉為獨立的 PPTX 原生物件（文字框、矩形、連接線⋯）。
      可在 PowerPoint 中個別點選、修改文字、調整顏色與位置。
      適合需要後續微調的簡報。
      Each SVG element becomes an individually editable shape.
      Best when you need to fine-tune content after export.

  [2] embed
      整張 SVG 以圖片方式嵌入，視覺還原度最高但無法個別編輯元素。
      Each SVG is inserted as a single image — pixel-perfect but not editable.
      Best for presentation-only decks where layout accuracy is critical.

"""


def _prompt_mode() -> str:
    print(_MODE_HELP, end="")
    while True:
        try:
            choice = input("Choose [1/2] (Enter = 1 native): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "native"
        if choice in ("", "1", "native"):
            return "native"
        if choice in ("2", "embed"):
            return "embed"
        print("  Please enter 1 or 2.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert SVG slides to PPTX (native shapes or SVG embed)"
    )
    ap.add_argument("--slides", required=True,
                    help="Directory containing slide*.svg files")
    ap.add_argument("--out", required=True, help="Output .pptx file path")
    ap.add_argument("--mode", choices=["native", "embed"], default=None,
                    help="native: editable shapes; embed: SVG blip. "
                         "Omit to be prompted with a description of each mode.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    slide_dir = Path(args.slides)
    svg_files = sorted(slide_dir.glob("slide*.svg"))
    if not svg_files:
        print(f"No slide*.svg files found in {slide_dir}", file=sys.stderr)
        sys.exit(1)

    mode = args.mode if args.mode is not None else _prompt_mode()

    if mode == "embed":
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from to_pptx import pack_slides
        pack_slides(svg_files, Path(args.out))
        print(f"\n{len(svg_files)} slide(s) → {args.out} (embed mode)")
    else:
        convert_file(args.slides, args.out, verbose=args.verbose)


if __name__ == "__main__":
    main()
