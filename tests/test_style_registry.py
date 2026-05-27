import pytest
from pdf_engine.normalize import normalize
from pdf_engine.style_registry import StyleRegistry, ResolvedTextStyle, ResolvedParagraphStyle
from reportlab.lib.colors import HexColor


def test_builds_from_context(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    assert registry is not None


def test_default_text_style(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    ts = registry.text("ts_default")
    assert ts.id == "ts_default"
    assert ts.font_size == 12
    assert ts.color == "#1f2937"


def test_missing_text_style_returns_default(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    ts = registry.text("nonexistent_id")
    assert ts.id == "ts_default"


def test_default_paragraph_style(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    ps = registry.paragraph("ps_default")
    assert ps.alignment == "left"
    assert ps.line_height == 1.4


def test_missing_paragraph_returns_default(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    ps = registry.paragraph("nonexistent")
    assert ps.id == "ps_default"


def test_fill_style(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    fs = registry.fill("fs_blue")
    assert fs is not None
    assert fs.color == "#246ed6"
    assert fs.type == "solid"


def test_missing_fill_returns_none(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    assert registry.fill("nonexistent") is None


def test_rl_color_hex(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    color = registry.rl_color("#ff0000")
    assert abs(color.red - 1.0) < 0.01
    assert abs(color.green - 0.0) < 0.01


def test_rl_color_with_opacity(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    color = registry.rl_color("#000000", opacity=0.5)
    assert abs(color.alpha - 0.5) < 0.01


def test_rl_color_invalid_falls_back(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    color = registry.rl_color("not-a-color")
    assert color is not None


def test_bold_detected(minimal_template, minimal_data):
    template = dict(minimal_template)
    template["styles"] = dict(minimal_template["styles"])
    template["styles"]["text"] = minimal_template["styles"]["text"] + [
        {"id": "ts_bold", "name": "Bold", "fontFamily": "Inter", "fontWeight": "Bold",
         "fontSize": 12, "color": "#000", "italic": False, "underline": False,
         "strikethrough": False, "letterSpacing": 0, "lineHeight": 1.4,
         "superscript": False, "subscript": False, "superscriptOffset": 33,
         "subscriptOffset": 33, "superSubSize": 58, "textTransform": "none",
         "fillStyleId": None, "borderStyleId": None}
    ]
    ctx = normalize(template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    ts = registry.text("ts_bold")
    assert ts.bold is True
    assert ts.font_weight == "Bold"


def test_font_name_resolves(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    registry = StyleRegistry.from_context(ctx)
    ts = registry.text("ts_default")
    name = registry.font_name(ts)
    assert isinstance(name, str)
    assert len(name) > 0
