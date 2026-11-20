# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`obs2pdf` is a small Python package that converts an Obsidian-flavoured Markdown note into a typeset
PDF via Pandoc (Markdown → Typst) and Typst (Typst → PDF). It's a `uv`-managed project: a
`pyproject.toml`-based package under `src/obs2pdf/`, installable as a CLI tool (`obs2pdf` console
script), with a `pytest` suite under `tests/`. It is meant to be published: **no personal data
(names, affiliations, institutions) belongs in the repo** — identity lives in the user's own
`~/.config/obs2pdf/config.toml` (profiles), and the shipped templates are generic document types.

## Running / developing

```bash
uv sync                                          # dev env
uv run obs2pdf examples/minutes.md               # convert a note in place
uv run obs2pdf note.md --template report -p work
uv run obs2pdf note.md --catppuccin-flavor none --keep-typst
uv run obs2pdf config show examples/letter.md    # resolved settings + source of each
uv run obs2pdf config init                       # write the starter config
uv run pytest                                    # no pandoc/typst required
uv run ruff check && uv run ruff format --check  # lint + format (CI enforces both)
make -C examples                                 # render all examples (built-in defaults only)
```

Rendering needs `pandoc` and `typst` (≥ 0.13; CI renders the examples with 0.13 and latest) on
`PATH`; `convert()` checks up front (`deps.check_external_dependencies()`). `typst compile` needs
network access the first time it uses `@preview/cheq` (every template), `@preview/catppuccin` (any
flavor but `none`) or `@preview/letter-pro` (cached afterwards). In a sandbox
without access to `~/.cache`, set `TYPST_PACKAGE_CACHE_PATH` to a writable dir, and `OBS2PDF_CONFIG`
to point at a test config (or a nonexistent path for pure built-in defaults).

