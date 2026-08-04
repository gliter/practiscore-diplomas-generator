"""Configuration, grouping, ranking, and diploma-data generation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import re
from copy import deepcopy
from typing import Any, Mapping

import yaml


class DiplomaDataError(ValueError):
    """Raised when diploma configuration or selection data is invalid."""


DIMENSIONS = {"division", "class", "category"}
SERIES_TYPES = {"best_shooter", "most_accurate", "fastest"}
TEXT_VARIABLES = {"division", "category", "class", "place", "type"}
SHOOTER_VARIABLES = {
    "shooter_id",
    "first_name",
    "last_name",
    "division",
    "categories",
    "class",
    "raw_time",
    "points_down",
    "steel_misses",
    "penalty_seconds",
    "total_time",
    "dnf",
    "dq",
    "shooter_uid",
}
_EXPRESSION = re.compile(r"{{\s*([^{}]+?)\s*}}")
_MAP_CALL = re.compile(r"^([A-Za-z_]\w*)\(\s*([a-z_]+(?:\.[a-z_]+)?)\s*\)$")


@dataclass(frozen=True)
class FilterConfig:
    include: tuple[str, ...]
    exclude: tuple[str, ...]


@dataclass(frozen=True)
class MapConfig:
    entries: tuple[tuple[str | int, str], ...]


@dataclass(frozen=True)
class SeriesConfig:
    key: str
    type: str
    group_by: tuple[str, ...]
    filters: dict[str, FilterConfig]
    min_competitors: tuple[int, ...]
    exclude_dq: bool
    exclude_dnf: bool
    ineligible_penalties: tuple[str, ...]
    excluded_surnames: tuple[str, ...]
    excluded_ids: tuple[str, ...]
    mark_chrono_failure_as_dnf: bool
    maps: dict[str, MapConfig]
    first_line_template: str
    second_line_template: str
    third_line_template: str | None
    fourth_line_template: str | None


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise DiplomaDataError(f"{context} must be a mapping")
    return value


def _values(value: Any, context: str, default: tuple[str, ...] = ("*",), allow_empty: bool = False) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, list) or (not value and not allow_empty) or not all(isinstance(item, str) for item in value):
        label = "list of strings" if allow_empty else "non-empty list of strings"
        raise DiplomaDataError(f"{context} must be a {label}")
    for pattern in value:
        if pattern != "*":
            try:
                re.compile(pattern)
            except re.error as exc:
                raise DiplomaDataError(f"{context} contains invalid regular expression {pattern!r}: {exc}") from exc
    return tuple(value)


def _load_maps(value: Any) -> dict[str, MapConfig]:
    raw_maps = _mapping(value or {}, "maps")
    maps: dict[str, MapConfig] = {}
    for name, raw_map in raw_maps.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_]\w*", name):
            raise DiplomaDataError(f"maps contains invalid map name: {name!r}")
        mapping = _mapping(raw_map, f"maps.{name}")
        entries: list[tuple[str | int, str]] = []
        for map_key, map_value in mapping.items():
            if isinstance(map_key, bool) or not isinstance(map_key, (str, int)):
                raise DiplomaDataError(f"maps.{name} keys must be strings or integers")
            if not isinstance(map_value, str):
                raise DiplomaDataError(f"maps.{name}.{map_key!r} must map to a string")
            if isinstance(map_key, str):
                try:
                    re.compile(map_key)
                except re.error as exc:
                    raise DiplomaDataError(f"maps.{name} contains invalid regular expression {map_key!r}: {exc}") from exc
            entries.append((map_key, map_value))
        if not entries:
            raise DiplomaDataError(f"maps.{name} must contain at least one entry")
        maps[name] = MapConfig(tuple(entries))
    return maps


def _validate_template(template: Any, context: str, maps: Mapping[str, MapConfig], required: bool = True) -> str | None:
    if template is None and not required:
        return None
    if not isinstance(template, str) or not template:
        raise DiplomaDataError(f"{context} must be a non-empty string")
    if template.count("{{") != template.count("}}"):
        raise DiplomaDataError(f"{context} contains malformed template syntax")
    cursor = 0
    for match in _EXPRESSION.finditer(template):
        expression = match.group(1).strip()
        call = _MAP_CALL.fullmatch(expression)
        if call:
            map_name, variable = call.groups()
            if map_name not in maps:
                raise DiplomaDataError(f"{context} references unknown map {map_name!r}")
            if not (variable in TEXT_VARIABLES or (variable.startswith("shooter.") and variable[8:] in SHOOTER_VARIABLES)):
                raise DiplomaDataError(f"{context} references unknown variable {variable!r}")
        elif not (expression in TEXT_VARIABLES or (expression.startswith("shooter.") and expression[8:] in SHOOTER_VARIABLES)):
            raise DiplomaDataError(f"{context} contains invalid expression {expression!r}")
        cursor = match.end()
    if "{{" in template[cursor:] or "}}" in template[cursor:]:
        raise DiplomaDataError(f"{context} contains malformed template syntax")
    return template


def _lookup_map(map_config: MapConfig, value: Any, context: str) -> str:
    if value is None:
        raise DiplomaDataError(f"{context} cannot map a null value")
    if isinstance(value, int) and not isinstance(value, bool):
        for key, result in map_config.entries:
            if isinstance(key, int) and not isinstance(key, bool) and key == value:
                return result
    else:
        text_value = str(value)
        for key, result in map_config.entries:
            if isinstance(key, str) and re.fullmatch(key, text_value):
                return result
    raise DiplomaDataError(f"{context} has no mapping for {value!r}")


def _render_template(template: str, record: Mapping[str, Any], config: SeriesConfig, context: str) -> str:
    values = dict(record)
    values["type"] = config.type

    def value_for(variable: str) -> Any:
        if variable.startswith("shooter."):
            return record.get("shooter", {}).get(variable[8:])
        return values.get(variable)

    def replace(match: re.Match[str]) -> str:
        expression = match.group(1).strip()
        call = _MAP_CALL.fullmatch(expression)
        if call:
            map_name, variable = call.groups()
            return _lookup_map(config.maps[map_name], value_for(variable), f"{context} map {map_name!r}")
        value = value_for(expression)
        if value is None:
            raise DiplomaDataError(f"{context} variable {expression!r} is null")
        return str(value)

    return _EXPRESSION.sub(replace, template)


def load_config(path: str | Path) -> dict[str, SeriesConfig]:
    """Load and validate the Feature 2 YAML configuration."""
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as exc:
        raise DiplomaDataError(f"Could not read config {config_path}: {exc}") from exc
    root = _mapping(raw, "config")
    raw_series = _mapping(root.get("series"), "series")
    if not raw_series:
        raise DiplomaDataError("series must contain at least one series")
    raw_exclusions = _mapping(root.get("exclude_shooters", {}), "exclude_shooters")
    excluded_surnames = _values(raw_exclusions.get("surnames"), "exclude_shooters.surnames", default=(), allow_empty=True)
    excluded_ids = _values(raw_exclusions.get("ids"), "exclude_shooters.ids", default=(), allow_empty=True)
    mark_chrono_failure_as_dnf = root.get("mark_chrono_failure_as_dnf", True)
    if not isinstance(mark_chrono_failure_as_dnf, bool):
        raise DiplomaDataError("mark_chrono_failure_as_dnf must be boolean")
    maps = _load_maps(root.get("maps", {}))

    result: dict[str, SeriesConfig] = {}
    for key, raw_value in raw_series.items():
        if not isinstance(key, str) or not key:
            raise DiplomaDataError("series keys must be non-empty strings")
        series = _mapping(raw_value, f"series.{key}")
        series_type = series.get("type")
        if series_type not in SERIES_TYPES:
            raise DiplomaDataError(f"series.{key}.type must be one of {sorted(SERIES_TYPES)}")
        group_by_raw = series.get("group_by", [])
        if not isinstance(group_by_raw, list) or len(set(group_by_raw)) != len(group_by_raw) or not all(item in DIMENSIONS for item in group_by_raw):
            raise DiplomaDataError(f"series.{key}.group_by must contain unique dimensions: {sorted(DIMENSIONS)}")
        filters_raw = _mapping(series.get("filters", {}), f"series.{key}.filters")
        filter_names = {"division": "divisions", "class": "classes", "category": "categories"}
        filters: dict[str, FilterConfig] = {}
        for dimension in DIMENSIONS:
            filter_name = filter_names[dimension]
            raw_filter = filters_raw.get(filter_name)
            if isinstance(raw_filter, dict):
                include = _values(raw_filter.get("include"), f"series.{key}.filters.{filter_name}.include")
                exclude = _values(raw_filter.get("exclude"), f"series.{key}.filters.{filter_name}.exclude", default=(), allow_empty=True)
            else:
                include = _values(raw_filter, f"series.{key}.filters.{filter_name}")
                exclude = ()
            filters[dimension] = FilterConfig(include=include, exclude=exclude)
        thresholds = series.get("min_competitors")
        if not isinstance(thresholds, list) or not thresholds or not all(isinstance(item, int) and item >= 0 for item in thresholds):
            raise DiplomaDataError(f"series.{key}.min_competitors must be a non-empty list of non-negative integers")
        if len(thresholds) > 5 or list(thresholds) != sorted(set(thresholds)):
            raise DiplomaDataError(f"series.{key}.min_competitors must be strictly increasing and contain at most 5 thresholds")
        penalties = series.get("ineligible_penalties", [])
        if not isinstance(penalties, list) or not all(isinstance(item, str) for item in penalties):
            raise DiplomaDataError(f"series.{key}.ineligible_penalties must be a list of strings")
        for field in ("exclude_dq", "exclude_dnf"):
            if field in series and not isinstance(series[field], bool):
                raise DiplomaDataError(f"series.{key}.{field} must be boolean")
        text = _mapping(series.get("text"), f"series.{key}.text")
        first_line_template = _validate_template(text.get("first_line"), f"series.{key}.text.first_line", maps)
        second_line_template = _validate_template(text.get("second_line"), f"series.{key}.text.second_line", maps)
        third_line_template = _validate_template(text.get("third_line"), f"series.{key}.text.third_line", maps, required=False)
        fourth_line_template = _validate_template(text.get("fourth_line"), f"series.{key}.text.fourth_line", maps, required=False)
        result[key] = SeriesConfig(
            key=key,
            type=series_type,
            group_by=tuple(group_by_raw),
            filters=filters,
            min_competitors=tuple(thresholds),
            exclude_dq=series.get("exclude_dq", True),
            exclude_dnf=series.get("exclude_dnf", True),
            ineligible_penalties=tuple(penalties),
            excluded_surnames=excluded_surnames,
            excluded_ids=excluded_ids,
            mark_chrono_failure_as_dnf=mark_chrono_failure_as_dnf,
            maps=maps,
            first_line_template=first_line_template,
            second_line_template=second_line_template,
            third_line_template=third_line_template,
            fourth_line_template=fourth_line_template,
        )
    return result


def _number(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _matches(value: str, filter_config: FilterConfig) -> bool:
    included = "*" in filter_config.include or any(re.fullmatch(pattern, value) is not None for pattern in filter_config.include)
    excluded = any(re.fullmatch(pattern, value) is not None for pattern in filter_config.exclude)
    return included and not excluded


def _matches_any(value: str, patterns: tuple[str, ...]) -> bool:
    return any(re.fullmatch(pattern, value) is not None for pattern in patterns)


def _eligible(uid: str, shooter: Mapping[str, Any], config: SeriesConfig) -> bool:
    if config.exclude_dq and shooter.get("dq", False):
        return False
    if config.exclude_dnf and shooter.get("dnf", False):
        return False
    if _matches_any(str(shooter.get("last_name", "")), config.excluded_surnames):
        return False
    if _matches_any(str(shooter.get("shooter_id", "")), config.excluded_ids):
        return False
    if any(int(shooter.get("penalties", {}).get(name, 0)) > 0 for name in config.ineligible_penalties):
        return False
    values = {
        "division": str(shooter.get("division", "")),
        "class": str(shooter.get("class", "")),
    }
    if not _matches(values["division"], config.filters["division"]):
        return False
    if not _matches(values["class"], config.filters["class"]):
        return False
    categories = shooter.get("categories", [])
    if not isinstance(categories, list):
        return False
    return _matches("", config.filters["category"]) if "*" in config.filters["category"].include else any(_matches(category, config.filters["category"]) for category in categories)


def _groups(summary: Mapping[str, Mapping[str, Any]], config: SeriesConfig) -> dict[tuple[str, ...], list[tuple[str, Mapping[str, Any], int]]]:
    groups: dict[tuple[str, ...], list[tuple[str, Mapping[str, Any], int]]] = {}
    for source_index, (uid, shooter) in enumerate(summary.items()):
        if not _eligible(uid, shooter, config):
            continue
        category_values = shooter.get("categories", []) if "category" in config.group_by else [None]
        if not category_values:
            category_values = []
        for category in category_values:
            values = {
                "division": str(shooter.get("division", "")),
                "class": str(shooter.get("class", "")),
                "category": category,
            }
            group_key = tuple(values[dimension] for dimension in config.group_by)
            groups.setdefault(group_key, []).append((uid, shooter, source_index))
    if not config.group_by:
        groups.setdefault((), [])
    return groups


def _metric(shooter: Mapping[str, Any], config_type: str, steel_miss_pd_count: Decimal) -> Decimal:
    if config_type == "best_shooter":
        return Decimal(str(shooter["total_time"]))
    if config_type == "fastest":
        return Decimal(str(shooter["raw_time"]))
    return Decimal(str(shooter["points_down"])) + Decimal(str(shooter["steel_misses"])) * steel_miss_pd_count


def generate_diplomas(summary: Mapping[str, Mapping[str, Any]], definition: Mapping[str, Any], configs: Mapping[str, SeriesConfig]) -> dict[str, list[dict[str, Any]]]:
    """Generate selected diploma records from a shooter summary."""
    steel_miss_pd_count = Decimal(str(definition.get("match_steelmisspdcount", 0)))
    declared_penalties = {str(item.get("pen_name")) for item in definition.get("match_penalties", []) if isinstance(item, dict) and item.get("pen_name")}
    result: dict[str, list[dict[str, Any]]] = {}
    for key, config in configs.items():
        unknown = set(config.ineligible_penalties) - declared_penalties
        if unknown:
            raise DiplomaDataError(f"series.{key}.ineligible_penalties contains unknown penalties: {sorted(unknown)}")
        records: list[dict[str, Any]] = []
        for group_key, members in _groups(summary, config).items():
            diploma_count = sum(1 for threshold in config.min_competitors if len(members) >= threshold)
            if diploma_count == 0:
                continue
            ranked = sorted(
                members,
                key=lambda item: (_metric(item[1], config.type, steel_miss_pd_count), Decimal(str(item[1]["total_time"])), str(item[1].get("last_name", "")).casefold(), str(item[1].get("first_name", "")).casefold(), item[2]),
            )
            for place, (uid, shooter, _) in enumerate(ranked[:diploma_count], start=1):
                group_values = dict(zip(config.group_by, group_key))
                copied_shooter = deepcopy(shooter)
                copied_shooter["shooter_uid"] = uid
                records.append({
                    "place": place,
                    "division": group_values.get("division"),
                    "class": group_values.get("class"),
                    "category": group_values.get("category"),
                    "metric_value": _number(_metric(shooter, config.type, steel_miss_pd_count)),
                    "first_line": "",
                    "second_line": "",
                    "shooter": copied_shooter,
                })
                record = records[-1]
                record["first_line"] = _render_template(config.first_line_template, record, config, f"series.{key}.text.first_line")
                record["second_line"] = _render_template(config.second_line_template, record, config, f"series.{key}.text.second_line")
                if config.third_line_template is not None:
                    record["third_line"] = _render_template(config.third_line_template, record, config, f"series.{key}.text.third_line")
                if config.fourth_line_template is not None:
                    record["fourth_line"] = _render_template(config.fourth_line_template, record, config, f"series.{key}.text.fourth_line")
        result[key] = records
    return {"diplomas": result}
