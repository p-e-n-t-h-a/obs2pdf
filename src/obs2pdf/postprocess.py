"""Post-processing of the Typst source pandoc emits, before it's wrapped in
a template preamble and compiled."""

from __future__ import annotations

import re


def activate_typst_internal_link(text: str) -> str:
    """Replace the placeholders inserted by preprocess.remove_obsidian_links()
    with actual Typst markup, after the pandoc conversion has run. Wiki links
    call the obs2pdf-wikilink() helper from templates/_base.typ, so their
    styling lives in Typst with the rest of the theme."""
    text = text.replace("PRE-LINK-HASH", "#obs2pdf-wikilink([")
    text = text.replace("POST-LINK-HASH", "])")
    text = text.replace("PRE-HIGHLIGHT-HASH", "#highlight([")
    text = text.replace("POST-HIGHLIGHT-HASH", "])")
    return text


def recreate_checkboxes(text: str) -> str:
    """Pandoc emits Unicode checkbox glyphs; turn them back into Typst-Markdown
    task list syntax."""
    text = text.replace("- ☒ ", "- [x] ")
    text = text.replace("- ☐ ", "- [ ] ")
    return text


TABLE_COLUMNS_RE = re.compile(r"columns:\s*\(([^)]*)\)")


def fix_table_column_widths(text: str) -> str:
    """Pandoc derives #table columns widths from the *source* pipe-table's
    dash-separator lengths (e.g. `columns: (5.88%, 94.12%)`), which rarely
    matches how wide the actual cell content is. A narrow percentage forces
    Typst to lay out that column at a fixed width regardless of content,
    so text overflows the cell/page border instead of wrapping. Replacing
    every percentage width with `auto` lets Typst size each column to fit
    its content within the available page width instead."""

    def replace(match: re.Match) -> str:
        widths = match.group(1)
        if "%" not in widths:
            return match.group(0)
        fixed = re.sub(r"[\d.]+%", "auto", widths)
        return f"columns: ({fixed})"

    return TABLE_COLUMNS_RE.sub(replace, text)


TYPST_HEADING_RE = re.compile(r"^(=+)( .*)$")

# Marks where a leftover H1 (a "part title") should go; resolved into an
# actual page break + heading by wrap_page_parts() once the whole body is
# known, since a #pagebreak() can't appear inside the #columns(..) container
# each part's flowing text lives in.
PART_BREAK_MARKER = "\x00OBS2PDF-PART-BREAK\x00"


def shift_heading_depths(text: str) -> str:
    """Shift every remaining heading up one level (## -> #, ### -> ##, ...),
    so that H2 becomes the top-level numbered section, matching how the
    note's H1 was already pulled out as the document title. Any leftover H1
    is marked with PART_BREAK_MARKER for wrap_page_parts() to turn into
    another title line."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        match = TYPST_HEADING_RE.match(line)
        if match is None:
            continue
        depth = len(match.group(1))
        rest = match.group(2).strip()
        if depth == 1:
            lines[i] = PART_BREAK_MARKER + rest
        else:
            lines[i] = "=" * (depth - 1) + " " + rest
    return "\n".join(lines)


LABEL_LINE_RE = re.compile(r"^<[\w-]+>$")


def wrap_page_parts(body: str, columns_open: str, columns_close: str) -> str:
    """Split body at each PART_BREAK_MARKER (a note's level-1 headings, once
    there is more than one of them) and render each as an unnumbered,
    title-styled heading that resets the heading counter, so numbering
    starts over for each new part. All parts stay inline in one continuous
    columns block, alongside the outline (if any), rather than each getting
    its own page.

    Each part title is tagged with the <obs2pdf-part-title> label so the
    template can select and style it unambiguously, regardless of whatever
    heading-numbering rules apply elsewhere (e.g. the minutes template's "TOP 1" scheme).
    That leaves no room for pandoc's own anchor label (a heading can only
    carry one label), so that one is simply dropped.
    """
    segments = body.split(PART_BREAK_MARKER)
    parts = [segments[0]]

    for segment in segments[1:]:
        title_line, _, rest = segment.partition("\n")
        rest_first_line, sep, rest_tail = rest.partition("\n")
        if LABEL_LINE_RE.match(rest_first_line.strip()):
            rest = rest_tail if sep else ""

        parts.append(
            f"#heading(depth: 1, numbering: none)[{title_line.strip()}] <obs2pdf-part-title>\n"
            "#counter(heading).update(0)\n" + rest
        )

    return columns_open + "\n".join(parts) + columns_close
