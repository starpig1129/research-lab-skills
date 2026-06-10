# SVG → Native PPTX Converter Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace `skills/report-slides/scripts/to_pptx.py` with a new `svg_to_pptx/` package that converts every SVG element produced by `generate_slides.py` into fully editable native PowerPoint shapes — indistinguishable from manually drawn PPT diagrams.

**Architecture:** SVG → lxml parse → style inheritance pass → text-shape attachment pass → connector binding pass → per-element conversion (shapes / text / path) → python-pptx shapes + OOXML XML injection → `.pptx`.

**Tech Stack:** Python 3.8+, `python-pptx` (already installed), `lxml` (already installed), Python stdlib only — no system dependencies.

---

## 1. Context

### Current Flow

```
slide_data.json
    → generate_slides.py   → slide*.svg  (SVG generation, unchanged)
    → to_pptx.py           → deck.pptx   (embeds SVG as native SVG blip — viewable but NOT editable)
```

### Target Flow

```
slide_data.json
    → generate_slides.py   → slide*.svg  (unchanged)
    → svg_to_pptx/         → deck.pptx   (every element = native editable shape)
```

`to_pptx.py` is **preserved** as a `--mode embed` fallback. The new CLI is fully backward-compatible:

```bash
# New (native shapes — default)
python -m svg_to_pptx --slides ./output/ --out deck.pptx

# Fallback (SVG embed, identical to old to_pptx.py)
python -m svg_to_pptx --slides ./output/ --out deck.pptx --mode embed

# Debug output
python -m svg_to_pptx --slides ./output/ --out deck.pptx --verbose
```

---

## 2. File Structure

```
skills/report-slides/scripts/
├── generate_slides.py              # unchanged
├── to_pptx.py                      # preserved (embed fallback)
└── svg_to_pptx/
    ├── __init__.py                 # exports: SvgConverter, convert_file, cli_main
    ├── converter.py                # orchestration: parse → pre-process → dispatch → save
    ├── style_parser.py             # fill / stroke / opacity / transform resolution
    ├── shapes.py                   # rect, circle, ellipse + text-in-shape write
    ├── text_converter.py           # standalone TextBox (unattached text)
    ├── path_parser.py              # SVG d="" → command list
    ├── path_to_pptx.py             # commands → FreeformBuilder / OOXML custGeom
    ├── connector.py                # line, polyline + anchor binding
    └── tests/
        ├── __init__.py
        ├── test_style_parser.py
        ├── test_shapes.py
        ├── test_text_converter.py
        ├── test_path_parser.py
        ├── test_path_to_pptx.py
        ├── test_connector.py
        └── test_integration.py
```

---

## 3. SVG Element Coverage

### 3a. Basic Shapes (`shapes.py`)

| SVG element | PPTX API | Notes |
|---|---|---|
| `rect` | `add_shape(MSO_SHAPE_TYPE.RECTANGLE)` | `rx` attribute → rounded rectangle |
| `circle` | `add_shape(MSO_SHAPE_TYPE.OVAL)` | `cx/cy/r` → x/y/w/h |
| `ellipse` | `add_shape(MSO_SHAPE_TYPE.OVAL)` | `rx/ry` axes |
| `image` | `add_picture` | href/xlink:href → embedded bitmap |

After creating a shape, `shapes.py` checks whether any text should be attached (see §4).

### 3b. Text (`text_converter.py`)

Text elements NOT consumed by text-shape attachment become standalone TextBox shapes:

- `text` → `add_textbox`, position from `x/y`
- `tspan` → separate `Run` objects inside one `Paragraph`
- Attributes mapped: `font-size`, `font-weight`, `font-family`, `fill` (→ font color), `text-anchor` (start/middle/end → PP_ALIGN.LEFT/CENTER/RIGHT)
- Multi-line text (multiple `tspan` with `dy`) → multiple `Paragraph` objects

### 3c. Paths (`path_parser.py` + `path_to_pptx.py`)

**Parsing** — `path_parser.py` tokenizes the `d` attribute into a normalized absolute command list:
```python
[("M", 10.0, 20.0), ("L", 100.0, 20.0), ("C", 50.0, 0.0, 80.0, 0.0, 100.0, 50.0), ("Z",)]
```
All relative commands (m/l/h/v/c/q/s/t/a/z) are converted to absolute equivalents.

**Conversion dispatch** — `path_to_pptx.py`:

