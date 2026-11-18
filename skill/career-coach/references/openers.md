# Openers: short, specific, in the user's voice

Read `writing-rules.md` first. An opener has exactly three parts. Anything else is cut.

1. **Hook**: one real thing *this company* did recently, specific enough that it could not be pasted
   into a note to another company. Dated, with a URL kept in the person JSON (`hook`, `hook_date`,
   `hook_url`). Inside 60 days is best; past 120 days, find a newer one.
2. **Proof**: one or two facts about the user that map to *this role*, from `cc.py facts` only.
3. **Ask**: one concrete, easy-to-say-yes ask that fits the phase.

## The ask by phase (`cc.py doctor` prints today's phase from the config)

A role with an **open req** always gets the application ask, whatever the date. Otherwise:

- **relationship**: the user is not asking for a job yet. Ask for 10 to 15 minutes to learn how the
  team hires for this kind of role and when reqs open for their start date. No "I'm applying", no
  referral ask: a polite no on timing burns the first impression.
- **application**: name the open req, give graduation and start date, ask for a quick call with the
  hiring manager or a referral.
- **close**: follow-ups and thank-yous only.

Phase names, dates and advice text are whatever the config's `[[phases]]` say; the three above are the
defaults the example config ships with.

## Voice

Match the config's `voice_samples`. Friendly, direct, a little casual, no corporate filler.

- "Hi <first name>," (or "Hey" for a peer, an alum or someone they have met).
- Contractions, plain words, short sentences.
- Name organizations in full the first time.
- See the banned phrases in `writing-rules.md`; `cc.py check` warns on them.

## Proof points

Build a small table for the user from `cc.py facts` in the first session, one line per role family
(ops, BD, PM, GTM, finance), and reuse it. Re-run `cc.py facts` before each batch: a row can change.
Keep wording no stronger than the row ("grew the budget to", not "raised").

## Formats and limits

| Kind | Limit | When |
|---|---|---|
| `note` (LinkedIn connection note) | the config's note limit: 200 characters free, 300 Premium | Aim for the last 50 characters of the limit (250 to 300 with Premium) so the ask is a full sentence. Write it so it works alone |
| `message` (LinkedIn DM or InMail) | 120 words, aim for 60 to 100 | After they accept, or with InMail |
| `email` | 160 words; follow-up emails under 120 | The day-3 follow-up in `apply-loop.md`, or when asked; only to a sourced address |
| `answer` (form answers, essays, bullets) | 300 words; always `--strict` | Every application answer |

Always produce `note` and `message`. Run each through
`cc.py check --kind note|message --allow '<sourced company number>'` and fix every ERROR. The upsert
refuses a failing draft.

## Examples (fake person, fake companies)

Every example opens with a first-person take, carries one proof and ends on the full-sentence ask.

Relationship phase, hiring manager at a hardware startup, cold, Premium note:

> **note** (286 chars): Hi Jane, what I find interesting about the second test site is that you're testing in the field before the factory is done, which is the hard way and the fast way. I closed 12 corporate sponsors for State's robotics club. Would you have 10 minutes for a call on how your ops team hires?

> **message**: Hi Jane, what I find interesting about the second test site is that it puts field testing ahead of the factory build, so the ops team has to run two schedules at once. That is the kind of work I want after I finish CS and Economics at State University in May. I led sponsorships for our robotics club and closed 12 corporate sponsors. Would you have 10 minutes for a call on how your operations team hires for August 2027 starts?

Application phase, open req, alum:

> **note**: Hey Sam, fellow State grad here. I applied for the Business Operations Associate role. To me the best part of it is owning planning across two sites in year one. I ran sponsorships for our robotics club for 2+ years. Would you have 10 minutes for a call on what the role owns first?

Day-3 follow-up email after applying (template and timing in `apply-loop.md`):

> Hi Sam, I applied for the Business Operations Associate role and sent you a note on LinkedIn, so I'm following up here. What I find interesting about the new Springfield line is that it doubles output without a second shift, which makes planning the bottleneck. I closed 12 corporate sponsors for our robotics club. I finish at State University in May. My resume is attached. Would you have 10 minutes for a call on what the role owns first?

Intro ask to a connector, batched:

> Hey Riley, hope the new role is going well. I'm lining up conversations for after I graduate in May, and two companies I'm most interested in are Acme Robotics and Globex Systems. Do you know Jordan Sample at Acme well enough to intro me? I'd want 10 minutes to learn how their ops team hires. Happy to send a short blurb you can forward.
