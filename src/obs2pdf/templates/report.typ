// obs2pdf template: report
//
// Single-column report: a title page (logo, title, author, affiliation,
// date), the table of contents on its own page (on by default — set
// `outline = false` to drop it), numbered headings with every top-level
// section starting on a new page, and the usual header/footer from page 2.
// Set `bibliography` to a .bib file to resolve [@citekey] citations.

#show: obs2pdf-base.with(
  heading-numbering: "1.1.1",
  margin: (x: 2.5cm, top: 2.5cm, bottom: 2.5cm),
)

#show heading.where(depth: 1): it => {
  pagebreak(weak: true)
  v(1em)
  text(size: 1.4em, it)
  v(0.6em)
}

// The table of contents goes on its own page below, not inline.
#let obs2pdf-inline-outline() = none

#page(header: none, footer: none, {
  set align(center)
  set par(justify: false)
  obs2pdf-logo(2.5cm)
  v(1fr)
  text(28pt, weight: "black", font: obs2pdf-heading-font, hyphenate: false, fill: obs2pdf-theme.title-fill, obs2pdf-cfg.title)
  v(0.8em)
  line(length: 40%, stroke: 1.5pt + obs2pdf-theme.accent)
  v(0.8em)
  text(14pt, obs2pdf-author-line)
  v(0.3em)
  text(11pt, obs2pdf-lines(obs2pdf-cfg.affiliation))
  v(1fr)
  text(11pt, obs2pdf-today)
})

#if obs2pdf-cfg.outline {
  obs2pdf-outline()
  pagebreak(weak: true)
}
