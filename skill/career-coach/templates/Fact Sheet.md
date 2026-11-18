---
created: {{date}}
tags:
  - career/resume
  - type/reference
---
# Fact Sheet

The single source of truth for every number, date, title and count about you that appears on a resume, on LinkedIn, in a cover letter, in a form answer or in an outreach note. Claude may cite a fact only from a row whose Status is exactly `decided` or starts with `verified`. Everything else is blocked, and `cc.py check` refuses drafts that use its numbers.

Status key:
- **verified**: a record backs it (offer letter, results page, tracker, analytics). Add the source in the last column.
- **decided**: you picked one value where records disagree or are missing, and you will stand behind it in an interview.
- **estimate**: your own number with no record yet. Blocked.
- **conflict**: two documents disagree. Blocked until you settle it.
- **blocked**: retired or never to be printed. Its numbers are refused even in other wording.
- **example**: placeholder rows from the template. Blocked. Delete them or replace them with real rows.

Rules that keep the checker honest:
- Keep the Status cell to the status word only (notes go in the last column), or the row reads as blocked.
- Put the exact printable wording in "Value to use", including units ("$180K", "31", "4th").
- When you retire a number, keep the row with status `blocked` so old phrasings still get caught.

## Example Club (replace with a real club, team or project)

| Fact | Value to use | Status | Source / note |
|---|---|---|---|
| Role and dates | Sponsorship Lead, Sep 2024 to May 2026 | example | club roster |
| Team size | 30+ | example | roster count, spring 2026 |
| Corporate sponsors closed | 12 | example | sponsor tracker |
| Competition result | 2nd of 20 teams, Apr 2026 | example | results page URL |
| Team size, older figure | 45 | blocked | an old resume said 45; the roster never passed 35 |

## Example Corp internship (replace)

| Fact | Value to use | Status | Source / note |
|---|---|---|---|
| Title and dates | Operations Intern, Jun 2025 to Aug 2025 | example | offer letter |
| Tool users | 150+ daily users | example | manager quoted internal analytics |
| Savings | about $40K a year | estimate | your own estimate; blocked until a record backs it |

## Education

| Fact | Value to use | Status | Source / note |
|---|---|---|---|
| School | State University | example | |
| Degrees | B.S. Computer Science; B.A. Economics | example | list each degree as its own education entry on forms |
| Graduation | May 2027 | example | |
| GPA (cumulative) | 3.5 | example | forms get the cumulative GPA unless they ask for major GPA |
