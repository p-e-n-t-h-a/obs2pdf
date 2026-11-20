"""Checks for the external (non-Python) binaries obs2pdf shells out to."""

from __future__ import annotations

import shutil

EXTERNAL_DEPENDENCIES = (
    ("pandoc", "https://pandoc.org"),
    ("typst", "https://typst.app"),
)


def check_external_dependencies() -> None:
    """Fail fast with an actionable message if pandoc/typst aren't on PATH,
    instead of letting a missing binary surface as an opaque OSError/
    CalledProcessError partway through conversion."""
    missing = [(cmd, url) for cmd, url in EXTERNAL_DEPENDENCIES if shutil.which(cmd) is None]
    if not missing:
        return
    lines = ["missing required dependencies:"]
    lines.extend(f"  - {cmd} (install from {url})" for cmd, url in missing)
    raise RuntimeError("\n".join(lines))
