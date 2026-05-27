"""
image_renderer.py
"""
from __future__ import annotations
import os
from reportlab.pdfgen.canvas import Canvas
from pdf_engine.coordinate import element_rect
from pdf_engine.normalize import DocumentContext
from pdf_engine.style_registry import StyleRegistry


def render_image(
    canvas: Canvas,
    element: dict,
    page_h_pt: float,
    ctx: DocumentContext,
    registry: StyleRegistry,
    assets_base_path: str = "",
) -> None:
    x, y, w, h = element_rect(
        element["x"], element["y"], element["width"], element["height"], page_h_pt
    )

    source = element.get("source", {})
    kind = source.get("kind", "placeholder")

    if kind == "placeholder":
        _draw_placeholder(canvas, x, y, w, h)
        return

    image_path = None

    if kind == "asset":
        asset = ctx.get_asset(source.get("assetId", ""))
        if asset:
            asset_source = asset.get("source", {})
            url = asset_source.get("url", "")
            # url is like "/images/filename.png" — resolve against base path
            image_path = os.path.join(assets_base_path, url.lstrip("/"))

    elif kind == "url":
        image_path = source.get("url", "")

    if not image_path or not os.path.exists(image_path):
        _draw_placeholder(canvas, x, y, w, h)
        return

    fit = element.get("fit", "contain")
    rotation = element.get("rotation", 0)

    canvas.saveState()
    if rotation:
        # Rotate around the element's centre point
        cx, cy = x + w / 2, y + h / 2
        canvas.translate(cx, cy)
        canvas.rotate(rotation)
        canvas.translate(-cx, -cy)

    if fit == "contain":
        canvas.drawImage(image_path, x, y, width=w, height=h,
                         preserveAspectRatio=True, mask="auto")
    elif fit == "cover":
        canvas.drawImage(image_path, x, y, width=w, height=h,
                         preserveAspectRatio=False, mask="auto")
    else:
        canvas.drawImage(image_path, x, y, width=w, height=h, mask="auto")

    canvas.restoreState()


def _draw_placeholder(canvas: Canvas, x: float, y: float, w: float, h: float) -> None:
    canvas.saveState()
    canvas.setFillColorRGB(0.9, 0.9, 0.9)
    canvas.setStrokeColorRGB(0.7, 0.7, 0.7)
    canvas.rect(x, y, w, h, stroke=1, fill=1)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(x + w / 2, y + h / 2 - 4, "[ Image ]")
    canvas.restoreState()
