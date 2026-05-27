"""
image_renderer.py
"""
from __future__ import annotations
import base64
import io
import os
import tempfile
import urllib.request
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
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

    source = element.get("source") or {}
    kind = source.get("kind", "placeholder")

    if kind == "placeholder":
        _draw_placeholder(canvas, x, y, w, h)
        return

    image_src = None   # file path OR ImageReader
    tmp_path = None    # temp file to clean up after draw

    if kind == "asset":
        asset_id = (source.get("assetId") or source.get("id")
                    or source.get("imageId") or source.get("asset_id") or "")
        asset = ctx.get_asset(asset_id)
        if asset:
            image_src, tmp_path = _resolve_asset_source(asset, assets_base_path)

    elif kind == "url":
        url = source.get("url", "")
        if url.startswith(("http://", "https://")):
            image_src, tmp_path = _fetch_url(url)
        elif url:
            image_src = os.path.join(assets_base_path, url.lstrip("/\\"))

    if not image_src:
        _draw_placeholder(canvas, x, y, w, h)
        return

    # If it's a file path, verify it exists
    if isinstance(image_src, str) and not os.path.exists(image_src):
        _draw_placeholder(canvas, x, y, w, h)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return

    fit = element.get("fit", "contain")
    rotation = element.get("rotation", 0)

    canvas.saveState()
    try:
        if rotation:
            cx, cy = x + w / 2, y + h / 2
            canvas.translate(cx, cy)
            canvas.rotate(rotation)
            canvas.translate(-cx, -cy)

        if fit == "contain":
            canvas.drawImage(image_src, x, y, width=w, height=h,
                             preserveAspectRatio=True, mask="auto")
        elif fit == "cover":
            canvas.drawImage(image_src, x, y, width=w, height=h,
                             preserveAspectRatio=False, mask="auto")
        else:
            canvas.drawImage(image_src, x, y, width=w, height=h, mask="auto")
    except Exception:
        _draw_placeholder(canvas, x, y, w, h)
    finally:
        canvas.restoreState()
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _resolve_asset_source(
    asset: dict,
    assets_base_path: str,
) -> tuple:
    """Returns (image_src, tmp_path). image_src is a file path or ImageReader."""
    asset_source = asset.get("source") or {}
    asset_kind = asset_source.get("kind", "localFile")

    if asset_kind == "base64":
        data_url = asset_source.get("data") or ""
        if data_url.startswith("data:"):
            return _decode_base64(data_url)
        return None, None

    url = (asset_source.get("url") or asset_source.get("path")
           or asset.get("url") or asset.get("path") or asset.get("src") or "")

    if not url:
        return None, None

    if url.startswith(("http://", "https://")):
        return _fetch_url(url)

    file_path = os.path.join(assets_base_path, url.lstrip("/\\"))
    return file_path, None


def _decode_base64(data_url: str) -> tuple:
    """Decode a data:image/...;base64,... URL to a temp file. Returns (path, path)."""
    try:
        header, b64 = data_url.split(",", 1)
        ext = "png"
        if "jpeg" in header or "jpg" in header:
            ext = "jpg"
        elif "gif" in header:
            ext = "gif"
        raw = base64.b64decode(b64)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        tmp.write(raw)
        tmp.flush()
        tmp.close()
        return tmp.name, tmp.name
    except Exception:
        return None, None


def _fetch_url(url: str) -> tuple:
    """Download a remote URL to a temp file. Returns (path, path) or (None, None)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "image/png")
            ext = "png"
            if "jpeg" in content_type or "jpg" in content_type:
                ext = "jpg"
            elif "gif" in content_type:
                ext = "gif"
            raw = resp.read()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        tmp.write(raw)
        tmp.flush()
        tmp.close()
        return tmp.name, tmp.name
    except Exception:
        return None, None


def _draw_placeholder(canvas: Canvas, x: float, y: float, w: float, h: float) -> None:
    canvas.saveState()
    canvas.setFillColorRGB(0.9, 0.9, 0.9)
    canvas.setStrokeColorRGB(0.7, 0.7, 0.7)
    canvas.rect(x, y, w, h, stroke=1, fill=1)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(x + w / 2, y + h / 2 - 4, "[ Image ]")
    canvas.restoreState()
