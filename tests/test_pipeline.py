"""convert() end to end, with pandoc and typst replaced by stand-ins."""

import json
import os

import pytest

from obs2pdf import pipeline


@pytest.fixture
def fake_tools(monkeypatch, tmp_path):
    """Stub out pandoc and typst; record each typst invocation along with the
    .typ source it was given (read while it still exists)."""
    monkeypatch.setenv("OBS2PDF_CONFIG", str(tmp_path / "no-config.toml"))
    monkeypatch.setattr(pipeline, "check_external_dependencies", lambda: None)
    monkeypatch.setattr(pipeline.pypandoc, "convert_text", lambda text, to, format: text)
    calls = []

    def fake_run(cmd, check):
        typst_path = cmd[-2]
        with open(typst_path, encoding="utf-8") as f:
            source = f.read()
        inputs = json.loads(cmd[cmd.index("--input") + 1].removeprefix("obs2pdf="))
        calls.append({"cmd": cmd, "typst_path": typst_path, "source": source, "inputs": inputs})

    monkeypatch.setattr(pipeline.subprocess, "run", fake_run)
    return calls


def write_note(directory, text, name="note.md"):
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def test_convert_passes_settings_as_json_and_cleans_up(fake_tools, tmp_path):
    note = write_note(tmp_path, "---\nobs2pdf.author: Jane\n---\n# My Title\n\nBody\n")
    pdf = pipeline.convert(str(note), user_config={})

    assert pdf == str(tmp_path / "note.pdf")
    (call,) = fake_tools
    assert call["inputs"]["title"] == "My Title"
    assert call["inputs"]["author"] == "Jane"
    assert call["inputs"]["filename"] == "note.md"
    assert "#let obs2pdf-base" in call["source"]
    assert "#obs2pdf-body[" in call["source"]
    # The temporary source sits next to the note and is removed afterwards.
    assert os.path.dirname(call["typst_path"]) == str(tmp_path)
    assert not os.path.exists(call["typst_path"])
    assert os.listdir(tmp_path) == ["note.md"]


def test_convert_never_touches_an_existing_typ_file(fake_tools, tmp_path):
    note = write_note(tmp_path, "Body\n")
    own = tmp_path / "note.typ"
    own.write_text("// the user's own file")

    pipeline.convert(str(note), user_config={})

    assert fake_tools[0]["typst_path"] != str(own)
    assert own.read_text() == "// the user's own file"


def test_keep_typst_writes_note_typ(fake_tools, tmp_path):
    note = write_note(tmp_path, "Body\n")
    pipeline.convert(str(note), keep_typst=True, user_config={})

    assert fake_tools[0]["typst_path"] == str(tmp_path / "note.typ")
    assert (tmp_path / "note.typ").read_text(encoding="utf-8") == fake_tools[0]["source"]


def test_temporary_typ_file_is_removed_when_typst_fails(monkeypatch, fake_tools, tmp_path):
    note = write_note(tmp_path, "Body\n")

    def failing_run(cmd, check):
        raise pipeline.subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(pipeline.subprocess, "run", failing_run)
    with pytest.raises(pipeline.subprocess.CalledProcessError):
        pipeline.convert(str(note), user_config={})
    assert os.listdir(tmp_path) == ["note.md"]


def test_title_falls_back_to_filename(fake_tools, tmp_path):
    note = write_note(tmp_path, "No heading here\n", name="my_meeting_notes.md")
    pipeline.convert(str(note), user_config={})
    assert fake_tools[0]["inputs"]["title"] == "my meeting notes"


def test_multiple_h1_keep_their_headings(fake_tools, tmp_path):
    note = write_note(tmp_path, "# Part One\n\nA\n\n# Part Two\n\nB\n")
    pipeline.convert(str(note), user_config={})
    assert fake_tools[0]["inputs"]["title"] == "note"


def test_open_tasks_are_collected(fake_tools, tmp_path):
    note = write_note(tmp_path, "- [ ] open one\n- [x] done\n")
    pipeline.convert(str(note), user_config={})
    assert fake_tools[0]["inputs"]["action_items"] == ["open one"]


def test_file_settings_resolve_relative_to_note_and_widen_root(fake_tools, tmp_path):
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    note = write_note(vault, "Body\n")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "logo.png").write_bytes(b"png")

    pipeline.convert(str(note), overrides={"logo": "../assets/logo.png"}, user_config={})

    call = fake_tools[0]
    root = call["cmd"][call["cmd"].index("--root") + 1]
    assert root == str(tmp_path)
    assert call["inputs"]["logo"] == "/assets/logo.png"


def test_missing_file_setting_is_an_error(fake_tools, tmp_path):
    note = write_note(tmp_path, "Body\n")
    with pytest.raises(ValueError, match="file not found"):
        pipeline.convert(str(note), overrides={"bibliography": "refs.bib"}, user_config={})


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"template": "nope"}, "unknown template"),
        ({"theme": {"flavor": "dark"}}, "unknown catppuccin flavor"),
        ({"theme": {"accent": "purple"}}, "unknown catppuccin accent"),
        ({"outline_depth": -1}, "outline_depth"),
        ({"letter": {"style": "posh"}}, "unknown letter style"),
    ],
)
def test_invalid_settings_are_rejected(overrides, message, fake_tools, tmp_path):
    note = write_note(tmp_path, "Body\n")
    with pytest.raises(ValueError, match=message):
        pipeline.convert(str(note), overrides=overrides, user_config={})
    assert fake_tools == []
