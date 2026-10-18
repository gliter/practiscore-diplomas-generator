# PractiScore Diplomas Generator

Create one diploma document from a PractiScore match export. This guide walks through the normal workflow in the Windows graphical app. You can also use the command line if you prefer.

## Create Diplomas In The Graphical App

### 1. Export the match

In PractiScore, finish and verify the match, then choose **Import / Export** → **Export Match**. Save the exported archive. The app accepts `.pcs`, `.psc`, and `.zip` files; all three are ZIP archives. An unpacked export directory is also supported when using the command line.

### 2. Choose the match, award configuration, and template

Double-click `practiscore-diplomas.exe`. The dropdowns list match archives from the working directory, configurations from `configs`, and DOCX/ODT templates from `templates`. Choose **Choose another file…** to browse elsewhere. Keep `configs` and `templates` beside the executable when using the packaged Windows app.

As soon as you choose a match, the app parses the shooter data and saves `shooters-summary-<match-name>.yaml` in the working directory. If a summary for that match already exists and differs from the fresh parse, the app shows both file paths and modification times. Choose **Data from .pcs** to use the new export or **Data from summary** to keep your edited summary. If both versions are identical, no prompt is shown.

Choose the award configuration and diploma template. The configuration determines who qualifies and what award series are created. The template controls the document layout. Diploma rows appear in the main table when the required inputs are available.
To edit a configuration in the app, select it and click **Edit**. Click **Apply** to validate and use the changes in memory; use **Save** or **Save as** to write them to a file. If you close the app with unsaved configuration changes, you can save, save as, discard, or cancel.

### 3. Review the shooters and diploma rows

Use **Edit shooter data** beside the match selector to review or correct shooter records. Changes are kept in the editor until you choose **Save changes**. Division and class use match-provided dropdown values; categories and penalties have dedicated editors. Calculated penalty seconds and total time are shown for reference. Saving the shooter summary updates the YAML file and regenerates diploma data. If diploma rows were manually edited, the app asks whether to discard those edits before recalculating.

Review the diploma table before generating the document:

- Double-click a cell to edit it. The red **×** removes a row after confirmation; the blue switch icon changes its shooter. Use **New row…** to add a diploma.
- Use the column headings to sort or filter. Filters can include multiple values, and a dot in a heading indicates an active filter.
- The shooter picker uses the same sortable and filterable table. Its search matches names, divisions, categories, and classes.
- Rows with a template-line error are highlighted red. The affected line shows a short `<błąd: ...>` message, while the other diplomas are still generated. Correct the configuration and recalculate, or replace the error text manually.

Within each series, groups are ordered from the largest eligible group to the smallest. Diplomas within a group are listed from the last awarded place to first place.

### 4. Generate the document

Choose **Generate diplomas…** to save the document, or **Generate diplomas and open** to save it and open it in your system's default application. Choose the output path and format in the save dialog. DOCX and ODT work directly; PDF and cross-format conversion require LibreOffice with `soffice` on `PATH`.

The app also keeps two review files in the working directory:

```text
shooters-summary-<match-name>.yaml
diplomas-data-<match-name>.yaml
```

Keep these files with the match records if you want to review or reuse the parsed shooter data and selected diploma rows later.

## Use The Command Line

Install the project with `uv sync`, then run the terminal interactive workflow with:

```powershell
uv run practiscore-diplomas -I
```

The `-I` option opens the arrow-key and Enter menu. Running the executable normally opens the GUI. For repeatable commands or automation, use `parse` and `render` directly.

Parse an archive and create the review YAML files:

```powershell
uv run practiscore-diplomas parse -i "match-export.zip" -c "configs\gpa_t1_config.yaml"
```

Render directly from an archive:

```powershell
uv run practiscore-diplomas render `
  -i "match-export.zip" `
  -c "configs\gpa_t1_config.yaml" `
  -t "templates\example-diploma-template.docx" `
  --output-docx "diplomas.docx"
```

Render previously reviewed diploma data:

```powershell
uv run practiscore-diplomas render `
  -d "diplomas-data-Match-Name.yaml" `
  -t "templates\example-diploma-template.docx" `
  --output-docx "diplomas.docx"
