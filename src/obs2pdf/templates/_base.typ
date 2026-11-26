// Shared base for every obs2pdf template, concatenated after _theme.typ and
// before the template's own file (see obs2pdf.templates.template_source).
//
// What it provides, for templates to use:
//
//   obs2pdf-cfg            all resolved settings (see defaults.toml), plus
//                          title, filename, has_multiple_h1, action_items
//   obs2pdf-theme          resolved colors: accent, page-fill, text-fill,
//                          title-fill, heading-fill(depth), bold-fill,
//                          italic-fill, highlight-fill, highlight-text-fill
//   obs2pdf-t(key)         a UI string in the document language
//   obs2pdf-format-date(d) "YYYY-MM-DD" or a datetime -> localized date
//   obs2pdf-base           `#show: obs2pdf-base.with(...)` — page setup and
//                          all the common show/set rules
//   obs2pdf-title-block()  the big centered title
//
// and the hooks the converted note body calls, which a template may
// redefine with its own `#let` after this file:
//
//   obs2pdf-body(body)          wraps the whole note body (e.g. in columns)
//   obs2pdf-inline-outline()    placed at the start of the body
//   obs2pdf-wikilink(body)      an Obsidian [[wiki link]]
//
// Settings arrive as one JSON document via `typst compile --input
// obs2pdf=...`, never substituted into the source as text, so titles or
// names containing Typst markup characters are always safe.

#import "@preview/cheq:0.4.0": checklist

// ---- Settings ----------------------------------------------------------

#let obs2pdf-merge(base, overlay) = {
  let result = base
  for (key, value) in overlay {
    if type(value) == dictionary and type(result.at(key, default: none)) == dictionary {
      result.insert(key, obs2pdf-merge(result.at(key), value))
    } else {
      result.insert(key, value)
    }
  }
  result
}

// Fallbacks for compiling a kept .typ file by hand without --input; obs2pdf
// itself always passes every setting. They mirror defaults.toml, except
// that the flavor is "none" so no package download is needed.
#let obs2pdf-fallback-cfg = (
  title: "", filename: "", author: "", role: "", affiliation: (),
  lang: "en", paper: "a4", logo: "", bibliography: "",
  outline: false, outline_depth: 0,
  has_multiple_h1: false, action_items: (),
  theme: (flavor: "none", accent: "mauve", print_friendly: true, fallback_color: "#1e66f5"),
  fonts: (body: "Libertinus Serif", heading: "", mono: "DejaVu Sans Mono", size: 10),
  contact: (address: (), phone: "", email: "", web: ""),
  minutes: (
    date: "", time: "", location: "", chair: "", minute_taker: "",
    present: (), absent: (), guests: (), action_items: true, signatures: true,
  ),
  letter: (
    recipient: (), subject: "", date: "", location: "", annotations: "",
    reference_signs: (:), closing: "", format: "DIN-5008-B", style: "din",
  ),
)

#let obs2pdf-cfg = {
  let raw = sys.inputs.at("obs2pdf", default: none)
  if raw == none { obs2pdf-fallback-cfg } else { obs2pdf-merge(obs2pdf-fallback-cfg, json(bytes(raw))) }
}

#let obs2pdf-theme = obs2pdf-resolve-theme(obs2pdf-cfg.theme)

// ---- Language ----------------------------------------------------------

#let obs2pdf-strings = (
  en: (
    dated: "Document dated",
    date: "Date",
    time: "Time",
    location: "Location",
    chair: "Chair",
    minute-taker: "Minute-taker",
    present: "Present",
    absent: "Absent",
    guests: "Guests",
    agenda-item: "Item",
    action-items: "Action items",
    task: "Task",
  ),
  de: (
    dated: "Dokument datiert",
    date: "Datum",
    time: "Uhrzeit",
    location: "Ort",
    chair: "Sitzungsleitung",
    minute-taker: "Protokollführung",
    present: "Anwesend",
    absent: "Abwesend",
    guests: "Gäste",
    agenda-item: "TOP",
    action-items: "Offene Aufgaben",
    task: "Aufgabe",
  ),
)

