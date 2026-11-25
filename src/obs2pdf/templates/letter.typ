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

// letter-pro's default header (sender block bottom right, rebuilt exactly as
// letter-simple does it) plus the logo at the left margin, its bottom edge
// 5mm above the end of the header box like the sender block's. Its height
// fits the header box: 20mm for DIN-5008-B, 12mm for the shallower A.
#let obs2pdf-letter-header = if obs2pdf-cfg.logo == "" { auto } else {
  let margin = obs2pdf-letter-margin
  let header-size = letter-formats.at(obs2pdf-letter.format).header-size
  let logo-height = calc.min(header-size - 15mm, 20mm)
  let sender = obs2pdf-letter-sender
  place(top + left, dx: margin.left, dy: header-size - 5mm - logo-height, obs2pdf-logo(logo-height))
  pad(left: margin.left, right: margin.right, top: margin.top, bottom: 5mm, align(
    bottom + right,
    header-simple(
      sender.name,
      if sender.address != none { sender.address.split(", ").join(linebreak()) },
      extra: sender.extra,
    ),
  ))
}

#set page(fill: obs2pdf-theme.page-fill)
#show: obs2pdf-base.with(setup-page: false)

#show: letter-simple.with(
  format: obs2pdf-letter.format,
  font: obs2pdf-body-font,
  margin: obs2pdf-letter-margin,
  header: obs2pdf-letter-header,
  sender: obs2pdf-letter-sender,
  recipient: obs2pdf-lines(obs2pdf-letter.recipient),
  annotations: if obs2pdf-letter.annotations != "" { obs2pdf-letter.annotations },
  reference-signs: obs2pdf-letter.reference_signs.pairs().map(((key, value)) => ([#key], [#value])),
  date: {
    let date = if obs2pdf-letter.date != "" { obs2pdf-format-date(obs2pdf-letter.date) } else { obs2pdf-today }
    if obs2pdf-letter.location != "" { [#obs2pdf-letter.location, #date] } else { date }
  },
  subject: if obs2pdf-letter.subject != "" {
    obs2pdf-letter.subject
  } else if obs2pdf-cfg.title != "" {
    obs2pdf-cfg.title
  },
)

#show: body => {
  body
  if obs2pdf-letter.closing != "" {
    v(0.65em)
    obs2pdf-letter.closing
    v(1.4cm)
    obs2pdf-cfg.author
  }
}
