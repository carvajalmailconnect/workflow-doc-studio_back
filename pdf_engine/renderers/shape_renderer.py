"""
shape_renderer.py  —  all geometric shape types
"""
from __future__ import annotations
import math
from reportlab.pdfgen.canvas import Canvas
from pdf_engine.coordinate import element_rect, mm, safe_float
from pdf_engine.style_registry import StyleRegistry


def render_shape(canvas: Canvas, element: dict, page_h_pt: float, registry: StyleRegistry) -> None:
    shape = element.get("shape", "rectangle")
    x, y, w, h = element_rect(
        element["x"], element["y"], element["width"], element["height"], page_h_pt
    )
    border = element.get("border")

    effective_fill = _resolve_fill(element.get("fill"), border, registry)
    _apply_fill(canvas, effective_fill, registry)
    has_stroke = _apply_border(canvas, border, registry)
    s = 1 if has_stroke else 0

    _DISPATCH.get(shape, _draw_unknown)(canvas, x, y, w, h, border, s)

    canvas.restoreState()


# ── Fill resolution ────────────────────────────────────────────────────────────

def _resolve_fill(fill: dict | None, border: dict | None, registry: StyleRegistry) -> dict | None:
    """Return inline fill; fall back to border style's fillFillStyleId."""
    if fill and fill.get("type") not in (None, "none"):
        return fill
    if border:
        style_ref = border.get("styleRef")
        if style_ref:
            bs = registry.border(style_ref)
            if bs and bs.fill_fill_style_id:
                fs = registry.fill(bs.fill_fill_style_id)
                if fs and fs.type != "none":
                    return {"type": "solid", "color": fs.color, "opacity": fs.opacity}
    return None


def _apply_fill(canvas: Canvas, fill: dict | None, registry: StyleRegistry) -> None:
    canvas.saveState()
    if not fill or fill.get("type") == "none":
        canvas.setFillColorRGB(1, 1, 1, 0)
        return
    if fill.get("type") == "solid":
        color = registry.rl_color(fill.get("color", "#ffffff"), fill.get("opacity", 1.0))
        canvas.setFillColor(color)


def _apply_border(canvas: Canvas, border: dict | None, registry: StyleRegistry) -> bool:
    """Configure stroke state. Returns True if a visible stroke should be drawn."""
    if not border:
        canvas.setStrokeColorRGB(0, 0, 0, 0)
        canvas.setLineWidth(0.001)
        return False

    style_ref = border.get("styleRef")
    if style_ref:
        bs = registry.border(style_ref)
        if bs:
            canvas.setStrokeColor(registry.rl_color(bs.line_color))
            canvas.setLineWidth(mm(bs.line_width))
            return True

    mode = border.get("mode", "none")
    if mode == "unified":
        unified = border.get("unified") or {}
        if unified.get("enabled"):
            canvas.setStrokeColor(registry.rl_color(unified.get("color") or "#000000"))
            canvas.setLineWidth(mm(safe_float(unified.get("width"), 1)))
            return True

    canvas.setStrokeColorRGB(0, 0, 0, 0)
    canvas.setLineWidth(0.001)
    return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _poly(canvas: Canvas, points: list[tuple], stroke: int) -> None:
    path = canvas.beginPath()
    path.moveTo(*points[0])
    for p in points[1:]:
        path.lineTo(*p)
    path.close()
    canvas.drawPath(path, stroke=stroke, fill=1)


def _regular_polygon(canvas: Canvas, x, y, w, h, n: int, stroke: int, start_angle: float = -math.pi / 2) -> None:
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w / 2, h / 2
    pts = [(cx + rx * math.cos(start_angle + 2 * math.pi * i / n),
            cy + ry * math.sin(start_angle + 2 * math.pi * i / n))
           for i in range(n)]
    _poly(canvas, pts, stroke)


