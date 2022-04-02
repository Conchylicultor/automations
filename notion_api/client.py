"""Main client API."""

from __future__ import annotations

import collections
import dataclasses
import datetime
import os
import functools
from typing import Any

from etils import epy
import notion_client

Json = Any


@functools.lru_cache()
def _get_client() -> notion_client.Client:
    return notion_client.Client(
        auth=os.environ["NOTION_TOKEN"],
        # log_level=logging.DEBUG,
    )


class Client:
    """Notion API."""

    def __init__(self) -> None:
        self.api = _get_client()


class Database:
    """."""

    def __init__(self, database_id: str) -> None:
        # TODO
        self._client = _get_client()

        results = self._client.databases.query(
            database_id=database_id,
            # start_cursor
            # sorts
            # filter
        )
        # Result:
        # 'object', 'results', 'next_cursor', 'has_more'
        self.pages = [Page(r) for r in results["results"]]
        assert not results["has_more"]


class Page(collections.UserDict):
    def __init__(self, row: Json):
        super().__init__()
        self.json = row
        for field_name, field in row["properties"].items():
            self[field_name] = _parse_property(field)

    def __repr__(self) -> str:
        lines = epy.Lines()
        lines += f"{self.__class__.__name__}("
        with lines.indent():
            for k, v in self.items():
                lines += f"{k!r}: {v!r}"
        lines += ")"
        return lines.join()


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
    if property["type"] == "formula":
        return NotImplementedElem(property)
    elif property["type"] == "date":
        content = property["date"]
        if content is None:
            return None
        assert content["end"] is None
        assert content["time_zone"] is None
        return datetime.datetime.strptime(content["start"], "%Y-%m-%d")
    elif property["type"] == "multi_select":
        return NotImplementedElem(property)
    elif property["type"] == "relation":
        return NotImplementedElem(property)
    elif property["type"] == "title":
        return _parse_text(property["title"])
    else:
        raise NotImplementedError("Unsupported property type.")
