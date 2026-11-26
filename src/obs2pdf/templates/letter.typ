// obs2pdf template: letter
//
// DIN 5008 business letter, laid out by the letter-pro package
// (https://typst.app/universe/package/letter-pro). The note's body is the
// letter text. The sender comes from `author` and the [contact] settings
// (typically set once in a profile), the rest from [letter], usually set
// per note:
//
//   ---
//   obs2pdf:
//     template: letter
//     letter:
//       recipient: [Example Corp., Jane Roe, Main Street 1, 12345 Example City]
//       subject: Your offer of 1 November     # default: the note's title
//       location: Example City                # "Example City, <date>"
//       reference_signs: { Your ref: AB-12 }
//       closing: Kind regards
//   ---
//
// Catppuccin theming is off for letters by default (theme.flavor = "none",
// see [templates.letter] in defaults.toml).
//
// If `logo` is set it goes top left in the letterhead, opposite the sender
// block; without one the header is letter-pro's default.
//
// letter.style = "fancy" keeps the DIN layout (address window, folding and
// hole marks) but adds a Catppuccin accent stripe along the top of every
// page, a tinted letterhead band (logo, author, role, contact details), an
// underlined subject, and a running header and footer on multi-page
// letters. It always uses Catppuccin colors: theme.flavor picks the
// palette ("none", the letter default, means Latte) and theme.accent the
// highlight color.

#import "@preview/letter-pro:3.0.0": header-simple, letter-formats, letter-simple

#let obs2pdf-letter = obs2pdf-cfg.letter
#let obs2pdf-contact = obs2pdf-cfg.contact

// letter-pro's default margins, spelled out because the logo header needs them.
#let obs2pdf-letter-margin = (left: 25mm, right: 20mm, top: 20mm, bottom: 20mm)

#let obs2pdf-letter-sender = (
  name: obs2pdf-cfg.author,
  address: if obs2pdf-contact.address.len() > 0 { obs2pdf-contact.address.join(", ") },
  extra: obs2pdf-lines(
    (obs2pdf-contact.phone, obs2pdf-contact.email, obs2pdf-contact.web).filter(s => s != ""),
  ),
)

// letter-pro's default header layout (sender block bottom right, rebuilt
// exactly as letter-simple does it) plus the logo at the left margin, its
// bottom edge 5mm above the end of the header box like the sender block's.
// Its height fits the header box: 20mm for DIN-5008-B, 12mm for the
// shallower A. Shared by both styles; `fancy` passes a colored sender block.
#let obs2pdf-letter-letterhead(sender-block) = {
  let margin = obs2pdf-letter-margin
  let header-size = letter-formats.at(obs2pdf-letter.format).header-size
  if obs2pdf-cfg.logo != "" {
    let logo-height = calc.min(header-size - 15mm, 20mm)
    place(top + left, dx: margin.left, dy: header-size - 5mm - logo-height, obs2pdf-logo(logo-height))
  }
  pad(left: margin.left, right: margin.right, top: margin.top, bottom: 5mm, align(bottom + right, sender-block))
}

#let obs2pdf-letter-sender-address = if obs2pdf-letter-sender.address != none {
  obs2pdf-letter-sender.address.split(", ").join(linebreak())
}

// Without a logo, letter-pro builds the very same header itself.
#let obs2pdf-letter-header = if obs2pdf-cfg.logo == "" { auto } else {
  obs2pdf-letter-letterhead(header-simple(
    obs2pdf-letter-sender.name,
    obs2pdf-letter-sender-address,
    extra: obs2pdf-letter-sender.extra,
  ))
}

#let obs2pdf-letter-date = if obs2pdf-letter.date != "" {
  obs2pdf-format-date(obs2pdf-letter.date)
} else { obs2pdf-today }

#let obs2pdf-letter-subject = if obs2pdf-letter.subject != "" {
  obs2pdf-letter.subject
} else if obs2pdf-cfg.title != "" {
  obs2pdf-cfg.title
}

// A multi-line subject is set ragged right (not justified: obs2pdf-base
// justifies everything, which stretched the first line's word spacing) and
// balanced: kept to as few lines as at full width, but in the narrowest
// block that allows that, so its lines come out about equally long instead
// of one full line and a stray word or two.
//
// The bold weight (which letter-pro adds around the subject) is set here
// too: `measure` doesn't see it from outside, so it would measure regular
// text, find it fits narrower, and break the real bold text too early.
#let obs2pdf-letter-balanced(body) = layout(size => {
  let body = {
    set par(justify: false)
    set text(weight: "bold")
    body
  }
  let height(width) = measure(block(width: width, body)).height
  let target = height(size.width)
  let (lo, hi) = (0pt, size.width)
  for _ in range(14) {
    let mid = (lo + hi) / 2
    if height(mid) > target { lo = mid } else { hi = mid }
  }
  block(width: hi, body)
})

