# Writing rules

These apply to every connection note, message, email, form answer, essay skeleton, cover letter line
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

Every note and message ends with one thing that is easy to answer, ideally a short call or a specific
question:

- Good: "Would you have 10 minutes for a quick call this week or next?"
- Good: "Is there a new grad ops role I should apply to, or someone on your team you'd point me to?"
- Weak: "Open to connecting?", "Would love to connect.", "Let me know if you'd like to chat sometime."

Exactly one ask per draft. A number in the ask (10 minutes) is not about the user, so pass
`--allow '10'` to `cc.py check`.

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
followed X since I was a kid") the user did not give you. Write a skeleton with bracketed slots and
let the user put the motivation lines in their own words.

## Vetting

Do not draft a full packet for a role the user is unlikely to get. Skip, and record the reason, when:

- the **required or preferred** experience is **3+ years** (a "preferred 4+ years" line counts even if
  the minimum is only a degree),
- the role is mid-level or senior by its own description,
- it must start well before the user's configured start date,
- it needs a clearance or citizenship the user does not have.

Keep: new grad, early career, 0 to 2 years, or explicit graduating-class programs. If the user asks for
a stretch, do it and say what the stretch is. A skipped role can still be worth a note to the person
who owns the work.

## Voice

Read the `voice_samples` in the config. Match them: contractions, plain words, short sentences, second
person. Start with "Hi <first name>," (or "Hey" for a peer, an alum or someone the user has met).

## Before you hand a draft over

Read it as the recipient. Would they know in the first line why this is to *them*? Is there exactly one
concrete ask? Could it be sent to a different company with the name swapped? If yes, rewrite the hook.
