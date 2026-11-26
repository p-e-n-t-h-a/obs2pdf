---
obs2pdf.template: letter
obs2pdf.letter.style: fancy
# Sender details normally live in a profile in your config.toml; they're
# set here so the example renders a full letterhead on its own.
obs2pdf.author: Jane Doe
obs2pdf.role: Electrical Engineering, M.Sc.
obs2pdf.contact.address:
  - Example Street 1
  - 12345 Example City
obs2pdf.contact.phone: +49 123 456789
obs2pdf.contact.email: jane.doe@example.org
obs2pdf.contact.web: example.org/jane
obs2pdf.letter.recipient:
  - Example Corp.
  - Attn. John Roe
  - Main Street 1
  - 12345 Example City
obs2pdf.letter.date: 2026-12-10
obs2pdf.letter.location: Example City
obs2pdf.letter.closing: Kind regards
---
# Application for the position of Signal Integrity Engineer

Dear Mr Roe,

with great interest I read your advertisement for a signal integrity
engineer. Over the past four years I have worked on exactly the physics
your tools analyse: vias, channels and printed circuit boards, from
full-wave simulation to published results.

The `fancy` letter style keeps the DIN 5008 layout of the plain letter —
address window, folding and hole marks, reference line — and adds a
Catppuccin color stripe, a tinted letterhead with the logo, author, role
and contact details, an underlined subject, and a running header and
footer when the letter runs to a second page.

I would be glad to tell you more in a personal conversation.
