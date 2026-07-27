import json
import sys
from pathlib import Path

import yaml

from practiscore_diplomas.cli import DEFAULT_DIPLOMAS_OUTPUT, DEFAULT_SUMMARY_OUTPUT, main
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
""",
        encoding="utf-8",
    )


def test_cli_uses_default_output_names(tmp_path: Path, monkeypatch):
    input_dir = tmp_path / "match"
    write_export(input_dir)
    write_config(tmp_path / "config.yaml")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "parse", str(input_dir)])

    assert main() == 0
    assert (tmp_path / DEFAULT_SUMMARY_OUTPUT).is_file()
    output = tmp_path / DEFAULT_DIPLOMAS_OUTPUT
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
    monkeypatch.setattr(sys, "argv", ["practiscore-diplomas", "parse", str(input_dir), "--config", str(config), "--summary-output", str(summary), "--diplomas-output", str(diplomas)])

    assert main() == 0
    assert summary.is_file()
    assert diplomas.is_file()
