# claude-job-search-kit

A Claude Code skill that runs a new-grad or early-career job search out of a folder of markdown notes.
It finds companies with fresh signals, sweeps public job boards for new roles, vets and scores them
against your own lanes, names the right people to contact with a source for every name, drafts short
openers, essays and cover letters that only use numbers you have verified, fills application forms in
Chrome up to the Submit button, follows up by email three days after you apply, and measures what gets
replies so each batch is better than the last. Your pipeline and follow-up dates live in your vault.

You click every Submit and every Send. Claude never does.

## What it does

| You say | What happens |
|---|---|
| "what got posted this week" | `cc.py sweep` reads every board in your `ats.tsv` (about 140 public Greenhouse, Lever, Ashby and BambooHR boards ship with the kit), keeps business roles posted in the last 7 days that ask for at most 2 years, and Claude vets and ranks them |
| "find me roles" | Claude finds companies that raised, launched or posted in the last 60 days, pulls their open roles, scores each 0 to 100 and writes one note per company |
| "who should I reach out to at Acme" | warm paths from your LinkedIn export and people notes first, then the hiring manager, a founder, alumni, a recruiter, each with a source URL |
| "draft openers for Jane" | a connection note and a message: your take on one dated thing the company did, one verified fact about you, and "Would you have 10 minutes for a call on X?" |
| "prep the form for this posting" | the live form questions (roles that require a transcript are flagged), answers from Standard Answers, essays written in full from your Story Bank, a cover letter |
| "fill it" | Claude in Chrome fills up to five forms in tabs, attaches resume and cover letter, reads every field back, and stops before Submit |
| "run the apply loop" | `cc.py loop` shows who needs a LinkedIn note first, whose day-3 follow-up email is due, and what applied cold; Claude drafts the emails |
| "I applied to Acme", "sent Jane" | checks your inbox for the confirmation, logs it with the channel, and sets follow-up dates from one cadence table |
| "what's working" | `cc.py metrics`: reply, accept and screen rates by week, channel, person kind, proof point and opener style |
| "what's due" | one list of follow-ups, sorted by date |

The CLI (`scripts/cc.py`) is one stdlib-only Python file. It does every read and write of the vault,
refuses drafts that use unverified numbers or em dashes, refuses people without a source URL, and never
overwrites the fields and sections that belong to you.

## Quick start: paste this into Claude Code

Open a new Claude Code session in any folder and paste the prompt below. Fill in the lines in brackets
first, or delete them and Claude will ask. Claude installs the kit, runs the checks, interviews you to
fill in your config, Fact Sheet, Standard Answers and Story Bank, then takes you through your first
Apply Loop batch. It asks before anything that would send, submit or spend money.

```text
Set up claude-job-search-kit for my job search and take me from zero to my first Apply Loop batch.

About me: [name, school, degree(s), graduation month and year, earliest start date]
What I'm looking for: [role types, industries, cities or regions, and how much of my list should be in my home region]
My notes folder: [path to an Obsidian vault or any folder, e.g. ~/Documents/Job Search]
LinkedIn: [free or Premium / Sales Navigator]

Do it in this order, and stop and show me the result after each step:
1. Clone https://github.com/matis-tbc/claude-job-search-kit into ~/claude-job-search-kit and copy
   skill/career-coach into ~/.claude/skills/career-coach. If that skill folder already exists, ask
   before replacing it.
2. Run `cc.py init --vault-path "<my notes folder>"`, then fill config.toml from what I told you
   above (set [linkedin] premium to match my account). Ask me only for the values you can't fill.
   Show me the finished config.
3. Run `cc.py setup`, `cc.py doctor --net` and `test_cc.py`. Tell me if anything fails.
4. Read the README, skill/career-coach/SKILL.md and references/apply-loop.md so you know the rules:
   you never send or submit anything, no paid tools, numbers about me only from verified Fact Sheet
   rows, a source URL for every person, never guess an email, no em dashes, and you do every step
   yourself except my Submit and Send clicks.
5. Interview me for the Fact Sheet. Ask for my resume (I'll paste it or give you the PDF path),
   then go line by line: one row per number, title and date. Each row starts blocked, and I mark it
   verified or decided. Keep it moving: skip small numbers that will never be printed.
6. Fill Standard Answers with me: contact details, every degree as its own entry, GPA, start date,
   work authorization, sponsorship, relocation, transcript policy, EEO (decline by default) and my
   work history with exact titles and dates.
7. Fill the Story Bank with me: 5 real STAR stories (a sales or persistence story, a failure, a team
   conflict, a crisis, something I built), each with a one-line lesson. Then add one [[proofs]] tag
   per proof point to the config.
8. Ask where my upload-ready resume PDFs are and record their exact file names. If I have TeX
   (tectonic or pdflatex), build one cover letter from the template so I can see the format.
9. Run the first sweep ("what got posted this week"), skip anything that asks for more experience
   than I have or requires a transcript, and give me a ranked shortlist of 5 with one line of
   reasoning each.
10. Run my first Apply Loop batch on the roles I pick: name 1 or 2 people per role (warm paths
   first, then the manager who owns the team), draft and check the LinkedIn notes, write the essays
   and cover letters, fill the forms in Chrome up to Submit if the extension is connected, and draft
   the day-3 follow-up emails into a batch note. I click every Submit and Send and tell you what I sent.
11. Finish by writing the Next Session note, with the date the follow-up emails go out and the date
   to run `cc.py metrics`.
```

