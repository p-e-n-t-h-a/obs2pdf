// Catppuccin theming shared by every obs2pdf template. Colors come from the
// real "catppuccin" Typst Universe package, not hardcoded hex values, so
// they always track upstream: https://typst.app/universe/package/catppuccin/
//
// Heading colors follow the Catppuccin style guide's numbered accent order:
// https://github.com/catppuccin/catppuccin/blob/main/docs/style-guide.md
// #1 Red (the extracted title), #2 Peach, #3 Yellow, #4 Green, #5 Sapphire,
// #6 Lavender. Only 5 colors remain for depths 1-6 (originally H2-H7), so
// depth 6 reuses the last one. Bold/italic have no color defined by the
// style guide, so they use a deliberate (and easily changed) pick: bold ->
// Sapphire, italic -> Green, highlight background -> Yellow.
//
// This file is concatenated ahead of _base.typ and the template itself by
// obs2pdf.templates.template_source() (not imported), so its #let bindings
// are simply in scope for what follows.

#let obs2pdf-title-role = "red"
#let obs2pdf-heading-role-order = ("peach", "yellow", "green", "sapphire", "lavender", "lavender")
#let obs2pdf-bold-role = "sapphire"
#let obs2pdf-italic-role = "green"
#let obs2pdf-highlight-role = "yellow"

// Resolves the [theme] settings (flavor, accent, print_friendly,
// fallback_color) into concrete colors for a template to use.
//
// flavor "none" gives a plain black-on-white page using fallback_color as
// the accent, without importing (or downloading) the catppuccin package.
//
// print_friendly forces the page background, body text, and the extracted
// title to black-on-white, while leaving headings/bold/italic/accent
// colored, so emphasis still stands out on a printed page.
#let obs2pdf-resolve-theme(theme) = {
  let flavor = theme.at("flavor", default: "none")
  let print-friendly = theme.at("print_friendly", default: false)
  if flavor == "none" or flavor == "" {
    return (
      accent: rgb(theme.at("fallback_color", default: "#1e66f5")),
      page-fill: white,
      text-fill: black,
      title-fill: black,
      heading-fill: (depth) => black,
      bold-fill: black,
      italic-fill: black,
      highlight-fill: rgb("#fffd11a1"), // Typst's own default
      highlight-text-fill: black,
    )
  }

  import "@preview/catppuccin:1.1.0": get-flavor
  let palette = get-flavor(flavor).colors
  let role-color(role) = rgb(palette.at(role).hex)

  (
    accent: role-color(theme.at("accent", default: "mauve")),
    page-fill: if print-friendly { white } else { role-color("base") },
    text-fill: if print-friendly { black } else { role-color("text") },
    title-fill: if print-friendly { black } else { role-color(obs2pdf-title-role) },
    heading-fill: (depth) => role-color(obs2pdf-heading-role-order.at(depth - 1)),
    bold-fill: role-color(obs2pdf-bold-role),
    italic-fill: role-color(obs2pdf-italic-role),
    // ==highlights==: dark text on the flavor's yellow (lightened on a
    // white page), readable either way.
    highlight-fill: if print-friendly {
      role-color(obs2pdf-highlight-role).lighten(55%)
    } else { role-color(obs2pdf-highlight-role) },
    highlight-text-fill: if print-friendly { black } else { role-color("base") },
  )
}
