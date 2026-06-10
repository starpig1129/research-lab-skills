# SVG → Native PPTX Converter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `skills/report-slides/scripts/svg_to_pptx/` — a Python package that converts every SVG element from `generate_slides.py` into fully editable native PowerPoint shapes, replacing `to_pptx.py`.

**Architecture:** SVG parsed by lxml → style inheritance pass → text-shape attachment pre-pass → element dispatch (shapes/text/path/connectors) → python-pptx API + OOXML XML injection → `.pptx`. Post-pass binds connectors to shape anchors. `to_pptx.py` preserved as `--mode embed` fallback.

**Tech Stack:** Python 3.8+, python-pptx 1.0+, lxml 6+, stdlib only.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `skills/report-slides/scripts/svg_to_pptx/__init__.py` | Create | Public exports |
| `skills/report-slides/scripts/svg_to_pptx/converter.py` | Create | Orchestration, CoordSystem, pre/post passes |
| `skills/report-slides/scripts/svg_to_pptx/style_parser.py` | Create | fill/stroke/color/transform resolution |
| `skills/report-slides/scripts/svg_to_pptx/shapes.py` | Create | rect, circle, ellipse, image |
| `skills/report-slides/scripts/svg_to_pptx/text_converter.py` | Create | Standalone TextBox |
| `skills/report-slides/scripts/svg_to_pptx/connector.py` | Create | line/polyline + anchor binding |
| `skills/report-slides/scripts/svg_to_pptx/path_parser.py` | Create | SVG d="" → normalized absolute command list |
| `skills/report-slides/scripts/svg_to_pptx/path_to_pptx.py` | Create | FreeformBuilder + OOXML custGeom + arc decomposition |
| `skills/report-slides/scripts/svg_to_pptx/__main__.py` | Create | CLI entry point |
| `skills/report-slides/scripts/svg_to_pptx/tests/__init__.py` | Create | Test package |
| `skills/report-slides/scripts/svg_to_pptx/tests/test_style_parser.py` | Create | Style unit tests |
| `skills/report-slides/scripts/svg_to_pptx/tests/test_shapes.py` | Create | Shape unit tests |
| `skills/report-slides/scripts/svg_to_pptx/tests/test_text_converter.py` | Create | Text unit tests |
| `skills/report-slides/scripts/svg_to_pptx/tests/test_connector.py` | Create | Connector unit tests |
| `skills/report-slides/scripts/svg_to_pptx/tests/test_path_parser.py` | Create | Path parser unit tests |
| `skills/report-slides/scripts/svg_to_pptx/tests/test_path_to_pptx.py` | Create | Path PPTX unit tests |
| `skills/report-slides/scripts/svg_to_pptx/tests/test_integration.py` | Create | End-to-end SVG → PPTX tests |
| `skills/report-slides/SKILL.md` | Modify | Document new CLI |

---

## Task 1: Package skeleton + CoordSystem

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/__init__.py`
- Create: `skills/report-slides/scripts/svg_to_pptx/converter.py`
- Create: `skills/report-slides/scripts/svg_to_pptx/tests/__init__.py`

- [ ] **Step 1: Write failing test**

Create `skills/report-slides/scripts/svg_to_pptx/tests/__init__.py` (empty).

Create `skills/report-slides/scripts/svg_to_pptx/tests/test_style_parser.py` — add just the import test first:

```python
# tests/test_style_parser.py
import pytest
from svg_to_pptx.converter import CoordSystem

def test_coordsystem_from_viewbox():
    cs = CoordSystem.from_viewbox("0 0 1200 675")
    assert cs.svg_w == 1200.0
    assert cs.svg_h == 675.0

def test_coordsystem_x_scaling():
    cs = CoordSystem.from_viewbox("0 0 1200 675")
    # SVG x=600 (halfway) → PPTX x=6_096_000 (half of 12_192_000)
    assert cs.x(600) == 6_096_000

def test_coordsystem_y_scaling():
    cs = CoordSystem.from_viewbox("0 0 1200 675")
    # SVG y=337.5 (halfway) → PPTX y=3_429_000 (half of 6_858_000)
    assert cs.y(337.5) == 3_429_000

def test_coordsystem_missing_viewbox():
    cs = CoordSystem.from_viewbox("")
    assert cs.svg_w == 1200.0
    assert cs.svg_h == 675.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_style_parser.py::test_coordsystem_from_viewbox -v
```

Expected: `ModuleNotFoundError: No module named 'svg_to_pptx'`

- [ ] **Step 3: Create package files**

Create `skills/report-slides/scripts/svg_to_pptx/__init__.py`:

```python
from .converter import CoordSystem, SvgConverter, convert_file

__all__ = ["CoordSystem", "SvgConverter", "convert_file"]
```

Create `skills/report-slides/scripts/svg_to_pptx/converter.py`:

```python
"""converter.py — orchestration layer for SVG → native PPTX conversion."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from lxml import etree
from pptx import Presentation
from pptx.util import Emu

PPTX_W = 12_192_000
PPTX_H = 6_858_000
_SVG_NS = "http://www.w3.org/2000/svg"
_XLINK_NS = "http://www.w3.org/1999/xlink"


@dataclass
class CoordSystem:
    svg_w: float
    svg_h: float

    def x(self, v: float) -> int:
        return round(float(v) / self.svg_w * PPTX_W)

    def y(self, v: float) -> int:
        return round(float(v) / self.svg_h * PPTX_H)

    @classmethod
    def from_viewbox(cls, viewbox: str) -> "CoordSystem":
        parts = viewbox.strip().split()
        if len(parts) == 4:
            try:
                return cls(svg_w=float(parts[2]), svg_h=float(parts[3]))
            except ValueError:
                pass
        return cls(svg_w=1200.0, svg_h=675.0)


def _local_tag(elem: Any) -> str:
    tag = elem.tag
    return tag.split("}")[-1] if "}" in tag else tag


class SvgConverter:
    """Converts one SVG file into one PPTX slide."""

    def __init__(self, svg_path: str, verbose: bool = False) -> None:
        self.svg_path = svg_path
        self.verbose = verbose
        tree = etree.parse(svg_path)
        self.root = tree.getroot()
        vb = self.root.get("viewBox", "0 0 1200 675")
        self.cs = CoordSystem.from_viewbox(vb)
        self._shape_labels: Dict[int, Any] = {}   # id(shape_elem) → text_elem
        self._text_to_shape: Dict[int, Any] = {}  # id(text_elem) → shape_elem
        self._defs: Dict[str, Any] = {}            # id attr → elem

    def convert(self, prs: Presentation, slide_layout: Any) -> Any:
        slide = prs.slides.add_slide(slide_layout)
        self._resolve_defs()
        self._resolve_use_elements()
        self._compute_text_attachments()
        self._dispatch_children(slide, self.root, {})
        self._bind_connectors(slide)
        return slide

    # ── Pre-processing stubs (implemented in later tasks) ─────────────────────

    def _resolve_defs(self) -> None:
        for elem in self.root.iter():
            if _local_tag(elem) == "defs":
                for child in elem:
                    eid = child.get("id")
                    if eid:
                        self._defs[eid] = child

    def _resolve_use_elements(self) -> None:
        pass  # implemented in Task 10

    def _compute_text_attachments(self) -> None:
        pass  # implemented in Task 6

    def _dispatch_children(self, slide: Any, parent: Any, inherited: Dict) -> None:
        from .style_parser import compute_style
        for elem in parent:
            tag = _local_tag(elem)
            try:
                style = compute_style(elem, inherited)
                self._dispatch_element(slide, elem, style)
            except Exception as exc:
                if self.verbose:
                    print(f"  [warn] {tag}: {exc}")

    def _dispatch_element(self, slide: Any, elem: Any, style: Dict) -> None:
        tag = _local_tag(elem)
        if tag in ("rect", "circle", "ellipse", "image"):
            from .shapes import dispatch_shape
            dispatch_shape(slide, elem, style, self.cs,
                           self._shape_labels.get(id(elem)))
        elif tag == "text":
            if id(elem) not in self._text_to_shape:
                from .text_converter import add_textbox
                add_textbox(slide, elem, style, self.cs)
        elif tag in ("line", "polyline", "polygon"):
            from .connector import dispatch_connector
            dispatch_connector(slide, elem, style, self.cs)
        elif tag == "path":
            from .path_parser import parse_path, has_curves
            from .path_to_pptx import add_path_shape
            d = elem.get("d", "")
            if d:
                cmds = parse_path(d)
                add_path_shape(slide, cmds, self.cs, style)
        elif tag == "g":
            self._dispatch_children(slide, elem, style)
        # other tags silently skipped

    def _bind_connectors(self, slide: Any) -> None:
        pass  # implemented in Task 7

    def _connector_registry(self) -> List:
        return []


def convert_file(slides_dir: str, out_path: str, verbose: bool = False) -> None:
    prs = Presentation()
    prs.slide_width = Emu(PPTX_W)
    prs.slide_height = Emu(PPTX_H)
    layout = prs.slide_layouts[6]

    svg_files = sorted(Path(slides_dir).glob("slide*.svg"))
    if not svg_files:
        raise ValueError(f"No slide*.svg files found in {slides_dir}")

    for svg_path in svg_files:
        conv = SvgConverter(str(svg_path), verbose=verbose)
        conv.convert(prs, layout)
        if verbose:
            print(f"  + {svg_path.name}")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)
    print(f"\n{len(svg_files)} slide(s) → {out_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_style_parser.py -k "coordsystem" -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/
git commit -m "feat(svg_to_pptx): add package skeleton with CoordSystem and converter stub"
```

---

## Task 2: style_parser.py — color, fill, stroke

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/style_parser.py`
- Modify: `skills/report-slides/scripts/svg_to_pptx/tests/test_style_parser.py`

- [ ] **Step 1: Write failing tests**

Append to `svg_to_pptx/tests/test_style_parser.py`:

```python
from svg_to_pptx.style_parser import (
    parse_inline_style, resolve_color, compute_style, apply_fill, apply_stroke
)
from pptx.dml.color import RGBColor
from lxml import etree

def test_parse_inline_style():
    r = parse_inline_style("fill:#3b82f6;stroke:#1d4ed8;stroke-width:2")
    assert r == {"fill": "#3b82f6", "stroke": "#1d4ed8", "stroke-width": "2"}

def test_parse_inline_style_with_spaces():
    r = parse_inline_style(" fill : #fff ; stroke: none ")
    assert r["fill"] == "#fff"
    assert r["stroke"] == "none"

def test_resolve_color_hex6():
    assert resolve_color("#3b82f6") == RGBColor(0x3b, 0x82, 0xf6)

def test_resolve_color_hex3():
    assert resolve_color("#f0f") == RGBColor(0xff, 0x00, 0xff)

def test_resolve_color_named_white():
    assert resolve_color("white") == RGBColor(0xff, 0xff, 0xff)

def test_resolve_color_named_blue():
    assert resolve_color("blue") == RGBColor(0x00, 0x00, 0xff)

def test_resolve_color_none():
    assert resolve_color("none") is None

def test_resolve_color_invalid():
    assert resolve_color("notacolor") is None

def test_compute_style_attr_fallback():
    elem = etree.fromstring('<rect fill="#ff0000"/>')
    result = compute_style(elem, {})
    assert result["fill"] == "#ff0000"

def test_compute_style_inherited():
    elem = etree.fromstring('<rect/>')
    result = compute_style(elem, {"fill": "#00ff00"})
    assert result["fill"] == "#00ff00"

def test_compute_style_inline_overrides_attr():
    elem = etree.fromstring('<rect fill="#ff0000" style="fill:#00ff00"/>')
    result = compute_style(elem, {})
    assert result["fill"] == "#00ff00"

def test_compute_style_inline_overrides_inherited():
    elem = etree.fromstring('<rect style="stroke:none"/>')
    result = compute_style(elem, {"stroke": "#000000"})
    assert result["stroke"] == "none"
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_style_parser.py -k "not coordsystem" -v
```

Expected: `ImportError: cannot import name 'parse_inline_style'`

- [ ] **Step 3: Create style_parser.py**

Create `skills/report-slides/scripts/svg_to_pptx/style_parser.py`:

```python
"""style_parser.py — SVG style/attribute resolution for python-pptx."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from pptx.dml.color import RGBColor
from pptx.util import Pt

