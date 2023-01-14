"""Page element."""

from __future__ import annotations

import dataclasses
import datetime
import functools
from typing import Self

from auto_notion import database
from auto_notion import property as propertylib
from auto_notion.typing import Json


@dataclasses.dataclass
class User:
    id: str

    @classmethod
    def from_json(cls, json: Json) -> Self:
        assert json["object"] == "user"
        return cls(
            id=json["id"],
        )


@dataclasses.dataclass
class EditInfo:
    by: User
    time: datetime.datetime

    @classmethod
    def from_json(cls, json: Json, *, prefix: str) -> Self:
        return cls(
            by=User.from_json(json[f"{prefix}_by"]),
            time=datetime.datetime.fromisoformat(json[f"{prefix}_time"]),
        )


@dataclasses.dataclass
class DatabasePage:  # TODO(epot): 2 class for DB page and non-db page
    db: database.Database
    id: str
    created: EditInfo
    last_edited: EditInfo
    json: Json

    @classmethod
    def from_json(cls, json: Json, *, db: database.Database) -> Self:
        self = cls(
            db=db,
            id=json["id"],
            created=EditInfo.from_json(json, prefix="created"),
            last_edited=EditInfo.from_json(json, prefix="last_edited"),
            json=json,
        )
        return self

    @functools.cached_property
    def props(self) -> propertylib.Properties:
        return propertylib.Properties.from_json(
            self.json["properties"],
            db=self.db,
            page=self,
        )