// ---- letter.style = "fancy" --------------------------------------------

#let obs2pdf-letter-fancy = obs2pdf-letter.style == "fancy"

// The Catppuccin flavor; Latte when theme.flavor is "none". Only loaded for
// the fancy style, so plain letters still don't need the package.
//
// Every color of the fancy style is a palette role, not obs2pdf-theme's
// print-friendly black: body text subtext1, headings/name text, secondary
// text overlay1, separators surface2, letterhead band crust. The page is
// white for a light flavor with print_friendly, else the flavor's base.
#let obs2pdf-letter-flavor = if obs2pdf-letter-fancy {
  import "@preview/catppuccin:1.1.0": get-flavor
  let flavor = obs2pdf-cfg.theme.flavor
  get-flavor(if flavor in ("none", "") { "latte" } else { flavor })
}
#let obs2pdf-letter-palette = if obs2pdf-letter-fancy { obs2pdf-letter-flavor.colors }
#let obs2pdf-letter-color(role) = rgb(obs2pdf-letter-palette.at(role).hex)
#let obs2pdf-letter-paper = if obs2pdf-letter-fancy {
  if obs2pdf-letter-flavor.light and obs2pdf-cfg.theme.print_friendly { white } else { obs2pdf-letter-color("base") }
}

#let obs2pdf-letter-accent = if obs2pdf-letter-fancy { obs2pdf-letter-color(obs2pdf-cfg.theme.accent) }
#let obs2pdf-letter-gradient = if obs2pdf-letter-fancy {
  gradient.linear(obs2pdf-letter-accent, obs2pdf-letter-color("blue"))
}

// All 14 Catppuccin accents, in the palette's own order, as a thin stripe
// across the top edge of every page.
#let obs2pdf-letter-stripe = if obs2pdf-letter-fancy {
  let accents = obs2pdf-letter-palette
    .values()
    .filter(c => c.at("accent", default: false))
    .sorted(key: c => c.order)
  place(top + left, stack(dir: ltr, ..accents.map(c => rect(
    width: 100% / accents.len(),
    height: 4pt,
    fill: rgb(c.hex),
  ))))
}

// The first-page letterhead: the plain letter's layout (logo left, sender
// block bottom right, same sizes), on a tinted band filling letter-pro's
// header box, with the name in the palette's text color, the role (if any)
// below it in the accent color, and email/web as colored links.
#let obs2pdf-letter-fancy-header = if obs2pdf-letter-fancy {
  let contact = obs2pdf-contact
  let web-url(s) = if s.starts-with("http") { s } else { "https://" + s }
  let extra = (
    contact.phone,
    if contact.email != "" { link("mailto:" + contact.email, contact.email) },
    if contact.web != "" { link(web-url(contact.web), contact.web) },
  ).filter(it => it not in (none, ""))
  let sender-block = {
    set text(fill: obs2pdf-letter-color("subtext1"))
    // No hanging punctuation: a trailing "." would stick out past the edge.
    set text(overhang: false)
    // Links here are colored, not underlined like in the body.
    show underline: it => it.body
    show link: set text(fill: obs2pdf-letter-color("blue"))
    header-simple(
      {
        text(fill: obs2pdf-letter-color("text"), obs2pdf-cfg.author)
        if obs2pdf-cfg.role != "" {
          linebreak()
          text(size: 8pt, fill: obs2pdf-letter-accent, tracking: 1.2pt, upper(obs2pdf-cfg.role))
        }
      },
      obs2pdf-letter-sender-address,
      extra: obs2pdf-lines(extra),
    )
  }
  block(
    width: 100%,
    height: 100%,
    fill: obs2pdf-letter-color("crust"),
    stroke: (bottom: 1pt + obs2pdf-letter-color("surface0")),
    obs2pdf-letter-letterhead(sender-block),
  )
}

