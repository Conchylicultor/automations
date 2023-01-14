"""Database element."""

from __future__ import annotations

import collections
import functools
from typing import Any

from auto_notion import page as pagelib
from auto_notion import property_info, utils
from auto_notion.typing import Json

if True:
    # Circular import
    from auto_notion import filters as filterslib


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
    def props(self) -> property_info.PropertiesInfo:
        return property_info.PropertiesInfo.from_json(
            self._retrive["properties"],
            db=self,
        )

    def __iter__(self) -> DatabaseIterator:
        return DatabaseIterator(self)

    def __getitem__(self, filters: filterslib.Filter) -> DatabaseIterator:
        return DatabaseIterator(self, filter=filters)

    @property
    def filters(self) -> filterslib.FilterProperties:
        return filterslib.FilterProperties.from_json(
            self._retrive["properties"],
            db=self,
        )

    # TODO: Custom __repr__


class DatabaseIterator:

    def __init__(self, db: Database, *, filter: filterslib.Filter | None = None):
        self._db = db
        # Could use
        # from notion_client.helpers import iterate_paginated_api
        # instead
        self._results = collections.deque()
        self._next_cursor = None
        self._has_more = True
        self._filter = filter

        if filter is not None and not isinstance(filter, filterslib.Filter):
            raise TypeError(f"Invalid filter: {filter!r}")

    def __iter__(self) -> DatabaseIterator:
        return self

    def __next__(self) -> PropertyProxy:
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
                    filter=self._json_filter,
                )
                self._results.extend(results["results"])
                self._next_cursor = results["next_cursor"]
                self._has_more = results["has_more"]
        page = pagelib.DatabasePage.from_json(self._results.popleft(), db=self._db)
        return PropertyProxy(page)

    @property
    def _json_filter(self) -> Json:
        if self._filter is None:
            return None
        else:
            return self._filter.to_json()


class PropertyProxy:
    """Wrap the page to allow easy access to property fields."""

    def __init__(self, page):
        object.__setattr__(self, "_page", page)

    # Could merge with PropertiesBase (by unifying `get_props_fn`)

    def __dir__(self) -> list[str]:
        return list(self._page.props._props) + ["INFO"]

    def __getattr__(self, key: str) -> Any:
        return self._page.props._props[key].value

    def __setattr__(self, key: str, value: Any) -> None:
        self._page.props._props[key].value = value

    @property
    def INFO(self) -> pagelib.DatabasePage:
        return self._page