After that, use the phrases in the table above. A good second session is "run the apply loop": it
starts from `cc.py loop --due --days 3` and picks up exactly where the last batch left off.

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code)
- Python 3.9 or newer (`python3 --version`). No packages to install.
- A folder for your notes. An [Obsidian](https://obsidian.md) vault works best (wikilinks, Bases
  dashboards), but any plain folder of markdown files works.
- Optional: the [Claude in Chrome](https://claude.ai/chrome) extension, for form filling and LinkedIn
  staging.
- Optional: an email connector (for example Gmail) in Claude, so Claude can find application
  confirmations and replies and put follow-up emails into your drafts. Claude only creates drafts.
- Optional: TeX ([tectonic](https://tectonic-typesetting.github.io) or pdflatex) to build cover letters
  from the template.

## Install

1. **Copy the skill** into your Claude Code skills folder:

   ```bash
   git clone <this repo> ~/claude-job-search-kit      # or download and unzip it
   mkdir -p ~/.claude/skills
   cp -R ~/claude-job-search-kit/skill/career-coach ~/.claude/skills/career-coach
   ```

2. **Create your config.** Point it at your vault (an existing Obsidian vault, or a new empty folder):

   ```bash
   python3 -I ~/.claude/skills/career-coach/scripts/cc.py init --vault-path "$HOME/Documents/Job Search Vault"
   ```

   This writes `~/.config/job-search-kit/config.toml` from `config.example.toml` and never overwrites an
   existing file. Open it and replace every example value: your name, school, degrees, graduation and
   start date, the lanes you are aiming for, your home region and how much of each shortlist should be
   there (`home_region_share`, `0` turns it off), your search phases and dates, whether you have
   LinkedIn Premium (300-character notes, written at 250 to 300) or a free account (200), and one
   `[[proofs]]` tag per proof point you cite, so `cc.py metrics` can tell which ones get replies.

   To keep the config somewhere else, set `JOB_KIT_CONFIG=/path/to/config.toml` or pass `--config`.

3. **Lay out the vault:**

   ```bash
   python3 -I ~/.claude/skills/career-coach/scripts/cc.py setup
   ```

   This creates the folders, copies the templates (Fact Sheet, Standard Answers, Story Bank, Application
   Tracker, Next Session, Connectors, and reference copies of the Company, Person, Form Prep and Apply
   Loop Batch formats plus the cover-letter template) and
   seeds `Data/ats.tsv` with the public job boards. It never overwrites a file, so it is safe to run on
   an existing vault. Every path is set in `[paths]` in the config.

4. **Check it:**

   ```bash
   python3 -I ~/.claude/skills/career-coach/scripts/cc.py doctor        # add --net to probe the board APIs
   python3 -I ~/.claude/skills/career-coach/scripts/test_cc.py          # 46 tests on a temp vault
   ```

5. **Optional: Claude in Chrome.** Install the extension, sign in, and allow it on the job boards and
   LinkedIn. Claude only uses it when you ask in that session. See
   `skill/career-coach/references/browser-apply.md` for what it will and will not do.

6. **Optional: your LinkedIn export.** LinkedIn, Settings, Data privacy, Get a copy of your data,
   Connections. Drop `Connections.csv` into `<job search folder>/Data/`. `cc.py warm` then checks every
   company against your real 1st-degree network.

## First session

Open Claude Code anywhere and say "let's set up my job search". The skill triggers on any job-search
request.

1. **Fact Sheet (20 minutes, the important part).** Claude walks through your resume with you and
   writes one row per number, title and date. Every row starts blocked. You mark it `verified` (a record
   backs it: an offer letter, a results page, a tracker) or `decided` (you picked a value and will
   defend it in an interview). Only those rows can appear in anything Claude writes. Retired numbers
   stay as `blocked` rows so old phrasings keep getting caught.
2. **Standard Answers (5 minutes).** Contact details, school, every degree, GPA, start date, work
   authorization, sponsorship, relocation, transcript policy, the EEO default (decline), and your work
   history with exact titles and dates.
3. **Story Bank (15 minutes).** Five real STAR stories with a one-line lesson each. Claude writes every
   essay from these, a different story per question, so this is what makes applications fast.
4. **Resumes.** Put upload-ready PDFs in the resume folder from your config. Claude recommends only
   those files, by exact name.
5. **First sweep.** Say "what got posted this week". Claude sweeps the boards, skips anything that
   requires or prefers 3+ years, and gives you a ranked shortlist with the reasons.
6. **First Apply Loop batch.** Pick a few roles. Say "run the apply loop on these". For each role Claude
   names 1 or 2 people and drafts their notes, writes the essays and a cover letter, fills the form, and
   drafts the day-3 follow-up email. You read, click Submit and Send, and say "sent Jane". The full
   cycle is in `skill/career-coach/references/apply-loop.md`.
7. **Next time**, start with "where am I", "what's due" or "run the apply loop". Every week, say "what's
   working" for the metrics. Claude reads the Next Session note first and
   rewrites it at the end of long sessions, so nothing depends on an old chat.

Add your own target companies' boards at any time: "add Acme's job board" runs `cc.py jobs` with their
careers page once and caches the board for future sweeps.

## Safety rules

These are enforced in the skill instructions and, where code can enforce them, in `cc.py`:

- **Nothing is sent or submitted by Claude.** No email, no LinkedIn message or connection request, no
  application. Claude fills and stages; you click every Submit and every Send.
- **No paid credits.** No paid enrichment tools, paid email finders or paid APIs. Free web search,
  public job boards and your vault only. If something would cost money, Claude says what and asks.
- **Numbers about you come only from verified Fact Sheet rows.** `cc.py check` refuses any number from a
  conflict, estimate, unconfirmed or blocked row, and `--strict` (used for form answers, essays and
  resume bullets) refuses any number that is not on a verified row at all.
- **Every person needs a source URL.** `cc.py upsert-person` refuses a person without one.
- **Never guess an email address.** An email is refused unless it has a public source URL.
- **No em dashes, no emojis.** Every write refuses em dashes.
- **Your edits are yours.** The script rewrites only its own marked blocks and machine fields; your
  status, next actions, follow-up dates and Notes sections are never overwritten. Folders listed in
  `[paths] protected` are never edited.
- **In the browser**, Claude stops at every login, CAPTCHA, attestation, payment and Submit, never
  presses Enter in a form field, keeps at most 5 tabs open, and never navigates a tab you handed over.

## Layout

```
claude-job-search-kit/
  README.md
  LICENSE
  skill/career-coach/            copy this folder to ~/.claude/skills/career-coach
    SKILL.md                     what Claude reads
    config.example.toml          copied by `cc.py init`
    data/ats.tsv                 seed list of public job boards
    references/                  sourcing, scoring, people, openers, writing rules, apply loop, cover letters,
                                 browser playbook, vault formats
    scripts/cc.py                the CLI (stdlib only)
    scripts/test_cc.py           tests on a temp vault and config
    templates/                   vault notes copied by `cc.py setup`
```

## Limits

- `cc.py` reads Greenhouse, Lever, Ashby and BambooHR boards. Workday, Oracle, Eightfold, Rippling and
  custom career pages are checked by hand or in the browser.
- The sweep's role families are business roles (ops, BD, finance, PM, go-to-market). Engineering roles
  are filtered out by design; edit `FAMILIES` and `EXCLUDE` in `cc.py` if you want them.
- The number checker is good but not context-perfect: a verified number reused for a different claim
  can pass. Read every claim in context before you send it.
- The seed boards lean toward hardware, energy, space, robotics and AI startups. Add your own sectors.
- The non-US location filter and the default phase advice assume a US search; `us_only = false` turns
  the filter off.

## License

MIT. See `LICENSE`.
