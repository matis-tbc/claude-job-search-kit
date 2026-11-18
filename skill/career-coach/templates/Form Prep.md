---
created: {{date}}
tags:
  - career/application
  - type/notes
---
# Form Prep, YYYY-MM-DD <batch name>

One note per batch of applications (up to five, filled in tabs at once). Every question is pulled live with `cc.py questions --ats <ats>:<slug> --id <id>`; a `FLAG transcript required` line means skip the role. **[YOU]** marks the answers only you can give. Standing answers come from [[Standard Answers]], essays from the [[Story Bank]]. Claude writes every answer in full, fills the form in the browser and attaches the resume and cover letter; you read the filled form and click Submit yourself.

## 1. <Company>, <Role> (<City, ST>)
[Apply](https://example.com/jobs/1) | Fit 74 | <pay band if posted> | <onsite, hybrid or remote> | company note [[<Company>]]

**What the job is:** two or three plain sentences from the posting: what you would own, who you would work with.

**Catch:** anything that could sink it: required or preferred years (skip at 3+), a start date before yours, clearance or citizenship lines, travel.

**Resume:** `<exact PDF filename>` from the resume folder. **Cover letter:** `cover_letter_<company>.pdf` (see `references/cover-letter.md`).

| Question | Answer |
|---|---|
| LinkedIn Profile (required) | from Standard Answers |
| Authorized to work in the U.S.? (required) | Yes |
| Sponsorship now or in the future? (required) | No |
| Why <Company>? (required) | Written in full below |
| Salary expectations | **[YOU]**. Default: "Within the posted range" |
| Education | One entry per degree |
| Voluntary EEO questions | Decline to answer |

**Why <Company>?** (written by Claude, checked with `cc.py check --strict --kind answer`; no brackets left)
> What I find interesting about <Company> is <a real, recent thing they did and why it matters, in plain words>. That is the work I want to do: <why that mission>. <ONE bridge from one Story Bank story, ideally touching their domain>. <Close on the team, the office or the place, if true>.

**Other essays:** one Story Bank story per question, no repeats on the same form, each ending with its lesson tied to this company.

## Contacts and order
| Role | First | Second |
|---|---|---|
| <Company> | [[<Hiring manager>]], <title> (hiring manager) | [[<Recruiter or alum>]], <title> |

Touch first, then apply: stage the notes the same day you submit, so the day-3 email can say "I applied and sent you a note on LinkedIn." Claude keeps at most five tabs open and stops before every Send.

## After you submit
Claude checks your inbox for the ATS confirmation ("Thank you for applying") and runs `cc.py applied`, which sets the follow-up dates. No confirmation after a day or two means it did not go through. The day-3 follow-up email is drafted the same day (see `references/apply-loop.md`).
