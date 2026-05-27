# Codebase Map — workflow-doc-studio_back

> **Purpose:** Quick-reference navigator. Drop this file into a new Claude session to skip re-reading the codebase.  
> **Last updated:** 2026-05-27  
> **Branch:** `claude/jolly-gauss-jTYKY`

---

## 1. Pipeline Overview (3 Stages)

```
POST /generate          POST /render
      │                       │
      ▼                       │
workflow/executor.py           │   ← only for /generate
  execute() → (templateJson, data)
      │                       │
      └──────────┬────────────┘
                 ▼
   pdf_engine/normalize.py
     normalize() → DocumentContext
                 │
                 ▼
   pdf_engine/page_renderer.py
     render_pdf() → bytes (PDF)
```

### Entry points

| Endpoint | File | Handler |
|---|---|---|
| `POST /generate` | `api/main.py:51` | `generate()` |
| `POST /render` | `api/main.py:85` | `render()` |
| `GET /health` | `api/main.py:94` | `health()` |
| `GET /test-render` | `api/main.py:99` | `test_render()` |
| CLI render | `run.py:16` | `cmd_render()` |
| CLI server | `run.py:51` | `cmd_server()` |

Shared render helper: `api/main.py:160` → `_render_to_response(template_json, data_context)`

---

## 2. Stage 1 — Workflow Executor (`workflow/executor.py`)

Only called for `/generate`. Runs a topological sort on the DAG, executes nodes in order.

| Function | Line | What it does |
|---|---|---|
| `execute(workflow_json, trigger_data)` | 29 | Main entry: topo-sort + execute; returns `(templateJson, data)` |
| `_apply_webhook_defaults(config, data)` | 88 | Injects default values from `webhook-trigger` node |
| `_apply_processor(config, data)` | 103 | Field mappings + transforms from `data-processor` node |
| `_apply_transform(value, transform)` | 133 | Supports: `uppercase`, `lowercase`, `capitalize`, `trim` |
| `_topological_sort(nodes, adjacency)` | 157 | Kahn's algorithm; raises on cycles |
| `_build_adjacency(edges)` | 147 | Builds `{node_id: [successor_ids]}` from edge list |
| `_get_nested(data, path)` | 182 | Dot-path accessor: `"user.address.city"` |

**Node types:** `webhook-trigger`, `data-processor`, `document-designer`, `data-viewer`  
**Error class:** `WorkflowExecutionError` at line 25

---

## 3. Stage 2 — Normalization (`pdf_engine/normalize.py`)

Strips UI fields, builds lookup indexes, collapses inline border/fill.

| Function / Class | Line | What it does |
|---|---|---|
| `normalize(template_json, data_context)` | 28 | Main entry; returns `DocumentContext` |
| `_process_element(el)` | 70 | Strips UI fields, calls collapse helpers |
| `_collapse_border(el)` | 77 | Converts `el.border` shorthand → structured dict or `None` |
| `_collapse_fill(el)` | 91 | Converts `el.fill` shorthand → structured dict or `None` |
| `_build_asset_index(images)` | 109 | `{asset.id: asset_dict}` from `template.images[]` |
| `_build_area_index(areas)` | 114 | `{area.id: area_dict}` — recursive over nested areas |
| `class DocumentContext` | 139 | Holds template, indexes, data |
| `DocumentContext.get_area(area_id)` | 166 | Lookup by id from area_index |
| `DocumentContext.get_asset(asset_id)` | 169 | Lookup by id from asset_index |
| `DocumentContext.get_var(name, default)` | 172 | Raw data access |

**UI fields stripped:** `createdAt`, `updatedAt`, `zIndex`, `locked`, `pagePreview`, `__typename`  
**Important:** `dict.get("key", default)` does NOT protect against explicit JSON `null`. Use `dict.get("key") or default` for strings, `safe_float(dict.get("key"), default)` for numbers.

---

## 4. Stage 3 — PDF Rendering (`pdf_engine/page_renderer.py`)

