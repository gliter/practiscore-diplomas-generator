import json
import zipfile
from pathlib import Path

import pytest

from practiscore_diplomas.parser import MatchParseError, MatchData, parse_match, parse_match_data


def make_data() -> MatchData:
    return MatchData(
        {
            "match_name": "Synthetic Match",
            "match_pointsdownvalue": 0.5,
            "match_steelmisspdcount": 10,
            "match_penalties": [{"pen_name": "Miss", "pen_val": 5}, {"pen_name": "Procedural Error", "pen_val": 3}],
            "match_shooters": [
                {"sh_uid": "shooter-a", "sh_id": "GPA-001", "sh_fn": "Test", "sh_ln": "Alpha", "sh_dvp": "FSO", "sh_grd": "Gold", "sh_ctgs": '["Senior"]'},
                {"sh_uid": "shooter-b", "sh_fn": "Test", "sh_ln": "Bravo", "sh_dvp": "CPI", "sh_grd": "Silver", "sh_ctgs": "[]", "sh_dq": True},
            ],
        },
        {
            "match_scores": [
                {"stage_stagescores": [{"shtr": "shooter-a", "str": [10.25, 2], "pens": [1, 0], "tpts": [1, 2], "popm": 1}]},
                {"stage_stagescores": [{"shtr": "shooter-a", "str": [5.75], "pens": [0, 1], "popm": 0, "dnf": False}]},
            ],
            "match_scores_history": {"ignored": True},
        },
    )


def test_aggregates_scores_and_penalties():
    result = parse_match_data(make_data())
    participant = result["shooter-a"]
    assert participant["raw_time"] == 18
    assert participant["shooter_id"] == "GPA-001"
    assert participant["categories"] == ["Senior"]
    assert participant["penalties"] == {"Miss": 1, "Procedural Error": 1}
    assert participant["points_down"] == 3
    assert participant["steel_misses"] == 1
    assert participant["penalty_seconds"] == 14.5
    assert participant["total_time"] == 32.5


def test_excludes_shooter_without_score():
    assert "shooter-b" not in parse_match_data(make_data())


def test_excludes_deleted_shooter_even_with_score():
    data = make_data()
    definition = dict(data.definition)
    definition["match_shooters"] = [
        {**data.definition["match_shooters"][0], "sh_del": True},
    ]
    assert parse_match_data(MatchData(definition, data.scores)) == {}


def test_marks_shooter_with_missing_stage_as_dnf():
    data = make_data()
    data_with_partial_score = MatchData(
        data.definition,
        {"match_scores": [data.scores["match_scores"][0], {"stage_stagescores": []}]},
    )
    result = parse_match_data(data_with_partial_score)
    assert result["shooter-a"]["dnf"] is True


def test_marks_failed_chrono_as_dnf_when_enabled():
    data = make_data()
    definition = dict(data.definition)
    definition["match_stages"] = [{"stage_uuid": "chrono", "stage_scoretype": "Chrono"}]
    scores = {"match_scores": [{"stage_uuid": "chrono", "stage_stagescores": [{"shtr": "shooter-a", "gear_check": "Fail", "str": [0]}]}]}
    assert parse_match_data(MatchData(definition, scores))["shooter-a"]["dnf"] is True
    assert parse_match_data(MatchData(definition, scores), mark_chrono_failure_as_dnf=False)["shooter-a"]["dnf"] is False


def test_reads_archive_and_directory(tmp_path: Path):
    directory = tmp_path / "export"
    directory.mkdir()
    for name, value in (("match_def.json", make_data().definition), ("match_scores.json", make_data().scores)):
        (directory / name).write_text(json.dumps(value), encoding="utf-8")
    archive = tmp_path / "export.pcs"
    with zipfile.ZipFile(archive, "w") as handle:
        for name in ("match_def.json", "match_scores.json"):
            handle.write(directory / name, name)
    assert parse_match(directory) == parse_match(archive)


def test_rejects_missing_archive_member(tmp_path: Path):
    archive = tmp_path / "bad.psc"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("match_def.json", "{}")
    with pytest.raises(MatchParseError, match="match_scores.json"):
        parse_match(archive)