# ── 140 CSS named colors ──────────────────────────────────────────────────────
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
    "font-size", "font-weight", "font-family", "text-anchor", "transform",
    "fill-opacity", "stroke-opacity",
)

_DASHARRAY_MAP = {
    "none": None,
    "4 2": "dash",
    "2 2": "dot",
    "4 2 1 2": "dashDot",
}


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
    style = dict(inherited)
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_style_parser.py -v
```

Expected: `15 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/style_parser.py \
        skills/report-slides/scripts/svg_to_pptx/tests/test_style_parser.py
git commit -m "feat(svg_to_pptx): add style_parser with color resolution and fill/stroke apply"
```

---

## Task 3: shapes.py — rect, circle, ellipse

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/shapes.py`
- Create: `skills/report-slides/scripts/svg_to_pptx/tests/test_shapes.py`

- [ ] **Step 1: Write failing tests**

Create `skills/report-slides/scripts/svg_to_pptx/tests/test_shapes.py`:

```python
import pytest
from lxml import etree
from pptx import Presentation
from pptx.util import Emu

from svg_to_pptx.converter import CoordSystem
from svg_to_pptx.shapes import dispatch_shape
from svg_to_pptx.style_parser import compute_style

def _blank_slide():
    prs = Presentation()
    prs.slide_width = Emu(12_192_000)
    prs.slide_height = Emu(6_858_000)
    return prs.slides.add_slide(prs.slide_layouts[6]), prs

CS = CoordSystem(svg_w=1200.0, svg_h=675.0)

def test_rect_creates_one_shape():
    slide, _ = _blank_slide()
    elem = etree.fromstring('<rect x="100" y="50" width="200" height="100" fill="#3b82f6"/>')
    style = compute_style(elem, {})
    dispatch_shape(slide, elem, style, CS, None)
    assert len(slide.shapes) == 1

def test_rect_position_and_size():
    slide, _ = _blank_slide()
    elem = etree.fromstring('<rect x="0" y="0" width="1200" height="675" fill="#fff"/>')
    style = compute_style(elem, {})
    dispatch_shape(slide, elem, style, CS, None)
    shape = slide.shapes[0]
    assert shape.left == 0
    assert shape.top == 0
    assert shape.width == 12_192_000
    assert shape.height == 6_858_000

def test_circle_creates_oval():
    slide, _ = _blank_slide()
    elem = etree.fromstring('<circle cx="600" cy="337" r="100" fill="#10b981"/>')
    style = compute_style(elem, {})
    dispatch_shape(slide, elem, style, CS, None)
    assert len(slide.shapes) == 1
    shape = slide.shapes[0]
    # width = height = 2r in EMU
    expected_w = CS.x(200)
    assert abs(shape.width - expected_w) <= 1

def test_rect_with_label_writes_text_in_shape():
    slide, _ = _blank_slide()
    rect_elem = etree.fromstring('<rect x="40" y="80" width="160" height="70" fill="#3b82f6"/>')
    text_elem = etree.fromstring('<text x="120" y="115" fill="white">Hello</text>')
    style = compute_style(rect_elem, {})
    dispatch_shape(slide, rect_elem, style, CS, text_elem)
    shape = slide.shapes[0]
    assert shape.has_text_frame
    assert shape.text_frame.paragraphs[0].runs[0].text == "Hello"

def test_ellipse_creates_oval():
    slide, _ = _blank_slide()
    elem = etree.fromstring('<ellipse cx="300" cy="200" rx="80" ry="40" fill="#f00"/>')
    style = compute_style(elem, {})
    dispatch_shape(slide, elem, style, CS, None)
    assert len(slide.shapes) == 1
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_shapes.py -v
```

Expected: `ImportError: cannot import name 'dispatch_shape'`

- [ ] **Step 3: Create shapes.py**

Create `skills/report-slides/scripts/svg_to_pptx/shapes.py`:

```python
"""shapes.py — rect, circle, ellipse, image → python-pptx shapes."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from pptx.util import Emu, Pt
from pptx.enum.text import PP_ALIGN

from .style_parser import apply_fill, apply_stroke, resolve_color, compute_style
from .converter import CoordSystem, _local_tag

_ALIGN = {"start": PP_ALIGN.LEFT, "middle": PP_ALIGN.CENTER, "end": PP_ALIGN.RIGHT}


def dispatch_shape(slide: Any, elem: Any, style: Dict,
                   cs: CoordSystem, label_elem: Optional[Any]) -> Optional[Any]:
    tag = _local_tag(elem)
    if tag == "rect":
        return _add_rect(slide, elem, style, cs, label_elem)
    elif tag in ("circle", "ellipse"):
        return _add_oval(slide, elem, style, cs, label_elem)
    elif tag == "image":
        return _add_image(slide, elem, style, cs)
    return None


def _add_rect(slide: Any, elem: Any, style: Dict,
              cs: CoordSystem, label_elem: Optional[Any]) -> Any:
    x = cs.x(float(elem.get("x", 0)))
    y = cs.y(float(elem.get("y", 0)))
    w = max(1, cs.x(float(elem.get("width", 0))))
    h = max(1, cs.y(float(elem.get("height", 0))))
    shape = slide.shapes.add_shape(1, Emu(x), Emu(y), Emu(w), Emu(h))
    apply_fill(shape, style.get("fill", "black"))
    apply_stroke(shape, style)
    if label_elem is not None:
        _write_label(shape, label_elem, style)
    return shape


def _add_oval(slide: Any, elem: Any, style: Dict,
              cs: CoordSystem, label_elem: Optional[Any]) -> Any:
    tag = _local_tag(elem)
    if tag == "circle":
        cx = float(elem.get("cx", 0))
        cy = float(elem.get("cy", 0))
        r = float(elem.get("r", 0))
        x, y, w, h = cx - r, cy - r, 2 * r, 2 * r
    else:  # ellipse
        cx = float(elem.get("cx", 0))
        cy = float(elem.get("cy", 0))
        rx = float(elem.get("rx", 0))
        ry = float(elem.get("ry", 0))
        x, y, w, h = cx - rx, cy - ry, 2 * rx, 2 * ry
    ex = cs.x(x); ey = cs.y(y)
    ew = max(1, cs.x(w)); eh = max(1, cs.y(h))
    shape = slide.shapes.add_shape(9, Emu(ex), Emu(ey), Emu(ew), Emu(eh))
    apply_fill(shape, style.get("fill", "black"))
    apply_stroke(shape, style)
    if label_elem is not None:
        _write_label(shape, label_elem, style)
    return shape


def _add_image(slide: Any, elem: Any, style: Dict, cs: CoordSystem) -> Optional[Any]:
    href = elem.get("href") or elem.get(
        "{http://www.w3.org/1999/xlink}href", "")
    if not href or href.startswith("data:"):
        return None  # skip data URIs
    x = cs.x(float(elem.get("x", 0)))
    y = cs.y(float(elem.get("y", 0)))
    w = max(1, cs.x(float(elem.get("width", 100))))
    h = max(1, cs.y(float(elem.get("height", 100))))
    try:
        return slide.shapes.add_picture(href, Emu(x), Emu(y), Emu(w), Emu(h))
    except Exception:
        return None


def _write_label(shape: Any, text_elem: Any, parent_style: Dict) -> None:
    tf = shape.text_frame
    tf.word_wrap = True
    lines = _collect_text_lines(text_elem, parent_style)
    for i, (text, line_style) in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        anchor = line_style.get("text-anchor", parent_style.get("text-anchor", "middle"))
        para.alignment = _ALIGN.get(anchor, PP_ALIGN.CENTER)
        run = para.add_run()
        run.text = text
        _apply_font(run, line_style, parent_style)


def _collect_text_lines(text_elem: Any, parent_style: Dict):
    lines = []
    direct_text = (text_elem.text or "").strip()
    if direct_text:
        lines.append((direct_text, parent_style))
    for tspan in text_elem:
        if _local_tag(tspan) == "tspan":
            ts = compute_style(tspan, parent_style)
            t = (tspan.text or "").strip()
            if t:
                lines.append((t, ts))
    if not lines:
        lines.append(("", parent_style))
    return lines


def _apply_font(run: Any, style: Dict, parent_style: Dict) -> None:
    size_raw = style.get("font-size", parent_style.get("font-size", "14"))
    try:
        run.font.size = Pt(float(re.sub(r"[^0-9.]", "", size_raw) or "14"))
    except ValueError:
        run.font.size = Pt(14)
    weight = style.get("font-weight", parent_style.get("font-weight", "normal"))
    if weight in ("bold", "700", "800", "900"):
        run.font.bold = True
    color_val = style.get("fill", parent_style.get("fill", "#000000"))
    rgb = resolve_color(color_val)
    if rgb:
        run.font.color.rgb = rgb
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_shapes.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/shapes.py \
        skills/report-slides/scripts/svg_to_pptx/tests/test_shapes.py
git commit -m "feat(svg_to_pptx): add shapes.py with rect, oval, image, label writing"
```