| Function | Line | What it does |
|---|---|---|
| `render_pdf(ctx, assets_base_path, fonts_base_path)` | 26 | Creates canvas, iterates pages/elements, dispatches to renderers |
| `_draw_background(canvas, page, w_pt, h_pt, registry)` | 84 | Page background fill |
| `_render_elements(canvas, page, h_pt, ctx, registry, fm, page_vars, assets_base_path)` | 100 | Dispatches each element by `type` |
| `_check_condition(element, ctx)` | 140 | Evaluates `element.condition` — skips element if false |
| `_load_fonts(fm, template, fonts_base_path)` | 165 | Loads custom + bundled + system fonts |

**Element type → renderer dispatch** (inside `_render_elements`):

| `element.type` | Renderer function | File |
|---|---|---|
| `contentarea` | `render_contentarea()` | `renderers/contentarea_renderer.py:33` |
| `table` | `render_table()` | `renderers/table_renderer.py:31` |
| `image` | `render_image()` | `renderers/image_renderer.py:12` |
| `text` | `render_text()` | `renderers/text_renderer.py:34` |
| `shape` | `render_shape()` | `renderers/shape_renderer.py:11` |
| `qr` | `render_qr()` | `renderers/qr_renderer.py:11` |
| `barcode` | `render_barcode()` | `renderers/barcode_renderer.py:20` |

---

## 5. Coordinate System (`pdf_engine/coordinate.py`)

**Rule:** JSON uses mm + Y-down. ReportLab uses pt + Y-up. Never do raw conversion — always use these helpers.

| Function | Line | Formula |
|---|---|---|
| `safe_float(value, default)` | 15 | Handles `None`, `bool`, CSS units (`px`/`pt`/`em`), CSS keywords (`"normal"`) |
| `mm(value)` | 36 | `value × 2.8346` (mm → pt) |
| `element_rect(x_mm, y_mm, w_mm, h_mm, page_h_pt)` | 54 | Returns `(x, y, w, h)` in pt; flips Y: `y = page_h_pt - mm(y_mm) - mm(h_mm)` |
| `apply_margin(...)` | 75 | Returns usable content rect after page margins |

---

## 6. Style Registry (`pdf_engine/style_registry.py`)

Resolves named styles from `templateJson.styles` into typed Python objects.

| Class / Method | Line | What it does |
|---|---|---|
| `class ResolvedTextStyle` | 27 | Holds font, size, color, bold, italic, line height, etc. |
| `class ResolvedParagraphStyle` | 50 | Holds alignment, padding, spacing, list config |
| `class ResolvedFillStyle` | 68 | Holds fill type, color, opacity |
| `class ResolvedBorderStyle` | 77 | Holds line color/width/style, radius, margins, per-side config |
| `StyleRegistry.from_context(ctx, font_manager)` | 104 | Factory — builds registry from DocumentContext |
| `StyleRegistry.text(style_id)` | 195 | Returns `ResolvedTextStyle`; falls back to built-in default |
| `StyleRegistry.paragraph(style_id)` | 200 | Returns `ResolvedParagraphStyle` |
| `StyleRegistry.fill(style_id)` | 205 | Returns `ResolvedFillStyle` or `None` |
| `StyleRegistry.border(style_id)` | 210 | Returns `ResolvedBorderStyle` or `None` |
| `StyleRegistry.rl_color(hex_color, opacity)` | 217 | Converts `#rrggbb` → ReportLab `Color` |
| `StyleRegistry.font_name(ts)` | 235 | Resolves font name from `ResolvedTextStyle` via FontManager |

**Loading methods (called by `from_context`):** `_load_text:121`, `_load_paragraph:146`, `_load_fill:165`, `_load_border:175`

---

## 7. Font Manager (`pdf_engine/font_manager.py`)

