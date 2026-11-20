"""Template discovery and assembly.

A template is a single .typ file named after the document type it produces.
Built-in ones live in src/obs2pdf/templates/; users can add more (or replace
a built-in one) by dropping a .typ file into ~/.config/obs2pdf/templates/.
Files starting with "_" are shared helpers, not templates.

Every template gets the shared helpers (_theme.typ, then _base.typ)
concatenated in front of it — concatenated rather than linked via Typst's
own `#import`, since the combined file is written into the note's own
directory (so the note's relative image paths resolve), where a path-based
import of the helpers would break.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from .config import user_templates_dir

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

SHARED_HELPERS = ("_theme.typ", "_base.typ")

BUILTIN_TEMPLATES = ("notes", "minutes", "report", "letter", "cheatsheet", "handout")


def _builtin_dir() -> Traversable:
    # "templates" is a plain data directory (no __init__.py), so it's
    # addressed as a subpath of the obs2pdf package rather than imported.
    return resources.files("obs2pdf").joinpath("templates")


def available_templates(user_dir: Path | None = None) -> dict[str, Traversable | Path]:
    """Template name -> file, user templates overriding built-in ones."""
    found: dict[str, Traversable | Path] = {
        name: _builtin_dir().joinpath(f"{name}.typ") for name in BUILTIN_TEMPLATES
    }
    user_dir = user_dir if user_dir is not None else user_templates_dir()
    if user_dir.is_dir():
        for path in sorted(user_dir.glob("*.typ")):
            if not path.name.startswith("_"):
                found[path.stem] = path
    return found


def template_source(name: str, user_dir: Path | None = None) -> str:
    """The full Typst preamble for template `name`: shared helpers followed
    by the template file itself."""
    templates = available_templates(user_dir)
    if name not in templates:
        raise ValueError(f"unknown template {name!r}; choose one of {sorted(templates)}")
    helpers = [
        _builtin_dir().joinpath(helper).read_text(encoding="utf-8") for helper in SHARED_HELPERS
    ]
    own = templates[name].read_text(encoding="utf-8")
    return "\n".join([*helpers, own]) + "\n"