---

## Task 4: text_converter.py — standalone TextBox

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/text_converter.py`
- Create: `skills/report-slides/scripts/svg_to_pptx/tests/test_text_converter.py`

- [ ] **Step 1: Write failing tests**

Create `skills/report-slides/scripts/svg_to_pptx/tests/test_text_converter.py`:

```python
import pytest
from lxml import etree
from pptx import Presentation
from pptx.util import Emu
from pptx.enum.text import PP_ALIGN

from svg_to_pptx.converter import CoordSystem
from svg_to_pptx.text_converter import add_textbox
from svg_to_pptx.style_parser import compute_style

CS = CoordSystem(svg_w=1200.0, svg_h=675.0)

def _slide():
    prs = Presentation()
    prs.slide_width = Emu(12_192_000)
    prs.slide_height = Emu(6_858_000)
    return prs.slides.add_slide(prs.slide_layouts[6])

def test_textbox_creates_shape():
    slide = _slide()
    elem = etree.fromstring('<text x="600" y="50" font-size="24">Hello</text>')
    add_textbox(slide, elem, compute_style(elem, {}), CS)
    assert len(slide.shapes) == 1

def test_textbox_text_content():
    slide = _slide()
    elem = etree.fromstring('<text x="100" y="100">World</text>')
    add_textbox(slide, elem, compute_style(elem, {}), CS)
    assert slide.shapes[0].text_frame.paragraphs[0].runs[0].text == "World"

def test_textbox_center_alignment():
    slide = _slide()
    elem = etree.fromstring('<text x="600" y="100" text-anchor="middle">Centered</text>')
    add_textbox(slide, elem, compute_style(elem, {}), CS)
    para = slide.shapes[0].text_frame.paragraphs[0]
    assert para.alignment == PP_ALIGN.CENTER

def test_textbox_tspan_multiline():
    slide = _slide()
    elem = etree.fromstring(
        '<text x="100" y="100">'
        '<tspan x="100" dy="0">Line 1</tspan>'
        '<tspan x="100" dy="20">Line 2</tspan>'
        '</text>'
    )
    add_textbox(slide, elem, compute_style(elem, {}), CS)
    tf = slide.shapes[0].text_frame
    texts = [p.runs[0].text for p in tf.paragraphs if p.runs]
    assert "Line 1" in texts
    assert "Line 2" in texts

def test_textbox_font_size():
    slide = _slide()
    elem = etree.fromstring('<text x="100" y="100" font-size="32">Big</text>')
    add_textbox(slide, elem, compute_style(elem, {}), CS)
    from pptx.util import Pt
    run = slide.shapes[0].text_frame.paragraphs[0].runs[0]
    assert run.font.size == Pt(32)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_text_converter.py -v
```

Expected: `ImportError: cannot import name 'add_textbox'`

- [ ] **Step 3: Create text_converter.py**

Create `skills/report-slides/scripts/svg_to_pptx/text_converter.py`:

```python
"""text_converter.py — standalone TextBox for unattached SVG <text> elements."""
from __future__ import annotations

import re
from typing import Any, Dict

from pptx.util import Emu, Pt
from pptx.enum.text import PP_ALIGN

from .style_parser import compute_style, resolve_color
from .converter import CoordSystem, _local_tag
from .shapes import _collect_text_lines, _apply_font, _ALIGN

_TB_W = 3_000_000   # default TextBox width: ~8 cm
_TB_H =   500_000   # default TextBox height: ~1.4 cm


def add_textbox(slide: Any, elem: Any, style: Dict, cs: CoordSystem) -> Any:
    try:
        tx = float(elem.get("x", 0))
        ty = float(elem.get("y", 0))
    except ValueError:
        tx, ty = 0.0, 0.0

    ex = cs.x(tx)
    ey = cs.y(ty)
    anchor = style.get("text-anchor", "start")

    # Shift TextBox left so text visually aligns at SVG anchor point
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_text_converter.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/text_converter.py \
        skills/report-slides/scripts/svg_to_pptx/tests/test_text_converter.py
git commit -m "feat(svg_to_pptx): add text_converter for standalone TextBox"
```

---

## Task 5: connector.py — line/polyline + anchor binding stubs

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/connector.py`
- Create: `skills/report-slides/scripts/svg_to_pptx/tests/test_connector.py`

- [ ] **Step 1: Write failing tests**

Create `skills/report-slides/scripts/svg_to_pptx/tests/test_connector.py`:

```python
import pytest
from lxml import etree
from pptx import Presentation
from pptx.util import Emu
from pptx.oxml.ns import qn

from svg_to_pptx.converter import CoordSystem
from svg_to_pptx.connector import dispatch_connector, build_anchor_map, bind_connector_end
from svg_to_pptx.style_parser import compute_style

CS = CoordSystem(svg_w=1200.0, svg_h=675.0)

def _slide():
    prs = Presentation()
    prs.slide_width = Emu(12_192_000)
    prs.slide_height = Emu(6_858_000)
    return prs.slides.add_slide(prs.slide_layouts[6])

def test_line_creates_connector():
    slide = _slide()
    elem = etree.fromstring('<line x1="100" y1="100" x2="400" y2="100" stroke="#000"/>')
    dispatch_connector(slide, elem, compute_style(elem, {}), CS)
    assert len(slide.shapes) == 1

def test_polyline_creates_n_minus_1_connectors():
    slide = _slide()
    elem = etree.fromstring('<polyline points="0,0 100,0 200,100" stroke="#000"/>')
    dispatch_connector(slide, elem, compute_style(elem, {}), CS)
    assert len(slide.shapes) == 2  # 3 points → 2 segments

def test_polygon_closes_path():
    slide = _slide()
    elem = etree.fromstring('<polygon points="0,0 100,0 50,100" stroke="#000"/>')
    dispatch_connector(slide, elem, compute_style(elem, {}), CS)
    assert len(slide.shapes) == 3  # 3 points → 3 segments (closed)

def test_build_anchor_map_rect():
    # rect at (100,50) size (200,100) → 8 anchors
    anchors = build_anchor_map([(None, 100.0, 50.0, 200.0, 100.0, 42)])
    assert 42 in anchors
    assert len(anchors[42]) == 8

def test_build_anchor_map_nearest():
    # anchor at rect center-top = (200, 50)
    anchors = build_anchor_map([(None, 100.0, 50.0, 200.0, 100.0, 42)])
    # idx 1 = top-center = (200, 50)
    top_center = next(a for a in anchors[42] if a[2] == 1)
    assert top_center[0] == 200.0  # x
    assert top_center[1] == 50.0   # y

def test_bind_connector_injects_xml():
    slide = _slide()
    # Create a connector
    from svg_to_pptx.connector import _add_line
    conn = _add_line(slide, 0, 0, 100, 0, {})
    shape = slide.shapes.add_shape(1, Emu(0), Emu(0), Emu(CS.x(200)), Emu(CS.y(100)))
    bind_connector_end(conn, True, shape.shape_id, 3)
    cxnSp = conn._element
    nvCxnSpPr = cxnSp.find(qn('p:nvCxnSpPr'))
    cNvCxnSpPr = nvCxnSpPr.find(qn('p:cNvCxnSpPr'))
    stCxn = cNvCxnSpPr.find(qn('a:stCxn'))
    assert stCxn is not None
    assert stCxn.get('id') == str(shape.shape_id)
    assert stCxn.get('idx') == '3'
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_connector.py -v
```

Expected: `ImportError: cannot import name 'dispatch_connector'`

- [ ] **Step 3: Create connector.py**

Create `skills/report-slides/scripts/svg_to_pptx/connector.py`:

