---
created: {{date}}
tags:
  - career/application
  - type/reference
---
# Story Bank

Every essay, short answer, cover-letter bridge and interview answer is built from these stories. Claude writes form essays in full from this note (no brackets), uses a **different story for each question** on the same form, and ends each answer with the story's lesson tied to that company's work. Numbers in a story must be on a `verified` or `decided` row of the [[Fact Sheet]]; `cc.py check --strict --kind answer` enforces it.

Add a story the day something happens, while you still remember the details. Five strong stories cover almost every question.

## Quick map

| They ask | Lead story | Backup | One-line lesson |
|---|---|---|---|
| Tell me about yourself | The arc | | [one sentence on the thread that runs through your work] |
| Ambiguity, outside your domain | Example: the club's first sponsor season | | Learn the customer before the pitch |
| Pressure or a crisis | Example: the event-day supplier failure | | Stabilize first, diagnose second |
| Failure or mistake | Example: the missed demo date | | Run a cheap trial before the expensive one |
| Team conflict | Example: two leads leave mid-season | | Write the process down so it survives turnover |
| Persistence, rejection, sales | Example: the sponsor pipeline | | A steady weekly habit beats a burst of effort |
| Built something that lasts | Example: the internship tracking tool | | Hand it off with docs, not with you |
| Used data to decide | **GAP** | | |
| Disagreed with a lead | **GAP** | | |
| Weakness | **GAP** | | |

Mark a row **GAP** when you have no real story yet. Never fill a gap with an invented one; leave it and tell Claude to pick another question type.

## Story format (STAR plus a lesson)

Copy this block for each story. Keep each part to one to three sentences; Claude expands or trims to the form's word limit.

### Example: the sponsor pipeline (replace with your own)
- **Situation:** the robotics club had two sponsors and a budget that could not cover the season's build.
- **Task:** as sponsorship lead, find enough corporate support to fund travel and parts.
- **Action:** built a target list by industry, wrote a short pitch per segment, kept two afternoons a week for calls and tracked every lead in one sheet.
- **Result:** 12 corporate sponsors by spring (Fact Sheet row: Corporate sponsors closed).
- **Lesson:** a steady weekly habit beats a burst of effort.
- **Fits:** BD, partnerships, sales, ops. **Avoid for:** pure analytics questions.

### Example: the missed demo date (replace)
- **Situation:**
- **Task:**
- **Action:**
- **Result:**
- **Lesson:**
- **Fits:**

## How Claude uses this note

1. Read the form's questions (`cc.py questions`) and assign one story per question, no repeats.
2. Write each answer in full, in the user's voice: the situation in one line, what *you* did, the result, then the lesson as one sentence tied to something specific about the company ("That is the same problem your field team has when...").
3. Run each through `cc.py check --strict --kind answer`.
4. Show the answers in the Form Prep note before filling the form, so the user reads them once.

---
[[Standard Answers]] | [[Fact Sheet]]
