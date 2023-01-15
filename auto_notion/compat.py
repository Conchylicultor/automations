"""3.8 backports."""
import functools
import typing

typing.Self = typing.Any
functools.cache = functools.lru_cache(maxsize=None)

import backports.datetime_fromisoformat

backports.datetime_fromisoformat.MonkeyPatch.patch_fromisoformat()
