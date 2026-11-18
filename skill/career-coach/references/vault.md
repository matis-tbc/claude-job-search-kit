# Vault layout and note formats

The vault is any folder of markdown files: an Obsidian vault, or a plain folder. Its root and every path
below come from the config (`[paths]`); the defaults are shown. Override the root with `--vault` or
`CAREER_VAULT` (that is how tests run on a temp copy). All writes go through `cc.py`; do not hand-write
company or person notes.

```
<job_search> = Career/Job Search
  Companies/<Company>.md        one note per company (cc.py upsert-company)
  Runs/Run, YYYY-MM-DD <mode>.md   one log per run (cc.py log-run)
  Data/ats.tsv                  job boards for sweep (seeded by cc.py setup, appended by cc.py jobs)
  Data/Connections.csv          optional LinkedIn export (read by cc.py warm)
  Data/messaged.tsv             optional: name, messages, last (no message content)
  Data/Company Follows.csv      optional seed list
  Application Tracker.md        hand-kept table (cc.py import-tracker reads it)
  Standard Answers.md           every repeated form answer
  Story Bank.md                 STAR stories with a lesson line: the source for every essay
  Next Session.md               the handoff note, read first each session
  Connectors.md                 people who can make intros
  Target Companies.md           optional list of companies the user already wants
  Templates/                    the Company, Person, Form Prep and Apply Loop Batch formats, and
                                cover_letter_template.tex
<fact_sheet> = Career/Resume/Fact Sheet.md
<resume_dir> = Career/Resume/Ready to Send   upload-ready PDFs only
<people> = People/<Full Name>.md              career contacts (cc.py upsert-person)
```

People who already have a note in `<people>` or any folder in `[warm.people_dirs]` are never duplicated:
the script adds a `## Career outreach` block to the existing note and leaves the rest alone.

Tags: companies `career/research` + `type/tracker`; people `career/research` + `type/reference`; run logs
`career/research` + `type/log`. If the user has their own tag system, ask before adding new tags.

Optional Obsidian Bases: a `Pipeline.base` over `Companies/` (group by `status`, sort by `fit`) and a
`People.base` over notes tagged `career/research` with an `outreach` property give a dashboard. They are
not required; `cc.py status` and `cc.py due` print the same information.

## Ownership

| Field | Owner | Script behavior |
|---|---|---|
| `fit`, `stage`, `last_round`, `hq`, `home_region`, `best_role`, `roles_open`, `signal`, `signal_date`, `warm`, `lane`, `sector`, `domain`, `updated` | skill | overwritten each run when provided |
| `status`, `priority`, `next_action`, `next_date` | user | set only when empty; `--force-human` only if they asked |
| `outreach`, `last_contact`, `next_touch` (people) | user | set only when empty |
| `channel`, `sent_on`, `accepted_on`, `email_drafted`, `email_on`, `replied_on`, `replied_via`, `proof`, `tier`, `earlier_rounds` (people) | user, via `cc.py mark` | written only by `mark` on the user's say-so; read by `loop` and `metrics` |
| `<!-- cc:x -->` blocks | skill | replaced (signals and people are merged, log is appended) |
| `## Notes` and anything outside blocks | user | never touched |

Company `status`: research, reach-out, contacted, talking, applied, interviewing, offer, closed, parked.
Person `outreach`: not-contacted, drafted, sent, replied, meeting, dormant, closed. `cc.py lint` flags any
other value. When the user says they sent something, run `cc.py mark --person X --outreach sent` (sets
`last_contact`, `next_touch` from the cadence table, and the company `status: contacted` if it was
`research` or `reach-out`). When they say they applied, run `cc.py applied`.

Apply Loop flags on `mark --person X` (`apply-loop.md`): `--channel note|inmail|open-profile|email|text|intro`
(first touch; `sent_on` is set on the first `--outreach sent` of a round and does not move until a new
round), `--accepted` (`accepted_on`, `next_touch` the next day for the message), `--email drafted|sent`
(`email_drafted`, `email_on`; `sent` also sets `last_contact` and `next_touch` 7 days out, and on a person
not yet contacted it counts as the first touch: `outreach: sent`, `channel: email`), `--replied-via
linkedin|email|text|phone` (`replied_via`, `replied_on` if empty, and `outreach: replied`), `--proof <tag>`
(a `[[proofs]]` tag from the config; otherwise `metrics` infers it from the draft matching the channel) and
`--tier 1|2|3`. A new `--outreach sent` after `replied`, `meeting`, `dormant` or `closed` starts a new
round: the old loop dates move to `earlier_rounds` so `loop` and `metrics` see the new send, not the old
reply. Person flags without `--person`, bad dates and multi-line values exit 2 and change nothing.
`cc.py lint` flags a `channel` outside that list.

