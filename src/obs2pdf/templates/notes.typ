// obs2pdf template: notes (default)
//
// General-purpose notes: two columns, numbered headings (1, 1.1, 1.1.1),
// page header with the file name and affiliation (plus logo), footer with
// author, date and page count.

#show: obs2pdf-base.with(heading-numbering: "1.1.1")

#let obs2pdf-body(body) = columns(2, gutter: 18pt, body)

#obs2pdf-title-block()
