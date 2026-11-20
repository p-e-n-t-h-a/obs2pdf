# obs2pdf

[![CI](https://github.com/p-e-n-t-h-a/obs2pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/p-e-n-t-h-a/obs2pdf/actions/workflows/ci.yml)

Turn Obsidian notes into well-typeset PDFs — notes, meeting minutes,
reports, letters, cheatsheets and handouts — via
[Pandoc](https://pandoc.org) and [Typst](https://typst.app).

```bash
obs2pdf "Board Meeting.md"                    # → Board Meeting.pdf
obs2pdf note.md --template report             # pick a document type
obs2pdf note.md -p work                       # use your "work" profile
```

- **Understands Obsidian syntax**: `[[wiki links]]`, `![[embeds]]` (images
  and transcluded notes, searched across the whole vault), `==highlights==`,
  `%%comments%%`, task lists, YAML frontmatter.
- **Document types, not just styles**: each template is built for a job —
  minutes number agenda items and collect open tasks, letters follow
  DIN 5008, reports get a title page and table of contents.
- **Profiles for the contexts you write in**: name, role, affiliation,
  language, logo and default document type per context (work, club,
  hobby...), kept in your own config file, selectable per note.
- **[Catppuccin](https://catppuccin.com) theming** matching the Catppuccin
  Obsidian theme: colored headings on a white, printable page by default,
  the flavor's own background on request, or plain black on white.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) to install
  (it brings its own Python ≥ 3.10)
- [pandoc](https://pandoc.org/installing.html) on `PATH`
- [typst](https://github.com/typst/typst#installation) ≥ 0.13 on `PATH`
- Network access on the first run (and the first letter), so Typst can
  fetch the packages the templates use from
  [Typst Universe](https://typst.app/universe/); they're cached afterwards.

## Install

```bash
git clone https://github.com/p-e-n-t-h-a/obs2pdf.git
cd obs2pdf
./install.sh          # uv tool install + bash tab-completion
obs2pdf config init   # optional: create ~/.config/obs2pdf/config.toml
```

`install.sh` installs the checkout in editable mode, so a `git pull` is all
an update takes; `./uninstall.sh` removes obs2pdf and the tab-completion
again (your config stays).

Or straight from GitHub, without a checkout or tab-completion:

```bash
uv tool install git+https://github.com/p-e-n-t-h-a/obs2pdf
uv tool upgrade obs2pdf     # update
uv tool uninstall obs2pdf   # remove
```

## Document types

Pick one with `--template`, in a profile, or in a note's frontmatter. Try
each one on the notes in [`examples/`](examples/).

| Template | For | Layout |
|---|---|---|
| `notes` (default) | everyday notes | two columns, numbered headings, header/footer |
| `minutes` | meeting minutes | agenda items ("TOP 1" / "Item 1"), meeting-details block, open-task table, signature lines |
| `report` | papers, documentation | title page, table of contents, one chapter per page, bibliography |
| `letter` | formal letters | DIN 5008 via [letter-pro](https://typst.app/universe/package/letter-pro), sender from your profile |
| `cheatsheet` | reference sheets | landscape, three columns, dense type |
| `handout` | flyers, info sheets, player handouts | single column, large type, no header/footer |

The note's first `# Heading` becomes the document title (otherwise the
filename does), and `##` becomes the top-level section. A note with several
`# Headings` is treated as multiple parts, each with its own title and
section numbering.

## Configuration

Settings are layered; each layer overrides the ones above it:

1. **Built-in defaults**: [`src/obs2pdf/defaults.toml`](src/obs2pdf/defaults.toml),
   which also documents every setting
2. **Your config file**: `~/.config/obs2pdf/config.toml` (or
   `$XDG_CONFIG_HOME/obs2pdf/config.toml`, or the file named by
   `$OBS2PDF_CONFIG`)
3. **A profile** from that file: chosen with `-p NAME`, the note's
   frontmatter, or `default_profile`
4. **The note's frontmatter**: the `obs2pdf:` key, or `obs2pdf.*` dotted keys
5. **Command-line flags**

`obs2pdf config show [note.md]` prints the final values and which layer each
one came from. `obs2pdf config init` writes a commented starter file.

### Profiles

A profile is a partial config for one context you write in:

```toml
# ~/.config/obs2pdf/config.toml
default_profile = "work"

[fonts]
body = "Nunito"           # applies to every profile

[profiles.work]
author = "Jane Doe"
role = "M. Sc."
affiliation = ["Example University", "Institute of Examples"]
logo = "~/.config/obs2pdf/assets/university.png"

[profiles.club]
author = "Jane Doe"
role = "Secretary"
affiliation = ["Example Sports Club e.V."]
lang = "de"
template = "minutes"      # club notes are minutes unless stated otherwise

[profiles.club.contact]   # sender block for letters
address = ["Clubhouse Road 1", "12345 Example Town"]
email = "secretary@example.org"
```

### Frontmatter

Any setting can also be set per note, under `obs2pdf:`. That's where
per-document details go, such as the meeting details for minutes or the
recipient of a letter:

```yaml
---
obs2pdf:
  profile: club
  minutes:
    date: 2026-11-19
    location: Clubhouse
    chair: Chair [[John Roe]]
    present:
      - Treasurer [[Jane Doe]]
      - Max Mustermann
    absent: [Erika Musterfrau]
---
```

```yaml
---
obs2pdf:
  template: letter
  letter:
    recipient: [Example Corp., Attn. Jane Roe, Main Street 1, 12345 Example City]
    reference_signs: { "Your ref": "AB-12" }
    closing: Kind regards
---
```

People in `minutes` (chair, minute-taker, attendees) can be plain names or
Obsidian links with an optional role, `Role [[Name]]` or `[[Name|Alias]]`; the
link brackets are dropped and the role goes in its own column. Quote an entry
when text follows the link (`"[[Jane Doe]] (guest)"`), since YAML can't parse
that unquoted.

#### Flat keys for Obsidian's Properties panel

Obsidian's Properties panel can't edit nested mappings like the ones above.
Every setting can also be written as a flat key with its dotted path, which
Obsidian treats as a normal text or list property:

```yaml
---
obs2pdf.template: minutes
obs2pdf.minutes.date: 2026-11-19
obs2pdf.minutes.chair: "[[John Roe]]"
obs2pdf.minutes.present:
  - Treasurer [[Jane Doe]]
  - Max Mustermann
obs2pdf.letter.reference_signs.Customer no.: 4711
---
```

Both forms can be mixed; a dotted key wins over the same setting under
`obs2pdf:`. A dotted property left empty counts as not set, so a note
template can list them all. Obsidian only treats a property value as a link
when the whole value is the link (`"[[John Roe]]"`); `Treasurer [[Jane Doe]]`
still renders as a linked name in the PDF, but isn't a backlink in Obsidian.
To keep the role next to the name *and* get the backlink, put the role in the
link's alias: `"[[Jane Doe|Treasurer Jane Doe]]"`. When the alias contains the
note name, only the name is set as a link in the PDF and the rest of the
alias becomes the role (this applies to minutes people only; links in the
body keep their alias).

The other frontmatter keys (`tags`, `aliases`, ...) are ignored. For every
available option in YAML form, with comments, see
[`examples/all-options.md`](examples/all-options.md).

### Your own templates

Any `.typ` file in `~/.config/obs2pdf/templates/` becomes a template with
that name, and replaces a built-in one if the names match. Copy a built-in
template from [`src/obs2pdf/templates/`](src/obs2pdf/templates/) as a
starting point. Templates are real Typst; they build on the shared helpers in
[`_base.typ`](src/obs2pdf/templates/_base.typ) (all settings as
`obs2pdf-cfg`, theme colors as `obs2pdf-theme`, page setup as
`obs2pdf-base`); see the comment at the top of that file.

## Command line

```
obs2pdf NOTE.md [options]
obs2pdf config {init,show,path}
obs2pdf --version
```

| Flag | Description |
|---|---|
| `-o, --output PATH` | PDF path (default: next to the note) |
| `-p, --profile NAME` | Profile from the config file |
| `--template NAME` | Document type (see above) |
| `-t, --title TEXT` | Title (default: the first H1, else the filename) |
| `-a, --author TEXT`, `--role TEXT` | Author and role |
| `--affiliation TEXT` | Header affiliation; repeat for multiple lines |
| `--lang CODE` | Document language (`en`, `de`, ...) |
| `--outline` / `--no-outline` | Table of contents |
| `--outline-depth N` | Deepest heading level in the outline (0 = all) |
| `--catppuccin-flavor NAME` | `latte`, `frappe`, `macchiato`, `mocha`, or `none` for a plain page |
| `--catppuccin-accent NAME` | Accent color for links and rules |
| `--print-friendly` / `--no-print-friendly` | White page and black text, headings and accents still colored (the default), or the flavor's own background |
| `--font FAMILY`, `--mono FAMILY` | Body and monospace font families (override `[fonts]`) |
| `--font-size PT` | Body text size in points (overrides `fonts.size`) |
| `--keep-typst` | Keep the generated `.typ` file |
| `--list-templates`, `--list-profiles` | List and exit |

## Theming

Colors come from the real
[`catppuccin` Typst package](https://typst.app/universe/package/catppuccin/),
so they always match upstream. Headings follow the
[Catppuccin style guide](https://github.com/catppuccin/catppuccin/blob/main/docs/style-guide.md)'s
accent order (red title, then peach, yellow, green, sapphire, lavender);
bold is sapphire, italic green, highlights yellow. To change that mapping,
edit [`_theme.typ`](src/obs2pdf/templates/_theme.typ).

By default `theme.print_friendly` is on: the page stays white and body text
black, only headings, emphasis and the accent are colored, and the default
flavor becomes `latte`, whose colors are made for light backgrounds. Turn
it off (`--no-print-friendly`, or `print_friendly = false` under `[theme]`)
to get the flavor's own background, e.g. the dark `macchiato`. With
`flavor = "none"` the page is plain black on white, with
`theme.fallback_color` as the accent, and the catppuccin package isn't
downloaded.

The default fonts (Libertinus Serif, DejaVu Sans Mono) ship with Typst, so
output looks the same everywhere. Set `[fonts]` to any installed font.

## Obsidian syntax, step by step

1. `![[image.png|300]]` becomes an image (optionally 300 px wide);
   `![[Other Note]]` inlines that note (its frontmatter dropped). Files are
   searched below the note's folder first, then across the whole vault (the
   nearest folder containing `.obsidian`). Embeds that can't be found stay
   as plain text.
2. `[[Note]]`, `[[Note|alias]]` and `[[Note#Heading]]` become bold, accent-colored text;
   `==text==` becomes a highlight.
3. `%%comments%%` and `<!-- comments -->` are removed.
4. `->` and `=>` become arrows.
5. `- [ ]` / `- [x]` render as checkboxes; open ones also feed the minutes'
   task table.
6. `[@citekey]` citations resolve against `bibliography = "refs.bib"`.

Known limitation: processing is regex-based, so Obsidian syntax inside code
blocks (for example a `#` heading line inside a fenced block) can be
misread.

## Development

```bash
uv sync
uv run obs2pdf examples/minutes.md --keep-typst
uv run pytest
uv run ruff check && uv run ruff format --check
make -C examples          # render every example note to PDF
```

The test suite covers all the Python logic and needs neither pandoc nor
typst (both are stubbed out where the pipeline calls them). Changes to templates are best checked by rendering
[`examples/`](examples/): `make -C examples` renders them with the built-in
defaults (`minutes.pdf`, ...), `make -C examples user` with your own
`config.toml` (`minutes.user.pdf`, ...), `make -C examples both` does both.
Only what's out of date is rebuilt, also after changes to obs2pdf itself or
to your config.

## License

[MIT](LICENSE)
