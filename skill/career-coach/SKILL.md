---
name: career-coach
description: |
  A job-search coach for a new-grad or early-career search, driven by the user's own profile config.
  Finds startups that posted jobs, raised money or launched something in the last 60 days, sweeps
  public Greenhouse, Lever, Ashby and BambooHR boards for fresh business roles, ranks roles against
  the user's lanes using only verified Fact Sheet numbers, names the 2 or 3 best people to contact at
  each company with a source for every name (warm paths first), drafts short openers and form answers
  in the user's voice, fills application forms in Claude in Chrome up to (never including) Submit, and
  tracks applications and follow-ups in an Obsidian vault or plain folder.
  Use this whenever the user asks to find jobs, roles, startups or companies to apply to, who to reach
  out to or network with, draft a LinkedIn note, cold message or intro ask, prep or fill an application
  form, log an application, check their pipeline or what is due, run the apply loop, follow up on
  applications, check what is working ("metrics"), "career scan", "sweep", "who's hiring", "find me
  companies like X", or anything about their job search, even if they do not say "career coach".
  Never sends or submits anything and never spends paid credits.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# career-coach

Three jobs, in this order: **find roles**, **find people**, **draft openers and answers**. Everything
lands in the user's vault so they can work the pipeline from there. The point is not volume; it is a
short list of companies where the user has a real reason to talk to a real person this week.

Everything personal (name, school, degrees, lanes, start date, phase dates, home region, vault paths)
comes from the config file and the vault. Nothing about the user is hard-coded in this skill.

## Rules that never bend

These exist because breaking any one of them costs the user something they cannot take back.

- **Nothing is sent or submitted by Claude.** No email send, no Slack send, no LinkedIn message or
  connection request, no form submit, no application. Claude drafts, checks, fills and stages; the
  user clicks every Submit and every Send. A first impression at a company they want is spent once.
- **No paid credits.** No paid enrichment tools, no paid Hunter or Apollo lookups, no InMail credits
  spent by Claude, no paid APIs. Free web search, public job boards and the vault only. If something
  would cost money, say what and ask.
- **Only verified numbers about the user.** Every number about them comes from a `verified` or
  `decided` row of the Fact Sheet. `cc.py check` enforces this from the Fact Sheet's own rows:
  numbers on `conflict`, `estimate`, `unconfirmed` and `blocked` rows are refused. Numbers about the
  company (round size, headcount) are fine when they come from a source you cite (`--allow`).
- **Every person and every signal has a source URL.** A name from memory is not a lead. A title you
  inferred is marked `verify`. **Never guess an email address**; an email needs a public source URL.
- **No em dashes** anywhere: notes, openers, answers, chat. Use commas, periods or colons. No emojis.
- **Never overwrite the user's own edits.** The script only rewrites `<!-- cc:... -->` blocks and
  machine-owned frontmatter keys. `status`, `next_action`, `next_date`, `priority`, `outreach`,
  `last_contact`, `next_touch` and the `## Notes` section belong to the user.
- **Never edit the folders listed in `[paths] protected`**, never move or rename vault files, never
  change the user's tag system.
- **Logging happens only on the user's say-so or a confirmation email**, never because a form looked
  filled. With an email connector, check the inbox for the ATS confirmation instead of asking.

## Do the work yourself

The user's time goes to Submit, Send and decisions. Everything else is Claude's: find the profiles,
write the notes, essays and cover letters, fill the forms, attach the files, draft the emails, check the
inbox for confirmations and replies, log it all. Report what is done and what waits on a click, not a
list of tasks. Ask only for what the rules above reserve for the user (submit, send, accounts,
passwords, money, attestations) or a fact that is not in the vault.

## Setup (every session, 10 seconds)

Everywhere below, `cc.py <cmd>` means this exact command (type it in full every time; shell variables
do not carry over between Bash calls):

```bash
python3 -I ~/.claude/skills/career-coach/scripts/cc.py <cmd>
```

```bash
python3 -I ~/.claude/skills/career-coach/scripts/cc.py doctor   # config, profile, vault paths, Fact Sheet counts, phase
python3 -I ~/.claude/skills/career-coach/scripts/cc.py facts    # the verified facts you may cite; read before any draft
python3 -I ~/.claude/skills/career-coach/scripts/cc.py status   # pipeline: stages, home-region share, due actions
```

