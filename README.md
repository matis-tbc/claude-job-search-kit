# claude-job-search-kit

A Claude Code skill that runs a new-grad or early-career job search out of a folder of markdown notes.
It sweeps public job boards for fresh roles, finds the right people to contact (with a source for every
name), drafts short openers, essays and cover letters that only use numbers you have verified, fills
application forms in Chrome up to the Submit button, drafts follow-up emails three days after you
apply, and measures what gets replies.

**You click every Submit and every Send. Claude never does.**

## What Claude does, and what it never does

| Claude does on its own | Claude never does |
|---|---|
| Sweeps public job boards and reads careers pages | Sends an email, LinkedIn note, InMail or message |
| Researches companies and people, with a source URL for each | Submits an application or clicks Submit |
| Drafts notes, emails, essays, cover letters and form answers | Spends money: paid tools, paid email finders, InMail credits |
| Fills forms in Chrome and attaches your files, then stops | Guesses an email address or invents a number about you |
| Puts follow-up emails into your email drafts (if connected) | Logs a send or an application you have not confirmed |
| Reads and writes notes in your vault | Edits your own fields, Notes sections or protected folders |

It stops and hands control to you at every login, CAPTCHA, attestation, payment and Submit.

## Prerequisites

| Need | Required? | Why |
|---|---|---|
| [Claude Code](https://docs.claude.com/en/docs/claude-code) | Required | Runs the skill |
| Python 3.9 or newer (`python3 --version`) | Required | Runs `cc.py`. No packages to install. macOS ships 3.9 |
| A notes folder | Required | Any folder of markdown files. [Obsidian](https://obsidian.md) is optional but nicer (links, dashboards) |
| [Claude in Chrome](https://claude.ai/chrome) extension | Optional | Form filling and LinkedIn staging. Without it, Claude gives you answers to paste |
| An email connector in Claude (for example Gmail) | Optional | Finds application confirmations and replies, writes follow-up drafts. Drafts only |
| TeX (`tectonic` or `pdflatex`) | Optional | Builds cover letter PDFs from the template |

## Quickstart (10 minutes)

**1. Install the skill** (2 minutes):

```bash
git clone https://github.com/matis-tbc/claude-job-search-kit ~/claude-job-search-kit
mkdir -p ~/.claude/skills
cp -R ~/claude-job-search-kit/skill/career-coach ~/.claude/skills/career-coach
alias cc='python3 -I ~/.claude/skills/career-coach/scripts/cc.py'   # optional shortcut for this README
```

Without the alias, `cc` below means `python3 -I ~/.claude/skills/career-coach/scripts/cc.py`.

**2. Create your config and vault** (3 minutes). Use an existing Obsidian vault or a new folder:

```bash
cc init --vault-path "$HOME/Documents/Job Search Vault"   # writes ~/.config/job-search-kit/config.toml
cc setup                                                  # creates the folder, notes and job board list
```

Neither command overwrites a file that exists, so both are safe on an existing vault.

**3. Edit the config** (4 minutes). Open `~/.config/job-search-kit/config.toml` and replace every example
value. See [Fill in your profile](#fill-in-your-profile) below.

**4. Check it** (1 minute):

```bash
cc doctor          # every line should read ok or todo; add --net to test the job board APIs
python3 -I ~/.claude/skills/career-coach/scripts/test_cc.py   # the test suite on a temp vault
```

**5. Start.** Open Claude Code in any folder and say **"let's set up my job search"**. Claude reads your
config, interviews you for the Fact Sheet, Standard Answers and Story Bank, and runs your first sweep.

<details>
<summary>Or let Claude do all of it: paste this prompt into a new Claude Code session</summary>

Fill in the bracketed lines first, or delete them and Claude will ask.

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

</details>

## Fill in your profile

Four things make the output yours. Claude interviews you for the last three; you can also edit the notes
by hand. All paths are inside your vault and set in `[paths]` in the config.

| What | Where | What goes in it | Time |
|---|---|---|---|
| Config | `~/.config/job-search-kit/config.toml` | `[profile]` name, school, degrees, graduation, start date. `[search]` home region and its share of each shortlist (`0` turns it off), role families, max years. `[[lanes]]` the kinds of roles you want. `[[phases]]` your search calendar. `[linkedin] premium` (300-character notes) or free (200). `[[proofs]]` one tag per proof point you cite | 5 min |
| Fact Sheet | `Career/Resume/Fact Sheet.md` | One row per number, title and date on your resume. Every row starts blocked. Mark it `verified` (a record backs it) or `decided` (you will defend it in an interview). Only those rows can appear in anything Claude writes | 20 min |
| Standard Answers | `Career/Job Search/Standard Answers.md` | Contact details, each degree, GPA, start date, work authorization, sponsorship, relocation, transcript policy, EEO (decline by default), work history with exact titles and dates | 5 min |
| Story Bank | `Career/Job Search/Story Bank.md` | Five real STAR stories, each with a one-line lesson. Every essay is written from these, a different story per question | 15 min |

Also put your upload-ready resume PDFs in `Career/Resume/Ready to Send/`. Claude recommends only those
files, by exact name. Optional: drop LinkedIn's `Connections.csv` export (Settings, Data privacy, Get a
copy of your data, Connections) into `Career/Job Search/Data/` so warm paths use your real network.

## The daily loop

Say these to Claude. The CLI line is what Claude runs, or what you can run yourself.

| Step | You say | What happens | CLI |
|---|---|---|---|
| 1. What's due | "what's due" or "run the apply loop" | Follow-ups due today: whose day-3 email is due, who needs a LinkedIn note first, what you applied to cold | `cc loop --due --days 3`, `cc due` |
| 2. Find roles | "what got posted this week" | Sweeps about 140 public boards for business roles posted in the last 7 days asking for at most 2 years, then vets and ranks them | `cc sweep` |
| 3. Find people | "who should I reach out to at Acme" | Warm paths first, then the manager who owns the team, each with a source URL | `cc warm --company Acme` |
| 4. Draft | "draft openers for Jane" | A connection note and a message: your take on one dated thing the company did, one verified fact, and "Would you have 10 minutes for a call on X?" | `cc check --kind note` |
| 5. Apply | "prep the form", then "fill it" | Live form questions (transcript-required roles flagged), answers, essays, cover letter; Chrome fills up to 5 tabs and stops before Submit | `cc questions` |
| 6. Log | "sent Jane a note", "I applied to Acme" | Records the send, the channel and the application, checks your inbox for the confirmation, sets follow-up dates | `cc mark`, `cc applied` |
| 7. Weekly | "what's working" | Reply, accept and screen rates by week, channel, person kind, proof point and opener style | `cc metrics` |

Logging by hand, if you prefer:

```bash
cc mark --person "Jane Doe" --outreach sent --channel note       # sent a connection note today
cc mark --person "Jane Doe" --accepted                           # she accepted
cc applied --company "Acme" --role "BizOps Associate" --resume "Resume.pdf"
cc mark --person "Jane Doe" --email sent                         # sent the day-3 follow-up email
cc mark --person "Jane Doe" --outreach replied --replied-via email
```

The full cycle, with timings and the email template, is in `skill/career-coach/references/apply-loop.md`.
Claude writes a Next Session note at the end of long sessions, so the next session starts from your
vault, not from an old chat.

## Privacy

- **Everything stays local.** Your config lives in `~/.config/job-search-kit/`, your notes in your
  vault. Nothing in this repo holds your data, and `.gitignore` blocks `config.toml`,
  `Connections.csv` and `messaged.tsv` in case you work inside the clone.
- **Network calls** from `cc.py` go only to public job board APIs (Greenhouse, Lever, Ashby, BambooHR)
  and careers pages you point it at. No telemetry, no accounts, no API keys.
- **Claude sees what you share in a session**, as with any Claude Code use: your resume, notes and
  form pages. Leave out anything you would not paste into Claude.
- **Do not publish your vault.** It holds your contacts, drafts, Standard Answers (contact details,
  work authorization) and your LinkedIn export with your connections' names.
- **Transcripts:** by default Claude skips roles that require one and leaves optional transcript
  uploads blank.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `no config at ...` | Run `cc init --vault-path "<folder>"`, or set `JOB_KIT_CONFIG=/path/to/config.toml` |
| `vault not found at ...` | Run `cc setup` (it creates the folder), or fix `[paths] vault` in the config |
| `config ... could not be read` on Python 3.9 or 3.10 | The fallback parser reads a subset of TOML: keep arrays on one line and quote every string |
| `doctor` shows `todo profile` | `[profile] name` is still the example. Replace every example value in the config |
| `check` refuses a number about you | Mark its Fact Sheet row `verified` or `decided`, or drop the number. Company numbers you cite: `--allow '$140M'` |
| `sweep` finds nothing | Run `cc doctor --net` to test the board APIs; try `cc sweep --days 30`; add your own boards with "add Acme's job board" |
| The skill does not trigger | Check `~/.claude/skills/career-coach/SKILL.md` exists, restart Claude Code, then say "career coach" |
| Claude cannot fill forms | Install Claude in Chrome, sign in, connect it to Claude Code and allow it on the job board sites |
| `metrics` is all zeros | Nothing is logged yet. Log sends with `cc mark --person ... --outreach sent --channel note` |
| `mark` changed nothing | Person fields (`--channel`, `--email`, `--tier` ...) need `--person`; company changes need `--company` and `--status` |

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
- The sweep keeps business roles (ops, BD, finance, PM, go-to-market). Engineering roles are filtered
  out by design; edit `FAMILIES` and `EXCLUDE` in `cc.py` if you want them.
- The number checker is good but not context-perfect: a verified number reused for a different claim
  can pass. Read every claim in context before you send it.
- The seed boards lean toward hardware, energy, space, robotics and AI startups. Add your own sectors.
- The non-US location filter and the default phase advice assume a US search; `us_only = false` turns
  the filter off.

## License

MIT. See `LICENSE`.
