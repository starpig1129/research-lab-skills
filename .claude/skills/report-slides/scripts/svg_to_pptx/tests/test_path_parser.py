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
    assert len(cmds[1]) == 7


def test_relative_cubic_bezier():
    cmds = parse_path("M 0 100 c 25 -100 75 -100 100 0")
    c = cmds[1]
    assert c[0] == "C"
    assert c[5] == pytest.approx(100.0)
    assert c[6] == pytest.approx(100.0)


def test_smooth_cubic_s_becomes_c():
    cmds = parse_path("M 0 0 C 10 -10 20 -10 30 0 S 50 10 60 0")
    assert cmds[2][0] == "C"


def test_quadratic_bezier():
    cmds = parse_path("M 0 100 Q 50 0 100 100")
    assert cmds[1] == ("Q", 50.0, 0.0, 100.0, 100.0)


def test_arc_command():
    cmds = parse_path("M 0 0 A 50 50 0 0 1 100 0")
    assert cmds[1][0] == "A"
    assert len(cmds[1]) == 8


def test_implicit_repeat_after_m():
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
