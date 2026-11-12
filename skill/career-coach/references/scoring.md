# Scoring: fit from 0 to 100

Score each matching **role**, then give the **company** the score of its best role (or of the company
itself when no role is posted). Show the breakdown in the company note's Snapshot so the user can argue
with it. Be honest: an inflated 85 on everything makes the ranking useless.

Lanes, home region, fun cities, stage band and max years all come from the config.

| Factor | Points | How to score |
|---|---|---|
| Role family | 25 | The user's top families (from their lanes): 20 to 25. Adjacent families: 15 to 18. Generic sales with no technical angle: 8. Half or more pure engineering (unless that is a lane): 0 and drop it |
| Evidence match | 25 | Count the posting's real requirements that a **verified** fact covers. 80%+ covered: 25. Half: 13. Tell real requirements from boilerplate |
| Level and timing | 15 | Use the posting's stated years (`Yrs` from `cc.py jobs`), never the title alone: "Associate" roles often want 5+. New grad, or 0 to 2 years: 15. Required or preferred 3+ years: skip (see `writing-rules.md#vetting`). Note it if the posting says "start immediately" and the user starts later |
| Company stage and sector | 15 | Inside the stage band and the first lane: 15. Inside the band, a later lane: 10. Seed: 7. Late stage: 5 |
| Warm path | 10 | 1st-degree connection, coworker or club person there: 10. Alum on the team, or an org contact: 7. Connector intro possible: 5. Cold: 0 |
| Momentum | 5 | Signal in the last 30 days: 5. 31 to 60: 3 |
| Location | 5 | Home region: 5. A city in `fun_cities`: 3. Remote: 3. Elsewhere: 1 |

**Skills bonus**: if the role wants something the user is unusually strong at and the Fact Sheet proves
(for example scripting, SQL or internal tools inside an ops or PM job), add up to 5 (cap 100).

## Bands

- **80 to 100**: act this week. Name people and draft openers.
- **65 to 79**: worth people research; openers only if a warm path exists.
- **50 to 64**: keep on the list, refresh in a month.
- **under 50**: do not write a note unless the user asked for that company.

## Which resume

Recommend one upload-ready file from `[paths] resume_dir` by exact filename, matched to the role family.
Never suggest a file outside that folder.

## Shortlist shape

Rank by fit, then enforce: at least `home_region_share` of the list in the home region (ceil for small
lists; skip the rule when the share is 0), at most 3 companies from a later lane in a first-lane scan
unless the user asked for that lane, and no more than one company that only made it on a posting with
no other signal. If fresh home-region companies run out, say so rather than adding stale ones.