def _star_points(cx, cy, rx, ry, n_points: int, inner_ratio: float, start_angle: float) -> list[tuple]:
    pts = []
    for i in range(n_points * 2):
        angle = start_angle + math.pi * i / n_points
        r = (rx, ry) if i % 2 == 0 else (rx * inner_ratio, ry * inner_ratio)
        pts.append((cx + r[0] * math.cos(angle), cy + r[1] * math.sin(angle)))
    return pts


# ── Rectangle variants ─────────────────────────────────────────────────────────

def _draw_rectangle(canvas, x, y, w, h, border, stroke):
    radius = _border_radius(border)
    if radius > 0:
        canvas.roundRect(x, y, w, h, radius, stroke=stroke, fill=1)
    else:
        canvas.rect(x, y, w, h, stroke=stroke, fill=1)


def _draw_round_rect(canvas, x, y, w, h, border, stroke):
    """Rounded rectangle — use fixed 15% radius if border has none."""
    radius = _border_radius(border) or min(w, h) * 0.15
    canvas.roundRect(x, y, w, h, radius, stroke=stroke, fill=1)


def _draw_snip_rect(canvas, x, y, w, h, border, stroke):
    """Top-right corner is cut (snipped) at 45 degrees."""
    cut = min(w, h) * 0.2
    pts = [(x, y), (x + w - cut, y), (x + w, y + cut), (x + w, y + h), (x, y + h)]
    _poly(canvas, pts, stroke)


def _draw_round_rect_1(canvas, x, y, w, h, border, stroke):
    """Only top-right corner is rounded."""
    r = min(w, h) * 0.2
    path = canvas.beginPath()
    path.moveTo(x, y)
    path.lineTo(x + w - r, y)
    path.curveTo(x + w, y, x + w, y, x + w, y + r)
    path.lineTo(x + w, y + h)
    path.lineTo(x, y + h)
    path.close()
    canvas.drawPath(path, stroke=stroke, fill=1)


# ── Lines ──────────────────────────────────────────────────────────────────────

def _draw_line(canvas, x, y, w, h, border, stroke):
    canvas.line(x, y + h / 2, x + w, y + h / 2)


def _draw_line_arrow(canvas, x, y, w, h, border, stroke):
    """Horizontal line with right arrowhead."""
    ah = h * 0.4
    aw = min(w * 0.15, ah * 1.5)
    mid_y = y + h / 2
    canvas.line(x, mid_y, x + w - aw, mid_y)
    pts = [(x + w - aw, mid_y - ah / 2), (x + w, mid_y), (x + w - aw, mid_y + ah / 2)]
    _poly(canvas, pts, stroke)


def _draw_line_darrow(canvas, x, y, w, h, border, stroke):
    """Horizontal line with arrowheads on both ends."""
    ah = h * 0.4
    aw = min(w * 0.15, ah * 1.5)
    mid_y = y + h / 2
    canvas.line(x + aw, mid_y, x + w - aw, mid_y)
    pts_r = [(x + w - aw, mid_y - ah / 2), (x + w, mid_y), (x + w - aw, mid_y + ah / 2)]
    pts_l = [(x + aw, mid_y - ah / 2), (x, mid_y), (x + aw, mid_y + ah / 2)]
    _poly(canvas, pts_r, stroke)
    _poly(canvas, pts_l, stroke)


def _draw_line_elbow(canvas, x, y, w, h, border, stroke):
    """L-shaped elbow connector (top-left → bottom-left → bottom-right)."""
    path = canvas.beginPath()
    path.moveTo(x, y + h)
    path.lineTo(x, y)
    path.lineTo(x + w, y)
    canvas.drawPath(path, stroke=max(stroke, 1), fill=0)


# ── Basic polygons ─────────────────────────────────────────────────────────────

def _draw_ellipse(canvas, x, y, w, h, border, stroke):
    canvas.ellipse(x, y, x + w, y + h, stroke=stroke, fill=1)


def _draw_triangle(canvas, x, y, w, h, border, stroke):
    pts = [(x + w / 2, y + h), (x, y), (x + w, y)]
    _poly(canvas, pts, stroke)


