"""Layered configuration.

Settings are resolved by deep-merging these layers, lowest precedence first:

  1. built-in defaults           src/obs2pdf/defaults.toml
  2. built-in template defaults  [templates.<name>] in that same file
  3. user config                 ~/.config/obs2pdf/config.toml
  4. profile                     [profiles.<name>] in the user config
  5. note frontmatter            the note's `obs2pdf:` YAML mapping
  6. command line                flags given explicitly

Every layer uses the same schema (the one documented in defaults.toml), so a
profile, frontmatter block or CLI override is just a partial config. The
user config file follows the XDG base-directory convention: $OBS2PDF_CONFIG
(a file path) wins, then $XDG_CONFIG_HOME/obs2pdf/config.toml, then
~/.config/obs2pdf/config.toml.
"""

from __future__ import annotations

import copy
import os
import sys
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

# Top-level keys of the user config file that aren't settings themselves.
USER_ONLY_KEYS = ("default_profile", "profiles")
# Sub-tables whose contents are free-form (not validated key by key).
FREEFORM_TABLES = ("letter.reference_signs",)

BUILTIN_LAYER = "built-in defaults"


class ConfigError(ValueError):
    """Invalid or inconsistent configuration (bad TOML, unknown profile...)."""


def config_dir() -> Path:
    explicit = os.environ.get("OBS2PDF_CONFIG")
    if explicit:
        return Path(explicit).expanduser().parent
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "obs2pdf"


def config_path() -> Path:
    explicit = os.environ.get("OBS2PDF_CONFIG")
    if explicit:
        return Path(explicit).expanduser()
    return config_dir() / "config.toml"


def display_path(path: Path) -> str:
    """`path` with the home directory abbreviated to ~, for messages."""
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def user_templates_dir() -> Path:
    return config_dir() / "templates"


def _read_package_text(name: str) -> str:
    return resources.files("obs2pdf").joinpath(name).read_text(encoding="utf-8")


def load_builtin_defaults() -> dict[str, Any]:
    return tomllib.loads(_read_package_text("defaults.toml"))


def example_config_text() -> str:
    return _read_package_text("config.example.toml")


def load_user_config(path: Path | None = None) -> dict[str, Any]:
    """The parsed user config, or {} if there is none."""
    path = path or config_path()
    if not path.is_file():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}") from exc


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """{"theme": {"flavor": "x"}} -> {"theme.flavor": "x"}; free-form tables
    are kept as a single leaf."""
    flat: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict) and path not in FREEFORM_TABLES:
            flat.update(_flatten(value, path + "."))
        else:
            flat[path] = value
    return flat