// Running header from page 2 on: author and role, the date opposite, and a
// fading accent rule underneath.
#let obs2pdf-letter-running-header = context if here().page() > 1 {
  set text(size: 8.5pt, fill: obs2pdf-letter-color("overlay1"))
  grid(
    columns: (1fr, auto),
    align: bottom,
    {
      text(size: 10pt, weight: "bold", fill: obs2pdf-letter-color("text"), obs2pdf-cfg.author)
      if obs2pdf-cfg.role != "" {
        h(8pt)
        text(weight: "bold", fill: obs2pdf-letter-accent, tracking: 1.2pt, upper(obs2pdf-cfg.role))
      }
    },
    obs2pdf-letter-date,
  )
  v(-4pt)
  line(length: 100%, stroke: (
    paint: gradient.linear(obs2pdf-letter-accent, obs2pdf-letter-color("blue"), obs2pdf-letter-paper),
    thickness: 1pt,
  ))
}

// letter-pro's page number line (shown on multi-page letters only), as
// "Author · Subject" on the left and "2 / 3" on the right.
#let obs2pdf-letter-page-numbering(current, total) = {
  set text(size: 8pt, fill: obs2pdf-letter-color("overlay1"))
  let faint(body) = text(fill: obs2pdf-letter-color("surface2"), body)
  grid(
    columns: (1fr, auto),
    column-gutter: 12pt,
    align: (left, right),
    (obs2pdf-cfg.author, obs2pdf-letter-subject).filter(s => s not in (none, "")).join([ #h(3pt)#faint[·]#h(3pt) ]),
    [#text(weight: "bold", fill: obs2pdf-letter-accent, str(current))#faint(" / ")#total],
  )
}

// The subject, larger, with a short accent rule below it. letter-pro sets
// it in bold already.
#let obs2pdf-letter-fancy-subject = if obs2pdf-letter-fancy and obs2pdf-letter-subject != none {
  obs2pdf-letter-balanced(text(size: 1.15em, fill: obs2pdf-letter-color("text"), obs2pdf-letter-subject))
  v(-2pt)
  line(length: 2.5cm, stroke: (paint: obs2pdf-letter-gradient, thickness: 2pt, cap: "round"))
  v(4pt)
}

// ---- Page setup --------------------------------------------------------

#set page(fill: obs2pdf-theme.page-fill)
// letter-pro owns margins, the folding marks (page background) and the
// footer, but leaves foreground and header free.
#set page(
  fill: obs2pdf-letter-paper,
  foreground: obs2pdf-letter-stripe,
  header: obs2pdf-letter-running-header,
) if obs2pdf-letter-fancy
#show: obs2pdf-base.with(setup-page: false)

// Fancy body text (and recipient, date, closing) in the palette's subtext1.
// Without a flavor, obs2pdf-theme would set bold/italic in black; keep them
// in the body color instead (with a flavor, they keep the theme's colors).
#set text(fill: obs2pdf-letter-color("subtext1")) if obs2pdf-letter-fancy
#show strong: set text(fill: obs2pdf-letter-color("subtext1")) if (
  obs2pdf-letter-fancy and obs2pdf-cfg.theme.flavor == "none"
)
#show emph: set text(fill: obs2pdf-letter-color("subtext1")) if (
  obs2pdf-letter-fancy and obs2pdf-cfg.theme.flavor == "none"
)

#show: letter-simple.with(
  format: obs2pdf-letter.format,
  font: obs2pdf-body-font,
  margin: obs2pdf-letter-margin,
  header: if obs2pdf-letter-fancy { obs2pdf-letter-fancy-header } else { obs2pdf-letter-header },
  page-numbering: if obs2pdf-letter-fancy { obs2pdf-letter-page-numbering } else { auto },
  sender: obs2pdf-letter-sender,
  recipient: obs2pdf-lines(obs2pdf-letter.recipient),
  annotations: if obs2pdf-letter.annotations != "" { obs2pdf-letter.annotations },
  reference-signs: obs2pdf-letter.reference_signs.pairs().map(((key, value)) => ([#key], [#value])),
  date: {
    let date = obs2pdf-letter-date
    if obs2pdf-letter.location != "" { [#obs2pdf-letter.location, #date] } else { date }
  },
  subject: if obs2pdf-letter-fancy {
    obs2pdf-letter-fancy-subject
  } else if obs2pdf-letter-subject != none {
    obs2pdf-letter-balanced(obs2pdf-letter-subject)
  },
)

// letter-pro makes the subject the PDF title, but the balanced subject is
// measured layout with no extractable text; set the plain string instead.
#set document(title: obs2pdf-letter-subject)

#show: body => {
  body
  if obs2pdf-letter.closing != "" {
    v(0.65em)
    obs2pdf-letter.closing
    v(1.4cm)
    obs2pdf-cfg.author
  }
}