```

Use `--output-odt` or `--output-pdf` to select another output format. Output paths are optional. The `parse` command requires a configuration; direct `render -i` also requires one. Use `--help` for all options.

## Award Configuration

### Choose an example configuration

The `configs` folder contains example award rules:

| File | Intended use |
| --- | --- |
| `gpa_t1_config.yaml` | GPA Tier 1 matches. |
| `idpa_t1_config.yaml` | IDPA Tier 1 matches. |
| `idpa_t2_config.yaml` | IDPA Tier 2 matches. |

Start with the configuration closest to your match. Make a copy before changing it so the original example remains available.

The configuration controls award series, such as division winners, category winners, fastest competitor, and most accurate competitor. It also decides who is eligible. By default, the supplied configurations exclude DQ and DNF competitors. A failed Chrono check is treated as DNF unless the configuration changes that setting.

### Common Configuration Changes

You may need to edit the configuration if your match uses different divisions, categories, award counts, or wording. The main concepts are:

| Setting | Meaning |
| --- | --- |
| `series` | The award series to create. Each named entry becomes a separate ranking. |
| `type` | `best_shooter`, `most_accurate`, or `fastest`. |
| `group_by` | Split the ranking by `division`, `class`, or `category`. |
| `min_competitors` | Number of competitors required for each additional diploma. `[1, 6, 11]` gives 1 diploma for 1-5 people, 2 for 6-10, and 3 for 11 or more. |
| `filters` | Include or exclude divisions, categories, or classes. Patterns are regular expressions. |
| `text` | The lines printed on the diploma. |

If a configuration error appears, check quotation marks, indentation, and the spelling of division/category names. YAML indentation matters: use spaces, not tabs.

## Configuration Reference

Configuration files use YAML. Start by copying the closest example from `configs`, then edit the copy in a text editor. Keep the indentation consistent: use spaces, never the Tab key.

The main parts of a configuration are:

```yaml
exclude_shooters:
  surnames: []
  ids: []
mark_chrono_failure_as_dnf: true
maps: {}
series: {}
```

### Award Series

Each entry under `series` describes one kind of diploma. The entry name is only an internal label, so choose a short, meaningful name. This example creates division awards:

```yaml
series:
  best_in_division:
    type: best_shooter
    group_by: [division]
    min_competitors: [1, 6, 11]
    text:
      first_line: "{{ division }} DIVISION"
      second_line: "{{ place }} PLACE"
```

| Setting | What it controls |
| --- | --- |
| `type` | Ranking method: `best_shooter` selects the best overall result, `most_accurate` selects the lowest points-down result, and `fastest` selects the lowest raw time. |
| `group_by` | Creates separate rankings for each listed value: `division`, `class`, and/or `category`. Leave it out for one ranking covering everyone. |
| `min_competitors` | Award thresholds. `[1, 6, 11]` gives one diploma for 1-5 eligible people, two for 6-10, and three from 11 onward. `[5]` gives no diploma below 5 people and one from 5 onward. |
| `exclude_dq` | When `true`, DQ competitors cannot receive this award. The default is `true`. |
| `exclude_dnf` | When `true`, DNF competitors cannot receive this award. The default is `true`. |
| `ineligible_penalties` | A list of penalty names that make a competitor ineligible for this one series. Use the penalty name exactly as it appears in the export. |

Every series needs `type`, `text.first_line`, and `text.second_line`. `group_by`, filters, penalty rules, and the third and fourth text line are optional.

### Filters

Filters limit a series to selected divisions, categories, or classes. They use regular expressions. A pattern is matched against the complete PractiScore value, so use `.*` when the registration text continues after the code.

```yaml
filters:
  divisions:
    include: ["CPI.*", "CPO.*"]
  categories:
    exclude: ["Lady.*"]
```

The example includes divisions whose registration name begins with `CPI` or `CPO`, while excluding the Lady category. The available filter groups are `divisions`, `categories`, and `classes`.

| Form | Meaning |
| --- | --- |
| Omit `filters` or a filter group | Include all values. |
| `include` | Include only values matching at least one listed pattern. |
| `exclude` | Exclude values matching a listed pattern. Exclusion takes priority over inclusion. |
| A simple list, such as `divisions: ["CPI.*"]` | Short form of `include`. |

### Maps And Diploma Line Text

Maps turn a value from PractiScore into the shorter wording printed on a diploma. They are especially useful when a division or category contains registration details that should not appear in the title.

```yaml
maps:
  division_code:
    "CPI.*": CPI
    "CPO.*": CPO
  division_place:
    1: CHAMPION
    2: 2nd PLACE
    3: 3rd PLACE
```

The program checks map entries from top to bottom and uses the first matching entry. Put more specific patterns before general ones. Quote text patterns such as `"CPI.*"`; numeric keys, such as places, do not need quotes.

The `text` section defines up to four lines for each diploma. The first two are required; the third and fourth are optional.

```yaml
text:
  first_line: "{{ division_code(division) }} DIVISION"
  second_line: "{{ division_place(place) }}"
  third_line: "{{ shooter.raw_time }} s"
  fourth_line: "{{ shooter.points_down }} PD"
