"""Property info."""

from __future__ import annotations

import dataclasses
import functools
from collections.abc import Callable
from typing import Any, ClassVar, Generic, Self, TypeVar

import notion_client
from etils import epy

from auto_notion import database
from auto_notion import page as pagelib
from auto_notion import utils
from auto_notion.typing import Json

_PropT = TypeVar("_PropT")


@dataclasses.dataclass
class PropertyBase:
    TYPE: ClassVar[str | None] = None

    id: str
    name: str
    json: Json
    db: database.Database

    def __init_subclass__(cls, **kwargs) -> None:
        if cls.TYPE:
            cls._TYPE_TO_CLS[cls.TYPE] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def from_json(
        cls,
        json: Json,
        *,
        name: str,
        db: database.Database,
        **kwargs,
    ) -> Self:
        type_ = json["type"]
        child_cls = cls._TYPE_TO_CLS.get(type_)
        if child_cls is None:
            print(f"Unsupported property {type_}")
            child_cls = cls

        return child_cls(
            id=json["id"],
            name=name,
            json=json,
            db=db,
            **kwargs,  # Additional kwargs forwarded to child class
        )

    @functools.cached_property
    def snake_name(self) -> str:
        return utils.to_snake_case(self.name)

    @property
    def type(self) -> str:
        return self.json["type"]

    @functools.cached_property
    def api(self) -> notion_client.Client:
        return self.db.api


class PropertiesBase(Generic[_PropT]):
    _props: dict[str, _PropT]

    _PROP_CLS: ClassVar[type[_PropT]]

    @classmethod
    def from_json(
        cls,
        json: Json,
        *,
        db: database.Database,
        **kwargs,
    ) -> Self:
        props = [
            cls._PROP_CLS.from_json(p, name=k, db=db, **kwargs) for k, p in json.items()
        ]
        return cls({p.snake_name: p for p in props})

    def __init__(self, state: dict[str, _PropT]):
        object.__setattr__(self, "_props", state)

    def __dir__(self) -> list[str]:
        return list(self._props)

    def __repr__(self) -> str:
        return epy.Lines.make_block(
            type(self).__qualname__,
            {k: v.value for k, v in self._props.items()},
        )

    def __getattr__(self, key: str) -> _PropT:
        return self._props[key]

    def __setattr__(self, key: str, value) -> None:
        # To easy to make the error, so forward (or raise error ?)
        # self._props[key].value = value
        raise AttributeError(f"Cannot directly assign `{type(self).__name__}`. ")


# Supported fields:


# class PropertyType(epy.StrEnum):
#     CREATED_TIME = enum.auto()
#     DATE = enum.auto()
#     MULTI_SELECT = enum.auto()
#     FORMULA = enum.auto()
#     RELATION = enum.auto()
#     RICH_TEXT = enum.auto()
#     TITLE = enum.auto()


_t = [
    # "title",
    # "rich_text",
    # "number",
    "select",
    "multi_select",
    "status",
    "date",
    "formula",
    "relation",
    "rollup",
    "people",
    "files",
    "checkbox",
    "url",
    "email",
    "phone_number",
    "created_time",
    "created_by",
    "last_edited_time",
    "last_edited_by",
]
