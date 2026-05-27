from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ── Styles ──────────────────────────────────────────────────────────────────

class TextStyle(BaseModel):
    id: str
    name: str = ""
    fontFamily: str = "Helvetica"
    fontWeight: str = "Regular"
    fontSize: float = 12
    color: str = "#000000"
    italic: bool = False
    smallCaps: bool = False
    letterSpacing: float = 0
    lineHeight: float = 1.4
    textTransform: str = "none"
    underline: bool = False
    strikethrough: bool = False
    superscript: bool = False
    subscript: bool = False
    superscriptOffset: float = 33
    subscriptOffset: float = 33
    superSubSize: float = 58
    fillStyleId: Optional[str] = None
    borderStyleId: Optional[str] = None


class Hyphenation(BaseModel):
    enabled: bool = False
    minLeft: int = 2
    minRight: int = 2
    maxConsecutive: int = 2


class ParagraphStyle(BaseModel):
    id: str
    name: str = ""
    alignment: Literal["left", "center", "right", "justify"] = "left"
    verticalAlign: Literal["top", "middle", "bottom"] = "top"
    lineHeight: float = 1.4
    firstLineIndent: float = 0
    leftIndent: float = 0
    rightIndent: float = 0
    spaceBefore: float = 0
    spaceAfter: float = 0
    wordWrap: bool = True
    listStyle: Literal["none", "bullet", "numbered"] = "none"
    listIndent: float = 5
    listColor: str = ""
    defaultTextStyleId: Optional[str] = None
    hyphenation: Optional[Hyphenation] = None


class GradientStop(BaseModel):
    color: str
    offset: float
    opacity: float = 1.0


class Gradient(BaseModel):
    type: Literal["linear", "radial"] = "linear"
    angle: float = 0
    cx: float = 50
    cy: float = 50
    stops: list[GradientStop] = Field(default_factory=list)


class FillStyle(BaseModel):
    id: str
    name: str = ""
    type: Literal["solid", "gradient", "none"] = "solid"
    color: str = "#ffffff"
    opacity: float = 1.0
    gradient: Optional[Gradient] = None


class BorderSide(BaseModel):
    enabled: bool = True
    lineWidth: Optional[float] = None
    lineStyle: Optional[str] = None
    lineColor: Optional[str] = None


class BorderCorner(BaseModel):
    corner: Optional[str] = None
    radiusX: Optional[float] = None
    radiusY: Optional[float] = None


class BorderStyle(BaseModel):
    id: str
    name: str = ""
    lineWidth: float = 1.0
    lineCap: str = "Butt"
    lineStyle: str = "Solid"
    lineColor: str = "#000000"
    sides: dict[str, BorderSide] = Field(default_factory=dict)
    corner: str = "Standard"
    radiusX: float = 0
    radiusY: float = 0
    corners: dict[str, BorderCorner] = Field(default_factory=dict)
    join: str = "Miter"
    miter: float = 10
    fillFillStyleId: Optional[str] = None
    lineFillStyleId: Optional[str] = None
    marginLeft: float = 0
    marginRight: float = 0
    marginTop: float = 0
    marginBottom: float = 0


class Styles(BaseModel):
    text: list[TextStyle] = Field(default_factory=list)
    paragraph: list[ParagraphStyle] = Field(default_factory=list)
    border: list[BorderStyle] = Field(default_factory=list)
    fill: list[FillStyle] = Field(default_factory=list)
    cell: list[Any] = Field(default_factory=list)
    line: list[Any] = Field(default_factory=list)


# ── Images / Assets ──────────────────────────────────────────────────────────

class ImageSource(BaseModel):
    kind: Literal["localFile", "url", "variable", "placeholder"]
    url: Optional[str] = None
    filename: Optional[str] = None
    saved: bool = False


class ImageProperties(BaseModel):
    useImageDpi: bool = False
    dpiX: int = 96
    dpiY: int = 96
    maintainAspectRatio: bool = True
    useAlphaChannel: bool = True


class ImageAsset(BaseModel):
    id: str
    name: str = ""
    assetKind: str = "static"
    source: ImageSource
    properties: ImageProperties = Field(default_factory=ImageProperties)


# ── Element borders & fills (inline on elements) ──────────────────────────────

class InlineBorderSide(BaseModel):
    enabled: bool = False
    width: float = 1
    style: str = "solid"
    color: str = "#d1d5db"


class InlineBorderRadius(BaseModel):
    mode: str = "unified"
    unified: float = 0
    topLeft: float = 0
    topRight: float = 0
    bottomRight: float = 0
    bottomLeft: float = 0


class InlineBorder(BaseModel):
    mode: Literal["none", "unified", "sides"] = "none"
    unified: InlineBorderSide = Field(default_factory=InlineBorderSide)
    sides: dict[str, InlineBorderSide] = Field(default_factory=dict)
    radius: InlineBorderRadius = Field(default_factory=InlineBorderRadius)
    styleRef: Optional[str] = None