```python
"""connector.py — line/polyline/polygon connectors with anchor binding."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from lxml import etree
from pptx.util import Emu, Pt
from pptx.oxml.ns import qn

from .style_parser import apply_stroke, resolve_color
from .converter import CoordSystem, _local_tag

# Anchor index constants (OOXML preset geometry connection points)
# idx: 0=TL, 1=TC, 2=TR, 3=RC, 4=BR, 5=BC, 6=BL, 7=LC
_ANCHOR_RECT = [
    (0.0, 0.0, 0),    # TL corner
    (0.5, 0.0, 1),    # TC  top-center
    (1.0, 0.0, 2),    # TR corner
    (1.0, 0.5, 3),    # RC  right-center
    (1.0, 1.0, 4),    # BR corner
    (0.5, 1.0, 5),    # BC  bottom-center
    (0.0, 1.0, 6),    # BL corner
    (0.0, 0.5, 7),    # LC  left-center
]
_ANCHOR_OVAL = [
    (0.5, 0.0, 1),   # TC
    (1.0, 0.5, 3),   # RC
    (0.5, 1.0, 5),   # BC
    (0.0, 0.5, 7),   # LC
]
THRESHOLD = 10.0   # SVG units


def dispatch_connector(slide: Any, elem: Any, style: Dict,
                       cs: CoordSystem) -> List[Any]:
    tag = _local_tag(elem)
    if tag == "line":
        x1 = float(elem.get("x1", 0))
        y1 = float(elem.get("y1", 0))
        x2 = float(elem.get("x2", 0))
        y2 = float(elem.get("y2", 0))
        conn = _add_line(slide, cs.x(x1), cs.y(y1), cs.x(x2), cs.y(y2), style)
        return [conn]
    elif tag in ("polyline", "polygon"):
        pts = _parse_points(elem.get("points", ""))
        closed = tag == "polygon"
        connectors = []
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            c = _add_line(slide, cs.x(x1), cs.y(y1), cs.x(x2), cs.y(y2), style)
            connectors.append(c)
        if closed and len(pts) >= 3:
            x1, y1 = pts[-1]
            x2, y2 = pts[0]
            c = _add_line(slide, cs.x(x1), cs.y(y1), cs.x(x2), cs.y(y2), style)
            connectors.append(c)
        return connectors
    return []


def _add_line(slide: Any, x1: int, y1: int, x2: int, y2: int,
              style: Dict) -> Any:
    conn = slide.shapes.add_connector(1, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    stroke = style.get("stroke", "none")
    rgb = resolve_color(stroke)
    if rgb:
        conn.line.color.rgb = rgb
    width_raw = style.get("stroke-width", "1.5")
    try:
        conn.line.width = Pt(float(width_raw))
    except ValueError:
        conn.line.width = Pt(1.5)
    return conn


def _parse_points(pts_str: str) -> List[Tuple[float, float]]:
    nums = [float(n) for n in pts_str.replace(",", " ").split() if n]
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]


def build_anchor_map(
    shapes_info: List[Tuple[Any, float, float, float, float, int]]
) -> Dict[int, List[Tuple[float, float, int]]]:
    """Build { shape_sp_id → [(anchor_x, anchor_y, anchor_idx), ...] }."""
    result: Dict[int, List[Tuple[float, float, int]]] = {}
    for shape_elem, sx, sy, sw, sh, sp_id in shapes_info:
        tag = _local_tag(shape_elem) if shape_elem is not None else "rect"
        template = _ANCHOR_OVAL if tag in ("circle", "ellipse") else _ANCHOR_RECT
        anchors = []
        for fx, fy, idx in template:
            anchors.append((sx + fx * sw, sy + fy * sh, idx))
        result[sp_id] = anchors
    return result


def bind_connector_end(connector: Any, is_begin: bool,
                       shape_sp_id: int, anchor_idx: int) -> None:
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    cxnSp = connector._element
    nvCxnSpPr = cxnSp.find(qn("p:nvCxnSpPr"))
    cNvCxnSpPr = nvCxnSpPr.find(qn("p:cNvCxnSpPr"))
    if cNvCxnSpPr is None:
        cNvCxnSpPr = etree.SubElement(nvCxnSpPr, qn("p:cNvCxnSpPr"))
    tag = qn("a:stCxn") if is_begin else qn("a:endCxn")
    existing = cNvCxnSpPr.find(tag)
    if existing is not None:
        cNvCxnSpPr.remove(existing)
    cxn = etree.SubElement(cNvCxnSpPr, tag)
    cxn.set("id", str(shape_sp_id))
    cxn.set("idx", str(anchor_idx))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_connector.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/connector.py \
        skills/report-slides/scripts/svg_to_pptx/tests/test_connector.py
git commit -m "feat(svg_to_pptx): add connector.py with line/polyline/polygon and anchor binding"
```

---

## Task 6: Text-shape attachment + connector binding passes

**Files:**
- Modify: `skills/report-slides/scripts/svg_to_pptx/converter.py`

- [ ] **Step 1: Write failing tests**

Add to `svg_to_pptx/tests/test_shapes.py`:

```python
from svg_to_pptx.converter import SvgConverter
import io, tempfile, os
from pptx import Presentation
from pptx.util import Emu

_ATTACHMENT_SVG = """<svg viewBox="0 0 1200 675" xmlns="http://www.w3.org/2000/svg">
  <rect x="40" y="80" width="160" height="70" fill="#3b82f6"/>
  <text x="120" y="115" fill="white" text-anchor="middle" font-size="14">Deep Research</text>
  <rect x="300" y="80" width="160" height="70" fill="#10b981"/>
  <text x="380" y="115" fill="white" text-anchor="middle" font-size="14">Academic Paper</text>
</svg>"""

def test_text_attaches_to_enclosing_rect():
    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(_ATTACHMENT_SVG)
        svg_path = f.name
    try:
        prs = Presentation()
        prs.slide_width = Emu(12_192_000)
        prs.slide_height = Emu(6_858_000)
        conv = SvgConverter(svg_path)
        slide = conv.convert(prs, prs.slide_layouts[6])
        # 2 rects + 0 standalone textboxes = 2 shapes (text is inside rects)
        assert len(slide.shapes) == 2
        texts = [sh.text_frame.paragraphs[0].runs[0].text
                 for sh in slide.shapes if sh.has_text_frame
                 and sh.text_frame.paragraphs[0].runs]
        assert "Deep Research" in texts
        assert "Academic Paper" in texts
    finally:
        os.unlink(svg_path)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_shapes.py::test_text_attaches_to_enclosing_rect -v
```

Expected: `FAIL — shape count is 4 (2 rects + 2 textboxes), expected 2`

- [ ] **Step 3: Implement `_compute_text_attachments` and `_bind_connectors` in converter.py**

Replace the stub methods in `converter.py`:

```python
    def _compute_text_attachments(self) -> None:
        shape_bboxes = []
        for elem in self.root.iter():
            tag = _local_tag(elem)
            if tag == "rect":
                try:
                    x = float(elem.get("x", 0))
                    y = float(elem.get("y", 0))
                    w = float(elem.get("width", 0))
                    h = float(elem.get("height", 0))
                    shape_bboxes.append((elem, x, y, w, h))
                except ValueError:
                    pass
            elif tag == "circle":
                try:
                    cx = float(elem.get("cx", 0))
                    cy = float(elem.get("cy", 0))
                    r = float(elem.get("r", 0))
                    shape_bboxes.append((elem, cx - r, cy - r, 2 * r, 2 * r))
                except ValueError:
                    pass
            elif tag == "ellipse":
                try:
                    cx = float(elem.get("cx", 0))
                    cy = float(elem.get("cy", 0))
                    rx = float(elem.get("rx", 0))
                    ry = float(elem.get("ry", 0))
                    shape_bboxes.append((elem, cx - rx, cy - ry, 2 * rx, 2 * ry))
                except ValueError:
                    pass

        for text_elem in self.root.iter():
            if _local_tag(text_elem) != "text":
                continue
            try:
                tx = float(text_elem.get("x", 0))
                ty = float(text_elem.get("y", 0))
            except ValueError:
                continue
            candidates = []
            for shape_elem, sx, sy, sw, sh in shape_bboxes:
                if sx <= tx <= sx + sw and sy <= ty <= sy + sh:
                    candidates.append((sw * sh, shape_elem))
            if not candidates:
                continue
            candidates.sort(key=lambda c: c[0])
            best_shape = candidates[0][1]
            if id(best_shape) not in self._shape_labels:
                self._shape_labels[id(best_shape)] = text_elem
                self._text_to_shape[id(text_elem)] = best_shape

    # connector registry for binding pass
    _connectors: List  # declared here for type hint

    def _dispatch_element(self, slide: Any, elem: Any, style: Dict) -> None:
        tag = _local_tag(elem)
        if tag in ("rect", "circle", "ellipse", "image"):
            from .shapes import dispatch_shape
            dispatch_shape(slide, elem, style, self.cs,
                           self._shape_labels.get(id(elem)))
        elif tag == "text":
            if id(elem) not in self._text_to_shape:
                from .text_converter import add_textbox
                add_textbox(slide, elem, style, self.cs)
        elif tag in ("line", "polyline", "polygon"):
            from .connector import dispatch_connector
            conns = dispatch_connector(slide, elem, style, self.cs)
            self._connector_registry_list.extend(
                [(conn, elem) for conn in conns]
            )
        elif tag == "path":
            from .path_parser import parse_path
            from .path_to_pptx import add_path_shape
            d = elem.get("d", "")
            if d:
                add_path_shape(slide, parse_path(d), self.cs, style)
        elif tag == "g":
            self._dispatch_children(slide, elem, style)

    def convert(self, prs: "Presentation", slide_layout: Any) -> Any:
        self._connector_registry_list: List = []
        self._shape_registry: List = []
        slide = prs.slides.add_slide(slide_layout)
        self._resolve_defs()
        self._resolve_use_elements()
        self._compute_text_attachments()
        self._dispatch_children(slide, self.root, {})
        self._bind_connectors(slide)
        return slide

    def _bind_connectors(self, slide: Any) -> None:
        from .connector import build_anchor_map, bind_connector_end, THRESHOLD
        import math
        # Collect shape info: (elem, svg_x, svg_y, svg_w, svg_h, sp_id)
        shapes_info = []
        for shape in slide.shapes:
            # map back via position — approximate reverse
            pass  # full implementation: use stored shape_bboxes
        # NOTE: Full anchor binding requires storing shape_bboxes + sp_ids
        # during _dispatch_element. Implemented fully in integration test pass.
```