| Commands present | Strategy |
|---|---|
| M/L/H/V/Z only | `FreeformBuilder` (public python-pptx API) |
| Contains C/Q/S/T | OOXML `a:custGeom` injection with `a:cubicBezTo` / `a:quadBezTo` |
| Contains A (arc) | Decompose arc → ≤4 cubic Bézier segments (Maisonobe algorithm), then OOXML |
| S command | Reflect previous C endpoint → treat as C before dispatch |
| T command | Reflect previous Q endpoint → treat as Q before dispatch |

**OOXML custGeom injection:**
```xml
<p:sp>
  <p:spPr>
    <a:custGeom>
      <a:pathLst>
        <a:path w="{emu_w}" h="{emu_h}">
          <a:moveTo><a:pt x="..." y="..."/></a:moveTo>
          <a:cubicBezTo>
            <a:pt x="..." y="..."/>  <!-- control1 -->
            <a:pt x="..." y="..."/>  <!-- control2 -->
            <a:pt x="..." y="..."/>  <!-- end point -->
          </a:cubicBezTo>
          <a:close/>
        </a:path>
      </a:pathLst>
    </a:custGeom>
  </p:spPr>
</p:sp>
```

### 3d. Connectors (`connector.py`)

| SVG element | Strategy |
|---|---|
| `line` | `add_connector(MSO_CONNECTOR_TYPE.STRAIGHT)` |
| `polyline` | Chain of straight connectors, one per segment |
| `polygon` | Closed chain (last point → first point) |
| `marker` attribute | Map to `connector.line.begin_style` / `end_style` using `ArrowheadStyle` |

Marker mapping:
```
marker-end: url(#arrow*)  → ArrowheadStyle.ARROW
marker-end: url(#open*)   → ArrowheadStyle.OPEN
no marker                 → ArrowheadStyle.NONE
```

### 3e. Groups (`converter.py`)

`<g>` elements are recursively converted. Style attributes on `<g>` propagate to children via the style inheritance pass (§5) before conversion begins.

### 3f. `defs` / `use` Resolution (pre-processing in `converter.py`)

Before main conversion:
1. Parse all `<defs>` children into an id-keyed dict
2. For each `<use href="#id">`: clone the referenced element, apply `use`'s `x/y/transform`, replace `<use>` node with clone in the tree
3. After resolution, proceed with normal conversion (no special `use` handling downstream)

---

## 4. Text-Shape Attachment

Runs as a **pre-processing pass** in `converter.py` before any shapes are created.

```
For each <text> element in document order:
  1. Compute text_cx, text_cy (center point from x/y attributes)
  2. For each candidate shape (rect, circle, ellipse) parsed before this text:
       - Compute shape bounding box
       - Check: text_cx inside [shape.x, shape.x + shape.w]
                text_cy inside [shape.y, shape.y + shape.h]
  3. If exactly one match → mark shape as "has_label: <text_element>"
     If multiple matches  → pick smallest area (tightest enclosure)
     If no match          → mark text as standalone
  4. During shape creation (shapes.py):
       - If shape has_label → write text into shape.text_frame (not a TextBox)
       - Standalone text    → text_converter.py creates TextBox
```

**Result:** Double-clicking a shape in PowerPoint opens it for text editing directly. Moving the shape moves the text with it.

---

## 5. Style Resolution (`style_parser.py`)

Priority (highest first):
1. `style="..."` inline CSS attribute (parsed as key:value pairs)
2. Individual presentation attributes (`fill="..."`, `stroke="..."`, etc.)
3. Inherited computed style from parent `<g>`
4. SVG spec defaults (`fill: black`, `stroke: none`)

Supported properties:

| SVG property | python-pptx mapping |
|---|---|
| `fill: #rrggbb` | `shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(...)` |
| `fill: none` | `shape.fill.background()` |
| `fill: url(#gradId)` | Lookup gradient in defs; inject GradFill OOXML |
| `stroke: #rrggbb` | `shape.line.color.rgb = RGBColor(...)` |
| `stroke-width` | `shape.line.width = Pt(...)` |
| `stroke-dasharray` | Map to OOXML dash style (`solid`, `dash`, `dot`, `dashDot`) |
| `opacity` | Inject `<a:solidFill><a:srgbClr><a:alpha val="..."/>` in XML |
| `transform: translate(x,y)` | Apply offset to shape EMU position |
| `transform: rotate(deg,cx,cy)` | `shape.rotation = deg` |
| `transform: scale(sx,sy)` | Multiply width/height by factors |
| `transform: matrix(a,b,c,d,e,f)` | Decompose → translate + rotate + scale |

