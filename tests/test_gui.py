from pathlib import Path

import pytest
import yaml

import practiscore_diplomas.gui as gui
from practiscore_diplomas.gui import EXTRA, _upgrade_legacy_summary, _summaries_equal, _load_settings, _save_settings, _settings_path, _assign_shooter, _file_choices, _filtered_shooter_uids, _filter_sort_items, _matches_column_filters, _new_diploma_row, _next_place, _shooter_display_values, _penalty_label, _sort_value


def test_next_place_uses_highest_place_within_series():
    rows = [
        {"_series": "open", "place": 1},
        {"_series": "open", "place": 3},
        {"_series": "ladies", "place": 8},
        {"_series": "open", "place": "manual"},
    ]

    assert _next_place(rows, "open") == 4


def test_assign_shooter_replaces_full_shooter_record_without_aliasing():
    record = {"shooter": {"shooter_uid": "old", "first_name": "Old"}}
    summary = {
        "new": {
            "shooter_uid": "ignored",
            "first_name": "Alex",
            "last_name": "Example",
            "division": "Open",
            "class": "A",
            "categories": ["Lady"],
            "shooter_id": "42",
        }
    }

    _assign_shooter(record, "new", summary)
    record["shooter"]["first_name"] = "Edited"

    assert record["shooter"]["shooter_uid"] == "new"
    assert record["shooter"]["first_name"] == "Edited"
    assert summary["new"]["first_name"] == "Alex"


def test_assign_shooter_updates_explicit_grouping_context():
    record = {"division": "Old", "class": "B", "category": "Senior"}
    summary = {
        "new": {
            "division": "Open",
            "class": "A",
            "categories": ["Lady", "Senior"],
            "first_name": "Alex",
        }
    }

    _assign_shooter(record, "new", summary, ("division", "class", "category"))

    assert (record["division"], record["class"], record["category"]) == ("Open", "A", "Senior")


def test_shooter_search_matches_first_name_surname_and_class():
    summary = {
        "uid-a": {"first_name": "Anna", "last_name": "Example", "class": "A"},
        "uid-b": {"first_name": "Boris", "last_name": "Shooter", "class": "B"},
    }

    assert _filtered_shooter_uids(summary, "ann") == ["uid-a"]
    assert _filtered_shooter_uids(summary, "SHOOT") == ["uid-b"]
    assert _filtered_shooter_uids(summary, " b ") == ["uid-b"]


def test_shooter_search_matches_division_and_category():
    summary = {
        "uid": {"first_name": "Alex", "last_name": "Example", "division": "Production", "categories": ["Senior", "Lady"], "class": "A"},
    }

    assert _filtered_shooter_uids(summary, "production") == ["uid"]
    assert _filtered_shooter_uids(summary, "senior") == ["uid"]
    assert _filtered_shooter_uids(summary, "lady") == ["uid"]



def test_file_choices_list_matching_files_and_other_option(tmp_path: Path):
    (tmp_path / "match-b.pcs").write_bytes(b"")
    (tmp_path / "match-a.pcs").write_bytes(b"")
    (tmp_path / "match-c.zip").write_bytes(b"")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    choices = _file_choices(tmp_path, ("*.pcs", "*.psc", "*.zip"), "Choose another file…")

    assert choices == [
        str((tmp_path / "match-a.pcs").resolve()),
        str((tmp_path / "match-b.pcs").resolve()),
        str((tmp_path / "match-c.zip").resolve()),
        "Choose another file…",
    ]


def test_file_choices_allow_missing_search_directory(tmp_path: Path):
    assert _file_choices(tmp_path / "missing", ("*.docx", "*.odt"), "Other") == ["Other"]


def test_shooter_search_matches_uid():
    summary = {
        "competitor-42": {"first_name": "Alex", "last_name": "Example"},
        "competitor-99": {"first_name": "Sam", "last_name": "Sample"},
    }

    assert _filtered_shooter_uids(summary, "42") == ["competitor-42"]


def test_shooter_display_values_include_identity_grouping_and_score():
    shooter = {
        "first_name": "Anna", "last_name": "Example", "division": "Production",
        "categories": ["Lady", "Senior"], "class": "B", "total_time": "42.5",
        "points_down": 12, "steel_misses": 1,
    }

    values = _shooter_display_values(shooter, EXTRA["en"])

    assert values[:5] == ("Anna", "Example", "Production", "Lady, Senior", "B")
    assert "Total time: 42.5" in values[5]
    assert "Points down: 12" in values[5]


def test_column_filters_combine_case_insensitive_contains_checks():
    values = {"division": "Production Optics", "category": "Lady, Senior", "place": 1}

    assert _matches_column_filters(values, {"division": "optics", "category": "senior"})
    assert not _matches_column_filters(values, {"division": "optics", "category": "junior"})


def test_sort_values_sort_numbers_numerically():
    assert _sort_value("2") < _sort_value("10")
    assert _sort_value("Alpha") < _sort_value("bravo")