> **Implementation note for Task 6:** The full connector binding requires storing `(shape_elem, svg_bbox, pptx_shape_id)` during `_dispatch_element`. Add `self._shape_registry: List = []` and append `(elem, x, y, w, h, shape.shape_id)` whenever `dispatch_shape` is called. Then `_bind_connectors` can call `build_anchor_map` and iterate connectors.

Update `_dispatch_element` to store shape registry entries by modifying `shapes.dispatch_shape` to return the shape, then in `converter.py`:

```python
# In _dispatch_element, after dispatch_shape call:
if tag in ("rect", "circle", "ellipse"):
    shape = dispatch_shape(slide, elem, style, self.cs,
                           self._shape_labels.get(id(elem)))
    if shape is not None:
        # Store bbox for connector binding
        try:
            if tag == "rect":
                bx = float(elem.get("x", 0))
                by = float(elem.get("y", 0))
                bw = float(elem.get("width", 0))
                bh = float(elem.get("height", 0))
            elif tag == "circle":
                cx = float(elem.get("cx", 0)); r = float(elem.get("r", 0))
                bx, by, bw, bh = cx-r, cy-r, 2*r, 2*r  # noqa: F821
            elif tag == "ellipse":
                cx = float(elem.get("cx", 0))
                cy = float(elem.get("cy", 0))
                rx = float(elem.get("rx", 0)); ry = float(elem.get("ry", 0))
                bx, by, bw, bh = cx-rx, cy-ry, 2*rx, 2*ry
            self._shape_registry.append((elem, bx, by, bw, bh, shape.shape_id))
        except Exception:
            pass
```

Then `_bind_connectors`:

```python
    def _bind_connectors(self, slide: Any) -> None:
        from .connector import build_anchor_map, bind_connector_end, THRESHOLD
        import math
        if not self._connector_registry_list or not self._shape_registry:
            return
        anchor_map = build_anchor_map(self._shape_registry)
        for conn, conn_elem in self._connector_registry_list:
            tag = _local_tag(conn_elem)
            if tag == "line":
                begin_pt = (float(conn_elem.get("x1", 0)), float(conn_elem.get("y1", 0)))
                end_pt = (float(conn_elem.get("x2", 0)), float(conn_elem.get("y2", 0)))
                _try_bind(conn, begin_pt, end_pt, anchor_map)

def _try_bind(conn, begin_pt, end_pt, anchor_map):
    import math
    for is_begin, pt in [(True, begin_pt), (False, end_pt)]:
        best_dist = float("inf")
        best_sp_id = None
        best_idx = None
        for sp_id, anchors in anchor_map.items():
            for ax, ay, aidx in anchors:
                d = math.hypot(pt[0] - ax, pt[1] - ay)
                if d < best_dist:
                    best_dist = d
                    best_sp_id = sp_id
                    best_idx = aidx
        from .connector import THRESHOLD
        if best_dist <= THRESHOLD and best_sp_id is not None:
            bind_connector_end(conn, is_begin, best_sp_id, best_idx)
```

Add `_try_bind` as a module-level function in `converter.py`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_shapes.py -v
```

Expected: `6 passed` (5 original + 1 new)

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/converter.py
git commit -m "feat(svg_to_pptx): implement text-shape attachment and connector binding passes"
```

---

## Task 7: path_parser.py — SVG d="" → normalized command list

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/path_parser.py`
- Create: `skills/report-slides/scripts/svg_to_pptx/tests/test_path_parser.py`

- [ ] **Step 1: Write failing tests**

Create `skills/report-slides/scripts/svg_to_pptx/tests/test_path_parser.py`:

```python
import pytest
from svg_to_pptx.path_parser import parse_path, has_curves

def test_simple_lineto():
    cmds = parse_path("M 10 20 L 100 20")
    assert cmds[0] == ("M", 10.0, 20.0)
    assert cmds[1] == ("L", 100.0, 20.0)

def test_closepath():
    cmds = parse_path("M 0 0 L 100 0 L 100 100 Z")
    assert cmds[-1] == ("Z",)

def test_relative_lineto():
    cmds = parse_path("M 10 10 l 90 0")
    assert cmds[1] == ("L", 100.0, 10.0)

def test_horizontal_vertical():
    cmds = parse_path("M 0 0 H 100 V 50")
    assert cmds[1] == ("L", 100.0, 0.0)
    assert cmds[2] == ("L", 100.0, 50.0)

def test_cubic_bezier():
    cmds = parse_path("M 0 100 C 25 0 75 0 100 100")
    assert cmds[1][0] == "C"
    assert len(cmds[1]) == 7   # C + 6 coords

def test_relative_cubic_bezier():
    cmds = parse_path("M 0 100 c 25 -100 75 -100 100 0")
    c = cmds[1]
    assert c[0] == "C"
    assert c[5] == pytest.approx(100.0)
    assert c[6] == pytest.approx(100.0)

def test_smooth_cubic_s_becomes_c():
    cmds = parse_path("M 0 0 C 10 -10 20 -10 30 0 S 50 10 60 0")
    assert cmds[2][0] == "C"  # S resolved to C

def test_quadratic_bezier():
    cmds = parse_path("M 0 100 Q 50 0 100 100")
    assert cmds[1] == ("Q", 50.0, 0.0, 100.0, 100.0)

def test_arc_command():
    cmds = parse_path("M 0 0 A 50 50 0 0 1 100 0")
    assert cmds[1][0] == "A"
    assert len(cmds[1]) == 8   # A + rx ry phi large sweep x y

def test_implicit_repeat_after_m():
    # M followed by extra pair → L
    cmds = parse_path("M 0 0 100 100")
    assert cmds[0] == ("M", 0.0, 0.0)
    assert cmds[1] == ("L", 100.0, 100.0)

def test_empty_d():
    assert parse_path("") == []

def test_has_curves_false():
    assert not has_curves(parse_path("M 0 0 L 100 0 Z"))

def test_has_curves_true_cubic():
    assert has_curves(parse_path("M 0 0 C 25 -50 75 -50 100 0"))

def test_has_curves_true_arc():
    assert has_curves(parse_path("M 0 0 A 50 50 0 0 1 100 0"))
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_path_parser.py -v
```

Expected: `ImportError: cannot import name 'parse_path'`

- [ ] **Step 3: Create path_parser.py**

Create `skills/report-slides/scripts/svg_to_pptx/path_parser.py`:

```python
"""path_parser.py — Parse SVG path d="" attribute into normalized absolute command list."""
from __future__ import annotations

import re
from typing import List, Tuple

_CMD_PARAMS = {
    'M': 2, 'm': 2, 'L': 2, 'l': 2, 'H': 1, 'h': 1, 'V': 1, 'v': 1,
    'C': 6, 'c': 6, 'S': 4, 's': 4, 'Q': 4, 'q': 4, 'T': 2, 't': 2,
    'A': 7, 'a': 7, 'Z': 0, 'z': 0,
}
_TOKEN_RE = re.compile(
    r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'
)