| Method | Line | What it does |
|---|---|---|
| `FontManager.__init__()` | 120 | Initialises with ReportLab built-ins |
| `FontManager.load_from_template(template_json, fonts_base_path)` | 144 | Loads fonts declared in `templateJson.fonts[]` |
| `FontManager.load_directory(directory, families)` | 137 | Scans a directory for TTF/OTF files |
| `FontManager.resolve(family, bold, italic)` | 226 | Returns registered font name; falls back to Helvetica |
| `FontManager.resolve_from_style(ts)` | 247 | Shorthand that reads bold/italic from `ResolvedTextStyle` |
| `_parse_font_filename(fname)` | 67 | Extracts `(family, bold, italic)` from filename keywords |

**Bundled fonts dir:** `fonts/`  
**Fallback chain:** declared fonts → bundled fonts → system fonts → ReportLab built-ins

---

## 8. HTML Parser (`pdf_engine/html_parser.py`)

Parses rich-text HTML from `contentArea.content` into structured objects.

| Type / Function | Line | What it does |
|---|---|---|
| `class InlineStyle` | 33 | bold, italic, underline, color, font_size_override, super/subscript |
| `class TextRun` | 63 | Piece of text + style; may be `is_var`, `is_area_ref`, `is_element_ref` |
| `class Paragraph` | 77 | List of TextRuns + list_item/list_depth/list_type |
| `_parse_css(style_attr)` | 106 | Converts inline `style="..."` → `InlineStyle` |
| `parse_content(html)` | 313 | Public API: HTML string → `list[Paragraph]` |

**Special span classes:** `var-tag` (→ `TextRun.is_var`), `area-tag` (→ `is_area_ref`), `element-tag` (→ `is_element_ref`)

---

## 9. Variable & Area Resolvers

### `pdf_engine/variable_resolver.py`

| Function | Line | What it does |
|---|---|---|
| `resolve_var(name, data, page_vars)` | 39 | Resolves `${varName}` — dot paths, array index, special vars |
| `resolve_paragraphs(paragraphs, data, page_vars)` | 62 | Mutates `TextRun.text` in place for all `is_var` runs |
| `_get_nested(data, path)` | 81 | Dot-path accessor: `"user.address.city"`, `"items[0].name"` |

**Special variables (resolved at render time):** `$pageNumber`, `$pageCount`, `$today`, `$now`

### `pdf_engine/area_resolver.py`

| Function | Line | What it does |
|---|---|---|
| `resolve_area(area_id, ctx)` | 98 | Follows `trueAreaId`/`falseAreaId` chains; returns effective area |
| `get_effective_content(area_id, ctx)` | 122 | Returns final HTML content string after condition branching |
| `evaluate_condition(area, ctx)` | 42 | Evaluates `selectionVariable` or `selectionScript` |
| `_eval_script(script, data)` | 68 | Safe `eval()` of simple boolean script in data context |

**Conditional areas use:** `flowType: "inline-condition"` + `selectionVariable` or `selectionScript`

---

## 10. Renderer Details

### `contentarea_renderer.py`

Most complex renderer — handles rich HTML text, inline areas, embedded tables, variable substitution.

| Function | Line | What it does |
|---|---|---|
| `render_contentarea(canvas, element, page_h_pt, ctx, registry, page_vars)` | 33 | Main entry; creates Frame + builds story |
| `_build_story(area, default_ts, ctx, registry, page_vars, available_width, extra_area_lookup)` | 75 | Resolves area chain, parses HTML, converts to ReportLab flowables |
| `_para_to_flowables(para, ...)` | 110 | One `Paragraph` → one or more ReportLab flowables |
| `_expand_area_inline(area_id, ...)` | 169 | Recursively renders inline sub-area references |
| `_build_embedded_table_flowable(element, ...)` | 237 | Renders `element-tag` table references as inline flowables |
| `_runs_to_rl_xml(runs, default_ts, registry)` | 346 | Converts `TextRun` list → ReportLab XML string (`<b>`, `<font color>`, etc.) |
| `_make_rl_style(ts, registry, para)` | 391 | `ResolvedTextStyle` → `RLParagraphStyle` |
| `_make_list_item(xml_text, base_style, para)` | 414 | Bullet/numbered list item flowable |

