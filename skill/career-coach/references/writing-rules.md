# Writing rules

These apply to every connection note, message, email, form answer, essay, cover letter line
and resume bullet. They came from real feedback on drafts that did not work.

## Format

- **No em dashes**, anywhere. Not in notes, answers, run logs or chat. Use a comma, a period or a colon.
  A spaced en dash counts as an em dash. `cc.py check` and every upsert refuse them.
- No emojis. At most one exclamation point, usually none.
- No "As a ..." openings. No flattery that could be sent to anyone.
- Never: "I hope this message finds you well", "I came across your profile", "passionate", "excited to
  connect", "pick your brain", "leverage", "synergy", "delve", "touch base", "circle back". `cc.py check`
  warns on these.

## End on a concrete ask

Every note, message and email ends with one closing sentence that is easy to say yes to:

- Standard: "Would you have 10 minutes for a call on <something specific to them>?" Good values for X:
  how the team hires for the role, what the role owns first, where a new generalist would help most in
  the team's next year.
- Also fine: "Is there a new grad ops role I should apply to, or someone on your team you'd point me to?"
- Weak: "Open to connecting?", "Would love to connect.", "Let me know if you'd like to chat sometime.",
  a clipped "10 min on X?", coffee offers, "happy to meet", a sign-off line after the ask.

Exactly one ask per draft, and it is the last sentence. `cc.py check` warns when a note, message or
email does not end on a question. A time ask ("10 minutes") is not read as a claim about the user.

## Outreach messages: what goes in

The rules for every connection note, InMail, LinkedIn message and email:

- **Open with a first-person take, not a list of facts.** "What I find interesting about X is ...",
  "To me, the hard part of X is ...". Never explain the recipient's own company to them: they know
  their launch better than you do. Dig past the press release for the take.
- **No hedges and no filler.** No "seems like", "looks like", "reads like", "I'd guess", "must be" about
  facts (`cc.py check` warns on these). Cut lines that carry no information: a standalone "congrats on
  the round" opener, trivia about the person's background ("I saw you did your PhD on X"), school or
  program details nobody asked for.
- **One proof** from the Fact Sheet that maps to the role. Lead with scale and relevance (below).
- **One ask**, as above.
- **Length:** connection notes run to the config's limit: 250 to 300 characters with Premium (150 to
  200 free) so the ask is a full sentence; `cc.py check --kind note` warns when a note is short.
  Messages aim for 60 to 90 words; follow-up emails stay under 120.
- **Subject lines** are a short phrase about their thing ("Selling to utilities twice"), never "from a
  State University senior". "Fellow <school> grad, <company> question" only for real alumni.
- **When the user admires the person**, build the message on that person's path and ask to learn how
  they work. It is worth 10 minutes to them even with no job at stake; do not say so.
