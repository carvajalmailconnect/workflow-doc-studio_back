from pdf_engine.html_parser import parse_content, Paragraph, TextRun


def test_plain_text():
    paras = parse_content("Hello world")
    assert len(paras) == 1
    assert paras[0].runs[0].text == "Hello world"


def test_var_tag():
    paras = parse_content('<span class="var-tag" data-var="userId">userId</span>')
    runs = paras[0].runs
    var_runs = [r for r in runs if r.is_var]
    assert len(var_runs) == 1
    assert var_runs[0].var_name == "userId"


def test_area_tag():
    paras = parse_content('<span class="area-tag" data-area="area_abc">→ Area</span>')
    runs = paras[0].runs
    area_runs = [r for r in runs if r.is_area_ref]
    assert len(area_runs) == 1
    assert area_runs[0].area_id == "area_abc"


def test_bold_span():
    paras = parse_content('<span style="font-weight: bold;">Bold text</span>')
    assert paras[0].runs[0].style.bold is True


def test_italic_span():
    paras = parse_content('<span style="font-style: italic;">Italic</span>')
    assert paras[0].runs[0].style.italic is True


def test_color_rgb():
    paras = parse_content('<span style="color: rgb(36, 110, 214);">Blue</span>')
    assert paras[0].runs[0].style.color == "#246ed6"


def test_color_hex():
    paras = parse_content('<span style="color: #ff0000;">Red</span>')
    assert paras[0].runs[0].style.color == "#ff0000"


def test_superscript():
    paras = parse_content('<span style="vertical-align: super;">sup</span>')
    assert paras[0].runs[0].style.superscript is True


def test_subscript():
    paras = parse_content('<span style="vertical-align: sub;">sub</span>')
    assert paras[0].runs[0].style.subscript is True


def test_font_size_named():
    paras = parse_content('<span style="font-size: x-small;">tiny</span>')
    assert paras[0].runs[0].style.font_size_override == 8


def test_line_break():
    paras = parse_content("line1<br>line2")
    text = "".join(r.text for r in paras[0].runs)
    assert "\n" in text


def test_div_creates_paragraph():
    paras = parse_content("<div>Para 1</div><div>Para 2</div>")
    non_empty = [p for p in paras if not p.is_empty()]
    assert len(non_empty) >= 2


def test_nested_bold_and_color():
    html = '<span style="color: rgb(12, 89, 198);">use<span style="font-weight: bold;">r</span></span>'
    paras = parse_content(html)
    runs = paras[0].runs
    assert any(r.style.color == "#0c59c6" for r in runs)
    assert any(r.style.bold for r in runs)


def test_empty_content():
    paras = parse_content("")
    assert len(paras) == 1


def test_bullet_list():
    html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
    paras = parse_content(html)
    list_paras = [p for p in paras if p.list_item]
    assert len(list_paras) == 2
    assert list_paras[0].list_type == "bullet"


def test_mixed_text_and_var():
    html = 'Hello <span class="var-tag" data-var="name">name</span>!'
    paras = parse_content(html)
    runs = paras[0].runs
    texts = [r.text for r in runs if not r.is_var]
    vars_ = [r.var_name for r in runs if r.is_var]
    assert "name" in vars_
    assert any("Hello" in t for t in texts)
