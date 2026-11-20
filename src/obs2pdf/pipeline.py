"""Core conversion pipeline: raw Markdown -> settings resolution -> Pandoc
-> Typst post-processing -> template assembly -> typst compile."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from typing import Any

import pypandoc

from . import config
from .catppuccin import CATPPUCCIN_ACCENTS, CATPPUCCIN_FLAVORS
from .deps import check_external_dependencies
from .postprocess import (
    PART_BREAK_MARKER,
    activate_typst_internal_link,
    fix_table_column_widths,
    recreate_checkboxes,
    shift_heading_depths,
    wrap_page_parts,
)
from .preprocess import (
    HEADING1_RE,
    delete_enclosed_text,
    delete_html_comments,
    extract_open_tasks,
    extract_title_heading,
    normalize_for_pandoc,
    remove_obsidian_links,
    resolve_obsidian_embeds,
    split_frontmatter,
)
from .templates import available_templates, template_source
from .vault import find_vault_root

# Settings that name a file; resolved relative to the note and passed to
# Typst as paths relative to the compile root.
FILE_SETTINGS = ("logo", "bibliography")


def read_note(path: str) -> tuple[dict[str, Any], str]:
    """The note's obs2pdf frontmatter settings (the `obs2pdf:` mapping and
    any `obs2pdf.*` dotted keys) and its Markdown body."""
    with open(path, encoding="utf-8") as file:
        frontmatter, body = split_frontmatter(file.read())
    return config.frontmatter_settings(frontmatter), body


def resolve_settings(
    path: str | None = None,
    overrides: dict[str, Any] | None = None,
    user_config: dict[str, Any] | None = None,
) -> config.Resolved:
    """Resolve every config layer for the note at `path` (frontmatter is
    skipped if path is None) and validate the result."""
    frontmatter = read_note(path)[0] if path else {}
    if user_config is None:
        user_config = config.load_user_config()
    resolved = config.resolve(
        cli=overrides,
        frontmatter=frontmatter,
        user_config=user_config,
        user_config_name=config.display_path(config.config_path()),
    )
    validate(resolved.settings)
    return resolved


def validate(settings: dict[str, Any]) -> None:
    templates = available_templates()
    if settings["template"] not in templates:
        raise ValueError(
            f"unknown template {settings['template']!r}; choose one of {sorted(templates)}"
        )
    flavor = settings["theme"]["flavor"]
    if flavor != "none" and flavor not in CATPPUCCIN_FLAVORS:
        raise ValueError(
            f"unknown catppuccin flavor {flavor!r}; choose one of {(*CATPPUCCIN_FLAVORS, 'none')}"
        )
    accent = settings["theme"]["accent"]
    if accent not in CATPPUCCIN_ACCENTS:
        raise ValueError(
            f"unknown catppuccin accent {accent!r}; choose one of {CATPPUCCIN_ACCENTS}"
        )
    depth = settings["outline_depth"]
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 0:
        raise ValueError(f"outline_depth must be a non-negative integer, got {depth!r}")
    size = settings["fonts"]["size"]
    if not isinstance(size, (int, float)) or isinstance(size, bool) or size <= 0:
        raise ValueError(f"fonts.size must be a positive number (points), got {size!r}")


def resolve_file_setting(value: str, note_dir: str) -> str:
    path = os.path.expanduser(value)
    if not os.path.isabs(path):
        path = os.path.join(note_dir, path)
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        raise ValueError(f"file not found: {value} (resolved to {path})")
    return path


def typst_root_for(base_root: str, files: list[str]) -> str:
    """Typst can only read files under --root, so widen it to the common
    ancestor of the vault and any referenced file outside it (e.g. a logo in
    ~/.config/obs2pdf/)."""
    if not files:
        return base_root
    return os.path.commonpath([base_root, *(os.path.dirname(f) for f in files)])


def convert(
    path: str,
    overrides: dict[str, Any] | None = None,
    output: str | None = None,
    keep_typst: bool = False,
    user_config: dict[str, Any] | None = None,
) -> str:
    """Convert the note at `path` to PDF and return the PDF's path.

    `overrides` is a partial settings dict (same schema as defaults.toml,
    plus an optional `profile` key) layered on top of the user config and
    the note's frontmatter — this is what the CLI flags turn into.
    """
    check_external_dependencies()

    resolved = resolve_settings(path, overrides, user_config)
    for warning in resolved.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    settings = resolved.settings

    _, content = read_note(path)
    note_dir = os.path.dirname(os.path.abspath(path))
    vault_root = find_vault_root(note_dir) or note_dir

    content = resolve_obsidian_embeds(content, note_dir)
    action_items = extract_open_tasks(content)
    # A note with more than one level-1 heading has no single title to pull
    # out: all of its H1s are instead kept in the body and rendered inline as
    # their own title-styled headings (see shift_heading_depths /
    # wrap_page_parts below).
    if len(HEADING1_RE.findall(content)) > 1:
        heading_title = None
    else:
        heading_title, content = extract_title_heading(content)
    content = remove_obsidian_links(content)
    content = delete_enclosed_text(content)
    content = delete_html_comments(content)
    content = normalize_for_pandoc(content)

    content = pypandoc.convert_text(content, "typst", format="md")
    content = shift_heading_depths(content)
    has_multiple_h1 = PART_BREAK_MARKER in content

    content = activate_typst_internal_link(content)
    content = recreate_checkboxes(content)
    content = fix_table_column_widths(content)
    content = "#obs2pdf-inline-outline()\n" + content
    content = wrap_page_parts(content, "#obs2pdf-body[\n", "\n]\n")

    name_path, _ = os.path.splitext(path)
    title = settings["title"] or heading_title or os.path.basename(name_path).replace("_", " ")

    files = {
        key: resolve_file_setting(settings[key], note_dir) for key in FILE_SETTINGS if settings[key]
    }
    typst_root = typst_root_for(vault_root, list(files.values()))

    data = dict(settings)
    data.update(
        title=title,
        filename=os.path.basename(path),
        has_multiple_h1=has_multiple_h1,
        action_items=action_items,
    )
    for key, file_path in files.items():
        # A leading "/" makes Typst resolve the path against --root.
        data[key] = "/" + os.path.relpath(file_path, typst_root).replace(os.sep, "/")

    typst_source = template_source(settings["template"]) + content
    # The .typ file must sit next to the note so its relative image paths
    # resolve. Only --keep-typst writes `<note>.typ`; otherwise a uniquely
    # named hidden file is used, so an existing `<note>.typ` is never
    # overwritten and concurrent runs on the same note don't collide.
    if keep_typst:
        typst_path = name_path + ".typ"
    else:
        fd, typst_path = tempfile.mkstemp(
            dir=note_dir, prefix=f".{os.path.basename(name_path)}.", suffix=".obs2pdf.typ"
        )
        os.close(fd)
    with open(typst_path, "w", encoding="utf-8") as file:
        file.write(typst_source)

    pdf_path = output or (name_path + ".pdf")
    cmd = [
        "typst",
        "compile",
        "--root",
        typst_root,
        "--input",
        "obs2pdf=" + json.dumps(data, ensure_ascii=False, default=str),
        typst_path,
        pdf_path,
    ]
    try:
        subprocess.run(cmd, check=True)
    finally:
        if not keep_typst:
            os.remove(typst_path)

    return pdf_path
