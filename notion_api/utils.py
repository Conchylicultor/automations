"""Main client API."""

from __future__ import annotations

import collections
import dataclasses
import datetime
import functools
import os
from typing import Any

import notion_client
from etils import epy

Json = Any


@functools.cache
def get_client(token: str | None = None) -> notion_client.Client:
    options = notion_client.client.ClientOptions(
        auth=os.environ["NOTION_API_SPORT"],
    )
    return notion_client.Client(options)


def to_date(date: str) -> datetime.datetime:
    # TODO: Implement
    # E.g. 2023-01-05T18:34:00.000Z
    return datetime.datetime.now()
