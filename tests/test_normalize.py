from pdf_engine.normalize import normalize, DocumentContext


def test_returns_document_context(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    assert isinstance(ctx, DocumentContext)


def test_strips_ui_fields(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    page = ctx.pages[0]
    assert "createdAt" not in page
    assert "updatedAt" not in page
    assert "locked" not in page
    assert "zIndex" not in page


def test_strips_ui_fields_from_elements(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    el = ctx.pages[0]["elements"][0]
    assert "createdAt" not in el
    assert "updatedAt" not in el
    assert "locked" not in el


def test_collapses_none_border(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    ca_element = ctx.pages[0]["elements"][0]
    assert ca_element["border"] is None


def test_keeps_enabled_border(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    shape_element = ctx.pages[0]["elements"][1]
    assert shape_element["border"] is not None


def test_collapses_none_fill(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    ca_element = ctx.pages[0]["elements"][0]
    assert ca_element["fill"] is None


def test_area_index_built(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    assert "area_1" in ctx.area_index


def test_area_index_nested(minimal_data):
    template = {
        "version": "1.0",
        "styles": {"text": [], "paragraph": [], "border": [], "fill": [], "cell": [], "line": []},
        "images": [], "fonts": [], "pages": [], "rowSets": [], "outputChannels": ["pdf"],
        "contentAreas": [
            {
                "id": "root",
                "type": "simple", "label": "Root", "height": 30, "content": "",
                "elements": [], "visible": True, "condition": None,
                "children": [
                    {
                        "id": "child_1",
                        "type": "simple", "label": "Child", "height": 30, "content": "",
                        "elements": [], "visible": True, "condition": None,
                        "children": [
                            {"id": "grandchild", "type": "simple", "label": "GC",
                             "height": 30, "content": "", "elements": [], "visible": True,
                             "condition": None, "children": []}
                        ],
                    }
                ],
            }
        ],
    }
    ctx = normalize(template, minimal_data)
    assert "root" in ctx.area_index
    assert "child_1" in ctx.area_index
    assert "grandchild" in ctx.area_index


def test_data_context_attached(minimal_template, minimal_data):
    ctx = normalize(minimal_template, minimal_data)
    assert ctx.get_var("name") == "Oscar"
    assert ctx.get_var("userId") == 42
    assert ctx.get_var("missing", "default") == "default"


def test_does_not_mutate_original(minimal_template, minimal_data):
    import copy
    original = copy.deepcopy(minimal_template)
    normalize(minimal_template, minimal_data)
    assert minimal_template["pages"][0]["elements"][0].get("createdAt") == \
           original["pages"][0]["elements"][0].get("createdAt")