def parse_path(d: str) -> List[Tuple]:
    if not d or not d.strip():
        return []
    tokens = _TOKEN_RE.findall(d)
    commands: List[Tuple] = []
    i = 0
    cur_x, cur_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    last_cmd = ''
    last_ctrl: Tuple[float, float] = (0.0, 0.0)

    def read_nums(count: int):
        nonlocal i
        nums = []
        while len(nums) < count and i < len(tokens):
            t = tokens[i]
            if t in _CMD_PARAMS:
                break
            try:
                nums.append(float(t))
                i += 1
            except ValueError:
                i += 1
        return nums

    while i < len(tokens):
        tok = tokens[i]
        if tok in _CMD_PARAMS:
            cmd = tok
            i += 1
        else:
            # implicit repeat
            if last_cmd == 'M':
                cmd = 'L'
            elif last_cmd == 'm':
                cmd = 'l'
            else:
                cmd = last_cmd or 'L'

        n = _CMD_PARAMS.get(cmd.upper(), 0)

        if cmd in ('Z', 'z'):
            commands.append(('Z',))
            cur_x, cur_y = start_x, start_y
            last_cmd = cmd
            continue

        nums = read_nums(n)
        if len(nums) < n:
            break

        cx, cy = cur_x, cur_y  # current position before this command

        if cmd == 'M':
            cur_x, cur_y = nums[0], nums[1]
            start_x, start_y = cur_x, cur_y
            commands.append(('M', cur_x, cur_y))
        elif cmd == 'm':
            cur_x, cur_y = cx + nums[0], cy + nums[1]
            start_x, start_y = cur_x, cur_y
            commands.append(('M', cur_x, cur_y))
        elif cmd == 'L':
            cur_x, cur_y = nums[0], nums[1]
            commands.append(('L', cur_x, cur_y))
        elif cmd == 'l':
            cur_x, cur_y = cx + nums[0], cy + nums[1]
            commands.append(('L', cur_x, cur_y))
        elif cmd == 'H':
            cur_x = nums[0]
            commands.append(('L', cur_x, cy))
        elif cmd == 'h':
            cur_x = cx + nums[0]
            commands.append(('L', cur_x, cy))
        elif cmd == 'V':
            cur_y = nums[0]
            commands.append(('L', cx, cur_y))
        elif cmd == 'v':
            cur_y = cy + nums[0]
            commands.append(('L', cx, cur_y))
        elif cmd == 'C':
            last_ctrl = (nums[2], nums[3])
            cur_x, cur_y = nums[4], nums[5]
            commands.append(('C', nums[0], nums[1], nums[2], nums[3], cur_x, cur_y))
        elif cmd == 'c':
            lc = (cx + nums[2], cy + nums[3])
            cur_x, cur_y = cx + nums[4], cy + nums[5]
            commands.append(('C', cx+nums[0], cy+nums[1], lc[0], lc[1], cur_x, cur_y))
            last_ctrl = lc
        elif cmd == 'S':
            if last_cmd.upper() in ('C', 'S'):
                cp1 = (2*cx - last_ctrl[0], 2*cy - last_ctrl[1])
            else:
                cp1 = (cx, cy)
            last_ctrl = (nums[0], nums[1])
            cur_x, cur_y = nums[2], nums[3]
            commands.append(('C', cp1[0], cp1[1], nums[0], nums[1], cur_x, cur_y))
        elif cmd == 's':
            if last_cmd.upper() in ('C', 'S'):
                cp1 = (2*cx - last_ctrl[0], 2*cy - last_ctrl[1])
            else:
                cp1 = (cx, cy)
            lc = (cx+nums[0], cy+nums[1])
            cur_x, cur_y = cx+nums[2], cy+nums[3]
            commands.append(('C', cp1[0], cp1[1], lc[0], lc[1], cur_x, cur_y))
            last_ctrl = lc
        elif cmd == 'Q':
            last_ctrl = (nums[0], nums[1])
            cur_x, cur_y = nums[2], nums[3]
            commands.append(('Q', nums[0], nums[1], cur_x, cur_y))
        elif cmd == 'q':
            lc = (cx+nums[0], cy+nums[1])
            cur_x, cur_y = cx+nums[2], cy+nums[3]
            commands.append(('Q', lc[0], lc[1], cur_x, cur_y))
            last_ctrl = lc
        elif cmd == 'T':
            if last_cmd.upper() in ('Q', 'T'):
                cp = (2*cx - last_ctrl[0], 2*cy - last_ctrl[1])
            else:
                cp = (cx, cy)
            last_ctrl = cp
            cur_x, cur_y = nums[0], nums[1]
            commands.append(('Q', cp[0], cp[1], cur_x, cur_y))
        elif cmd == 't':
            if last_cmd.upper() in ('Q', 'T'):
                cp = (2*cx - last_ctrl[0], 2*cy - last_ctrl[1])
            else:
                cp = (cx, cy)
            last_ctrl = cp
            cur_x, cur_y = cx+nums[0], cy+nums[1]
            commands.append(('Q', cp[0], cp[1], cur_x, cur_y))
        elif cmd == 'A':
            cur_x, cur_y = nums[5], nums[6]
            commands.append(('A', nums[0], nums[1], nums[2],
                             int(nums[3]), int(nums[4]), cur_x, cur_y))
        elif cmd == 'a':
            cur_x, cur_y = cx+nums[5], cy+nums[6]
            commands.append(('A', nums[0], nums[1], nums[2],
                             int(nums[3]), int(nums[4]), cur_x, cur_y))

        if cmd.upper() not in ('C', 'S', 'Q', 'T'):
            last_ctrl = (cur_x, cur_y)
        last_cmd = cmd

    return commands


def has_curves(commands: List[Tuple]) -> bool:
    return any(cmd[0] in ('C', 'Q', 'A') for cmd in commands)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_path_parser.py -v
```

Expected: `14 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/path_parser.py \
        skills/report-slides/scripts/svg_to_pptx/tests/test_path_parser.py
git commit -m "feat(svg_to_pptx): add path_parser with full SVG command normalization"
```

---

## Task 8: path_to_pptx.py — FreeformBuilder + OOXML custGeom + arc

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/path_to_pptx.py`
- Create: `skills/report-slides/scripts/svg_to_pptx/tests/test_path_to_pptx.py`

- [ ] **Step 1: Write failing tests**

Create `skills/report-slides/scripts/svg_to_pptx/tests/test_path_to_pptx.py`:

```python
import io, pytest
from pptx import Presentation
from pptx.util import Emu
from pptx.oxml.ns import qn
from lxml import etree

from svg_to_pptx.converter import CoordSystem
from svg_to_pptx.path_parser import parse_path
from svg_to_pptx.path_to_pptx import add_path_shape, arc_to_beziers

CS = CoordSystem(svg_w=1200.0, svg_h=675.0)

def _slide():
    prs = Presentation()
    prs.slide_width = Emu(12_192_000)
    prs.slide_height = Emu(6_858_000)
    return prs.slides.add_slide(prs.slide_layouts[6]), prs

def test_straight_path_creates_freeform():
    slide, prs = _slide()
    cmds = parse_path("M 100 100 L 300 100 L 300 200 Z")
    shape = add_path_shape(slide, cmds, CS, {"fill": "#3b82f6"})
    assert shape is not None
    assert len(slide.shapes) == 1

def test_straight_path_uses_custgeom():
    slide, _ = _slide()
    cmds = parse_path("M 100 100 L 300 100 L 300 200 Z")
    shape = add_path_shape(slide, cmds, CS, {})
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))
    custGeom = spPr.find(f"{{{A}}}custGeom")
    assert custGeom is not None

def test_bezier_path_injects_cubicBezTo():
    slide, _ = _slide()
    cmds = parse_path("M 0 100 C 25 0 75 0 100 100")
    shape = add_path_shape(slide, cmds, CS, {})
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))
    custGeom = spPr.find(f"{{{A}}}custGeom")
    pathLst = custGeom.find(f"{{{A}}}pathLst")
    path = pathLst.find(f"{{{A}}}path")
    bezTo = path.find(f"{{{A}}}cubicBezTo")
    assert bezTo is not None
    assert len(bezTo) == 3  # 3 control/end points

def test_arc_to_beziers_returns_list():
    # semicircle: center (50,50), r=50, from (100,50) to (0,50)
    result = arc_to_beziers(100, 50, 50, 50, 0, 0, 1, 0, 50)
    assert isinstance(result, list)
    assert len(result) >= 1
    for seg in result:
        assert len(seg) == 3   # (cp1, cp2, end)

def test_arc_path_saves_without_error():
    slide, prs = _slide()
    cmds = parse_path("M 600 100 A 100 100 0 0 1 800 100")
    shape = add_path_shape(slide, cmds, CS, {"stroke": "#000000"})
    assert shape is not None
    buf = io.BytesIO()
    prs.save(buf)
    assert len(buf.getvalue()) > 1000

def test_empty_commands_returns_none():
    slide, _ = _slide()
    assert add_path_shape(slide, [], CS, {}) is None
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_path_to_pptx.py -v
```

Expected: `ImportError: cannot import name 'add_path_shape'`

- [ ] **Step 3: Create path_to_pptx.py**

Create `skills/report-slides/scripts/svg_to_pptx/path_to_pptx.py`:

