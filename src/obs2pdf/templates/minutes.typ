// obs2pdf template: minutes
//
// Meeting minutes. Every top-level section ("## ..." in the note) is an
// agenda item ("TOP 1" in German, "Item 1" in English), centered. Below
// the title sits a block with the meeting details; at the end come a table
// of all open "- [ ]" tasks and signature lines for chair and minute-taker.
// Meeting details come from the [minutes] settings, usually set per note:
//
//   ---
//   obs2pdf:
//     template: minutes
//     minutes:
//       date: 2026-11-19
//       time: "19:00 – 21:00"
//       location: Clubhouse
//       chair: John Roe
//       present: [Jane Doe, John Roe]
//       absent: [Max Mustermann]
//   ---
//
// A person (chair, minute_taker, or an entry of present/absent/guests) can
// be a plain name or a wiki link with an optional role around it:
//
//       chair: Chair [[John Roe]]
//       present:
//         - Treasurer [[Jane Doe]]
//         - [[John Roe|John]]
//         - "[[Max Mustermann]] (guest)"   # YAML needs quotes here
//         - "[[Erika Musterfrau|Secretary Erika Musterfrau]]"
//
// The last form keeps the role inside the link, so Obsidian's Properties
// panel sees the whole entry as a link (backlinks work); in the PDF only
// the name is a link and the rest of the alias becomes the role.
//
// Linked names are styled like wiki links in the body. As soon as anyone
// in a list has a role, the list is set as aligned name/role rows instead
// of a comma-separated line.

#let obs2pdf-minutes = obs2pdf-cfg.minutes

// "Role [[Name|Alias]]" -> (name: "Alias", role: "Role", linked: true);
// text after the link counts as role too, a plain entry is just a name.
// An alias that contains the note name splits around it, so the whole
// entry can be one link in Obsidian's Properties panel while only the name
// is a link in the PDF: "[[Jane Doe|Treasurer Jane Doe (absent)]]" ->
// (name: "Jane Doe", role: "Treasurer (absent)").
#let obs2pdf-minutes-person(entry) = {
  let m = entry.match(regex("^(.*?)\[\[([^\]|]*)(?:\|([^\]]*))?\]\](.*)$"))
  if m == none { return (name: entry.trim(), role: "", linked: false) }
  let (before, target, alias, after) = m.captures
  let target = target.trim()
  let alias = if alias == none { "" } else { alias.trim() }
  let name = if alias != "" { alias } else { target }
  let parts = (before,)
  let pos = if alias != "" and target != "" { alias.position(target) }
  if pos != none {
    name = target
    parts += (alias.slice(0, pos), alias.slice(pos + target.len()))
  }
  parts.push(after)
  // Trim separators left over from "Name, Role" / "Role: Name".
  let role = parts.map(s => s.trim(regex("[\s,;:–—-]+"))).filter(s => s != "").join(" ")
  (name: name, role: if role == none { "" } else { role }, linked: true)
}

#let obs2pdf-minutes-name(person) = {
  if person.linked { obs2pdf-wikilink(person.name) } else { person.name }
}

// One person on a line: "Name (Role)".
#let obs2pdf-minutes-inline(entry) = {
  if entry == "" { return "" }
  let p = obs2pdf-minutes-person(entry)
  if p.role == "" { obs2pdf-minutes-name(p) } else [#obs2pdf-minutes-name(p) (#p.role)]
}

// A list of people: comma-separated names (content), or, if anyone has a
// role, an array of (name, role) rows for the details grid to align.
#let obs2pdf-minutes-people(entries) = {
  let people = entries.map(obs2pdf-minutes-person).filter(p => p.name != "")
  if people.len() == 0 { return none }
  if people.all(p => p.role == "") {
    people.map(obs2pdf-minutes-name).join(", ")
  } else {
    people.map(p => (obs2pdf-minutes-name(p), p.role))
  }
}

#let obs2pdf-minute-taker = if obs2pdf-minutes.minute_taker != "" {
  obs2pdf-minutes.minute_taker
} else {
  obs2pdf-cfg.author
}

#show: obs2pdf-base

#show heading.where(depth: 1, outlined: true): set heading(
  numbering: (..n) => obs2pdf-t("agenda-item") + " " + str(n.pos().first()),
)
// Part titles of multi-part notes are depth-1 headings too; returning `it`
// leaves them to the base <obs2pdf-part-title> rule.
#show heading.where(depth: 1): it => {
  if it.at("label", default: none) == <obs2pdf-part-title> { return it }
  show: block.with(breakable: false, width: 100%)
  show: align.with(center)
  show: par.with(justify: false)
  show: text.with(hyphenate: false)
  if it.numbering != none {
    context counter(heading).display(it.numbering)
    linebreak()
  }
  it.body
}

#let obs2pdf-body(body) = columns(2, gutter: 18pt, body)

#let obs2pdf-minutes-details() = {
  let m = obs2pdf-minutes
  let rows = (
    ("date", obs2pdf-format-date(m.date)),
    ("time", m.time),
    ("location", m.location),
    ("chair", obs2pdf-minutes-inline(m.chair)),
    ("minute-taker", obs2pdf-minutes-inline(obs2pdf-minute-taker)),
    ("present", obs2pdf-minutes-people(m.present)),
    ("absent", obs2pdf-minutes-people(m.absent)),
    ("guests", obs2pdf-minutes-people(m.guests)),
  ).filter(((key, value)) => value != none and value != "")
  if rows.len() > 0 {
    v(0.4em)
    block(
      width: 100%,
      inset: (y: 0.6em),
      stroke: (top: 1pt + obs2pdf-theme.accent, bottom: 1pt + obs2pdf-theme.accent),
      // label | name | role; everything but name/role rows spans both.
      grid(
        columns: (auto, auto, 1fr),
        column-gutter: 1.2em,
        row-gutter: 0.6em,
        ..rows.map(((key, value)) => {
          let label = text(weight: "bold", obs2pdf-t(key))
          if type(value) == array {
            value.enumerate().map(((i, (name, role))) => (if i == 0 { label }, name, role))
          } else {
            ((label, grid.cell(colspan: 2, value)),)
          }
        }).flatten(),
      ),
    )
    v(0.6em)
  }
}

#let obs2pdf-minutes-closing() = {
  let m = obs2pdf-minutes
  let tasks = obs2pdf-cfg.action_items
  if m.action_items and tasks.len() > 0 {
    v(1.2em)
    heading(depth: 1, numbering: none, outlined: false, obs2pdf-t("action-items"))
    table(
      columns: (auto, 1fr),
      stroke: 0.5pt + obs2pdf-theme.accent,
      inset: 6pt,
      table.header(text(weight: "bold")[\#], text(weight: "bold", obs2pdf-t("task"))),
      ..tasks.enumerate().map(((i, task)) => (str(i + 1), task)).flatten(),
    )
  }
  if m.signatures {
    v(3.5em)
    let signers = (
      (m.chair, obs2pdf-t("chair")),
      (obs2pdf-minute-taker, obs2pdf-t("minute-taker")),
    ).map(((entry, label)) => (obs2pdf-minutes-person(entry).name, label))
    block(breakable: false, grid(
      columns: (1fr, 1fr),
      column-gutter: 2cm,
      ..signers.map(((name, label)) => {
        line(length: 100%, stroke: 0.6pt + obs2pdf-theme.text-fill)
        v(-0.3em)
        text(9pt, (name, label).filter(s => s != "").join(linebreak()))
      }),
    ))
  }
}

#show: body => {
  body
  obs2pdf-minutes-closing()
}

#obs2pdf-title-block()
#obs2pdf-minutes-details()
