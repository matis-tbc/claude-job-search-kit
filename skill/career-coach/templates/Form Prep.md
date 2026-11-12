---
created: {{date}}
tags:
  - career/application
  - type/notes
---
# Form Prep, YYYY-MM-DD <batch name>

One note per batch of applications. Every question is pulled live with `cc.py questions --ats <ats>:<slug> --id <id>`. **[YOU]** marks the answers only you can give. Standing answers come from [[Standard Answers]]. Claude fills the form in the browser; you attach files if the page blocks uploads, read the filled form and click Submit yourself.

## 1. <Company>, <Role> (<City, ST>)
[Apply](https://example.com/jobs/1) | Fit 74 | <pay band if posted> | <onsite, hybrid or remote> | company note [[<Company>]]

**What the job is:** two or three plain sentences from the posting: what you would own, who you would work with.

**Catch:** anything that could sink it: required or preferred years (skip at 3+), a start date before yours, clearance or citizenship lines, travel.

**Resume:** `<exact PDF filename>` from the resume folder.

| Question | Answer |
|---|---|
| LinkedIn Profile (required) | from Standard Answers |
| Authorized to work in the U.S.? (required) | Yes |
| Sponsorship now or in the future? (required) | No |
| Why <Company>? (required) | **[YOU]**. A skeleton follows the table |
| Salary expectations | **[YOU]**. Default: "Within the posted range" |
| Education | One entry per degree |
| Voluntary EEO questions | Decline to answer |

Skeleton for "Why <Company>?", for you to rewrite in your words (answer the why; no fact list; at most one number about you):
*[One line, in your words, on what you admire about what they are building and why it matters.] [Why that mission is the work you want to do.] [ONE bridge from your own experience, ideally touching their domain.] [Close on fit or place, if true.]*

## Contacts and order
| Role | First | Second |
|---|---|---|
| <Company> | [[<Hiring manager>]], <title> (hiring manager) | [[<Recruiter or alum>]], <title> |

Stage the notes after you submit. Claude opens at most 3 to 5 tabs and stops before every Send.

## After you submit
Tell Claude "submitted <Company>" and it runs `cc.py applied`, which sets the follow-up dates.
