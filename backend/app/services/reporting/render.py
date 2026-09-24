"""Phase 6 Step 5 — report export rendering (HTML, JSON, PDF).

Converts the deterministic ReportGenerator / ReportStore payload into the
three documented export formats (docs/ROADMAP.md Phase 6 "Report templating
(HTML, JSON, PDF)" and "Report sanitization (prevent XSS in HTML reports)").

Guarantees:
- Deterministic: identical report data always renders identical bytes for
  every format (stable key ordering, stable section order, fixed PDF
  metadata/invariant output).
- No fabrication: sections keep their documented ordering, unavailable
  sections keep available=false plus an explicit reason, and empty findings
  keep their note; nothing is invented to fill a gap.
- Safe: every report value is HTML-escaped before it reaches the markup, so
  no report data can become executable HTML/script.
- Honest PDF: when no PDF library is installed the renderer raises
  PdfRendererUnavailableError instead of emitting a fake PDF.
"""

import io
import json
import re
from html import escape as _escape
from typing import Any, Dict, List, Optional, Tuple

from app.services.reporting.generator import (
    VALID_FORMATS,
    InvalidReportTypeError,
)

JSON_FORMAT = "json"
HTML_FORMAT = "html"
PDF_FORMAT = "pdf"

# Export formats that produce a standalone artifact file (reports.file_path).
ARTIFACT_FORMATS: Tuple[str, ...] = (HTML_FORMAT, PDF_FORMAT)

# Documented download media types (docs/API_CONTRACT.md 4.9).
MEDIA_TYPES: Dict[str, str] = {
    JSON_FORMAT: "application/json",
    HTML_FORMAT: "text/html",
    PDF_FORMAT: "application/pdf",
}

PDF_RENDERER_HINT = (
    "PDF rendering is unavailable: no supported PDF library is installed in "
    "this environment (reportlab or WeasyPrint). Install reportlab to enable "
    "PDF export; HTML and JSON export are unaffected."
)

# Control characters that must never reach rendered output.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Nesting guard for deeply nested section data.
_MAX_DEPTH = 6


class PdfRendererUnavailableError(RuntimeError):
    """Raised when the environment provides no usable PDF renderer.

    Step 5 requires the limitation to be reported explicitly rather than
    returning fabricated PDF bytes.
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or PDF_RENDERER_HINT)


# ----------------------------------------------------------------------
# Deterministic serialization (single implementation shared with
# ReportStore so persisted content and JSON export can never diverge).
# ----------------------------------------------------------------------


def serialize_report(report: Dict[str, Any]) -> str:
    """Serialize report data to deterministic JSON text."""
    return json.dumps(report, sort_keys=True, separators=(",", ":"), default=str)


def deserialize_report(content: str) -> Dict[str, Any]:
    """Parse stored report JSON, rejecting non-object payloads."""
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Stored report content is not a JSON object")
    return data


# ----------------------------------------------------------------------
# Text helpers
# ----------------------------------------------------------------------


def scalar_text(value: Any) -> str:
    """Canonical single-line rendering of any report value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return str(value)


