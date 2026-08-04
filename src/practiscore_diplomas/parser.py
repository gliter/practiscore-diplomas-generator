"""Parse current scores from PractiScore match exports."""

from __future__ import annotations

import json
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping


class MatchParseError(ValueError):
    """Raised when a PractiScore export cannot be parsed."""


@dataclass(frozen=True)
class MatchData:
    definition: Mapping[str, Any]
    scores: Mapping[str, Any]


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise MatchParseError(f"Could not read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MatchParseError(f"JSON file {path} must contain an object")
    return value


def _from_directory(directory: Path) -> MatchData:
    if not directory.is_dir():
        raise MatchParseError(f"Input directory does not exist: {directory}")
    files = {name: directory / name for name in ("match_def.json", "match_scores.json")}
    missing = [name for name, path in files.items() if not path.is_file()]
    if missing:
        raise MatchParseError(f"Export is missing: {', '.join(missing)}")
    return MatchData(_load_json(files["match_def.json"]), _load_json(files["match_scores.json"]))


def _from_archive(path: Path) -> MatchData:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            missing = [name for name in ("match_def.json", "match_scores.json") if name not in names]
            if missing:
                raise MatchParseError(f"Export is missing: {', '.join(missing)}")
            values = {}
            for name in ("match_def.json", "match_scores.json"):
                try:
                    values[name] = json.loads(archive.read(name).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise MatchParseError(f"Could not read JSON member {name}: {exc}") from exc
    except zipfile.BadZipFile as exc:
        raise MatchParseError(f"Input is not a valid ZIP archive: {path}") from exc
    if not all(isinstance(value, dict) for value in values.values()):
        raise MatchParseError("Export JSON members must contain objects")
    return MatchData(values["match_def.json"], values["match_scores.json"])


def _read_input(path: Path) -> MatchData:
    if path.is_dir():
        return _from_directory(path)
    if path.is_file():
        return _from_archive(path)
    raise MatchParseError(f"Input does not exist: {path}")


def load_match_data(path: str | Path) -> MatchData:
    """Load the two JSON documents from an archive or unpacked export."""
    return _read_input(Path(path))


def _decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise MatchParseError(f"Expected a numeric value, got {value!r}") from exc


def _sum_numbers(values: Any) -> Decimal:
    if values is None:
        return Decimal(0)
    if not isinstance(values, list):
        raise MatchParseError(f"Expected an array of numbers, got {values!r}")
    return sum((_decimal(value) for value in values), Decimal(0))


def _number(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _categories(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise MatchParseError(f"Invalid shooter categories JSON: {value!r}") from exc
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise MatchParseError(f"Shooter categories must be a JSON array of strings: {value!r}")
    return value


def _shooters(definition: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    values = definition.get("match_shooters", [])
    if not isinstance(values, list):
        raise MatchParseError("match_shooters must be an array")
    result: dict[str, Mapping[str, Any]] = {}
    for shooter in values:
        if not isinstance(shooter, dict) or not shooter.get("sh_uid"):
            raise MatchParseError("Every shooter must have a sh_uid")
        if shooter.get("sh_del", False):
            continue
        result[str(shooter["sh_uid"])] = shooter
    return result


def _score_rows(scores: Mapping[str, Any]) -> Iterable[tuple[int, str | None, Mapping[str, Any]]]:
    stages = scores.get("match_scores", [])
    if not isinstance(stages, list):
        raise MatchParseError("match_scores must be an array")
    for stage_index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            raise MatchParseError("Every match score stage must be an object")
        rows = stage.get("stage_stagescores", [])
        if not isinstance(rows, list):
            raise MatchParseError("stage_stagescores must be an array")
        for row in rows:
            if not isinstance(row, dict) or not row.get("shtr"):
                raise MatchParseError("Every score row must have a shtr")
            yield stage_index, stage.get("stage_uuid"), row


def parse_match_data(data: MatchData, mark_chrono_failure_as_dnf: bool = True) -> dict[str, dict[str, Any]]:
    definition = data.definition
    shooter_map = _shooters(definition)
    stage_count = len(data.scores.get("match_scores", []))
    chrono_stage_uuids = {
        str(stage.get("stage_uuid"))
        for stage in definition.get("match_stages", [])
        if isinstance(stage, dict) and str(stage.get("stage_scoretype", "")).casefold() == "chrono" and stage.get("stage_uuid")
    }
    points_down_value = _decimal(definition.get("match_pointsdownvalue"))
    steel_miss_count = _decimal(definition.get("match_steelmisspdcount"))
    penalty_defs = definition.get("match_penalties", []) or []
    if not isinstance(penalty_defs, list):
        raise MatchParseError("match_penalties must be an array")
    penalty_values: dict[str, Decimal] = {}
    for penalty in penalty_defs:
        if not isinstance(penalty, dict) or "pen_name" not in penalty:
            raise MatchParseError("Every penalty must have a pen_name")
        penalty_values[str(penalty["pen_name"])] = _decimal(penalty.get("pen_val"))

    aggregates: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"raw_time": Decimal(0), "penalties": defaultdict(int), "points_down": 0, "steel_misses": 0, "dnf": False, "chrono_failed": False, "stages": set()}
    )
    for stage_index, stage_uuid, row in _score_rows(data.scores):
        uid = str(row["shtr"])
        aggregate = aggregates[uid]
        aggregate["stages"].add(stage_index)
        if mark_chrono_failure_as_dnf and stage_uuid in chrono_stage_uuids and row.get("gear_check") != "Pass":
            aggregate["chrono_failed"] = True
        aggregate["raw_time"] += _sum_numbers(row.get("str"))
        counts = row.get("pens", []) or []
        if not isinstance(counts, list):
            raise MatchParseError("pens must be an array")
        for index, name in enumerate(penalty_values):
            count = counts[index] if index < len(counts) else 0
            aggregate["penalties"][name] += int(_decimal(count))
        point_count = _sum_numbers(row.get("tpts"))
        steel_misses = int(_decimal(row.get("popm")))
        aggregate["points_down"] += int(point_count)
        aggregate["steel_misses"] += steel_misses
        aggregate["dnf"] = aggregate["dnf"] or bool(row.get("dnf", False))

    output: dict[str, dict[str, Any]] = {}
    for uid, shooter in shooter_map.items():
        if uid not in aggregates:
            continue
        aggregate = aggregates[uid]
        penalties = dict(aggregate["penalties"])
        for name in penalty_values:
            penalties.setdefault(name, 0)
        declared_seconds = sum((Decimal(count) * penalty_values[name] for name, count in penalties.items() if name in penalty_values), Decimal(0))
        point_seconds = Decimal(aggregate["points_down"]) * points_down_value
        steel_seconds = Decimal(aggregate["steel_misses"]) * steel_miss_count * points_down_value
        penalty_seconds = declared_seconds + point_seconds + steel_seconds
        dnf = bool(aggregate["dnf"] or aggregate["chrono_failed"] or len(aggregate["stages"]) < stage_count)
        dq = bool(shooter.get("sh_dq", False))
        output[uid] = {
            "shooter_id": shooter.get("sh_id", ""),
            "first_name": shooter.get("sh_fn", ""),
            "last_name": shooter.get("sh_ln", ""),
            "division": shooter.get("sh_dvp", ""),
            "categories": _categories(shooter.get("sh_ctgs")),
            "class": shooter.get("sh_grd", ""),
            "raw_time": _number(aggregate["raw_time"]),
            "penalties": penalties,
            "points_down": aggregate["points_down"],
            "steel_misses": aggregate["steel_misses"],
            "penalty_seconds": _number(penalty_seconds),
            "total_time": _number(aggregate["raw_time"] + penalty_seconds),
            "dnf": dnf,
            "dq": dq,
        }
    return output


def parse_match(path: str | Path) -> dict[str, dict[str, Any]]:
    """Parse a PractiScore archive or unpacked export directory."""
    return parse_match_data(load_match_data(path))


def parse_match_file(path: str | Path) -> dict[str, dict[str, Any]]:
    """Parse a PractiScore ZIP archive."""
    return parse_match(path)


def parse_match_directory(path: str | Path) -> dict[str, dict[str, Any]]:
    """Parse an unpacked PractiScore export directory."""
    return parse_match_data(_from_directory(Path(path)))