def _draw_right_triangle(canvas, x, y, w, h, border, stroke):
    pts = [(x, y), (x + w, y), (x, y + h)]
    _poly(canvas, pts, stroke)


def _draw_diamond(canvas, x, y, w, h, border, stroke):
    pts = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
    _poly(canvas, pts, stroke)


def _draw_parallelogram(canvas, x, y, w, h, border, stroke):
    offset = w * 0.2
    pts = [(x + offset, y + h), (x, y), (x + w - offset, y), (x + w, y + h)]
    _poly(canvas, pts, stroke)


def _draw_trapezoid(canvas, x, y, w, h, border, stroke):
    inset = w * 0.15
    pts = [(x, y), (x + w, y), (x + w - inset, y + h), (x + inset, y + h)]
    _poly(canvas, pts, stroke)


def _draw_pentagon(canvas, x, y, w, h, border, stroke):
    _regular_polygon(canvas, x, y, w, h, 5, stroke)


def _draw_hexagon(canvas, x, y, w, h, border, stroke):
    _regular_polygon(canvas, x, y, w, h, 6, stroke, start_angle=0)


def _draw_heptagon(canvas, x, y, w, h, border, stroke):
    _regular_polygon(canvas, x, y, w, h, 7, stroke)


def _draw_octagon(canvas, x, y, w, h, border, stroke):
    _regular_polygon(canvas, x, y, w, h, 8, stroke, start_angle=math.pi / 8)


# ── Complex polygons ───────────────────────────────────────────────────────────

def _draw_cross(canvas, x, y, w, h, border, stroke):
    t = w * 0.3
    s = h * 0.3
    pts = [
        (x + (w - t) / 2, y),
        (x + (w + t) / 2, y),
        (x + (w + t) / 2, y + (h - s) / 2),
        (x + w, y + (h - s) / 2),
        (x + w, y + (h + s) / 2),
        (x + (w + t) / 2, y + (h + s) / 2),
        (x + (w + t) / 2, y + h),
        (x + (w - t) / 2, y + h),
        (x + (w - t) / 2, y + (h + s) / 2),
        (x, y + (h + s) / 2),
        (x, y + (h - s) / 2),
        (x + (w - t) / 2, y + (h - s) / 2),
    ]
    _poly(canvas, pts, stroke)


def _draw_chevron(canvas, x, y, w, h, border, stroke):
    tip = w * 0.35
    pts = [
        (x, y),
        (x + w - tip, y),
        (x + w, y + h / 2),
        (x + w - tip, y + h),
        (x, y + h),
        (x + tip, y + h / 2),
    ]
    _poly(canvas, pts, stroke)


def _draw_home_plate(canvas, x, y, w, h, border, stroke):
    """Pentagon like a baseball home plate (flat top, pointed bottom)."""
    pts = [
        (x, y + h),
        (x, y + h * 0.4),
        (x + w / 2, y),
        (x + w, y + h * 0.4),
        (x + w, y + h),
    ]
    _poly(canvas, pts, stroke)


def _draw_arrow_right(canvas, x, y, w, h, border, stroke):
    shaft_h = h * 0.4
    head_w = w * 0.35
    pts = [
        (x, y + (h - shaft_h) / 2),
        (x + w - head_w, y + (h - shaft_h) / 2),
        (x + w - head_w, y),
        (x + w, y + h / 2),
        (x + w - head_w, y + h),
        (x + w - head_w, y + (h + shaft_h) / 2),
        (x, y + (h + shaft_h) / 2),
    ]
    _poly(canvas, pts, stroke)


def _draw_arrow_lr(canvas, x, y, w, h, border, stroke):
    shaft_h = h * 0.4
    head_w = w * 0.25
    pts = [
        (x, y + h / 2),
        (x + head_w, y),
        (x + head_w, y + (h - shaft_h) / 2),
        (x + w - head_w, y + (h - shaft_h) / 2),
        (x + w - head_w, y),
        (x + w, y + h / 2),
        (x + w - head_w, y + h),
        (x + w - head_w, y + (h + shaft_h) / 2),
        (x + head_w, y + (h + shaft_h) / 2),
        (x + head_w, y + h),
    ]
    _poly(canvas, pts, stroke)


