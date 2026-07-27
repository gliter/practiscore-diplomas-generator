import pytest

from practiscore_diplomas.diplomas import DiplomaDataError, generate_diplomas, load_config
from tests.test_parser import make_data


def config_file(tmp_path, text):
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
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
    assert records[0]["place"] == 1
    assert records[0]["division"] == "FSO"
    assert records[0]["class"] == "Gold"
    assert records[0]["category"] is None
    assert records[0]["shooter"]["shooter_id"] == "GPA-002"
    assert "eligible_competitors" not in records[0]
    assert "qualification_threshold" not in records[0]


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


def test_rejects_invalid_filter_regular_expression(tmp_path):
    with pytest.raises(DiplomaDataError, match="regular expression"):
        load_config(config_file(tmp_path, """series:
  bad:
    type: fastest
    filters:
      divisions: ['[']
    min_competitors: [0]
"""))
