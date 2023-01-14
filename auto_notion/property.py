"""Property element."""

from __future__ import annotations

import dataclasses
import datetime
import enum
import functools
from collections.abc import Callable
from typing import Any, ClassVar, Generic, Self, TypeVar

from etils import epy

from auto_notion import page as pagelib
from auto_notion import property_base, property_info
from auto_notion import text as textlib
from auto_notion import utils
from auto_notion.typing import Json

_T = TypeVar("_T")


@dataclasses.dataclass
class Property(property_base.PropertyBase, Generic[_T]):

    _TYPE_TO_CLS: ClassVar[dict[str, type[Property]]] = {}

    page: pagelib.DatabasePage

    @property
    def value(self) -> _T:
        val = self.json[self.TYPE]
        if val is None:
            return val
        else:
            return self.parse(val)

    @value.setter
    def value(self, new_val: _T) -> None:
        if new_val is not None:  # Otherwise clear the field
            new_val = self.serialize(new_val)

        # TODO(epot): Validate the value (type, range,...)
        query = {self.id: {self.type: new_val}}
        try:
            new_page = self.api.pages.update(
                self.page.id,
                properties=query,
            )
        except Exception as e:
            e.add_note(f"query: {query}")
            raise
        self.json[self.TYPE] = new_page["properties"][self.name][self.TYPE]

    @functools.cached_property
    def info(self) -> property_info.PropertyInfo:
        return self.page.props[self.snake_name]

    # TODO: Custom __repr__

    # Childs

    # TODO: Raise error instead ?

    def parse(self, value: Json) -> _T:
        return value

    def serialize(self, value) -> Json:
        raise NotImplementedError(
            f"Serializatioin for {self.type} ({self.name}) not implemented."
        )


class _Text(Property[str]):

    def parse(self, json: Json):
        return textlib.json_to_str(json)

    def serialize(self, value) -> Json:
        return textlib.str_to_json(value)


class Title(_Text):
    TYPE = "title"

    # def serialize(self) -> Json:
    #     pass


class RichText(_Text):
    TYPE = "rich_text"


class _Value(Property[_T]):

    def parse(self, value: Json) -> _T:
        return value

    def serialize(self, value) -> Json:
        return value


class Number(_Value[float | int]):
    TYPE = "number"


class Checkbox(_Value[bool]):
    TYPE = "checkbox"


class Select(Property[epy.StrEnum | None]):
    TYPE = "select"

    def parse(self, value: Json) -> str:
        return value["name"]

    def serialize(self, value) -> Json:
        if value not in self.db.props._props[self.snake_name].choices:
            # TODO: difflib for hint ?
            raise ValueError(f"Unexpected {self.name!r} value: {value!r}.")
        return {"name": value}


class MultiSelect(Property[list[epy.StrEnum]]):
    TYPE = "multi_select"


class Date(Property[datetime.datetime | None]):
    TYPE = "date"

    def parse(self, value: Json):
        assert value["end"] is None
        return datetime.datetime.fromisoformat(value["start"])

    def serialize(self, value: datetime.datetime) -> Json:
        return {
            "start": value.isoformat(),
            "end": None,
        }


class _Time(Property[datetime.datetime]):

    def parse(self, value: Json):
        return datetime.datetime.fromisoformat(value)

    def serialize(self) -> Json:
        raise ValueError(f"{self.TYPE} ({self.name}) property is read-only.")


class CreatedTime(_Time):
    TYPE = "created_time"


class LastEditedBy(_Time):
    TYPE = "last_edited_time"


class Properties(property_base.PropertiesBase[Property]):
    _PROP_CLS = Property

    def __repr__(self) -> str:
        return epy.Lines.make_block(
            type(self).__qualname__,
            {k: v.value for k, v in self._props.items()},
        )