def _draw_arrow_ud(canvas, x, y, w, h, border, stroke):
    shaft_w = w * 0.4
    head_h = h * 0.25
    pts = [
        (x + w / 2, y),
        (x + w, y + head_h),
        (x + (w + shaft_w) / 2, y + head_h),
        (x + (w + shaft_w) / 2, y + h - head_h),
        (x + w, y + h - head_h),
        (x + w / 2, y + h),
        (x, y + h - head_h),
        (x + (w - shaft_w) / 2, y + h - head_h),
        (x + (w - shaft_w) / 2, y + head_h),
        (x, y + head_h),
    ]
    _poly(canvas, pts, stroke)


def _draw_arrow_bent(canvas, x, y, w, h, border, stroke):
    """Bent/curved arrow pointing right-down."""
    shaft_h = h * 0.35
    shaft_w = w * 0.35
    head_w = w * 0.3
    head_h = h * 0.4
    pts = [
        (x, y + h),
        (x, y + h * 0.35),
        (x + w - head_w, y + h * 0.35),
        (x + w - head_w, y),
        (x + w, y + h / 2),
        (x + w - head_w, y + h),
        (x + w - head_w, y + h * 0.35 + shaft_h),
        (x + shaft_w, y + h * 0.35 + shaft_h),
        (x + shaft_w, y + h),
    ]
    _poly(canvas, pts, stroke)


# ── Math symbols ───────────────────────────────────────────────────────────────

def _draw_math_plus(canvas, x, y, w, h, border, stroke):
    _draw_cross(canvas, x, y, w, h, border, stroke)


def _draw_math_multiply(canvas, x, y, w, h, border, stroke):
    t = min(w, h) * 0.2
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) / 2
    c = math.cos(math.pi / 4)
    s = math.sin(math.pi / 4)
    ht = t / 2

    def rot(px, py):
        return cx + c * (px - cx) - s * (py - cy), cy + s * (px - cx) + c * (py - cy)

    base_pts = [
        (cx - ht, y), (cx + ht, y),
        (cx + ht, cy - ht), (x + w, cy - ht),
        (x + w, cy + ht), (cx + ht, cy + ht),
        (cx + ht, y + h), (cx - ht, y + h),
        (cx - ht, cy + ht), (x, cy + ht),
        (x, cy - ht), (cx - ht, cy - ht),
    ]
    pts = [rot(px, py) for px, py in base_pts]
    _poly(canvas, pts, stroke)


def _draw_math_divide(canvas, x, y, w, h, border, stroke):
    """Divide symbol: horizontal bar with dots above and below."""
    bar_h = h * 0.08
    dot_r = min(w, h) * 0.06
    bar_y = y + h / 2 - bar_h / 2
    canvas.rect(x + w * 0.1, bar_y, w * 0.8, bar_h, stroke=stroke, fill=1)
    canvas.circle(x + w / 2, y + h * 0.75, dot_r, stroke=stroke, fill=1)
    canvas.circle(x + w / 2, y + h * 0.25, dot_r, stroke=stroke, fill=1)


def _draw_math_equal(canvas, x, y, w, h, border, stroke):
    bar_h = h * 0.12
    gap = h * 0.08
    cy = y + h / 2
    canvas.rect(x + w * 0.1, cy + gap / 2, w * 0.8, bar_h, stroke=stroke, fill=1)
    canvas.rect(x + w * 0.1, cy - gap / 2 - bar_h, w * 0.8, bar_h, stroke=stroke, fill=1)


def _draw_math_nequal(canvas, x, y, w, h, border, stroke):
    _draw_math_equal(canvas, x, y, w, h, border, stroke)
    # Diagonal slash
    canvas.saveState()
    canvas.setLineWidth(mm(0.6))
    canvas.line(x + w * 0.3, y + h * 0.2, x + w * 0.7, y + h * 0.8)
    canvas.restoreState()


