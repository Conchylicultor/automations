"""Page element."""

from __future__ import annotations

import dataclasses
import datetime
import functools
from typing import Self

from notion_api import database, property, utils
from notion_api.typing import Json


@dataclasses.dataclass
class User:
    id: str

    @classmethod
    def from_json(cls, data: Json) -> Self:
        assert data["object"] == "user"
        return cls(
            id=data["id"],
        )


@dataclasses.dataclass
class EditInfo:
    by: User
    time: datetime.datetime

    @classmethod
    def from_json(cls, data: Json, *, prefix: str) -> Self:
        return cls(
            by=User.from_json(data[f"{prefix}_by"]),
            time=utils.to_date(data[f"{prefix}_time"]),
        )


@dataclasses.dataclass
class DatabasePage:  # TODO(epot): 2 class for DB page and non-db page
    db: database.Database
    id: str
    created: EditInfo
    last_edited: EditInfo
    props: property.Properties

    @classmethod
    def from_json(cls, data: Json, *, db: database.Database) -> Self:
        self = cls(
            db=db,
            id=data["id"],
            created=EditInfo.from_json(data, prefix="created"),
            last_edited=EditInfo.from_json(data, prefix="last_edited"),
            props=property.Properties.from_json(
                data["properties"], future_page=lambda: self
            ),
        )
        return self