def unknown_keys(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    known = set(_flatten(schema))
    known_tables = {k.rsplit(".", 1)[0] for k in known if "." in k}
    unknown = []
    for key, value in _flatten(data).items():
        if key in known:
            continue
        if isinstance(value, dict) and key in known_tables:
            continue  # an empty table, e.g. `[theme]` with nothing in it
        unknown.append(key)
    return unknown


FRONTMATTER_KEY = "obs2pdf"


def frontmatter_settings(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """The obs2pdf settings in a note's parsed YAML frontmatter.

    Settings can be a nested `obs2pdf:` mapping, flat dotted keys such as
    `obs2pdf.minutes.chair` (Obsidian's Properties panel can edit those, but
    not nested mappings), or both. A dotted key wins over the same setting in
    the nested mapping, and a dotted key left empty (`null`, as Obsidian
    writes an empty property) counts as not set.
    """
    nested = frontmatter.get(FRONTMATTER_KEY) or {}
    if not isinstance(nested, dict):
        raise ConfigError(f"the '{FRONTMATTER_KEY}' frontmatter key must be a mapping")

    prefix = FRONTMATTER_KEY + "."
    dotted: dict[str, Any] = {}
    for key, value in frontmatter.items():
        if not isinstance(key, str) or not key.startswith(prefix) or value is None:
            continue
        path = _split_dotted_key(key[len(prefix) :], key)
        for part in reversed(path):
            value = {part: value}
        _merge_dotted(dotted, value, key)

    return deep_merge(nested, dotted)


def _split_dotted_key(path: str, key: str) -> list[str]:
    """Split a dotted path: "minutes.chair" -> ["minutes", "chair"]. Once it reaches a
    free-form table, the rest is one key, since those keys are the user's own
    labels and may contain dots ("Customer no.")."""
    parts: list[str] = []
    rest = path
    while rest:
        if ".".join(parts) in FREEFORM_TABLES:
            parts.append(rest)
            break
        part, dot, rest = rest.partition(".")
        parts.append(part)
        if not part or (dot and not rest):
            raise ConfigError(f"frontmatter key '{key}': empty name between dots")
    if not parts:
        raise ConfigError(f"frontmatter key '{key}': no setting name after '{FRONTMATTER_KEY}.'")
    return parts


def _merge_dotted(target: dict[str, Any], overlay: dict[str, Any], key: str) -> None:
    """Merge one dotted key's nested value into `target`, refusing to set a
    setting twice or to use one name as both a table and a value."""
    for name, value in overlay.items():
        if name not in target:
            target[name] = copy.deepcopy(value)
        elif isinstance(target[name], dict) and isinstance(value, dict):
            _merge_dotted(target[name], value, key)
        else:
            raise ConfigError(
                f"frontmatter key '{key}' conflicts with another '{FRONTMATTER_KEY}.' key"
            )


@dataclass
class Resolved:
    settings: dict[str, Any]
    # dotted key -> name of the layer that last set it
    sources: dict[str, str] = field(default_factory=dict)
    profile: str = ""
    template: str = ""
    warnings: list[str] = field(default_factory=list)


def _schema(builtin: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in builtin.items() if k != "templates"}


def resolve(
    cli: dict[str, Any] | None = None,
    frontmatter: dict[str, Any] | None = None,
    user_config: dict[str, Any] | None = None,
    builtin: dict[str, Any] | None = None,
    user_config_name: str = "config.toml",
) -> Resolved:
    """Merge every layer into one settings dict. `cli` and `frontmatter` may
    carry a `profile` key to select a profile; the rest of their keys are
    settings overrides."""
    cli = dict(cli or {})
    frontmatter = dict(frontmatter or {})
    user_config = dict(user_config or {})
    builtin = builtin if builtin is not None else load_builtin_defaults()
    schema = _schema(builtin)
    warnings: list[str] = []

    profiles = user_config.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ConfigError(f"{user_config_name}: 'profiles' must be a table")

    profile_name = (
        cli.pop("profile", None)
        or frontmatter.pop("profile", None)
        or user_config.get("default_profile")
        or ""
    )
    cli.pop("profile", None)
    frontmatter.pop("profile", None)
    if profile_name and profile_name not in profiles:
        available = ", ".join(sorted(profiles)) or "none defined"
        raise ConfigError(
            f"unknown profile {profile_name!r} (available: {available}); "
            f"profiles are [profiles.<name>] tables in {user_config_name}"
        )
    profile = profiles.get(profile_name, {}) if profile_name else {}

    user_settings = {k: v for k, v in user_config.items() if k not in USER_ONLY_KEYS}

    template = next(
        (
            layer["template"]
            for layer in (cli, frontmatter, profile, user_settings, schema)
            if layer.get("template")
        ),
        "",
    )
    template_defaults = builtin.get("templates", {}).get(template, {})

    layers: list[tuple[str, dict[str, Any]]] = [
        (BUILTIN_LAYER, schema),
        (f"built-in '{template}' template defaults", template_defaults),
        (user_config_name, user_settings),
        (f"profile '{profile_name}'", profile),
        ("frontmatter", frontmatter),
        ("command line", cli),
    ]

    settings: dict[str, Any] = {}
    sources: dict[str, str] = {}
    for name, data in layers:
        if not data:
            continue
        if name != BUILTIN_LAYER:
            for key in unknown_keys(data, schema):
                warnings.append(f"{name}: unknown setting '{key}' (ignored)")
            data = _known_only(data, schema)
        settings = deep_merge(settings, data)
        for key in _flatten(data):
            sources[key] = name

    settings["affiliation"] = _as_lines(settings.get("affiliation"))
    settings["contact"]["address"] = _as_lines(settings["contact"].get("address"))
    settings["letter"]["recipient"] = _as_lines(settings["letter"].get("recipient"))
    minutes = settings["minutes"]
    for key in ("present", "absent", "guests"):
        value = _yaml_wikilink(minutes.get(key))
        items = value if isinstance(value, list) else _as_lines(value)
        minutes[key] = [str(_yaml_wikilink(item)) for item in items]
    for key in ("chair", "minute_taker"):
        minutes[key] = str(_yaml_wikilink(minutes.get(key)) or "")

    # A print-friendly page is white, so unless a flavor was picked on
    # purpose, use the one designed for light backgrounds.
    if settings["theme"]["print_friendly"] and sources.get("theme.flavor") == BUILTIN_LAYER:
        settings["theme"]["flavor"] = "latte"
        sources["theme.flavor"] = "print_friendly"

    return Resolved(
        settings=settings,
        sources=sources,
        profile=profile_name,
        template=settings["template"],
        warnings=warnings,
    )


def _known_only(data: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key not in schema:
            continue
        if isinstance(value, dict) and isinstance(schema[key], dict) and schema[key]:
            result[key] = _known_only(value, schema[key])
        else:
            result[key] = value
    return result


def _as_lines(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def _yaml_wikilink(value: Any) -> Any:
    """Undo YAML reading an unquoted `[[Name]]` as a nested list.

    `chair: [[Jane Doe]]` or `- [[Jane Doe]]` is a flow sequence in YAML,
    giving `[["Jane Doe"]]`; turn that back into the text `"[[Jane Doe]]"`.
    Anything else is returned unchanged.
    """
    if (
        isinstance(value, list)
        and len(value) == 1
        and isinstance(value[0], list)
        and len(value[0]) == 1
        and not isinstance(value[0][0], (list, dict))
    ):
        return f"[[{value[0][0]}]]"
    return value


def profile_names(user_config: dict[str, Any] | None = None) -> list[str]:
    if user_config is None:
        try:
            user_config = load_user_config()
        except ConfigError:
            return []
    profiles = user_config.get("profiles", {})
    return sorted(profiles) if isinstance(profiles, dict) else []


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    if isinstance(value, dict):
        inner = ", ".join(f"{_toml_key(k)} = {_toml_value(v)}" for k, v in value.items())
        return "{ " + inner + " }" if inner else "{}"
    s = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{s}"'


def _toml_key(key: str) -> str:
    if key.replace("_", "").replace("-", "").isalnum():
        return key
    return _toml_value(key)


def format_resolved(resolved: Resolved) -> str:
    """Render resolved settings as TOML, each value annotated with the layer
    it came from (for `obs2pdf config show`)."""
    lines = [
        f"# profile:  {resolved.profile or '(none)'}",
        f"# template: {resolved.template}",
        "",
    ]

    def emit(data: dict[str, Any], prefix: str) -> None:
        def is_table(k: str, v: Any) -> bool:
            return isinstance(v, dict) and f"{prefix}{k}" not in FREEFORM_TABLES

        scalars = [(k, v) for k, v in data.items() if not is_table(k, v)]
        tables = [(k, v) for k, v in data.items() if is_table(k, v)]
        rows = [(f"{_toml_key(k)} = {_toml_value(v)}", f"{prefix}{k}") for k, v in scalars]
        width = max((len(r) for r, _ in rows), default=0)
        for row, path in rows:
            lines.append(f"{row:<{width}}  # {resolved.sources.get(path, '?')}")
        for key, value in tables:
            lines.append("")
            lines.append(f"[{prefix}{key}]")
            emit(value, f"{prefix}{key}.")

    emit(resolved.settings, "")
    return "\n".join(lines) + "\n"
