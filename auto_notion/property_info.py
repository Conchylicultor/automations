"""Property info."""

from __future__ import annotations

import dataclasses
import functools
from typing import ClassVar, Self

from auto_notion import database, property_base
from auto_notion.typing import Json


@dataclasses.dataclass
class PropertyInfo(property_base.PropertyBase):
    """Header of the database property."""

    _TYPE_TO_CLS: ClassVar[dict[str, type[PropertyInfo]]] = {}


class PropertiesInfo(property_base.PropertiesBase[PropertyInfo]):
    _PROP_CLS = PropertyInfo


class _Select(PropertyInfo):

    @property
    def choices(self) -> list[str]:
        return [opt["name"] for opt in self.json[self.TYPE]["options"]]


class Select(_Select):
    TYPE = "select"


class MultiSelect(_Select):
    TYPE = "multi_select"
