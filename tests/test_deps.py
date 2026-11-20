import pytest

from obs2pdf import deps


def test_check_external_dependencies_passes_when_all_present(monkeypatch):
    monkeypatch.setattr(deps.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    deps.check_external_dependencies()  # should not raise


def test_check_external_dependencies_reports_missing_binaries(monkeypatch):
    monkeypatch.setattr(deps.shutil, "which", lambda cmd: None)
    with pytest.raises(RuntimeError) as excinfo:
        deps.check_external_dependencies()
    message = str(excinfo.value)
    assert "pandoc" in message
    assert "typst" in message
    assert "https://pandoc.org" in message
    assert "https://typst.app" in message


def test_check_external_dependencies_reports_only_the_missing_one(monkeypatch):
    def fake_which(cmd):
        return "/usr/bin/pandoc" if cmd == "pandoc" else None

    monkeypatch.setattr(deps.shutil, "which", fake_which)
    with pytest.raises(RuntimeError) as excinfo:
        deps.check_external_dependencies()
    lines = str(excinfo.value).splitlines()
    assert not any("pandoc" in line for line in lines)
    assert any("typst" in line for line in lines)
