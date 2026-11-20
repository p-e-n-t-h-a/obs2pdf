from obs2pdf.postprocess import (
    PART_BREAK_MARKER,
    activate_typst_internal_link,
    fix_table_column_widths,
    recreate_checkboxes,
    shift_heading_depths,
    wrap_page_parts,
)


def test_activate_typst_internal_link():
    text = "PRE-LINK-HASHSome NotePOST-LINK-HASH and PRE-HIGHLIGHT-HASHwordPOST-HIGHLIGHT-HASH"
    result = activate_typst_internal_link(text)
    assert result == ("#obs2pdf-wikilink([Some Note]) and #highlight([word])")


def test_recreate_checkboxes():
    text = "- ☒ done\n- ☐ todo\n"
    result = recreate_checkboxes(text)
    assert result == "- [x] done\n- [ ] todo\n"


def test_fix_table_column_widths_replaces_percentages():
    text = "#table(\n  columns: (5.88%, 94.12%),\n  ...\n)"
    result = fix_table_column_widths(text)
    assert "columns: (auto, auto)" in result


def test_fix_table_column_widths_leaves_non_percentage_columns_alone():
    text = "#table(\n  columns: (auto, 1fr),\n  ...\n)"
    result = fix_table_column_widths(text)
    assert result == text


def test_shift_heading_depths_shifts_up_one_level():
    text = "== Section\n=== Subsection\nplain line"
    result = shift_heading_depths(text)
    assert "= Section" in result
    assert "== Subsection" in result
    assert "plain line" in result


def test_shift_heading_depths_marks_extra_h1_as_part_break():
    text = "= Extra Part Title"
    result = shift_heading_depths(text)
    assert result == PART_BREAK_MARKER + "Extra Part Title"


def test_wrap_page_parts_no_parts_just_wraps():
    body = "some content"
    result = wrap_page_parts(body, "<open>", "<close>")
    assert result == "<open>some content<close>"


def test_wrap_page_parts_splits_and_labels_each_part():
    body = (
        "intro"
        + PART_BREAK_MARKER
        + "Part One\nbody one"
        + PART_BREAK_MARKER
        + "Part Two\nbody two"
    )
    result = wrap_page_parts(body, "OPEN", "CLOSE")
    assert result.startswith("OPEN")
    assert result.endswith("CLOSE")
    assert "intro" in result
    assert "#heading(depth: 1, numbering: none)[Part One] <obs2pdf-part-title>" in result
    assert "#counter(heading).update(0)" in result
    assert "body one" in result
    assert "#heading(depth: 1, numbering: none)[Part Two] <obs2pdf-part-title>" in result
    assert "body two" in result


def test_wrap_page_parts_drops_pandoc_anchor_label_line():
    body = PART_BREAK_MARKER + "Part One\n<some-pandoc-label>\nbody one"
    result = wrap_page_parts(body, "", "")
    assert "<some-pandoc-label>" not in result
    assert "body one" in result