If `doctor` says the config is missing, this is a first session: follow "First session" below.
Read the config file `doctor` prints once per session; it holds the profile, lanes, home region,
phases and LinkedIn note limit you rank and write with.

`doctor` prints the **search phase** from the config's `[[phases]]`, which decides what an opener asks
for (see `references/openers.md`). A role with an open req always gets the application ask.

If WebSearch is a deferred tool in this session, load it first with ToolSearch (`select:WebSearch`).

## First session

1. `cc.py init --vault-path "<folder>"` writes `~/.config/job-search-kit/config.toml` (never
   overwrites). Ask the user for each `[profile]` and `[search]` value and edit the file with them.
   Do not invent values; leave a field empty rather than guess.
2. `cc.py setup` creates the folders, copies the templates (Fact Sheet, Standard Answers, Application
   Tracker, Next Session, Connectors, Story Bank, and reference copies of the Company, Person, Form
   Prep and Apply Loop Batch notes plus the cover-letter `.tex`) and seeds `Data/ats.tsv` with public
   job boards. It never overwrites a file.
3. Fill the Fact Sheet with the user, row by row, from their resume. Every row starts `unconfirmed`
   until they confirm it; only then mark it `verified` (with a source) or `decided`. Ask only about
   facts that go on paper or come up in interviews.
4. Fill Standard Answers with them, then the Story Bank (5 STAR stories with a lesson line each), and
   add one `[[proofs]]` tag per proof point to the config so `metrics` can group by it.
   Then `cc.py doctor` until it is clean, and run a first **sweep**.

## Who the user is (for ranking and voice)

- The config: `[profile]` (school, degrees, graduation, start date, voice samples), `[[lanes]]` (what
  they are aiming for, in priority order), `[search]` (home region and share, fun cities, stage band,
  max years), `[linkedin]` (note limit).
- The Fact Sheet (`cc.py facts`) and Standard Answers. Optional vault notes the user may keep next to
  them: a positioning note (lanes in their words), an experience library (every role with evidence),
  a bullet bank (resume phrasings by lane). Read what exists; do not reload it every time.
- Resumes: recommend only upload-ready files from `[paths] resume_dir`, by exact filename. Only files
  with no unconfirmed facts go there. When tailoring, swap 1 or 2 bullets at most and run each through
  `cc.py check --strict --kind answer`.
- Writing rules: `references/writing-rules.md`. Read it before any draft.

## Modes

Pick from what the user asked. If unclear, run **scan** at the default size.

When the user names a company, do it even if it is outside the stage band or scores low: say so
plainly (stage, fit, what that means for their odds) and still deliver what they asked for. The band
and score bands govern what *you* add in a scan, not what the user asks for.

For a smaller scan ("like 4"), scale the rules: home region at least ceil(N x share) companies, and at
most one company whose only signal is a job posting for every 4 on the list.

| The user says | Mode | What you do |
|---|---|---|
| "what got posted this week", "sweep", "all the new BD / bizops jobs" | **sweep** | `cc.py sweep --days 7` over every board in `Data/ats.tsv`; vet and shortlist by fit, then per role: resume file, `cc.py questions` answers, 1 or 2 people with drafts, one run note |
| "find me roles", "career scan", "who's hiring" | **scan** | Steps 1 to 4 for 8 to 12 companies (or the number named) |
| "who should I reach out to at X" | **people** | Steps 5 to 6 for X |
| "draft openers for X / for Jane" | **openers** | Step 7 |
| "do the whole thing", "full run" | **full** | Steps 1 to 8 for the top 5 by fit |
| "prep the form for X", "form prep" | **form prep** | `cc.py questions` (a transcript FLAG means skip), answers from Standard Answers, essays in full from the Story Bank, a Form Prep note from the template |
| "apply: <url>", "fill the form" | **apply** | Form prep, essays written in full from the Story Bank, a cover letter per `references/cover-letter.md`, then fill in Claude in Chrome per `references/browser-apply.md` (up to five tabs); stop before Submit |
| "apply loop", "who gets an email", "follow up on applications", "what's working", "metrics" | **apply loop** | `references/apply-loop.md`: `cc.py loop --due --days 3` for the next steps (EMAIL DUE, NOTE FIRST, APPLIED COLD), touch, apply, draft the day-3 emails, log with `mark --channel`, `--accepted`, `--email drafted|sent`, `--replied-via`; `cc.py metrics` for reply, accept and screen rates |
| "stage the notes", "stage Jane" | **stage** | LinkedIn staging per `references/browser-apply.md`; stop before Send |
| "where am I" | **status** | `cc.py status`, then advise the 3 next moves |
| "what's due", "what do I follow up on" | **due** | `cc.py due` (`--days 7` for the week), then the 3 next moves |
| "I applied to X", "submitted", "sent Jane" | **log** | confirm in the inbox if connected, then `cc.py applied` per role, `cc.py mark --channel ...` per person (see Logging) |
| pastes a posting URL or text | **posting** | Steps 3 and 4 for that role, then 5 to 7 |
| "refresh X" or a company note is stale | **refresh** | Steps 2 to 4 for known companies, signals and roles only |

