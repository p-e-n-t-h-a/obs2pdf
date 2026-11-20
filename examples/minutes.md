---
# Flat `obs2pdf.*` keys instead of a nested `obs2pdf:` mapping, so every
# setting is a plain property in Obsidian's Properties panel.
# People carry their role inside the link alias: Obsidian sees one whole
# link (backlinks work), the PDF links only the name and puts the rest of
# the alias in the role column.
obs2pdf.template: minutes
obs2pdf.minutes.date: 2026-11-19
obs2pdf.minutes.time: "19:00 – 20:30"
obs2pdf.minutes.location: Community Hall, Room 2
obs2pdf.minutes.chair: "[[Alex Example]]"
obs2pdf.minutes.minute_taker: "[[Jordan Doe]]"
obs2pdf.minutes.present:
  - "[[Alex Example|Chair Alex Example]]"
  - "[[Sam Sample|Treasurer Sam Sample (from item 2)]]"
  - "[[Jordan Doe|Secretary Jordan Doe]]"
  - Youth Officer vacant
obs2pdf.minutes.absent:
  - "[[Robin Roe|Board Member Robin Roe (voted by mail)]]"
obs2pdf.minutes.guests:
  - "[[Casey Case|Speaker Casey Case]]"
---
# Board Meeting November

## Opening

The chair opens the meeting at 19:02 and confirms a quorum.

## Annual Budget

The treasurer presents the draft budget. **Decision:** approved unanimously.

- [ ] Sam: publish the budget on the website
- [x] Jordan: send invitations

## Summer Festival

- [ ] **Jordan** books the venue by [[2027-01-15]]
- [ ] Alex asks the city about permits

## Any Other Business

None.
