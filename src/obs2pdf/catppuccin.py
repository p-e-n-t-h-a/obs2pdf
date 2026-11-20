"""Catppuccin flavor/accent names accepted on the CLI. The actual color
resolution (mapping a flavor/accent/print-friendly combination to concrete
colors) lives in Typst, in templates/_theme.typ, alongside the rest of the
presentation — see that file for the heading/role color policy. This module
only needs to know the valid names, to validate settings and expose them as
argparse choices; the defaults live in defaults.toml."""

from __future__ import annotations

CATPPUCCIN_FLAVORS = ("latte", "frappe", "macchiato", "mocha")
CATPPUCCIN_ACCENTS = (
    "rosewater",
    "flamingo",
    "pink",
    "mauve",
    "red",
    "maroon",
    "peach",
    "yellow",
    "green",
    "teal",
    "sky",
    "sapphire",
    "blue",
    "lavender",
)
