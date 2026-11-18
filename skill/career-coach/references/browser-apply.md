# Browser playbook: filling applications and staging LinkedIn notes (Claude in Chrome)

Claude in Chrome drives the user's real, logged-in Chrome. Claude fills and stages. **The user clicks
every Submit and every Send.** Use this only when the user asks in the current session and the
extension is connected (`tabs_context_mcp` answers).

Load the browser tools once, in one ToolSearch call, before starting:
`select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__tabs_close_mcp,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__file_upload`

## Global rules

- **Tabs: at most 5 Claude-opened tabs at a time.** The normal batch is five applications filled in
  five tabs, then the user reads each one and clicks Submit. Close each tab after the user has
  submitted, saved or sent from it. Opening a dozen edit tabs at once can freeze Chrome.
- **Do the work, do not hand it back.** Claude fills every field, writes every essay, attaches the
  resume and cover letter and reports what is ready for a click. The user's steps are only the ones
  the stop list below reserves for them.
- **Never press Enter or Return inside a form field.** On Greenhouse an Enter in a react-select
  submitted a whole application before anyone had read it. Pick options by clicking them; move between
  fields by clicking or with Tab.
- **Never navigate a tab the user handed over** for a specific purpose (a Sales Navigator search, a
  form they started). Open a new tab instead, within the tab cap.
- Navigate straight to the ATS URL, not the company page that iframes it (company-domain URLs with
  `?gh_jid=<id>` are Greenhouse: open `job-boards.greenhouse.io/<slug>/jobs/<id>`).
- Fill only from Standard Answers, the Story Bank and the Form Prep note for this role. A required field
  not covered goes on the list the user sees.
- **Optional fields stay blank unless the answer is accurate today.** Never list a past employer as the
  current company or a past title as the current title.
- Upload resumes only from the configured resume folder, by exact filename. Attach the cover letter
  built per `cover-letter.md` wherever the form takes one.
- **After every resume upload, re-read every field.** Greenhouse, Lever, Ashby and Workday autoparse the
  resume and overwrite fields you already filled (a past employer showing up as "Current company" is
  the common one). Correct each to Standard Answers.
- **Transcript uploads:** a required transcript means skip the role (check `cc.py questions` before any
  drafting); an optional one stays blank. Follow the Standard Answers transcript row if it says otherwise.
- **Before typing anything, check `document.activeElement`** is the field you mean. A click that missed
  its target leaves focus elsewhere, and the next keystrokes land in the wrong field (a country name
  once ended up in a last-name box).
- **Read back every field** after filling and compare it to what you meant to enter. List mismatches
  first in the handover. React forms can show a value they did not accept.
- **Stop and hand over at**: any login, password, account creation or one-time code; any CAPTCHA or
  "human check"; any "I certify this is true" box or e-signature; any payment or upsell; and **Submit**.
- End with a short report: filled, left blank, anything odd, and exactly what waits on the user (tick
  the attestation, click Submit).
