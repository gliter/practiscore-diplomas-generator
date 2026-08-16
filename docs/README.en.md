# PractiScore Diplomas Generator

This tool reads a PractiScore `.pcs` or `.psc` export, selects diploma recipients according to a YAML configuration, and renders the selected diplomas into one DOCX file.

## Running On Windows

Run `practiscore-diplomas.exe` from PowerShell in the folder containing the executable. The executable does not require Python or `uv`. Keep the `configs` folder and the DOCX template next to it, or pass their full paths.

## Interactive Mode

Run the program without arguments to open an interactive menu. Use the up and down arrows and press Enter to choose one of these workflows:

- render directly from a PractiScore `.pcs` or `.psc` export;
- render from a diploma-data YAML file;
- parse a PractiScore export into the shooter summary and diploma-data YAML files.

The menu lists configurations from `configs`, match and YAML files from the current directory, and DOCX/ODT templates from the current directory. Each picker also includes a `Choose file` option to open the system file dialog. If the dialog is cancelled, the picker returns to the list. Rendering uses a system save dialog with a suggested output name. A success message is displayed after the operation finishes.

## Language

Help follows the system locale. Polish systems use Polish help; other locales use English. Override it explicitly with `--language` either before or after the command:

```powershell
practiscore-diplomas --language en --help
practiscore-diplomas parse --language pl --help
```

## Parse A Match

Parsing requires a configuration file:

```powershell
practiscore-diplomas parse `
  -i "match-export.pcs" `
  -c "configs\gpa_t1_config.yaml"
```

An unpacked export directory containing `match_def.json` and `match_scores.json` is also accepted. By default, parse writes:

```text
shooters-summary-<match-name>.yaml
diplomas-data-<match-name>.yaml
```

Spaces and invalid Windows filename characters in the match name are replaced with hyphens or underscores. Override either output explicitly:

```powershell
practiscore-diplomas parse -i "match-export.pcs" `
  -c "competition.yaml" `
  -s "results\summary.yaml" `
  -d "results\diplomas.yaml"
```

The shooter summary is keyed by PractiScore `sh_uid`. It contains the visible `shooter_id`, name, division, class, categories, raw time, penalty data, points down, steel misses, total time, DNF, and DQ status. Deleted shooters, shooters without current score rows, and shooters excluded by configuration are not selected. Missing stages and failed Chrono checks can mark a shooter DNF.

## Two Workflows

There are two ways to use the tool:

1. `parse` → `render`: parse the match first, review or manually edit the generated `diplomas-data-<match-name>.yaml`, then render that file. Use this workflow when you need to correct a name, adjust a displayed value, remove a diploma, or make another deliberate change before creating the DOCX.
2. Direct `render`: provide the match export, configuration, and DOCX template to `render`. The tool parses the match, saves both intermediate YAML files, and creates the DOCX in one step. Use this workflow when you want the convenience of one command but still want the generated data available for review.

The two-step workflow is also useful when the same diploma data needs to be rendered again with a different template.

## Configuration

The top-level configuration contains `maps` and a keyed `series` mapping. A minimal series looks like this:

```yaml
series:
  best_in_division:
    type: best_shooter
    group_by: [division]
    min_competitors: [1, 6, 11]
    exclude_dq: true
    exclude_dnf: true
    ineligible_penalties: []
    text:
      first_line: "{{ division }} DIVISION"
      second_line: "{{ place }}"
```

Supported series types are `best_shooter`, `most_accurate`, and `fastest`. `group_by` can use `division`, `class`, and `category`. A threshold list counts awards cumulatively: `[1, 6, 11]` produces one award for 1-5 eligible competitors, two for 6-10, and three for 11 or more. A threshold of `1` prevents an empty group from producing an award.

Filters use regular expressions. `include` limits values; `exclude` removes matching values. If a filter or one of its include/exclude lists is omitted, it means include everything or exclude nothing. When `include` is present, an `exclude` for the same dimension is unnecessary.

```yaml
filters:
  divisions:
    include: ["CCP|CDP|ESP|SSP"]
  categories:
    exclude: ["Lady"]
```

Top-level `exclude_shooters.surnames` and `exclude_shooters.ids` accept regex lists. `mark_chrono_failure_as_dnf` defaults to `true`; set it to `false` only when Chrono failures should not affect eligibility.

Maps convert export values into display values. Text maps use regex keys and place maps use integer keys:

```yaml
maps:
  division_code:
    "CO": CO
  division_place:
    1: CHAMPION
```

Text supports `division`, `category`, `class`, `place`, `type`, `shooter.<field>`, and map calls such as `{{ division_code(division) }}`. Missing mappings are configuration errors.

## DOCX or ODT Template

Render the generated diploma data with a DOCX or ODT template:

```powershell
practiscore-diplomas render `
  -d "diplomas-data-Plata-o-Plomo-2025.yaml" `
  -t "diploma-template.docx" `
  --output-docx "diplomas.docx"
```

The template is cloned once for each diploma record, preserving configured series order and ranking order. The result has one diploma page per record. Placeholders in paragraphs and tables use `{{ field }}` syntax. Use `--output-odt` for an ODT document or `--output-pdf` for a PDF. The path after each output option is optional, so `--output-odt` creates `diplomas.odt`; provide a path to override it. `-o` is an alias for `--output-docx`; the three output options are mutually exclusive. PDF output requires LibreOffice with `soffice` available on `PATH`.

An ODT template rendered to ODT output is handled directly by the program and does not require LibreOffice:

```powershell
practiscore-diplomas render `
  -d "diplomas-data-MATCH.yaml" `
  -t "diploma-template.odt" `
  --output-odt
```

LibreOffice is needed only when converting between DOCX and ODT, or when creating PDF output.

Alternatively, parse and render directly from a match export. The configuration is required in this mode. This command also writes `shooters-summary-<match-name>.yaml` and `diplomas-data-<match-name>.yaml` next to the DOCX so you can review or edit the intermediate data:

```powershell
practiscore-diplomas render `
  -i "match-export.pcs" `
  -c "configs\gpa_t1_config.yaml" `
  -t "diploma-template.docx"
```

The default output is `diplomas.docx` when using `-d` and `diplomas-<match-name>.docx` when using `-i`. Use `-o` to override it.

Available diploma fields include `first_line`, `second_line`, optional `third_line` and `fourth_line`, `place`, `division`, `category`, `class`, and `metric_value`. Shooter fields use paths such as `{{ shooter.first_name }}`, `{{ shooter.last_name }}`, `{{ shooter.raw_time }}`, and `{{ shooter.points_down }}`. Missing optional third and fourth lines render empty; unknown or missing required fields fail clearly.

## Example Template

The folder contains `example-diploma-template.docx`, a minimal template containing only the diploma lines and shooter name. ODT templates use the same `{{ field }}` placeholders in text paragraphs. Use the example template to verify the workflow before preparing your own template.
