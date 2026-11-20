import pytest

from obs2pdf.templates import BUILTIN_TEMPLATES, available_templates, template_source


def test_builtin_templates_exist(tmp_path):
    templates = available_templates(user_dir=tmp_path)
    assert set(templates) == set(BUILTIN_TEMPLATES)
    for source in templates.values():
        assert source.is_file()


def test_template_source_unknown_name_raises(tmp_path):
    with pytest.raises(ValueError):
        template_source("does-not-exist", user_dir=tmp_path)


@pytest.mark.parametrize("name", BUILTIN_TEMPLATES)
def test_template_source_starts_with_shared_helpers(name, tmp_path):
    source = template_source(name, user_dir=tmp_path)
    assert source.index("obs2pdf-resolve-theme") < source.index("#let obs2pdf-base")
    assert source.index("#let obs2pdf-base") < source.index(f"obs2pdf template: {name}")


@pytest.mark.parametrize("name", BUILTIN_TEMPLATES)
def test_builtin_templates_contain_no_personal_defaults(name, tmp_path):
    # Identity belongs in the user's config, never in a shipped template.
    source = template_source(name, user_dir=tmp_path)
    assert "default-author" not in source
    assert "default-affiliation" not in source


def test_user_templates_are_discovered_and_override_builtins(tmp_path):
    (tmp_path / "mine.typ").write_text("// mine")
    (tmp_path / "notes.typ").write_text("// my notes")
    (tmp_path / "_helper.typ").write_text("// not a template")
    templates = available_templates(user_dir=tmp_path)
    assert "mine" in templates
    assert "_helper" not in templates
    assert template_source("notes", user_dir=tmp_path).rstrip().endswith("// my notes")
