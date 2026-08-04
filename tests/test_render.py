from pathlib import Path
import sys
import zipfile

import yaml
from docx import Document

from practiscore_diplomas.render import DiplomaRenderError, render_diplomas
from practiscore_diplomas.cli import main


def write_template(path: Path) -> None:
    document = Document()
    paragraph = document.add_paragraph()
    paragraph.add_run("{{ first_")
    paragraph.add_run("line }} / {{ shooter.last_name }}")
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "{{ place }} {{ shooter.raw_time }} {{ third_line }} {{ fourth_line }}"
    document.save(path)


def write_data(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "diplomas": {
                    "first_series": [
                        {
                            "place": 1,
                            "first_line": "FIRST",
                            "second_line": "Alpha",
                            "shooter": {"last_name": "One", "raw_time": 12.5},
                        },
                        {
                            "place": 2,
                            "first_line": "SECOND",
                            "second_line": "Beta",
                            "third_line": "EXTRA",
                            "shooter": {"last_name": "Two", "raw_time": 15},
                        },
                    ],
                    "second_series": [
                        {
                            "place": 1,
                            "first_line": "THIRD",
                            "second_line": "Gamma",
                            "shooter": {"last_name": "Three", "raw_time": 18},
                        }
                    ],
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_render_creates_one_page_per_diploma_and_preserves_order(tmp_path: Path):
    template = tmp_path / "template.docx"
    data = tmp_path / "diplomas.yaml"
    output = tmp_path / "result.docx"
    write_template(template)
    write_data(data)

    render_diplomas(data, template, output)

    document = Document(output)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "FIRST / One" in text
    assert "SECOND / Two" in text
    assert "THIRD / Three" in text
    assert text.index("FIRST") < text.index("SECOND") < text.index("THIRD")
    table_text = "\n".join(cell.text for table in document.tables for row in table.rows for cell in row.cells)
    assert "1 12.5  " in table_text
    assert "2 15 EXTRA " in table_text
    assert "1 18  " in table_text

    with zipfile.ZipFile(output) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    assert document_xml.count('w:type="page"') == 2

    rendered_paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    assert rendered_paragraphs == ["FIRST / One", "SECOND / Two", "THIRD / Three"]


def test_render_rejects_unknown_placeholder(tmp_path: Path):
    template = tmp_path / "template.docx"
    data = tmp_path / "diplomas.yaml"
    output = tmp_path / "result.docx"
    document = Document()
    document.add_paragraph("{{ missing_field }}")
    document.save(template)
    write_data(data)

    try:
        render_diplomas(data, template, output)
    except DiplomaRenderError as exc:
        assert "unknown placeholder" in str(exc)
    else:
        raise AssertionError("render_diplomas should reject unknown placeholders")


def test_render_cli_uses_diplomas_data_default(tmp_path: Path, monkeypatch):
    template = tmp_path / "template.docx"
    data = tmp_path / "diplomas-data.yaml"
    output = tmp_path / "diplomas.docx"
    write_template(template)
    write_data(data)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "render", "--template", str(template), "-o", str(output)])

    assert main() == 0
    assert output.is_file()
