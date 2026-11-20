# Changelog

All notable changes to obs2pdf are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [0.1.0] - unreleased

First public release.

- Converts Obsidian notes to PDF via Pandoc (Markdown → Typst) and Typst:
  wiki links, embeds and transclusions (searched across the vault),
  highlights, comments, task lists, citations.
- Six document types: `notes`, `minutes`, `report`, `letter` (DIN 5008),
  `cheatsheet`, `handout`; your own templates in
  `~/.config/obs2pdf/templates/`.
- Layered configuration: built-in defaults, per-template defaults,
  `~/.config/obs2pdf/config.toml`, profiles, note frontmatter (nested
  `obs2pdf:` or flat `obs2pdf.*` keys for Obsidian's Properties panel) and
  command-line flags; `obs2pdf config show` explains where each value comes
  from.
- Catppuccin theming via the official Typst package, print-friendly by
  default.
- English and German UI strings and date formats.

[0.1.0]: https://github.com/p-e-n-t-h-a/obs2pdf/releases/tag/v0.1.0