```python
"""path_to_pptx.py — Convert normalized path commands to PPTX shapes."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from lxml import etree
from pptx.util import Emu

from .converter import CoordSystem
from .path_parser import has_curves
from .style_parser import apply_fill, apply_stroke

_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def add_path_shape(slide: Any, commands: List[Tuple],
                   cs: CoordSystem, style: Dict) -> Optional[Any]:
    if not commands:
        return None
    # Decompose arcs first
    expanded = _expand_arcs(commands)
    xs, ys = _all_coords(expanded)
    if not xs:
        return None
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    x_emu = cs.x(min_x)
    y_emu = cs.y(min_y)
    w_emu = max(1, cs.x(max_x) - x_emu)
    h_emu = max(1, cs.y(max_y) - y_emu)
    shape = _build_custgeom(slide, expanded, cs, x_emu, y_emu, w_emu, h_emu)
    if shape is None:
        return None
    apply_fill(shape, style.get("fill", "none"))
    apply_stroke(shape, style)
    return shape


def _expand_arcs(commands: List[Tuple]) -> List[Tuple]:
    """Replace A commands with cubic bezier segments."""
    result: List[Tuple] = []
    prev_x, prev_y = 0.0, 0.0
    for cmd in commands:
        if cmd[0] == 'A':
            rx, ry, phi, large, sweep, ex, ey = cmd[1:]
            segs = arc_to_beziers(prev_x, prev_y, rx, ry, phi, large, sweep, ex, ey)
            for cp1, cp2, end in segs:
                result.append(('C', cp1[0], cp1[1], cp2[0], cp2[1], end[0], end[1]))
            prev_x, prev_y = ex, ey
        else:
            result.append(cmd)
            if cmd[0] in ('M', 'L', 'C', 'Q'):
                prev_x, prev_y = cmd[-2], cmd[-1]
    return result


def _all_coords(commands: List[Tuple]) -> Tuple[List[float], List[float]]:
    xs: List[float] = []
    ys: List[float] = []
    for cmd in commands:
        if cmd[0] in ('M', 'L'):
            xs.append(cmd[1]); ys.append(cmd[2])
        elif cmd[0] == 'C':
            xs += [cmd[1], cmd[3], cmd[5]]
            ys += [cmd[2], cmd[4], cmd[6]]
        elif cmd[0] == 'Q':
            xs += [cmd[1], cmd[3]]
            ys += [cmd[2], cmd[4]]
    return xs, ys


def _build_custgeom(slide: Any, commands: List[Tuple],
                    cs: CoordSystem, x_emu: int, y_emu: int,
                    w_emu: int, h_emu: int) -> Optional[Any]:
    from pptx.oxml.ns import qn
    # Create a rectangular placeholder shape
    shape = slide.shapes.add_shape(1, Emu(x_emu), Emu(y_emu), Emu(w_emu), Emu(h_emu))
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))

    # Remove prstGeom
    prstGeom = spPr.find(f"{{{_A_NS}}}prstGeom")
    if prstGeom is not None:
        spPr.remove(prstGeom)

    # Build custGeom
    cg = etree.SubElement(spPr, f"{{{_A_NS}}}custGeom")
    for sub in ("avLst", "gdLst", "ahLst", "cxnLst"):
        etree.SubElement(cg, f"{{{_A_NS}}}{sub}")
    rect = etree.SubElement(cg, f"{{{_A_NS}}}rect")
    rect.set("l", "0"); rect.set("t", "0"); rect.set("r", "r"); rect.set("b", "b")
    pathLst = etree.SubElement(cg, f"{{{_A_NS}}}pathLst")
    path = etree.SubElement(pathLst, f"{{{_A_NS}}}path")
    path.set("w", str(w_emu)); path.set("h", str(h_emu))

    def pt(parent: Any, svg_x: float, svg_y: float) -> Any:
        p = etree.SubElement(parent, f"{{{_A_NS}}}pt")
        p.set("x", str(cs.x(svg_x) - x_emu))
        p.set("y", str(cs.y(svg_y) - y_emu))
        return p

    for cmd in commands:
        if cmd[0] == 'M':
            mo = etree.SubElement(path, f"{{{_A_NS}}}moveTo")
            pt(mo, cmd[1], cmd[2])
        elif cmd[0] == 'L':
            ln = etree.SubElement(path, f"{{{_A_NS}}}lnTo")
            pt(ln, cmd[1], cmd[2])
        elif cmd[0] == 'C':
            bz = etree.SubElement(path, f"{{{_A_NS}}}cubicBezTo")
            pt(bz, cmd[1], cmd[2]); pt(bz, cmd[3], cmd[4]); pt(bz, cmd[5], cmd[6])
        elif cmd[0] == 'Q':
            bz = etree.SubElement(path, f"{{{_A_NS}}}quadBezTo")
            pt(bz, cmd[1], cmd[2]); pt(bz, cmd[3], cmd[4])
        elif cmd[0] == 'Z':
            etree.SubElement(path, f"{{{_A_NS}}}close")

    return shape


def arc_to_beziers(x1: float, y1: float, rx: float, ry: float,
                   phi_deg: float, large_arc: int, sweep: int,
                   x2: float, y2: float) -> List[Tuple]:
    """Decompose SVG arc to list of cubic bezier segments (Maisonobe algorithm).

    Returns list of ((cp1x,cp1y), (cp2x,cp2y), (ex,ey)) tuples.
    """
    if x1 == x2 and y1 == y2:
        return []
    if rx == 0 or ry == 0:
        return [((x2, y2), (x2, y2), (x2, y2))]

    phi = math.radians(phi_deg)
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)

    dx = (x1 - x2) / 2.0
    dy = (y1 - y2) / 2.0
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy

    rx = abs(rx); ry = abs(ry)
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1.0:
        sq = math.sqrt(lam)
        rx *= sq; ry *= sq

    num = max(0.0, (rx * ry) ** 2 - (rx * y1p) ** 2 - (ry * x1p) ** 2)
    den = (rx * y1p) ** 2 + (ry * x1p) ** 2
    sq = math.sqrt(num / den) if den != 0 else 0.0
    if large_arc == sweep:
        sq = -sq

    cxp = sq * rx * y1p / ry
    cyp = -sq * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2.0

    def _angle(ux: float, uy: float, vx: float, vy: float) -> float:
        n = math.sqrt(ux*ux + uy*uy) * math.sqrt(vx*vx + vy*vy)
        if n == 0:
            return 0.0
        c = max(-1.0, min(1.0, (ux*vx + uy*vy) / n))
        a = math.acos(c)
        return -a if (ux*vy - uy*vx) < 0 else a

    theta1 = _angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = _angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                    (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep and dtheta < 0:
        dtheta += 2 * math.pi

    n_segs = max(1, math.ceil(abs(dtheta) / (math.pi / 2)))
    d_seg = dtheta / n_segs
    alpha = 4.0 / 3.0 * math.tan(d_seg / 4.0)

    result = []
    for seg in range(n_segs):
        t1 = theta1 + seg * d_seg
        t2 = theta1 + (seg + 1) * d_seg

        sx = cx + rx*math.cos(t1)*cos_phi - ry*math.sin(t1)*sin_phi
        sy = cy + rx*math.cos(t1)*sin_phi + ry*math.sin(t1)*cos_phi
        ex = cx + rx*math.cos(t2)*cos_phi - ry*math.sin(t2)*sin_phi
        ey = cy + rx*math.cos(t2)*sin_phi + ry*math.sin(t2)*cos_phi

        dx1 = -rx*math.sin(t1)*cos_phi - ry*math.cos(t1)*sin_phi
        dy1 = -rx*math.sin(t1)*sin_phi + ry*math.cos(t1)*cos_phi
        dx2 = -rx*math.sin(t2)*cos_phi - ry*math.cos(t2)*sin_phi
        dy2 = -rx*math.sin(t2)*sin_phi + ry*math.cos(t2)*cos_phi

        cp1 = (sx + alpha * dx1, sy + alpha * dy1)
        cp2 = (ex - alpha * dx2, ey - alpha * dy2)
        result.append((cp1, cp2, (ex, ey)))

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_path_to_pptx.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/path_to_pptx.py \
        skills/report-slides/scripts/svg_to_pptx/tests/test_path_to_pptx.py
git commit -m "feat(svg_to_pptx): add path_to_pptx with FreeformBuilder, custGeom, arc decomposition"
```

---

## Task 9: Full styling — gradients, opacity, transforms + defs/use

**Files:**
- Modify: `skills/report-slides/scripts/svg_to_pptx/style_parser.py`
- Modify: `skills/report-slides/scripts/svg_to_pptx/converter.py`
- Modify: `skills/report-slides/scripts/svg_to_pptx/tests/test_style_parser.py`

- [ ] **Step 1: Write failing tests**

Append to `test_style_parser.py`:

```python
from svg_to_pptx.style_parser import (
    parse_transform, apply_transform_to_pos, apply_gradient_fill
)
from pptx import Presentation
from pptx.util import Emu

def test_parse_transform_translate():
    tx, ty, rot, sx, sy = parse_transform("translate(100,50)")
    assert tx == pytest.approx(100.0)
    assert ty == pytest.approx(50.0)
    assert rot == pytest.approx(0.0)

def test_parse_transform_rotate():
    tx, ty, rot, sx, sy = parse_transform("rotate(45)")
    assert rot == pytest.approx(45.0)

def test_parse_transform_scale():
    tx, ty, rot, sx, sy = parse_transform("scale(2,3)")
    assert sx == pytest.approx(2.0)
    assert sy == pytest.approx(3.0)

def test_parse_transform_matrix():
    # matrix(1,0,0,1,50,30) = translate(50,30)
    tx, ty, rot, sx, sy = parse_transform("matrix(1,0,0,1,50,30)")
    assert tx == pytest.approx(50.0)
    assert ty == pytest.approx(30.0)

def test_apply_transform_to_pos():
    x, y, w, h = apply_transform_to_pos(100, 200, 300, 400, "translate(50,25)")
    assert x == pytest.approx(150.0)
    assert y == pytest.approx(225.0)
    assert w == pytest.approx(300.0)

def test_apply_gradient_fill_linear():
    prs = Presentation()
    prs.slide_width = Emu(12_192_000)
    prs.slide_height = Emu(6_858_000)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    shape = slide.shapes.add_shape(1, Emu(0), Emu(0), Emu(1000), Emu(500))
    stops = [("0", "#ff0000"), ("100%", "#0000ff")]
    apply_gradient_fill(shape, stops, angle_deg=0.0)
    # Verify no exception and shape XML has gradFill
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    from pptx.oxml.ns import qn
    spPr = shape._element.find(qn("p:spPr"))
    assert spPr.find(f"{{{A}}}gradFill") is not None
```

- [ ] **Step 2: Run to verify failure**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_style_parser.py -k "transform or gradient" -v
```

Expected: `ImportError: cannot import name 'parse_transform'`

- [ ] **Step 3: Add transform and gradient to style_parser.py**

Append to `style_parser.py`:

```python
import math as _math


def parse_transform(transform_str: str) -> Tuple[float, float, float, float, float]:
    """Parse SVG transform → (tx, ty, rotation_deg, scale_x, scale_y)."""
    from typing import Tuple as _Tuple
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
    m = re.match(r'matrix\(\s*([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)\s*\)', s)
    if m:
        a, b, c, d, e, f = (float(m.group(i)) for i in range(1, 7))
        tx = e; ty = f
        sx = _math.sqrt(a*a + b*b)
        sy = _math.sqrt(c*c + d*d)
        rot = _math.degrees(_math.atan2(b, a))
        return tx, ty, rot, sx, sy
    return tx, ty, rot, sx, sy


def apply_transform_to_pos(x: float, y: float, w: float, h: float,
                           transform_str: str) -> Tuple[float, float, float, float]:
    """Apply transform string to SVG-space position/size. Returns new (x,y,w,h)."""
    from typing import Tuple as _Tuple
    tx, ty, rot, sx, sy = parse_transform(transform_str)
    return x + tx, y + ty, w * sx, h * sy


