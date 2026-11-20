"""Pre-processing of the raw Obsidian-flavoured Markdown, before it goes
through Pandoc. Regex/string based, not a real Markdown parser."""

from __future__ import annotations

import contextlib
import os
import re
from typing import Any

import yaml

from .vault import find_attachment, find_vault_root

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?\n)?(?:---|\.\.\.)[ \t]*(?:\n|\Z)", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a leading YAML frontmatter block off the note. Returns the parsed
    mapping ({} if there is none) and the remaining body. Invalid YAML is
    reported as a ValueError rather than silently ignored, since the
    frontmatter may carry obs2pdf settings."""
    match = FRONTMATTER_RE.match(text.lstrip("\ufeff"))
    if match is None:
        return {}, text
    try:
        data = yaml.safe_load(match.group(1) or "")
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("YAML frontmatter must be a mapping")
    return data, text.lstrip("\ufeff")[match.end() :]


OBSIDIAN_EMBED_RE = re.compile(r"!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")


def resolve_obsidian_embeds(
    text: str, search_root: str, _embedding_stack: tuple[str, ...] = ()
) -> str:
    """Turn Obsidian ![[image.png]] embeds into real Markdown images, and
    ![[Note Name]] / ![[Note Name.md]] embeds into the transcluded note's
    contents (resolved recursively), by locating the referenced file under
    search_root. If not found there, falls back to searching the whole
    Obsidian vault (the nearest ancestor directory containing `.obsidian`,
    found via find_vault_root) so embeds referencing files outside the
    note's own subtree still resolve. Embeds that can't be found, or that
    would recurse into a note already being embedded, are left as plain,
    inert text instead of a broken image."""

    def replace(match: re.Match) -> str:
        embed_name = match.group(1).strip()
        width = (match.group(2) or "").strip()

        found_path = find_attachment(embed_name, search_root)
        if found_path is None and "." not in os.path.basename(embed_name):
            found_path = find_attachment(embed_name + ".md", search_root)
        if found_path is None:
            vault_root = find_vault_root(search_root)
            if vault_root is not None and vault_root != search_root:
                found_path = find_attachment(embed_name, vault_root)
                if found_path is None and "." not in os.path.basename(embed_name):
                    found_path = find_attachment(embed_name + ".md", vault_root)
        if found_path is None:
            return rf"\![\[{embed_name}\]\]"

        if found_path.lower().endswith(".md"):
            if found_path in _embedding_stack:
                return rf"\![\[{embed_name}\]\]"
            with open(found_path, encoding="utf-8") as f:
                embedded_content = f.read()
            # Invalid frontmatter in an embedded note isn't ours to report;
            # inline that note as-is.
            with contextlib.suppress(ValueError):
                _, embedded_content = split_frontmatter(embedded_content)
            return resolve_obsidian_embeds(
                embedded_content.strip(),
                search_root,
                _embedding_stack + (found_path,),
            )

        rel_path = os.path.relpath(found_path, search_root)
        if any(c in rel_path for c in " \t()"):
            rel_path = f"<{rel_path}>"

        image_md = f"![]({rel_path})"
        if width.isdigit():
            image_md += f'{{width="{width}px"}}'
        return image_md

    return OBSIDIAN_EMBED_RE.sub(replace, text)


HEADING1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*$\n?", re.MULTILINE)


def extract_title_heading(text: str) -> tuple[str | None, str]:
    """Pull out the note's first level-1 heading (if any) to use as the
    document title, removing it from the body so it isn't rendered twice."""
    match = HEADING1_RE.search(text)
    if match is None:
        return None, text
    title = match.group(1).strip()
    remaining = text[: match.start()] + text[match.end() :]
    return title, remaining


OPEN_TASK_RE = re.compile(r"^[ \t]*[-*+][ \t]+\[ \][ \t]+(.+?)[ \t]*$", re.MULTILINE)
WIKI_LINK_RE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
INLINE_MARKUP_RE = re.compile(r"(\*\*|__|==|~~|`)")


def extract_open_tasks(text: str) -> list[str]:
    """Plain-text versions of every unchecked "- [ ] task" in the note, for
    the minutes template's action-item table. Inline markup is stripped
    (wiki links keep their display text) since the result is passed to
    Typst as data, not markup."""
    tasks = []
    for match in OPEN_TASK_RE.finditer(text):
        task = WIKI_LINK_RE.sub(r"\1", match.group(1))
        task = MD_LINK_RE.sub(r"\1", task)
        task = INLINE_MARKUP_RE.sub("", task).strip()
        if task:
            tasks.append(task)
    return tasks


def remove_obsidian_links(text: str) -> str:
    """Turn [[wiki links]] and ==highlights== into placeholder-wrapped text
    that survives the pandoc round-trip, so they can be re-activated as
    Typst markup afterwards."""
    PRE_LINK = "PRE-LINK-HASH"
    POST_LINK = "POST-LINK-HASH"
    PRE_HIGHLIGHT = "PRE-HIGHLIGHT-HASH"
    POST_HIGHLIGHT = "POST-HIGHLIGHT-HASH"

    while True:
        start_index = text.find("[[")
        end_index = text.find("]]", start_index)
        if start_index == -1 or end_index == -1:
            break
        if "|" in text[start_index:end_index]:
            break_index = text[start_index : end_index + 2].find("|")
            linkname = PRE_LINK + text[start_index + break_index + 1 : end_index] + POST_LINK
        elif "#" in text[start_index:end_index]:
            break_index = text[start_index : end_index + 2].find("#")
            linkname = PRE_LINK + text[start_index + break_index + 1 : end_index] + POST_LINK
        else:
            linkname = PRE_LINK + text[start_index + 2 : end_index] + POST_LINK

        text = text[:start_index] + linkname + text[end_index + 2 :]

    while True:
        start_index = text.find("==")
        end_index = text.find("==", start_index + 2)
        if start_index == -1 or end_index == -1:
            break
        linkname = PRE_HIGHLIGHT + text[start_index + 2 : end_index] + POST_HIGHLIGHT
        text = text[:start_index] + linkname + text[end_index + 2 :]

    return text


def delete_enclosed_text(text: str) -> str:
    """Strip Obsidian %%comment%% blocks entirely."""
    while True:
        start_index = text.find("%%")
        end_index = text.find("%%", start_index + 2)
        if start_index == -1 or end_index == -1:
            break
        text = text[:start_index] + text[end_index + 2 :]
    return text


HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def delete_html_comments(text: str) -> str:
    """Strip Markdown/HTML <!-- comment --> blocks entirely."""
    return HTML_COMMENT_RE.sub("", text)


LIST_AFTER_PARAGRAPH_RE = re.compile(
    r"^([^\n#>\-\s].*\S)\n([ \t]*(?:[-*+]|\d+[.)])[ \t]+)", re.MULTILINE
)


def normalize_for_pandoc(text: str) -> str:
    """A few literal/regex fixups that make pandoc's Markdown reader behave
    the way Obsidian notes expect."""
    text = text.replace("\n#", "\n\n#")  # ensure blank line before headings
    # Ensure a blank line before a list that immediately follows a paragraph
    # line: pandoc's markdown reader treats "- item" right after a paragraph
    # (no blank line) as a lazy continuation of that paragraph, not a list.
    text = LIST_AFTER_PARAGRAPH_RE.sub(r"\1\n\n\2", text)
    text = text.replace("->", r"$\rightarrow$")
    text = text.replace("=>", r"$\implies$")
    return text
