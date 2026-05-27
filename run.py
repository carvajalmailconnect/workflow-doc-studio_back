"""
run.py — CLI para pruebas locales

Uso:
  python run.py render  --template workflow.json --data data.json --out doc.pdf
  python run.py server  [--host 0.0.0.0] [--port 8080]
  python run.py test-render              (genera PDF desde fixture mínimo)
"""
from __future__ import annotations
import argparse
import json
import os
import sys


def cmd_render(args):
    with open(args.template, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Acepta workflow completo o templateJson directo
    if "nodes" in raw:
        from workflow.executor import execute
        data = {}
        if args.data:
            with open(args.data, "r", encoding="utf-8") as f:
                data = json.load(f)
        template_json, data_context = execute(raw, data)
    else:
        template_json = raw.get("templateJson", raw)
        data_context = {}
        if args.data:
            with open(args.data, "r", encoding="utf-8") as f:
                data_context = json.load(f)

    from pdf_engine.normalize import normalize
    from pdf_engine.page_renderer import render_pdf

    ctx = normalize(template_json, data_context)
    pdf = render_pdf(
        ctx,
        assets_base_path=args.assets or "",
        fonts_base_path=args.fonts or "",
    )

    out_path = args.out or "output.pdf"
    with open(out_path, "wb") as f:
        f.write(pdf)
    print(f"PDF generado: {out_path} ({len(pdf):,} bytes)")


def cmd_server(args):
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def cmd_test_render(_args):
    """Genera un PDF de prueba sin necesidad de archivos externos."""
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
                {
                    "id": "shp2", "type": "shape",
                    "x": 120, "y": 80, "width": 60, "height": 40,
                    "rotation": 0, "visible": True, "condition": None, "shape": "ellipse",
                    "fill": {"type": "solid", "color": "#dcfce7", "opacity": 1, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                    "border": {"mode": "none", "unified": {"enabled": False, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
                },
            ],
        }],
        "contentAreas": [{
            "id": "area1", "type": "simple", "label": "A1", "height": 50,
            "content": '<b>Workflow Doc Studio</b> — PDF Engine v1.0<br>Generado: <span class="var-tag" data-var="$today">$today</span>',
            "elements": [], "children": [], "visible": True, "condition": None,
            "defaultTextStyleId": "ts_default",
        }],
    }

    from pdf_engine.normalize import normalize
    from pdf_engine.page_renderer import render_pdf

    ctx = normalize(template, {})
    pdf = render_pdf(ctx)

    out_path = "test_output.pdf"
    with open(out_path, "wb") as f:
        f.write(pdf)
    print(f"Test PDF generado: {out_path} ({len(pdf):,} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Workflow Doc Studio — PDF Engine CLI")
    sub = parser.add_subparsers(dest="command")

    p_render = sub.add_parser("render", help="Genera PDF desde un workflow o templateJson")
    p_render.add_argument("--template", required=True, help="Path al JSON del workflow o templateJson")
    p_render.add_argument("--data",     help="Path al JSON de datos (trigger payload)")
    p_render.add_argument("--out",      help="Path de salida del PDF (default: output.pdf)")
    p_render.add_argument("--assets",   help="Directorio base para assets de imágenes")
    p_render.add_argument("--fonts",    help="Directorio base para fuentes custom")

    p_server = sub.add_parser("server", help="Inicia el servidor FastAPI")
    p_server.add_argument("--host",   default="0.0.0.0")
    p_server.add_argument("--port",   default=8080, type=int)
    p_server.add_argument("--reload", action="store_true")

    sub.add_parser("test-render", help="Genera un PDF de prueba (no requiere archivos)")

    args = parser.parse_args()

    if args.command == "render":
        cmd_render(args)
    elif args.command == "server":
        cmd_server(args)
    elif args.command == "test-render":
        cmd_test_render(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
