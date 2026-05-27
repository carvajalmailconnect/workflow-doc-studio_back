from pdf_engine.html_parser import parse_content
from pdf_engine.variable_resolver import resolve_var, resolve_paragraphs, PAGE_VARS


def test_simple_var():
    assert resolve_var("name", {"name": "Oscar"}) == "Oscar"


def test_missing_var_returns_empty():
    assert resolve_var("missing", {}) == ""


def test_nested_dot_path():
    data = {"user": {"address": {"city": "Bogotá"}}}
    assert resolve_var("user.address.city", data) == "Bogotá"


def test_array_index():
    data = {"items": ["a", "b", "c"]}
    assert resolve_var("items.1", data) == "b"


def test_special_today():
    from datetime import date
    result = resolve_var("$today", {})
    assert result == date.today().isoformat()


def test_special_now():
    result = resolve_var("$now", {})
    assert "T" in result


def test_page_vars_take_priority():
    page_vars = {"$pageNumber": 3}
    result = resolve_var("$pageNumber", {}, page_vars)
    assert result == "3"


def test_page_vars_not_resolved_without_page_vars():
    result = resolve_var("$pageNumber", {}, page_vars=None)
    assert result == ""


def test_float_without_decimals():
    assert resolve_var("price", {"price": 42.0}) == "42"


def test_float_with_decimals():
    assert resolve_var("price", {"price": 3.14}) == "3.14"


def test_bool_true():
    assert resolve_var("active", {"active": True}) == "true"


def test_bool_false():
    assert resolve_var("active", {"active": False}) == "false"


def test_resolve_paragraphs_mutates_in_place():
    html = 'Hi <span class="var-tag" data-var="name">name</span>!'
    paras = parse_content(html)
    resolve_paragraphs(paras, {"name": "Oscar"})
    var_runs = [r for p in paras for r in p.runs if r.is_var]
    assert var_runs[0].text == "Oscar"


def test_resolve_paragraphs_leaves_page_vars_unresolved():
    html = '<span class="var-tag" data-var="$pageNumber">$pageNumber</span>'
    paras = parse_content(html)
    resolve_paragraphs(paras, {}, page_vars=None)
    var_runs = [r for p in paras for r in p.runs if r.is_var]
    # $pageNumber is a PAGE_VAR — should NOT be resolved (stays empty or original)
    assert var_runs[0].var_name in PAGE_VARS
