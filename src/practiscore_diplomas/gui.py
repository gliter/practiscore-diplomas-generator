"""Tkinter GUI for diploma generation and review."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import tkinter as tk
import yaml
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .cli import _match_document_path, _match_output_path, _system_language, _write_yaml
from .diplomas import _render_template_or_error, generate_diplomas, load_config, load_config_text
from .parser import SUMMARY_OPTIONS_KEY, derive_score_fields, load_match_data, parse_match_data
from .render import render_diploma_data
from .help_viewer import show_help

LABELS = {
    "en": ["PractiScore Diplomas", "PractiScore file (.pcs, .psc, or .zip)", "Configuration (.yaml)", "Template (.docx or .odt)", "Browse…", "Regenerate diploma data", "Generate diplomas…", "Series", "Place", "Division", "Category", "Class", "Shooter ID", "First name", "Last name", "First line", "Second line", "Third line", "Fourth line", "Choose a PCS file to create or load shooter data; select configuration to generate diploma data.", "Diplomas loaded: {}. Double-click a cell to edit it.", "Diplomas generated: {}", "Could not complete the operation", "Save generated diplomas", "No diploma records were produced by this configuration.", "Choose another file…", "Add diploma row", "Remove selected row", "Change shooter", "Select shooter", "Use shooter", "Cancel", "Select a diploma row to copy before adding one.", "Select one or more diploma rows to remove.", "Select a diploma row first."],
    "pl": ["Dyplomy PractiScore", "Plik PractiScore (.pcs, .psc lub .zip)", "Konfiguracja (.yaml)", "Szablon (.docx lub .odt)", "Wybierz…", "Przelicz dane dyplomów", "Generuj dyplomy…", "Seria", "Miejsce", "Dywizja", "Kategoria", "Klasa", "ID strzelca", "Imię", "Nazwisko", "Pierwsza linia", "Druga linia", "Trzecia linia", "Czwarta linia", "Wybierz plik PCS, aby utworzyć lub wczytać dane strzelców; konfiguracja generuje dane dyplomów.", "Wczytane dyplomy: {}. Kliknij dwukrotnie komórkę, aby ją edytować.", "Wygenerowano dyplomy: {}", "Nie można wykonać operacji", "Zapisz wygenerowane dyplomy", "Ta konfiguracja nie wygenerowała żadnych dyplomów.", "Wybierz inny plik…", "Dodaj wiersz dyplomu", "Usuń wybrany wiersz", "Zmień strzelca", "Wybierz strzelca", "Wybierz strzelca", "Anuluj", "Zaznacz wiersz dyplomu do skopiowania.", "Zaznacz co najmniej jeden wiersz do usunięcia.", "Najpierw zaznacz wiersz dyplomu."],
}
COLS = ("series", "place", "division", "category", "class", "id", "first", "last", "line1", "line2", "line3", "line4")
EXTRA = {
    "en": {"search": "Search by name, division, category or class", "details": "Shooter details", "first_name": "First name", "last_name": "Last name", "division": "Division", "categories": "Categories", "class": "Class", "shooter_id": "Shooter ID", "penalties": "Penalties", "chrono_failure": "Chrono failure", "uid": "UID", "result": "Result", "edit_shooters": "Edit shooters", "edit_shooters_button": "Edit shooter data", "edit_config": "Edit", "save_config": "Save", "save_config_as": "Save as", "config_editor": "Edit configuration", "apply_config": "Apply", "discard_config": "Discard", "config_unapplied": "Changes not applied yet. Click Apply to validate and use them.", "config_apply_prompt": "Apply the configuration edits before closing?\nConfiguration file: {}", "config_valid": "Valid configuration.", "config_pending_status": "Configuration changed in memory. Recalculate diploma data to apply it.", "config_invalid": "Invalid configuration: {}", "unsaved_config_title": "Unsaved configuration", "unsaved_config_prompt": "The configuration has unsaved changes:\n{}\nSave before closing?", "save_close": "Save", "save_as_close": "Save as", "discard_close": "Discard changes", "cancel_close": "Cancel", "new_row": "New row…", "save_shooters": "Save changes", "unsaved_title": "Unsaved shooter changes", "unsaved_prompt": "Save changes to the shooter summary before closing?", "parse_source_title": "Shooter data source", "parse_source_prompt": "Choose which shooter data to use.", "use_pcs": "Data from .pcs ({})", "use_summary": "Data from summary ({})", "source_path": "File: {}", "cancel_label": "Cancel", "stale_warning": "Diploma rows were manually changed. Regenerate diploma data from the updated shooter summary and discard those manual diploma changes?", "stale_status": "Shooter data changed, but diploma data was not regenerated. Click ‘Regenerate diploma data’ to update it.", "recalculate_prompt": "Recalculate diploma data from the shooter summary and discard manual diploma edits?", "raw_time": "Raw time", "points_down": "Points down", "steel_misses": "Steel misses", "penalty": "Penalty", "penalty_seconds": "Penalty", "total_time": "Total time", "dnf": "DNF", "dq": "DQ", "sort_ascending": "Sort ascending", "sort_descending": "Sort descending", "filter_column": "Filter this column…", "clear_filter": "Clear this column filter", "filter_title": "Column filter", "filter_prompt": "Choose the values to show. Click several values to include them all.", "select_all": "Select all", "select_none": "Select none", "apply_filter": "Apply", "clear_all": "Clear filter", "cancel_label": "Cancel", "generate_open": "Generate diplomas and open", "open_error": "The document was generated, but could not be opened: {}", "confirm_title": "Remove diploma", "confirm_remove": "Remove the diploma for {name} (place {place})?"},
    "pl": {"search": "Szukaj po imieniu, nazwisku, dywizji, kategorii lub klasie", "details": "Dane strzelca", "first_name": "Imię", "last_name": "Nazwisko", "division": "Dywizja", "categories": "Kategorie", "class": "Klasa", "shooter_id": "ID strzelca", "penalties": "Kary", "chrono_failure": "Błąd chrono", "uid": "UID", "result": "Wynik", "edit_shooters": "Edytuj strzelców", "edit_shooters_button": "Edytuj dane strzelców", "edit_config": "Edytuj", "save_config": "Zapisz", "save_config_as": "Zapisz jako", "config_editor": "Edytuj konfigurację", "apply_config": "Zastosuj", "discard_config": "Odrzuć", "config_unapplied": "Zmiany nie są jeszcze zastosowane. Kliknij Zastosuj, aby je sprawdzić i użyć.", "config_apply_prompt": "Zastosować zmiany konfiguracji przed zamknięciem?\nPlik konfiguracji: {}", "config_valid": "Konfiguracja jest poprawna.", "config_pending_status": "Konfiguracja zmieniona w pamięci. Przelicz dane dyplomów, aby ją zastosować.", "config_invalid": "Błędna konfiguracja: {}", "unsaved_config_title": "Niezapisana konfiguracja", "unsaved_config_prompt": "Konfiguracja ma niezapisane zmiany:\n{}\nZapisać przed zamknięciem?", "save_close": "Zapisz", "save_as_close": "Zapisz jako", "discard_close": "Odrzuć zmiany", "cancel_close": "Anuluj", "new_row": "Nowy wiersz…", "save_shooters": "Zapisz zmiany", "unsaved_title": "Niezapisane zmiany strzelców", "unsaved_prompt": "Zapisać zmiany w podsumowaniu strzelców przed zamknięciem?", "parse_source_title": "Źródło danych strzelców", "parse_source_prompt": "Wybierz, których danych strzelców użyć.", "use_pcs": "Dane z .pcs ({})", "use_summary": "Dane z podsumowania ({})", "source_path": "Plik: {}", "cancel_label": "Anuluj", "stale_warning": "Wiersze dyplomów zostały zmienione ręcznie. Czy przeliczyć dane dyplomów na podstawie aktualnych danych strzelców i odrzucić ręczne zmiany dyplomów?", "stale_status": "Dane strzelców zostały zmienione, ale dane dyplomów nie zostały przeliczone. Kliknij „Przelicz dane dyplomów”, aby je zaktualizować.", "recalculate_prompt": "Przeliczyć dane dyplomów na podstawie podsumowania strzelców i odrzucić ręczne zmiany w dyplomach?", "raw_time": "Czas surowy", "points_down": "Punkty stracone", "steel_misses": "Chybienia do stali", "penalty": "Kary", "penalty_seconds": "Kary", "total_time": "Czas łączny", "dnf": "DNF", "dq": "DQ", "sort_ascending": "Sortuj rosnąco", "sort_descending": "Sortuj malejąco", "filter_column": "Filtruj tę kolumnę…", "clear_filter": "Wyczyść filtr kolumny", "filter_title": "Filtr kolumny", "filter_prompt": "Wybierz widoczne wartości. Kliknij kilka wartości, aby pokazać je wszystkie.", "select_all": "Zaznacz wszystkie", "select_none": "Odznacz wszystkie", "apply_filter": "Zastosuj", "clear_all": "Wyczyść filtr", "cancel_label": "Anuluj", "generate_open": "Generuj dyplomy i otwórz", "open_error": "Dokument został wygenerowany, ale nie można go otworzyć: {}", "confirm_title": "Usuń dyplom", "confirm_remove": "Usunąć dyplom strzelca {name} (miejsce {place})?"},
}
EXTRA["en"]["restored_status"] = "Diploma data restored from {}. You can generate the document or recalculate to replace these rows."
EXTRA["pl"]["restored_status"] = "Wczytano zapisane dane dyplomów z {}. Możesz wygenerować dokument lub przeliczyć dane, zastępując te wiersze."
EXTRA["en"].update({
    "diploma_source_title": "Diploma data source",
    "diploma_source_prompt": "Saved diploma data differs from awards calculated from the current shooter data and configuration. Choose which data to use.",
    "use_saved_diplomas": "Use saved data",
    "regenerate_diplomas": "Generate again",
    "diploma_source_warning": "Generating again replaces the saved diploma data, including manual edits.",
})
EXTRA["pl"].update({
    "diploma_source_title": "Źródło danych dyplomów",
    "diploma_source_prompt": "Zapisane dane dyplomów różnią się od danych wyliczonych z aktualnych strzelców i konfiguracji. Wybierz, których danych użyć.",
    "use_saved_diplomas": "Użyj danych z pliku",
    "regenerate_diplomas": "Wygeneruj ponownie",
    "diploma_source_warning": "Ponowne generowanie zastąpi zapisane dane dyplomów, w tym ręczne poprawki.",
})
TEXT_FIELDS = dict(line1="first_line", line2="second_line", line3="third_line", line4="fourth_line")
SHOOTER_FIELDS = dict(id="shooter_id", first="first_name", last="last_name")


@dataclass(frozen=True)
class _CellDisplay:
    raw: str
    display: str

    def __str__(self) -> str:
        return self.raw



def _settings_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / "PractiScore Diplomas" / "settings.json"


def _load_settings(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1}
    if not isinstance(value, dict) or value.get("version") != 1:
        return {"version": 1}
    return value


def _save_settings(path: Path, settings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as handle:
            temporary_path = Path(handle.name)
            json.dump(settings, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def _diploma_data(rows: list[dict[str, Any]]) -> dict[str, Any]:
    diplomas: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        record = deepcopy(row)
        series = record.pop("_series")
        diplomas.setdefault(series, []).append(record)
    return {"diplomas": diplomas}


def _diploma_rows(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("diplomas"), dict):
        raise ValueError("Diploma data must contain a 'diplomas' mapping")
    rows = []
    for series, records in data["diplomas"].items():
        if not isinstance(series, str) or not isinstance(records, list):
            raise ValueError("Diploma series must map names to lists of records")
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("shooter", {}), dict):
                raise ValueError(f"Invalid diploma record in series {series!r}")
            rows.append({**deepcopy(record), "_series": series})
    return rows


def _compare_restored_diplomas(
    saved_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    definition: dict[str, Any],
    configs: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    """Calculate a baseline without changing restored rows or their YAML file."""
    baseline = _diploma_rows(generate_diplomas(summary, definition, configs))
    return baseline, saved_rows != baseline


def _choose_diploma_source(parent: tk.Tk, path: Path, messages: dict[str, str]) -> str | None:
    dialog = tk.Toplevel(parent)
    dialog.title(messages["diploma_source_title"])
    dialog.transient(parent)
    dialog.resizable(False, False)
    result = None

    def choose(source: str | None) -> None:
        nonlocal result
        result = source
        dialog.destroy()

    ttk.Label(dialog, text=messages["diploma_source_prompt"], wraplength=560, justify="left").grid(
        row=0, column=0, columnspan=2, padx=18, pady=(18, 10), sticky="w"
    )
    ttk.Label(dialog, text=messages["source_path"].format(path.resolve()), wraplength=560, justify="left").grid(
        row=1, column=0, columnspan=2, padx=18, pady=(0, 10), sticky="w"
    )
    ttk.Label(dialog, text=messages["diploma_source_warning"], wraplength=560, justify="left").grid(
        row=2, column=0, columnspan=2, padx=18, pady=(0, 14), sticky="w"
    )
    ttk.Button(dialog, text=messages["use_saved_diplomas"], command=lambda: choose("saved")).grid(
        row=3, column=0, padx=(18, 6), pady=(0, 12), sticky="ew"
    )
    ttk.Button(dialog, text=messages["regenerate_diplomas"], command=lambda: choose("regenerate")).grid(
        row=3, column=1, padx=(6, 18), pady=(0, 12), sticky="ew"
    )
    ttk.Button(dialog, text=messages["cancel_label"], command=lambda: choose(None)).grid(
        row=4, column=1, padx=18, pady=(0, 16), sticky="e"
    )
    dialog.columnconfigure(0, weight=1)
    dialog.columnconfigure(1, weight=1)
    dialog.bind("<Escape>", lambda _event: choose(None))
    dialog.protocol("WM_DELETE_WINDOW", lambda: choose(None))
    dialog.update_idletasks()
    width, height = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
    x = max(0, (dialog.winfo_screenwidth() - width) // 2)
    y = max(0, (dialog.winfo_screenheight() - height) // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")
    dialog.grab_set()
    dialog.focus_set()
    dialog.wait_window()
    return result


def _load_diploma_rows(path: Path) -> list[dict[str, Any]]:
    return _diploma_rows(yaml.safe_load(path.read_text(encoding="utf-8")))


def _save_diploma_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Replace the snapshot atomically so a failed save keeps the previous file."""
    data = _diploma_data(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as stream:
            temporary_path = Path(stream.name)
            yaml.safe_dump(data, stream, allow_unicode=True, sort_keys=False)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _upgrade_legacy_summary(summary: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    """Add chrono_failure to pre-field summaries using the selected PCS scores."""
    upgraded = deepcopy(summary)
    upgraded[SUMMARY_OPTIONS_KEY] = deepcopy(parsed.get(SUMMARY_OPTIONS_KEY, {"divisions": [], "categories": [], "classes": []}))
    for uid, record in upgraded.items():
        if uid == SUMMARY_OPTIONS_KEY:
            continue
        record.pop("penalty_seconds", None)
        record.pop("total_time", None)
        if "chrono_failure" in record or uid not in parsed:
            continue
        parsed_record = parsed[uid]
        record["chrono_failure"] = bool(parsed_record.get("chrono_failure", False))
        if record["chrono_failure"] and not parsed_record.get("dnf", False):
            # Older parser versions folded chrono failures into dnf.
            record["dnf"] = False
    return upgraded


def _summaries_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare shooter summaries by their data, independent of YAML key order."""
    return left == right


def _file_choices(directory: Path, patterns: tuple[str, ...], other_label: str) -> list[str]:
    files = {
        path.resolve()
        for pattern in patterns
        for path in directory.glob(pattern)
        if path.is_file()
    } if directory.is_dir() else set()
    return [str(path) for path in sorted(files, key=lambda item: item.name.casefold())] + [other_label]


def _next_place(rows: list[dict[str, Any]], series: str) -> int:
    places = []
    for row in rows:
        if row.get("_series") != series:
            continue
        try:
            places.append(int(row.get("place", 0)))
        except (TypeError, ValueError):
            continue
    return max(places, default=0) + 1


def _assign_shooter(
    record: dict[str, Any],
    uid: str,
    summary: dict[str, Any],
    group_by: tuple[str, ...] = (),
) -> None:
    shooter = deepcopy(summary[uid])
    options = summary.get(SUMMARY_OPTIONS_KEY, {})
    if isinstance(options, dict):
        shooter.update(derive_score_fields(shooter, options))
    shooter["shooter_uid"] = uid
    record["shooter"] = shooter
    if "division" in group_by:
        record["division"] = shooter.get("division")
    if "class" in group_by:
        record["class"] = shooter.get("class")
    if "category" in group_by:
        categories = shooter.get("categories", [])
        current = record.get("category")
        record["category"] = current if current in categories else (categories[0] if categories else None)


def _filtered_shooter_uids(summary: dict[str, Any], query: str) -> list[str]:
    normalized = query.casefold().strip()
    return [
        uid for uid, shooter in summary.items()
        if uid != SUMMARY_OPTIONS_KEY and normalized in " ".join((
            str(uid),
            str(shooter.get("first_name", "")),
            str(shooter.get("last_name", "")),
            str(shooter.get("division", "")),
            " ".join(str(value) for value in shooter.get("categories", [])),
            str(shooter.get("class", "")),
        )).casefold()
    ]


def _penalty_label(name: str, values: dict[str, Any]) -> str:
    if name not in values:
        return name
    return f"{name} ({values[name]} s)"


def _shooter_display_values(shooter: dict[str, Any], labels: dict[str, str], options: dict[str, Any] | None = None) -> tuple[str, ...]:
    if options and any(key in options for key in ("penalty_values", "points_down_value", "steel_miss_pd_count")):
        shooter = {**shooter, **derive_score_fields(shooter, options)}
    result_parts = []
    for key, label in (("total_time", "total_time"), ("raw_time", "raw_time"), ("points_down", "points_down"), ("steel_misses", "steel_misses"), ("penalty_seconds", "penalty")):
        value = shooter.get(key)
        if value not in (None, ""):
            result_parts.append(f"{labels[label]}: {value}")
    if shooter.get("dnf"):
        result_parts.append(labels["dnf"])
    if shooter.get("dq"):
        result_parts.append(labels["dq"])
    return (
        str(shooter.get("first_name") or "—"),
        str(shooter.get("last_name") or "—"),
        str(shooter.get("division") or "—"),
        ", ".join(str(item) for item in shooter.get("categories", [])) or "—",
        str(shooter.get("class") or "—"),
        ", ".join(result_parts) or "—",
    )


def _new_diploma_row(source: dict[str, Any], uid: str, summary: dict[str, Any], group_by: tuple[str, ...]) -> dict[str, Any]:
    record = deepcopy(source)
    record["_series"] = ""
    record["place"] = 1
    for field in ("first_line", "second_line", "third_line", "fourth_line"):
        record[field] = ""
    record["metric_value"] = None
    shooter = summary[uid]
    record["division"] = shooter.get("division")
    record["class"] = shooter.get("class")
    categories = shooter.get("categories", [])
    current_category = record.get("category")
    record["category"] = current_category if current_category in categories else (categories[0] if categories else None)
    _assign_shooter(record, uid, summary, group_by)
    return record


def _matches_column_filters(values: dict[str, Any], filters: dict[str, str]) -> bool:
    return all(query.casefold() in str(values.get(column, "") or "").casefold() for column, query in filters.items())


def _sort_value(value: Any) -> tuple[int, Any]:
    text = str(value or "").strip()
    if not text:
        return (2, "")
    try:
        return (0, Decimal(text))
    except InvalidOperation:
        return (1, text.casefold())



def _filter_sort_items(items: list[tuple[str, tuple[Any, ...], Any]], columns: tuple[str, ...], filters: dict[str, frozenset[str]], sort_column: str | None, reverse: bool) -> list[tuple[str, tuple[Any, ...], Any]]:
    column_indexes = {column: index for index, column in enumerate(columns)}
    filtered = [
        item for item in items
        if all(str(item[1][column_indexes[column]] or "") in values for column, values in filters.items())
    ]
    if sort_column is not None:
        index = column_indexes[sort_column]
        filtered.sort(key=lambda item: _sort_value(item[1][index]), reverse=reverse)
    return filtered


class _FilterableTable:
    """Shared heading menu, value filters, and sorting for GUI tables."""

    def __init__(self, tree: ttk.Treeview, columns: tuple[str, ...], labels: dict[str, str], extra: dict[str, str], state: dict[str, Any] | None = None, on_change=None, after_refresh=None):
        self.tree = tree
        self.columns = columns
        self.labels = labels
        self.extra = extra
        self.items: list[tuple[str, tuple[Any, ...], Any]] = []
        self.filters: dict[str, frozenset[str]] = {}
        self.sort_column: str | None = None
        self.reverse = False
        self.on_change = on_change
        self.after_refresh = after_refresh
        state = state or {}
        if state.get("sort_column") in columns:
            self.sort_column = state["sort_column"]
            self.reverse = bool(state.get("reverse", False))
        saved_filters = state.get("filters", {})
        if isinstance(saved_filters, dict):
            self.filters = {key: frozenset(values) for key, values in saved_filters.items() if key in columns and isinstance(values, list)}
        widths = state.get("widths", {})
        if isinstance(widths, dict):
            for column, width in widths.items():
                if column in columns and isinstance(width, int) and width > 0:
                    self.tree.column(column, width=width)
        for column in columns:
            self.tree.heading(column, text=f"{labels[column]}  ▾", command=lambda field=column: self._show_menu(field))
        self._last_state: dict[str, Any] = {"widths": {}, "sort_column": self.sort_column, "reverse": self.reverse, "filters": {}}
        self.tree.bind("<ButtonRelease-1>", self._remember_state, add="+")
        self._remember_state()

    def set_items(self, items: list[tuple[str, tuple[Any, ...], Any]]) -> None:
        self.items = items
        self.refresh()

    def _snapshot_state(self) -> dict[str, Any]:
        return {
            "widths": {column: int(self.tree.column(column, "width")) for column in self.columns},
            "sort_column": self.sort_column,
            "reverse": self.reverse,
            "filters": {column: sorted(values) for column, values in self.filters.items()},
        }

    def export_state(self) -> dict[str, Any]:
        try:
            self._last_state = self._snapshot_state()
        except tk.TclError:
            pass
        return self._last_state

    def _remember_state(self, _event=None) -> None:
        try:
            self._last_state = self._snapshot_state()
        except tk.TclError:
            return
        self._changed()

    def _changed(self) -> None:
        self._last_state = self._snapshot_state()
        if self.on_change:
            self.on_change()

    def refresh(self) -> None:
        for column in self.columns:
            indicator = "  ●" if column in self.filters else ""
            self.tree.heading(column, text=f"{self.labels[column]}  ▾{indicator}")
        selection = self.tree.selection()
        old_items = self.tree.get_children()
        if old_items:
            self.tree.delete(*old_items)
        visible = _filter_sort_items(self.items, self.columns, self.filters, self.sort_column, self.reverse)
        for item in visible:
            iid, values, image = item[:3]
            tags = item[3] if len(item) > 3 else ()
            shown_values = tuple(value.display if isinstance(value, _CellDisplay) else value for value in values)
            kwargs = {"image": image} if image else {}
            self.tree.insert("", "end", iid=iid, values=shown_values, tags=tags, **kwargs)
        for iid in selection:
            if self.tree.exists(iid):
                self.tree.selection_add(iid)
        self._last_state = self._snapshot_state()
        if self.after_refresh:
            self.after_refresh(visible)

    def _show_menu(self, column: str) -> None:
        menu = tk.Menu(self.tree, tearoff=False)
        menu.add_command(label=self.extra["sort_ascending"], command=lambda: self._sort(column, False))
        menu.add_command(label=self.extra["sort_descending"], command=lambda: self._sort(column, True))
        menu.add_separator()
        menu.add_command(label=self.extra["filter_column"], command=lambda: self._choose_filter(column))
        if column in self.filters:
            menu.add_command(label=self.extra["clear_filter"], command=lambda: self._clear_filter(column))
        x, y = self.tree.winfo_pointerxy()
        self._menu = menu
        menu.tk_popup(x, y)

    def _sort(self, column: str, reverse: bool) -> None:
        self.sort_column = column
        self.reverse = reverse
        self.refresh()
        self._changed()

    def _choose_filter(self, column: str) -> None:
        dialog = tk.Toplevel(self.tree)
        dialog.title(f"{self.extra['filter_column'].rstrip('…')} — {self.labels[column]}")
        owner = self.tree.winfo_toplevel()
        screen_width, screen_height = owner.winfo_screenwidth(), owner.winfo_screenheight()
        width, height = min(640, max(480, screen_width - 100)), min(780, max(600, screen_height - 100))
        x, y = max(0, (screen_width - width) // 2), max(0, (screen_height - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.minsize(min(480, width), min(600, height))
        dialog.transient(owner)
        dialog.grab_set()
        ttk.Label(dialog, text=self.extra["filter_prompt"], wraplength=width - 50).grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))
        values = sorted({str(item[1][self.columns.index(column)] or "") for item in self.items}, key=str.casefold)
        choices = tk.Listbox(dialog, selectmode="multiple", exportselection=False)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=choices.yview)
        choices.configure(yscrollcommand=scrollbar.set)
        value_list = ttk.Frame(dialog)
        value_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=12, pady=6)
        value_list.columnconfigure(0, weight=1)
        value_list.rowconfigure(0, weight=1)
        choices.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        for value in values:
            choices.insert("end", value or "—")
        selected = self.filters.get(column)
        if selected is None:
            if values:
                choices.selection_set(0, "end")
        else:
            for index, value in enumerate(values):
                if value in selected:
                    choices.selection_set(index)
        controls = ttk.Frame(dialog)
        controls.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=6)
        ttk.Button(controls, text=self.extra["select_all"], command=lambda: choices.selection_set(0, "end")).pack(side="left")
        ttk.Button(controls, text=self.extra["select_none"], command=lambda: choices.selection_clear(0, "end")).pack(side="left", padx=6)
        actions = ttk.Frame(dialog)
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 12))

        def apply_filter() -> None:
            self.filters[column] = frozenset(values[index] for index in choices.curselection())
            self.refresh()
            self._changed()
            dialog.destroy()

        def clear_filter() -> None:
            self.filters.pop(column, None)
            self.refresh()
            self._changed()
            dialog.destroy()

        ttk.Button(actions, text=self.extra["clear_all"], command=clear_filter).pack(side="left")
        ttk.Button(actions, text=self.extra["apply_filter"], command=apply_filter).pack(side="right")
        ttk.Button(actions, text=self.extra["cancel_label"], command=dialog.destroy).pack(side="right", padx=6)
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(1, weight=1)
        dialog.wait_window()

    def _clear_filter(self, column: str) -> None:
        self.filters.pop(column, None)
        self.refresh()
        self._changed()

def _load_action_icons(root: tk.Tk) -> tuple[tk.PhotoImage, tk.PhotoImage, tk.PhotoImage]:
    asset_dir = Path(__file__).resolve().parent / "assets"
    return tuple(
        tk.PhotoImage(master=root, file=str(asset_dir / name)).subsample(28, 28)
        for name in ("trash-solid.png", "refresh-double.png", "edit-pencil.png")
    )


def launch_gui(language: str | None = None) -> int:
    words = LABELS.get(language or _system_language(), LABELS["en"])
    (title, match_label, config_label, template_label, browse_label, review_label, generate_label,
     *tail) = words
    labels = dict(zip(COLS, tail[:len(COLS)]))
    ready, loaded, saved, error, save_title, empty, other_label, add_label, _remove_label, shooter_label, picker_title, use_label, cancel_label, add_required, _remove_required, shooter_required = tail[len(COLS):]
    settings_file = _settings_path()
    settings = _load_settings(settings_file)
    root = tk.Tk()
    root.title(title)
    window_settings = settings.get("window", {})
    geometry = window_settings.get("geometry") if isinstance(window_settings, dict) else None
    root.geometry(geometry if isinstance(geometry, str) else "1200x700")
    root.minsize(850, 500)
    try:
        root.state("zoomed" if not isinstance(window_settings, dict) or window_settings.get("state") not in ("normal", "zoomed") else window_settings["state"])
    except tk.TclError:
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    paths = {key: tk.StringVar() for key in ("match", "config", "template")}
    status = tk.StringVar(value=ready)
    data: dict[str, Any] | None = None
    match_definition: dict[str, Any] | None = None
    summary_file: Path | None = None
    diploma_file: Path | None = None
    active_match_path = ""
    diplomas_restored = False
    generated_rows: list[dict[str, Any]] = []
    diplomas_stale = False
    recalculate_button: ttk.Button | None = None
    recalculate_frame: tk.Frame | None = None
    rows: list[dict[str, Any]] = []
    shooter_summary: dict[str, Any] = {}
    series_configs: dict[str, Any] = {}
    work_dir = Path.cwd()
    specs = [
        ("config", config_label, work_dir / "configs", ("*.yaml", "*.yml"), ("YAML", "*.yaml *.yml")),
        ("match", match_label, work_dir, ("*.pcs", "*.psc", "*.zip"), ("PractiScore", "*.pcs *.psc *.zip")),
        ("template", template_label, work_dir / "templates", ("*.docx", "*.odt"), ("Templates", "*.docx *.odt")),
    ]
    selectors: dict[str, ttk.Combobox] = {}
    last_selected = {key: "" for key, *_rest in specs}
    last_files = settings.get("last_files", {})
    if isinstance(last_files, dict):
        for key in paths:
            saved_path = last_files.get(key)
            if isinstance(saved_path, str):
                paths[key].set(saved_path)
                last_selected[key] = saved_path

    save_job: str | None = None
    table_controllers: dict[str, _FilterableTable] = {}

    def save_settings() -> None:
        nonlocal save_job
        save_job = None
        settings["version"] = 1
        settings["last_files"] = {key: variable.get() for key, variable in paths.items() if variable.get()}
        settings["window"] = {"geometry": root.geometry(), "state": root.state()}
        table_states = settings.setdefault("tables", {})
        if not isinstance(table_states, dict):
            table_states = {}
        for name, controller in table_controllers.items():
            try:
                table_states[name] = controller.export_state()
            except tk.TclError:
                continue
        settings["tables"] = table_states
        try:
            _save_settings(settings_file, settings)
        except OSError:
            pass

    def schedule_save(*_args) -> None:
        nonlocal save_job
        if save_job is not None:
            root.after_cancel(save_job)
        save_job = root.after(400, save_settings)

    match_selector_host: ttk.Frame | None = None
    config_selector_host: ttk.Frame | None = None
    for index, (key, label, directory, patterns, filetype) in enumerate(specs):
        choices = _file_choices(directory, patterns, other_label)
        variable = paths[key]
        selector_host = ttk.Frame(root) if key in {"match", "config"} else root
        selector = ttk.Combobox(selector_host, textvariable=variable, values=choices, state="readonly")
        selectors[key] = selector
        ttk.Label(root, text=label, width=26).grid(row=index, column=0, padx=9, pady=6, sticky="w")
        if key == "match":
            match_selector_host = selector_host
            selector_host.grid(row=index, column=1, columnspan=2, padx=5, pady=6, sticky="ew")
            selector_host.columnconfigure(0, weight=1)
            selector.pack(side="left", fill="x", expand=True)
        elif key == "config":
            config_selector_host = selector_host
            selector_host.grid(row=index, column=1, columnspan=2, padx=5, pady=6, sticky="ew")
            selector_host.columnconfigure(0, weight=1)
            selector.pack(side="left", fill="x", expand=True)
        else:
            selector.grid(row=index, column=1, columnspan=2, padx=5, pady=6, sticky="ew")

        def select_file(_event=None, target=key, caption=label, folder=directory, types=filetype):
            selected = paths[target].get()
            if selected != other_label:
                if target == "config" and not allow_config_switch(selected):
                    paths[target].set(config_loaded_path or last_selected[target])
                    return
                last_selected[target] = selected
                schedule_save()
                if target == "match":
                    process_selected_match()
                elif target == "config":
                    load_config_source(selected)
                    if shooter_summary:
                        recalculate_after_config_change()
                return
            chosen = filedialog.askopenfilename(
                title=caption,
                initialdir=str(folder if folder.is_dir() else work_dir),
                filetypes=[types, ("All files", "*.*")],
            )
            if chosen:
                if target == "config" and not allow_config_switch(chosen):
                    paths[target].set(config_loaded_path or last_selected[target])
                    return
                current_values = list(selectors[target]["values"])
                if chosen not in current_values:
                    current_values.insert(max(0, len(current_values) - 1), chosen)
                    selectors[target]["values"] = current_values
                paths[target].set(chosen)
                last_selected[target] = chosen
                if target == "match":
                    process_selected_match()
                elif target == "config":
                    if not load_config_source(chosen):
                        paths[target].set(config_loaded_path or last_selected[target])
                        return
                    if shooter_summary:
                        recalculate_after_config_change()
            else:
                paths[target].set(last_selected[target])
            selectors[target].focus_set()
            schedule_save()

        selector.bind("<<ComboboxSelected>>", select_file)

    extra = EXTRA.get(language or _system_language(), EXTRA["en"])
    config_buffer: str | None = None
    config_draft: str | None = None
    config_disk_text: str | None = None
    config_loaded_path: str | None = None
    config_editor: tk.Toplevel | None = None
    config_status = tk.StringVar(value="")
    config_buttons: dict[str, ttk.Button] = {}

    def config_is_dirty() -> bool:
        return config_draft is not None and config_draft != config_disk_text

    def update_config_buttons() -> None:
        enabled = config_buffer is not None
        if "edit" in config_buttons:
            config_buttons["edit"].state(["!disabled"] if enabled else ["disabled"])
        dirty = config_is_dirty()
        for key in ("save", "save_as"):
            if key in config_buttons:
                config_buttons[key].state(["!disabled"] if dirty else ["disabled"])

    def load_config_source(path: str) -> bool:
        nonlocal config_buffer, config_draft, config_disk_text, config_loaded_path
        try:
            content = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror(error, str(exc), parent=root)
            return False
        config_buffer = content
        config_draft = content
        config_disk_text = content
        config_loaded_path = str(Path(path).resolve())
        # Loading a file should not surface semantic validation errors. The editor
        # gives a quiet line highlight for YAML syntax and validates fully on Apply.
        config_status.set("")
        update_config_buttons()
        return True

    def allow_config_switch(new_path: str) -> bool:
        if not config_is_dirty():
            return True
        try:
            same_path = config_loaded_path == str(Path(new_path).resolve())
        except OSError:
            same_path = False
        if same_path:
            return True
        choice = messagebox.askyesnocancel(
            extra["unsaved_config_title"],
            extra["unsaved_config_prompt"].format(config_loaded_path or paths["config"].get()),
            parent=root,
        )
        if choice is None:
            return False
        if choice:
            return save_config_buffer()
        return True

    def save_config_buffer(save_as: bool = False, target_path: str | None = None) -> bool:
        nonlocal config_buffer, config_draft, config_disk_text, config_loaded_path, diplomas_stale
        if config_buffer is None:
            return False
        if config_draft != config_buffer:
            messagebox.showinfo(extra["config_editor"], extra["config_unapplied"], parent=config_editor or root)
            return False
        try:
            load_config_text(config_buffer, config_loaded_path or paths["config"].get() or "configuration")
        except Exception as exc:
            messagebox.showerror(error, str(exc), parent=config_editor or root)
            return False
        path_text = target_path
        if save_as and not path_text:
            current = Path(config_loaded_path or paths["config"].get() or work_dir / "config.yaml")
            path_text = filedialog.asksaveasfilename(
                title=extra["save_config_as"], initialdir=str(current.parent),
                initialfile=current.name, defaultextension=current.suffix or ".yaml",
                filetypes=[("YAML", "*.yaml *.yml"), ("All files", "*.*")], parent=root,
            )
            if not path_text:
                return False
        if not path_text:
            path_text = config_loaded_path or paths["config"].get()
        if not path_text:
            return False
        try:
            Path(path_text).write_text(config_buffer, encoding="utf-8", newline="")
        except OSError as exc:
            messagebox.showerror(error, str(exc), parent=config_editor or root)
            return False
        config_loaded_path = str(Path(path_text).resolve())
        config_disk_text = config_buffer
        config_draft = config_buffer
        paths["config"].set(path_text)
        last_selected["config"] = path_text
        current_values = list(selectors["config"]["values"])
        if path_text not in current_values:
            current_values.insert(max(0, len(current_values) - 1), path_text)
            selectors["config"]["values"] = current_values
        config_status.set(extra["config_valid"])
        update_config_buttons()
        schedule_save()
        if shooter_summary:
            if has_manual_diploma_edits() and not messagebox.askyesno(
                extra["edit_shooters"], extra["stale_warning"], parent=root
            ):
                diplomas_stale = True
                update_recalculate_button()
                status.set(extra["config_pending_status"])
            else:
                regenerate_diplomas()
        return True

    def open_config_editor() -> None:
        nonlocal config_editor
        selected = paths["config"].get()
        if config_buffer is None and selected and selected != other_label:
            if not load_config_source(selected):
                return
        if config_buffer is None:
            messagebox.showinfo(title, ready, parent=root)
            return
        if config_editor is not None and config_editor.winfo_exists():
            config_editor.deiconify()
            config_editor.lift()
            return
        editor = tk.Toplevel(root)
        config_editor = editor
        editor.title(extra["config_editor"])
        editor.geometry("1050x720")
        editor.minsize(700, 450)
        editor.columnconfigure(0, weight=1)
        editor.rowconfigure(1, weight=1)
        text = tk.Text(editor, wrap="none", undo=True, font=("Consolas", 11), padx=8, pady=8)
        text.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(10, 4))
        yscroll = ttk.Scrollbar(editor, orient="vertical", command=text.yview)
        yscroll.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(10, 4))
        xscroll = ttk.Scrollbar(editor, orient="horizontal", command=text.xview)
        xscroll.grid(row=2, column=0, sticky="ew", padx=10)
        text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        text.tag_configure("yaml_key", foreground="#1459a5")
        text.tag_configure("yaml_string", foreground="#8a3c00")
        text.tag_configure("yaml_comment", foreground="#777777")
        text.tag_configure("yaml_literal", foreground="#7a3e9d")
        text.insert("1.0", config_draft if config_draft is not None else config_buffer)
        text.edit_modified(False)
        editor_status = tk.StringVar(value=extra["config_unapplied"])
        ttk.Label(editor, textvariable=editor_status, anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 0))
        controls = ttk.Frame(editor)
        controls.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        def highlight_yaml() -> None:
            content = text.get("1.0", "end-1c")
            for tag in ("yaml_key", "yaml_string", "yaml_comment", "yaml_literal", "yaml_error_line"):
                text.tag_remove(tag, "1.0", "end")
            import re
            patterns = {
                "yaml_comment": r"(?m)#.*$",
                "yaml_key": r"(?m)^\s*[\w.-]+(?=\s*:)" ,
                "yaml_string": r"(?m)(?:'[^'\n]*'|\"[^\"\n]*\")",
                "yaml_literal": r"(?i)\b(?:true|false|null|yes|no|on|off)\b|(?<![\w.])-?\d+(?:\.\d+)?\b",
            }
            error_line = None
            try:
                yaml.compose(content)
            except yaml.YAMLError as exc:
                mark = getattr(exc, "problem_mark", None)
                # PyYAML reports a missing colon at the next key, where it
                # discovers the problem. In that case the context mark points
                # to the actual malformed simple key.
                if getattr(exc, "problem", None) == "could not find expected ':'":
                    mark = getattr(exc, "context_mark", None) or mark
                if mark is not None:
                    error_line = mark.line
            if error_line is not None:
                start = f"{error_line + 1}.0"
                end = f"{error_line + 1}.end"
                text.tag_add("yaml_error_line", start, end)
            for tag, pattern in patterns.items():
                for match in re.finditer(pattern, content):
                    text.tag_add(tag, f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            text.tag_configure("yaml_error_line", background="#fff3f1")
            text.tag_lower("yaml_error_line")

        def apply_current_config(show_error: bool = True, close_editor: bool = True) -> bool:
            nonlocal config_buffer, config_draft, diplomas_stale
            candidate = text.get("1.0", "end-1c")
            config_draft = candidate
            try:
                load_config_text(candidate, config_loaded_path or "in-memory configuration")
            except Exception as exc:
                editor_status.set(extra["config_invalid"].format(exc))
                text.after_idle(highlight_yaml)
                if show_error:
                    messagebox.showerror(error, str(exc), parent=editor)
                return False
            config_buffer = candidate
            config_draft = candidate
            editor_status.set(extra["config_valid"])
            config_status.set(extra["config_valid"])
            update_config_buttons()
            if shooter_summary:
                if has_manual_diploma_edits() and not messagebox.askyesno(
                    extra["edit_shooters"], extra["stale_warning"], parent=root
                ):
                    diplomas_stale = True
                    update_recalculate_button()
                    status.set(extra["config_pending_status"])
                else:
                    regenerate_diplomas()
            if close_editor:
                try:
                    editor.grab_release()
                    editor.destroy()
                except tk.TclError:
                    pass
            else:
                text.after_idle(highlight_yaml)
            return True

        def on_config_edit(_event=None) -> None:
            nonlocal config_draft
            if not text.edit_modified():
                return
            config_draft = text.get("1.0", "end-1c")
            text.edit_modified(False)
            editor_status.set(extra["config_unapplied"])
            update_config_buttons()
            text.after_idle(highlight_yaml)

        def request_editor_close() -> None:
            nonlocal config_draft
            candidate = text.get("1.0", "end-1c")
            if candidate != config_buffer:
                prompt = tk.Toplevel(editor)
                prompt.title(extra["config_editor"])
                prompt.transient(editor)
                prompt.resizable(False, False)
                prompt.grab_set()
                ttk.Label(
                    prompt,
                    text=extra["config_apply_prompt"].format(config_loaded_path or paths["config"].get()),
                    wraplength=520,
                    justify="left",
                ).pack(
                    padx=18, pady=(18, 12), anchor="w"
                )
                result = {"choice": None}

                def choose(value: str) -> None:
                    result["choice"] = value
                    prompt.destroy()

                buttons = ttk.Frame(prompt)
                buttons.pack(fill="x", padx=12, pady=(0, 12))
                ttk.Button(buttons, text=extra["cancel_label"], command=lambda: choose("cancel")).pack(side="right")
                ttk.Button(buttons, text=extra["discard_config"], command=lambda: choose("discard")).pack(side="right", padx=6)
                ttk.Button(buttons, text=extra["apply_config"], command=lambda: choose("apply")).pack(side="right")
                prompt.protocol("WM_DELETE_WINDOW", lambda: choose("cancel"))
                prompt.update_idletasks()
                prompt.geometry(f"+{editor.winfo_rootx() + 80}+{editor.winfo_rooty() + 80}")
                editor.wait_window(prompt)
                choice = result["choice"]
                if choice == "cancel":
                    return
                if choice == "apply" and not apply_current_config(close_editor=False):
                    return
                if choice == "discard":
                    config_draft = config_buffer
                    update_config_buttons()
            editor.grab_release()
            editor.destroy()

        text.bind("<<Modified>>", on_config_edit)
        ttk.Button(controls, text=extra["cancel_label"], command=request_editor_close).pack(side="right")
        ttk.Button(controls, text=extra["apply_config"], command=apply_current_config).pack(side="right", padx=(0, 8))
        editor.protocol("WM_DELETE_WINDOW", request_editor_close)
        editor.grab_set()
        def maximize_config_editor() -> None:
            if not editor.winfo_exists():
                return
            try:
                editor.state("zoomed")
            except tk.TclError:
                try:
                    editor.attributes("-zoomed", True)
                except tk.TclError:
                    pass
        editor.after(100, maximize_config_editor)
        text.focus_set()
        highlight_yaml()

    if config_selector_host is not None:
        config_buttons["edit"] = ttk.Button(config_selector_host, text=extra["edit_config"], command=open_config_editor)
        config_buttons["save"] = ttk.Button(config_selector_host, text=extra["save_config"], command=save_config_buffer)
        config_buttons["save_as"] = ttk.Button(config_selector_host, text=extra["save_config_as"], command=lambda: save_config_buffer(save_as=True))
        config_buttons["save_as"].pack(side="right", padx=(4, 0))
        config_buttons["save"].pack(side="right", padx=(4, 0))
        config_buttons["edit"].pack(side="right", padx=(4, 0))
        update_config_buttons()

    action_icons = _load_action_icons(root)
    table_frame = ttk.Frame(root, relief="solid", borderwidth=1)
    table_frame.grid(row=4, column=0, columnspan=4, padx=9, pady=8, sticky="nsew")
    style = ttk.Style(root)
    data_tree_style = "DiplomaData.Treeview"
    action_tree_style = "DiplomaAction.Treeview"
    action_heading_style = f"{action_tree_style}.Heading"
    style.configure(data_tree_style, padding=0, borderwidth=0, relief="flat")
    style.layout(data_tree_style, [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure(action_tree_style, padding=0, borderwidth=0, relief="flat")
    style.configure(action_heading_style, padding=0, borderwidth=0, relief="flat")
    style.layout(action_tree_style, [("Treeview.treearea", {"sticky": "nswe"})])
    style.layout(
        action_heading_style,
        [("Treeheading.padding", {"sticky": "nswe", "children": [
            ("Treeheading.image", {"side": "top", "sticky": ""}),
        ]})],
    )
    style.layout(
        f"{action_tree_style}.Item",
        [("Treeitem.padding", {"sticky": "nswe", "children": [
            ("Treeitem.image", {"side": "left", "sticky": ""}),
        ]})],
    )
    tree = ttk.Treeview(
        table_frame,
        columns=COLS,
        show="headings",
        selectmode="browse",
        style=data_tree_style,
    )
    for col in COLS:
        tree.column(col, width=145 if col.startswith("line") else 110, minwidth=70)
    tree.tag_configure("new-row", foreground="#707070")
    tree.tag_configure("template-error", foreground="#9b1c1c", background="#fff0f0")
    tree.grid(row=0, column=3, sticky="nsew")
    action_trees: list[ttk.Treeview] = []
    for index, icon in enumerate(action_icons):
        action_tree = ttk.Treeview(
            table_frame,
            show=("tree", "headings"),
            selectmode="none",
            style=action_tree_style,
        )
        action_tree.heading("#0", text="", image=icon)
        action_tree.column("#0", width=30, minwidth=30, stretch=False, anchor="center")
        action_tree.grid(row=0, column=index, sticky="ns")
        action_trees.append(action_tree)
    table_frame.columnconfigure(3, weight=1)
    table_frame.rowconfigure(0, weight=1)

    def scroll_table(*args) -> None:
        tree.yview(*args)
        for action_tree in action_trees:
            action_tree.yview(*args)

    sy = ttk.Scrollbar(table_frame, orient="vertical", command=scroll_table)
    sy.grid(row=0, column=4, sticky="ns")

    def report_table_scroll(first: str, last: str) -> None:
        sy.set(first, last)
        for action_tree in action_trees:
            action_tree.yview_moveto(first)

    tree.configure(yscrollcommand=report_table_scroll, xscrollcommand=lambda first, last: sx.set(first, last))
    sx = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    sx.grid(row=1, column=3, sticky="ew")

    def sync_action_trees(visible_items) -> None:
        for action_index, action_tree in enumerate(action_trees):
            children = action_tree.get_children()
            if children:
                action_tree.delete(*children)
            for item in visible_items:
                iid = item[0]
                action_tree.insert("", "end", iid=iid, image=action_icons[action_index])
            action_tree.insert("", "end", iid="__new__")
            action_tree.yview_moveto(tree.yview()[0])
        tree.insert(
            "", "end", iid="__new__", values=(extra["new_row"], *("" for _ in COLS[1:])), tags=("new-row",)
        )

    saved_tables = settings.get("tables", {})
    saved_diplomas_table = saved_tables.get("diplomas", {}) if isinstance(saved_tables, dict) else {}
    table = _FilterableTable(
        tree,
        COLS,
        labels,
        EXTRA.get(language or _system_language(), EXTRA["en"]),
        saved_diplomas_table,
        schedule_save,
        sync_action_trees,
    )
    table_controllers["diplomas"] = table
    help_window: tk.Toplevel | None = None

    def open_help(_event=None):
        nonlocal help_window
        if help_window is not None and help_window.winfo_exists():
            help_window.deiconify()
            help_window.lift()
            help_window.focus_set()
        else:
            try:
                help_window = show_help(root, language or _system_language())
            except (OSError, UnicodeError) as exc:
                messagebox.showerror(error, str(exc), parent=root)
        return "break"

    footer = ttk.Frame(root)
    footer.grid(row=5, column=0, columnspan=4, padx=9, pady=7, sticky="ew")
    help_label = "Pomoc (F1)" if (language or _system_language()) == "pl" else "Help (F1)"
    ttk.Button(footer, text=help_label, command=open_help).pack(side="right", padx=(12, 0))
    ttk.Label(footer, textvariable=status, anchor="w").pack(side="left", fill="x", expand=True)
    root.bind("<F1>", open_help)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(4, weight=1)

    def choose_shooter() -> str | None:
        if not shooter_summary:
            return None
        extra = EXTRA.get(language or _system_language(), EXTRA["en"])
        dialog = tk.Toplevel(root)
        dialog.title(picker_title)
        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        width = min(1600, max(1050, screen_width - 80))
        height = min(900, max(600, screen_height - 100))
        x, y = max(0, (screen_width - width) // 2), max(0, (screen_height - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.minsize(min(1050, width), min(600, height))
        dialog.grab_set()
        search = tk.StringVar()
        ttk.Label(dialog, text=extra["search"]).grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
        ttk.Entry(dialog, textvariable=search).grid(row=1, column=0, padx=12, pady=4, sticky="ew")
        shooter_columns = ("first_name", "last_name", "division", "categories", "class", "result")
        candidates = ttk.Treeview(dialog, columns=shooter_columns, show="headings", selectmode="browse")
        shooter_labels = {key: extra[key] for key in shooter_columns}
        for column, width in (("first_name", 125), ("last_name", 140), ("division", 130), ("categories", 180), ("class", 80), ("result", 420)):
            candidates.column(column, width=width, minwidth=70, stretch=column == "result")
        saved_tables = settings.get("tables", {})
        shooter_table_state = saved_tables.get("shooters", {}) if isinstance(saved_tables, dict) else {}
        shooter_table = _FilterableTable(candidates, shooter_columns, shooter_labels, extra, shooter_table_state, schedule_save)
        table_controllers["shooters"] = shooter_table
        candidates.grid(row=2, column=0, padx=12, pady=6, sticky="nsew")
        vertical = ttk.Scrollbar(dialog, orient="vertical", command=candidates.yview)
        vertical.grid(row=2, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(dialog, orient="horizontal", command=candidates.xview)
        horizontal.grid(row=3, column=0, padx=12, sticky="ew")
        candidates.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        result: list[str | None] = [None]
        visible_uids: list[str] = []

        def filter_shooters(*_args) -> None:
            query = search.get().casefold().strip()
            visible_uids.clear()
            existing = candidates.get_children()
            if existing:
                candidates.delete(*existing)
            visible_uids.extend(_filtered_shooter_uids(shooter_summary, query))
            shooter_table.set_items([
                (uid, _shooter_display_values(shooter_summary[uid], extra, shooter_summary.get(SUMMARY_OPTIONS_KEY, {})), None)
                for uid in visible_uids
            ])
            if visible_uids:
                candidates.selection_set(visible_uids[0])
                candidates.focus(visible_uids[0])

        def accept() -> None:
            selection = candidates.selection()
            if selection:
                result[0] = selection[0]
                dialog.destroy()

        search.trace_add("write", filter_shooters)
        candidates.bind("<Double-1>", lambda _event: accept())
        ttk.Button(dialog, text=cancel_label, command=dialog.destroy).grid(row=4, column=0, padx=12, pady=12, sticky="w")
        ttk.Button(dialog, text=use_label, command=accept).grid(row=4, column=0, padx=12, pady=12, sticky="e")
        dialog.bind("<Return>", lambda _event: accept())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(2, weight=1)
        filter_shooters()
        dialog.wait_window()
        schedule_save()
        return result[0]

    def refresh_generated_lines(record: dict[str, Any]) -> None:
        config = series_configs[record["_series"]]
        context = f"series.{record['_series']}.text"
        record["first_line"] = _render_template_or_error(config.first_line_template, record, config, f"{context}.first_line")
        record["second_line"] = _render_template_or_error(config.second_line_template, record, config, f"{context}.second_line")
        if config.third_line_template is not None:
            record["third_line"] = _render_template_or_error(config.third_line_template, record, config, f"{context}.third_line")
        if config.fourth_line_template is not None:
            record["fourth_line"] = _render_template_or_error(config.fourth_line_template, record, config, f"{context}.fourth_line")

    def refresh_rows(select_index: int | None = None) -> None:
        table.set_items([
            (
                str(index),
                tuple(get(record, col) for col in COLS),
                None,
                ("template-error",) if any(
                    str(record.get(field, "")).startswith("<błąd:")
                    for field in ("first_line", "second_line", "third_line", "fourth_line")
                ) else (),
            )
            for index, record in enumerate(rows)
        ])
        update_recalculate_button()
        if select_index is not None and tree.exists(str(select_index)):
            tree.selection_set(str(select_index))
            tree.focus(str(select_index))

    def get(record: dict[str, Any], col: str) -> Any:
        if col == "series":
            return record["_series"]
        if col in SHOOTER_FIELDS:
            return record.get("shooter", {}).get(SHOOTER_FIELDS[col], "")
        return record.get(TEXT_FIELDS.get(col, col), "")

    def put(record: dict[str, Any], col: str, value: str) -> None:
        if col == "series":
            record["_series"] = value
        elif col in SHOOTER_FIELDS:
            record.setdefault("shooter", {})[SHOOTER_FIELDS[col]] = value
        else:
            record[TEXT_FIELDS.get(col, col)] = value

    def has_manual_diploma_edits() -> bool:
        return diplomas_restored or rows != generated_rows

    def save_manual_diplomas(previous_rows: list[dict[str, Any]]) -> None:
        nonlocal data, rows
        try:
            if diploma_file is None:
                raise OSError("No diploma data file selected")
            _save_diploma_rows(diploma_file, rows)
            data = _diploma_data(rows)
        except (OSError, yaml.YAMLError) as exc:
            rows = previous_rows
            messagebox.showerror(error, str(exc), parent=root)

    def recalculate_after_config_change() -> None:
        if has_manual_diploma_edits() and not messagebox.askyesno(
            extra["edit_shooters"], extra["recalculate_prompt"], parent=root
        ):
            set_diplomas_stale(extra["config_pending_status"])
        else:
            regenerate_diplomas()

    def update_recalculate_button() -> None:
        if recalculate_button is None:
            return
        has_manual_edits = has_manual_diploma_edits()
        should_enable = data is not None and bool(shooter_summary) and (has_manual_edits or diplomas_stale)
        recalculate_button.state(["!disabled"] if should_enable else ["disabled"])
        recalculate_button.configure(style="Stale.TButton" if should_enable else "TButton")
        if recalculate_frame is not None:
            recalculate_frame.configure(background="#ef6c00" if should_enable else root.cget("background"))

    def set_diplomas_stale(message: str | None = None) -> None:
        nonlocal diplomas_stale
        diplomas_stale = True
        update_recalculate_button()
        if message:
            status.set(message)

    def regenerate_diplomas() -> bool:
        nonlocal data, rows, generated_rows, diplomas_stale, diplomas_restored, series_configs
        config_path = Path(paths["config"].get()) if paths["config"].get() else None
        if match_definition is None or config_path is None or not config_path.is_file():
            return False
        try:
            if config_buffer is None or config_loaded_path != str(config_path.resolve()):
                if not load_config_source(str(config_path)):
                    return False
            configs = load_config_text(config_buffer or "", str(config_path))
            replacement = generate_diplomas(shooter_summary, match_definition, configs)
            replacement_rows = _diploma_rows(replacement)
            if diploma_file is not None:
                _save_diploma_rows(diploma_file, replacement_rows)
        except Exception as exc:
            messagebox.showerror(error, str(exc), parent=root)
            return False
        series_configs = configs
        data = replacement
        rows = replacement_rows
        generated_rows = deepcopy(rows)
        diplomas_stale = False
        diplomas_restored = False
        refresh_rows()
        status.set(empty if not rows else loaded.format(len(rows)))
        return True

    def choose_summary_source(pcs_path: Path, pcs_time: str, summary_path: Path, summary_time: str) -> str | None:
        dialog = tk.Toplevel(root)
        dialog.title(extra["parse_source_title"])
        dialog.transient(root)
        dialog.resizable(False, False)
        dialog.grab_set()
        result: list[str | None] = [None]
        ttk.Label(dialog, text=extra["parse_source_prompt"]).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 10), sticky="w")
        def choose(source: str) -> None:
            result[0] = source
            dialog.destroy()
        ttk.Button(dialog, text=extra["use_pcs"].format(pcs_time), command=lambda: choose("pcs")).grid(row=1, column=0, padx=10, pady=(8, 3), sticky="ew")
        ttk.Button(dialog, text=extra["use_summary"].format(summary_time), command=lambda: choose("summary")).grid(row=1, column=1, padx=10, pady=(8, 3), sticky="ew")
        ttk.Label(dialog, text=extra["source_path"].format(pcs_path.resolve()), wraplength=420, justify="left").grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nw")
        ttk.Label(dialog, text=extra["source_path"].format(summary_path.resolve()), wraplength=420, justify="left").grid(row=2, column=1, padx=10, pady=(0, 10), sticky="nw")
        ttk.Button(dialog, text=extra["cancel_label"], command=dialog.destroy).grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 12), sticky="e")
        dialog.columnconfigure(0, weight=1)
        dialog.columnconfigure(1, weight=1)
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.wait_window()
        return result[0]

    def process_selected_match(*_args) -> None:
        nonlocal match_definition, shooter_summary, summary_file, diploma_file, diplomas_stale
        nonlocal data, rows, generated_rows, diplomas_restored, series_configs, active_match_path
        selected = Path(paths["match"].get()) if paths["match"].get() else None
        if selected is None or not selected.is_file():
            return
        try:
            match = load_match_data(selected)
            candidate_definition = dict(match.definition)
            candidate_summary_file = _match_output_path("shooters-summary", match.definition.get("match_name"))
            parsed_summary = parse_match_data(match)
            summary = None
            if candidate_summary_file.is_file():
                pcs_time = datetime.fromtimestamp(selected.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                summary_time = datetime.fromtimestamp(candidate_summary_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                try:
                    existing_summary = yaml.safe_load(candidate_summary_file.read_text(encoding="utf-8"))
                    if not isinstance(existing_summary, dict) or not all(isinstance(k, str) and isinstance(v, dict) for k, v in existing_summary.items()):
                        raise ValueError("Shooter summary must be a mapping of UID to shooter records")
                    migrated_summary = _upgrade_legacy_summary(existing_summary, parsed_summary)
                except Exception as exc:
                    raise ValueError(f"{candidate_summary_file}: {exc}") from exc
                if _summaries_equal(parsed_summary, migrated_summary):
                    summary = migrated_summary
                    if migrated_summary != existing_summary:
                        _write_yaml(candidate_summary_file, migrated_summary)
                else:
                    choice = choose_summary_source(selected, pcs_time, candidate_summary_file, summary_time)
                    if choice is None:
                        paths["match"].set(active_match_path)
                        last_selected["match"] = active_match_path
                        return
                    if choice == "summary":
                        summary = migrated_summary
                        if migrated_summary != existing_summary:
                            _write_yaml(candidate_summary_file, migrated_summary)
            if summary is None:
                summary = parsed_summary
                _write_yaml(candidate_summary_file, summary)
            candidate_file = _match_output_path("diplomas-data", match.definition.get("match_name"))
            saved_rows = _load_diploma_rows(candidate_file) if candidate_file.is_file() else None
            baseline = []
            differs = saved_rows is not None
            candidate_configs = {}
            should_regenerate = saved_rows is None
            config_path = paths["config"].get()
            if config_path and Path(config_path).is_file():
                try:
                    candidate_configs = load_config_text(config_buffer or "", config_path)
                    if saved_rows is not None:
                        baseline, differs = _compare_restored_diplomas(
                            saved_rows, summary, candidate_definition, candidate_configs
                        )
                        if differs:
                            choice = _choose_diploma_source(root, candidate_file, extra)
                            if choice is None:
                                paths["match"].set(active_match_path)
                                last_selected["match"] = active_match_path
                                return
                            should_regenerate = choice == "regenerate"
                except Exception as exc:
                    messagebox.showerror(error, str(exc), parent=root)
            match_definition = candidate_definition
            summary_file = candidate_summary_file
            active_match_path = str(selected)
            shooter_summary = summary
            diploma_file = candidate_file
            rows = saved_rows if saved_rows is not None else []
            generated_rows = baseline
            data = _diploma_data(rows) if saved_rows is not None else None
            diplomas_restored = differs
            diplomas_stale = False
            series_configs = candidate_configs
            refresh_rows()
            if saved_rows is not None:
                if diplomas_restored:
                    status.set(extra["restored_status"].format(diploma_file.resolve()))
                else:
                    status.set(empty if not rows else loaded.format(len(rows)))
            if should_regenerate:
                diplomas_stale = saved_rows is None
                regenerate_diplomas()
        except Exception as exc:
            paths["match"].set(active_match_path)
            last_selected["match"] = active_match_path
            messagebox.showerror(error, str(exc), parent=root)

    def load():
        if not shooter_summary:
            process_selected_match()
            return
        if not (diplomas_stale or has_manual_diploma_edits()):
            return
        if not messagebox.askyesno(
            extra["edit_shooters"], extra["recalculate_prompt"], parent=root
        ):
            return
        regenerate_diplomas()

    def edit_shooters(initial_search: str = "") -> None:
        nonlocal shooter_summary, diplomas_stale
        if not shooter_summary or summary_file is None:
            messagebox.showinfo(title, ready, parent=root)
            return
        dialog = tk.Toplevel(root)
        dialog.title(extra["edit_shooters"])
        dialog.geometry("1100x700")
        dialog.minsize(900, 560)
        dialog.grab_set()

        def maximize_editor() -> None:
            if not dialog.winfo_exists():
                return
            try:
                dialog.state("zoomed")
            except tk.TclError:
                try:
                    dialog.attributes("-zoomed", True)
                except tk.TclError:
                    pass

        dialog.after(100, maximize_editor)

        fields = ("shooter_id", "first_name", "last_name", "division", "categories", "class", "raw_time", "penalties", "points_down", "steel_misses", "penalty_seconds", "total_time", "dnf", "chrono_failure", "dq")
        columns = ("uid",) + fields
        headings = {field: extra.get(field, field.replace("_", " ").title()) for field in columns}
        original = deepcopy(shooter_summary)
        edited = deepcopy(shooter_summary)
        search = tk.StringVar(value=initial_search)
        ttk.Label(dialog, text=extra["search"]).grid(row=0, column=0, padx=12, pady=(12, 3), sticky="w")
        search_box = ttk.Entry(dialog, textvariable=search)
        search_box.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        table_frame = ttk.Frame(dialog)
        table_frame.grid(row=2, column=0, padx=12, pady=4, sticky="nsew")
        view = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        view.tag_configure("modified", background="#fff0d9")
        for field in columns:
            view.heading(field, text=headings[field])
            view.column(field, width=150 if field in {"uid", "categories", "penalties"} else 115, minwidth=75, stretch=True)
        view.pack(side="left", fill="both", expand=True)

        calculated_fields = ("penalty_seconds", "total_time")
        calculated_view = ttk.Treeview(
            table_frame, columns=calculated_fields, show="headings", selectmode="browse", height=1,
            style="Calculated.Treeview",
        )
        calculated_view.tag_configure("calculated", foreground="#777777", background="#f1f1f1")
        for field in calculated_fields:
            calculated_view.heading(field, text=f"{headings[field]} (wyliczone)")
            calculated_view.column(field, width=150, minwidth=120, stretch=False, anchor="e")
        calculated_view.pack(side="right", fill="y")

        vertical = ttk.Scrollbar(dialog, orient="vertical")
        vertical.grid(row=2, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(dialog, orient="horizontal", command=view.xview)
        horizontal.grid(row=3, column=0, padx=12, sticky="ew")
        syncing_scroll = False
        def sync_scroll_from_main(first, last):
            nonlocal syncing_scroll
            vertical.set(first, last)
            if not syncing_scroll:
                syncing_scroll = True
                calculated_view.yview_moveto(first)
                syncing_scroll = False
        def sync_scroll_from_calculated(first, last):
            nonlocal syncing_scroll
            if not syncing_scroll:
                syncing_scroll = True
                view.yview_moveto(first)
                syncing_scroll = False
            vertical.set(first, last)
        def scroll_both(*args):
            view.yview(*args)
            calculated_view.yview(*args)
        vertical.configure(command=scroll_both)
        view.configure(yscrollcommand=sync_scroll_from_main, xscrollcommand=horizontal.set)
        calculated_view.configure(yscrollcommand=sync_scroll_from_calculated)
        saved_tables = settings.get("tables", {})
        shooter_editor_state = saved_tables.get("shooter_editor", {}) if isinstance(saved_tables, dict) else {}
        editor_table = _FilterableTable(view, columns, headings, extra, shooter_editor_state, schedule_save)
        # Keep these values in the shared sort/filter model, but render them in the
        # adjacent view so their cells can have a muted, read-only style.
        for field in calculated_fields:
            view.column(field, width=0, minwidth=0, stretch=False)
        table_controllers["shooter_editor"] = editor_table

        selection_sync = False
        def sync_selection(source, destination):
            nonlocal selection_sync
            if selection_sync:
                return
            selected = tuple(iid for iid in source.selection() if destination.exists(iid))
            current = tuple(destination.selection())
            if selected == current:
                return
            selection_sync = True
            try:
                if current:
                    destination.selection_remove(*current)
                if selected:
                    destination.selection_add(*selected)
            finally:
                selection_sync = False
        view.bind("<<TreeviewSelect>>", lambda _event: sync_selection(view, calculated_view), add="+")
        calculated_view.bind("<<TreeviewSelect>>", lambda _event: sync_selection(calculated_view, view), add="+")

        def refresh_calculated_view(visible_items):
            nonlocal syncing_scroll
            was_syncing = syncing_scroll
            syncing_scroll = True
            try:
                old_items = calculated_view.get_children()
                if old_items:
                    calculated_view.delete(*old_items)
                for item in visible_items:
                    iid, values = item[0], item[1]
                    calculated_view.insert(
                        "", "end", iid=iid,
                        values=tuple(str(values[columns.index(field)]) for field in calculated_fields),
                        tags=("calculated",),
                    )
            finally:
                syncing_scroll = was_syncing
            for field in calculated_fields:
                indicator = "  ●" if field in editor_table.filters else ""
                calculated_view.heading(field, text=f"{headings[field]} (wyliczone)  ▾{indicator}", command=lambda column=field: editor_table._show_menu(column))
            if not was_syncing:
                calculated_view.yview_moveto(view.yview()[0])
            sync_selection(view, calculated_view)
        editor_table.after_refresh = refresh_calculated_view

        def display_value(uid: str, field: str, calculated: dict[str, Any] | None = None, baseline_calculated: dict[str, Any] | None = None) -> str | _CellDisplay:
            record = edited[uid]
            if calculated is None:
                calculated = derive_score_fields(record, edited.get(SUMMARY_OPTIONS_KEY, {}))
            value = calculated.get(field) if field in {"penalty_seconds", "total_time"} else record.get(field, False if field in {"dnf", "chrono_failure", "dq"} else {} if field == "penalties" else [] if field == "categories" else "")
            if field == "categories":
                text = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
            elif field == "penalties":
                text = ", ".join(f"{name}: {count}" for name, count in value.items()) if isinstance(value, dict) else str(value)
            elif field in {"dnf", "chrono_failure", "dq"}:
                text = "☑" if value else "☐"
            else:
                text = str(value)
            baseline_record = original.get(uid, {})
            if baseline_calculated is None:
                baseline_calculated = derive_score_fields(baseline_record, original.get(SUMMARY_OPTIONS_KEY, {}))
            baseline = baseline_calculated.get(field) if field in {"penalty_seconds", "total_time"} else baseline_record.get(field, False if field in {"dnf", "chrono_failure", "dq"} else {} if field == "penalties" else [] if field == "categories" else "")
            if field in {"penalty_seconds", "total_time"}:
                return text
            return _CellDisplay(text, f"🟠 {text}") if value != baseline else text

        def rebuild_items(*_args) -> None:
            nonlocal syncing_scroll
            visible_uids = _filtered_shooter_uids(edited, search.get())
            items = []
            for uid in visible_uids:
                calculated = derive_score_fields(edited[uid], edited.get(SUMMARY_OPTIONS_KEY, {}))
                baseline_calculated = derive_score_fields(original.get(uid, {}), original.get(SUMMARY_OPTIONS_KEY, {}))
                values = (uid, *(display_value(uid, field, calculated, baseline_calculated) for field in fields))
                tags = ("modified",) if any(edited[uid].get(field) != original.get(uid, {}).get(field) for field in fields if field not in {"penalty_seconds", "total_time"}) else ()
                items.append((uid, values, None, tags))
            syncing_scroll = True
            try:
                editor_table.set_items(items)
            finally:
                syncing_scroll = False
            if view.get_children():
                calculated_view.yview_moveto(view.yview()[0])

        search.trace_add("write", rebuild_items)
        rebuild_items()
        if initial_search and view.exists(initial_search):
            view.selection_set(initial_search)
            view.see(initial_search)
        search_box.focus_set()
        search_box.icursor("end")

        match_options = edited.get(SUMMARY_OPTIONS_KEY, {})
        divisions = list(match_options.get("divisions", []))
        classes = list(match_options.get("classes", []))
        categories = list(match_options.get("categories", []))
        penalty_types = sorted({str(name) for record in edited.values() for name in record.get("penalties", {})}, key=str.casefold)
        penalty_values = match_options.get("penalty_values", {}) if isinstance(match_options, dict) else {}
        if not isinstance(penalty_values, dict):
            penalty_values = {}

        def refresh_record(uid: str) -> None:
            calculated = derive_score_fields(edited[uid], edited.get(SUMMARY_OPTIONS_KEY, {}))
            baseline_calculated = derive_score_fields(original.get(uid, {}), original.get(SUMMARY_OPTIONS_KEY, {}))
            values = (uid, *(display_value(uid, field, calculated, baseline_calculated) for field in fields))
            tags = ("modified",) if any(edited[uid].get(field) != original.get(uid, {}).get(field) for field in fields if field not in {"penalty_seconds", "total_time"}) else ()
            editor_table.items = [
                (item_uid, values if item_uid == uid else item_values, image, tags if item_uid == uid else (item[3] if len(item) > 3 else ()))
                for item in editor_table.items
                for item_uid, item_values, image in [item[:3]]
            ]
            editor_table.refresh()

        def edit_penalties(uid: str) -> None:
            penalty_dialog = tk.Toplevel(dialog)
            penalty_dialog.title(extra["penalties"])
            penalty_dialog.transient(dialog)
            penalty_dialog.grab_set()
            current = edited[uid].get("penalties", {})
            entries: dict[str, ttk.Spinbox] = {}
            ttk.Label(penalty_dialog, text=f"{edited[uid].get('first_name', '')} {edited[uid].get('last_name', '')}").grid(row=0, column=0, columnspan=2, padx=14, pady=10, sticky="w")
            for index, name in enumerate(sorted(set(penalty_types) | set(current), key=str.casefold), start=1):
                ttk.Label(penalty_dialog, text=_penalty_label(name, penalty_values)).grid(row=index, column=0, padx=14, pady=4, sticky="w")
                count = ttk.Spinbox(penalty_dialog, from_=0, to=9999, width=8)
                count.set(str(current.get(name, 0)))
                count.grid(row=index, column=1, padx=14, pady=4, sticky="e")
                entries[name] = count
            actions = ttk.Frame(penalty_dialog)
            actions.grid(row=len(entries) + 1, column=0, columnspan=2, padx=12, pady=12, sticky="ew")
            def save_penalties() -> None:
                try:
                    values = {name: int(widget.get()) for name, widget in entries.items()}
                    if any(value < 0 for value in values.values()):
                        raise ValueError("Penalty counts must be non-negative integers")
                except ValueError as exc:
                    messagebox.showerror(error, str(exc), parent=penalty_dialog)
                    return
                edited[uid]["penalties"] = values
                refresh_record(uid)
                penalty_dialog.destroy()
            ttk.Button(actions, text=extra["cancel_label"], command=penalty_dialog.destroy).pack(side="left")
            ttk.Button(actions, text=extra["save_shooters"], command=save_penalties).pack(side="right")
            penalty_dialog.bind("<Escape>", lambda _event: penalty_dialog.destroy())
            penalty_dialog.wait_window()

        def edit_categories(uid: str) -> None:
            category_dialog = tk.Toplevel(dialog)
            category_dialog.title(extra["categories"])
            category_dialog.geometry("500x620")
            category_dialog.minsize(380, 360)
            category_dialog.transient(dialog)
            category_dialog.grab_set()
            current_values = edited[uid].get("categories", [])
            if not isinstance(current_values, list):
                current_values = []
            options = sorted(set(categories) | {str(value) for value in current_values}, key=str.casefold)
            ttk.Label(
                category_dialog,
                text=f"{edited[uid].get('first_name', '')} {edited[uid].get('last_name', '')}",
            ).grid(row=0, column=0, columnspan=2, padx=14, pady=(12, 6), sticky="w")

            list_frame = ttk.Frame(category_dialog)
            list_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=6, sticky="nsew")
            canvas = tk.Canvas(list_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            choices_frame = ttk.Frame(canvas)
            window_id = canvas.create_window((0, 0), window=choices_frame, anchor="nw")
            choices_frame.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")
            list_frame.columnconfigure(0, weight=1)
            list_frame.rowconfigure(0, weight=1)

            chosen = {value: tk.BooleanVar(value=value in current_values) for value in options}
            for index, value in enumerate(options):
                ttk.Checkbutton(choices_frame, text=value, variable=chosen[value]).grid(row=index, column=0, padx=8, pady=3, sticky="w")

            quick_actions = ttk.Frame(category_dialog)
            quick_actions.grid(row=2, column=0, columnspan=2, padx=12, sticky="ew")
            ttk.Button(quick_actions, text=extra["select_all"], command=lambda: [variable.set(True) for variable in chosen.values()]).pack(side="left")
            ttk.Button(quick_actions, text=extra["select_none"], command=lambda: [variable.set(False) for variable in chosen.values()]).pack(side="left", padx=6)

            actions = ttk.Frame(category_dialog)
            actions.grid(row=3, column=0, columnspan=2, padx=12, pady=12, sticky="ew")
            def save_categories() -> None:
                edited[uid]["categories"] = [value for value in options if chosen[value].get()]
                category_dialog.destroy()
                dialog.after_idle(lambda: refresh_record(uid) if dialog.winfo_exists() else None)
            ttk.Button(actions, text=extra["cancel_label"], command=category_dialog.destroy).pack(side="left")
            ttk.Button(actions, text=extra["save_shooters"], command=save_categories).pack(side="right")
            category_dialog.columnconfigure(0, weight=1)
            category_dialog.rowconfigure(1, weight=1)
            category_dialog.bind("<Escape>", lambda _event: category_dialog.destroy())
            category_dialog.wait_window()

        def begin_edit(event):
            if view.identify("region", event.x, event.y) != "cell":
                return
            uid, colid = view.identify_row(event.y), view.identify_column(event.x)
            index = int(colid[1:]) - 1
            if not uid or index <= 0:
                return
            field = columns[index]
            if field in {"penalty_seconds", "total_time"}:
                return "break"
            box = view.bbox(uid, colid)
            if not box:
                return
            x, y, width, height = box
            if field == "penalties":
                edit_penalties(uid)
                return
            if field == "categories":
                edit_categories(uid)
                return
            if field in {"division", "class"}:
                values = divisions if field == "division" else classes
                current = str(edited[uid].get(field, ""))
                choices = list(values)
                if current and current not in choices:
                    choices.append(current)
                combo = ttk.Combobox(view, values=choices, state="readonly")
                combo.place(x=x, y=y, width=width, height=height)
                combo.set(current)
                combo.focus_set()
                def commit_combo(_event=None):
                    if combo.winfo_exists():
                        edited[uid][field] = combo.get()
                        combo.destroy()
                        refresh_record(uid)
                combo.bind("<<ComboboxSelected>>", commit_combo)
                combo.bind("<Return>", commit_combo)
                combo.bind("<Escape>", lambda _event: combo.destroy())
                def close_if_focus_left() -> None:
                    if not combo.winfo_exists():
                        return
                    try:
                        focused_path = str(combo.tk.call("focus"))
                    except tk.TclError:
                        focused_path = ""
                    combo_path = str(combo)
                    if not focused_path or (
                        focused_path != combo_path
                        and not focused_path.startswith(combo_path + ".popdown")
                    ):
                        commit_combo()
                combo.bind("<FocusOut>", lambda _event: combo.after(150, close_if_focus_left))
                combo.after_idle(lambda: combo.tk.call("ttk::combobox::Post", combo) if combo.winfo_exists() else None)
                return
            if field in {"dnf", "chrono_failure", "dq"}:
                variable = tk.BooleanVar(value=bool(edited[uid].get(field, False)))
                def update_checkbox() -> None:
                    edited[uid][field] = variable.get()
                    baseline = original.get(uid, {}).get(field, False)
                    text = "☑" if variable.get() else "☐"
                    view.set(uid, field, f"🟠 {text}" if variable.get() != baseline else text)
                    row_changed = any(edited[uid].get(name) != original.get(uid, {}).get(name) for name in fields if name not in {"penalty_seconds", "total_time"})
                    view.item(uid, tags=("modified",) if row_changed else ())
                check = ttk.Checkbutton(view, variable=variable, command=update_checkbox)
                check.place(x=x + max(0, (width - 24) // 2), y=y, width=24, height=height)
                check.focus_set()
                check.invoke()
                check.bind("<FocusOut>", lambda _event: check.destroy())
                return
            entry = ttk.Entry(view)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, str(edited[uid].get(field, "")))
            entry.focus_set()
            def commit(_event=None):
                if not entry.winfo_exists():
                    return
                value = entry.get().strip()
                try:
                    if field in {"raw_time", "points_down", "steel_misses"}:
                        number = Decimal(value or "0")
                        if not number.is_finite() or (field in {"points_down", "steel_misses"} and number != number.to_integral_value()):
                            raise ValueError("Enter a valid number")
                        edited[uid][field] = int(number) if number == number.to_integral_value() else float(number)
                    else:
                        edited[uid][field] = value
                except (InvalidOperation, ValueError) as exc:
                    messagebox.showerror(error, str(exc), parent=dialog)
                    entry.focus_set()
                    return
                entry.destroy()
                refresh_record(uid)
            entry.bind("<Return>", commit)
            entry.bind("<FocusOut>", commit)
            entry.bind("<Escape>", lambda _event: entry.destroy())
        def begin_picker(event):
            if view.identify("region", event.x, event.y) != "cell":
                return
            colid = view.identify_column(event.x)
            index = int(colid[1:]) - 1 if colid else -1
            if index > 0 and columns[index] in {"division", "class", "categories", "dnf", "chrono_failure", "dq"}:
                begin_edit(event)
                return "break"

        def begin_double_edit(event):
            if view.identify("region", event.x, event.y) == "cell":
                colid = view.identify_column(event.x)
                index = int(colid[1:]) - 1 if colid else -1
                if index > 0 and columns[index] not in {"division", "class", "categories", "dnf", "chrono_failure", "dq"}:
                    begin_edit(event)

        view.bind("<Button-1>", begin_picker, add="+")
        view.bind("<Double-1>", begin_double_edit)

        def save_summary() -> None:
            nonlocal shooter_summary, diplomas_stale
            try:
                for uid, record in edited.items():
                    if uid != SUMMARY_OPTIONS_KEY:
                        record.pop("penalty_seconds", None)
                        record.pop("total_time", None)
                _write_yaml(summary_file, edited)
            except Exception as exc:
                messagebox.showerror(error, str(exc), parent=dialog)
                return
            shooter_summary = deepcopy(edited)
            dialog.destroy()
            has_manual_diplomas = has_manual_diploma_edits()
            if has_manual_diplomas:
                if not messagebox.askyesno(
                    extra["edit_shooters"], extra["stale_warning"], parent=root
                ):
                    set_diplomas_stale(extra["stale_status"])
                    return
            if not regenerate_diplomas():
                set_diplomas_stale(extra["stale_status"])

        def request_close() -> None:
            has_unsaved_changes = any(
                edited.get(uid, {}) != record
                for uid, record in original.items()
            )
            if has_unsaved_changes:
                choice = messagebox.askyesnocancel(
                    extra["unsaved_title"], extra["unsaved_prompt"], parent=dialog
                )
                if choice is None:
                    return
                if choice:
                    save_summary()
                    return
            dialog.destroy()

        actions = ttk.Frame(dialog)
        actions.grid(row=4, column=0, padx=12, pady=12, sticky="ew")
        ttk.Button(actions, text=extra["cancel_label"], command=request_close).pack(side="left")
        ttk.Button(actions, text=extra["save_shooters"], command=save_summary).pack(side="right")
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(2, weight=1)
        dialog.bind("<Escape>", lambda _event: request_close())
        dialog.protocol("WM_DELETE_WINDOW", request_close)
        dialog.wait_window()
        table_controllers.pop("shooter_editor", None)

    def edit(event):
        if tree.identify_row(event.y) == "__new__":
            return
        if tree.identify("region", event.x, event.y) != "cell":
            return
        iid, colid = tree.identify_row(event.y), tree.identify_column(event.x)
        if not iid or not colid:
            return
        col_index = int(colid[1:]) - 1
        if col_index >= len(COLS):
            return
        col = COLS[col_index]
        box = tree.bbox(iid, colid)
        if not box:
            return
        x, y, width, height = box
        editor = ttk.Entry(tree)
        editor.place(x=x, y=y, width=width, height=height)
        editor.insert(0, str(tree.set(iid, col)))
        editor.focus_set()
        committed = False
        def commit(_event=None):
            nonlocal committed
            if committed:
                return
            committed = True
            value = editor.get()
            row_index = int(iid)
            previous_rows = deepcopy(rows)
            put(rows[row_index], col, value)
            save_manual_diplomas(previous_rows)
            editor.destroy()
            refresh_rows(row_index)
        editor.bind("<Return>", commit)
        editor.bind("<FocusOut>", commit)
        def cancel_edit(_event=None):
            nonlocal committed
            committed = True
            editor.destroy()
        editor.bind("<Escape>", cancel_edit)
    tree.bind("<Double-1>", edit)


    def add_row() -> None:
        if data is None or not shooter_summary:
            messagebox.showinfo(title, add_required, parent=root)
            return
        uid = choose_shooter()
        if uid is None:
            return
        source = {
            "_series": "",
            "place": 1,
            "first_line": "",
            "second_line": "",
            "third_line": "",
            "fourth_line": "",
            "shooter": {},
        }
        record = _new_diploma_row(source, uid, shooter_summary, ())
        previous_rows = deepcopy(rows)
        rows.append(record)
        save_manual_diplomas(previous_rows)
        refresh_rows(len(rows) - 1)

    def new_row_click(event):
        if tree.identify_row(event.y) == "__new__":
            add_row()
            return "break"

    tree.bind("<Button-1>", new_row_click, add="+")


    def change_shooter(index: int | None = None) -> None:
        if index is None:
            selection = tree.selection()
            if not selection:
                messagebox.showinfo(title, shooter_required, parent=root)
                return
            index = int(selection[0])
        uid = choose_shooter()
        if uid is None:
            return
        series_config = series_configs.get(rows[index]["_series"])
        group_by = series_config.group_by if series_config else ("division", "class", "category")
        previous_rows = deepcopy(rows)
        _assign_shooter(rows[index], uid, shooter_summary, group_by)
        if series_config:
            refresh_generated_lines(rows[index])
        save_manual_diplomas(previous_rows)
        refresh_rows(index)

    def action_for_row(action: str, event):
        row_id = action_trees[{"remove": 0, "switch": 1, "edit": 2}[action]].identify_row(event.y)
        if not row_id or row_id == "__new__":
            return "break"
        index = int(row_id)
        if action == "remove":
            shooter = rows[index].get("shooter", {})
            name = " ".join(str(shooter.get(key, "")) for key in ("first_name", "last_name")).strip()
            if messagebox.askyesno(
                extra["confirm_title"],
                extra["confirm_remove"].format(name=name, place=rows[index].get("place", "")),
                parent=root,
            ):
                previous_rows = deepcopy(rows)
                rows.pop(index)
                save_manual_diplomas(previous_rows)
                refresh_rows(min(index, len(rows) - 1) if rows else None)
        elif action == "switch":
            tree.selection_set(row_id)
            change_shooter(index)
        else:
            uid = str(rows[index].get("shooter", {}).get("shooter_uid", ""))
            edit_shooters(uid)
        return "break"

    for action_name, action_tree in zip(("remove", "switch", "edit"), action_trees):
        action_tree.bind("<Button-1>", lambda event, name=action_name: action_for_row(name, event))
        action_tree.bind(
            "<MouseWheel>",
            lambda event: (tree.yview_scroll(int(-event.delta / 120), "units"), "break")[1],
        )

    def generate(open_after: bool = False):
        if data is None:
            messagebox.showinfo(title, ready, parent=root)
            return
        if diplomas_stale:
            if not messagebox.askyesno(extra["edit_shooters"], extra["stale_warning"], parent=root):
                return
            if not regenerate_diplomas():
                return
        template, source = Path(paths["template"].get()), Path(paths["match"].get())
        ext = template.suffix.lower()
        suggested = _match_document_path("diplomas", source.stem).with_suffix(ext)
        output = filedialog.asksaveasfilename(title=save_title, initialfile=suggested.name,
            defaultextension=ext, filetypes=[("DOCX", "*.docx"), ("ODT", "*.odt"), ("PDF", "*.pdf")])
        if not output:
            return
        try:
            render_diploma_data(_diploma_data(rows), template, Path(output))
            status.set(saved.format(output))
            if open_after:
                try:
                    if os.name == "nt":
                        os.startfile(output)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", output])
                    else:
                        subprocess.Popen(["xdg-open", output])
                except Exception as exc:
                    messagebox.showerror(error, extra["open_error"].format(exc), parent=root)
            else:
                messagebox.showinfo(title, status.get(), parent=root)
        except Exception as exc:
            messagebox.showerror(error, str(exc), parent=root)

    button_style = ttk.Style(root)
    button_style.configure("Stale.TButton", background="#ffcc80", foreground="#5d3200")
    button_style.map("Stale.TButton", background=[("active", "#ffb74d")])
    # A Tk frame keeps the orange border visible under native Windows themes.
    # Reserve the same padding while disabled to avoid moving the controls.
    recalculate_frame = tk.Frame(root, background=root.cget("background"), padx=4, pady=4, borderwidth=0)
    recalculate_frame.grid(row=3, column=0, padx=9, pady=5, sticky="w")
    recalculate_button = ttk.Button(recalculate_frame, text=review_label, command=load, state="disabled")
    recalculate_button.pack()
    update_recalculate_button()
    generate_actions = ttk.Frame(root)
    generate_actions.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="e")
    ttk.Button(generate_actions, text=extra["generate_open"], command=lambda: generate(open_after=True)).pack(side="right")
    ttk.Button(generate_actions, text=generate_label, command=generate).pack(side="right", padx=(0, 6))
    if match_selector_host is not None:
        ttk.Button(
            match_selector_host,
            text=extra["edit_shooters_button"],
            command=edit_shooters,
        ).pack(side="right", padx=(6, 0))
    root.bind("<Configure>", schedule_save)

    def choose_unsaved_config_action() -> str:
        prompt = tk.Toplevel(root)
        prompt.title(extra["unsaved_config_title"])
        prompt.transient(root)
        prompt.grab_set()
        result = ["cancel"]
        ttk.Label(
            prompt,
            text=extra["unsaved_config_prompt"].format(config_loaded_path or paths["config"].get()),
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=4, padx=18, pady=(18, 12), sticky="w")
        actions = (
            ("save", extra["save_close"]),
            ("save_as", extra["save_as_close"]),
            ("discard", extra["discard_close"]),
            ("cancel", extra["cancel_close"]),
        )
        for col, (value, label) in enumerate(actions):
            ttk.Button(prompt, text=label, command=lambda choice=value: (result.__setitem__(0, choice), prompt.destroy())).grid(row=1, column=col, padx=6, pady=(0, 14), sticky="e")
        prompt.update_idletasks()
        width, height = prompt.winfo_reqwidth(), prompt.winfo_reqheight()
        x = max(0, (prompt.winfo_screenwidth() - width) // 2)
        y = max(0, (prompt.winfo_screenheight() - height) // 2)
        prompt.geometry(f"{width}x{height}+{x}+{y}")
        prompt.bind("<Escape>", lambda _event: prompt.destroy())
        prompt.protocol("WM_DELETE_WINDOW", prompt.destroy)
        prompt.wait_window()
        return result[0]

    def close_window() -> None:
        nonlocal save_job
        if config_is_dirty():
            choice = choose_unsaved_config_action()
            if choice == "cancel":
                return
            if choice == "save" and not save_config_buffer():
                return
            if choice == "save_as" and not save_config_buffer(save_as=True):
                return
        if save_job is not None:
            root.after_cancel(save_job)
            save_job = None
        save_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_window)
    if paths["config"].get() and paths["config"].get() != other_label:
        load_config_source(paths["config"].get())
    if paths["match"].get():
        process_selected_match()
    root.mainloop()
    return 0
