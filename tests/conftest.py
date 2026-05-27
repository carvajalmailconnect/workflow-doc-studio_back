"""Shared fixtures for all tests."""
import pytest


# ── Minimal templateJson (1 page, text + shape + qr + barcode + image) ────────

@pytest.fixture
def minimal_template():
    return {
        "version": "1.0",
        "styles": {
            "text": [
                {
                    "id": "ts_default",
                    "name": "Default",
                    "fontFamily": "Inter",
                    "fontWeight": "Regular",
                    "fontSize": 12,
                    "color": "#1f2937",
                    "italic": False,
                    "underline": False,
                    "strikethrough": False,
                    "letterSpacing": 0,
                    "lineHeight": 1.4,
                    "superscript": False,
                    "subscript": False,
                    "superscriptOffset": 33,
                    "subscriptOffset": 33,
                    "superSubSize": 58,
                    "textTransform": "none",
                    "fillStyleId": None,
                    "borderStyleId": None,
                }
            ],
            "paragraph": [
                {
                    "id": "ps_default",
                    "name": "Default Paragraph Style",
                    "alignment": "left",
                    "verticalAlign": "top",
                    "lineHeight": 1.4,
                    "letterSpacing": 0,
                    "firstLineIndent": 0,
                    "leftIndent": 0,
                    "rightIndent": 0,
                    "spaceBefore": 0,
                    "spaceAfter": 0,
                    "wordWrap": True,
                    "listStyle": "none",
                    "listIndent": 5,
                    "listColor": "",
                    "defaultTextStyleId": None,
                }
            ],
            "border": [],
            "fill": [
                {
                    "id": "fs_blue",
                    "name": "BlueFill",
                    "type": "solid",
                    "color": "#246ed6",
                    "opacity": 1.0,
                    "gradient": {"type": "linear", "angle": 90, "cx": 50, "cy": 50, "stops": []},
                }
            ],
            "cell": [],
            "line": [],
        },
        "images": [],
        "fonts": [],
        "pages": [
            {
                "id": "pg_1",
                "name": "Page 1",
                "size": {"preset": "A4", "width": 210, "height": 297, "unit": "mm"},
                "orientation": "portrait",
                "margins": {"top": 20, "right": 20, "bottom": 20, "left": 20},
                "background": {"type": "solid", "color": "#ffffff"},
                "visible": True,
                "header": None,
                "footer": None,
                "elements": [
                    {
                        "id": "ca_1",
                        "type": "contentarea",
                        "x": 10, "y": 10, "width": 100, "height": 30,
                        "visible": True,
                        "locked": False,
                        "condition": None,
                        "areaRef": "area_1",
                        "border": {"mode": "none", "unified": {"enabled": False, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
                        "fill": {"type": "none", "color": "#ffffff", "opacity": 1.0, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                        "createdAt": "2026-01-01T00:00:00Z",
                        "updatedAt": "2026-01-01T00:00:00Z",
                    },
                    {
                        "id": "shp_1",
                        "type": "shape",
                        "x": 10, "y": 50, "width": 30, "height": 20,
                        "rotation": 0,
                        "visible": True,
                        "locked": False,
                        "condition": None,
                        "shape": "rectangle",
                        "fill": {"type": "solid", "color": "#e5e7eb", "opacity": 1.0, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                        "border": {"mode": "unified", "unified": {"enabled": True, "width": 1, "style": "solid", "color": "#9ca3af"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
                        "createdAt": "2026-01-01T00:00:00Z",
                        "updatedAt": "2026-01-01T00:00:00Z",
                    },
                ],
            }
        ],
        "contentAreas": [
            {
                "id": "area_1",
                "type": "simple",
                "label": "Area 1",
                "height": 30,
                "content": "Hello <span class=\"var-tag\" data-var=\"name\">name</span>!",
                "elements": [],
                "children": [],
                "visible": True,
                "condition": None,
                "defaultTextStyleId": "ts_default",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
            }
        ],
        "rowSets": [],
        "outputChannels": ["pdf"],
    }


@pytest.fixture
def minimal_data():
    return {"name": "Oscar", "userId": 42, "plan": "pro"}


# ── Workflow JSON fixture (from real frontend export) ──────────────────────────

@pytest.fixture
def workflow_with_webhook():
    return {
        "version": "1.0",
        "nodes": [
            {
                "id": "webhook-1",
                "type": "webhook-trigger",
                "position": {"x": 0, "y": 0},
                "zIndex": 1,
                "data": {
                    "config": {
                        "method": "POST",
                        "path": "/webhook",
                        "schema": {
                            "enabled": True,
                            "strict": False,
                            "fields": [
                                {"id": "f1", "name": "userId", "type": "integer", "required": True, "defaultValue": "", "enum": [], "children": []},
                                {"id": "f2", "name": "name",   "type": "string",  "required": True, "defaultValue": "World", "enum": [], "children": []},
                            ],
                        },
                    },
                    "locked": False,
                    "definitionType": "webhook-trigger",
                },
            },
            {
                "id": "designer-1",
                "type": "document-designer",
                "position": {"x": 200, "y": 0},
                "zIndex": 1,
                "data": {
                    "config": {"templateJson": None},  # filled by test
                    "locked": False,
                    "definitionType": "document-designer",
                },
            },
        ],
        "edges": [
            {
                "id": "e1",
                "source": "webhook-1",
                "target": "designer-1",
                "sourceHandle": "out",
                "targetHandle": "in",
            }
        ],
    }