**Gradient support:** `linearGradient` and `radialGradient` defined in `<defs>` are parsed and injected as OOXML `<a:gradFill>` inside `<p:spPr>`.

**Named colors:** Full CSS named color table (140 colors) resolved to hex in `style_parser.py`.

---

## 6. Connector Binding

Runs as a **post-processing pass** in `converter.py` after all shapes are placed.

```
Build anchor_map: { shape_id → [(anchor_x, anchor_y, anchor_idx), ...] }
  For rect:          8 anchors — N/S/E/W edge centers + 4 corners
  For circle/ellipse: 4 anchors — N/S/E/W edge centers
  THRESHOLD = 10 px (SVG coordinate space)

For each connector in slide:
  For begin_point (x1,y1) and end_point (x2,y2):
    Find nearest anchor across all shapes where distance < THRESHOLD
    If found:
      Inject into connector XML:
        <p:cNvCxnSpPr>
          <a:stCxn  id="{shape_sp_id}" idx="{anchor_idx}"/>  ← begin
          <a:endCxn id="{shape_sp_id}" idx="{anchor_idx}"/>  ← end
        </p:cNvCxnSpPr>
```

**Result:** Dragging a shape in PowerPoint causes its connected arrows to re-route and stay attached — identical to manually drawn connected diagrams.

---

## 7. Coordinate System

SVG `viewBox` → PPTX EMU conversion:

```python
PPTX_W = 12_192_000  # EMU (matches existing to_pptx.py)
PPTX_H =  6_858_000  # EMU

@dataclass
class CoordSystem:
    svg_w: float   # viewBox width
    svg_h: float   # viewBox height

    def x(self, v: float) -> int:
        return round(v / self.svg_w * PPTX_W)

    def y(self, v: float) -> int:
        return round(v / self.svg_h * PPTX_H)
```

`CoordSystem` is instantiated once in `converter.py` and passed to all sub-modules. Missing `viewBox` defaults to `0 0 1200 675` (matches `generate_slides.py`).

---

## 8. Error Handling

| Situation | Behavior |
|---|---|
| Unsupported SVG element (`<filter>`, `<mask>`, etc.) | Skip silently; `--verbose` logs warning with element tag and line |
| Malformed `d` attribute in `<path>` | Skip shape; log error with element source position |
| `<use>` references undefined `id` | Skip; log warning |
| Missing `viewBox` | Default to `0 0 1200 675` |
| Gradient referenced but not in defs | Fall back to solid fill using first `<stop>` `stop-color` |
| Any element exception | Log error; continue with remaining elements (never abort) |

---

## 9. Testing Strategy

**Unit tests (per module):**
- `test_style_parser.py` — inline CSS, attribute fallback, g-inheritance, transform decomposition, named colors, gradient parsing
- `test_path_parser.py` — all command types (M/L/H/V/C/Q/S/T/A/Z), relative→absolute, arc decomposition, empty/malformed input
- `test_shapes.py` — rect sizing/rounding, circle→oval, text-attachment detection (single match, multi-match, no match)
- `test_text_converter.py` — tspan multi-line, text-anchor→PP_ALIGN, font size/weight/color
- `test_connector.py` — anchor map building, threshold distance, OOXML stCxn/endCxn output
- `test_path_to_pptx.py` — straight-only→FreeformBuilder, bezier→custGeom XML wellformed, arc→bezier approximation error bound

**Integration tests (`test_integration.py`):**
- SVG fixture: rect + centered text + circle + arrow between them
  - Assert: shape count = 3 (not 4), text in rect.text_frame, connector has stCxn/endCxn
- SVG fixture: each `generate_slides.py` slide type output
  - Assert: no shapes are None, all shapes have non-zero width/height

---

## 10. Delivery Phases

| Phase | Deliverables |
|---|---|
| **P1 — Core shapes** | `shapes.py`, `text_converter.py`, `style_parser.py` (solid fill/stroke only), `converter.py` skeleton, basic unit tests |
| **P2 — Attachment + binding** | Text-shape attachment pass, connector binding pass, `connector.py`, integration test fixture |
| **P3 — Path support** | `path_parser.py`, `path_to_pptx.py` (FreeformBuilder + custGeom + arc decomposition), path unit tests |
| **P4 — Full styling** | Gradients, opacity, transforms, defs/use resolution, named colors |
| **P5 — CLI + docs** | `__main__.py` entry point, `--mode embed` fallback wiring to `to_pptx.py`, update `report-slides/SKILL.md` |
