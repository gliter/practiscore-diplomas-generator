from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .diplomas import DiplomaDataError, generate_diplomas, load_config
from .parser import MatchParseError, load_match_data, parse_match_data
from .render import DiplomaRenderError, render_diplomas

DEFAULT_CONFIG = Path("config.yaml")
DEFAULT_SUMMARY_OUTPUT = Path("shooters-summary.yaml")
DEFAULT_DIPLOMAS_OUTPUT = Path("diplomas-data.yaml")


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(value, stream, allow_unicode=True, sort_keys=False)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse PractiScore exports and generate diploma data.")
    commands = parser.add_subparsers(dest="command", required=True)
    parse = commands.add_parser("parse", help="Create the shooter summary and diploma data files")
    parse.add_argument("input", type=Path, help="PractiScore .pcs/.psc archive or unpacked export directory")
    parse.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help=f"Configuration YAML (default: {DEFAULT_CONFIG})")
    parse.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT, help=f"Shooter summary YAML (default: {DEFAULT_SUMMARY_OUTPUT})")
    parse.add_argument("--diplomas-output", type=Path, default=DEFAULT_DIPLOMAS_OUTPUT, help=f"Diploma data YAML (default: {DEFAULT_DIPLOMAS_OUTPUT})")
    render = commands.add_parser("render", help="Render diploma data into a DOCX document")
    render.add_argument("--diplomas-input", type=Path, default=DEFAULT_DIPLOMAS_OUTPUT, help=f"Diploma data YAML (default: {DEFAULT_DIPLOMAS_OUTPUT})")
    render.add_argument("--template", type=Path, required=True, help="DOCX diploma template")
    render.add_argument("-o", "--output", type=Path, required=True, help="Final DOCX output")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "render":
        try:
            render_diplomas(args.diplomas_input, args.template, args.output)
        except (DiplomaRenderError, OSError) as exc:
            parser.error(str(exc))
        return 0
    try:
        match = load_match_data(args.input)
        configs = load_config(args.config)
        mark_chrono_failure_as_dnf = next(iter(configs.values())).mark_chrono_failure_as_dnf
        summary = parse_match_data(match, mark_chrono_failure_as_dnf=mark_chrono_failure_as_dnf)
        diplomas = generate_diplomas(summary, match.definition, configs)
        _write_yaml(args.summary_output, summary)
        _write_yaml(args.diplomas_output, diplomas)
    except (MatchParseError, DiplomaDataError, OSError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
