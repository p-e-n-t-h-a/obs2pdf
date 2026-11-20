// obs2pdf template: cheatsheet
//
// Dense reference sheet: landscape, three columns, small type and tight
// spacing, a one-line title bar instead of a title block, no page header.
// 8pt type by default (see [templates.cheatsheet] in defaults.toml).

#show: obs2pdf-base.with(
  flipped: true,
  header: none,
  margin: (x: 1cm, top: 1cm, bottom: 1.4cm),
)

#set par(justify: false, spacing: 0.75em)
#set list(spacing: 0.5em)
#set enum(spacing: 0.5em)
#show heading: set block(above: 1em, below: 0.5em)
#show heading.where(depth: 1): set text(size: 1.375em)
#show heading.where(depth: 2): set text(size: 1.19em)
#show heading.where(depth: 3): set text(size: 1.06em)
#show raw.where(block: true): set block(inset: 4pt, width: 100%, stroke: 0.5pt + obs2pdf-theme.accent)

#let obs2pdf-body(body) = columns(3, gutter: 12pt, body)

#if obs2pdf-cfg.title != "" {
  grid(
    columns: (1fr, auto),
    align: (left + bottom, right + bottom),
    text(16pt, weight: "black", font: obs2pdf-heading-font, fill: obs2pdf-theme.title-fill, obs2pdf-cfg.title),
    text(8pt, style: "italic", (obs2pdf-author-line, obs2pdf-today).filter(s => s != "").join(" · ")),
  )
  v(-0.2em)
  line(length: 100%, stroke: 1pt + obs2pdf-theme.accent)
}
