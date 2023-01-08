"""Database element."""

from __future__ import annotations

import collections
import functools

from notion_api import page, property, utils
from notion_api.typing import Json


class Database:

    def __init__(self, id: str):
        # TODO: Add caching
        # TODO: Better way of controlling client
        self.id = id
        self.api = utils.get_client()

    @functools.cached_property
    def _retrive(self) -> Json:
        return self.api.databases.retrieve(self.id)

    @functools.cached_property
    def props(self) -> property.PropertiesInfo:
        return property.PropertiesInfo.from_json(self._retrive["properties"])

    def __iter__(self) -> DatabaseIterator:
        return DatabaseIterator(self)


class DatabaseIterator:

    def __init__(self, db: Database):
        self._db = db
        # Could use
        # from notion_client.helpers import iterate_paginated_api
        # instead
        self._results = collections.deque()
        self._next_cursor = None
        self._has_more = True

    def __iter__(self) -> DatabaseIterator:
        return self

    def __next__(self) -> page.Page:
        if not self._results:
            if not self._has_more:
                # No more results
                raise StopIteration
            else:
                # Fetch the next results
                results = self._db.api.databases.query(
                    database_id=self._db.id,
                    start_cursor=self._next_cursor,
                    # filter_properties
                    # page_size
                    # sorts
                    # filter
                )
                self._results.extend(results["results"])
                self._next_cursor = results["next_cursor"]
                self._has_more = results["has_more"]
        return page.DatabasePage.from_json(self._results.popleft(), db=self._db)
