from pathlib import Path

import pytest

from obs2pdf import config
from obs2pdf.config import BUILTIN_LAYER, ConfigError, resolve
from obs2pdf.pipeline import validate


def test_config_path_follows_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv("OBS2PDF_CONFIG", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert config.config_path() == tmp_path / "obs2pdf" / "config.toml"
    assert config.user_templates_dir() == tmp_path / "obs2pdf" / "templates"


def test_config_path_defaults_to_dot_config(monkeypatch, tmp_path):
    monkeypatch.delenv("OBS2PDF_CONFIG", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert config.config_path() == tmp_path / ".config" / "obs2pdf" / "config.toml"


def test_explicit_config_env_var_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("OBS2PDF_CONFIG", str(tmp_path / "custom.toml"))
    assert config.config_path() == tmp_path / "custom.toml"


def test_missing_user_config_is_empty(tmp_path):
    assert config.load_user_config(tmp_path / "nope.toml") == {}


def test_invalid_toml_raises_config_error(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("this is = = not toml")
    with pytest.raises(ConfigError):
        config.load_user_config(path)


def test_example_config_is_valid_toml_and_all_commented_out():
    assert config.tomllib.loads(config.example_config_text()) == {}


def test_builtin_defaults_alone():
    resolved = resolve()
    assert resolved.template == "notes"
    assert resolved.profile == ""
    assert resolved.settings["theme"]["print_friendly"] is True
    # print_friendly (on by default) swaps the default dark flavor for latte.
    assert resolved.settings["theme"]["flavor"] == "latte"
    assert resolved.sources["theme.flavor"] == "print_friendly"


USER = {
    "default_profile": "work",
    "author": "Jane Doe",
    "theme": {"accent": "teal"},
    "profiles": {
        "work": {"role": "M. Sc.", "affiliation": "Example University"},
        "club": {
            "role": "Secretary",
            "template": "minutes",
            "lang": "de",
            "minutes": {"chair": "John Roe"},
        },
    },
}


def test_layers_merge_in_precedence_order():
    resolved = resolve(
        cli={"role": "Dr."},
        frontmatter={"profile": "club", "theme": {"flavor": "mocha"}},
        user_config=USER,
    )
    s = resolved.settings
    assert resolved.profile == "club"
    assert resolved.template == "minutes"
    assert s["author"] == "Jane Doe"  # user config
    assert s["lang"] == "de"  # profile
    assert s["minutes"]["chair"] == "John Roe"  # profile, nested
    assert s["minutes"]["signatures"] is True  # built-in, same table
    assert s["theme"] == {**s["theme"], "flavor": "mocha", "accent": "teal"}
    assert s["role"] == "Dr."  # command line beats profile
    assert resolved.sources["role"] == "command line"
    assert resolved.sources["theme.accent"] == "config.toml"
    assert resolved.sources["lang"] == "profile 'club'"


def test_default_profile_used_when_none_selected():
    resolved = resolve(user_config=USER)
    assert resolved.profile == "work"
    assert resolved.settings["affiliation"] == ["Example University"]


def test_cli_profile_beats_frontmatter_profile():
    resolved = resolve(cli={"profile": "work"}, frontmatter={"profile": "club"}, user_config=USER)
    assert resolved.profile == "work"


def test_unknown_profile_raises():
    with pytest.raises(ConfigError, match="unknown profile 'nope'"):
        resolve(cli={"profile": "nope"}, user_config=USER)


def test_template_defaults_apply_below_user_settings():
    resolved = resolve(frontmatter={"template": "report"})
    assert resolved.settings["outline"] is True
    assert resolved.sources["outline"] == "built-in 'report' template defaults"

    resolved = resolve(frontmatter={"template": "report"}, user_config={"outline": False})
    assert resolved.settings["outline"] is False


def test_letter_defaults_to_no_theme():
    resolved = resolve(cli={"template": "letter"})
    assert resolved.settings["theme"]["flavor"] == "none"


def test_font_size_has_per_template_defaults():
    assert resolve().settings["fonts"]["size"] == 10
    assert resolve(cli={"template": "report"}).settings["fonts"]["size"] == 11
    assert resolve(cli={"template": "cheatsheet"}).settings["fonts"]["size"] == 8
    resolved = resolve(cli={"template": "cheatsheet"}, frontmatter={"fonts": {"size": 9}})
    assert resolved.settings["fonts"]["size"] == 9


@pytest.mark.parametrize("size", [0, -1, True, "11pt", None])
def test_invalid_font_size_rejected(size):
    settings = resolve().settings
    settings["fonts"]["size"] = size
    with pytest.raises(ValueError, match="fonts.size"):
        validate(settings)


def test_print_friendly_switches_default_flavor_to_latte():
    assert resolve(cli={"theme": {"print_friendly": True}}).settings["theme"]["flavor"] == "latte"
    chosen = resolve(cli={"theme": {"print_friendly": True, "flavor": "mocha"}})
    assert chosen.settings["theme"]["flavor"] == "mocha"


def test_without_print_friendly_the_default_flavor_applies():
    resolved = resolve(cli={"theme": {"print_friendly": False}})
    assert resolved.settings["theme"]["flavor"] == "macchiato"
    assert resolved.sources["theme.flavor"] == BUILTIN_LAYER


def test_unknown_keys_warn_and_are_dropped():
    resolved = resolve(frontmatter={"autor": "typo", "theme": {"flavour": "x"}})
    assert "autor" not in resolved.settings
    assert any("'autor'" in w for w in resolved.warnings)
    assert any("'theme.flavour'" in w for w in resolved.warnings)


def test_reference_signs_table_is_free_form():
    resolved = resolve(frontmatter={"letter": {"reference_signs": {"Your ref": "AB-12"}}})
    assert resolved.warnings == []
    assert resolved.settings["letter"]["reference_signs"] == {"Your ref": "AB-12"}


def test_strings_are_normalized_to_line_lists():
    resolved = resolve(frontmatter={"affiliation": "One line", "minutes": {"present": "Solo"}})
    assert resolved.settings["affiliation"] == ["One line"]
    assert resolved.settings["minutes"]["present"] == ["Solo"]


def test_minutes_people_accept_unquoted_wiki_links():
    # Unquoted `[[Name]]` is a nested YAML list; it must come back as text.
    resolved = resolve(
        frontmatter={
            "minutes": {
                "chair": [["Alex Example"]],
                "present": ["Chair [[Alex Example]]", [["Jordan Doe"]], "Sam"],
                "absent": [[["Robin Roe"]]],
                "guests": [["Kim Kay"]],
            }
        }
    )
    m = resolved.settings["minutes"]
    assert m["chair"] == "[[Alex Example]]"
    assert m["present"] == ["Chair [[Alex Example]]", "[[Jordan Doe]]", "Sam"]
    assert m["absent"] == ["[[Robin Roe]]"]
    assert m["guests"] == ["[[Kim Kay]]"]


def test_frontmatter_nested_mapping():
    fm = {"tags": ["x"], "obs2pdf": {"template": "minutes", "minutes": {"chair": "A"}}}
    assert config.frontmatter_settings(fm) == {"template": "minutes", "minutes": {"chair": "A"}}


def test_frontmatter_without_settings_is_empty():
    assert config.frontmatter_settings({"tags": ["x"]}) == {}
    assert config.frontmatter_settings({"obs2pdf": None}) == {}


def test_frontmatter_nested_must_be_a_mapping():
    with pytest.raises(ConfigError, match="must be a mapping"):
        config.frontmatter_settings({"obs2pdf": "minutes"})


def test_frontmatter_dotted_keys_nest():
    fm = {
        "tags": ["x"],
        "obs2pdf.template": "minutes",
        "obs2pdf.minutes.chair": "[[Alex Example]]",
        "obs2pdf.minutes.present": ["Chair [[Alex Example]]", "Sam"],
        "obs2pdf.theme.flavor": "latte",
    }
    assert config.frontmatter_settings(fm) == {
        "template": "minutes",
        "minutes": {"chair": "[[Alex Example]]", "present": ["Chair [[Alex Example]]", "Sam"]},
        "theme": {"flavor": "latte"},
    }


def test_frontmatter_dotted_keys_beat_nested_and_merge_with_it():
    fm = {
        "obs2pdf": {"minutes": {"chair": "Old", "location": "Clubhouse"}},
        "obs2pdf.minutes.chair": "New",
    }
    assert config.frontmatter_settings(fm) == {
        "minutes": {"chair": "New", "location": "Clubhouse"},
    }


def test_frontmatter_empty_dotted_key_is_not_set():
    # Obsidian writes an empty property as `key:` -> None.
    fm = {"obs2pdf": {"minutes": {"location": "Clubhouse"}}, "obs2pdf.minutes.location": None}
    assert config.frontmatter_settings(fm) == {"minutes": {"location": "Clubhouse"}}


def test_frontmatter_dotted_profile_selects_profile():
    settings = config.frontmatter_settings({"obs2pdf.profile": "club"})
    resolved = resolve(
        frontmatter=settings,
        user_config={"profiles": {"club": {"author": "Club Secretary"}}},
    )
    assert resolved.profile == "club"
    assert resolved.settings["author"] == "Club Secretary"
    assert resolved.sources["author"] == "profile 'club'"


def test_frontmatter_dotted_reference_signs_keep_dots_in_labels():
    fm = {
        "obs2pdf.letter.reference_signs.Customer no.": 4711,
        "obs2pdf.letter.reference_signs.Your ref": "AB-12",
    }
    settings = config.frontmatter_settings(fm)
    assert settings == {"letter": {"reference_signs": {"Customer no.": 4711, "Your ref": "AB-12"}}}
    assert resolve(frontmatter=settings).warnings == []


def test_frontmatter_dotted_unknown_key_warns():
    settings = config.frontmatter_settings({"obs2pdf.minutes.presnt": ["A"]})
    resolved = resolve(frontmatter=settings)
    assert any("'minutes.presnt'" in w for w in resolved.warnings)


@pytest.mark.parametrize(
    "fm",
    [
        {"obs2pdf.minutes": "x", "obs2pdf.minutes.chair": "A"},
        {"obs2pdf.minutes": {"chair": "A"}, "obs2pdf.minutes.chair": "B"},
    ],
)
def test_frontmatter_conflicting_dotted_keys_raise(fm):
    with pytest.raises(ConfigError, match="conflicts"):
        config.frontmatter_settings(fm)


@pytest.mark.parametrize("key", ["obs2pdf.", "obs2pdf..chair", "obs2pdf.minutes."])
def test_frontmatter_malformed_dotted_keys_raise(key):
    with pytest.raises(ConfigError):
        config.frontmatter_settings({key: "x"})


def test_format_resolved_annotates_sources():
    text = config.format_resolved(resolve(user_config={"author": "Jane"}))
    assert 'author = "Jane"' in text
    assert "# config.toml" in text
    assert "[theme]" in text


def test_display_path_abbreviates_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert config.display_path(tmp_path / "a" / "b.toml") == "~/a/b.toml"
    assert config.display_path(Path("/elsewhere/x")) == "/elsewhere/x"
