import pytest

from obs2pdf.preprocess import (
    delete_enclosed_text,
    delete_html_comments,
    extract_open_tasks,
    extract_title_heading,
    normalize_for_pandoc,
    remove_obsidian_links,
    resolve_obsidian_embeds,
    split_frontmatter,
)


def test_remove_obsidian_links_plain_wiki_link():
    text = "see [[Some Note]] for details"
    result = remove_obsidian_links(text)
    assert result == "see PRE-LINK-HASHSome NotePOST-LINK-HASH for details"


def test_remove_obsidian_links_piped_display_text():
    text = "see [[Some Note|display text]] for details"
    result = remove_obsidian_links(text)
    assert result == "see PRE-LINK-HASHdisplay textPOST-LINK-HASH for details"


def test_remove_obsidian_links_heading_anchor():
    text = "see [[Some Note#Section]] for details"
    result = remove_obsidian_links(text)
    assert result == "see PRE-LINK-HASHSectionPOST-LINK-HASH for details"


def test_remove_obsidian_links_highlight():
    text = "this is ==important== text"
    result = remove_obsidian_links(text)
    assert result == "this is PRE-HIGHLIGHT-HASHimportantPOST-HIGHLIGHT-HASH text"


def test_remove_obsidian_links_multiple_links():
    text = "[[A]] and [[B]]"
    result = remove_obsidian_links(text)
    assert result == "PRE-LINK-HASHAPOST-LINK-HASH and PRE-LINK-HASHBPOST-LINK-HASH"


def test_delete_enclosed_text_strips_obsidian_comment():
    text = "before %%secret comment%% after"
    assert delete_enclosed_text(text) == "before  after"


def test_delete_enclosed_text_strips_multiple_comments():
    text = "%%one%% keep %%two%%"
    assert delete_enclosed_text(text) == " keep "


def test_delete_html_comments_single_line():
    text = "before <!-- hidden --> after"
    assert delete_html_comments(text) == "before  after"


def test_delete_html_comments_multiline():
    text = "before <!--\nhidden\nmulti-line\n--> after"
    assert delete_html_comments(text) == "before  after"


def test_extract_title_heading_found():
    text = "# My Title\n\nSome body text.\n"
    title, remaining = extract_title_heading(text)
    assert title == "My Title"
    assert "# My Title" not in remaining
    assert "Some body text." in remaining


def test_extract_title_heading_not_found():
    text = "## Not an H1\n\nbody\n"
    title, remaining = extract_title_heading(text)
    assert title is None
    assert remaining == text


def test_normalize_for_pandoc_blank_line_before_heading():
    text = "some text\n# Heading"
    result = normalize_for_pandoc(text)
    assert "some text\n\n# Heading" in result


def test_normalize_for_pandoc_blank_line_before_list():
    text = "a paragraph\n- item one\n- item two"
    result = normalize_for_pandoc(text)
    assert "a paragraph\n\n- item one" in result


def test_normalize_for_pandoc_arrows():
    text = "a -> b and c => d"
    result = normalize_for_pandoc(text)
    assert result == r"a $\rightarrow$ b and c $\implies$ d"


def test_resolve_obsidian_embeds_image_found(tmp_path):
    note_dir = tmp_path / "note_dir"
    note_dir.mkdir()
    (note_dir / "picture.png").write_bytes(b"fake-image-bytes")
    text = "before ![[picture.png]] after"
    result = resolve_obsidian_embeds(text, str(note_dir))
    assert result == "before ![](picture.png) after"


def test_resolve_obsidian_embeds_image_with_width(tmp_path):
    note_dir = tmp_path / "note_dir"
    note_dir.mkdir()
    (note_dir / "picture.png").write_bytes(b"fake-image-bytes")
    text = "![[picture.png|300]]"
    result = resolve_obsidian_embeds(text, str(note_dir))
    assert result == '![](picture.png){width="300px"}'


def test_resolve_obsidian_embeds_not_found_left_inert():
    text = "before ![[missing.png]] after"
    result = resolve_obsidian_embeds(text, "/nonexistent/dir")
    assert result == r"before \![\[missing.png\]\] after"


def test_resolve_obsidian_embeds_note_transclusion(tmp_path):
    note_dir = tmp_path / "note_dir"
    note_dir.mkdir()
    (note_dir / "Other Note.md").write_text("transcluded content", encoding="utf-8")
    text = "before ![[Other Note]] after"
    result = resolve_obsidian_embeds(text, str(note_dir))
    assert result == "before transcluded content after"


def test_resolve_obsidian_embeds_self_reference_guarded(tmp_path):
    note_dir = tmp_path / "note_dir"
    note_dir.mkdir()
    (note_dir / "Loop.md").write_text("![[Loop]]", encoding="utf-8")
    text = "![[Loop]]"
    result = resolve_obsidian_embeds(text, str(note_dir))
    # The first ![[Loop]] resolves into Loop.md's own content, which is
    # itself "![[Loop]]" — that inner reference must not recurse forever.
    assert result == r"\![\[Loop\]\]"


def test_resolve_obsidian_embeds_falls_back_to_vault_root(tmp_path):
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / ".obsidian").mkdir()
    attachments = vault_root / "attachments"
    attachments.mkdir()
    (attachments / "picture.png").write_bytes(b"fake-image-bytes")

    note_dir = vault_root / "notes" / "sub"
    note_dir.mkdir(parents=True)

    text = "![[picture.png]]"
    result = resolve_obsidian_embeds(text, str(note_dir))
    assert result == "![](../../attachments/picture.png)"


def test_split_frontmatter_parses_yaml_and_strips_it():
    data, body = split_frontmatter("---\nobs2pdf:\n  template: minutes\n---\n# Title\n")
    assert data == {"obs2pdf": {"template": "minutes"}}
    assert body == "# Title\n"


def test_split_frontmatter_without_frontmatter():
    assert split_frontmatter("# Title\n---\nx\n") == ({}, "# Title\n---\nx\n")


def test_split_frontmatter_empty_block():
    assert split_frontmatter("---\n---\nbody") == ({}, "body")


def test_split_frontmatter_invalid_yaml_raises():
    with pytest.raises(ValueError):
        split_frontmatter("---\nkey: [unclosed\n---\nbody")


def test_transcluded_note_frontmatter_is_dropped(tmp_path):
    (tmp_path / "Other.md").write_text("---\ntags: [x]\n---\nEmbedded text")
    result = resolve_obsidian_embeds("Before\n![[Other]]\nAfter", str(tmp_path))
    assert result == "Before\nEmbedded text\nAfter"


def test_extract_open_tasks_strips_markup():
    text = (
        "- [ ] **Jordan** books [[Venue|the venue]] by [[2027-01-15]]\n"
        "- [x] done already\n"
        "  * [ ] nested `task` with [link](http://x)\n"
        "not a - [ ] task\n"
    )
    assert extract_open_tasks(text) == [
        "Jordan books the venue by 2027-01-15",
        "nested task with link",
    ]
