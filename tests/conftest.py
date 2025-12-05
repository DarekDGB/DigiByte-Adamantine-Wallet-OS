"""
Pytest configuration – ensure the project root is on sys.path.

This makes imports like `from core.wallet_service import WalletService`
work reliably in all CI jobs (Android / iOS / Web), regardless of the
current working directory.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    # tests/  -> project root is one level up
    root = Path(__file__).resolve().parents[1]

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


_ensure_project_root_on_path()
