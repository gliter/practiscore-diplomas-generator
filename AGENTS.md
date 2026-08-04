# Agent Guide

## Repository Purpose

This repository contains a Python application that parses PractiScore exports, selects diploma recipients, and renders diploma documents. `parse` writes the intermediate shooter summary and diploma data; `render` turns diploma data and a DOCX template into the final document.

## Development Setup

Use `uv` for dependency and environment management:

```powershell
uv sync
uv run pytest
```

The project targets Python 3.10 or newer. Keep dependencies declared in `pyproject.toml`; do not rely on globally installed packages.

## Current Architecture

- `src/practiscore_diplomas/parser.py`: archive/directory loading and score aggregation.
- `src/practiscore_diplomas/diplomas.py`: configuration validation, grouping, eligibility, ranking, and diploma-data generation.
- `src/practiscore_diplomas/render.py`: DOCX template expansion and multi-page document assembly.
- `src/practiscore_diplomas/cli.py`: `parse`/`render` command-line interface and YAML serialization.
- `tests/`: anonymized unit and CLI tests.
- `diplom generator.md`: product specification and PractiScore field notes.

The parser reads only current `match_scores` data. `match_scores_history` is not part of the current result. The shooter summary is keyed by `sh_uid` and includes all shooter definitions from `match_def.json`. Each record preserves `sh_id` as `shooter_id`, which represents the visible GPA or IDPA competitor number.

## CLI Contract

```text
practiscore-diplomas parse INPUT [--config PATH] [--summary-output PATH] [--diplomas-output PATH]
practiscore-diplomas render [--diplomas-input PATH] --template PATH -o PATH
```

The `parse` command defaults to `config.yaml`, `shooters-summary.yaml`, and `diplomas-data.yaml`. Do not introduce `-o` for intermediate outputs: `-o` is reserved for the final rendered diploma document. `render` defaults to `diplomas-data.yaml`, clones the DOCX template for every record in series/ranking order, and writes one output DOCX. It expands placeholders in body paragraphs and tables using `{{ field }}` syntax. Supported fields include the diploma lines, `place`, `division`, `category`, `class`, `metric_value`, and `shooter.<field>` values. Missing `third_line` and `fourth_line` values render empty; other missing or unknown placeholders are errors.

Diploma configuration uses keyed series mappings. Filter values are regular expressions, with `*` reserved for match-all. Structured filters support `include` and `exclude`; include must match and exclude takes precedence. The filters section, dimensions, include lists, and exclude lists are optional; omitted values mean include all and exclude none. `min_competitors: [5, 7, 13]` produces one diploma at 5 eligible competitors, two at 7, and three at 13. Diploma output is keyed by series and contains placement plus explicit grouping context.

The optional top-level `exclude_shooters` mapping accepts regex lists under `surnames` and `ids`; matching shooters are excluded from every diploma series.

`mark_chrono_failure_as_dnf` defaults to `true`. Chrono stages are identified by `stage_scoretype: Chrono`, and any result without `gear_check: Pass` marks that shooter DNF.

Feature 2b requires every series to define `text.first_line` and `text.second_line`; `third_line` and `fourth_line` are optional. Templates support raw fields (`division`, `category`, `class`, `place`, `type`), explicit shooter fields such as `shooter.raw_time` and `shooter.points_down`, and named global map calls such as `{{ division_code(division) }}` or `{{ class_code(shooter.class) }}`. Map misses are errors; do not add unrestricted expression evaluation.

## Implementation Rules

- Preserve the existing public parser API unless a feature requires a deliberate change.
- Use `Decimal` or equivalent careful arithmetic for score calculations; avoid avoidable binary floating-point accumulation errors.
- Treat missing `pens`, `tpts`, and `str` arrays as zero values where the export format defines them as optional.
- Mark a shooter as DNF when current score rows do not cover every stage, even if no explicit DNF flag is present.
- Keep PractiScore penalty names intact as keys in the penalty-count mapping.
- Keep `points_down` and `steel_misses` as dedicated participant fields; do not duplicate them inside `penalties`.
- Add tests for new scoring behavior, malformed inputs, and CLI behavior.
- Use synthetic names, emails, IDs, and match data in tests and documentation. Never copy personal data from the supplied exports.
- Keep changes scoped to the requested feature and avoid unrelated formatting or refactoring.
- Keep DOCX rendering tests synthetic and verify both paragraph and table placeholder replacement.

## Verification Checklist

Before completing a change:

1. Run `uv run pytest`.
2. Run `uv run practiscore-diplomas --help` when changing the CLI.
3. Run a focused DOCX rendering test when changing template behavior.
4. For parser changes, test both an archive and an unpacked export when relevant.
5. Confirm generated files and dependency caches are ignored by Git.