#let obs2pdf-t(key) = {
  let table = obs2pdf-strings.at(obs2pdf-cfg.lang, default: obs2pdf-strings.en)
  table.at(key, default: obs2pdf-strings.en.at(key))
}

// Each entry maps a datetime to a string. Typst's `[month repr:long]` is English-only, so
// non-English month names are looked up explicitly.
#let obs2pdf-de-months = (
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
)

#let obs2pdf-date-formats = (
  en: d => d.display("[month repr:long] [day padding:none], [year]"),
  de: d => str(d.day()) + ". " + obs2pdf-de-months.at(d.month() - 1) + " " + str(d.year()),
)

#let obs2pdf-format-date(value) = {
  let fmt = obs2pdf-date-formats.at(obs2pdf-cfg.lang, default: obs2pdf-date-formats.en)
  if type(value) == datetime { return fmt(value) }
  let m = str(value).match(regex("^(\d{4})-(\d{2})-(\d{2})$"))
  if m == none { return value }
  let (y, mo, d) = m.captures.map(int)
  fmt(datetime(year: y, month: mo, day: d))
}

#let obs2pdf-today = obs2pdf-format-date(datetime.today())

// ---- Small helpers -----------------------------------------------------

#let obs2pdf-font-list(name, fallback) = (if name != "" { (name,) } else { () }) + fallback
#let obs2pdf-body-font = obs2pdf-font-list(obs2pdf-cfg.fonts.body, ("Libertinus Serif",))
#let obs2pdf-heading-font = if obs2pdf-cfg.fonts.heading == "" { obs2pdf-body-font } else {
  obs2pdf-font-list(obs2pdf-cfg.fonts.heading, obs2pdf-body-font)
}
#let obs2pdf-mono-font = obs2pdf-font-list(obs2pdf-cfg.fonts.mono, ("DejaVu Sans Mono",))

// Lines of text joined with line breaks, or none if there are none.
#let obs2pdf-lines(lines) = if lines.len() > 0 { lines.join(linebreak()) }

// "Jane Doe, Secretary" — author plus role, for footers ("" if neither is set).
#let obs2pdf-author-line = {
  let parts = (obs2pdf-cfg.author, obs2pdf-cfg.role).filter(s => s != "")
  if parts.len() > 0 { parts.join(", ") } else { "" }
}

#let obs2pdf-logo(height) = if obs2pdf-cfg.logo != "" { image(obs2pdf-cfg.logo, height: height) }

// Pandoc emits `#horizontalrule` for a Markdown `---`.
#let horizontalrule = line(length: 100%, stroke: 1pt + obs2pdf-theme.accent)

// ---- Hooks called from the converted note body -------------------------

#let obs2pdf-body(body) = body

#let obs2pdf-outline() = if obs2pdf-cfg.outline {
  let depth = obs2pdf-cfg.outline_depth
  outline(indent: auto, depth: if depth > 0 { depth } else { none })
}
#let obs2pdf-inline-outline() = obs2pdf-outline()

#let obs2pdf-wikilink(body) = text(fill: obs2pdf-theme.accent, weight: "bold", body)

// ---- Page and text setup -----------------------------------------------

#let obs2pdf-default-header = context grid(
  columns: (1fr, 1fr),
  align: (left + horizon, right + horizon),
  text(8pt, style: "italic", obs2pdf-cfg.filename),
  stack(
    dir: ltr,
    spacing: 6pt,
    align(horizon, text(8pt, style: "italic", obs2pdf-lines(obs2pdf-cfg.affiliation))),
    align(horizon, obs2pdf-logo(0.9cm)),
  ),
)

