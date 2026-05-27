"""
api/main.py  —  FastAPI entrypoint

Endpoints:
  POST /generate       Full workflow execution → PDF bytes
  POST /render         Direct templateJson + data → PDF (no workflow graph)
  GET  /health         Liveness check
  GET  /test-render    Genera PDF de prueba sin payload (smoke-test rápido)

Run with:
  uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
  python run.py server --reload

Swagger UI: http://localhost:8080/docs
"""

from __future__ import annotations
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from workflow.executor import execute, WorkflowExecutionError
from pdf_engine.normalize import normalize
from pdf_engine.page_renderer import render_pdf

app = FastAPI(title="Workflow Doc Studio — PDF Engine", version="1.0.0")

ASSETS_BASE_PATH = os.environ.get("ASSETS_BASE_PATH", "")


# ── Request/response models ───────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    """Full workflow execution: graph + trigger data → PDF."""
    workflow: dict           # the full workflow JSON from workflow-doc-studio
    data: dict[str, Any] = {}  # trigger payload (webhook body, etc.)


class RenderRequest(BaseModel):
    """Direct render: templateJson + data context → PDF (skips workflow graph)."""
    templateJson: dict
    data: dict[str, Any] = {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/generate", summary="Execute workflow graph and generate PDF")
async def generate(request: Request) -> Response:
    """
    Accepts two formats:

    Format A — raw workflow JSON (what the front-end exports directly):
      { "version": "1.0", "nodes": [...], "edges": [...] }

    Format B — wrapped with optional trigger data:
      { "workflow": { "version": "1.0", "nodes": [...], "edges": [...] }, "data": {...} }
    """
    body = await request.json()

    # Detect format: if body has "nodes" or "edges" at root it's a raw workflow
    if "nodes" in body or "edges" in body:
        workflow = body
        data = {}
    else:
        try:
            req = GenerateRequest.model_validate(body)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        workflow = req.workflow
        data = req.data

    try:
        template_json, data_context = execute(workflow, data)
    except WorkflowExecutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {exc}")

    return _render_to_response(template_json, data_context)


@app.post("/render", summary="Render templateJson directly to PDF")
async def render(req: RenderRequest) -> Response:
    """
    Skips workflow graph execution. Useful for previewing a single template
    with a known data payload.
    """
    return _render_to_response(req.templateJson, req.data)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/test-render", summary="Genera un PDF de prueba (smoke-test)")
async def test_render() -> Response:
    """
    Genera un PDF mínimo sin necesidad de payload.
    Útil para confirmar desde Postman/curl que el servidor responde.
    """
    template = {
        "version": "1.0",
        "styles": {
            "text": [{"id": "ts_default", "name": "Default", "fontFamily": "Helvetica",
                      "fontWeight": "Regular", "fontSize": 14, "color": "#1f2937",
                      "italic": False, "underline": False, "strikethrough": False,
                      "letterSpacing": 0, "lineHeight": 1.5, "superscript": False,
                      "subscript": False, "superscriptOffset": 33, "subscriptOffset": 33,
                      "superSubSize": 58, "textTransform": "none",
                      "fillStyleId": None, "borderStyleId": None}],
            "paragraph": [{"id": "ps_default", "name": "Default", "alignment": "left",
                           "verticalAlign": "top", "lineHeight": 1.5, "letterSpacing": 0,
                           "firstLineIndent": 0, "leftIndent": 0, "rightIndent": 0,
                           "spaceBefore": 0, "spaceAfter": 0, "wordWrap": True,
                           "listStyle": "none", "listIndent": 5, "listColor": "",
                           "defaultTextStyleId": None}],
            "border": [], "fill": [], "cell": [], "line": [],
        },
        "images": [], "fonts": [], "rowSets": [], "outputChannels": ["pdf"],
        "pages": [{
            "id": "pg1", "name": "Page 1", "visible": True,
            "size": {"preset": "A4", "width": 210, "height": 297, "unit": "mm"},
            "orientation": "portrait",
            "margins": {"top": 20, "right": 20, "bottom": 20, "left": 20},
            "background": {"type": "solid", "color": "#ffffff"},
            "header": None, "footer": None,
            "elements": [
                {
                    "id": "ca1", "type": "contentarea",
                    "x": 20, "y": 20, "width": 170, "height": 50,
                    "visible": True, "condition": None, "areaRef": "area1",
                    "border": {"mode": "none", "unified": {"enabled": False, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
                    "fill": {"type": "none", "color": "#fff", "opacity": 1, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                },
                {
                    "id": "shp1", "type": "shape",
                    "x": 20, "y": 80, "width": 80, "height": 40,
                    "rotation": 0, "visible": True, "condition": None, "shape": "rectangle",
                    "fill": {"type": "solid", "color": "#dbeafe", "opacity": 1, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                    "border": {"mode": "unified", "unified": {"enabled": True, "width": 1, "style": "solid", "color": "#3b82f6"}, "sides": {}, "radius": {"mode": "unified", "unified": 5}},
                },
            ],
        }],
        "contentAreas": [{
            "id": "area1", "type": "simple", "label": "A1", "height": 50,
            "content": "<b>Workflow Doc Studio</b> — PDF Engine v1.0<br>Test render OK",
            "elements": [], "children": [], "visible": True, "condition": None,
            "defaultTextStyleId": "ts_default",
        }],
    }
    return _render_to_response(template, {})


# ── Shared render helper ──────────────────────────────────────────────────────

def _render_to_response(template_json: dict, data_context: dict) -> Response:
    try:
        ctx = normalize(template_json, data_context)
        pdf_bytes = render_pdf(ctx, assets_base_path=ASSETS_BASE_PATH)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF rendering failed: {exc}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="document.pdf"'},
    )
