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
//       reference_signs: { Your ref: AB-12 }
//       closing: Kind regards
//   ---
//
// Catppuccin theming is off for letters by default (theme.flavor = "none",
// see [templates.letter] in defaults.toml).

#import "@preview/letter-pro:3.0.0": letter-simple

#let obs2pdf-letter = obs2pdf-cfg.letter
#let obs2pdf-contact = obs2pdf-cfg.contact

#set page(fill: obs2pdf-theme.page-fill)
#show: obs2pdf-base.with(setup-page: false)

#show: letter-simple.with(
  format: obs2pdf-letter.format,
  font: obs2pdf-body-font,
  sender: (
    name: obs2pdf-cfg.author,
    address: if obs2pdf-contact.address.len() > 0 { obs2pdf-contact.address.join(", ") },
    extra: obs2pdf-lines(
      (obs2pdf-contact.phone, obs2pdf-contact.email, obs2pdf-contact.web).filter(s => s != ""),
    ),
  ),
  recipient: obs2pdf-lines(obs2pdf-letter.recipient),
  annotations: if obs2pdf-letter.annotations != "" { obs2pdf-letter.annotations },
  reference-signs: obs2pdf-letter.reference_signs.pairs().map(((key, value)) => ([#key], [#value])),
  date: if obs2pdf-letter.date != "" { obs2pdf-format-date(obs2pdf-letter.date) } else { obs2pdf-today },
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
