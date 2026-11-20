// obs2pdf template: handout
//
// Handouts, flyers, info sheets, tabletop player handouts: a single column
// of larger type, no page header or footer, a big title framed by accent
// rules, and unnumbered, centered top-level headings.

#show: obs2pdf-base.with(
  header: none,
  footer: none,
  margin: (x: 2.2cm, y: 2cm),
)

#show heading.where(depth: 1): it => block(width: 100%, above: 1.6em, below: 0.9em, align(center, {
  text(size: 1.3em, it.body)
  v(-0.4em)
  line(length: 25%, stroke: 0.8pt + obs2pdf-theme.accent)
}))

// A title framed by two full-width accent rules.
#let handout-framed(title) = {
  line(length: 100%, stroke: 2pt + obs2pdf-theme.accent)
  v(-0.2em)
  title
  v(-0.2em)
  line(length: 100%, stroke: 2pt + obs2pdf-theme.accent)
  v(0.8em)
}

// Part titles of multi-part notes (one per H1) are depth-1 headings too.
// This rule is defined after the heading rule above, so it runs first and the
// section-heading styling never sees them.
#show <obs2pdf-part-title>: it => block(width: 100%, above: 2em, handout-framed(
  align(center, par(justify: false, text(
    26pt, weight: "black", font: obs2pdf-heading-font, hyphenate: false,
    fill: obs2pdf-theme.title-fill, it.body,
  ))),
))

#if not obs2pdf-cfg.has_multiple_h1 and obs2pdf-cfg.title != "" {
  handout-framed(obs2pdf-title-block(size: 32pt))
}
