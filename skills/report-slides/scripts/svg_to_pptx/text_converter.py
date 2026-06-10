"""text_converter.py — standalone TextBox for unattached SVG <text> elements."""
from __future__ import annotations

from typing import Any, Dict

from pptx.util import Emu, Pt
from pptx.enum.text import PP_ALIGN

from .style_parser import compute_style
from .converter import CoordSystem, _local_tag
from .shapes import _collect_text_lines, _apply_font, _ALIGN

_TB_W = 3_000_000
_TB_H = 500_000


def add_textbox(slide: Any, elem: Any, style: Dict, cs: CoordSystem) -> Any:
    try:
        tx = float(elem.get("x", 0))
        ty = float(elem.get("y", 0))
    except ValueError:
        tx, ty = 0.0, 0.0

    ex = cs.x(tx)
    ey = cs.y(ty)
    anchor = style.get("text-anchor", "start")

    if anchor == "middle":
        ex = max(0, ex - _TB_W // 2)
    elif anchor == "end":
        ex = max(0, ex - _TB_W)

    tb = slide.shapes.add_textbox(Emu(ex), Emu(ey), Emu(_TB_W), Emu(_TB_H))
    tf = tb.text_frame
    tf.word_wrap = False

    lines = _collect_text_lines(elem, style)
    for i, (text, line_style) in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        a = line_style.get("text-anchor", style.get("text-anchor", "start"))
        para.alignment = _ALIGN.get(a, PP_ALIGN.LEFT)
        if text:
            run = para.add_run()
            run.text = text
            _apply_font(run, line_style, style)

    return tb