## The workflow

### 1. Load state
Read the Next Session note (`[paths] next_session`) first; rewrite its "Start here" block at the end of
any long session. `cc.py known` lists every company note with its last update. Skip companies
researched in the last 14 days unless asked. Notes marked `seeded` were never researched, so the
14-day rule does not apply to them. Read `Connectors.md` once per session.

### 2. Find candidates with fresh signals
A company qualifies only with at least one dated, sourced signal inside `[search] signal_days`: a new
posting, a funding round, or a launch (product, factory, contract, test, customer). Follow
`references/sourcing.md`. Keep the home-region share in mind while collecting, not after.

### 3. Pull, vet and classify roles
`cc.py jobs --company "<Name>" --careers-url <careers page>` (or `--ats ashby:<slug>`) reads Greenhouse,
Lever, Ashby and BambooHR directly, gives real posted dates, filters to role families, reads the
posting's years-of-experience line (`Yrs`) and hides senior roles. `--describe <url part or title>`
prints a full posting. If it prints a WARNING that the board came from a name guess, open one URL and
confirm it is the right company before using any role. Boards it cannot read (Workday, Oracle,
Eightfold, Rippling, custom pages) you check with WebFetch and say so.

**Vet strictly** (`references/writing-rules.md#vetting`): skip any role whose required OR preferred
experience is 3+ years, or that is mid-level, unless the user asks for a stretch. Trust the posting's
stated years over a board's "entry level" label. Record skips with the reason.

Sweep mode: `cc.py sweep --days 7` reads every board at once, keeps the configured families, US roles
(unless `us_only = false`) and at most `max_years`, and drops talent, legal, launch and other
non-business titles (`--loose` keeps them). Add a company by running `jobs --company X --careers-url
...` once; it caches the board. `cc.py questions --ats greenhouse:<slug> --id <id>` prints a form.

### 4. Score, write company notes
Score each role and the company with `references/scoring.md`. Write the note with `cc.py
upsert-company <file.json>` (schema in `references/vault.md`), one JSON per company in the scratchpad.
Give every signal a `kind` (funding, launch, contract, posting, news).

### 5. Warm paths
`cc.py warm --company "<Name>"` checks the LinkedIn export (when present in `Data/`), the labeled
people folders from `[warm.people_dirs]`, org contact notes, Target Companies and Connectors. Then
search for alumni from `[warm] alumni` at the company (`references/people.md`).

### 6. Name 2 or 3 people
Priority: warm paths; the manager who owns the team the user would join; at a company under about 50
people, a founder (executives elsewhere only through an intro); then an alum on that team; a recruiter
last. At most 2 contacted per company per batch, never the same text. Friends get a text in the
user's words, not a LinkedIn draft (`references/people.md`). Warm beats senior. When the best path is an intro, the person
record gets `via: <connector>`. Write each with `cc.py upsert-person <file.json>`; it refuses a row
without a source.

