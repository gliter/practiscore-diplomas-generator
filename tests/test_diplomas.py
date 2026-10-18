import pytest
import yaml

from practiscore_diplomas.diplomas import DiplomaDataError, generate_diplomas, load_config, load_config_text
from tests.test_parser import make_data


def config_file(tmp_path, text):
    path = tmp_path / "config.yaml"
    config = yaml.safe_load(text)
    for series in config.get("series", {}).values():
        series.setdefault("text", {"first_line": "{{ type }}", "second_line": "{{ place }}"})
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def test_generates_grouped_ranked_records_and_thresholds(tmp_path):
    data = make_data()
    summary = {
        "shooter-a": {**{k: v for k, v in {"shooter_uid": "shooter-a"}.items()}, **{
            "shooter_id": "GPA-001", "first_name": "Test", "last_name": "Zulu", "division": "FSO", "class": "Gold", "categories": ["Senior"], "raw_time": 18, "penalties": {"Miss": 1, "Procedural Error": 1}, "points_down": 3, "steel_misses": 1, "total_time": 32.5, "dnf": False, "dq": False
        }},
        "shooter-b": {"shooter_id": "GPA-002", "first_name": "Test", "last_name": "Alpha", "division": "FSO", "class": "Gold", "categories": ["Senior", "Lady"], "raw_time": 10, "penalties": {"Miss": 0, "Procedural Error": 0}, "points_down": 0, "steel_misses": 0, "total_time": 10, "dnf": False, "dq": False},
    }
    config = load_config(config_file(tmp_path, """series:
  best_shooter:
    type: best_shooter
    group_by: [division, class]
    filters:
      divisions: [FSO]
      classes: [Gold]
      categories: ['*']
    min_competitors: [1, 2]
"""))
    output = generate_diplomas(summary, data.definition, config)
    records = output["diplomas"]["best_shooter"]
    assert len(records) == 2
    assert [record["place"] for record in records] == [2, 1]
    assert records[-1]["division"] == "FSO"
    assert records[-1]["class"] == "Gold"
    assert records[-1]["category"] is None
    assert records[-1]["shooter"]["shooter_id"] == "GPA-002"
    assert records[-1]["first_line"] == "best_shooter"
    assert records[-1]["second_line"] == "1"
    assert "eligible_competitors" not in records[-1]
    assert "qualification_threshold" not in records[-1]


def test_category_membership_and_penalty_exclusion(tmp_path):
    data = make_data()
    summary = {
        "a": {"first_name": "A", "last_name": "Same", "division": "FSO", "class": "Gold", "categories": ["Senior", "Lady"], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {"Miss": 0}, "dnf": False, "dq": False},
        "b": {"first_name": "B", "last_name": "Beta", "division": "FSO", "class": "Gold", "categories": ["Lady"], "raw_time": 2, "total_time": 2, "points_down": 0, "steel_misses": 0, "penalties": {"Miss": 1}, "dnf": False, "dq": False},
    }
    config = load_config(config_file(tmp_path, """series:
  fastest:
    type: fastest
    group_by: [category]
    min_competitors: [1]
    ineligible_penalties: [Miss]
"""))
    output = generate_diplomas(summary, data.definition, config)["diplomas"]["fastest"]
    assert {(item["category"], item["shooter"]["first_name"]) for item in output} == {("Senior", "A"), ("Lady", "A")}


def test_rejects_invalid_thresholds(tmp_path):
    with pytest.raises(DiplomaDataError, match="min_competitors"):
        load_config(config_file(tmp_path, """series:
  bad:
    type: fastest
    min_competitors: [7, 5]
"""))


def test_filter_values_are_regular_expressions(tmp_path):
    config = load_config(config_file(tmp_path, """series:
  iron:
    type: fastest
    filters:
      divisions: [CPI.*]
    min_competitors: [0]
"""))
    assert config["iron"].filters["division"].include == ("CPI.*",)


