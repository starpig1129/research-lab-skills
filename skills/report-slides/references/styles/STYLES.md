# Slide Styles Reference

Loaded by `report-slides` to resolve styles during slide generation.
Read this file when resolving a style or when writing [C] Claude SVG slides.

---

## Built-in styles

| Name | File | Best for |
|------|------|----------|
| `default` | `styles/default.md` | Academic meetings, research progress reports |
| `minimal` | `styles/minimal.md` | Print, publications, no-color contexts |
| `dark` | `styles/dark.md` | Projector rooms, conference presentations |
| `paper` | `styles/paper.md` | Thesis / journal paper style — dark teal-blue on white |

---

## Frontmatter schema

All fields are optional; missing fields fall back to `default` values.

| Key | Type | Description | Default |
|-----|------|-------------|---------|
| `name` | string | Style identifier (slug) | — |
| `description` | string | One-line description | — |
| `primary` | hex | Accent color: top bar, titles, bullets | `#1e3a5f` |
| `bg` | hex | Slide background | `#ffffff` |
| `body` | hex | Main text | `#374151` |
| `muted` | hex | Captions, footer, axis labels | `#64748b` |
| `border` | hex | Dividers, card borders | `#e2e8f0` |
| `card` | hex | Card / alternating row fill | `#f8fafc` |
| `positive` | hex | Success / increase values | `#059669` |
| `warn` | hex | Caution values | `#d97706` |
| `danger` | hex | Error / decrease values | `#dc2626` |
| `font` | CSS string | `font-family` attribute | `'Helvetica Neue', Arial, sans-serif` |
| `top_bar_h` | int | Top accent bar height in px | `6` |

---

## Applying to [C] Claude SVG slides

When writing SVG directly (Path C), read the resolved style file's frontmatter and
substitute its values. Treat missing keys as the defaults in the table above.

The standard slide structure (canvas, top bar, title, divider, footer) stays constant —
only the color and font values change:

```
viewBox="0 0 1200 675"
<rect fill="{bg}"/>
<rect x="0" y="0" width="1200" height="{top_bar_h}" fill="{primary}"/>
<text x="600" y="44" font-size="20" font-weight="700" fill="{primary}" text-anchor="middle">
<line x1="40" y1="54" x2="1160" y2="54" stroke="{border}" stroke-width="1.5"/>
<text x="1160" y="660" font-size="10" fill="{muted}" text-anchor="end">
font-family="{font}"
```

Color roles within slide content:
- Section headers, bullet markers → `primary`
- Body paragraphs → `body`
- Captions, notes, secondary labels → `muted`
- Positive numbers / improvements → `positive`
- Warnings / caveats → `warn`
- Errors / regressions → `danger`

---

## Creating a custom style

Copy any built-in as a starting point and edit its frontmatter:

```yaml
---
name: mycompany
description: Company brand — teal on off-white
primary: "#0d9488"
bg: "#f8fafc"
positive: "#0d9488"
warn: "#d97706"
danger: "#dc2626"
body: "#1e293b"
muted: "#64748b"
border: "#e2e8f0"
card: "#f1f5f9"
font: "'Inter', Arial, sans-serif"
top_bar_h: 8
---
```

Save to `docs/slides/styles/<name>.md` for a project-local named style, or copy to
`docs/slides/_style.md` to make it the project default.
