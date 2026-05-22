#!/usr/bin/env python3
"""to_pptx.py — Pack SVG slides into a PPTX with native SVG embedding.

SVG files are embedded directly into the PPTX (viewed natively by PowerPoint 2016+/365).
A minimal white PNG is included as a fallback for older viewers.

Only requires:  pip install python-pptx
No cairosvg, Pillow, Inkscape, or any image converter needed.

Usage:
    python scripts/to_pptx.py \
        --slides docs/slides/reports/2026-05-19_deck/ \
        --out    docs/slides/reports/2026-05-19_deck/deck.pptx
"""

import argparse
import struct
import zlib
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu
from pptx.opc.packuri import PackURI
from pptx.opc.package import Part
import lxml.etree as etree


# ── Slide dimensions (16:9 widescreen) ───────────────────────────────────────

SLIDE_W = 12_192_000   # EMU
SLIDE_H =  6_858_000   # EMU

# Relationship type for images
IMG_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

# XML namespaces used in the <p:pic> element
NS_A    = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_P    = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_R    = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_ASVG = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"

# Extension URI that tells PowerPoint "this pic has an SVG version"
SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"


# ── Minimal white PNG — no Pillow or cairosvg required ───────────────────────

def _make_white_png(width: int = 4, height: int = 3) -> bytes:
    """Return a tiny white PNG using Python stdlib only."""
    def chunk(name: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)   # RGB 8-bit
    row  = b"\x00" + b"\xff\xff\xff" * width                        # filter + white pixels
    idat = zlib.compress(row * height)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )


_WHITE_PNG = _make_white_png()


# ── SVG embedding ─────────────────────────────────────────────────────────────

def _relate_media(slide_part, blob: bytes, ext: str, content_type: str,
                  slide_idx: int, tag: str) -> str:
    """Add a media blob as a package Part and return its relationship ID."""
    partname = PackURI(f"/ppt/media/slide{slide_idx:02d}_{tag}.{ext}")
    part     = Part(partname, content_type, slide_part.package, blob)
    return slide_part.relate_to(part, IMG_REL)


def _build_pic_xml(png_rid: str, svg_rid: str, pic_id: int) -> etree._Element:
    """Build the <p:pic> lxml element for a full-slide SVG picture."""
    xml = (
        f'<p:pic'
        f' xmlns:p="{NS_P}"'
        f' xmlns:a="{NS_A}"'
        f' xmlns:r="{NS_R}"'
        f' xmlns:asvg="{NS_ASVG}">'

        f'<p:nvPicPr>'
        f'  <p:cNvPr id="{pic_id}" name="Slide {pic_id}"/>'
        f'  <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>'
        f'  <p:nvPr/>'
        f'</p:nvPicPr>'

        # PNG fallback in blipFill
        f'<p:blipFill>'
        f'  <a:blip r:embed="{png_rid}"/>'
        f'  <a:stretch><a:fillRect/></a:stretch>'
        f'</p:blipFill>'

        # Full-slide geometry
        f'<p:spPr>'
        f'  <a:xfrm>'
        f'    <a:off x="0" y="0"/>'
        f'    <a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/>'
        f'  </a:xfrm>'
        f'  <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'</p:spPr>'

        # SVG extension — PowerPoint 2016+ uses this instead of the PNG
        f'<p:extLst>'
        f'  <p:ext uri="{SVG_EXT_URI}">'
        f'    <asvg:svgBlip r:embed="{svg_rid}"/>'
        f'  </p:ext>'
        f'</p:extLst>'

        f'</p:pic>'
    )
    return etree.fromstring(xml.encode("utf-8"))


def add_svg_slide(prs: Presentation, svg_path: Path, slide_idx: int) -> None:
    """Append one blank slide to *prs* with the given SVG embedded natively."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])   # blank layout

    png_rid = _relate_media(slide.part, _WHITE_PNG,
                             "png", "image/png", slide_idx, "fallback")
    svg_rid = _relate_media(slide.part, svg_path.read_bytes(),
                             "svg", "image/svg+xml", slide_idx, "main")

    pic_elem = _build_pic_xml(png_rid, svg_rid, slide_idx + 1)
    slide.shapes._spTree.append(pic_elem)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Pack SVG slides into a PPTX with native SVG embedding")
    ap.add_argument("--slides", required=True,
                    help="Directory containing slide*.svg files")
    ap.add_argument("--out",    required=True,
                    help="Output .pptx file path")
    args = ap.parse_args()

    slide_dir = Path(args.slides)
    svg_files = sorted(slide_dir.glob("slide*.svg"))

    if not svg_files:
        print(f"No slide*.svg files found in {slide_dir}")
        return

    prs = Presentation()
    prs.slide_width  = Emu(SLIDE_W)
    prs.slide_height = Emu(SLIDE_H)

    for i, svg_path in enumerate(svg_files, start=1):
        add_svg_slide(prs, svg_path, i)
        print(f"  ✓ {svg_path.name}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    print(f"\n{len(svg_files)} slide(s) → {out_path}")
    print("Open with PowerPoint 2016+ / 365 for best SVG rendering.")


if __name__ == "__main__":
    main()