def test_shared_table_filters_allow_multiple_values_and_sort():
    items = [
        ("one", ("Production", "10"), None),
        ("two", ("Production", "2"), None),
        ("three", ("Open", "1"), None),
    ]

    shown = _filter_sort_items(
        items,
        ("division", "place"),
        {"division": frozenset({"Production", "Open"})},
        "place",
        False,
    )

    assert [item[0] for item in shown] == ["three", "two", "one"]


def test_added_diploma_row_clears_non_shooter_fields_and_uses_new_shooter_data():
    source = {
        "_series": "open", "place": 1, "division": "Old division", "category": "Old",
        "class": "Old class", "metric_value": 99, "first_line": "Old award",
        "second_line": "Old rank", "third_line": "Old third", "fourth_line": "Old fourth",
        "shooter": {"shooter_uid": "old", "first_name": "Old"},
    }
    summary = {
        "new": {"first_name": "Alex", "last_name": "Example", "division": "Production", "class": "A", "categories": ["Senior"], "shooter_id": "14"},
    }

    row = _new_diploma_row(source, "new", summary, ())

    assert row["_series"] == ""
    assert row["place"] == 1
    assert row["shooter"]["shooter_uid"] == "new"
    assert (row["division"], row["class"], row["category"]) == ("Production", "A", "Senior")
    assert row["metric_value"] is None
    assert row["first_line"] == row["second_line"] == row["third_line"] == row["fourth_line"] == ""
    assert source["first_line"] == "Old award"


def test_settings_file_round_trips_json_state(tmp_path: Path):
    path = tmp_path / "settings.json"
    state = {"version": 1, "last_files": {"match": "match.pcs"}, "tables": {"diplomas": {"filters": {"series": ["open"]}}}}

    _save_settings(path, state)

    assert _load_settings(path) == state


def test_settings_loader_ignores_invalid_or_unsupported_files(tmp_path: Path):
    path = tmp_path / "settings.json"
    path.write_text("not json", encoding="utf-8")
    assert _load_settings(path) == {"version": 1}
    path.write_text('{"version": 99}', encoding="utf-8")
    assert _load_settings(path) == {"version": 1}


