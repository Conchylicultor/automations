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


def to_snake_case(name: str) -> str:
    # TODO(epot): Better name normalization
    # * Not start by number
    # * Normalize accents (currently are `isalpha() is True` but `isascii() is False`)
    # * Normalize `(`, accents, special characters...
    chars = []
    for char in name.strip().lower():
        if char.isalnum():
            chars.append(char)
        elif char == " ":
            chars.append("_")
        else:
            continue
    return "".join(chars)
