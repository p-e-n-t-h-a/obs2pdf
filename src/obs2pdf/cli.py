"""Command-line entry point for obs2pdf.

    obs2pdf NOTE.md [options]          convert a note
    obs2pdf config init|show|path      manage the user config file

Every conversion flag defaults to "not given", so that settings from the
user config, the selected profile and the note's frontmatter apply unless a
flag explicitly overrides them (see obs2pdf.config for the layering).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import Any

import argcomplete

from . import __version__, config
from .catppuccin import CATPPUCCIN_ACCENTS, CATPPUCCIN_FLAVORS
from .pipeline import convert, resolve_settings
from .templates import available_templates


def _profile_completer(**_kwargs: Any) -> list[str]:
    return config.profile_names()


def _complete_profiles(action: argparse.Action) -> None:
    # argcomplete reads a `completer` attribute it expects us to attach.
    action.completer = _profile_completer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="obs2pdf",
        description="Convert an Obsidian-flavoured Markdown note to PDF via Typst. "
        "Defaults come from ~/.config/obs2pdf/config.toml (see 'obs2pdf config "
        "init') and the note's 'obs2pdf:' frontmatter; flags override both.",
        epilog="Config file: 'obs2pdf config {init,show,path}'.",
    )
    parser.add_argument("path", nargs="?", help="Path to the .md file to convert")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-o", "--output", help="Path for the generated PDF (default: <input>.pdf)")
    _complete_profiles(
        parser.add_argument("-p", "--profile", help="Profile from the config file to use")
    )
    parser.add_argument(
        "--template",
        choices=sorted(available_templates()),
        help="Document type (default: from config, else 'notes')",
    )
    parser.add_argument(
        "-t", "--title", help="Document title (default: the note's first H1, else the filename)"
    )
    parser.add_argument("-a", "--author", help="Author name")
    parser.add_argument("--role", help="Author role, shown after the name in footers")
    parser.add_argument(
        "--affiliation",
        action="append",
        help="Affiliation shown in the header; repeat for multiple lines",
    )
    parser.add_argument("--lang", help="Document language, e.g. en or de")
    parser.add_argument(
        "--outline",
        action=argparse.BooleanOptionalAction,
        help="Include a table of contents",
    )
    parser.add_argument(
        "--outline-depth",
        type=int,
        help="Maximum heading depth shown in the outline (0 = all levels)",
    )
    parser.add_argument(
        "--catppuccin-flavor",
        choices=(*CATPPUCCIN_FLAVORS, "none"),
        help="Catppuccin flavor to color the page with, or 'none' for a plain "
        "white page (default: from config, else macchiato)",
    )
    parser.add_argument(
        "--catppuccin-accent",
        choices=CATPPUCCIN_ACCENTS,
        help="Accent color for links, wiki-links and rules (default: from config, else mauve)",
    )
    parser.add_argument(
        "--print-friendly",
        action=argparse.BooleanOptionalAction,
        help="White page and black body text even with a Catppuccin flavor; "
        "headings, bold/italic and the accent stay colored (default: from "
        "config, else on; --no-print-friendly for the flavor's own background)",
    )
    parser.add_argument(
        "--font",
        metavar="FAMILY",
        help="Body font family (default: from config, else Libertinus Serif)",
    )
    parser.add_argument(
        "--font-size",
        type=float,
        metavar="PT",
        help="Body text size in points (default: from config, else per template)",
    )
    parser.add_argument(
        "--mono",
        metavar="FAMILY",
        help="Monospace font family for code (default: from config, else DejaVu Sans Mono)",
    )
    parser.add_argument(
        "--keep-typst",
        action="store_true",
        help="Keep the intermediate .typ file instead of deleting it",
    )
    parser.add_argument(
        "--list-templates", action="store_true", help="List available templates and exit"
    )
    parser.add_argument(
        "--list-profiles", action="store_true", help="List configured profiles and exit"
    )
    return parser


def build_config_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="obs2pdf config", description="Manage the obs2pdf user config file."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Write a commented starter config file")
    init.add_argument("--force", action="store_true", help="Overwrite an existing file")
    show = sub.add_parser("show", help="Print the resolved settings and where each one comes from")
    show.add_argument("path", nargs="?", help="A note, to include its frontmatter")
    _complete_profiles(show.add_argument("-p", "--profile"))
    show.add_argument("--template", choices=sorted(available_templates()))
    sub.add_parser("path", help="Print the config file location")
    return parser


def overrides_from_args(args: argparse.Namespace) -> dict[str, Any]:
    """The settings the user explicitly gave on the command line, in the
    config schema (so they can be layered on top of everything else)."""
    flat = {
        "profile": args.profile,
        "template": args.template,
        "title": getattr(args, "title", None),
        "author": getattr(args, "author", None),
        "role": getattr(args, "role", None),
        "affiliation": getattr(args, "affiliation", None),
        "lang": getattr(args, "lang", None),
        "outline": getattr(args, "outline", None),
        "outline_depth": getattr(args, "outline_depth", None),
    }
    overrides = {k: v for k, v in flat.items() if v is not None}
    theme = {
        "flavor": getattr(args, "catppuccin_flavor", None),
        "accent": getattr(args, "catppuccin_accent", None),
        "print_friendly": getattr(args, "print_friendly", None),
    }
    theme = {k: v for k, v in theme.items() if v is not None}
    if theme:
        overrides["theme"] = theme
    fonts = {
        "body": getattr(args, "font", None),
        "mono": getattr(args, "mono", None),
        "size": getattr(args, "font_size", None),
    }
    fonts = {k: v for k, v in fonts.items() if v is not None}
    if fonts:
        overrides["fonts"] = fonts
    return overrides


def config_main(argv: list[str]) -> int:
    args = build_config_parser().parse_args(argv)
    path = config.config_path()
    if args.command == "path":
        print(path)
        return 0
    if args.command == "init":
        if path.exists() and not args.force:
            print(f"error: {path} already exists (use --force to overwrite)", file=sys.stderr)
            return 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(config.example_config_text(), encoding="utf-8")
        print(f"wrote {path}")
        return 0
    # show
    if args.path and not os.path.isfile(args.path):
        print(f"error: no such file: {args.path}", file=sys.stderr)
        return 1
    try:
        resolved = resolve_settings(args.path, overrides_from_args(args))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for warning in resolved.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(f"# config file: {path}{'' if path.is_file() else ' (not found)'}")
    print(config.format_resolved(resolved), end="")
    return 0


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["config"]:
        sys.exit(config_main(argv[1:]))

    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

    if args.list_templates:
        for name, source in sorted(available_templates().items()):
            print(f"{name:<12} {source}")
        return
    if args.list_profiles:
        try:
            names = config.profile_names(config.load_user_config())
        except config.ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        if names:
            print("\n".join(names))
        else:
            print(f"no profiles defined in {config.config_path()}", file=sys.stderr)
        return

    if args.path is None:
        parser.error("the following arguments are required: path")
    if not os.path.isfile(args.path):
        print(f"error: no such file: {args.path}", file=sys.stderr)
        sys.exit(1)

    try:
        output_path = convert(
            args.path,
            overrides=overrides_from_args(args),
            output=args.output,
            keep_typst=args.keep_typst,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("error: typst compilation failed", file=sys.stderr)
        sys.exit(1)

    print(output_path)


if __name__ == "__main__":
    main()
