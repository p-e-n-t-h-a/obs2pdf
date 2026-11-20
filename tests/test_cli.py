import argparse

import pytest

from obs2pdf import __version__
from obs2pdf.cli import build_parser, overrides_from_args


def parse(*argv: str) -> argparse.Namespace:
    return build_parser().parse_args(list(argv))


def test_flags_default_to_not_given_so_config_applies():
    args = parse("note.md")
    assert args.path == "note.md"
    assert args.template is None
    assert args.profile is None
    assert args.outline is None
    assert args.print_friendly is None
    assert args.catppuccin_flavor is None
    assert overrides_from_args(args) == {}


def test_template_choice_rejects_unknown_template():
    with pytest.raises(SystemExit):
        parse("note.md", "--template", "does-not-exist")


def test_builtin_templates_are_choices():
    for name in ("notes", "minutes", "report", "letter", "cheatsheet", "handout"):
        assert parse("note.md", "--template", name).template == name


def test_overrides_map_flags_onto_config_schema():
    args = parse(
        "note.md",
        "-p",
        "club",
        "--template",
        "minutes",
        "-a",
        "Jane Doe",
        "--affiliation",
        "Line 1",
        "--affiliation",
        "Line 2",
        "--no-outline",
        "--catppuccin-flavor",
        "none",
        "--print-friendly",
    )
    assert overrides_from_args(args) == {
        "profile": "club",
        "template": "minutes",
        "author": "Jane Doe",
        "affiliation": ["Line 1", "Line 2"],
        "outline": False,
        "theme": {"flavor": "none", "print_friendly": True},
    }


def test_font_flags_map_onto_fonts_table():
    args = parse("note.md", "--font", "Source Serif 4", "--mono", "Fira Code")
    assert overrides_from_args(args) == {"fonts": {"body": "Source Serif 4", "mono": "Fira Code"}}
    assert overrides_from_args(parse("note.md", "--mono", "Fira Code")) == {
        "fonts": {"mono": "Fira Code"}
    }


def test_font_size_flag_parsed_as_float():
    assert overrides_from_args(parse("note.md", "--font-size", "11.5")) == {"fonts": {"size": 11.5}}


def test_outline_depth_parsed_as_int():
    args = parse("note.md", "--outline", "--outline-depth", "2")
    assert overrides_from_args(args) == {"outline": True, "outline_depth": 2}


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        parse("--version")
    assert excinfo.value.code == 0
    assert capsys.readouterr().out.strip() == f"obs2pdf {__version__}"


def test_no_print_friendly_flag():
    assert overrides_from_args(parse("note.md", "--no-print-friendly")) == {
        "theme": {"print_friendly": False}
    }
