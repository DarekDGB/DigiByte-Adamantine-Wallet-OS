"""
Robust pytest config that ensures the `core/` package is importable
in all CI environments (Android / iOS / Web).
"""

from __future__ import annotations
import sys
from pathlib import Path


def _find_project_root(marker_folder: str = "core") -> Path:
    """
    Walk upward from the current conftest file until we find a directory
    containing the target marker folder (`core`). This works even if
    CI runs tests from nested working directories.
    """
    current = Path(__file__).resolve().parent

    for _ in range(10):  # walk up max 10 levels for safety
        if (current / marker_folder).exists():
            return current
        current = current.parent

    raise RuntimeError("Could not locate project root containing /core directory")


# Ensure the project root is added to sys.path
project_root = _find_project_root()
root_str = str(project_root)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
