# Agent Guide

## Repository Purpose

This repository contains a Python application that parses PractiScore exports, selects diploma recipients, and will later generate diploma documents. The current implementation provides the `parse` operation, which writes both intermediate files. `render` is reserved for the future DOCX stage.

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
- `src/practiscore_diplomas/cli.py`: `parse`/`render` command-line interface and YAML serialization.
- `tests/`: anonymized unit and CLI tests.
- `diplom generator.md`: product specification and PractiScore field notes.

The parser reads only current `match_scores` data. `match_scores_history` is not part of the current result. The shooter summary is keyed by `sh_uid` and includes all shooter definitions from `match_def.json`. Each record preserves `sh_id` as `shooter_id`, which represents the visible GPA or IDPA competitor number.

## CLI Contract

```text
practiscore-diplomas parse INPUT [--config PATH] [--summary-output PATH] [--diplomas-output PATH]
practiscore-diplomas render ...
```

The `parse` command defaults to `config.yaml`, `shooters-summary.yaml`, and `diplomas-data.yaml`. Do not introduce `-o` for intermediate outputs: `-o` is reserved for the future final diploma document command.

Diploma configuration uses keyed series mappings. Filter values are regular expressions, with `*` reserved for match-all. Structured filters support `include` and `exclude`; include must match and exclude takes precedence. The filters section, dimensions, include lists, and exclude lists are optional; omitted values mean include all and exclude none. `min_competitors: [5, 7, 13]` produces one diploma at 5 eligible competitors, two at 7, and three at 13. Diploma output is keyed by series and contains placement plus explicit grouping context.

The optional top-level `exclude_shooters` mapping accepts regex lists under `surnames` and `ids`; matching shooters are excluded from every diploma series.

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

## Verification Checklist

Before completing a change:

1. Run `uv run pytest`.
2. Run `uv run practiscore-diplomas --help` when changing the CLI.
3. For parser changes, test both an archive and an unpacked export when relevant.
4. Confirm generated files and dependency caches are ignored by Git.