class InlineFill(BaseModel):
    type: Literal["none", "solid", "gradient"] = "none"
    color: str = "#ffffff"
    opacity: float = 1.0
    gradient: Optional[Gradient] = None
    imageId: Optional[str] = None


# ── Elements ─────────────────────────────────────────────────────────────────

class BaseElement(BaseModel):
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    visible: bool = True
    condition: Optional[str] = None
    border: Optional[InlineBorder] = None
    fill: Optional[InlineFill] = None


class ContentAreaElement(BaseElement):
    type: Literal["contentarea"] = "contentarea"
    areaRef: str
    previousAreaRef: Optional[str] = None
    nextAreaRef: Optional[str] = None
    flowToNextPage: bool = False
    dynamicHeight: bool = False


class ImageElementSource(BaseModel):
    kind: Literal["asset", "placeholder", "variable", "url"]
    assetId: Optional[str] = None
    url: Optional[str] = None


class ImageElement(BaseElement):
    type: Literal["image"] = "image"
    rotation: float = 0
    source: ImageElementSource
    fit: Literal["contain", "cover", "fill", "none"] = "contain"


class ShapeElement(BaseElement):
    type: Literal["shape"] = "shape"
    rotation: float = 0
    shape: Literal["rectangle", "ellipse", "triangle"]
    lineStyle: Optional[Any] = None


class TextElement(BaseElement):
    type: Literal["text"] = "text"
    rotation: float = 0
    content: str = ""
    overflow: str = "clip"
    textStyleId: Optional[str] = None
    paragraphStyle: Optional[dict] = None


class TableColumn(BaseModel):
    id: str
    label: str = ""
    width: float = 20
    widthUnit: str = "mm"
    align: str = "left"


class TableHeader(BaseModel):
    enabled: bool = True
    rows: list[Any] = Field(default_factory=list)


class TableBody(BaseModel):
    rows: list[Any] = Field(default_factory=list)


class TableFooter(BaseModel):
    enabled: bool = False
    rows: list[Any] = Field(default_factory=list)


class TableElement(BaseElement):
    type: Literal["table"] = "table"
    dataSource: Optional[str] = None
    columns: list[TableColumn] = Field(default_factory=list)
    header: TableHeader = Field(default_factory=TableHeader)
    body: TableBody = Field(default_factory=TableBody)
    footer: TableFooter = Field(default_factory=TableFooter)
    overflow: str = "paginate"


class QrElement(BaseElement):
    type: Literal["qr"] = "qr"
    rotation: float = 0
    value: str = ""
    valueSource: str = "static"
    errorCorrection: str = "M"
    foreground: str = "#000000"
    background: str = "#ffffff"


class BarcodeElement(BaseElement):
    type: Literal["barcode"] = "barcode"
    rotation: float = 0
    value: str = ""
    valueSource: str = "static"
    symbology: str = "CODE128"
    showText: bool = True
    foreground: str = "#000000"
    background: str = "#ffffff"


# ── Content Areas ─────────────────────────────────────────────────────────────

class ContentArea(BaseModel):
    id: str
    type: str = "simple"
    label: str = ""
    height: float = 30
    content: str = ""
    elements: list[Any] = Field(default_factory=list)
    children: list[ContentArea] = Field(default_factory=list)
    visible: bool = True
    condition: Optional[str] = None
    defaultTextStyleId: Optional[str] = None
    inlineStyleRefs: list[str] = Field(default_factory=list)
    flowType: Optional[str] = None
    selectionType: Optional[str] = None
    selectionScript: Optional[str] = None
    defaultAreaId: Optional[str] = None
    trueAreaId: Optional[str] = None
    falseAreaId: Optional[str] = None
    conditions: list[Any] = Field(default_factory=list)

ContentArea.model_rebuild()


# ── Pages ─────────────────────────────────────────────────────────────────────

class PageSize(BaseModel):
    preset: str = "A4"
    width: float = 210
    height: float = 297
    unit: str = "mm"


class PageMargins(BaseModel):
    top: float = 20
    right: float = 20
    bottom: float = 20
    left: float = 20


class PageBackground(BaseModel):
    type: str = "solid"
    color: str = "#ffffff"


class Page(BaseModel):
    id: str
    name: str = ""
    size: PageSize = Field(default_factory=PageSize)
    orientation: Literal["portrait", "landscape"] = "portrait"
    margins: PageMargins = Field(default_factory=PageMargins)
    background: PageBackground = Field(default_factory=PageBackground)
    visible: bool = True
    header: Optional[Any] = None
    footer: Optional[Any] = None
    elements: list[Any] = Field(default_factory=list)


# ── Template root ─────────────────────────────────────────────────────────────

class TemplateJson(BaseModel):
    version: str = "1.0"
    styles: Styles = Field(default_factory=Styles)
    images: list[ImageAsset] = Field(default_factory=list)
    pages: list[Page] = Field(default_factory=list)
    contentAreas: list[ContentArea] = Field(default_factory=list)
    rowSets: list[Any] = Field(default_factory=list)
    outputChannels: list[str] = Field(default_factory=lambda: ["pdf"])
