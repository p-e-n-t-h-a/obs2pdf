---
# Every setting obs2pdf understands, set from the note's YAML frontmatter.
# Each setting is a flat `obs2pdf.<path>` key, so Obsidian's Properties
# panel can edit it; a nested `obs2pdf:` mapping (`obs2pdf: {minutes:
# {chair: ...}}`) works too, and both can be mixed. Other frontmatter keys
# (tags, aliases, ...) are left to Obsidian. A key you leave out, or leave
# empty, keeps its value from the layers below (built-in defaults, template
# defaults, your config.toml, the active profile), and command-line flags
# still win. Run `obs2pdf config show examples/all-options.md` to see where
# each resolved value comes from.
# Note: editing properties in Obsidian's panel rewrites the frontmatter and
# drops these comments; read them in the repository.
tags: [obs2pdf, reference]

# Pick a [profiles.<name>] table from ~/.config/obs2pdf/config.toml.
# Commented out because an undefined profile is an error.
# obs2pdf.profile: work

# Document type: notes, minutes, report, letter, cheatsheet, handout, or
# the name of a .typ file in ~/.config/obs2pdf/templates/.
obs2pdf.template: notes

# Empty = the note's single "# H1" heading, else the filename.
obs2pdf.title: All Options at a Glance

obs2pdf.author: Alex Example
obs2pdf.role: Editor                  # appended in footers: "Alex Example, Editor"
obs2pdf.affiliation:                  # header lines; a plain string also works
  - Example Organisation
  - Department of Examples

obs2pdf.lang: en                      # ISO 639-1; obs2pdf translates "en" and "de"
obs2pdf.paper: a4                     # any Typst paper name: a4, us-letter, a5, ...

# Paths: absolute, "~/..." or relative to this note. Empty = none.
obs2pdf.logo: ""                      # e.g. attachments/logo.png
obs2pdf.bibliography: ""              # e.g. references.bib, enables [@citekey]

obs2pdf.outline: true                 # table of contents
obs2pdf.outline_depth: 2              # 0 = all heading levels

obs2pdf.theme.flavor: latte           # latte, frappe, macchiato, mocha, none
obs2pdf.theme.accent: teal            # any Catppuccin accent name
obs2pdf.theme.print_friendly: true    # white page, black body text; false = flavor's own background
obs2pdf.theme.fallback_color: "#1e66f5"   # accent when flavor is "none"; quote the '#'

obs2pdf.fonts.body: Libertinus Serif
obs2pdf.fonts.heading: New Computer Modern   # empty = same as body
obs2pdf.fonts.mono: DejaVu Sans Mono
obs2pdf.fonts.size: 11                # body text size in pt; default depends on template

# Used by the letter template.
obs2pdf.contact.address:
  - Example Street 1
  - 12345 Example City
obs2pdf.contact.phone: "+00 123 456789"   # quote numbers you want kept as text
obs2pdf.contact.email: alex@example.org
obs2pdf.contact.web: example.org

# Used by the minutes template.
obs2pdf.minutes.date: 2026-11-19      # YYYY-MM-DD is formatted per `lang`
obs2pdf.minutes.time: "19:00 – 20:30"
obs2pdf.minutes.location: Community Hall, Room 2
obs2pdf.minutes.chair: "[[Alex Example]]"   # quote a value starting with [[
obs2pdf.minutes.minute_taker: Sam Sample    # empty = author
# People: plain names, "Role [[Name]]", or "[[Name|Role Name]]". The last
# form is one whole link for Obsidian (backlinks work); in the PDF only the
# name is a link and the rest of the alias becomes the role.
obs2pdf.minutes.present:
  - Treasurer [[Alex Example]]
  - "[[Jordan Doe|Secretary Jordan Doe]]"
  - Sam Sample
obs2pdf.minutes.absent:
  - Robin Roe
obs2pdf.minutes.guests:
  - "[[Casey Case]] (press)"          # quote when text follows the [[link]]
obs2pdf.minutes.action_items: true    # table of open "- [ ]" tasks at the end
obs2pdf.minutes.signatures: true      # signature lines for chair and minute-taker

# Used by the letter template.
obs2pdf.letter.recipient:
  - Example Corp.
  - Attn. Jane Roe
  - Main Street 1
  - 12345 Example City
obs2pdf.letter.subject: ""            # empty = the document title
obs2pdf.letter.date: ""               # empty = today
obs2pdf.letter.location: Example City # put before the date: "Example City, <date>"
obs2pdf.letter.annotations: Registered mail
# Reference line: free-form labels after `reference_signs.` (dots allowed).
obs2pdf.letter.reference_signs.Your ref: AB-12
obs2pdf.letter.reference_signs.Customer no.: "4711"
obs2pdf.letter.closing: Kind regards
obs2pdf.letter.format: DIN-5008-B     # or DIN-5008-A
obs2pdf.letter.style: din             # or fancy: color stripe + tinted letterhead
---
# Frontmatter Reference

This note sets **every** obs2pdf option in its YAML frontmatter. Open the
Markdown source to read it; the PDF shows the effect of the settings the
*notes* template uses: title, author and role in the footer, the
affiliation in the header, the `latte` flavor with a `teal` ==accent==, a
separate heading font and a two-level table of contents.

## Sections that belong to other templates

The `minutes`, `letter` and `contact` settings are accepted by every
template but only read by the one they belong to. Switch `obs2pdf.template`
to `minutes` or `letter` to see them in use; see [[minutes]] and [[letter]]
for smaller examples.

### Overriding from the command line

Flags beat frontmatter, so `obs2pdf all-options.md --catppuccin-flavor none`
renders this note without colors.

## Quoting in YAML

- Quote values starting with `#`, `@`, `*` or `[` if they are meant as text.
- Quote times (`"19:00"`) and numbers you want kept verbatim (`"4711"`).
- Lists can be written inline (`[a, b]`) or one `- item` per line.