### `text_renderer.py`

Fixed-position plain text box (no HTML). Uses `textStyle` + `paragraphStyle` inline on element.

| Function | Line | What it does |
|---|---|---|
| `render_text(canvas, element, page_h_pt, registry)` | 34 | Background fill → border → text |

**Bold fix (2026-05):** inline `textStyle.bold` / `fontWeight` / `fontFamily` are now resolved via `registry._fm.resolve()` to get correct font name (e.g. `Helvetica-Bold`).

### `shape_renderer.py`

| Function | Line | What it does |
|---|---|---|
| `render_shape(canvas, element, page_h_pt, registry)` | 11 | Dispatches to fill + border + shape draw |
| `_draw_rectangle(canvas, x, y, w, h, border, stroke)` | 31 | Checks `border.radius.mode` before rounding; `stroke=0` when no border |
| `_draw_ellipse(canvas, x, y, w, h, stroke)` | 45 | Passes `stroke=1 if stroke else 0` |
| `_draw_triangle(canvas, x, y, w, h, stroke)` | 49 | Upward-pointing; uses `drawPath` |
| `_apply_fill(canvas, fill, registry)` | 58 | Sets fill color; transparent if type=`none` |
| `_apply_border(canvas, border, registry) → bool` | 70 | Configures stroke state; returns `True` if visible stroke |

**Hairline fix (2026-05):** `_apply_border` now returns `bool`; draw functions use `stroke=0` to prevent hairline artifacts when there's no border.

### `border_renderer.py`

Shared utility used by `text_renderer` and `contentarea_renderer` (not `shape_renderer`).

| Function | Line | What it does |
|---|---|---|
| `draw_border(canvas, x, y, w, h, border, registry, radius)` | 19 | Main entry for external use |
| `_draw_named_border(...)` | 70 | Handles `border.styleRef` lookup |
| `_draw_sides(...)` | 110 | Draws per-side from inline `border.sides` config |
| `_resolve_radius(border, default)` | 174 | Returns radius in pt; returns `default` if `mode` is `"none"`, `"standard"`, or `"disabled"` |

### `image_renderer.py`

| Function | Line | What it does |
|---|---|---|
| `render_image(canvas, element, page_h_pt, ctx, registry, assets_base_path)` | 12 | Resolves asset, draws image or placeholder |
| `_draw_placeholder(canvas, x, y, w, h)` | 74 | Grey box with `[ Image ]` label |

**Asset resolution order (2026-05 fix):**
- ID: `source.assetId` → `source.id` → `source.imageId` → `source.asset_id`
- URL: `asset.source.url` → `asset.source.path` → `asset.url` → `asset.path` → `asset.src`

**Image `fit` modes:** `contain` (preserves aspect), `cover` (stretches), other (raw placement)

### `table_renderer.py`

| Function | Line | What it does |
|---|---|---|
| `render_table(canvas, element, page_h_pt, ctx, registry)` | 31 | Header + body + footer; uses ReportLab `Table` |
| `_build_header_rows(header_cfg, columns, registry)` | 108 | Static header rows |
| `_build_body_rows(body_cfg, data_source, columns, ctx, registry)` | 121 | Iterates data rows; resolves variables |
| `_build_footer_rows(footer_cfg, columns, registry)` | 156 | Static footer rows |
| `_resolve_col_widths(columns, total_w_pt)` | 184 | `widthRatio` or `width`; falls back to equal distribution |
| `_border_style_cmds(table_border, cell_border, n_rows, n_cols)` | 229 | ReportLab `TableStyle` commands for borders |

### `qr_renderer.py` / `barcode_renderer.py`

| Function | Line | What it does |
|---|---|---|
| `render_qr(canvas, element, page_h_pt, ctx)` | `qr:11` | Renders QR code from `element.content` or resolved variable |
| `render_barcode(canvas, element, page_h_pt, ctx)` | `barcode:20` | Symbology map at line 11; renders via `python-barcode` |

