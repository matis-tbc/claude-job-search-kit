# The Apply Loop

One repeatable cycle per role: **touch a real person, apply, follow up by email, record what happened,
learn from the numbers.** Every step is logged with `cc.py`, so any session can pick it up cold and the
rates come from the vault, not memory.

Claude does the work: finds the roles and the people, writes the notes, essays and cover letters, fills
the forms, attaches the files, drafts the emails and logs everything. The user clicks Submit and Send,
and says what they sent or heard. Do not hand the user a to-do list for anything Claude can do itself.

## The loop

```
 find role --> name 1 or 2 people --> LinkedIn touch (day 0)
                                          |
                                          v
                 apply (same day or next) --> confirm in the inbox, cc.py applied
                                          |
             reply on LinkedIn? ----------+-- yes --> answer there, book the 10 minutes --> outcome
                                          |
                                          no, 3 days after BOTH the touch and the application
                                          v
                 follow-up email: "I applied for <role> and sent you a note on LinkedIn"
                                          |
             reply? ----------------------+-- yes --> book the call --> outcome
                                          |
                                          no, 7 days after the email
                                          v
                 second touch: a second person at the company, or one last LinkedIn line
                                          |
                                          no reply 24 days after the first touch --> dormant
                                          v
                 metrics: what got replies, what got screens --> change the next batch
```

Outcomes: `replied`, `meeting`, a screen (company status `interviewing`), or `dormant`.

## Timing (one source: `CADENCE` in cc.py)

| Event | Next step | Days |
|---|---|---|
| LinkedIn note or InMail sent | not accepted: InMail, Open Profile message, or the email | 7 (`note-sent`) |
| Applied, touch already sent, no reply | the follow-up email naming the role | 3 after the later of the two (`applied-email`) |
| Applied with no named person | find and stage one person | 3 (`applied-no-human`) |
| Follow-up email sent, no reply | second contact at the company, or a last LinkedIn line | 7 (`email-sent`) |
| Application, no response | follow up with the contact, naming the req | 10 (`application`) |
| Connection still pending | withdraw it | 14 (`pending-withdraw`) |
| Nothing after all touches | last polite touch, then dormant | 24 (`second-touch`) |

Order matters: touch first, then apply, so the email can say both. If the role is already applied for,
send the note the same day (`cc.py loop` flags this `NOTE FIRST`).

## Runbook (a session can follow this cold)

1. **See the board.** `cc.py loop --due --days 3` lists every person with the next step and its date.
   Flags: `EMAIL DUE` (applied, touch sent, no reply, 3 days passed), `NOTE FIRST` (applied but nobody
   at the company contacted), `APPLIED COLD` (no person named yet). `cc.py due` shows the same flags
   merged with every other follow-up.
2. **Find roles.** `cc.py sweep --days 7`, plus open roles at companies where someone already knows the
   user's name (the highest-odds applications). Vet per `writing-rules.md#vetting`: skip roles that ask
   for more experience than the user has (`max_years` in the config) unless they ask for a stretch. Run
   `cc.py questions` on every form first; a `FLAG transcript required` line means skip it (unless the
   Standard Answers transcript row says otherwise).
3. **Name the people.** Warm paths first (`cc.py warm`), then the manager who owns the team the user
   would join. Executives only through an intro. At most 2 people per company per batch, never the same
   text. Friends get a text in the user's own words, not a LinkedIn draft (`people.md`).
4. **Touch.** Write the note per `openers.md` and `writing-rules.md`, check it with `cc.py check --kind
   note`, and stage it in Chrome per `browser-apply.md` (never press Enter). After the user sends:
   `cc.py mark --person "X" --outreach sent --channel note|inmail|open-profile|email|text|intro`.
5. **Apply.** Claude writes every essay in full from the Story Bank, builds the cover letter
   (`cover-letter.md`), and fills up to five forms in tabs at once from Standard Answers. The user reads
   each and clicks Submit. Claude then checks the inbox for the ATS confirmation and runs
   `cc.py applied --company X --role "Title" --resume <exact PDF> --url <posting>`.
6. **Draft the follow-up email** the day the application goes in (template below), into the batch note
   (`Templates/Apply Loop Batch.md`), and, once a sourced address exists and the user has an email
   connector, into an email draft with the same resume attached: `cc.py mark --person "X" --email drafted`.
   Never guess an address.
7. **Send day** (3 days later): check the inbox and LinkedIn for replies first. Replied: answer there,
   `cc.py mark --person "X" --outreach replied --replied-via linkedin`, and delete the unsent draft with
   the user's OK. No reply: the user sends, then `cc.py mark --person "X" --email sent` (sets the next
   touch 7 days out).
8. **Replies.** Search the inbox (`from:<company domain> newer_than:14d`) and LinkedIn messages each
   session. Log every reply with `--replied-via email|linkedin|text|phone`; accepted connection
   requests with `--accepted`. Reply to a reply in one or two short lines (`writing-rules.md`).
9. **Measure every week.** `cc.py metrics`, and `cc.py metrics --since <batch date>` per batch. Write
   one line of what to change into the next batch note.

## The follow-up email (template)

Aim for under 120 words (`cc.py check --kind email` hard-stops at 160), no em dashes, a first-person take, one proof, one ask.
Attach the resume that went with the application. Subject: a short phrase about their thing, not about
the user.

> Hi {First}, I applied for the {Role} role and {sent you a note | messaged you} on LinkedIn, so I'm
> following up here. {What I find interesting about X is ...: one take of the user's own on something
> real they did, not a restatement of the LinkedIn note.} {One proof from the Fact Sheet that maps to the
> role.} I finish {degree} at {school} in {month}. My resume is attached. Would you have 10 minutes for a
> call on {what the role owns first | how the team hires}?

Rules: no hedges ("seems like", "I'd guess"), no list of facts about their own company, and no offers to
work for less or for equity in writing (save that for a call, if ever).

## What gets measured (`cc.py metrics`)

| Question | Where the data comes from |
|---|---|
| Reply rate overall and by week sent | `outreach`, `sent_on` (else `last_contact` while outreach is still `sent`; older notes past `sent` show as week `undated`), `replied_on` |
| Connection-note acceptance rate | `channel: note` and `accepted_on` (record accepts with `--accepted`) |
| Reply rate by channel: note, InMail, Open Profile, email | `channel`, `replied_via`, `email_on` |
| Reply rate by person kind, warm path and tier | `kind`, `warm`, `tier` |
| Reply rate by proof point and opener style | `proof` (else matched from the sent draft with the config's `[[proofs]]` patterns) and style (`my-take` vs `fact-hook`) |
| Application to screen, with a contact vs cold | Applications blocks (one per company and role, however many locations) plus company status `interviewing` or `offer` |

Read the numbers as direction until a group has 30 or more people. Compare by week sent: a fresh batch
has had less time to reply. Record the channel on every send from day one, or the channel rates have
nothing to work with.

## Person fields the loop adds (all optional, all set by `cc.py mark`)

`channel`, `sent_on`, `accepted_on`, `email_drafted`, `email_on`, `replied_on`, `replied_via`, `proof`,
`tier`, `earlier_rounds`. See `vault.md#ownership`.