## Applications block (`cc.py applied`)

Each company note gets a `## Applications` section with a `<!-- cc:applications -->` table, one row per
role and location: `| Role | Applied | Resume | Referral | Follow up | Link |` (empty cells are `-`). A row
is keyed by role and link, so a rerun adds nothing. `applied` also sets `status: applied` (only forward),
`next_action` and `next_date` (applied + 10 days, only while the status is at or before `applied`) and
appends a log line. `cc.py due` merges company `next_date`, person `next_touch` (else `last_contact` + 7
for `sent`) and each row's follow-up date, plus a day-3 item for an application with no referral and no
one in the People block.

## Company JSON (`cc.py upsert-company file.json`)

```json
{
  "name": "Northwind Robotics",
  "domain": "northwind.example",
  "lane": "A",
  "sector": "autonomous construction robotics",
  "stage": "Series B",
  "last_round": "$90M Series B, Sep 2026",
  "hq": "Springfield, IL",
  "home_region": true,
  "fit": 78,
  "best_role": "Program Manager",
  "warm": "cold",
  "why": "Two to five sentences: what they do, why the user fits, the risk.\n\n**Fit 78**: family 22, evidence 18, level 15, stage 15, warm 0, momentum 5, location 3.",
  "signals": [
    {"date": "2026-09-18", "kind": "funding", "what": "Raised a $90M Series B", "url": "https://example.com/news/1"},
    {"date": "2026-10-07", "kind": "posting", "what": "Posted 6 ops and program roles", "url": "https://jobs.ashbyhq.com/northwind"}
  ],
  "roles": [
    {"title": "Program Manager", "url": "https://example.com/jobs/1", "family": "ops", "seniority": "entry",
     "location": "Springfield, IL", "posted": "2026-08-28", "fit": 78, "resume": "Resume_Ops.pdf",
     "why": "owns schedule and deliverables, 0 to 2 years"}
  ],
  "roles_checked": "2026-10-23",
  "people": ["Jane Doe", "John Roe"],
  "openers": "optional markdown summary; the drafts themselves live on the person notes",
  "next_action": "only used when the note is new",
  "log": "scan: added, fit 78"
}
```

Required: `name`. Every signal needs `date` and `url`; give it a `kind` (funding, launch, contract,
posting, news) so the headline picks the strongest recent one, or set `"headline": true`. Omit `roles` to
leave the roles block as it was; pass `"roles": []` to record that nothing matched. `"seeded": true`
marks a stub that still needs research.

## Person JSON (`cc.py upsert-person file.json`)

```json
{
  "name": "Jane Doe",
  "company": "Northwind Robotics",
  "title": "Head of Program Management",
  "kind": "hiring-manager",
  "warm": "cold",
  "via": "Riley Mentor",
  "source": "https://www.linkedin.com/in/example-jane",
  "linkedin": "https://www.linkedin.com/in/example-jane",
  "verify": false,
  "why": "the Program Manager req reports to her team",
  "opener": {
    "hook": "new test site opened",
    "hook_date": "2026-10-15",
    "hook_url": "https://example.com/news/2",
    "note": "<= the config's note limit",
    "message": "<= 120 words",
    "allow": ["$90M", "10"]
  }
}
```

Required: `name`, `company`, `source`. `via` only when the path is an intro. An `email` anywhere is
refused unless `email_source` holds the public URL it came from. `allow` lists sourced company numbers
(and the minutes in the ask) the checker should accept.

## Run log body (`cc.py log-run --mode scan --body-file run.md`)

```markdown
## Asked
<what the user asked, in a line>

## Searches
- <query> (n useful results)

## Kept
| Company | Fit | Signal | Why |

## Dropped
| Company | Reason |

## Skipped roles (vetting)
| Company | Role | Reason |

## Warm paths found
## Home-region share
3 of 10 (30%)

## Open questions for the user
```