# ── Curved shapes ──────────────────────────────────────────────────────────────

def _draw_heart(canvas, x, y, w, h, border, stroke):
    cx = x + w / 2
    top_y = y + h * 0.7
    path = canvas.beginPath()
    path.moveTo(cx, y)
    path.curveTo(cx + w * 0.5, y - h * 0.1, cx + w * 0.5, top_y, cx, y + h / 2)
    path.curveTo(cx - w * 0.5, top_y, cx - w * 0.5, y - h * 0.1, cx, y)
    canvas.drawPath(path, stroke=stroke, fill=1)


def _draw_heart_v2(canvas, x, y, w, h, border, stroke):
    """Heart shape with cubic bezier curves, tip at bottom."""
    cx = x + w / 2
    # Two bumps at top, pointed bottom
    path = canvas.beginPath()
    path.moveTo(cx, y + h * 0.35)  # top-center valley
    # Left bump
    path.curveTo(cx - w * 0.05, y + h * 0.1,
                 cx - w * 0.5, y,
                 cx - w * 0.5, y + h * 0.35)
    path.curveTo(cx - w * 0.5, y + h * 0.65,
                 cx, y + h * 0.75,
                 cx, y + h)  # bottom tip
    # Right side
    path.curveTo(cx, y + h * 0.75,
                 cx + w * 0.5, y + h * 0.65,
                 cx + w * 0.5, y + h * 0.35)
    path.curveTo(cx + w * 0.5, y,
                 cx + w * 0.05, y + h * 0.1,
                 cx, y + h * 0.35)
    path.close()
    canvas.drawPath(path, stroke=stroke, fill=1)


def _draw_lightning(canvas, x, y, w, h, border, stroke):
    pts = [
        (x + w * 0.65, y),
        (x + w * 0.35, y + h * 0.45),
        (x + w * 0.6, y + h * 0.45),
        (x + w * 0.35, y + h),
        (x + w * 0.65, y + h * 0.55),
        (x + w * 0.4, y + h * 0.55),
    ]
    _poly(canvas, pts, stroke)


def _draw_moon(canvas, x, y, w, h, border, stroke):
    """Crescent moon using two arcs (outer circle minus inner offset circle)."""
    path = canvas.beginPath()
    cx = x + w * 0.45
    cy = y + h / 2
    r_out = min(w, h) / 2
    # Outer arc (full)
    path.arc(cx - r_out, cy - r_out, cx + r_out, cy + r_out, 0, 360)
    canvas.drawPath(path, stroke=stroke, fill=1)
    # Erase with background — approximate by drawing the cutout in white
    # Better approach: use a clipping path or polygon approximation
    canvas.saveState()
    canvas.setFillColorRGB(1, 1, 1)
    canvas.setStrokeColorRGB(1, 1, 1)
    cx2 = cx + w * 0.2
    canvas.circle(cx2, cy, r_out * 0.85, stroke=0, fill=1)
    canvas.restoreState()


def _draw_cloud(canvas, x, y, w, h, border, stroke):
    """Cloud approximated with overlapping circles."""
    r1 = h * 0.28
    r2 = h * 0.22
    r3 = h * 0.18
    base_y = y + h * 0.4
    # Draw base rect (bottom of cloud)
    canvas.rect(x + r3, base_y - r1, w - 2 * r3, h * 0.6 + r1, stroke=0, fill=1)
    # Bumps
    for cx_frac, r in [(0.2, r2), (0.4, r1), (0.6, r1), (0.8, r2)]:
        canvas.circle(x + w * cx_frac, base_y, r, stroke=0, fill=1)
    # Left and right edge circles
    canvas.circle(x + r3, base_y - r1 * 0.3, r3, stroke=0, fill=1)
    canvas.circle(x + w - r3, base_y - r1 * 0.3, r3, stroke=0, fill=1)
    # Draw outline if stroke
    if stroke:
        canvas.setFillColorRGB(0, 0, 0, 0)
        for cx_frac, r in [(0.2, r2), (0.4, r1), (0.6, r1), (0.8, r2)]:
            canvas.circle(x + w * cx_frac, base_y, r, stroke=1, fill=0)


