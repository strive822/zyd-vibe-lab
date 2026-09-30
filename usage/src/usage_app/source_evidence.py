"""Whitelist a quota schema observation; never archive an entire HTTP body."""

from __future__ import annotations

import math
import re


NUMERIC_FIELDS = frozenset({"percentage", "usedPercent", "remainingPercent", "currentValue", "usage", "limit", "total", "unit", "number",
                           "used", "remaining", "windowDurationMins", "duration", "windowDuration", "resetTime",
                           "resetAt", "resetsAt", "nextResetTime", "nextResetAt", "nextResetAtMs"})
UNIT_FIELDS = frozenset({"unit", "timeUnit", "durationUnit", "windowUnit"})
UNITS = frozenset({"MINUTE", "MINUTES", "HOUR", "HOURS", "DAY", "DAYS", "WEEK", "WEEKS",
                   "SECOND", "SECONDS", "MILLISECOND", "MILLISECONDS", "TOKENS", "CREDIT", "CREDITS"})


def glm_schema_observation(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict) or not isinstance(raw.get("data"), dict):
        return {"shape": "incompatible"}
    limits = raw["data"].get("limits")
    if not isinstance(limits, list):
        return {"shape": "incompatible"}
    observed: list[dict[str, object]] = []
    for item in limits[:32]:
        if not isinstance(item, dict):
            continue
        value: dict[str, object] = {"fieldNames": sorted(key for key in item if isinstance(key, str) and
                                                      re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,39}", key))}
        kind = item.get("type")
        if isinstance(kind, str) and re.fullmatch(r"[A-Z][A-Z_]{0,49}", kind):
            value["type"] = kind
        for key in NUMERIC_FIELDS:
            number = item.get(key)
            if isinstance(number, (int, float)) and not isinstance(number, bool) and math.isfinite(number):
                value[key] = number
        for key in UNIT_FIELDS:
            unit = item.get(key)
            if isinstance(unit, str) and unit.upper() in UNITS:
                value[key] = unit
        observed.append(value)
    return {"shape": "data.limits", "limits": observed,
            "boundary": "Field observation only. Percentage direction/window/recovery semantics still require official UI comparison."}
