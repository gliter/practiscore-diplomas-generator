# PractiScore Diplomas Generator

User documentation: [English](docs/README.en.md) | [Polski](docs/README.pl.md)

Python tooling for turning PractiScore match exports into diplomas. The project is being built feature by feature. The current implementation parses a match and generates both the shooter summary and diploma-selection data.

## Current Feature

The parser supports IDPA and GPA exports that use points-down scoring. For each shooter it aggregates:

- raw time across all stages and strings;
- declared penalty counts and penalty seconds;
- points-down penalties;
- steel misses;
- total time;
- shooter name, surname, division, class, and categories;
- DNF and DQ status.

The result is a YAML mapping keyed by PractiScore shooter UID. All shooters from `match_def.json` are included, even when they have no current score rows.

Each record also contains `shooter_id`, which is the visible competitor number from PractiScore, such as a GPA number or IDPA number. This is separate from the internal `sh_uid` used as the YAML key.

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/)

Install the project environment and dependencies:

```powershell
uv sync
```

## Parse A Match

Point the command at a `.pcs` or `.psc` PractiScore ZIP export:

```powershell
uv run practiscore-diplomas parse -i "match-export.pcs" -c "configs\gpa_t1_config.yaml"
```

This creates `shooters-summary-<match-name>.yaml` and `diplomas-data-<match-name>.yaml` in the current directory, with spaces in the match name replaced by hyphens. A configuration must be provided with `--config`; example configurations are in `configs/`. An unpacked export directory containing `match_def.json` and `match_scores.json` is also accepted:

```powershell
uv run practiscore-diplomas parse -i "path\to\unpacked-export" -c "configs\gpa_t1_config.yaml"
```

Output and config paths can be set with explicit long options:

```powershell
uv run practiscore-diplomas parse -i "match-export.pcs" `
  -c "competition.yaml" `
  -s "results\match-summary.yaml" `
  -d "results\diplomas-data.yaml"
```

`diplomas-data-<match name>.yaml` is keyed by configured series and contains placement, division/class/category context, ranking metric, and complete shooter details. Filter values are regular expressions; `*` is the explicit match-all value, so `CPI.*` matches the complete CPI division label. Filters can use `include` and `exclude`; a value must match an include pattern and must not match an exclude pattern. The whole `filters` section, an individual dimension filter, `include`, or `exclude` can be omitted: omitted filters include everything and exclude nothing. `min_competitors: [1, 6, 11]` means one diploma for 1–5 eligible competitors, two for 6–10, and three for 11 or more. A threshold of `1` prevents a series with no eligible competitors from producing a diploma.

Each series also defines `text.first_line` and `text.second_line`; optional `third_line` and `fourth_line` can be added. Templates support fields such as `{{ place }}`, `{{ shooter.raw_time }}`, and global map calls such as `{{ division_code(division) }}` or `{{ class_code(shooter.class) }}`. Global maps use regex keys for text values and integer keys for places. Missing mappings are reported as configuration errors.

## Render Diplomas

Render the intermediate diploma data into one DOCX file using a DOCX template:

```powershell
uv run practiscore-diplomas render `
  -d "diplomas-data-MATCH.yaml" `
  -t "diploma-template.docx" `
  -o "diplomas.docx"
```

The command can also parse and render a match directly:

```powershell
uv run practiscore-diplomas render `
  -i "match-export.pcs" `
  -c "configs\gpa_t1_config.yaml" `
  -t "diploma-template.docx"
```

The output defaults to `diplomas.docx` for diploma-data input and `diplomas-<match-name>.docx` for direct match input. The template is cloned once for each diploma record, in series and ranking order. Placeholders use `{{ field }}` syntax and can refer to `first_line`, `second_line`, optional `third_line`/`fourth_line`, `place`, `division`, `category`, `class`, `metric_value`, or shooter fields such as `{{ shooter.raw_time }}` and `{{ shooter.points_down }}`. Placeholders in document paragraphs and tables are supported. Missing optional third and fourth lines render as empty text; other missing or unknown fields are errors.

When direct match input is used, the command also writes `shooters-summary-<match-name>.yaml` and `diplomas-data-<match-name>.yaml` in the current directory. Review or edit the diploma data, then use the two-step `parse` → `render` workflow when manual changes are needed.

## Python API

The parser can also be used directly:

```python
from practiscore_diplomas import parse_match

summary = parse_match("match-export.pcs")
```

`parse_match` accepts either an archive path or an unpacked export directory. `parse_match_file` and `parse_match_directory` are available when the input type should be explicit.

## Development

Run the tests with:

```powershell
uv run pytest
```

The tests use synthetic, anonymized match data. The supplied example exports are useful for local integration checks, but real names, emails, and identifiers must not be copied into fixtures or documentation.

## Project Direction

The final workflow will use the parsed match, configuration, and DOCX template to produce diploma documents. The YAML shooter summary and diploma data are intermediate products, not final user-facing output.

Use the optional top-level `exclude_shooters` configuration to remove fake or non-competitive shooters from every series. Both fields accept regular expressions:

```yaml
exclude_shooters:
  surnames: ["(?i)^par$"]
  ids: ["^GPA0$"]
```

Chronograph stages are detected from `stage_scoretype: Chrono`. By default, a shooter whose Chrono result does not have `gear_check: Pass` is marked DNF. This can be disabled with `mark_chrono_failure_as_dnf: false`.
