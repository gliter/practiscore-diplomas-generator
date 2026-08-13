from __future__ import annotations

import argparse
import locale
import os
from pathlib import Path
import re
import sys

import yaml

from .diplomas import DiplomaDataError, generate_diplomas, load_config
from .parser import MatchParseError, load_match_data, parse_match_data
from .render import DiplomaRenderError, render_diploma_data, render_diplomas

DEFAULT_SUMMARY_OUTPUT = Path("shooters-summary.yaml")
DEFAULT_DIPLOMAS_OUTPUT = Path("diplomas-data.yaml")

_MESSAGES = {
    "en": {
        "description": "Parse PractiScore exports and generate diploma data.",
        "language": "CLI help language (default: system locale)",
        "parse_help": "Create shooter summary and diploma data files.",
        "parse_input": "PractiScore .pcs/.psc archive or unpacked export directory",
        "config": "Configuration YAML",
        "summary": "Shooter summary YAML (default: shooters-summary-<match-name>.yaml)",
        "diplomas": "Diploma data YAML (default: diplomas-data-<match-name>.yaml)",
        "render_help": "Render diploma data into a DOCX, ODT, or PDF document.",
        "diplomas_input": "Diploma data YAML (required unless --input is used)",
        "render_input": "PractiScore archive or unpacked export directory; also writes summary and diploma data YAML",
        "template": "DOCX or ODT diploma template",
        "output_docx": "Final DOCX output, path optional (default for DOCX templates)",
        "output_odt": "Final ODT output, path optional",
        "output_pdf": "Final PDF output, path optional (requires LibreOffice)",
        "render_config": "Configuration YAML (required with --input)",
        "examples": "Examples:\n  practiscore-diplomas parse -i MATCH.pcs -c configs\\gpa_t1_config.yaml\n  practiscore-diplomas render -d diplomas-data-MATCH.yaml -t diploma-template.docx\n  practiscore-diplomas render -i MATCH.pcs -c configs\\gpa_t1_config.yaml -t diploma-template.docx",
        "command_options": "Command options:\n  parse -i PATH -c PATH [-s PATH] [-d PATH]\n    -i, --input PATH      PractiScore archive or unpacked export directory (required)\n    -c, --config PATH     Configuration YAML (required)\n    -s, --summary-output PATH Shooter summary output\n    -d, --diplomas-data PATH Diploma data output\n  render (-d PATH | -i PATH) -t PATH [output option]\n    -d, --diplomas-data PATH Diploma data input\n    -i, --input PATH      Match input; writes summary and diploma data, then renders\n    -c, --config PATH     Configuration YAML (required with -i)\n    -t, --template PATH   DOCX or ODT diploma template (required)\n    -o, --output-docx PATH Final DOCX output (default: diplomas.docx or diplomas-<match-name>.docx)\n        --output-odt PATH Final ODT output\n        --output-pdf PATH Final PDF output (requires LibreOffice)",
    },
    "pl": {
        "description": "Parsuj eksporty PractiScore i generuj dane dyplomów.",
        "language": "Język pomocy CLI (domyślnie: ustawienia systemu)",
        "parse_help": "Utwórz podsumowanie strzelców i dane dyplomów.",
        "parse_input": "Archiwum PractiScore .pcs/.psc lub rozpakowany katalog eksportu",
        "config": "Plik YAML z konfiguracją",
        "summary": "Podsumowanie strzelców YAML (domyślnie: shooters-summary-<nazwa-meczu>.yaml)",
        "diplomas": "Dane dyplomów YAML (domyślnie: diplomas-data-<nazwa-meczu>.yaml)",
        "render_help": "Wygeneruj dokument DOCX, ODT lub PDF z danych dyplomów.",
        "diplomas_input": "Dane dyplomów YAML (wymagane, chyba że użyto --input)",
        "render_input": "Archiwum PractiScore lub rozpakowany katalog eksportu; zapisuje też podsumowanie i dane dyplomów YAML",
        "template": "Szablon dyplomu DOCX lub ODT",
        "output_docx": "Docelowy plik DOCX, ścieżka opcjonalna (domyślnie dla szablonu DOCX)",
        "output_odt": "Docelowy plik ODT, ścieżka opcjonalna",
        "output_pdf": "Docelowy plik PDF, ścieżka opcjonalna (wymaga LibreOffice)",
        "render_config": "Plik YAML z konfiguracją (wymagany z --input)",
        "examples": "Przykłady:\n  practiscore-diplomas parse -i MECZ.pcs -c configs\\gpa_t1_config.yaml\n  practiscore-diplomas render -d diplomas-data-MECZ.yaml -t szablon-dyplomu.docx\n  practiscore-diplomas render -i MECZ.pcs -c configs\\gpa_t1_config.yaml -t szablon-dyplomu.docx",
        "command_options": "Opcje poleceń:\n  parse -i PATH -c PATH [-s PATH] [-d PATH]\n    -i, --input PATH      Archiwum PractiScore lub rozpakowany katalog eksportu (wymagany)\n    -c, --config PATH     Plik YAML z konfiguracją (wymagany)\n    -s, --summary-output PATH Plik wynikowy podsumowania strzelców\n    -d, --diplomas-data PATH Plik wynikowy danych dyplomów\n  render (-d PATH | -i PATH) -t PATH [opcja wyjścia]\n    -d, --diplomas-data PATH Dane dyplomów jako wejście\n    -i, --input PATH      Wejście meczu; zapisuje podsumowanie i dane dyplomów, potem renderuje\n    -c, --config PATH     Plik YAML z konfiguracją (wymagany z -i)\n    -t, --template PATH   Szablon dyplomu DOCX lub ODT (wymagany)\n    -o, --output-docx PATH Docelowy plik DOCX (domyślnie: diplomas.docx lub diplomas-<nazwa-meczu>.docx)\n        --output-odt PATH Docelowy plik ODT\n        --output-pdf PATH Docelowy plik PDF (wymaga LibreOffice)",
    },
}


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
            yaml.safe_dump(value, stream, allow_unicode=True, sort_keys=False)


