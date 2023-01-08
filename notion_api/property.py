"""Property element."""

from __future__ import annotations

import dataclasses
import datetime
import enum
import functools
from collections.abc import Callable
from typing import Any, Self, TypeVar

import notion_client
from etils import epy

from notion_api import database
from notion_api import page as pagelib
from notion_api.typing import Json

_T = TypeVar("_T")
Future = Callable[[], _T]


class PropertyType(epy.StrEnum):
    CREATED_TIME = enum.auto()
    DATE = enum.auto()
    MULTI_SELECT = enum.auto()
    FORMULA = enum.auto()
    RELATION = enum.auto()
    RICH_TEXT = enum.auto()
    TITLE = enum.auto()


@dataclasses.dataclass
class PropertyInfo:
    """Header of the database property."""

    id: str
    name: str
    type: PropertyType

    @classmethod
    def from_json(cls, data: Json) -> Self:
        return cls(
            id=data["id"],
            name=data["name"],
            type=PropertyType(data["type"]),
        )

    @functools.cached_property
    def snake_name(self) -> str:
        return _to_snake_case(self.name)


@dataclasses.dataclass
class PropertiesInfo:
    props: list[PropertyInfo]

    @classmethod
    def from_json(cls, data: Json) -> Self:
        return cls([PropertyInfo.from_json(data) for data in data.values()])

    def __dir__(self) -> list[str]:
        return [p.snake_name for p in self.props]


@dataclasses.dataclass
class PropertyState(PropertyInfo):
    json: Json
    future_page: Future[pagelib.DatabasePage]

    @classmethod
    def from_json(
        cls, data: Json, *, name: str, future_page: Future[pagelib.DatabasePage]
    ) -> Self:
        return cls(
            future_page=future_page,
            id=data["id"],
            name=name,
            type=PropertyType(data["type"]),
            json=data,
        )

    @property
    def value(self) -> _T:
        return _parse_property(self.json)

    @value.setter
    def value(self, new_val: _T) -> None:
        # TODO(epot): Normalize the value
        self.api.pages.update(self.page.id, properties={self.id: new_val})

    @functools.cached_property
    def page(self) -> pagelib.DatabasePage:
        return self.future_page()

    @functools.cached_property
    def api(self) -> notion_client.Client:
        return self.page.db.api


class Properties:

    @classmethod
    def from_json(
        cls, data: Json, *, future_page: Future[pagelib.DatabasePage]
    ) -> Self:
        props = [
            PropertyState.from_json(p, name=k, future_page=future_page)
            for k, p in data.items()
        ]
        return cls({p.snake_name: p for p in props})

    def __init__(self, state: dict[str, PropertyState]):
        object.__setattr__(self, "_props", state)

    def __getattr__(self, key: str) -> Any:
        return self._props[key]

    def __dir__(self) -> list[str]:
        return list(self._props)


def _to_snake_case(name: str) -> str:
    # TODO(epot): Better name normalization
    # * Not start by number
    # * Normalize `(`, accents, special characters...
    return name.strip().replace(" ", "_").lower()


@dataclasses.dataclass
class NotImplementedElem:
    property: Json

    def __repr__(self) -> str:
        type = self.property["type"]
        return f"{self.__class__.__name__}({type!r})"


def _parse_text(text: Json):
    parts = []
    for elem in text:
        if elem["type"] == "text":
            parts.append(elem["plain_text"])
        else:
            raise NotImplementedError("Unsupported property type.")
    return "".join(parts)


def _parse_property(property: Json):
    match property["type"]:
        case "formula":
            return NotImplementedElem(property)
        case "date":
            content = property["date"]
            if content is None:
                return None
            assert content["end"] is None
            assert content["time_zone"] is None
            return datetime.datetime.strptime(content["start"], "%Y-%m-%d")
        case "multi_select":
            return NotImplementedElem(property["multi_select"])
        case "relation":
            return NotImplementedElem(property["relation"])
        case "rich_text":
            return _parse_text(property["rich_text"])
        case "title":
            return _parse_text(property["title"])
        case unknown:
            raise NotImplementedError(f"Unsupported property type. {unknown}")