def test_filter_values_support_include_and_exclude_regexes(tmp_path):
    data = make_data()
    summary = {
        "a": {"first_name": "A", "last_name": "A", "division": "FSO", "class": "Gold", "categories": ["Senior"], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
        "b": {"first_name": "B", "last_name": "B", "division": "FSO", "class": "Gold", "categories": ["Lady (Gender @ Birth)"], "raw_time": 2, "total_time": 2, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
    }
    config = load_config(config_file(tmp_path, """series:
  category:
    type: fastest
    group_by: [category]
    filters:
      categories:
        include: ['.*']
        exclude: ['Lady.*']
    min_competitors: [0]
"""))
    output = generate_diplomas(summary, data.definition, config)["diplomas"]["category"]
    assert [item["shooter"]["first_name"] for item in output] == ["A"]


def test_category_grouping_uses_only_categories_matching_the_series_filter(tmp_path):
    data = make_data()
    summary = {
        "a": {"first_name": "A", "last_name": "Alpha", "division": "FSO", "class": "Gold", "categories": ["Senior", "Lady"], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
        "b": {"first_name": "B", "last_name": "Beta", "division": "FSO", "class": "Gold", "categories": ["Lady"], "raw_time": 2, "total_time": 2, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
    }
    config = load_config(config_file(tmp_path, """series:
  best_lady:
    type: best_shooter
    group_by: [category]
    filters:
      categories:
        include: [Lady]
    min_competitors: [1, 2]
"""))

    output = generate_diplomas(summary, data.definition, config)["diplomas"]["best_lady"]

    assert [(item["category"], item["shooter"]["first_name"]) for item in output] == [("Lady", "B"), ("Lady", "A")]


def test_groups_sort_by_size_and_places_sort_from_last_to_first(tmp_path):
    data = make_data()
    summary = {}
    group_sizes = {"FSI": 4, "CSO": 2, "LCO": 1}
    for division, count in group_sizes.items():
        for index in range(count):
            uid = f"{division}-{index}"
            summary[uid] = {
                "first_name": uid,
                "last_name": uid,
                "division": division,
                "class": "A",
                "categories": [],
                "raw_time": index + 1,
                "total_time": index + 1,
                "points_down": 0,
                "steel_misses": 0,
                "penalties": {},
                "dnf": False,
                "dq": False,
            }
    config = load_config(config_file(tmp_path, """series:
  division:
    type: fastest
    group_by: [division]
    min_competitors: [1, 2, 3]
"""))

    records = generate_diplomas(summary, data.definition, config)["diplomas"]["division"]

    assert [(row["division"], row["place"]) for row in records] == [
        ("FSI", 3), ("FSI", 2), ("FSI", 1),
        ("CSO", 2), ("CSO", 1),
        ("LCO", 1),
    ]


def test_filters_and_filter_parts_are_optional(tmp_path):
    config = load_config(config_file(tmp_path, """series:
  all:
    type: fastest
    min_competitors: [0]
  excluded:
    type: fastest
    filters:
      divisions:
        exclude: [NFC.*]
    min_competitors: [0]
"""))
    assert config["all"].filters["division"].include == ("*",)
    assert config["all"].filters["division"].exclude == ()
    assert config["excluded"].filters["division"].include == ("*",)
    assert config["excluded"].filters["division"].exclude == ("NFC.*",)


def test_excludes_shooters_by_surname_or_id(tmp_path):
    data = make_data()
    summary = {
        "surname-match": {"first_name": "A", "last_name": "PAR", "shooter_id": "", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
        "id-match": {"first_name": "B", "last_name": "Other", "shooter_id": "GPA0", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 2, "total_time": 2, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
        "kept": {"first_name": "C", "last_name": "Kept", "shooter_id": "GPA1", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 3, "total_time": 3, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
    }
    config = load_config(config_file(tmp_path, """exclude_shooters:
  surnames: ['(?i)^par$']
  ids: ['GPA0']
series:
  fastest:
    type: fastest
    min_competitors: [0]
"""))
    output = generate_diplomas(summary, data.definition, config)["diplomas"]["fastest"]
    assert [item["shooter"]["first_name"] for item in output] == ["C"]


def test_chrono_setting_defaults_to_true(tmp_path):
    config = load_config(config_file(tmp_path, """series:
  fastest:
    type: fastest
    min_competitors: [0]
"""))
    assert config["fastest"].mark_chrono_failure_as_dnf is True


def test_rejects_invalid_filter_regular_expression(tmp_path):
    with pytest.raises(DiplomaDataError, match="regular expression"):
        load_config(config_file(tmp_path, """series:
  bad:
    type: fastest
    filters:
      divisions: ['[']
    min_competitors: [0]
"""))


def test_renders_global_maps_and_raw_variables(tmp_path):
    data = make_data()
    config = load_config(config_file(tmp_path, """maps:
      division_code:
        FSO.*: FSO
      place_text:
        1: WINNER
series:
  award:
    type: best_shooter
    group_by: [division]
    min_competitors: [0]
    text:
      first_line: '{{ division_code(division) }} DIVISION'
      second_line: '{{ place_text(place) }} {{ type }}'
      third_line: 'TIME {{ shooter.raw_time }} PD {{ shooter.points_down }}'
      fourth_line: '{{ shooter.last_name }} {{ shooter.shooter_id }}'
"""))
    summary = {"a": {"shooter_id": "ID-A", "first_name": "A", "last_name": "A", "division": "FSO (Full Size Optic)", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False}}
    record = generate_diplomas(summary, data.definition, config)["diplomas"]["award"][0]
    assert record["first_line"] == "FSO DIVISION"
    assert record["second_line"] == "WINNER best_shooter"
    assert record["third_line"] == "TIME 1 PD 0"
    assert record["fourth_line"] == "A ID-A"


def test_shooter_value_can_be_used_as_map_input(tmp_path):
    config = load_config(config_file(tmp_path, """maps:
  class_code:
    Gold.*: GOLD
series:
  award:
    type: fastest
    min_competitors: [0]
    text:
      first_line: '{{ class_code(shooter.class) }}'
      second_line: '{{ shooter.total_time }}'
"""))
    summary = {"a": {"first_name": "A", "last_name": "A", "shooter_id": "ID-1", "division": "FSO", "class": "Gold (78%)", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False}}
    record = generate_diplomas(summary, make_data().definition, config)["diplomas"]["award"][0]
    assert record["first_line"] == "GOLD"
    assert record["second_line"] == "1"


def test_requires_text_for_each_series(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("series:\n  missing:\n    type: fastest\n    min_competitors: [0]\n", encoding="utf-8")
    with pytest.raises(DiplomaDataError, match="text"):
        load_config(path)


def test_rejects_missing_map_entry(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("""maps:
  place_text:
    2: RUNNER-UP
series:
  award:
    type: fastest
    min_competitors: [0]
    text:
      first_line: '{{ place_text(place) }}'
      second_line: '{{ place_text(place) }}'
""", encoding="utf-8")
    config = load_config(path)
    summary = {"a": {"first_name": "A", "last_name": "A", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False}}
    records = generate_diplomas(summary, make_data().definition, config)["diplomas"]["award"]
    assert len(records) == 1
    assert records[0]["first_line"].startswith("<błąd: ")
    assert "no mapping" in records[0]["first_line"]
    assert records[0]["second_line"].startswith("<błąd: ")


def test_unknown_template_map_becomes_visible_line_error(tmp_path):
    config = load_config(config_file(tmp_path, """series:
  award:
    type: fastest
    min_competitors: [0]
    text:
      first_line: '{{ missing_map(division) }}'
      second_line: '{{ place }}'
"""))
    summary = {"a": {"first_name": "A", "last_name": "A", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False}}
    record = generate_diplomas(summary, make_data().definition, config)["diplomas"]["award"][0]
    assert record["first_line"].startswith("<błąd: ")
    assert record["first_line"] == "<błąd: unknown map 'missing_map'>"
    assert record["second_line"] == "1"


def test_unknown_template_field_becomes_visible_line_error(tmp_path):
    config = load_config(config_file(tmp_path, """series:
  award:
    type: fastest
    min_competitors: [0]
    text:
      first_line: '{{ shooter.last_nam }}'
      second_line: '{{ placement }}'
"""))
    summary = {"a": {"first_name": "A", "last_name": "A", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False}}
    record = generate_diplomas(summary, make_data().definition, config)["diplomas"]["award"][0]
    assert record["first_line"] == "<błąd: unknown shooter field 'last_nam'>"
    assert record["second_line"] == "<błąd: unknown field 'placement'>"


def test_chrono_failure_is_excluded_by_default_during_diploma_generation(tmp_path):
    data = make_data()
    summary = {"chrono": {"first_name": "A", "last_name": "A", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "chrono_failure": True, "dq": False}}
    config = load_config(config_file(tmp_path, """series:
  fastest:
    type: fastest
    min_competitors: [0]
"""))
    assert generate_diplomas(summary, data.definition, config)["diplomas"]["fastest"] == []


def test_chrono_failure_can_be_allowed_by_config(tmp_path):
    data = make_data()
    summary = {"chrono": {"first_name": "A", "last_name": "A", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "chrono_failure": True, "dq": False}}
    config = load_config(config_file(tmp_path, """mark_chrono_failure_as_dnf: false
series:
  fastest:
    type: fastest
    min_competitors: [0]
"""))
    assert len(generate_diplomas(summary, data.definition, config)["diplomas"]["fastest"]) == 1


def test_generator_ignores_match_options_section(tmp_path):
    data = make_data()
    summary = {
        "_match_options": {"divisions": ["FSO"], "categories": ["Senior"], "classes": ["Gold"]},
        "uid": {"first_name": "Test", "last_name": "Shooter", "division": "FSO", "class": "Gold", "categories": [], "raw_time": 1, "total_time": 1, "points_down": 0, "steel_misses": 0, "penalties": {}, "dnf": False, "dq": False},
    }
    config = load_config(config_file(tmp_path, """series:
  fastest:
    type: fastest
    min_competitors: [0]
"""))

    records = generate_diplomas(summary, data.definition, config)["diplomas"]["fastest"]

    assert [record["shooter"]["first_name"] for record in records] == ["Test"]


def test_loads_and_validates_configuration_from_memory(tmp_path):
    path = config_file(tmp_path, """series:
  award:
    type: fastest
    min_competitors: [1]
    text:
      first_line: '{{ shooter.first_name }}'
      second_line: '{{ place }}'
""")
    content = path.read_text(encoding="utf-8")
    assert load_config_text(content) == load_config(path)
    with pytest.raises(DiplomaDataError, match="Could not parse config"):
        load_config_text("series: [unterminated")
