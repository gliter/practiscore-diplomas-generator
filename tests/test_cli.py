import json
import builtins
import sys
from pathlib import Path

import pytest
import yaml

from practiscore_diplomas import cli
from practiscore_diplomas.cli import main
from tests.test_parser import make_data


def write_export(directory: Path) -> None:
    data = make_data()
    directory.mkdir()
    (directory / "match_def.json").write_text(json.dumps(data.definition), encoding="utf-8")
    (directory / "match_scores.json").write_text(json.dumps(data.scores), encoding="utf-8")


def write_config(path: Path) -> None:
    path.write_text(
        """series:
  best_shooter:
    type: best_shooter
    group_by: []
    min_competitors: [1]
    text:
      first_line: "{{ type }}"
      second_line: "{{ place }}"
""",
        encoding="utf-8",
    )


def test_cli_uses_default_output_names(tmp_path: Path, monkeypatch):
    input_dir = tmp_path / "match"
    write_export(input_dir)
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    write_config(config)
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "parse", "-i", str(input_dir), "-c", str(config)])

    assert main() == 0
    assert (tmp_path / "shooters-summary-Synthetic-Match.yaml").is_file()
    output = tmp_path / "diplomas-data-Synthetic-Match.yaml"
    assert output.is_file()
    assert set(yaml.safe_load(output.read_text(encoding="utf-8"))["diplomas"]) == {"best_shooter"}
    assert "&id" not in output.read_text(encoding="utf-8")


def test_cli_allows_output_override(tmp_path: Path, monkeypatch):
    input_dir = tmp_path / "match"
    write_export(input_dir)
    config = tmp_path / "custom-config.yaml"
    write_config(config)
    summary = tmp_path / "custom-summary.yaml"
    diplomas = tmp_path / "custom-diplomas.yaml"
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "parse", "-i", str(input_dir), "-c", str(config), "-s", str(summary), "-d", str(diplomas)])

    assert main() == 0
    assert summary.is_file()
    assert diplomas.is_file()


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["practiscore-diplomas", "--language", "en", "--help"], "Parse PractiScore exports"),
        (["practiscore-diplomas", "parse", "--help", "--language", "pl"], "Utwórz podsumowanie strzelców"),
    ],
)
def test_cli_help_supports_explicit_language(argv, expected, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert expected in capsys.readouterr().out


def test_cli_uses_polish_system_locale(monkeypatch):
    monkeypatch.setattr(cli.locale, "getlocale", lambda: ("Polish_Poland", "1250"))
    assert cli._language_from_argv([]) == "pl"


def test_cli_requires_config(tmp_path: Path, monkeypatch, capsys):
    input_dir = tmp_path / "match"
    write_export(input_dir)
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "parse", str(input_dir)])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2
    assert "--config" in capsys.readouterr().err


def test_cli_without_arguments_shows_complete_help(monkeypatch, capsys):
    monkeypatch.setattr(cli.locale, "getlocale", lambda: ("en_US", "UTF-8"))
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas"])

    assert main() == 0
    output = capsys.readouterr().out
    assert "parse -i PATH" in output
    assert "--config PATH" in output
    assert "--template PATH" in output
    assert "Examples:" in output
    assert "render -d diplomas-data-MATCH.yaml" in output
    assert "render -i MATCH.psc -c configs" in output


def test_polish_help_contains_diacritics(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "--language", "pl", "--help"])
    with pytest.raises(SystemExit):
        main()

    output = capsys.readouterr().out
    assert "dyplomów" in output
    assert "Język" in output
    assert "Przykłady:" in output


def test_interactive_arguments_for_rendering_pcs(tmp_path: Path, monkeypatch):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "gpa.yaml").write_text("series: {}", encoding="utf-8")
    (tmp_path / "match.psc").write_bytes(b"")
    (tmp_path / "template.odt").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    selections = iter([0, 0, 0, 0])
    monkeypatch.setattr(cli, "_select_option", lambda prompt, options: next(selections))
    monkeypatch.setattr(cli, "_system_save_dialog", lambda prompt, suggested: None)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")

    assert cli._interactive_arguments("en") == [
        "--language", "en", "render", "-i", "match.psc", "-c", "configs\\gpa.yaml",
        "-t", "template.odt", "--output-odt", "diplomas-match.odt",
    ]


def test_interactive_arguments_for_rendering_yaml_skips_config(tmp_path: Path, monkeypatch):
    (tmp_path / "diplomas-data.yaml").write_text("diplomas: {}", encoding="utf-8")
    (tmp_path / "template.docx").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    selections = iter([1, 0, 0])
    monkeypatch.setattr(cli, "_select_option", lambda prompt, options: next(selections))
    monkeypatch.setattr(cli, "_system_save_dialog", lambda prompt, suggested: Path("custom.docx"))

    assert cli._interactive_arguments("en") == [
        "--language", "en", "render", "-d", "diplomas-data.yaml",
        "-t", "template.docx", "--output-docx", "custom.docx",
    ]


def test_interactive_file_dialog_cancel_returns_to_list(tmp_path: Path, monkeypatch):
    (tmp_path / "match.psc").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    selections = iter([1, 0])
    monkeypatch.setattr(cli, "_select_option", lambda prompt, options: next(selections))
    monkeypatch.setattr(cli, "_system_file_dialog", lambda prompt, directory, patterns: None)

    assert cli._interactive_path("Choose", Path("."), ("*.psc",), cli._MESSAGES["en"]) == Path("match.psc")
