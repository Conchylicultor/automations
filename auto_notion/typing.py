"""Typing utils."""

from __future__ import annotations

JsonValue = str | bool | int | float | None | list["JsonValue"] | dict[str, "JsonValue"]
Json = dict[str, JsonValue]
