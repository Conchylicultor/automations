"""Notion API utils."""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    import auto_notion.compat as _compat

del sys

from auto_notion.database import Database