```

Use `{{ field }}` to insert a value, and `{{ map_name(field) }}` to use a map. The following values can be used in diploma lines:

| Value | Meaning |
| --- | --- |
| `division`, `category`, `class` | The value that defines the current award group. |
| `place` | Place in the award ranking. |
| `type` | Award type: `best_shooter`, `most_accurate`, or `fastest`. |
| `shooter.shooter_id` | Visible GPA or IDPA competitor number. |
| `shooter.first_name`, `shooter.last_name` | Competitor name. |
| `shooter.division`, `shooter.categories`, `shooter.class` | Values recorded for the competitor in PractiScore. |
| `shooter.raw_time`, `shooter.points_down`, `shooter.steel_misses`, `shooter.penalty_seconds`, `shooter.total_time` | Result values. |
| `shooter.dnf`, `shooter.chrono_failure`, `shooter.dq`, `shooter.shooter_uid` | Competitor status, separate Chrono check result, and internal identifier. |

These YAML text lines provide `first_line` through `fourth_line` to the document template. The placeholders in the DOCX or ODT template are described in the next section; map calls are used in the configuration, not directly in the document template.

### Excluding Specific Shooters And Chrono Failures

Use `exclude_shooters` to remove non-competitors, test records, or a PAR-time record from every award series. `surnames` and `ids` are regular-expression lists; either list can be empty.

```yaml
exclude_shooters:
  surnames: ["(?i)^par$"]
  ids: []
```

`chrono_failure` in the summary records a gear check on a Chrono stage that was not marked Pass. It is independent of `dnf`. During diploma data generation, `mark_chrono_failure_as_dnf: true` (the default) treats this as DNF; `false` allows the shooter to remain eligible. Parsing a PCS file does not require a configuration.

## Prepare A Diploma Template

Use a DOCX or ODT file as the template. Put placeholders where changing text should appear, for example:

```text
{{ first_line }}
{{ second_line }}
{{ shooter.first_name }} {{ shooter.last_name }}
```

The program makes one copy of the template for each diploma and preserves its paragraph and table formatting. The package includes `templates/example-diploma-template.docx` and `templates/example-diploma-template.odt`.

### Template Fields

| Field | Meaning |
| --- | --- |
| `first_line` | First line defined by the award configuration. |
| `second_line` | Second line defined by the award configuration. |
| `third_line` | Optional third line. Empty when the series does not define it. |
| `fourth_line` | Optional fourth line. Empty when the series does not define it. |
| `place` | Competitor's place in that award ranking. |
| `division` | Division used for the award. |
| `category` | Category used for the award. |
| `class` | Class used for the award. |
| `metric_value` | Ranking value, for example time or points down. |
| `shooter.shooter_id` | Visible GPA or IDPA competitor number. |
| `shooter.first_name` | Competitor's first name. |
| `shooter.last_name` | Competitor's last name. |
| `shooter.division` | Division recorded in PractiScore. |
| `shooter.categories` | Categories, shown as comma-separated text. |
| `shooter.class` | Class recorded in PractiScore. |
| `shooter.raw_time` | Total raw time before penalties. |
| `shooter.points_down` | Total points-down count. |
| `shooter.steel_misses` | Total missed steel targets. |
| `shooter.penalty_seconds` | Time added for penalties. |
| `shooter.total_time` | Raw time plus penalties. |
| `shooter.dnf` | `True` when the competitor is DNF. |
| `shooter.dq` | `True` when the competitor is DQ. |
| `shooter.shooter_uid` | Internal PractiScore identifier. Usually not needed on a diploma. |

Use the exact spelling and braces shown above. An unknown placeholder in the DOCX/ODT template stops document rendering with an error. A bad field or map in a configured diploma line is shown in that diploma row during review.

## Output Formats

| Format | Use |
| --- | --- |
| DOCX | Best when you want to edit the generated document. |
| ODT | Use with an ODT template or when you need an editable ODT document. |
| PDF | Requires LibreOffice with `soffice` available on `PATH`. |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| A match file is not listed | Confirm that it is a `.pcs`, `.psc`, or `.zip` export, or use **Choose file**. |
| No diploma was created for a division or category | Check the configuration's filters, `min_competitors`, and DNF/DQ rules. |
| A competitor is unexpectedly DNF | Check whether every stage has a score and whether Chrono was passed. |
| A placeholder causes an error | Check its spelling against the Template Fields table. |
| PDF output fails | Install LibreOffice and ensure `soffice` is available on `PATH`. |
| Text is not positioned correctly | Adjust the paragraph or table formatting in the template, then render again. |