- **Never offer to work for less, or for equity, in writing.** If it ever comes up, it is for a call.
- **Confidential or over-specific details:** say the count, not the names ("built pitch decks for 3
  new markets", not the list of cities). Keep the names on the Fact Sheet for an interview.

## Who gets which message

- **Warm paths first**, every batch: 1st-degree connections, alumni, coworkers, connectors.
- **Target the manager who owns the team** the user would join (the BD or partnerships manager, the
  head of business operations, a chief of staff). A founder only at a company under about 50 people.
  VPs and C-suite only through an intro. At most 2 people per company per batch, never the same text.
- **Friends get a text in the user's own words, not a LinkedIn draft.** A 1st-degree connection is not
  automatically a friend: ask the user which ones they actually know before drafting. At a company
  where a friend works, hold cold notes there until the friend answers.
- **Day 3 after applying**, with a LinkedIn touch already sent and no reply, the follow-up email opens
  "I applied for <role> and sent you a note on LinkedIn" and adds a new take, one proof, the resume and
  the same ask. Template: `apply-loop.md`.

## Replying to a reply

One or two short lines. Answer their question, add the one detail that prevents a misread, and if the
first message already asked for a call, close with a soft open door instead of asking again.

## Paste-ready text

Anything the user will paste (a text message, a LinkedIn reply, a short email) goes in chat as plain
lines: no `-` bullets, no `>` quote bars, no markdown, paste text first and commentary after. Emails go
into an email draft when the user has a connector (To left empty unless the address is sourced). Once
the user says they are editing a draft themselves, stop updating it and give replacement text instead.
When offering meeting times, check the user's calendar for real gaps and convert to the other person's
time zone.

## Lead with your strongest credential, in plain words

For BD, sales and partnerships outreach, the first line about the user should show scale and relevance
at once: the role, how long, and the outcome ("I ran sponsorships for our robotics club for 2+ years
and closed 12 corporate sponsors"). Do not lead with one narrow artifact ("I built a strategy deck
for..."). It undersells. Then one short line on why this person, then the ask.

Keep durations accurate to the Fact Sheet's titles and dates.

## Outcome numbers, not activity counts

Numbers should show what the work changed or how big it is in use: users, records, sponsors closed,
budget, results, rank. Drop activity counts: commits shipped, letters sent, calls made, hours logged,
messages answered, trade counts. They read as vanity.

- When a bullet has one unverified number, **drop the number and keep the bullet**. Do not cut the
  whole entry.
- Never state a claim stronger than its Fact Sheet row: "grew the budget to" is not "raised"; "to a
  test server" is not "shipped to production"; template-based drafting is not "AI drafting".
- Every number about the user traces to a `verified` or `decided` row about the same thing. A number
  that appears on the Fact Sheet in a different context is still wrong. The checker catches most of
  these; read each claim in context too.

## Why-us answers

For "Why do you want to work here?", "Why are you interested in X?" and cover-letter openers:

1. Answer the why. Lead with genuine admiration for what the company is doing and why it matters.
2. Say why that mission is the work the user wants to do.
3. ONE bridge from the user's own experience, best when it touches the company's domain.
4. Close on fit or place (the home region, a city they want), if true.

No fact lists and no stat dumps: at most one number about the user. Opinions about the company are
fine; claims about the user still come from the Fact Sheet. Never invent personal history ("I've
followed X since I was a kid") the user did not give you.

## Essays and short answers

Claude writes every essay and short answer in full. No brackets, no blanks, even when the form says
"in your own words": the user reads the finished answer before Submit and edits if they want.

- Source every answer from the **Story Bank** (and the Fact Sheet for numbers).
- Use a **different story for each question** on the same form. Reusing the one big story everywhere
  reads thin.
- End each answer with the story's **lesson, tied to the company's work** ("That is the same problem
  your field team has when ...").
- Respect the word limit; run each answer through `cc.py check --strict --kind answer`.
- If the Story Bank has no real story for a question, say so and ask; never invent one.

## Vetting

Do not draft a full packet for a role the user is unlikely to get. Skip, and record the reason, when:

- the **required or preferred** experience is **3+ years** (a "preferred 4+ years" line counts even if
  the minimum is only a degree),
- the role is mid-level or senior by its own description,
- it must start well before the user's configured start date,
- it needs a clearance or citizenship the user does not have,
- the form requires a transcript upload (the default; the Standard Answers transcript row can change it).

Keep: new grad, early career, 0 to 2 years, or explicit graduating-class programs. If the user asks for
a stretch, do it and say what the stretch is. A skipped role can still be worth a note to the person
who owns the work.

## Resumes

- Upload only from the upload-ready folder (`[paths] resume_dir`), by exact filename. A file with any
  unconfirmed fact does not go there.
- Fill one full page. Tailor by swapping 1 or 2 bullets to match the posting's lines.
- Put the website or portfolio link in the header of every resume and cover letter.
- TeX-built resumes: break the "ff" ligature and check the text layer (`cover-letter.md`).

## Voice

Read the `voice_samples` in the config. Match them: contractions, plain words, short sentences, second
person. Start with "Hi <first name>," (or "Hey" for a peer, an alum or someone the user has met).

## Before you hand a draft over

Read it as the recipient. Would they know in the first line why this is to *them*? Is there exactly one
concrete ask? Could it be sent to a different company with the name swapped? If yes, rewrite the hook.
