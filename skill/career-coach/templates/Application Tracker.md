---
created: {{date}}
tags:
  - career/application
  - type/tracker
---
# Application Tracker

A hand-kept view of every role you are considering. `cc.py import-tracker --dry-run` reads this table and prints the `cc.py applied` calls for rows whose Status starts with "Applied", so keep the seven columns and write applied rows as `Applied YYYY-MM-DD`.

## Active

| Company | Role | Lane | Status | Resume sent | Next action | Date |
|---|---|---|---|---|---|---|
| Acme Robotics | Business Operations Associate | A | Not applied | - | Apply this week; note to the hiring manager after. [apply](https://example.com/jobs/1) | 2026-11-01 |
| Globex Systems | Partnerships Associate (New Grad) | A | Applied 2026-11-03 | Resume_Ops.pdf | Follow up on 11-13, naming the req | 2026-11-03 |
| Initech | Sales Development Representative | B | Skipped 2026-11-04 (asks 3+ years) | - | None | 2026-11-04 |

## Logging rules
- Log the exact PDF filename you uploaded, so you know which version they read when they call.
- Status values: Not applied, Applied YYYY-MM-DD, Skipped YYYY-MM-DD (reason), Closed, Interviewing, Offer, Rejected.
- Skip any role whose required or preferred experience is 3+ years, unless you decide to stretch.