def _match_output_path(prefix: str, match_name: object) -> Path:
    name = str(match_name).strip() or "match"
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "-", name).strip(" .-") or "match"
    return Path(f"{prefix}-{name}.yaml")


def _match_document_path(prefix: str, match_name: object) -> Path:
    name = str(match_name).strip() or "match"
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "-", name).strip(" .-") or "match"
    return Path(f"{prefix}-{name}.docx")


def _default_document_path(prefix: str, match_name: object, template: Path) -> Path:
    extension = ".odt" if template.suffix.lower() == ".odt" else ".docx"
    if match_name is None:
        return Path(f"{prefix}{extension}")
    path = _match_document_path(prefix, match_name)
    return path.with_suffix(extension)


def _requested_output(args: argparse.Namespace, match_name: object) -> Path:
    selected = (
        (args.output_docx, ".docx"),
        (args.output_odt, ".odt"),
        (args.output_pdf, ".pdf"),
    )
    for value, extension in selected:
        if value is not None:
            if value == Path("."):
                default = _default_document_path("diplomas", match_name, args.template)
                return default.with_suffix(extension)
            return value
    return _default_document_path("diplomas", match_name, args.template)


def _system_language() -> str:
    candidates = [locale.getlocale()[0], os.environ.get("LC_ALL"), os.environ.get("LANG")]
    return "pl" if any(value and value.lower().startswith(("pl", "polish")) for value in candidates) else "en"


def _language_from_argv(argv: list[str]) -> str:
    for index, value in enumerate(argv):
        if value == "--language" and index + 1 < len(argv):
            return argv[index + 1]
        if value.startswith("--language="):
            return value.split("=", 1)[1]
    return _system_language()