#let obs2pdf-default-footer = context grid(
  columns: (1fr, 1fr, 1fr),
  align: (left + horizon, center + horizon, right + horizon),
  text(8pt, style: "italic", obs2pdf-author-line),
  text(8pt, style: "italic", [#obs2pdf-t("dated"): #obs2pdf-today]),
  text(8pt, style: "italic", counter(page).display("1 / 1", both: true)),
)

// The common look. Templates pass only what they change:
//   header / footer   auto (the defaults above), none, or custom content
//   setup-page        false to leave `set page` entirely to the template
//                     (e.g. when a package such as letter-pro owns it)
//   text-size         auto = the `fonts.size` setting (set per-template
//                     defaults in defaults.toml, not here)
#let obs2pdf-base(
  header: auto,
  footer: auto,
  setup-page: true,
  margin: (bottom: 2cm, top: 2cm, left: 1.5cm, right: 1.5cm),
  flipped: false,
  text-size: auto,
  heading-numbering: none,
  body,
) = {
  let cfg = obs2pdf-cfg
  let theme = obs2pdf-theme

  set document(
    title: cfg.title,
    author: (cfg.author,).filter(a => a != ""),
  )
  set page(
    paper: cfg.paper,
    flipped: flipped,
    margin: margin,
    fill: theme.page-fill,
    header: if header == auto { obs2pdf-default-header } else { header },
    footer: if footer == auto { obs2pdf-default-footer } else { footer },
  ) if setup-page
  let text-size = if text-size == auto { cfg.fonts.size * 1pt } else { text-size }
  set text(font: obs2pdf-body-font, size: text-size, lang: cfg.lang, fill: theme.text-fill)
  set par(justify: true)
  set heading(numbering: heading-numbering)

  show heading: set text(font: obs2pdf-heading-font, weight: "bold")
  show raw: set text(font: obs2pdf-mono-font, weight: "regular")
  show quote.where(block: true): it => block(
    inset: (left: 1em, rest: 0.4em),
    stroke: (left: 2.5pt + theme.accent),
    it.body,
  )
  show link: set text(fill: theme.accent)
  show link: underline
  show heading.where(depth: 1): set text(fill: (theme.heading-fill)(1))
  show heading.where(depth: 2): set text(style: "italic", fill: (theme.heading-fill)(2))
  show heading.where(depth: 3): set text(fill: (theme.heading-fill)(3))
  show heading.where(depth: 3): underline
  show heading.where(depth: 4): set text(fill: (theme.heading-fill)(4))
  show heading.where(depth: 5): set text(fill: (theme.heading-fill)(5))
  show heading.where(depth: 6): set text(fill: (theme.heading-fill)(6))
  show strong: set text(fill: theme.bold-fill)
  show emph: set text(fill: theme.italic-fill)
  set highlight(fill: theme.highlight-fill)
  show highlight: set text(fill: theme.highlight-text-fill)
  show <obs2pdf-part-title>: it => align(center, par(justify: false, text(
    20pt, weight: "black", font: obs2pdf-heading-font, hyphenate: false, fill: theme.title-fill, it.body,
  )))
  show outline.entry.where(level: 1): set text(weight: "bold")
  show outline.entry.where(level: 2): set text(style: "italic")
  show outline.entry.where(level: 3): set text(size: 0.9em)
  show figure: set text(size: 0.8em)
  // Pandoc wraps every table in a figure, and figures don't break across
  // pages by default: a long table would be pushed onto its own page and
  // overflow it. Let it break; `table.header` rows repeat on each page.
  show figure.where(kind: table): set block(breakable: true)
  show: checklist

  body

  if cfg.bibliography != "" {
    bibliography(cfg.bibliography)
  }
}

// The big centered document title. Not shown for multi-part notes (more
// than one H1), whose H1s are rendered inline as part titles instead; see
// obs2pdf.postprocess.wrap_page_parts.
#let obs2pdf-title-block(size: 25pt) = {
  if not obs2pdf-cfg.has_multiple_h1 and obs2pdf-cfg.title != "" {
    align(center, par(justify: false, text(
      size, weight: "black", font: obs2pdf-heading-font, hyphenate: false,
      fill: obs2pdf-theme.title-fill, obs2pdf-cfg.title,
    )))
  }
}