def clean_text(value: Any) -> str:
    """Strip control characters from a value while keeping it readable."""
    text = scalar_text(value)
    text = _CONTROL_CHARS.sub("", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def escape_value(value: Any) -> str:
    """Escape any report value for safe inclusion in HTML text/attributes."""
    return _escape(clean_text(value), quote=True)


def _pdf_text(value: Any) -> str:
    """Prepare a value for the PDF canvas (Latin-1 safe, single line)."""
    text = clean_text(value)
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    return text.encode("latin-1", "replace").decode("latin-1")


def _report_subtitle(report: Dict[str, Any]) -> str:
    case_number = report.get("case_number")
    title = report.get("title")
    parts = [str(v) for v in (case_number, title) if v]
    if not parts:
        parts.append(str(report.get("case_id") or "unidentified case"))
    return " - ".join(parts)


def _report_meta(report: Dict[str, Any]) -> List[Tuple[str, Any]]:
    unavailable = report.get("unavailable_sections") or []
    return [
        ("Case number", report.get("case_number")),
        ("Case ID", report.get("case_id")),
        ("Case title", report.get("title")),
        ("Report type", report.get("report_type")),
        ("Format", report.get("format")),
        ("Generated at", report.get("generated_at")),
        ("Generated by", report.get("generated_by")),
        (
            "Unavailable sections",
            ", ".join(unavailable) if unavailable else "none",
        ),
    ]


# ----------------------------------------------------------------------
# JSON export
# ----------------------------------------------------------------------


def render_json(report: Dict[str, Any]) -> str:
    """Deterministic structured JSON using the ReportStore contract."""
    return serialize_report(report)


# ----------------------------------------------------------------------
# HTML export
# ----------------------------------------------------------------------

_STYLE = """
* { box-sizing: border-box; }
body { margin: 0; padding: 2rem 1.25rem; background: #f4f6f9; color: #12151c;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 14px;
  line-height: 1.55; }
.report-header, .report-body, .report-footer { max-width: 62rem; margin: 0 auto; }
.report-header { background: #ffffff; border: 1px solid #d7dce5;
  border-radius: 6px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; }
.report-header h1 { margin: 0 0 .75rem; font-size: 1.5rem; letter-spacing: .01em; }
.report-meta { display: grid; grid-template-columns: max-content 1fr;
  gap: .25rem 1rem; margin: 0; }
.report-meta dt { font-weight: 700; color: #4a5262; }
.report-meta dd { margin: 0; word-break: break-word; }
.report-body { display: flex; flex-direction: column; gap: 1rem; }
.section { background: #ffffff; border: 1px solid #d7dce5; border-left: 4px solid #3b6ea5;
  border-radius: 4px; padding: 1rem 1.25rem; }
.section.unavailable { border-left-color: #a53b3b; }
.section h2 { margin: 0 0 .5rem; font-size: 1.1rem; }
.availability { display: inline-block; margin: 0 0 .6rem; padding: .1rem .5rem;
  border-radius: 999px; font-size: .75rem; font-weight: 700; text-transform: uppercase; }
.availability.available { background: #e4f2e7; color: #1c5c2c; }
.availability.unavailable { background: #f8e4e4; color: #7c2020; }
.reason { margin: 0 0 .5rem; color: #7c2020; }
.note { margin: .75rem 0 0; color: #4a5262; font-style: italic; }
.empty, .null { color: #6b7280; }
.section-body dl.data { margin: 0; display: grid; grid-template-columns: minmax(8rem, max-content) 1fr;
  gap: .2rem .9rem; }
.section-body dt { font-weight: 700; color: #4a5262; }
.section-body dd { margin: 0; word-break: break-word; }
.section-body dd dl.data { margin-top: .35rem; }
ul.data-list { margin: .25rem 0; padding-left: 1.25rem; }
.table-wrap { overflow-x: auto; margin: .35rem 0; }
table { border-collapse: collapse; width: 100%; font-size: .875rem; }
th, td { border: 1px solid #d7dce5; padding: .35rem .5rem; text-align: left;
  vertical-align: top; word-break: break-word; }
th { background: #eef1f6; font-weight: 700; }
code { font-family: "SFMono-Regular", Consolas, Menlo, monospace; font-size: .8125rem;
  background: #f0f2f6; padding: 0 .2rem; border-radius: 3px; }
.report-footer { margin-top: 1.5rem; color: #4a5262; font-size: .8125rem; }
"""


def render_html(report: Dict[str, Any]) -> str:
    """Render report data into a sanitized, non-executable HTML document."""
    sections = report.get("sections") or []
    parts: List[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<meta http-equiv=\"Content-Security-Policy\" "
        "content=\"default-src 'none'; style-src 'unsafe-inline'; "
        "img-src 'none'; script-src 'none'; object-src 'none'; "
        "base-uri 'none'; form-action 'none'\">",
        '<meta name="referrer" content="no-referrer">',
        '<meta name="generator" content="LedgerLens report renderer">',
        f"<title>{escape_value(_report_subtitle(report))}</title>",
        f"<style>{_STYLE}</style>",
        "</head>",
        "<body>",
        '<header class="report-header">',
        "<h1>LedgerLens Investigation Report</h1>",
        '<dl class="report-meta">',
    ]
    for label, value in _report_meta(report):
        parts.append(f"<dt>{escape_value(label)}</dt><dd>{escape_value(value)}</dd>")
    parts.extend(
        [
            "</dl>",
            "</header>",
            '<main class="report-body">',
        ]
    )
    for index, section in enumerate(sections, start=1):
        parts.append(_render_section(section, index))
    parts.extend(
        [
            "</main>",
            '<footer class="report-footer">',
            "<p>Rendered from persisted report data by LedgerLens. "
            f"Generated at {escape_value(report.get('generated_at'))}. "
            "All findings require human investigator verification.</p>",
            "</footer>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(parts) + "\n"


def _render_section(section: Dict[str, Any], index: int) -> str:
    key = escape_value(section.get("key") or "")
    title = escape_value(section.get("title") or section.get("key") or "")
    available = bool(section.get("available"))
    state = "available" if available else "unavailable"
    lines = [f'<section id="{key}" class="section {state}">']
    lines.append(f'<h2>{index}. {title}</h2>')
    if available:
        lines.append('<p class="availability available">Available</p>')
        data = section.get("data")
        if data is None:
            lines.append(
                '<p class="empty">No structured data recorded for this section.</p>'
            )
        else:
            lines.append(f'<div class="section-body">{_render_node(data, 0)}</div>')
    else:
        lines.append('<p class="availability unavailable">Unavailable</p>')
        lines.append(
            f'<p class="reason">Unavailable: {escape_value(section.get("reason"))}</p>'
        )
    if section.get("note"):
        lines.append(f'<p class="note">Note: {escape_value(section.get("note"))}</p>')
    lines.append("</section>")
    return "\n".join(lines)


def _render_code(value: Any) -> str:
    return f"<code>{escape_value(scalar_text(value))}</code>"


def _render_node(value: Any, depth: int) -> str:
    if isinstance(value, dict):
        if depth >= _MAX_DEPTH:
            return _render_code(value)
        if not value:
            return '<p class="empty">None recorded.</p>'
        parts = ['<dl class="data">']
        for item_key, item_value in value.items():
            parts.append(f"<dt>{escape_value(item_key)}</dt>")
            parts.append(f"<dd>{_render_node(item_value, depth + 1)}</dd>")
        parts.append("</dl>")
        return "".join(parts)
    if isinstance(value, list):
        if depth >= _MAX_DEPTH:
            return _render_code(value)
        if not value:
            return '<p class="empty">None recorded.</p>'
        if all(isinstance(item, dict) for item in value):
            return _render_table(value, depth)
        items = "".join(
            f"<li>{_render_node(item, depth + 1)}</li>" for item in value
        )
        return f'<ul class="data-list">{items}</ul>'
    if value is None:
        return '<span class="null">null</span>'
    return f"<span>{escape_value(value)}</span>"


def _render_cell(value: Any, depth: int) -> str:
    if isinstance(value, (dict, list)):
        return _render_code(value)
    if value is None:
        return '<span class="null">null</span>'
    return f"<span>{escape_value(value)}</span>"


def _render_table(rows: List[Dict[str, Any]], depth: int) -> str:
    headers: List[str] = []
    seen = set()
    for row in rows:
        for column in row:
            if column not in seen:
                seen.add(column)
                headers.append(column)
    head = "".join(f"<th>{escape_value(column)}</th>" for column in headers)
    body = []
    for row in rows:
        cells = "".join(
            f"<td>{_render_cell(row.get(column), depth + 1)}</td>"
            for column in headers
        )
        body.append(f"<tr>{cells}</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        f"{head}"
        "</tr></thead><tbody>"
        f"{''.join(body)}"
        "</tbody></table></div>"
    )


# ----------------------------------------------------------------------
# PDF export
# ----------------------------------------------------------------------

_PDF_FONT_BODY = "Helvetica"
_PDF_FONT_BOLD = "Helvetica-Bold"
_PDF_FONT_ITALIC = "Helvetica-Oblique"

_PDF_BODY_SIZE = 9.5
_PDF_BODY_LEADING = 13.0


def _import_reportlab():
    """Import the project PDF renderer (docs/ROADMAP.md "WeasyPrint or similar").

    Raises ImportError when no PDF library is installed; render_pdf converts
    that into PdfRendererUnavailableError so the limitation is explicit.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfgen import canvas as pdf_canvas

    return A4, simpleSplit, pdf_canvas


def render_pdf(report: Dict[str, Any]) -> bytes:
    """Render report data to a deterministic PDF document.

    Uses reportlab ("or similar" per docs/ROADMAP.md 780). Output is byte
    stable for identical input (invariant canvas, uncompressed content,
    fixed metadata).
    """
    try:
        pagesize, simple_split, pdf_canvas = _import_reportlab()
    except ImportError as exc:
        raise PdfRendererUnavailableError(PDF_RENDERER_HINT) from exc
    page_width, page_height = pagesize
    left = 46.0
    right_margin = 46.0
    top = page_height - 54.0
    bottom = 54.0
    max_width = page_width - left - right_margin

    flow = _pdf_flow(report)

    buffer = io.BytesIO()
    canvas = pdf_canvas.Canvas(
        buffer, pagesize=pagesize, invariant=1, pageCompression=0
    )
    canvas.setTitle("LedgerLens Investigation Report")
    canvas.setAuthor("LedgerLens")
    canvas.setCreator("LedgerLens report renderer")
    canvas.setSubject(scalar_text(report.get("report_type")))

    y = top
    for text, font, size, leading, space_before in flow:
        y -= space_before
        for line in _split_pdf_line(text, font, size, max_width, simple_split):
            if y - leading < bottom:
                _pdf_footer(canvas, left, page_height)
                canvas.showPage()
                y = top
            y -= leading
            canvas.setFont(font, size)
            canvas.drawString(left, y, line)
    _pdf_footer(canvas, left, page_height)
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def _pdf_footer(canvas: Any, left: float, page_height: float) -> None:
    canvas.setFont(_PDF_FONT_BODY, 8)
    canvas.drawString(
        left,
        30.0,
        f"LedgerLens - page {canvas.getPageNumber()} - investigative intelligence, "
        "requires human verification",
    )


def _split_pdf_line(
    text: str, font: str, size: float, max_width: float, simple_split
) -> List[str]:
    prepared = _pdf_text(text)
    if not prepared:
        return [""]
    lines: List[str] = []
    for raw_line in prepared.split("\n"):
        lines.extend(simple_split(raw_line, font, size, max_width))
    return lines or [""]


def _pdf_flow(report: Dict[str, Any]) -> List[Tuple[str, str, float, float, float]]:
    """Build the ordered (text, font, size, leading, space_before) flow."""
    flow: List[Tuple[str, str, float, float, float]] = []

    def add(
        text: str,
        font: str = _PDF_FONT_BODY,
        size: float = _PDF_BODY_SIZE,
        leading: float = _PDF_BODY_LEADING,
        space_before: float = 0.0,
    ) -> None:
        flow.append((text, font, size, leading, space_before))

    add("LedgerLens Investigation Report", _PDF_FONT_BOLD, 17.0, 22.0)
    add(_report_subtitle(report), _PDF_FONT_BOLD, 11.0, 15.0, space_before=4.0)
    for index, (label, value) in enumerate(_report_meta(report)):
        add(f"{label}: {scalar_text(value)}", space_before=8.0 if index == 0 else 0.0)

    for position, section in enumerate(report.get("sections") or [], start=1):
        title = section.get("title") or section.get("key") or ""
        add(f"{position}. {title}", _PDF_FONT_BOLD, 12.5, 16.0, space_before=14.0)
        if section.get("available"):
            add("Status: available", _PDF_FONT_ITALIC, 9.0, 12.0, space_before=2.0)
            data = section.get("data")
            if data is None:
                add(
                    "No structured data recorded for this section.",
                    _PDF_FONT_ITALIC,
                    9.0,
                    12.0,
                    space_before=2.0,
                )
            else:
                _pdf_node(data, 0, add)
        else:
            add("Status: unavailable", _PDF_FONT_ITALIC, 9.0, 12.0, space_before=2.0)
            add(f"Reason: {scalar_text(section.get('reason'))}")
        if section.get("note"):
            add(f"Note: {scalar_text(section.get('note'))}", _PDF_FONT_ITALIC)
    return flow


def _pdf_node(value: Any, indent: int, add) -> None:
    pad = "  " * indent
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if isinstance(item_value, (dict, list)):
                add(f"{pad}{item_key}:", _PDF_FONT_BOLD)
                _pdf_node(item_value, indent + 1, add)
            else:
                add(f"{pad}{item_key}: {scalar_text(item_value)}")
        return
    if isinstance(value, list):
        if not value:
            add(f"{pad}(none)", _PDF_FONT_ITALIC)
            return
        for position, item in enumerate(value, start=1):
            if isinstance(item, (dict, list)):
                add(f"{pad}{position}.", _PDF_FONT_BOLD)
                _pdf_node(item, indent + 1, add)
            else:
                add(f"{pad}{position}. {scalar_text(item)}")
        return
    add(f"{pad}{scalar_text(value)}")


# ----------------------------------------------------------------------
# Dispatch
# ----------------------------------------------------------------------


def render_report(report: Dict[str, Any], report_format: str) -> bytes:
    """Render report data to bytes in the requested documented format."""
    if report_format not in VALID_FORMATS:
        raise InvalidReportTypeError(
            f"Invalid report format {report_format!r}; "
            f"expected one of {', '.join(VALID_FORMATS)}"
        )
    if report_format == JSON_FORMAT:
        return render_json(report).encode("utf-8")
    if report_format == HTML_FORMAT:
        return render_html(report).encode("utf-8")
    return render_pdf(report)