def test_settings_path_uses_windows_roaming_appdata(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert _settings_path() == tmp_path / "PractiScore Diplomas" / "settings.json"


def test_legacy_summary_migration_separates_chrono_failure_from_dnf():
    old = {"one": {"dnf": True}, "two": {"dnf": True}, "three": {"dnf": False}}
    parsed = {
        "one": {"dnf": False, "chrono_failure": True},
        "two": {"dnf": True, "chrono_failure": True},
        "three": {"dnf": False, "chrono_failure": False},
        "_match_options": {"divisions": [], "categories": [], "classes": [], "penalty_values": {}, "points_down_value": 0, "steel_miss_pd_count": 0},
    }

    upgraded = _upgrade_legacy_summary(old, parsed)

    assert upgraded["one"] == {"dnf": False, "chrono_failure": True}
    assert upgraded["two"] == {"dnf": True, "chrono_failure": True}
    assert upgraded["three"] == {"dnf": False, "chrono_failure": False}
    assert old["one"]["dnf"] is True


def test_summary_comparison_ignores_mapping_key_order():
    left = {"uid-a": {"first_name": "Alex", "dnf": False}, "uid-b": {"first_name": "Bea", "dnf": True}}
    right = {"uid-b": {"dnf": True, "first_name": "Bea"}, "uid-a": {"dnf": False, "first_name": "Alex"}}

    assert _summaries_equal(left, right)
    assert not _summaries_equal(left, {**right, "uid-a": {"first_name": "Different", "dnf": False}})


def test_penalty_label_shows_match_value_in_seconds():
    assert _penalty_label("Miss", {"Miss": 5, "Procedural": 0.5}) == "Miss (5 s)"
    assert _penalty_label("Procedural", {"Miss": 5, "Procedural": 0.5}) == "Procedural (0.5 s)"
    assert _penalty_label("Legacy penalty", {"Miss": 5}) == "Legacy penalty"


def test_diploma_snapshot_restores_manual_edits_added_removed_and_switched_rows(tmp_path):
    path = tmp_path / "results" / "diplomas.yaml"
    rows = [
        {"_series": "division", "place": 2, "first_line": "Original", "shooter": {"shooter_uid": "one"}},
        {"_series": "division", "place": 1, "first_line": "Winner", "shooter": {"shooter_uid": "two"}},
    ]
    gui._save_diploma_rows(path, rows)
    edited = gui._load_diploma_rows(path)
    edited[0]["first_line"] = "Ręcznie poprawiony tekst"
    edited[0]["shooter"] = {"shooter_uid": "other", "first_name": "Alex"}
    edited.pop(1)
    edited.append({"_series": "", "place": 1, "first_line": "", "shooter": {"shooter_uid": "new"}})

    gui._save_diploma_rows(path, edited)
    restored = gui._load_diploma_rows(path)

    assert restored == edited
    assert restored[0]["first_line"] == "Ręcznie poprawiony tekst"
    assert restored[0]["shooter"]["shooter_uid"] == "other"
    assert restored[1]["_series"] == ""
    assert rows[0]["first_line"] == "Original"
    persisted = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "_series" not in persisted["diplomas"]["division"][0]
    assert list(persisted["diplomas"]) == ["division", ""]


def test_diploma_snapshot_preserves_an_intentionally_empty_table(tmp_path):
    path = tmp_path / "diplomas.yaml"
    gui._save_diploma_rows(path, [{"_series": "award", "place": 1}])
    gui._save_diploma_rows(path, [])

    assert path.is_file()
    assert gui._load_diploma_rows(path) == []
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == {"diplomas": {}}


def test_failed_diploma_snapshot_save_preserves_the_previous_file(monkeypatch, tmp_path):
    path = tmp_path / "diplomas.yaml"
    original = [{"_series": "award", "place": 1, "first_line": "Keep this"}]
    gui._save_diploma_rows(path, original)

    def fail_replace(*args):
        raise PermissionError("File is locked")

    monkeypatch.setattr(gui.os, "replace", fail_replace)
    with pytest.raises(PermissionError):
        gui._save_diploma_rows(path, [])

    assert gui._load_diploma_rows(path) == original
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("data", [None, [], {}, {"diplomas": []}, {"diplomas": {"award": {}}}, {"diplomas": {"award": [None]}}, {"diplomas": {"award": [{"shooter": []}]}}])
def test_malformed_diploma_snapshots_are_rejected_without_changing_the_file(tmp_path, data):
    path = tmp_path / "diplomas.yaml"
    content = yaml.safe_dump(data)
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        gui._load_diploma_rows(path)

    assert path.read_text(encoding="utf-8") == content


@pytest.mark.parametrize("edit", ["none", "text", "remove"])
def test_restored_diplomas_are_compared_with_current_awards_without_overwriting(tmp_path, edit):
    configs = gui.load_config_text("""
series:
  award:
    type: best_shooter
    min_competitors: [1]
    text:
      first_line: "{{ shooter.first_name }}"
      second_line: "{{ place }}"
""")
    summary = {"uid": {"first_name": "Alex", "last_name": "Example", "raw_time": 12, "total_time": 12, "points_down": 0, "steel_misses": 0, "categories": [], "penalties": {}}}
    definition = {"match_penalties": []}
    original = gui._diploma_rows(gui.generate_diplomas(summary, definition, configs))
    path = tmp_path / "diplomas.yaml"
    gui._save_diploma_rows(path, original)
    saved = gui._load_diploma_rows(path)
    if edit == "text":
        saved[0]["first_line"] = "Manual award text"
    elif edit == "remove":
        saved.clear()
    gui._save_diploma_rows(path, saved)
    contents = path.read_bytes()

    baseline, differs = gui._compare_restored_diplomas(saved, summary, definition, configs)

    assert baseline == original
    assert differs is (edit != "none")
    assert path.read_bytes() == contents
    assert gui._load_diploma_rows(path) == saved


def test_empty_restored_diplomas_match_an_empty_generated_ranking():
    configs = gui.load_config_text("""
series:
  award:
    type: best_shooter
    min_competitors: [1]
    text:
      first_line: Award
      second_line: Place
""")

    baseline, differs = gui._compare_restored_diplomas([], {}, {}, configs)

    assert baseline == []
    assert differs is False


@pytest.mark.parametrize("action, expected", [("use_saved_diplomas", "saved"), ("regenerate_diplomas", "regenerate"), ("cancel_label", None), ("close", None), ("escape", None)])
def test_diploma_source_dialog_returns_explicit_choice_and_displays_path(monkeypatch, tmp_path, action, expected):
    messages = gui.EXTRA["pl"]
    labels = []
    buttons = {}
    callbacks = {}

    class Dialog:
        def __getattr__(self, name):
            if name.startswith("winfo_"):
                return lambda: 600
            return lambda *args, **kwargs: None

        def bind(self, event, callback):
            callbacks[event] = callback

        def protocol(self, event, callback):
            callbacks[event] = callback

        def wait_window(self):
            if action == "close":
                callbacks["WM_DELETE_WINDOW"]()
            elif action == "escape":
                callbacks["<Escape>"](None)
            else:
                buttons[messages[action]]()

    class Widget:
        def __init__(self, parent, text, command=None, **kwargs):
            if command is None:
                labels.append(text)
            else:
                buttons[text] = command

        def grid(self, **kwargs):
            pass

    monkeypatch.setattr(gui.tk, "Toplevel", lambda parent: Dialog())
    monkeypatch.setattr(gui.ttk, "Label", Widget)
    monkeypatch.setattr(gui.ttk, "Button", Widget)
    path = tmp_path / "diplomas.yaml"

    result = gui._choose_diploma_source(object(), path, messages)

    assert result == expected
    assert any(str(path.resolve()) in label for label in labels)
    assert messages["diploma_source_warning"] in labels
    assert not path.exists()
