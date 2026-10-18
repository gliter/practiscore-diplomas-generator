from pathlib import Path
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
