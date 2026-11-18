# Sourcing: companies with something new in the last 60 days

A company makes a run only with a **dated, sourced signal inside `[search] signal_days`** (60 by
default). Three kinds count:

| Signal | Good sources | What to record |
|---|---|---|
| Posted a matching role | `cc.py jobs` or `cc.py sweep` (Greenhouse, Lever, Ashby and BambooHR give real dates), the careers page | role, posted date, URL |
| Raised money | company blog or press release, TechCrunch, Axios Pro Rata, Crunchbase News, regional business journals, the lead VC's announcement | round, amount, lead, date, URL |
| Launched something | product launch, factory or site opening, first flight or test, contract award, major customer | what, date, URL |

Funding and launches are the best hooks for openers. A posting alone is the weakest hook ("saw you're
hiring" is what everyone writes), so pair it with something else when you can.

## What works best

Probing job boards of companies you already have a name for beats broad news searches. Generic queries
("startup raises Series B October") mostly return stale directory pages. So: build a list of 20 to 40
plausible names fast, run `cc.py jobs` on each (seconds apiece) or put them in `Data/ats.tsv` and run
`cc.py sweep`, keep the ones with matching roles, and only then search news for each survivor's funding
or launch.

## Where candidates come from, in order

1. **The user's own lists.** `Target Companies.md`, `Data/Company Follows.csv` (LinkedIn export of
   companies they follow), `seeded` company notes, anything they paste.
2. **The seed boards** in `Data/ats.tsv` (`cc.py sweep`). The kit ships with about 140 public boards,
   weighted toward hardware, energy, space, robotics and AI. Add the user's own sectors early: one
   `cc.py jobs --company X --careers-url <url>` per company caches its board.
3. **Fresh funding news.** Run several searches in one turn:
   - `"Series A" OR "Series B" OR "Series C" raises <sector> <Month> <Year>` for each of the user's sectors
   - `<home region> startup raises Series <Month> <Year>` and `<home city> startup funding <Month> <Year>`
   - `site:techcrunch.com Series B <sector> <Month> <Year>`
   - `Crunchbase News biggest funding rounds week <date>`
4. **VC portfolios** that fit the user's lanes. JavaScript-rendered portfolios return an empty shell to
   WebFetch; search `"<VC>" led Series <sector> <Year>` instead.
5. **Job boards** for roles at companies you did not know: Indeed (when the Indeed connector is available
   in Claude, its job search is free to use), Built In (city editions), Y Combinator's Work
   at a Startup, Welcome to the Jungle, `site:jobs.ashbyhq.com "business operations"` style searches.
   Then go back to step 3 for that company's stage and a better hook.

## Checking stage

Confirm the **last priced round** from a source dated in the last 2 years. Record it as
`"$140M Series B, Sep 2026"`. Rules of thumb:
- Seed or pre-seed: below a Series A to C band. Keep only if the signal and fit are exceptional.
- Series D and later, public, or 1,000+ people: outside the band. Keep if the user listed them; do not
  add new ones in a scan.
- Grant-funded or bootstrapped: say so.
If you cannot confirm the stage, write `stage: unknown` and say so; never guess.

## Home-region share

At least `home_region_share` of each shortlist should be in `home_region` (locations matching
`home_region_pattern`). Search the home region on purpose early in the run (regional business journals,
the Built In city edition, "<home city>" plus the sector). If you cannot reach the share with fresh
signals, say so rather than adding stale companies.

## Dropping

Drop and log the reason when: no signal inside the window, the stage cannot be confirmed and the company
is not on the user's list, the only open roles are outside the user's lanes, the company had layoffs or a
shutdown signal in the last 90 days (mention it), or it is outside the user's country with no local site.