def _draw_pie(canvas, x, y, w, h, border, stroke):
    """Pie/sector — 270-degree arc (¾ circle)."""
    path = canvas.beginPath()
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) / 2
    path.moveTo(cx, cy)
    path.arc(cx - r, cy - r, cx + r, cy + r, 0, 270)
    path.close()
    canvas.drawPath(path, stroke=stroke, fill=1)


def _draw_teardrop(canvas, x, y, w, h, border, stroke):
    """Teardrop: circle top, pointed bottom."""
    r = w * 0.35
    cx = x + w / 2
    cy = y + h - r
    path = canvas.beginPath()
    path.arc(cx - r, cy - r, cx + r, cy + r, 45, 315)
    path.lineTo(cx, y)
    path.close()
    canvas.drawPath(path, stroke=stroke, fill=1)


def _draw_starburst(canvas, x, y, w, h, border, stroke):
    cx, cy = x + w / 2, y + h / 2
    pts = _star_points(cx, cy, w / 2, h / 2, 12, 0.6, -math.pi / 12)
    _poly(canvas, pts, stroke)


def _draw_star6(canvas, x, y, w, h, border, stroke):
    cx, cy = x + w / 2, y + h / 2
    pts = _star_points(cx, cy, w / 2, h / 2, 6, 0.5, -math.pi / 2)
    _poly(canvas, pts, stroke)


def _draw_unknown(canvas, x, y, w, h, border, stroke):
    """Fallback: draw a dashed rectangle outline only."""
    canvas.saveState()
    canvas.setDash(3, 3)
    canvas.rect(x, y, w, h, stroke=1, fill=0)
    canvas.restoreState()


# ── Border radius helper ───────────────────────────────────────────────────────

def _border_radius(border: dict | None) -> float:
    if not border:
        return 0
    radius_cfg = border.get("radius") or {}
    mode = str(radius_cfg.get("mode", "unified")).lower()
    if mode in ("none", "standard", "disabled"):
        return 0
    return mm(safe_float(radius_cfg.get("unified"), 0))


# ── Dispatch table ─────────────────────────────────────────────────────────────

_DISPATCH = {
    "rectangle":     _draw_rectangle,
    "round-rect":    _draw_round_rect,
    "snip-rect":     _draw_snip_rect,
    "round-rect-1":  _draw_round_rect_1,
    "ellipse":       _draw_ellipse,
    "triangle":      _draw_triangle,
    "right-triangle": _draw_right_triangle,
    "diamond":       _draw_diamond,
    "parallelogram": _draw_parallelogram,
    "trapezoid":     _draw_trapezoid,
    "pentagon":      _draw_pentagon,
    "hexagon":       _draw_hexagon,
    "heptagon":      _draw_heptagon,
    "octagon":       _draw_octagon,
    "cross":         _draw_cross,
    "chevron":       _draw_chevron,
    "home-plate":    _draw_home_plate,
    "heart":         _draw_heart_v2,
    "lightning":     _draw_lightning,
    "moon":          _draw_moon,
    "cloud":         _draw_cloud,
    "pie":           _draw_pie,
    "teardrop":      _draw_teardrop,
    "arrow-right":   _draw_arrow_right,
    "arrow-lr":      _draw_arrow_lr,
    "arrow-ud":      _draw_arrow_ud,
    "arrow-bent":    _draw_arrow_bent,
    "math-plus":     _draw_math_plus,
    "math-multiply": _draw_math_multiply,
    "math-divide":   _draw_math_divide,
    "math-equal":    _draw_math_equal,
    "math-nequal":   _draw_math_nequal,
    "starburst":     _draw_starburst,
    "star6":         _draw_star6,
    "line":          _draw_line,
    "line-arrow":    _draw_line_arrow,
    "line-darrow":   _draw_line_darrow,
    "line-elbow":    _draw_line_elbow,
}
