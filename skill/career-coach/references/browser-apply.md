# Browser playbook: filling applications and staging LinkedIn notes (Claude in Chrome)

Claude in Chrome drives the user's real, logged-in Chrome. Claude fills and stages. **The user clicks
every Submit and every Send.** Use this only when the user asks in the current session and the
extension is connected (`tabs_context_mcp` answers).

Load the browser tools once, in one ToolSearch call, before starting:
`select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__tabs_close_mcp,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__file_upload`

## Global rules

- **Tabs: keep at most 3 to 5 Claude-opened tabs at a time.** Close each one after the user has
  submitted, saved or sent from it. Opening a dozen edit tabs at once can freeze Chrome.
- **Never navigate a tab the user handed over** for a specific purpose (a Sales Navigator search, a
  form they started). Open a new tab instead, within the tab cap.
- Navigate straight to the ATS URL, not the company page that iframes it (company-domain URLs with
  `?gh_jid=<id>` are Greenhouse: open `job-boards.greenhouse.io/<slug>/jobs/<id>`).
- Fill only from Standard Answers and the Form Prep note for this role. A field not covered stays blank
  and goes on the list the user sees.
- Upload resumes only from the configured resume folder, by exact filename.
- After a resume parse (Ashby, Workday), re-read every autofilled field and correct it to Standard
  Answers.
- **Before typing anything, check `document.activeElement`** is the field you mean. A click that missed
  its target leaves focus elsewhere, and the next keystrokes land in the wrong field (a country name
  once ended up in a last-name box).
- **Read back every field** after filling and compare it to what you meant to enter. List mismatches
  first in the handover. React forms can show a value they did not accept.
- **Stop and hand over at**: any login, password, account creation or one-time code; any CAPTCHA or
  "human check"; any "I certify this is true" box or e-signature; any payment or upsell; and **Submit**.
- End with a short report: filled, left blank, anything odd, and what the user must do (attach files,
  tick the attestation, click Submit).

## Form content rules

- **Education: add every degree as its own entry.** A double major or dual degree gets one entry per
  degree ("Add another"). A form with only one entry undersells the user.
- **EEO and self-ID questions** (gender, race, veteran, disability): **decline to answer by default**,
  unless the user's Standard Answers row says otherwise.
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
4. Click the option element by script (match its visible text), or type to filter and press Enter
   after checking `document.activeElement`.
5. Re-read every single-value display afterward and confirm the right option stuck.

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

## Per-ATS notes

| ATS | Account | Claude fills | Stop points and quirks |
|---|---|---|---|
| Greenhouse | No | Name, email, phone, location, links, custom questions, dropdowns per the helpers above | EEO section: decline. Stop before "Submit application" |
| Ashby | No | Resume first (it autofills), then re-check name and email, links, custom questions | Stop before "Submit Application" |
| Lever | No | Resume, name, email, phone, current company, links, "Additional information" | hCaptcha on some boards at Submit: user |
| BambooHR | No | Contact fields, resume, date available, yes/no questions | Stop before Submit |
| JazzHR | No | Resume, links, start date, work authorization, sponsorship, essays after the user fills brackets | "Human Check" is a CAPTCHA: user. SMS consent unchecked |
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
   `cc.py check --kind note` enforces it). Free accounts get only a few personalized notes a month.
5. **Messages and InMail:** regular LinkedIn compose resists scripting; **Sales Navigator compose**
   works. Open the lead page (`/sales/lead/<id>`; get lead ids from a Sales Navigator search), click
   Message, then fill `input[placeholder*=Subject]` and `textarea[name=message]` with the native
   setter. Check whether the compose box says "Free" (Open Profile) before the user spends an InMail.
   Stop before Send.
6. Already 1st-degree: stage the message (120 words max) instead of a note. Already "Pending": stop
   and report. A note-limit or upsell dialog: stop and report; never "Send without a note" unless the
   user says so.
7. At most 5 staged at a time, within the tab cap, and keep connection requests to about 15 to 20 a
   day. Every note is written for that person. No automation tools, no identical text to many people:
   both get accounts restricted.
8. The user says "sent X, Y": run `cc.py mark --person X --outreach sent` for each.

## Claude in Chrome quirks

- Closing the last Claude-opened tab in its tab group dissolves the group.
- Screenshots can time out on LinkedIn pages; `javascript_tool` still works.
