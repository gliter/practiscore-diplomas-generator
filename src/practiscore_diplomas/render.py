"""Render diploma-data YAML records into a single DOCX document."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Mapping

import yaml
from docx import Document
from docx.document import Document as DocumentObject
from docx.opc.exceptions import PackageNotFoundError
from docx.table import _Cell
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_BREAK


class DiplomaRenderError(ValueError):
    """Raised when diploma data or a DOCX template cannot be rendered."""


_PLACEHOLDER = re.compile(r"{{\s*([^{}]+?)\s*}}")
_TOP_LEVEL_FIELDS = {
    "first_line",
    "second_line",
    "third_line",
    "fourth_line",
    "place",
    "division",
    "category",
    "class",
    "metric_value",
}


def _load_records(path: Path) -> list[Mapping[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as exc:
        raise DiplomaRenderError(f"Could not read diploma data {path}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("diplomas"), dict):
        raise DiplomaRenderError("Diploma data must contain a 'diplomas' mapping")
    records: list[Mapping[str, Any]] = []
    for series, values in raw["diplomas"].items():
        if not isinstance(values, list):
            raise DiplomaRenderError(f"diplomas.{series} must be a list")
        for index, record in enumerate(values):
            if not isinstance(record, dict):
                raise DiplomaRenderError(f"diplomas.{series}[{index}] must be a mapping")
            records.append(record)
    if not records:
        raise DiplomaRenderError("Diploma data contains no diploma records")
    return records


def _resolve(record: Mapping[str, Any], path: str, record_index: int) -> Any:
    parts = path.split(".")
    if parts[0] == "shooter":
        if len(parts) != 2 or not isinstance(record.get("shooter"), dict):
            raise DiplomaRenderError(f"Record {record_index}: invalid placeholder '{{{{ {path} }}}}'")
        value = record["shooter"].get(parts[1])
    elif len(parts) == 1 and parts[0] in _TOP_LEVEL_FIELDS:
        value = record.get(parts[0])
        if parts[0] in {"third_line", "fourth_line"} and parts[0] not in record:
            return ""
    else:
        raise DiplomaRenderError(f"Record {record_index}: unknown placeholder '{{{{ {path} }}}}'")
    if value is None:
        raise DiplomaRenderError(f"Record {record_index}: placeholder '{{{{ {path} }}}}' has no value")
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return value


def _render_text(text: str, record: Mapping[str, Any], record_index: int) -> str:
    if text.count("{{") != text.count("}}"):
        raise DiplomaRenderError(f"Record {record_index}: malformed placeholder syntax")

    def replace(match: re.Match[str]) -> str:
        path = match.group(1).strip()
        value = _resolve(record, path, record_index)
        return str(value)

    return _PLACEHOLDER.sub(replace, text)


def _replace_paragraph(paragraph: Paragraph, record: Mapping[str, Any], record_index: int) -> None:
    runs = list(paragraph.runs)
    if not runs:
        return
    combined = "".join(run.text or "" for run in runs)
    if "{{" not in combined and "}}" not in combined:
        return
    rendered = _render_text(combined, record, record_index)
    runs[0].text = rendered
    for run in runs[1:]:
        run.text = ""


def _replace_cell(cell: _Cell, record: Mapping[str, Any], record_index: int) -> None:
    for paragraph in cell.paragraphs:
        _replace_paragraph(paragraph, record, record_index)
    for table in cell.tables:
        for row in table.rows:
            for nested_cell in row.cells:
                _replace_cell(nested_cell, record, record_index)


def _render_document_page(document: DocumentObject, record: Mapping[str, Any], record_index: int) -> None:
    for paragraph in document.paragraphs:
        _replace_paragraph(paragraph, record, record_index)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                _replace_cell(cell, record, record_index)


def _body_blocks(document: DocumentObject) -> list[Any]:
    body = document._body._element
    return [deepcopy(child) for child in body if child.tag.endswith("}p") or child.tag.endswith("}tbl")]


def _insert_before_section_properties(body: Any, block: Any) -> None:
    section_properties = body.sectPr
    if section_properties is None:
        body.append(block)
    else:
        body.insert(body.index(section_properties), block)


def render_diplomas(diplomas_path: str | Path, template_path: str | Path, output_path: str | Path) -> None:
    """Render all diploma records into one DOCX file."""
    records = _load_records(Path(diplomas_path))
    template = Path(template_path)
    if not template.is_file():
        raise DiplomaRenderError(f"Template does not exist: {template}")
    output = Path(output_path)
    try:
        result = Document(template)
    except (OSError, ValueError, KeyError, PackageNotFoundError) as exc:
        raise DiplomaRenderError(f"Could not open DOCX template {template}: {exc}") from exc

    _render_document_page(result, records[0], 0)
    for record_index, record in enumerate(records[1:], start=1):
        page = Document(template)
        _render_document_page(page, record, record_index)
        break_paragraph = result.add_paragraph()
        break_paragraph.add_run().add_break(WD_BREAK.PAGE)
        body = result._body._element
        for block in _body_blocks(page):
            _insert_before_section_properties(body, block)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result.save(output)
    except OSError as exc:
        raise DiplomaRenderError(f"Could not write rendered DOCX {output}: {exc}") from exc