---

## 11. Pydantic Models (`models/template.py`)

Key classes for understanding the JSON schema:

| Class | Line | Describes |
|---|---|---|
| `TemplateJson` | 350 | Root: `pages[]`, `styles`, `images[]`, `fonts[]`, `contentAreas[]` |
| `Page` | 335 | `size`, `margins`, `background`, `elements[]` |
| `ContentArea` | 291 | `id`, `content` (HTML), `flowType`, `selectionVariable`, `trueAreaId`, `falseAreaId` |
| `BaseElement` | 185 | Common: `id`, `type`, `x`, `y`, `width`, `height`, `condition`, `border`, `fill` |
| `InlineBorder` | 167 | `mode` ("none"/"unified"/"sides"), `unified` (color/width/enabled), `radius`, `sides` |
| `InlineBorderRadius` | 158 | `mode` ("unified"/"none"/"standard"), `unified` (number, mm) |
| `Styles` | 115 | `textStyles[]`, `paragraphStyles[]`, `fillStyles[]`, `borderStyles[]` |
| `BorderStyle` | 93 | Named border: `lineColor`, `lineWidth`, `radius_x`, `margin_*`, `sides` |

---

## 12. Tests (`tests/`)

| File | Line count | Coverage area |
|---|---|---|
| `conftest.py` | — | `minimal_template`, `minimal_data`, `workflow_with_webhook` fixtures |
| `test_normalize.py` | 10 tests | `normalize()`, `DocumentContext`, collapse helpers |
| `test_html_parser.py` | 16 tests | `parse_content()`, CSS parsing, list handling |
| `test_style_registry.py` | 12 tests | Style lookup, color conversion, font resolution |
| `test_variable_resolver.py` | 14 tests | Dot paths, array index, special vars, page vars |
| `test_workflow_executor.py` | 5 tests | Node execution, topological sort, transforms |
| `test_integration.py` | 6 tests | Full render to PDF bytes; validates `output[:4] == b"%PDF"` |

**Run all:** `pytest tests/`  
**Run single:** `pytest tests/test_integration.py::test_render_shape_elements`

---

## 13. Known Gotchas & Applied Fixes

| Symptom | Root cause | Fix location |
|---|---|---|
| `AttributeError: 'NoneType'.get` on border | `dict.get("border", {})` doesn't protect against `"border": null` | Use `dict.get("border") or {}` everywhere |
| `ValueError: could not convert 'normal' to float` | CSS keyword strings in numeric fields | `safe_float()` in `coordinate.py:15` |
| `TypeError: str + int` in ReportLab XML | `ts.color` was `None` → became literal `"None"` string in XML | Always chain `or "#000000"` on color values |
| Bold text not appearing in `text` elements | Font resolved from TextStyle only; element-level `textStyle` override ignored | `text_renderer.py:76-91` — resolves inline bold/fontFamily via `registry._fm.resolve()` |
| Border radius applied when corners = "standard" | `border.radius.unified` value read without checking `border.radius.mode` | `border_renderer.py:174`, `shape_renderer.py:31` — check `mode` before applying value |
| Shapes show hairline border when no border set | `stroke=1` with `lineWidth=0` produces hairline in PDF viewers | `shape_renderer.py:70` — `_apply_border` returns `bool`; draw functions use `stroke=0` |
| Images not rendering | Only `source.assetId` and `asset.source.url` tried | `image_renderer.py:34-39` — multiple fallback keys tried |

---

## 14. Environment & Config

| Variable | Default | Purpose |
|---|---|---|
| `ASSETS_BASE_PATH` | `""` | Prepended to image asset paths |

**Fonts directory:** `fonts/` at project root (drop `.ttf`/`.otf` files here)  
**Start server:** `python run.py server --host 0.0.0.0 --port 8080 --reload`  
**Swagger UI:** `http://localhost:8080/docs`