The pytest suite covers all pure-Python logic with `tmp_path` fixtures; `test_pipeline.py` runs
`convert()` with pandoc and typst stubbed out. It does **not** run `typst compile` — verify Typst-facing changes by rendering every note in `examples/` (one per
template; `make -C examples`, CI's `render-examples` job does the same) and looking at the PDFs.

## Architecture

```
src/obs2pdf/
  cli.py              # argparse; `obs2pdf NOTE` + `obs2pdf config {init,show,path}` dispatch
  pipeline.py         # convert(): settings resolution + the whole pipeline below
  config.py           # layered config: XDG paths, deep merge, source tracking, validation
  defaults.toml       # built-in defaults — the schema AND documentation of every setting
  config.example.toml # what `obs2pdf config init` writes (all commented out)
  preprocess.py       # raw Markdown -> Markdown (frontmatter, embeds, links, comments, tasks)
  postprocess.py      # pandoc's Typst output -> final Typst body
  templates.py        # discovery (built-in + ~/.config/obs2pdf/templates) and assembly
  vault.py / deps.py / catppuccin.py
  templates/
    _theme.typ        # Catppuccin color resolution
    _base.typ         # settings loading, i18n strings, fonts, obs2pdf-base page/show rules, hooks
    notes.typ minutes.typ report.typ letter.typ cheatsheet.typ handout.typ
examples/             # one demo note per template + all-options.md (every frontmatter key)
```

### Settings: three separate concerns

- **Who** (profile): `author`, `role`, `affiliation`, `lang`, `logo`, `[contact]`, a default
  `template` — user config only.
- **What** (template / document type): layout and structure, shipped in the repo.
- **Look** (`[theme]`, `[fonts]`): global defaults any layer can override.

`config.resolve()` deep-merges, lowest first: built-in `defaults.toml` → built-in
`[templates.<name>]` defaults → user `config.toml` → `[profiles.<name>]` → note frontmatter
(`obs2pdf:` key) → CLI flags. Every layer has the same schema (a profile/frontmatter/CLI override is
just a partial config). Profile = `cli.profile or frontmatter.profile or default_profile`; template
is looked up across layers before merging so its built-in defaults can be slotted in. Unknown keys
warn and are dropped (`unknown_keys`, schema = `defaults.toml`; `FREEFORM_TABLES` like
`letter.reference_signs` are exempt). `sources` records which layer set each dotted key, for
`obs2pdf config show`. Adding a setting = add it (documented) to `defaults.toml` and to the
fallback dict in `_base.typ`; nothing else in Python needs to know about it.

### Pipeline (`pipeline.convert()`)

1. Split YAML frontmatter (`preprocess.split_frontmatter`), collect its settings
   (`config.frontmatter_settings`: the nested `obs2pdf:` mapping plus flat `obs2pdf.a.b` dotted keys
   for Obsidian's Properties panel, dotted wins, empty = unset, free-form tables keep dots in their
   keys), resolve settings, validate
   (template exists, flavor/accent names, `outline_depth`).
2. Pre-process (regex/string based, not a Markdown parser): `resolve_obsidian_embeds` (images and
   recursive note transclusion with loop guard and vault-root fallback; transcluded notes'
   frontmatter is dropped), `extract_open_tasks` (unchecked `- [ ]` as plain text, for the minutes
   task table), `extract_title_heading` (first H1 → title, only if there's exactly one H1),
   `remove_obsidian_links` (placeholders that survive pandoc), comment stripping,
   `normalize_for_pandoc`.
3. `pypandoc.convert_text(content, "typst", format="md")`.
4. Post-process: `shift_heading_depths` (H2 → depth 1; extra H1s → `PART_BREAK_MARKER`),
   `activate_typst_internal_link` (wiki links → `#obs2pdf-wikilink([...])`, highlights →
   `#highlight`), `recreate_checkboxes`, `fix_table_column_widths`, prepend
   `#obs2pdf-inline-outline()`, `wrap_page_parts(content, "#obs2pdf-body[", "]")` (part titles
   get the `<obs2pdf-part-title>` label + heading counter reset).
5. Assemble `_theme.typ + _base.typ + <template>.typ + body`, write it into the note's directory
   (so relative image paths resolve) as a hidden, uniquely named `.<note>.*.obs2pdf.typ` temp file
   (`<note>.typ` only with `--keep-typst`, so an existing file is never clobbered), run `typst
   compile --root <root> --input obs2pdf=<json>`, delete the temp file. File settings (`logo`, `bibliography`) are resolved relative to the note (or
   `~`/absolute), `--root` is widened to the common ancestor of the vault root and those files, and
   they're passed as root-absolute `/...` paths.

### Key design points to preserve

- **All visual styling lives in Typst** (`templates/*.typ`). Pandoc is only the Markdown→Typst source
  converter; there's no `--pdf-engine`. Even body-level hooks (columns, outline placement, wiki-link
  styling) are Typst functions the body *calls* (`obs2pdf-body`, `obs2pdf-inline-outline`,
  `obs2pdf-wikilink`) and templates *redefine* with a later `#let`.
- **Settings reach Typst as one JSON `--input`**, parsed in `_base.typ` with
  `json(bytes(sys.inputs.at("obs2pdf")))` and merged over a fallback dict — never substituted into
  source text, so titles/names containing Typst markup characters are safe. Only the converted body
  is written into the `.typ` file as markup.
- **Templates are thin**: `#show: obs2pdf-base.with(...)` (options: `header`/`footer` auto/none/
  content, `setup-page: false` when a package owns `set page` as in `letter.typ`, `margin`,
  `flipped`, `text-size` (default `auto` = `fonts.size`), `heading-numbering`), then only what's specific to that document type.
  Template-specific defaults (report → outline on + 11pt, letter → no theme, cheatsheet → 8pt,
  handout → 11.5pt) go in `[templates.<name>]` in `defaults.toml`, not in the `.typ`.
- **i18n**: obs2pdf's own UI strings and date formats are in `obs2pdf-strings` /
  `obs2pdf-date-formats` in `_base.typ` (`en`, `de`; others fall back to `en`). Use `obs2pdf-t(key)`.
  Date formats are functions `datetime -> str`, since Typst's `[month repr:long]` is English-only.
- **Catppuccin colors come from the real `catppuccin` Typst package**, never hardcoded hex.
  `flavor = "none"` skips that import. Heading/role color policy is centralized in `_theme.typ`
  (`obs2pdf-heading-role-order`, `obs2pdf-bold-role`, `obs2pdf-highlight-role`, ...).
  `theme.print_friendly` defaults to **true** (white page, black text, colored headings), and then
  `config.resolve()` swaps the built-in default flavor for `latte`.
- **Multi-part notes** (more than one H1): no title block (`obs2pdf-title-block` checks
  `has_multiple_h1`); each H1 is an inline part title that resets heading numbering.
- **Known limitations** (accepted, consistent with the regex approach): `#` lines inside fenced code
  blocks are misdetected as headings; a part-title heading carries only `<obs2pdf-part-title>`, so
  Pandoc's own anchor for it is dropped.

### Typst gotchas hit while writing this

- A function stored in a dictionary must be called as `(theme.heading-fill)(1)`, not
  `theme.heading-fill(1)`.
- `set` rules inside an `if` block are scoped to that block — use `set page(...) if cond`.
- Numbering patterns treat letters like `I`/`i`/`a` as counters, so "Item 1" must be a numbering
  *function* (see `minutes.typ`), not the pattern string `"Item 1"`.
- A later `#show: f` wraps everything after it, *inside* earlier show rules — that's how
  `letter.typ` and `minutes.typ` append content (closing, signatures) after the note body.
