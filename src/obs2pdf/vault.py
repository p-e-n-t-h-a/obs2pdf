"""Filesystem helpers for locating attachments and the enclosing Obsidian
vault, used by embed resolution and to pick the Typst compile root."""

from __future__ import annotations

import os

VAULT_ROOT_SEARCH_MAX_LEVELS = 25


def find_attachment(filename: str, search_root: str) -> str | None:
    """Search search_root and every subdirectory for a file named exactly
    `filename`, returning the first match (or None)."""
    for dirpath, _dirnames, filenames in os.walk(search_root):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None


def find_vault_root(start_dir: str) -> str | None:
    """Walk upward from start_dir looking for a directory containing an
    `.obsidian` folder (the marker of an Obsidian vault root). Capped at
    VAULT_ROOT_SEARCH_MAX_LEVELS parent directories, and stops at the
    filesystem root, so it can never scan an unbounded amount of the
    filesystem even if no vault is ever found."""
    current = os.path.abspath(start_dir)
    for _ in range(VAULT_ROOT_SEARCH_MAX_LEVELS):
        if os.path.isdir(os.path.join(current, ".obsidian")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent
    return None