def _build_parser(language: str | None = None) -> argparse.ArgumentParser:
    language = language or _system_language()
    if language not in _MESSAGES:
        language = _system_language()
    messages = _MESSAGES[language]
    parser = argparse.ArgumentParser(
        description=messages["description"],
        epilog=f"{messages['command_options']}\n\n{messages['examples']}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--language", choices=tuple(_MESSAGES), default=language, help=messages["language"])
    commands = parser.add_subparsers(dest="command", required=False)
    parse = commands.add_parser("parse", help=messages["parse_help"], description=messages["parse_help"], epilog=messages["examples"], formatter_class=argparse.RawDescriptionHelpFormatter)
    parse.add_argument("--language", choices=tuple(_MESSAGES), default=argparse.SUPPRESS, help=messages["language"])
    parse.add_argument("-i", "--input", type=Path, required=True, help=messages["parse_input"])
    parse.add_argument("-c", "--config", type=Path, required=True, help=messages["config"])
    parse.add_argument("-s", "--summary-output", type=Path, help=messages["summary"])
    parse.add_argument("-d", "--diplomas-data", dest="diplomas_data", type=Path, help=messages["diplomas"])
    render = commands.add_parser("render", help=messages["render_help"], description=messages["render_help"], epilog=messages["examples"], formatter_class=argparse.RawDescriptionHelpFormatter)
    render.add_argument("--language", choices=tuple(_MESSAGES), default=argparse.SUPPRESS, help=messages["language"])
    render_inputs = render.add_mutually_exclusive_group(required=True)
    render_inputs.add_argument("-d", "--diplomas-data", dest="diplomas_data", type=Path, help=messages["diplomas_input"])
    render_inputs.add_argument("-i", "--input", type=Path, help=messages["render_input"])
    render.add_argument("-c", "--config", type=Path, help=messages["render_config"])
    render.add_argument("-t", "--template", type=Path, required=True, help=messages["template"])
    outputs = render.add_mutually_exclusive_group()
    outputs.add_argument("-o", "--output-docx", dest="output_docx", nargs="?", const=Path("."), type=Path, help=messages["output_docx"])
    outputs.add_argument("--output-odt", dest="output_odt", nargs="?", const=Path("."), type=Path, help=messages["output_odt"])
    outputs.add_argument("--output-pdf", dest="output_pdf", nargs="?", const=Path("."), type=Path, help=messages["output_pdf"])
    return parser


def main() -> int:
    parser = _build_parser(_language_from_argv(sys.argv[1:]))
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "render":
        try:
            if args.input is not None:
                if args.config is None:
                    parser.error("--config is required when --input is used")
                match = load_match_data(args.input)
                configs = load_config(args.config)
                mark_chrono_failure_as_dnf = next(iter(configs.values())).mark_chrono_failure_as_dnf
                summary = parse_match_data(match, mark_chrono_failure_as_dnf=mark_chrono_failure_as_dnf)
                diploma_data = generate_diplomas(summary, match.definition, configs)
                _write_yaml(_match_output_path("shooters-summary", match.definition.get("match_name")), summary)
                _write_yaml(_match_output_path("diplomas-data", match.definition.get("match_name")), diploma_data)
                output = _requested_output(args, match.definition.get("match_name"))
                render_diploma_data(diploma_data, args.template, output)
            else:
                if args.config is not None:
                    parser.error("--config can only be used with --input")
                output = _requested_output(args, None)
                render_diplomas(args.diplomas_data, args.template, output)
        except (DiplomaRenderError, DiplomaDataError, MatchParseError, OSError, yaml.YAMLError) as exc:
            parser.error(str(exc))
        return 0
    try:
        match = load_match_data(args.input)
        configs = load_config(args.config)
        mark_chrono_failure_as_dnf = next(iter(configs.values())).mark_chrono_failure_as_dnf
        summary = parse_match_data(match, mark_chrono_failure_as_dnf=mark_chrono_failure_as_dnf)
        diplomas = generate_diplomas(summary, match.definition, configs)
        summary_output = args.summary_output or _match_output_path("shooters-summary", match.definition.get("match_name"))
        diplomas_output = args.diplomas_data or _match_output_path("diplomas-data", match.definition.get("match_name"))
        _write_yaml(summary_output, summary)
        _write_yaml(diplomas_output, diplomas)
    except (MatchParseError, DiplomaDataError, OSError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