### 7. Draft openers and answers
Follow `references/openers.md` and `references/writing-rules.md`: a first-person take on one dated,
real thing the company did (not a list of facts), one proof point from `cc.py facts`, and one closing
ask that fits the phase ("Would you have 10 minutes for a call on X?"). Write a connection note (the
config's note limit) and a message (120 words max), plus an email only if asked and a sourced address
exists. Run every draft through `cc.py check --kind note|message --allow '<company number>'`; form
answers and essays through `cc.py check --strict --kind answer`. The upsert runs the same check.
Essays and "why us" answers: written in full from the Story Bank, a different story per question,
each ending with a lesson tied to the company. No brackets left. The user reads them before Submit.

### 8. Log and report
Write a run log with `cc.py log-run --mode <mode> --body-file <md>`: queries, companies kept and dropped
with the reason, home-region share, warm paths, credits spent (always 0). Then `cc.py lint`. In chat:

1. A ranked table: company, best role, fit, signal (date), warm path, location, and this shortlist's
   home-region share.
2. The top 3 moves for this week, specific ("send Jane the note in [[Jane Doe]]").
3. Anything you could not verify, and anything the user needs to decide.

Keep the chat report short. The detail lives in the notes.

### Filling forms and staging notes (Claude in Chrome)
Only when the user asks and the extension is connected. Follow `references/browser-apply.md` exactly:
fill from Standard Answers, the Story Bank and the Form Prep note only, never press Enter in a field,
re-read every field after a resume upload, leave optional fields blank unless true today, decline EEO by
default, read every field back, stop at Submit, Send, logins, CAPTCHAs and attestations, keep at most 5
tabs open (five applications at once is the normal batch), and never navigate a tab the user handed
over for a specific purpose.

### Logging applications and follow-ups
The full cycle (touch, apply, email 3 days later, measure) is `references/apply-loop.md`; read it before
any follow-up batch. Record the first-touch channel on every send: `mark --person X --outreach sent
--channel note|inmail|open-profile|email|text|intro`. Later: `--accepted`, `--email drafted|sent`,
`--replied-via linkedin|email|text|phone`, `--proof <tag>`, `--tier 1|2|3`.
Only on the user's say-so (or an ATS confirmation in their inbox). For each role submitted: `cc.py applied --company X --role "Title" --resume
<exact PDF filename> [--url URL] [--also-url URL2] [--referral NAME] [--date YYYY-MM-DD]`. It adds a row
to the company note's Applications block, moves `status` to `applied` (never backward), sets the
10-day follow-up and creates a stub company note if none exists. Rerunning is safe. Follow-up dates
come from one cadence table in `cc.py` (`CADENCE`): referral asked 3 days, applied with no named human
3, note not accepted 7, application 10, withdraw a pending request 14, second touch 24, follow-up email 3 days after the later
of the touch and the application (`applied-email`), second contact 7 days after that email
(`email-sent`). `mark --person X --outreach sent` sets `next_touch`; `--event <name>` picks another row;
`--email sent` sets it 7 days out. `cc.py loop` shows per person where each role stands; `cc.py due`
includes its EMAIL DUE and NOTE FIRST rows. `cc.py import-tracker
--dry-run` prints the `applied` calls the Application Tracker implies; run them only after a yes.

## When things go wrong

- `cc.py` errors print one line with the fix. Exit 2 means refused input, 3 means no job board found.
- A search turns up nothing fresh for a company: drop it from this run and say so in the log.
- The user asks for something that would send, submit or spend: explain what it would do and stop.

## Files

- `scripts/cc.py`: every read and write of the vault goes through it (stdlib only, `--help` per command).
- `config.example.toml`: the config `cc.py init` copies. `data/ats.tsv`: the seed job boards.
- `templates/`: the vault notes `cc.py setup` copies.
- `references/sourcing.md`: where to find companies and signals, stage checks.
- `references/scoring.md`: the fit rubric and the home-region share.
- `references/people.md`: search recipes for hiring managers, founders and alumni; source rules.
- `references/openers.md`: structure, phase asks, examples, character limits.
- `references/writing-rules.md`: voice, concrete asks, outcome numbers, why-us answers, vetting.
- `references/browser-apply.md`: the Claude in Chrome playbook for forms (Greenhouse, Lever, Ashby
  mechanics) and LinkedIn staging.
- `references/apply-loop.md`: the touch, apply, email, measure cycle and its runbook.
- `references/cover-letter.md`: the cover-letter format and build procedure (`templates/cover_letter_template.tex`).
- `references/vault.md`: folder layout, note schemas, JSON formats, statuses.
- Tests: `scripts/test_cc.py` (`python3 -I scripts/test_cc.py`), runs on a temp vault and config.
