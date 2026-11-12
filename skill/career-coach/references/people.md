# People: who to contact, and proof they exist

Goal per company: **2 or 3 people**, each with a source URL, a one-line reason, and the warm path if
there is one. Fewer good names beat more weak ones.

## Who, in priority order

1. **Warm and relevant.** Anyone with a real tie to the user who sits on or near the team: a LinkedIn
   1st-degree connection, a coworker or club member (the labeled folders in `[warm.people_dirs]`), an
   alum from `[warm] alumni`, a contact at an organization the user already works with.
2. **The hiring manager.** The person the open role reports to. Read the posting for the team name
   ("reports to the Head of Business Operations"), then find who holds that title.
3. **A founder**, when the company is under about 100 people. At a Series A, the CEO or COO often *is*
   the hiring manager for ops, BD and special projects.
4. **A recruiter**, last, and only the one who owns that team or early-career hiring.

Warm beats senior. An alum two levels below the VP who will forward the note is worth more than the
VP who will not read it. When the strongest path is an introduction, the target person gets
`via: <connector name>` and the connector is the one the user messages.

## Connectors

`Connectors.md` in the job-search folder lists people who can make intros and what they can reach.
Batch asks to a connector: one message naming 2 to 4 specific people and why, never a vague "do you
know anyone".

## Search recipes (WebSearch; quotes matter; run several in one turn)

WebSearch does not always honor `site:`, and common names collide. Use the company's full name plus a
disambiguator (sector or domain), and run each recipe both with `site:linkedin.com/in` and as
`"<Company full name>" "<title>" LinkedIn`.

- Hiring manager:
  `"<Company>" ("head of business operations" OR "head of operations" OR "chief of staff" OR "VP operations" OR "head of strategy") site:linkedin.com/in`
  `"<Company>" ("head of product" OR "VP product" OR "director of product") site:linkedin.com/in`
  `"<Company>" ("head of partnerships" OR "VP business development" OR "head of BD" OR "head of growth") site:linkedin.com/in`
- Founders: `"<Company>" (founder OR "co-founder" OR CEO OR COO) site:linkedin.com/in`, plus the
  company's About or Team page and the funding press release.
- Alumni, once per entry in `[warm] alumni`: `"<Company>" "<school or club>" site:linkedin.com/in`.
- Recruiter: `"<Company>" ("recruiter" OR "talent acquisition" OR "early career") site:linkedin.com/in`.
- Also strong: `theorg.com/org/<company>` (a public org chart; third-party, so set `verify: true`), the
  posting itself (`cc.py jobs --describe ...` often names who the role reports to), the company blog,
  podcast and conference speaker pages, and funding announcements.

## What counts as a source

A LinkedIn profile URL, a company team page, a press release or article, a conference speaker page. A
search snippet counts only when it shows the person, the company and the title together. If the title
came from somewhere weaker, set `verify: true`; the note then says to confirm before sending.

Never allowed: a name from memory with no URL, a **guessed email address**, a person whose LinkedIn
shows a different current company, anyone under 18.

## LinkedIn connections export

When `Data/Connections.csv` exists (LinkedIn: Settings, Data privacy, Get a copy of your data,
Connections), `cc.py warm` matches every company against the user's real 1st-degree network. A hit
marked "you have messaged" (from an optional `Data/messaged.tsv` with `name`, `messages`, `last`
columns, no message content) is the warmest path there is. The export has no schools, so alumni still
come from search. If the file is missing, say so once per run.

Do not browse LinkedIn logged in as the user unless they ask in that session. When they do, follow
`browser-apply.md#linkedin-staging`: one profile at a time, stop before Send.

## The person JSON

See `vault.md#person-json`. Fields that matter most: `kind` (hiring-manager, founder, exec, recruiter,
alum, connector), `warm` (1st-degree, coworker, club, org-contact, alum, connector-intro, cold, or any
folder label from the config), `via`, `source`, `verify`, and the `opener` block.