- **After the user submits, check the inbox, not the user.** ATS confirmations ("Thank you for
  applying") arrive within minutes. With an email connector, search for them
  (`from:<company> OR "<company>" application newer_than:7d`) and log with `cc.py applied`. No
  confirmation after a day or two means it did not go through; say so and offer to refill it.

## Form content rules

- **Education: add every degree as its own entry.** A double major or dual degree gets one entry per
  degree ("Add another"). A form with only one entry undersells the user.
- **EEO and self-ID questions** (gender, race, veteran, disability): **decline to answer by default**,
  unless the user's Standard Answers row says otherwise.
- **Essays and short answers:** written in full by Claude from the Story Bank, one different story per
  question, each ending with a lesson tied to the company. Never leave brackets or blanks, even when the
  form says "in your own words" (the user reads them before Submit). Rules in `writing-rules.md`.
- SMS or marketing consent stays unchecked.
- "How did you hear": the Standard Answers default; "Referral: <name>" only after that person said yes.
- Salary: the user's call. Default text "Within the posted range" only if Standard Answers says so.
- GPA: the cumulative figure unless the field asks for major GPA.

## Greenhouse field-fill helpers

Greenhouse forms are React. Setting `.value` directly does not register. Use the native setter and fire
the events React listens for:

```js
function fill(sel, value) {
  const el = document.querySelector(sel);
  if (!el) return "missing " + sel;
  el.scrollIntoView({block: "center"});
  el.focus();
  const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(el, value);
  el.dispatchEvent(new Event("input", {bubbles: true}));
  el.dispatchEvent(new Event("change", {bubbles: true}));
  el.blur();
  return sel + " = " + el.value;
}
```

For contenteditable fields, focus the element and use `document.execCommand("insertText", false, text)`.

**Dropdowns (react-select) ignore script-only opening.** For each one:

1. `scrollIntoView({block: "center"})` on the control, so it sits at a known position.
2. Read its `getBoundingClientRect()`.
3. Open it with **one trusted coordinate click** (the `computer` tool's click at the rect's center).
   A script `click()` does not open react-select.
4. Click the option by script with the helper below (it matches the visible option text). For a long
   list, type a few letters to filter first, then click the option. **Never press Enter.**
5. Re-read every single-value display afterward and confirm the right option stuck.

```js
// Run after the menu is open. Clicks the visible [role=option] whose text matches.
function pickOption(text) {
  const opts = [...document.querySelectorAll('[role="option"]')].filter(o => o.offsetParent !== null);
  const t = text.trim().toLowerCase();
  const hit = opts.find(o => o.textContent.trim().toLowerCase() === t) ||
              opts.find(o => o.textContent.trim().toLowerCase().startsWith(t));
  if (!hit) return "no option '" + text + "'; visible: " + opts.map(o => o.textContent.trim()).slice(0, 15).join(" | ");
  hit.scrollIntoView({block: "center"});
  hit.click();
  return "picked " + hit.textContent.trim();
}
```

Quirks: the "Country" field next to the phone number is the phone dial code, not the user's country.
Location fields are autocompletes: type the city, wait for the list, pick the option. Invisible
reCAPTCHA can challenge on Submit; that is the user's step.

## Pages with reCAPTCHA

Pages that load reCAPTCHA (many Greenhouse, Ashby and JazzHR forms) often never finish loading in the
extension's eyes, so **screenshots, `find`, `read_page` and `file_upload` time out**. `javascript_tool`
and coordinate clicks still work. On those pages:

- Fill text fields and selects by script as above.
- **The user attaches the resume and cover letter files.** Say exactly which file goes in which field.
- Read back values by script instead of screenshots.
- Never try to solve or bypass the CAPTCHA.

## Lever field-fill helper

Lever application pages are plain HTML forms, so setting values by `name` and firing input and change
events works for text fields:

```js
// e.g. leverFill({"name": "Alex Example", "email": "alex@example.com", "phone": "...",
//                 "urls[LinkedIn]": "https://www.linkedin.com/in/your-profile/", "comments": "..."})
function leverFill(map) {
  return Object.entries(map).map(([name, value]) => {
    const el = document.querySelector(`[name="${name}"]`);
    if (!el) return "missing " + name;
    el.value = value;
    el.dispatchEvent(new Event("input", {bubbles: true}));
    el.dispatchEvent(new Event("change", {bubbles: true}));
    return name + " = " + el.value;
  });
}
```

Read the form's real field names first (`[...document.querySelectorAll("input,textarea,select")]
.map(e => e.name)`); custom questions use names like `cards[<id>][field0]`. Radio and checkbox answers
need a click on the right input. Leave `org` (current company) blank unless the user holds a job today,
and re-check it after the resume upload: Lever fills it from the resume.

## Ashby text fields

Ashby ignores values set by script: the field shows the text but the form submits it empty. Click the
field (a `find` ref or a coordinate click), confirm `document.activeElement` is that field, then type
with the `computer` tool. Upload the resume first, because the parse overwrites name, email, phone and
links; then fill or correct the rest and read every field back.

## Per-ATS notes

| ATS | Account | Claude fills | Stop points and quirks |
|---|---|---|---|
| Greenhouse | No | Name, email, phone, location, links, custom questions, dropdowns per the helpers above | EEO section: decline. Never Enter in a react-select. Stop before "Submit application" |
| Ashby | No | Resume first (it autofills), then click and type every text field, re-check name and email, links, custom questions | Script-set values do not stick. Stop before "Submit Application" |
| Lever | No | Resume, then fields by `name` per the helper above, links, "Additional information" | Re-check "Current company" after the upload. hCaptcha on some boards at Submit: user |
| BambooHR | No | Contact fields, resume, date available, yes/no questions | Stop before Submit |
| JazzHR | No | Resume, links, start date, work authorization, sponsorship, essays written from the Story Bank | "Human Check" is a CAPTCHA: user. SMS consent unchecked |
| Workday | Yes, one per company: the user signs in or creates it | My Information, My Experience (autofill, then fix every job to the Fact Sheet's titles and months), Application Questions, Voluntary Disclosures | Stop at Review. Sessions time out, so save each step. Dates are MM/YYYY |
| Oracle HCM | Email plus a one-time code: user | After the code: contact, resume, education, questions | The sign-in lives in that tab's session; do not move or reopen the tab |
| Eightfold | Usually asks to sign in first: user | Resume, contact, questions | Stop before Submit |

## LinkedIn staging

Claude may open a profile, open the Connect or Message dialog and type the drafted text. The user
clicks Send. One profile at a time, only for people with a person note, a source and a checked draft.

1. Open the `linkedin` URL from the person note. No URL: search "<name> <company>". More than one
   plausible match: stop and show the candidates.
2. **Verify while there:** read the headline and current position. Different company or role: skip
   this person and tell the user; do not stage.
3. **Connection notes:** open `https://www.linkedin.com/preload/custom-invite/?vanityName=<slug>`
   (the slug is the part after `/in/` in the profile URL). Click "Add a note" by script, then set the
   textarea with the native value setter plus input and change events. The character counter updating
   confirms LinkedIn registered it. Stop before Send.
4. **Note length:** 300 characters with Premium, 200 on a free account (`[linkedin]` in the config;
   `cc.py check --kind note` enforces it and warns under limit minus 50). With Premium, write 250 to 300
   characters so the note ends on a full-sentence ask: "Would you have 10 minutes for a call on X?",
   never a clipped "10 min on X?". Free accounts get only a few personalized notes a month.
   If the regular invite page will not take a script value, use the `find` tool for the dialog's
   textbox, click that ref and type; the invite modal is often not reachable by `document.querySelector`.
5. **Messages and InMail:** regular LinkedIn compose resists scripting; **Sales Navigator compose**
   works. Search `linkedin.com/sales/search/people?keywords=<Name>%20<Company>`, click the button labeled
   "Message <Name>", then `find` the "Subject (required)" textbox, click that ref, type the subject,
   press Tab (Tab only, never Enter) and type the body. Do not click coordinates inside the composer: a
   miss lands on "create draft" or another control. The profile page's own Message button opens a tab
   outside Claude's group. Check whether the compose box says "Free" (Open Profile) before the user
   spends an InMail. Stop before Send.
   **Sales Navigator connection note:** same search, "See more actions for <Name>", Connect, then type
   into the textarea of the dialog that contains "Send invitation" (not an old InMail composer's).
6. Already 1st-degree: stage the message (120 words max) instead of a note. Already "Pending": stop
   and report. A note-limit or upsell dialog: stop and report; never "Send without a note" unless the
   user says so.
7. At most 5 staged at a time, within the tab cap, and keep connection requests to about 15 to 20 a
   day. Every note is written for that person. No automation tools, no identical text to many people:
   both get accounts restricted.
8. **Platform limits:** LinkedIn caps InMail *sends* per month regardless of credits left ("You have
   reached the limit of InMail sends for this month"), and Sales Navigator rate-limits searches after
   roughly 100 in a few hours ("You've reached the request limit"). Pace lookups (collect profile URLs
   in the person notes first), and switch to connection notes when InMail is capped.
9. An unsent InMail composer blocks navigation with a "Leave site?" dialog. Force the navigation only
   when the draft text is saved in the person note.
10. The user says "sent X, Y": run `cc.py mark --person X --outreach sent --channel <note|inmail|open-profile>`
    for each (`--event note-sent` is the default cadence for a connection request).

## Claude in Chrome quirks

- Closing the last Claude-opened tab in its tab group dissolves the group.
- Screenshots can time out on LinkedIn pages; `javascript_tool` still works.
