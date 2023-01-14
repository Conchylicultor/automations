"""Colab common utils."""

import os
import pathlib
import sys


def add_notion_to_sys_path() -> None:
    root_dir = pathlib.Path(__file__).parent.parent
    assert (root_dir / "auto_notion" / "__init__.py").exists()
    sys.path.append(os.fspath(root_dir))
