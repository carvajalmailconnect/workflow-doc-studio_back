"""
Integration tests: full pipeline normalize → render_pdf → valid PDF bytes.
"""
import pytest
from pdf_engine.normalize import normalize
from pdf_engine.page_renderer import render_pdf


def _is_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF"


def test_render_minimal_template(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    pdf = render_pdf(ctx)
    assert _is_pdf(pdf)
    assert len(pdf) > 1000


def test_render_with_variable_in_contentarea(minimal_data):
    template = {
        "version": "1.0",
        "styles": {
            "text": [{"id": "ts_default", "name": "D", "fontFamily": "Helvetica",
                      "fontWeight": "Regular", "fontSize": 12, "color": "#000",
                      "italic": False, "underline": False, "strikethrough": False,
                      "letterSpacing": 0, "lineHeight": 1.4, "superscript": False,
                      "subscript": False, "superscriptOffset": 33, "subscriptOffset": 33,
                      "superSubSize": 58, "textTransform": "none",
                      "fillStyleId": None, "borderStyleId": None}],
            "paragraph": [{"id": "ps_default", "name": "D", "alignment": "left",
                           "verticalAlign": "top", "lineHeight": 1.4, "letterSpacing": 0,
                           "firstLineIndent": 0, "leftIndent": 0, "rightIndent": 0,
                           "spaceBefore": 0, "spaceAfter": 0, "wordWrap": True,
                           "listStyle": "none", "listIndent": 5, "listColor": "",
                           "defaultTextStyleId": None}],
            "border": [], "fill": [], "cell": [], "line": [],
        },
        "images": [], "fonts": [], "rowSets": [], "outputChannels": ["pdf"],
        "pages": [{
            "id": "pg1", "name": "P1", "visible": True,
            "size": {"preset": "A4", "width": 210, "height": 297, "unit": "mm"},
            "orientation": "portrait",
            "margins": {"top": 20, "right": 20, "bottom": 20, "left": 20},
            "background": {"type": "solid", "color": "#ffffff"},
            "header": None, "footer": None,
            "elements": [{
                "id": "ca1", "type": "contentarea",
                "x": 10, "y": 10, "width": 150, "height": 40,
                "visible": True, "condition": None, "areaRef": "area1",
                "border": {"mode": "none", "unified": {"enabled": False, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
                "fill": {"type": "none", "color": "#fff", "opacity": 1, "gradient": {"type": "linear", "angle": 0, "stops": []}},
            }],
        }],
        "contentAreas": [{
            "id": "area1", "type": "simple", "label": "A1", "height": 40,
            "content": 'Hello <span class="var-tag" data-var="name">name</span>, plan: <span class="var-tag" data-var="plan">plan</span>',
            "elements": [], "children": [], "visible": True, "condition": None,
            "defaultTextStyleId": "ts_default",
        }],
    }
    ctx = normalize(template, {"name": "Oscar", "plan": "pro"})
    pdf = render_pdf(ctx)
    assert _is_pdf(pdf)


def test_render_shape_elements():
    template = {
        "version": "1.0",
        "styles": {"text": [], "paragraph": [], "border": [], "fill": [], "cell": [], "line": []},
        "images": [], "fonts": [], "rowSets": [], "outputChannels": ["pdf"],
        "pages": [{
            "id": "pg1", "name": "P1", "visible": True,
            "size": {"preset": "A4", "width": 210, "height": 297, "unit": "mm"},
            "orientation": "portrait",
            "margins": {"top": 0, "right": 0, "bottom": 0, "left": 0},
            "background": {"type": "solid", "color": "#ffffff"},
            "header": None, "footer": None,
            "elements": [
                {"id": "s1", "type": "shape", "x": 10, "y": 10, "width": 50, "height": 30,
                 "rotation": 0, "visible": True, "condition": None, "shape": "rectangle",
                 "fill": {"type": "solid", "color": "#e5e7eb", "opacity": 1, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                 "border": {"mode": "unified", "unified": {"enabled": True, "width": 1, "style": "solid", "color": "#9ca3af"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}}},
                {"id": "s2", "type": "shape", "x": 70, "y": 10, "width": 40, "height": 40,
                 "rotation": 0, "visible": True, "condition": None, "shape": "ellipse",
                 "fill": {"type": "solid", "color": "#dbeafe", "opacity": 1, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                 "border": {"mode": "none", "unified": {"enabled": False, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}}},
                {"id": "s3", "type": "shape", "x": 120, "y": 10, "width": 30, "height": 30,
                 "rotation": 0, "visible": True, "condition": None, "shape": "triangle",
                 "fill": {"type": "solid", "color": "#fef3c7", "opacity": 1, "gradient": {"type": "linear", "angle": 0, "stops": []}},
                 "border": {"mode": "none", "unified": {"enabled": False, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}}},
            ],
        }],
        "contentAreas": [],
    }
    ctx = normalize(template, {})
    pdf = render_pdf(ctx)
    assert _is_pdf(pdf)


def test_render_table_with_datasource():
    template = {
        "version": "1.0",
        "styles": {
            "text": [{"id": "ts_default", "name": "D", "fontFamily": "Helvetica",
                      "fontWeight": "Regular", "fontSize": 10, "color": "#000",
                      "italic": False, "underline": False, "strikethrough": False,
                      "letterSpacing": 0, "lineHeight": 1.4, "superscript": False,
                      "subscript": False, "superscriptOffset": 33, "subscriptOffset": 33,
                      "superSubSize": 58, "textTransform": "none",
                      "fillStyleId": None, "borderStyleId": None}],
            "paragraph": [{"id": "ps_default", "name": "D", "alignment": "left",
                           "verticalAlign": "top", "lineHeight": 1.4, "letterSpacing": 0,
                           "firstLineIndent": 0, "leftIndent": 0, "rightIndent": 0,
                           "spaceBefore": 0, "spaceAfter": 0, "wordWrap": True,
                           "listStyle": "none", "listIndent": 5, "listColor": "",
                           "defaultTextStyleId": None}],
            "border": [], "fill": [], "cell": [], "line": [],
        },
        "images": [], "fonts": [], "rowSets": [], "outputChannels": ["pdf"],
        "pages": [{
            "id": "pg1", "name": "P1", "visible": True,
            "size": {"preset": "A4", "width": 210, "height": 297, "unit": "mm"},
            "orientation": "portrait",
            "margins": {"top": 10, "right": 10, "bottom": 10, "left": 10},
            "background": {"type": "solid", "color": "#ffffff"},
            "header": None, "footer": None,
            "elements": [{
                "id": "tbl1", "type": "table",
                "x": 10, "y": 10, "width": 170, "height": 80,
                "visible": True, "condition": None,
                "dataSource": "products",
                "columns": [
                    {"id": "c1", "label": "name",  "width": 80, "widthUnit": "mm", "align": "left"},
                    {"id": "c2", "label": "price", "width": 40, "widthUnit": "mm", "align": "right"},
                    {"id": "c3", "label": "qty",   "width": 50, "widthUnit": "mm", "align": "center"},
                ],
                "header": {"enabled": True, "rows": []},
                "body": {"rows": []},
                "footer": {"enabled": False, "rows": []},
                "tableBorder": {"mode": "unified", "unified": {"enabled": True, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
                "cellBorder":  {"mode": "unified", "unified": {"enabled": True, "width": 0.5, "style": "solid", "color": "#e5e7eb"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
                "alternateRowFill": {"type": "solid", "color": "#f9fafb", "opacity": 1},
                "overflow": "paginate",
                "border": {"mode": "none", "unified": {"enabled": False, "width": 1, "style": "solid", "color": "#d1d5db"}, "sides": {}, "radius": {"mode": "unified", "unified": 0}},
            }],
        }],
        "contentAreas": [],
    }
    data = {
        "products": [
            {"name": "Widget A", "price": "10.00", "qty": "5"},
            {"name": "Widget B", "price": "25.50", "qty": "2"},
            {"name": "Widget C", "price": "7.99",  "qty": "10"},
        ]
    }
    ctx = normalize(template, data)
    pdf = render_pdf(ctx)
    assert _is_pdf(pdf)


def test_render_multipage():
    page = {
        "id": "pg{}", "name": "Page {}", "visible": True,
        "size": {"preset": "A4", "width": 210, "height": 297, "unit": "mm"},
        "orientation": "portrait",
        "margins": {"top": 20, "right": 20, "bottom": 20, "left": 20},
        "background": {"type": "solid", "color": "#ffffff"},
        "header": None, "footer": None, "elements": [],
    }
    import copy
    pages = [copy.deepcopy(page) for _ in range(3)]
    for i, p in enumerate(pages):
        p["id"] = f"pg{i}"
        p["name"] = f"Page {i+1}"

    template = {
        "version": "1.0",
        "styles": {"text": [], "paragraph": [], "border": [], "fill": [], "cell": [], "line": []},
        "images": [], "fonts": [], "rowSets": [], "outputChannels": ["pdf"],
        "pages": pages,
        "contentAreas": [],
    }
    ctx = normalize(template, {})
    pdf = render_pdf(ctx)
    assert _is_pdf(pdf)
    # Multi-page PDFs are larger
    assert len(pdf) > 2000


def test_workflow_execute_to_pdf(minimal_template, minimal_data):
    from workflow.executor import execute
    workflow = {
        "version": "1.0",
        "nodes": [
            {
                "id": "wh-1", "type": "webhook-trigger",
                "position": {"x": 0, "y": 0}, "zIndex": 1,
                "data": {"config": {"schema": {"enabled": False, "fields": []}},
                         "locked": False, "definitionType": "webhook-trigger"},
            },
            {
                "id": "designer-1", "type": "document-designer",
                "position": {"x": 200, "y": 0}, "zIndex": 1,
                "data": {"config": {"templateJson": minimal_template},
                         "locked": False, "definitionType": "document-designer"},
            },
        ],
        "edges": [{"id": "e1", "source": "wh-1", "target": "designer-1",
                   "sourceHandle": "out", "targetHandle": "in"}],
    }
    template_json, data_context = execute(workflow, minimal_data)
    ctx = normalize(template_json, data_context)
    pdf = render_pdf(ctx)
    assert _is_pdf(pdf)