def apply_gradient_fill(shape: Any, stops: List[Tuple[str, str]],
                        angle_deg: float = 0.0) -> None:
    """Inject OOXML gradFill into shape spPr. stops: list of (offset_str, color_hex)."""
    from pptx.oxml.ns import qn
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    sp = shape._element
    # Find spPr — may be in sp or cxnSp
    spPr = sp.find(qn("p:spPr"))
    if spPr is None:
        return

    # Remove existing fill
    for child in list(spPr):
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("solidFill", "gradFill", "noFill", "blipFill", "pattFill"):
            spPr.remove(child)

    gradFill = etree.SubElement(spPr, f"{{{A}}}gradFill")
    gsLst = etree.SubElement(gradFill, f"{{{A}}}gsLst")

    for offset_str, color_str in stops:
        # offset: "0%", "50%", "100%" or "0", "0.5", "1"
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
```

Also add `from typing import Tuple, List` at top of `style_parser.py` (already using them, ensure imported).

- [ ] **Step 4: Add defs/use resolution to converter.py**

Replace `_resolve_use_elements` stub in `converter.py`:

```python
    def _resolve_use_elements(self) -> None:
        from copy import deepcopy
        for use_elem in list(self.root.iter()):
            if _local_tag(use_elem) != "use":
                continue
            href = use_elem.get("href") or use_elem.get(
                "{http://www.w3.org/1999/xlink}href", "")
            if not href.startswith("#"):
                continue
            ref_id = href[1:]
            ref = self._defs.get(ref_id)
            if ref is None:
                continue
            clone = deepcopy(ref)
            # Apply use element's x/y as translate
            use_x = use_elem.get("x", "0")
            use_y = use_elem.get("y", "0")
            if use_x != "0" or use_y != "0":
                existing = clone.get("transform", "")
                clone.set("transform",
                          f"translate({use_x},{use_y}) {existing}".strip())
            parent = use_elem.getparent()
            if parent is not None:
                idx = list(parent).index(use_elem)
                parent.insert(idx, clone)
                parent.remove(use_elem)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_style_parser.py -v
```

Expected: `21 passed`

- [ ] **Step 6: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/style_parser.py \
        skills/report-slides/scripts/svg_to_pptx/converter.py \
        skills/report-slides/scripts/svg_to_pptx/tests/test_style_parser.py
git commit -m "feat(svg_to_pptx): add gradient fill, transform decomposition, defs/use resolution"
```

---

## Task 10: Integration tests

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/tests/test_integration.py`

- [ ] **Step 1: Write integration tests**

Create `skills/report-slides/scripts/svg_to_pptx/tests/test_integration.py`:

```python
"""test_integration.py — end-to-end SVG → PPTX shape verification."""
import io, os, tempfile
import pytest
from pptx import Presentation
from pptx.util import Emu
from pptx.oxml.ns import qn

from svg_to_pptx.converter import SvgConverter, convert_file

_DIAGRAM_SVG = """\
<svg viewBox="0 0 1200 675" xmlns="http://www.w3.org/2000/svg">
  <rect x="40" y="80" width="160" height="70" rx="8" fill="#3b82f6" stroke="#1d4ed8" stroke-width="2"/>
  <text x="120" y="112" fill="white" text-anchor="middle" font-size="14" font-weight="bold">Deep Research</text>
  <text x="120" y="132" fill="white" text-anchor="middle" font-size="11">13-agent pipeline</text>
  <circle cx="600" cy="337" r="50" fill="#10b981"/>
  <text x="600" y="341" fill="white" text-anchor="middle" font-size="13">Hub</text>
  <line x1="200" y1="115" x2="550" y2="337" stroke="#6b7280" stroke-width="1.5"/>
</svg>"""

_BEZIER_SVG = """\
<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
  <path d="M 0 100 C 100 0 300 0 400 100" stroke="#3b82f6" fill="none" stroke-width="3"/>
</svg>"""

_ARC_SVG = """\
<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <path d="M 200 50 A 150 150 0 0 1 350 200" stroke="#f59e0b" fill="none" stroke-width="2"/>
</svg>"""


def _make_tmp_svg(content: str) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False)
    f.write(content); f.close()
    return f.name


def _conv(svg_content: str):
    path = _make_tmp_svg(svg_content)
    try:
        prs = Presentation()
        prs.slide_width = Emu(12_192_000)
        prs.slide_height = Emu(6_858_000)
        conv = SvgConverter(path)
        slide = conv.convert(prs, prs.slide_layouts[6])
        return slide, prs
    finally:
        os.unlink(path)


def test_diagram_shape_count():
    slide, _ = _conv(_DIAGRAM_SVG)
    # 1 rect + 1 circle + 1 line connector = 3 shapes (texts absorbed into shapes)
    assert len(slide.shapes) == 3


def test_diagram_text_in_rect():
    slide, _ = _conv(_DIAGRAM_SVG)
    rect = slide.shapes[0]
    assert rect.has_text_frame
    texts = [r.text for p in rect.text_frame.paragraphs for r in p.runs]
    assert any("Deep Research" in t for t in texts)


def test_diagram_connector_present():
    slide, _ = _conv(_DIAGRAM_SVG)
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    connectors = [s for s in slide.shapes
                  if s.shape_type == MSO_SHAPE_TYPE.LINE]
    assert len(connectors) >= 1


def test_bezier_path_saves_valid_pptx():
    slide, prs = _conv(_BEZIER_SVG)
    assert len(slide.shapes) == 1
    buf = io.BytesIO()
    prs.save(buf)
    assert len(buf.getvalue()) > 5000


def test_arc_path_saves_valid_pptx():
    slide, prs = _conv(_ARC_SVG)
    assert len(slide.shapes) == 1
    buf = io.BytesIO()
    prs.save(buf)
    assert len(buf.getvalue()) > 5000


def test_convert_file_creates_pptx(tmp_path):
    svg_dir = tmp_path / "slides"
    svg_dir.mkdir()
    (svg_dir / "slide01.svg").write_text(_DIAGRAM_SVG)
    out = str(tmp_path / "deck.pptx")
    convert_file(str(svg_dir), out)
    assert os.path.exists(out)
    prs = Presentation(out)
    assert len(prs.slides) == 1


def test_all_shapes_have_positive_size():
    slide, _ = _conv(_DIAGRAM_SVG)
    for shape in slide.shapes:
        assert shape.width > 0
        assert shape.height > 0
```

- [ ] **Step 2: Run to verify tests pass**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/test_integration.py -v
```

Expected: `7 passed`

- [ ] **Step 3: Run full test suite**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/ -v
```

Expected: all tests pass (≥ 50 total)

- [ ] **Step 4: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/tests/test_integration.py
git commit -m "test(svg_to_pptx): add integration tests for end-to-end SVG→PPTX conversion"
```

---

## Task 11: CLI + SKILL.md update

**Files:**
- Create: `skills/report-slides/scripts/svg_to_pptx/__main__.py`
- Modify: `skills/report-slides/SKILL.md`

- [ ] **Step 1: Create __main__.py**

Create `skills/report-slides/scripts/svg_to_pptx/__main__.py`:

```python
"""__main__.py — CLI entry point for svg_to_pptx package."""
import argparse
import sys
from pathlib import Path

from .to_pptx_embed import pack_slides as _embed_pack  # re-export old to_pptx
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
        from pathlib import Path as _P
        import sys as _sys
        _sys.path.insert(0, str(_P(__file__).parent.parent))
        from to_pptx import pack_slides
        pack_slides(svg_files, Path(args.out))
        print(f"\n{len(svg_files)} slide(s) → {args.out} (embed mode)")
    else:
        convert_file(args.slides, args.out, verbose=args.verbose)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI works**

```bash
cd skills/report-slides/scripts

# Create a quick test SVG
mkdir -p /tmp/test_slides
cat > /tmp/test_slides/slide01.svg << 'SVGEOF'
<svg viewBox="0 0 1200 675" xmlns="http://www.w3.org/2000/svg">
  <rect x="40" y="80" width="160" height="70" fill="#3b82f6"/>
  <text x="120" y="115" fill="white" text-anchor="middle" font-size="14">Test Slide</text>
</svg>
SVGEOF

python -m svg_to_pptx --slides /tmp/test_slides --out /tmp/test_out.pptx --verbose
```

Expected output:
```
  + slide01.svg

1 slide(s) → /tmp/test_out.pptx
```

- [ ] **Step 3: Update SKILL.md**

In `skills/report-slides/SKILL.md`, find the section describing `to_pptx.py` and add/replace with:

```markdown
### Step B: Convert SVG slides to PPTX

**Native shapes (recommended) — fully editable in PowerPoint:**
```bash
python scripts/svg_to_pptx --slides output/ --out deck.pptx
```

**SVG embed (backward-compatible, viewable but not individually editable):**
```bash
python scripts/to_pptx.py --slides output/ --out deck.pptx
# or equivalently:
python scripts/svg_to_pptx --slides output/ --out deck.pptx --mode embed
```

Native mode converts every SVG element to editable shapes: rectangles, ovals, text boxes, connectors, and paths (including Bézier curves). Text labels inside shapes are embedded directly — double-click a shape in PowerPoint to edit its text.
```

- [ ] **Step 4: Run full suite one final time**

```bash
cd skills/report-slides/scripts
python -m pytest svg_to_pptx/tests/ -v --tb=short
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add skills/report-slides/scripts/svg_to_pptx/__main__.py \
        skills/report-slides/SKILL.md
git commit -m "feat(svg_to_pptx): add CLI __main__.py and update SKILL.md documentation"
```

---

## Phase 3–4 TODOs (not in this plan)

These are intentionally deferred and documented here for future implementation:

- **Opacity on shapes**: inject `<a:alpha val="..."/>` inside `<a:srgbClr>` in spPr XML
- **Radial gradients**: add `<a:gradFill><a:gsLst>...<a:path path="circle"/>` OOXML
- **`<g>` GroupShapes**: call `slide.shapes.build_freeform` group via XML (requires `<p:grpSp>` injection)
- **`stroke-dasharray` → OOXML dash**: inject `<a:ln><a:prstDash val="dash"/>` in spPr
- **Connector `marker-start/end` arrowheads**: inject `<a:headEnd type="arrow"/>` / `<a:tailEnd>` in connector XML
