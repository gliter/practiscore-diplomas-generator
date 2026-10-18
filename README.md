# PractiScore Diplomas Generator

Create diploma documents from PractiScore match results. The application parses shooter data, applies award rules, lets you review the diploma list, and generates one DOCX, ODT, or PDF document.

**[Download the latest Windows package](https://github.com/gliter/practiscore-diplomas-generator/releases/latest/download/practiscore-diplomas-generator-windows-x64.zip)**

This link always downloads the package from the latest published release.

**User guides:** [English](docs/README.en.md) · [Polski](docs/README.pl.md)

## Quick Start

### Windows application

1. [Download the latest Windows package](https://github.com/gliter/practiscore-diplomas-generator/releases/latest/download/practiscore-diplomas-generator-windows-x64.zip) and extract it.
2. Keep the `configs` and `templates` folders beside `practiscore-diplomas.exe`.
3. Double-click the executable. Choose a PractiScore `.pcs`, `.psc`, or `.zip` match archive, an award configuration, and a DOCX/ODT template.
4. Review the diploma rows, then choose **Generate diplomas…** or **Generate diplomas and open**.

The application also accepts an unpacked PractiScore export directory from the command line. The GUI lists match files in its working directory and includes a file browser option for each input.

### Command line and interactive mode

The Windows executable includes both the GUI and CLI. Open PowerShell in the extracted package folder and add `-I` for the interactive terminal menu:

```powershell
.\practiscore-diplomas.exe -I
```

For automation, run `parse` and `render` directly:

```powershell
.\practiscore-diplomas.exe parse -i "match-export.zip" -c "configs\gpa_t1_config.yaml"
.\practiscore-diplomas.exe render -d "diplomas-data-Match.yaml" -t "templates\example-diploma-template.docx" -o "diplomas.docx"
```

The packaged executable requires neither Python nor `uv`. The user guides also describe running from source with `uv`. See the user guides for the full workflow, configuration, template fields, output formats, and troubleshooting.

## Development

The project targets Python 3.10 or newer and uses `uv` for environment management:

```powershell
uv sync --dev
uv run pytest
```

To run the GUI or terminal menu from source:

```powershell
uv run practiscore-diplomas
uv run practiscore-diplomas -I
```

For CLI commands from source, replace `.\practiscore-diplomas.exe` in the examples with `uv run practiscore-diplomas`.

The parser reads current `match_scores` data and shooter definitions from `match_def.json`. It produces a shooter summary keyed by PractiScore `sh_uid`, with the visible competitor number stored separately as `shooter_id`. The GUI and CLI both use the same parser, award configuration, and document rendering code.

To build the Windows executable and release ZIP on Windows, sync the development dependencies and run the PowerShell build script:

```powershell
uv sync --dev
pwsh -File .\scripts\build_windows.ps1 -Version 0.1.1
```

The build script uses PyInstaller. It packages the executable, example configurations, user guides, templates, and license. Generated build files are written under `build/` and `dist/`.

## Python API

The parser also works independently of award configuration:

```python
from practiscore_diplomas import parse_match

summary = parse_match("match-export.zip")
```

`parse_match` accepts an archive or unpacked export directory. `parse_match_file` and `parse_match_directory` are available for explicit input types. The summary contains raw shooter records and a `_match_options` entry used to calculate scores.
