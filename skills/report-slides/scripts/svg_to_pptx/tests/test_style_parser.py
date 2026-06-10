import pytest
from svg_to_pptx.converter import CoordSystem

def test_coordsystem_from_viewbox():
    cs = CoordSystem.from_viewbox("0 0 1200 675")
    assert cs.svg_w == 1200.0
    assert cs.svg_h == 675.0

def test_coordsystem_x_scaling():
    cs = CoordSystem.from_viewbox("0 0 1200 675")
    assert cs.x(600) == 6_096_000

def test_coordsystem_y_scaling():
    cs = CoordSystem.from_viewbox("0 0 1200 675")
    assert cs.y(337.5) == 3_429_000

def test_coordsystem_missing_viewbox():
    cs = CoordSystem.from_viewbox("")
    assert cs.svg_w == 1200.0
    assert cs.svg_h == 675.0

def test_coordsystem_malformed_viewbox():
    cs = CoordSystem.from_viewbox("0 0 abc 675")
    assert cs.svg_w == 1200.0
    assert cs.svg_h == 675.0
