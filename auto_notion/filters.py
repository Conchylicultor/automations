"""."""

from __future__ import annotations

import dataclasses
from typing import ClassVar, Self

from auto_notion import database, property_base
from auto_notion.typing import Json


@dataclasses.dataclass
class Filter:
    bool_state: bool = True

    def to_json(self) -> Json:
        raise NotImplementedError

    def __invert__(self) -> Self:
        return self.replace(bool_state=not self.bool_state)

    replace = dataclasses.replace


@dataclasses.dataclass
class FilterProperty(Filter, property_base.PropertyBase):

    _TYPE_TO_CLS: ClassVar[dict[str, type[FilterProperty]]] = {}

    def to_json(self) -> Json:
        return {
            "property": self.id,
            self.type: self._to_json_inner(),
        }

    def _to_json_inner(self) -> Json:
        raise NotImplementedError


class FilterProperties(property_base.PropertiesBase[FilterProperty]):
    """Wrap the page to allow easy access to property fields."""

    _PROP_CLS = FilterProperty


class Checkbox(FilterProperty):
    TYPE = "checkbox"

    def _to_json_inner(self) -> Json:
        return {
            "equals": self.bool_state,
        }
