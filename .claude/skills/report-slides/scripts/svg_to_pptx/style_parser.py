"""style_parser.py — SVG style/attribute resolution for python-pptx."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from pptx.dml.color import RGBColor
from pptx.util import Pt
from lxml import etree

CSS_COLORS: Dict[str, str] = {
    "aliceblue": "#f0f8ff", "antiquewhite": "#faebd7", "aqua": "#00ffff",
    "aquamarine": "#7fffd4", "azure": "#f0ffff", "beige": "#f5f5dc",
    "bisque": "#ffe4c4", "black": "#000000", "blanchedalmond": "#ffebcd",
    "blue": "#0000ff", "blueviolet": "#8a2be2", "brown": "#a52a2a",
    "burlywood": "#deb887", "cadetblue": "#5f9ea0", "chartreuse": "#7fff00",
    "chocolate": "#d2691e", "coral": "#ff7f50", "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc", "crimson": "#dc143c", "cyan": "#00ffff",
    "darkblue": "#00008b", "darkcyan": "#008b8b", "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9", "darkgreen": "#006400", "darkgrey": "#a9a9a9",
    "darkkhaki": "#bdb76b", "darkmagenta": "#8b008b", "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00", "darkorchid": "#9932cc", "darkred": "#8b0000",
    "darksalmon": "#e9967a", "darkseagreen": "#8fbc8f", "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f", "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1", "darkviolet": "#9400d3", "deeppink": "#ff1493",
    "deepskyblue": "#00bfff", "dimgray": "#696969", "dimgrey": "#696969",
    "dodgerblue": "#1e90ff", "firebrick": "#b22222", "floralwhite": "#fffaf0",
    "forestgreen": "#228b22", "fuchsia": "#ff00ff", "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff", "gold": "#ffd700", "goldenrod": "#daa520",
    "gray": "#808080", "green": "#008000", "greenyellow": "#adff2f",
    "grey": "#808080", "honeydew": "#f0fff0", "hotpink": "#ff69b4",
    "indianred": "#cd5c5c", "indigo": "#4b0082", "ivory": "#fffff0",
    "khaki": "#f0e68c", "lavender": "#e6e6fa", "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00", "lemonchiffon": "#fffacd", "lightblue": "#add8e6",
    "lightcoral": "#f08080", "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2", "lightgray": "#d3d3d3",
    "lightgreen": "#90ee90", "lightgrey": "#d3d3d3", "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a", "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa", "lightslategray": "#778899",
    "lightslategrey": "#778899", "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0", "lime": "#00ff00", "limegreen": "#32cd32",
    "linen": "#faf0e6", "magenta": "#ff00ff", "maroon": "#800000",
    "mediumaquamarine": "#66cdaa", "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3", "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371", "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a", "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585", "midnightblue": "#191970",
    "mintcream": "#f5fffa", "mistyrose": "#ffe4e1", "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead", "navy": "#000080", "oldlace": "#fdf5e6",
    "olive": "#808000", "olivedrab": "#6b8e23", "orange": "#ffa500",
    "orangered": "#ff4500", "orchid": "#da70d6", "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98", "paleturquoise": "#afeeee",
    "palevioletred": "#db7093", "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9", "peru": "#cd853f", "pink": "#ffc0cb",
    "plum": "#dda0dd", "powderblue": "#b0e0e6", "purple": "#800080",
    "rebeccapurple": "#663399", "red": "#ff0000", "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1", "saddlebrown": "#8b4513", "salmon": "#fa8072",
    "sandybrown": "#f4a460", "seagreen": "#2e8b57", "seashell": "#fff5ee",
    "sienna": "#a0522d", "silver": "#c0c0c0", "skyblue": "#87ceeb",
    "slateblue": "#6a5acd", "slategray": "#708090", "slategrey": "#708090",
    "snow": "#fffafa", "springgreen": "#00ff7f", "steelblue": "#4682b4",
    "tan": "#d2b48c", "teal": "#008080", "thistle": "#d8bfd8",
    "tomato": "#ff6347", "turquoise": "#40e0d0", "violet": "#ee82ee",
    "wheat": "#f5deb3", "white": "#ffffff", "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00", "yellowgreen": "#9acd32",
}

_STYLE_ATTRS = (
    "fill", "stroke", "stroke-width", "stroke-dasharray", "opacity",
    "font-size", "font-weight", "font-style", "font-family", "text-anchor", "transform",
    "fill-opacity", "stroke-opacity",
)


def parse_inline_style(style_str: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for part in style_str.split(";"):
        part = part.strip()
        if ":" in part:
            k, _, v = part.partition(":")
            result[k.strip()] = v.strip()
    return result


def resolve_color(value: str) -> Optional[RGBColor]:
    if not value or value.lower() in ("none", "transparent", ""):
        return None
    v = CSS_COLORS.get(value.lower(), value)
    v = v.lstrip("#")
    if len(v) == 3:
        v = v[0] * 2 + v[1] * 2 + v[2] * 2
    if len(v) != 6:
        return None
    try:
        return RGBColor(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    except (ValueError, IndexError):
        return None


def compute_style(elem: Any, inherited: Dict[str, str]) -> Dict[str, str]:
    style: Dict[str, str] = dict(inherited)
    for attr in _STYLE_ATTRS:
        val = elem.get(attr)
        if val is not None:
            style[attr] = val
    inline = elem.get("style", "")
    if inline:
        style.update(parse_inline_style(inline))
    return style


def apply_fill(shape: Any, fill_value: str) -> None:
    if not fill_value or fill_value.lower() in ("none", "transparent"):
        shape.fill.background()
        return
    rgb = resolve_color(fill_value)
    if rgb:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb


def apply_stroke(shape: Any, style: Dict[str, str]) -> None:
    stroke = style.get("stroke", "none")
    if not stroke or stroke.lower() == "none":
        shape.line.fill.background()
        return
    rgb = resolve_color(stroke)
    if rgb:
        shape.line.color.rgb = rgb
    width_raw = style.get("stroke-width", "1")
    try:
        shape.line.width = Pt(float(re.sub(r"[^0-9.]", "", width_raw) or "1"))
    except ValueError:
        shape.line.width = Pt(1)


import math as _math


def parse_transform(transform_str: str) -> Tuple[float, float, float, float, float]:
    """Parse SVG transform → (tx, ty, rotation_deg, scale_x, scale_y)."""
    tx, ty, rot, sx, sy = 0.0, 0.0, 0.0, 1.0, 1.0
    if not transform_str:
        return tx, ty, rot, sx, sy
    s = transform_str.strip()
    m = re.match(r'translate\(\s*([-\d.]+)(?:[,\s]+([-\d.]+))?\s*\)', s)
    if m:
        tx = float(m.group(1))
        ty = float(m.group(2) or 0)
        return tx, ty, rot, sx, sy
    m = re.match(r'rotate\(\s*([-\d.]+)(?:[,\s]+([-\d.]+)[,\s]+([-\d.]+))?\s*\)', s)
    if m:
        rot = float(m.group(1))
        return tx, ty, rot, sx, sy
    m = re.match(r'scale\(\s*([-\d.]+)(?:[,\s]+([-\d.]+))?\s*\)', s)
    if m:
        sx = float(m.group(1))
        sy = float(m.group(2) or m.group(1))
        return tx, ty, rot, sx, sy
    m = re.match(
        r'matrix\(\s*([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+'
        r'([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)\s*\)', s)
    if m:
        a, b, c, d, e, f = (float(m.group(i)) for i in range(1, 7))
        tx = e; ty = f
        sx = _math.sqrt(a * a + b * b)
        sy = _math.sqrt(c * c + d * d)
        rot = _math.degrees(_math.atan2(b, a))
        return tx, ty, rot, sx, sy
    return tx, ty, rot, sx, sy


def apply_transform_to_pos(x: float, y: float, w: float, h: float,
                           transform_str: str) -> Tuple[float, float, float, float]:
    tx, ty, rot, sx, sy = parse_transform(transform_str)
    return x + tx, y + ty, w * sx, h * sy


def apply_gradient_fill(shape: Any, stops: List[Tuple[str, str]],
                        angle_deg: float = 0.0) -> None:
    from pptx.oxml.ns import qn
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))
    if spPr is None:
        return
    for child in list(spPr):
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("solidFill", "gradFill", "noFill", "blipFill", "pattFill"):
            spPr.remove(child)
    gradFill = etree.SubElement(spPr, f"{{{A}}}gradFill")
    gsLst = etree.SubElement(gradFill, f"{{{A}}}gsLst")
    for offset_str, color_str in stops:
        offset_str = offset_str.strip()
        if offset_str.endswith("%"):
            pos = int(round(float(offset_str[:-1]) * 1000))
        else:
            try:
                pos = int(round(float(offset_str) * 100000))
            except ValueError:
                pos = 0
        gs = etree.SubElement(gsLst, f"{{{A}}}gs")
        gs.set("pos", str(pos))
        rgb = resolve_color(color_str)
        if rgb:
            srgb = etree.SubElement(gs, f"{{{A}}}srgbClr")
            srgb.set("val", f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
    lin = etree.SubElement(gradFill, f"{{{A}}}lin")
    ang_ooxml = int(round(angle_deg * 60000)) % 21600000
    lin.set("ang", str(ang_ooxml))
    lin.set("scaled", "0")
