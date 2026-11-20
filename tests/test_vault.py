from obs2pdf.vault import find_attachment, find_vault_root


def test_find_attachment_in_root(tmp_path):
    (tmp_path / "picture.png").write_bytes(b"data")
    found = find_attachment("picture.png", str(tmp_path))
    assert found == str(tmp_path / "picture.png")


def test_find_attachment_in_subdirectory(tmp_path):
    sub = tmp_path / "sub" / "deeper"
    sub.mkdir(parents=True)
    (sub / "picture.png").write_bytes(b"data")
    found = find_attachment("picture.png", str(tmp_path))
    assert found == str(sub / "picture.png")


def test_find_attachment_not_found(tmp_path):
    assert find_attachment("missing.png", str(tmp_path)) is None


def test_find_vault_root_finds_ancestor_with_obsidian_dir(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    note_dir = vault / "notes" / "sub"
    note_dir.mkdir(parents=True)

    assert find_vault_root(str(note_dir)) == str(vault)


def test_find_vault_root_returns_none_when_absent(tmp_path):
    note_dir = tmp_path / "notes" / "sub"
    note_dir.mkdir(parents=True)

    assert find_vault_root(str(note_dir)) is None


def test_find_vault_root_start_dir_itself_is_root(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)

    assert find_vault_root(str(vault)) == str(vault)
