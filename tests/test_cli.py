import json
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
    assert "render -i MATCH.pcs -c configs" in output


def test_polish_help_contains_diacritics(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "--language", "pl", "--help"])
    with pytest.raises(SystemExit):
        main()

    output = capsys.readouterr().out
    assert "dyplomów" in output
    assert "Język" in output
    assert "Przykłady:" in output
