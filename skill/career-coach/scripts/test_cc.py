#!/usr/bin/env python3
"""Tests for cc.py on a throwaway vault and config. Run: python3 -I test_cc.py (no network needed)."""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import warnings

warnings.simplefilter("ignore", ResourceWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.join(HERE, "cc.py")
EXAMPLE = os.path.join(os.path.dirname(HERE), "config.example.toml")

FACT_SHEET = """---
created: 2026-10-10
---
# Fact Sheet

## State Robotics Club

| Fact | Value to use | Status | Source / note |
|---|---|---|---|
| Team size | 50 | **conflict** | Resume says 50; LinkedIn says 40 |
| Competition result 2026 | 3rd in the nation, Mar 2026 | verified | results page |
| Record annual budget | $225K (2025-26 season) | verified as budget | say grew the budget to |
| Budget before the user led sponsorships | $53K or $79K | **conflict** | "4x" holds only from $53K |
| Corporate sponsors | 54 | verified | sponsor tracker |
| Sponsored share of build cost | 80%+ | estimate | the user's guess |

## Example Corp internship

| Fact | Value to use | Status | Source / note |
|---|---|---|---|
| Phishing simulation | site + 50 USB keys | verified (offer letter) | |
| Savings | estimated $150K per year | self-reported, not independently verified | |
| Assets tracked | 25,000+ | blocked | retired, same set as another row |

## Education

| Fact | Value to use | Status |
|---|---|---|
| GPA | 3.9/4.0 | **conflict** on label (major vs cumulative) |
"""

TRACKER = """---
tags:
  - type/tracker
---
# Application Tracker

## Active

| Company | Role | Lane | Status | Resume sent | Next action | Date |
|---|---|---|---|---|---|---|
| Northwind Aero | Special Projects Analyst | A | Not applied | - | Recruiting event next week | 2026-09-23 |
| Globex Signal | Business Development Representative | B | **Applied 2026-11-10** | Resume_BD.pdf | Send [[Jordan Sample]] the note today | 2026-11-10 |
| Acme Robotics | BizOps Associate | A | applied | - | Follow up. [apply](https://a.com/j) | 2026-11-08 |
| Initech Launch | BD Engineer I, **Springfield IL** | A | APPLIED 2026-11-09 (online) | [[Resume_BD]] | See [[Ready to Send\\|Ready]] | - |
| Umbrella Defense | Operations Analyst | A | Apply by **Fri 11-13** | Resume_Ops | Apply | - |
| Hooli Forge | Strategic Finance Associate | A | Applied | - | [[Casey Placeholder]] | - |
| Broken | row | only |
| Vandelay Print | Technical Sales | B | Not applied | Resume_BD | Built for 2027 grads | 2026-11-10 |

## Logging rules
- Log the exact PDF filename.
"""


def write_config(path, vault, extra=""):
    text = open(EXAMPLE, encoding="utf-8").read()
    text = re.sub(r'^vault = ".*"$', "vault = " + json.dumps(vault), text, count=1, flags=re.M)
    open(path, "w", encoding="utf-8").write(text + extra)


def load_cc():
    spec = importlib.util.spec_from_file_location("cc_under_test", CC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CCTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.v = os.path.join(self.tmp.name, "vault")
        self.cfg = os.path.join(self.tmp.name, "config.toml")
        write_config(self.cfg, self.v)
        os.makedirs(os.path.join(self.v, "Career/Resume"))
        os.makedirs(os.path.join(self.v, "People"))
        os.makedirs(os.path.join(self.v, "Work/People"))
        os.makedirs(os.path.join(self.v, "Career/Job Search/Data"))
        open(os.path.join(self.v, "Career/Resume/Fact Sheet.md"), "w").write(FACT_SHEET)
        open(os.path.join(self.v, "Work/People/Riley Mentor.md"), "w").write(
            "---\ntags:\n  - work/ops\n  - type/reference\n---\n# Riley Mentor\n\nKnows people at Castor Labs.\n")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cc(self, *args, stdin=None, today=None, config=None):
        env = dict(os.environ, JOB_KIT_CONFIG=config or self.cfg)
        for k in ("CAREER_TODAY", "CAREER_VAULT", "CAREER_PRENAMED_GLOB", "CAREER_FACT_SHEET"):
            env.pop(k, None)
        if today:
            env["CAREER_TODAY"] = today
        return subprocess.run([sys.executable, "-I", CC, *args], input=stdin, capture_output=True,
                              text=True, env=env)

    def write_json(self, name, obj):
        p = os.path.join(self.tmp.name, name)
        json.dump(obj, open(p, "w"))
        return p

    # config
    def test_missing_config_gives_fix_line(self):
        r = self.run_cc("facts", config=os.path.join(self.tmp.name, "nope.toml"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("cc.py init", r.stderr)

    def test_init_writes_once_and_setup_never_overwrites(self):
        cfg = os.path.join(self.tmp.name, "sub", "config.toml")
        fresh = os.path.join(self.tmp.name, "fresh vault")
        os.makedirs(fresh)
        r = self.run_cc("init", "--vault-path", fresh, config=cfg)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(json.dumps(fresh), open(cfg).read())
        self.assertIn("already exists", self.run_cc("init", config=cfg).stdout)
        r = self.run_cc("setup", config=cfg)
        self.assertEqual(r.returncode, 0, r.stderr)
        fs = os.path.join(fresh, "Career/Resume/Fact Sheet.md")
        self.assertTrue(os.path.exists(fs))
        self.assertTrue(os.path.exists(os.path.join(fresh, "Career/Job Search/Standard Answers.md")))
        self.assertTrue(os.path.exists(os.path.join(fresh, "Career/Job Search/Templates/Form Prep.md")))
        ats = os.path.join(fresh, "Career/Job Search/Data/ats.tsv")
        self.assertGreater(len(open(ats).read().splitlines()), 50)
        open(fs, "w").write("MINE")
        self.run_cc("setup", config=cfg)
        self.assertEqual(open(fs).read(), "MINE")
        r = self.run_cc("doctor", config=cfg)
        self.assertIn("boards for sweep", r.stdout)

    def test_toml_fallback_matches_tomllib(self):
        cc = load_cc()
        text = open(EXAMPLE, encoding="utf-8").read()
        mine = cc.parse_toml_subset(text)
        self.assertEqual(mine["profile"]["degrees"], ["B.S. Computer Science", "B.A. Economics"])
        self.assertEqual(mine["warm"]["people_dirs"]["coworker"], "Work/People")
        self.assertEqual(mine["search"]["home_region_pattern"], r"illinois|chicago|springfield|evanston|naperville|\bil\b")
        self.assertEqual([p["name"] for p in mine["phases"]], ["relationship", "application", "close"])
        try:
            import tomllib
        except ImportError:
            return
        self.assertEqual(mine, tomllib.loads(text))

    def test_phase_comes_from_config(self):
        self.assertIn("phase: relationship", self.run_cc("doctor", today="2026-11-10").stdout)
        self.assertIn("phase: application", self.run_cc("doctor", today="2027-02-01").stdout)
        self.assertIn("phase: close", self.run_cc("doctor", today="2027-06-01").stdout)

    # facts and check
    def test_facts_only_usable(self):
        out = self.run_cc("facts").stdout
        self.assertIn("Corporate sponsors: 54", out)
        self.assertNotIn("Team size", out)
        self.assertNotIn("Savings", out)
        self.assertNotIn("Assets tracked", out)
        self.assertIn("4 usable facts", out)
        self.assertIn("[BLOCKED: blocked]", self.run_cc("facts", "--all").stdout)

    def test_check_blocks_conflict_number_in_context(self):
        r = self.run_cc("check", "--kind", "message", stdin="I led a 50-person team at the robotics club.")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Team size", r.stdout)

    def test_check_allows_same_number_in_other_context(self):
        r = self.run_cc("check", stdin="I ran a phishing test with 50 USB keys.")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_check_blocks_note_only_numbers_and_estimates(self):
        for text in ("We grew the budget 4x.", "Sponsors covered 80%+ of the build.", "Led a team of 40 engineers.",
                     "Tracked 25,000+ assets."):
            r = self.run_cc("check", stdin=text)
            self.assertEqual(r.returncode, 1, text + r.stdout)

    def test_check_verified_numbers_pass(self):
        r = self.run_cc("check", stdin="We placed 3rd in the nation, closed 54 sponsors and grew the budget to "
                                       "$225K. Would you have 10 minutes for a quick call in 2026?")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_check_em_dash_and_length(self):
        r = self.run_cc("check", "--kind", "note", stdin="Hi Sam \u2014 quick one. " + "x" * 200)
        self.assertEqual(r.returncode, 1)
        self.assertIn("em dash", r.stdout)
        self.assertIn("limit is 200", r.stdout)

    def test_premium_note_limit(self):
        cfg = os.path.join(self.tmp.name, "premium.toml")
        write_config(cfg, self.v)
        text = open(cfg).read().replace("premium = false", "premium = true")
        open(cfg, "w").write(text)
        note = "Hi Sam, " + "x" * 250
        self.assertEqual(self.run_cc("check", "--kind", "note", stdin=note).returncode, 1)
        self.assertEqual(self.run_cc("check", "--kind", "note", stdin=note, config=cfg).returncode, 0)

    def test_check_unknown_number_warns_and_allow(self):
        r = self.run_cc("check", stdin="Congrats on the $140M raise.")
        self.assertEqual(r.returncode, 0)
        self.assertIn("WARN", r.stdout)
        r = self.run_cc("check", "--allow", "$140M",
                        stdin="Congrats on the $140M raise. Would you have 10 minutes for a call on hiring?")
        self.assertIn("ok", r.stdout)

    def test_check_strict_makes_unknown_numbers_errors(self):
        r = self.run_cc("check", "--strict", "--kind", "answer", stdin="I served 35+ clients.")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ERROR", r.stdout)
        r = self.run_cc("check", "--strict", "--kind", "answer", stdin="I closed 54 sponsors over 2 years.")
        self.assertEqual(r.returncode, 1)  # 2 is not on the Fact Sheet either
        r = self.run_cc("check", "--strict", "--kind", "answer", stdin="I closed 54 sponsors in 2026.")
        self.assertEqual(r.returncode, 0, r.stdout)

    # companies
    def company(self, **kw):
        base = {"name": "Acme Robotics", "fit": 70, "home_region": True,
                "signals": [{"date": "2026-10-01", "what": "Raised Series A", "url": "https://a.com/1"}],
                "roles": [{"title": "BizOps Associate", "url": "https://a.com/j", "fit": 70}],
                "people": ["Pat Lee"], "why": "Builds robots."}
        base.update(kw)
        return self.run_cc("upsert-company", self.write_json("c.json", base))

    def cpath(self, name="Acme Robotics"):
        return os.path.join(self.v, "Career/Job Search/Companies", name + ".md")

    def ppath(self, name="Pat Lee"):
        return os.path.join(self.v, "People", name + ".md")

    def test_company_create_and_merge_keeps_human_edits(self):
        self.assertEqual(self.company().returncode, 0)
        text = open(self.cpath()).read()
        self.assertIn("status: research", text)
        self.assertIn("home_region: true", text)
        text = text.replace("status: research", "status: talking") + "\nMY OWN NOTE\n"
        open(self.cpath(), "w").write(text)
        r = self.company(fit=81, status="research", people=["Sam Kim"],
                         signals=[{"date": "2026-10-20", "what": "Launched v2", "url": "https://a.com/2"}])
        self.assertEqual(r.returncode, 0, r.stderr)
        text = open(self.cpath()).read()
        self.assertIn("status: talking", text)
        self.assertIn("MY OWN NOTE", text)
        self.assertIn("fit: 81", text)
        self.assertIn("https://a.com/1", text)
        self.assertIn("https://a.com/2", text)
        self.assertIn("signal_date: 2026-10-20", text)
        self.assertIn("[[Pat Lee]]", text)
        self.assertIn("[[Sam Kim]]", text)
        self.assertEqual(text.count("<!-- cc:log -->"), 1)

    def test_company_refuses_unsourced_signal_and_em_dash(self):
        r = self.company(signals=[{"date": "2026-10-01", "what": "x"}])
        self.assertEqual(r.returncode, 2)
        r = self.company(why="Great \u2014 fit")
        self.assertEqual(r.returncode, 2)

    def test_no_roles_message_uses_profile_start(self):
        self.company(roles=[])
        self.assertIn("August 2027 start", open(self.cpath()).read())

    # people
    def test_person_requires_source_and_refuses_guessed_email(self):
        r = self.run_cc("upsert-person", self.write_json("p.json", {"name": "A B", "company": "Acme"}))
        self.assertEqual(r.returncode, 2)
        r = self.run_cc("upsert-person", self.write_json("p.json", {
            "name": "A B", "company": "Acme", "source": "https://x.com", "why": "a.b@acme.example"}))
        self.assertEqual(r.returncode, 2)

    def test_person_opener_checked(self):
        r = self.run_cc("upsert-person", self.write_json("p.json", {
            "name": "A B", "company": "Acme", "source": "https://x.com",
            "opener": {"note": "Hi A, I led a 50-person team. Chat?"}}))
        self.assertEqual(r.returncode, 2)
        self.assertIn("Team size", r.stderr)

    def test_person_create_then_existing_note_untouched(self):
        r = self.run_cc("upsert-person", self.write_json("p.json", {
            "name": "Pat Lee", "company": "Acme Robotics", "source": "https://linkedin.com/in/pat",
            "kind": "founder", "warm": "cold",
            "opener": {"note": "Hi Pat, congrats on the Series A. I closed 54 sponsors for our club. "
                               "Would you have 10 minutes for a quick call?", "allow": ["10"]}}))
        self.assertEqual(r.returncode, 0, r.stderr)
        text = open(self.ppath()).read()
        self.assertIn("outreach: drafted", text)
        self.assertIn("career/research", text)
        r = self.run_cc("upsert-person", self.write_json("p.json", {
            "name": "Riley Mentor", "company": "Castor Labs", "source": "Work/People/Riley Mentor.md",
            "kind": "connector"}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(self.ppath("Riley Mentor")))
        riley = open(os.path.join(self.v, "Work/People/Riley Mentor.md")).read()
        self.assertIn("work/ops", riley)
        self.assertIn("Knows people at Castor Labs.", riley)
        self.assertIn("<!-- cc:career -->", riley)

    def test_mark_sent_moves_company(self):
        self.company()
        self.run_cc("upsert-person", self.write_json("p.json", {
            "name": "Pat Lee", "company": "Acme Robotics", "source": "https://linkedin.com/in/pat"}))
        r = self.run_cc("mark", "--person", "Pat Lee", "--outreach", "sent", "--date", "2026-10-20")
        self.assertEqual(r.returncode, 0, r.stderr)
        p = open(self.ppath()).read()
        self.assertIn("outreach: sent", p)
        self.assertIn("next_touch: 2026-10-27", p)
        self.assertIn("status: contacted", open(self.cpath()).read())

    # warm, status, lint
    def test_warm_finds_connections_and_labeled_folders(self):
        open(os.path.join(self.v, "Career/Job Search/Data/Connections.csv"), "w").write(
            "Notes:\n\"When exporting...\"\n\nFirst Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            "Ana,Ruiz,https://www.linkedin.com/in/example-ana,,Castor Labs Inc,Ops Lead,01 Jan 2026\n")
        out = self.run_cc("warm", "--company", "Castor Labs").stdout
        self.assertIn("[1st-degree] Ana Ruiz", out)
        self.assertIn("[coworker] Riley Mentor", out)

    def test_warm_no_hits_names_alumni(self):
        out = self.run_cc("warm", "--company", "Nobody Corp").stdout
        self.assertIn("State University", out)

    def test_status_and_lint(self):
        self.company()
        out = self.run_cc("status").stdout
        self.assertIn("Illinois share (all active notes) 100% (target 25%+)", out)
        r = self.run_cc("lint")
        self.assertEqual(r.returncode, 0, r.stdout)

    # applied, due, lint enums, import-tracker
    def person(self, name="Pat Lee", company="Acme Robotics"):
        return self.run_cc("upsert-person", self.write_json("p.json", {
            "name": name, "company": company, "source": "https://linkedin.com/in/x"}))

    def test_applied_idempotent(self):
        self.company()
        args = ("applied", "--company", "Acme Robotics", "--role", "BizOps Associate", "--url", "https://a.com/j",
                "--resume", "Resume_Ops.pdf", "--date", "2026-11-10")
        r = self.run_cc(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        first = open(self.cpath()).read()
        self.assertIn("status: applied", first)
        self.assertIn("next_date: 2026-11-20", first)
        self.assertIn("| BizOps Associate | 2026-11-10 | Resume_Ops.pdf | - | 2026-11-20 | https://a.com/j |", first)
        self.assertIn("applied: BizOps Associate (Resume_Ops.pdf)", first)
        self.assertLess(first.index("## Applications"), first.index("## Log"))
        r = self.run_cc(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("already recorded", r.stdout)
        self.assertEqual(open(self.cpath()).read(), first)

    def test_applied_never_moves_status_backward(self):
        self.company()
        self.run_cc("mark", "--company", "Acme Robotics", "--status", "interviewing", "--next-date", "2026-11-12",
                    "--next-action", "Onsite")
        r = self.run_cc("applied", "--company", "Acme Robotics", "--role", "Program Manager", "--date", "2026-11-10")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("status stays interviewing", r.stdout)
        text = open(self.cpath()).read()
        self.assertIn("status: interviewing", text)
        self.assertIn("next_date: 2026-11-12", text)
        self.assertIn("next_action: Onsite", text)
        self.assertIn("| Program Manager | 2026-11-10 |", text)

    def test_applied_also_url_and_missing_company(self):
        r = self.run_cc("applied", "--company", "Nova Space", "--role", "Business Operations Analyst",
                        "--url", "https://gh.example/1", "--also-url", "https://gh.example/2", "--date", "2026-11-10",
                        "--referral", "Ana Ruiz")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = open(self.cpath("Nova Space")).read()
        self.assertIn("seeded: true", text)
        self.assertIn("status: applied", text)
        self.assertIn("https://gh.example/1 |", text)
        self.assertIn("https://gh.example/2 |", text)
        self.assertEqual(text.count("| Business Operations Analyst | 2026-11-10 |"), 2)
        self.assertIn("2 locations", text)
        self.run_cc("applied", "--company", "Nova Space", "--role", "Business Operations Analyst",
                    "--url", "https://gh.example/2", "--date", "2026-11-11")
        self.assertEqual(open(self.cpath("Nova Space")).read(), text)

    def test_cadence_in_mark(self):
        self.company()
        self.person()
        self.run_cc("mark", "--person", "Pat Lee", "--outreach", "sent", "--event", "referral-asked",
                    "--date", "2026-11-10")
        self.assertIn("next_touch: 2026-11-13", open(self.ppath()).read())

    def test_due_merges_sources_and_respects_days(self):
        self.company()
        self.person()
        self.person("Sam Kim", "Beta Labs")
        today = "2026-11-10"
        self.run_cc("applied", "--company", "Acme Robotics", "--role", "BizOps Associate", "--date", "2026-11-01")
        self.run_cc("mark", "--company", "Acme Robotics", "--status", "applied", "--next-date", "2026-11-09",
                    "--next-action", "Ping recruiter")
        self.run_cc("mark", "--person", "Pat Lee", "--outreach", "sent", "--date", "2026-11-01")  # next_touch 11-08
        self.run_cc("mark", "--person", "Sam Kim", "--outreach", "sent", "--date", "2026-10-31",
                    "--next-touch", "2026-11-14")
        out = self.run_cc("due", today=today).stdout
        self.assertIn("3 items", out)
        self.assertIn("| loop | Pat Lee | EMAIL DUE: email naming BizOps Associate", out)
        self.assertLess(out.index("| person | Pat Lee"), out.index("| company | Acme Robotics | Ping recruiter"))
        self.assertNotIn("application", out)
        self.assertNotIn("Sam Kim", out)
        out = self.run_cc("due", "--days", "1", today=today).stdout
        self.assertIn("| application | Acme Robotics | BizOps Associate (applied 2026-11-01)", out)
        self.assertNotIn("Sam Kim", out)
        out = self.run_cc("due", "--days", "4", today=today).stdout
        self.assertIn("5 items", out)
        self.assertIn("Sam Kim", out)
        status = self.run_cc("status", today=today).stdout
        self.assertIn("Pat Lee", status)
        self.assertNotIn("Sam Kim", status)

    def test_due_applied_with_no_named_human(self):
        self.run_cc("applied", "--company", "Nova Space", "--role", "Analyst", "--date", "2026-11-05")
        out = self.run_cc("due", today="2026-11-10").stdout
        self.assertIn("2026-11-08 (2 days overdue) | application | Nova Space | Analyst: applied with no named human", out)

    def test_check_note_target_ask_and_hedges(self):
        cfg = os.path.join(self.tmp.name, "premium.toml")
        write_config(cfg, self.v)
        text = open(cfg).read().replace("premium = false", "premium = true")
        open(cfg, "w").write(text)
        short = "Hi Sam, the new test site is a smart move. Would you have 10 minutes for a call on hiring?"
        out = self.run_cc("check", "--kind", "note", stdin=short, config=cfg).stdout
        self.assertIn("aim for 250 to 300", out)
        out = self.run_cc("check", "--kind", "note", stdin="Hi Sam, open to connecting.", config=cfg).stdout
        self.assertIn("does not end on a question", out)
        out = self.run_cc("check", stdin="Hi Sam, it seems like the new site is big. Would you have 10 minutes?").stdout
        self.assertIn("hedge 'seems like'", out)
        r = self.run_cc("check", "--kind", "answer", stdin="I like building things.")
        self.assertIn("ok", r.stdout)

    # the apply loop
    def test_mark_loop_fields(self):
        self.company()
        self.person()
        pp = self.ppath()
        self.run_cc("mark", "--person", "Pat Lee", "--outreach", "sent", "--channel", "note", "--date", "2026-11-10")
        self.run_cc("mark", "--person", "Pat Lee", "--accepted", "--date", "2026-11-11")
        text = open(pp).read()
        for want in ("channel: note", "sent_on: 2026-11-10", "accepted_on: 2026-11-11", "next_touch: 2026-11-17"):
            self.assertIn(want, text)
        self.run_cc("mark", "--person", "Pat Lee", "--email", "sent", "--date", "2026-11-14")
        text = open(pp).read()
        self.assertIn("email_on: 2026-11-14", text)
        self.assertIn("last_contact: 2026-11-14", text)
        self.assertIn("next_touch: 2026-11-21", text)
        self.assertIn("sent_on: 2026-11-10", text)
        self.run_cc("mark", "--person", "Pat Lee", "--outreach", "replied", "--replied-via", "email",
                    "--proof", "sponsors-54", "--tier", "1", "--date", "2026-11-15")
        text = open(pp).read()
        for want in ("replied_on: 2026-11-15", "replied_via: email", "proof: sponsors-54", "tier: 1"):
            self.assertIn(want, text)
        r = self.run_cc("mark", "--person", "Pat Lee", "--channel", "pigeon")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("pigeon", open(pp).read())

    def test_loop_email_due_then_cleared(self):
        self.company()
        self.person()
        self.run_cc("mark", "--person", "Pat Lee", "--outreach", "sent", "--channel", "note", "--date", "2026-11-10")
        self.run_cc("applied", "--company", "Acme Robotics", "--role", "BizOps Associate",
                    "--resume", "Resume_Ops.pdf", "--date", "2026-11-11")
        out = self.run_cc("loop", today="2026-11-14").stdout
        self.assertIn("1 emails due", out)
        self.assertIn("| Pat Lee | Acme Robotics | note | 2026-11-10 | BizOps Associate 2026-11-11 (Resume_Ops.pdf)", out)
        self.assertIn("| 2026-11-14 | EMAIL DUE |", out)
        self.assertIn("0 emails due", self.run_cc("loop", today="2026-11-13").stdout)
        pp = self.ppath()
        text = open(pp).read().replace("sent_on: 2026-11-10\n", "")  # an older note without sent_on
        open(pp, "w").write(text)
        self.run_cc("mark", "--person", "Pat Lee", "--email", "sent", "--date", "2026-11-14")
        self.assertIn("sent_on: 2026-11-10", open(pp).read())
        out = self.run_cc("loop", today="2026-11-14").stdout
        self.assertIn("0 emails due", out)
        self.assertIn("2026-11-21", out)

    def test_loop_note_first_and_applied_cold(self):
        self.company()
        self.person()  # drafted, nobody contacted at Acme yet
        self.run_cc("applied", "--company", "Acme Robotics", "--role", "BizOps Associate", "--date", "2026-11-11")
        self.run_cc("applied", "--company", "Nova Space", "--role", "Analyst", "--date", "2026-11-11")
        out = self.run_cc("loop", today="2026-11-12").stdout
        self.assertIn("1 notes to send first, 1 applied cold", out)
        self.assertIn("| (nobody) | Nova Space |", out)
        rows = json.loads(self.run_cc("loop", "--json", today="2026-11-12").stdout)
        self.assertEqual({r["flag"] for r in rows}, {"NOTE FIRST", "APPLIED COLD"})
        due = self.run_cc("loop", "--due", "--applied-only", today="2026-11-12").stdout
        self.assertIn("NOTE FIRST", due)

    def test_metrics_rates(self):
        self.company(people=["Pat Lee", "Sam Kim"])
        self.person()
        self.person("Sam Kim")
        self.run_cc("mark", "--person", "Pat Lee", "--outreach", "sent", "--channel", "inmail", "--date", "2026-11-10")
        self.run_cc("mark", "--person", "Sam Kim", "--outreach", "sent", "--channel", "note", "--date", "2026-11-10")
        self.run_cc("mark", "--person", "Pat Lee", "--outreach", "replied", "--replied-via", "linkedin",
                    "--date", "2026-11-12")
        self.run_cc("applied", "--company", "Acme Robotics", "--role", "BizOps Associate", "--date", "2026-11-11")
        out = self.run_cc("metrics", today="2026-11-14").stdout
        self.assertIn("People contacted: 2. Replied: 1/2 (50%).", out)
        self.assertIn("Median days to reply: 2", out)
        self.assertIn("| inmail | 1 | 1/1 (100%) |", out)
        self.assertIn("| note | 1 | 0/1 (0%) |", out)
        self.assertIn("| with a contact or referral | 1 | 0/1 (0%) |", out)
        self.assertIn("Small sample", out)
        self.assertIn("People contacted: 0.", self.run_cc("metrics", "--since", "2026-11-11", today="2026-11-14").stdout)

    def test_infer_proof_from_config_and_style(self):
        cc = load_cc()
        cfg = cc.load_config(type("A", (), {"config": self.cfg})())
        cfg["proofs"] = [{"tag": "result-3rd", "pattern": r"3rd in the"},
                         {"tag": "sponsors-54", "pattern": r"\b54 (corporate )?sponsors"}]
        cc.configure(cfg)
        self.assertEqual(cc.infer_proof("I closed 54 sponsors for our club."), "sponsors-54")
        self.assertEqual(cc.infer_proof("We placed 3rd in the nation."), "result-3rd")
        self.assertEqual(cc.infer_proof("No proof here."), "none")
        cfg["proofs"] = []
        self.assertEqual(cc.infer_proof("I closed 54 sponsors."), "none")
        self.assertEqual(cc.infer_style("Hi Jo, what I find interesting about X is Y."), "my-take")
        self.assertEqual(cc.infer_style("Hi Jo, congrats on the round."), "fact-hook")

    def test_lint_flags_bad_channel(self):
        self.company()
        self.person()
        text = open(self.ppath()).read()
        open(self.ppath(), "w").write(re.sub(r"^outreach: .*$", "\\g<0>\nchannel: pigeon", text, count=1, flags=re.M))
        r = self.run_cc("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("channel 'pigeon'", r.stdout)

    def test_lint_flags_bad_enums(self):
        self.company()
        self.person()
        for path, old, new in ((self.ppath(), "outreach: not-contacted", "outreach: dropped"),
                               (self.cpath(), "status: research", "status: maybe")):
            text = open(path).read()
            open(path, "w").write(text.replace(old, new))
        r = self.run_cc("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("outreach 'dropped'", r.stdout)
        self.assertIn("status 'maybe'", r.stdout)
        self.assertIn("2 problems", r.stdout)

    def test_import_tracker_dry_run(self):
        self.company()
        tracker = os.path.join(self.v, "Career/Job Search/Application Tracker.md")
        open(tracker, "w").write(TRACKER)
        before = sorted(os.listdir(os.path.join(self.v, "Career/Job Search/Companies")))
        r = self.run_cc("import-tracker", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("7 rows parsed, 3 applied, 2 could not be parsed", out)
        self.assertIn('--company "Globex Signal" --role "Business Development Representative" --date 2026-11-10 '
                      '--resume "Resume_BD.pdf"', out)
        self.assertIn('--company "Acme Robotics" --role "BizOps Associate" --date 2026-11-08 '
                      '--url "https://a.com/j"', out)
        self.assertIn("(company note exists)", out)
        self.assertIn('--company "Initech Launch" --role "BD Engineer I, Springfield IL" --date 2026-11-09 '
                      '--resume "Resume_BD"', out)
        self.assertNotIn("Northwind", out.split("## Could not parse")[0])
        self.assertIn("applied row with no date: Hooli Forge", out)
        self.assertIn("3 cells, expected 7", out)
        self.assertNotIn("Umbrella", out)
        self.assertEqual(sorted(os.listdir(os.path.join(self.v, "Career/Job Search/Companies"))), before)
        self.assertEqual(self.run_cc("import-tracker").returncode, 2)

    def test_headline_prefers_funding_over_posting(self):
        cc = load_cc()
        sig = [{"date": "2026-10-20", "what": "Posted 3 ops roles", "url": "u1", "kind": "posting"},
               {"date": "2026-10-01", "what": "Raised $600M Series C", "url": "u2", "kind": "funding"}]
        cc.TODAY = cc.dt.date(2026, 11, 1)
        self.assertEqual(cc.headline_signal(sig)[0], "Raised $600M Series C")
        sig[0]["headline"] = True
        self.assertEqual(cc.headline_signal(sig)[0], "Posted 3 ops roles")
        self.assertEqual(cc.headline_signal([{"date": "2026-10-20", "what": "Posted roles", "url": "u"}])[0],
                         "Posted roles")

    def test_signal_kind_survives_merge(self):
        self.company(signals=[{"date": "2026-10-01", "what": "Raised Series A", "url": "https://a.com/1",
                               "kind": "funding"}])
        self.company(signals=[{"date": "2026-10-20", "what": "Posted roles", "url": "https://a.com/3",
                               "kind": "posting"}])
        text = open(self.cpath()).read()
        self.assertIn("| funding |", text)

    def test_min_years(self):
        cc = load_cc()
        self.assertEqual(cc.min_years("You have 5+ years of experience in finance"), 5)
        self.assertEqual(cc.min_years("2-4 years of relevant work experience. 10 years of operations exp"), 2)
        self.assertIsNone(cc.min_years("We were founded 3 years ago."))
        self.assertNotIn("lunar", cc.slug_guesses("Lunar Outpost"))

    def test_classify_titles_and_home_region(self):
        cc = load_cc()
        cc.configure(cc.load_config(type("A", (), {"config": self.cfg, "vault": None})()))
        self.assertEqual(cc.classify_title("Business Operations Associate")[:2], ("ops", "entry"))
        self.assertEqual(cc.classify_title("Associate Product Manager")[0], "pm")
        self.assertEqual(cc.classify_title("Senior Software Engineer")[0], None)
        self.assertEqual(cc.classify_title("Technical Field Engineer")[0], None)
        self.assertEqual(cc.classify_title("Head of Partnerships")[1], "senior")
        self.assertEqual(cc.classify_title("2027 Early Career Business Operations")[1], "entry")
        self.assertTrue(cc.classify_title("Chief of Staff", "Chicago, IL")[2])
        self.assertFalse(cc.classify_title("Chief of Staff", "Austin, TX")[2])


class SweepFilters(unittest.TestCase):
    def test_non_us_and_noise(self):
        cc = load_cc()
        self.assertTrue(re.search(cc.NON_US_RE, "remote - netherlands"))
        self.assertFalse(re.search(cc.NON_US_RE, "austin, tx"))
        self.assertTrue(re.search(cc.SWEEP_NOISE_RE, "talent operations specialist"))
        self.assertFalse(re.search(cc.SWEEP_NOISE_RE, "business operations analyst"))

    def test_bamboo_and_ashby_parsers(self):
        cc = load_cc()
        j = cc.bamboo_job("acme", {"id": "7", "jobOpeningName": "BD Engineer",
                                   "location": {"city": "Springfield", "state": "Illinois"}},
                          {"jobOpeningName": "BD Engineer", "datePosted": "2026-09-11", "compensation": "$90,000 to $115,000",
                           "minimumExperience": "Entry-level", "description": "<p>4+ years of experience in DoD BD</p>"})
        self.assertEqual(j["url"], "https://acme.bamboohr.com/careers/7")
        self.assertEqual(j["location"], "Springfield, Illinois")
        self.assertEqual(str(j["posted"]), "2026-09-11")
        self.assertEqual(cc.min_years(j["text"]), 4)
        lines = cc.bamboo_form_lines({"email": {"isRequired": True, "label": "Email"},
                                      "desiredPay": {"isRequired": True, "label": "Desired Pay"},
                                      "customQuestions": [{"isRequired": True, "question": "Why us?", "options": []}]})
        self.assertEqual(lines, ["- [required] Desired Pay", "- [required] Why us?"])
        jp = {"applicationForm": {"sections": [{"fieldEntries": [
            {"isRequired": True, "field": {"path": "_systemfield_name", "title": "Name"}},
            {"isRequired": False, "field": {"path": "x", "title": "Portfolio", "selectableValues": []}}]}]}}
        self.assertEqual(cc.ashby_form_lines(jp), ["- [optional] Portfolio"])

    def test_transcript_flag(self):
        cc = load_cc()
        self.assertEqual(cc.transcript_flag("- [required] Why us?\n- [optional] Portfolio"), "")
        self.assertIn("required: skip", cc.transcript_flag("- [required] Unofficial transcript"))
        self.assertIn("optional", cc.transcript_flag("- [optional] Transcript (PDF)"))
        self.assertIn("required", cc.transcript_flag("- Upload your transcript"))  # Lever: no marker

    def test_seed_boards_are_well_formed(self):
        seed = os.path.join(os.path.dirname(HERE), "data", "ats.tsv")
        rows = [l.split("\t") for l in open(seed, encoding="utf-8").read().splitlines()]
        self.assertEqual(rows[0][:3], ["company", "ats", "slug"])
        names = [r[0].lower() for r in rows[1:]]
        self.assertEqual(len(names), len(set(names)), "duplicate company in seed ats.tsv")
        for r in rows[1:]:
            self.assertIn(r[1], ("greenhouse", "lever", "ashby", "bamboohr"), r)
            self.assertRegex(r[2], r"^[A-Za-z0-9_.-]+$")


if __name__ == "__main__":
    unittest.main(verbosity=1, warnings="ignore")
