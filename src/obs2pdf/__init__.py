"""obs2pdf: turn an Obsidian-flavoured Markdown note into a typeset PDF via
Pandoc and Typst."""

from __future__ import annotations

from .pipeline import convert

__version__ = "0.1.0"
__all__ = ["__version__", "convert"]
