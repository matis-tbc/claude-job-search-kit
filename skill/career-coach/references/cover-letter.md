# Cover letters

Attach a short cover letter to every application whose form takes one, even when it is optional.
Claude writes it, builds the PDF and attaches it; the user reads it before Submit.

## Format (about 150 to 200 words, four short paragraphs)

1. **Company hook.** One line on who the user is (school, degrees, graduation, start date) and that they
   want to start at the company. Then one or two plain-language sentences on something real and recent
   the company did, written as what the user finds interesting about it. No jargon unless the role needs
   it; it should read as a person who looked, not a press release.
2. **One bridge.** The link between the user's experience and the company's problem, in one or two
   sentences ("I have run a smaller version of that job: ..."). Pick it from the Story Bank; use a
   different story from the form's essays where you can.
3. **One proof.** A single short paragraph with one or two Fact Sheet numbers that map to the role.
4. **Close.** One line naming the team and the office ("I'd love to bring that to the operations team in
   Springfield.").

Also: a `Re:` line with the exact role title, no em dashes, no fact lists about the company, and the same
rules as `writing-rules.md` (why-us answers, outcome numbers, confidential details). Check the body with
`cc.py check --strict --kind answer` before building.

## Procedure

1. Copy `Templates/cover_letter_template.tex` (copied into the vault by `cc.py setup`) to
   `cover_letter_<company>.tex` next to the user's resume sources, never into the upload folder.
2. Fill the header once from Standard Answers (name, city, email, LinkedIn, website) and keep it the same
   as the resume header.
3. Replace every `[BRACKET]` with finished text. No brackets may survive into the PDF.
4. **Break the ff ligature**: type every "ff" as `f\kern0pt f` (`of\kern0pt fice`, `ef\kern0pt fort`).
   Some TeX engines store "ff" as a single glyph, and ATS keyword search then misses words like "office".
   `{}` does not break it; `\kern0pt` does.
5. Build with `tectonic cover_letter_<company>.tex` (or `pdflatex`/`xelatex`). If no TeX is installed, say
   so and offer the same text as a plain paste-in for the form's cover-letter box instead.
6. Check the text layer: `pdftotext cover_letter_<company>.pdf - | grep -c $'\xef\xac\x80'` must print 0
   (that byte sequence is the "ff" ligature). Also confirm it fits on one page.
7. Save the PDF in the upload folder (`[paths] resume_dir`) under the same base name, open it for the user
   to read once, then attach it in the form.

The same ligature rule applies to resume sources built with TeX. Run the same `pdftotext` check after any
resume rebuild.
