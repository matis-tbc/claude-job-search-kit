#!/usr/bin/env python3
"""career-coach helper CLI. Stdlib only.

Subcommands:
  doctor          check vault paths, Fact Sheet, data files, search phase (--net also probes ATS APIs)
  facts           print usable (verified) facts from the Fact Sheet; --all shows blocked rows too
  check           lint an opener: em dashes, length, and every number against the Fact Sheet
  jobs            list open roles for a company from Greenhouse, Lever or Ashby with posted dates
  sweep           every board in Data/ats.tsv at once: business roles posted in the last N days
  questions       the application form questions for one Greenhouse or Lever posting
  warm            find warm paths into a company from the vault, LinkedIn export and sponsor notes
  known           list company notes already in the vault with last update and status
  upsert-company  create or update a company note from JSON (keeps human-owned fields and Notes)
  upsert-person   create or update a person note from JSON (refuses rows without a source URL)
  log-run         write a run log note from a markdown body
  status          pipeline summary: stages, home-region share, due actions, follow-ups
  mark            record what the user did: --person X --outreach sent, or --company X --status talking
  applied         record an application on the company note (status, follow-up date, Applications block)
  due             one list of company next_date, person next_touch and application follow-ups due within N days
  lint            scan skill-written notes for em dashes, missing sources, broken markers and bad enum values
  import-tracker  --dry-run: print the `applied` calls the Application Tracker table implies
  init            write a starter config file (never overwrites one that exists)

Config: --config, else $JOB_KIT_CONFIG, else ~/.config/job-search-kit/config.toml.
Vault root: --vault, else $CAREER_VAULT, else [paths] vault in the config.
Every write goes through this file so formats stay identical across runs.
"""
import argparse
import csv
import datetime as dt
import glob
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

TODAY = dt.date.fromisoformat(os.environ["CAREER_TODAY"]) if os.environ.get("CAREER_TODAY") else dt.date.today()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) job-search-kit/1.0"
DEFAULT_CONFIG = "~/.config/job-search-kit/config.toml"


# ---------------------------------------------------------------- config

def _toml_value(raw, where):
    """One TOML value from the subset the kit uses: strings, ints, floats, bools, flat arrays."""
    v = raw.strip()
    if v.startswith('"'):
        m = re.match(r'"((?:[^"\\]|\\.)*)"', v)
        if not m:
            raise ValueError(f"{where}: unterminated string")
        return json.loads('"' + m.group(1) + '"')
    if v.startswith("'"):
        end = v.find("'", 1)
        if end == -1:
            raise ValueError(f"{where}: unterminated string")
        return v[1:end]
    if v.startswith("["):
        inner, items, buf, q = v[1:], [], "", None
        depth_close = None
        for i, ch in enumerate(inner):
            if q:
                buf += ch
                if ch == q and (q == "'" or buf[-2:-1] != "\\"):
                    q = None
                continue
            if ch in "\"'":
                q = ch
                buf += ch
            elif ch == ",":
                if buf.strip():
                    items.append(_toml_value(buf, where))
                buf = ""
            elif ch == "]":
                depth_close = i
                break
            elif ch == "#":
                break
            else:
                buf += ch
        if depth_close is None:
            raise ValueError(f"{where}: arrays must open and close on one line")
        if buf.strip():
            items.append(_toml_value(buf, where))
        return items
    v = v.split("#", 1)[0].strip()
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"[+-]?\d+", v.replace("_", "")):
        return int(v.replace("_", ""))
    if re.fullmatch(r"[+-]?\d+\.\d+", v):
        return float(v)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return dt.date.fromisoformat(v)
    raise ValueError(f"{where}: cannot read value '{v}' (quote strings)")


def parse_toml_subset(text):
    """Fallback for Python < 3.11 (no tomllib). Supports [table], [a.b], [[array-of-tables]],
    key = value with the values above, and # comments. That is all config.example.toml uses."""
    data = {}
    cur = data
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.fullmatch(r"\[\[\s*([A-Za-z0-9_.\-]+)\s*\]\](\s*#.*)?", s)
        if m:
            *parents, last = m.group(1).split(".")
            node = data
            for p in parents:
                node = node.setdefault(p, {})
            node.setdefault(last, []).append({})
            cur = node[last][-1]
            continue
        m = re.fullmatch(r"\[\s*([A-Za-z0-9_.\-]+)\s*\](\s*#.*)?", s)
        if m:
            node = data
            for p in m.group(1).split("."):
                node = node.setdefault(p, {})
                if isinstance(node, list):
                    node = node[-1]
            cur = node
            continue
        m = re.match(r'^([A-Za-z0-9_\-]+|"[^"]+")\s*=\s*(.+)$', s)
        if not m:
            raise ValueError(f"line {n}: expected key = value, got '{s[:60]}'")
        cur[m.group(1).strip('"')] = _toml_value(m.group(2), f"line {n}")
    return data


def load_toml(path):
    text = open(path, encoding="utf-8").read()
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(text)
    except ImportError:
        return parse_toml_subset(text)


CONFIG_DEFAULTS = {
    "profile": {"name": "", "first_name": "", "school": "", "school_short": "", "degrees": [],
                "graduation": "", "start_date": "", "home_city": "", "voice_samples": []},
    "paths": {
        "vault": "",
        "fact_sheet": "Career/Resume/Fact Sheet.md",
        "job_search": "Career/Job Search",
        "people": "People",
        "resume_dir": "Career/Resume/Ready to Send",
        "standard_answers": "Career/Job Search/Standard Answers.md",
        "next_session": "Career/Job Search/Next Session.md",
        "protected": [],
    },
    "search": {
        "home_region": "", "home_region_share": 0.25, "home_region_pattern": "",
        "fun_cities": [], "stage_band": "Series A to C", "signal_days": 60,
        "max_years": 2, "families": ["ops", "bd", "fin", "pm", "gtm"],
    },
    "linkedin": {"premium": False, "note_limit": 0},
    "warm": {"people_dirs": {}, "org_contact_globs": [], "prenamed_glob": "", "alumni": []},
    "lanes": [],
    "phases": [],
}


def config_path(args=None):
    return os.path.expanduser(getattr(args, "config", None) or os.environ.get("JOB_KIT_CONFIG") or DEFAULT_CONFIG)


def load_config(args=None, required=True):
    """Config dict with defaults filled in. Exits with a fix line when the file is missing or unreadable."""
    path = config_path(args)
    raw = {}
    if os.path.exists(path):
        try:
            raw = load_toml(path)
        except Exception as e:
            die(f"config {path} could not be read: {e}. Fix the line, or compare with config.example.toml.")
    elif required and not (getattr(args, "vault", None) or os.environ.get("CAREER_VAULT")):
        die(f"no config at {path}. Fix: run `cc.py init` and edit it, or set JOB_KIT_CONFIG.")
    cfg = {}
    for k, default in CONFIG_DEFAULTS.items():
        if isinstance(default, dict):
            cfg[k] = dict(default, **(raw.get(k) or {}))
        else:
            cfg[k] = raw.get(k, default)
    cfg["_path"] = path
    cfg["_exists"] = os.path.exists(path)
    return cfg


CFG = None  # set in main(); tests that import cc call configure() themselves


def configure(cfg):
    """Derive every path, pattern and label the commands use from one config dict."""
    global CFG, PATHS, PEOPLE_DIRS, PEOPLE_LABELS, ORG_GLOBS, PRENAMED_GLOB, HOME_RE, HOME_NAME, HOME_SHARE
    CFG = cfg
    p, js = cfg["paths"], cfg["paths"]["job_search"].rstrip("/")
    PATHS = {
        "fact_sheet": p["fact_sheet"],
        "companies": f"{js}/Companies",
        "runs": f"{js}/Runs",
        "data": f"{js}/Data",
        "people": p["people"].rstrip("/"),
        "target_companies": f"{js}/Target Companies.md",
        "connectors": f"{js}/Connectors.md",
        "tracker": f"{js}/Application Tracker.md",
        "standard_answers": p["standard_answers"],
        "next_session": p["next_session"],
        "resume_dir": p["resume_dir"],
    }
    labels = dict(cfg["warm"].get("people_dirs") or {})
    PEOPLE_LABELS = {v.rstrip("/"): k for k, v in labels.items()}
    PEOPLE_DIRS = [PATHS["people"]] + [d for d in PEOPLE_LABELS if d != PATHS["people"]]
    ORG_GLOBS = list(cfg["warm"].get("org_contact_globs") or [])
    PRENAMED_GLOB = os.path.expanduser(os.environ.get("CAREER_PRENAMED_GLOB") or cfg["warm"].get("prenamed_glob") or "")
    s = cfg["search"]
    HOME_NAME = s.get("home_region") or "home region"
    HOME_SHARE = float(s.get("home_region_share") or 0)
    HOME_RE = s.get("home_region_pattern") or (re.escape(s["home_region"].lower()) if s.get("home_region") else r"(?!x)x")
    return cfg


PATHS, PEOPLE_DIRS, PEOPLE_LABELS, ORG_GLOBS, PRENAMED_GLOB = {}, [], {}, [], ""
HOME_RE, HOME_NAME, HOME_SHARE = r"(?!x)x", "home region", 0.25


def profile(key, fallback=""):
    return (CFG or {}).get("profile", {}).get(key) or fallback

COMPANY_STATUSES = ["research", "reach-out", "contacted", "talking", "applied",
                    "interviewing", "offer", "closed", "parked"]
OUTREACH_STATUSES = ["not-contacted", "drafted", "sent", "replied", "meeting", "dormant", "closed"]
HUMAN_COMPANY_KEYS = ["status", "next_action", "next_date", "priority"]
HUMAN_PERSON_KEYS = ["outreach", "last_contact", "next_touch"]

# One follow-up cadence, read by mark, applied, status and due.
# event: (days after the event, what to do then)
CADENCE = {
    "referral-asked": (3, "no answer on the referral: apply anyway"),
    "applied-no-human": (3, "applied with no named human: find and stage one person"),
    "note-sent": (7, "note not accepted: InMail or Open Profile message, or the sourced follow-up email"),
    "note-accepted": (1, "send the TLDR message"),
    "application": (10, "no response: follow up with the contact, naming the req"),
    "pending-withdraw": (14, "connection still pending: withdraw it"),
    "second-touch": (24, "last polite touch, then mark dormant"),
    "interview": (0, "send the thank-you note"),
}


def cadence_date(event, day):
    """ISO date when the next step after `event` on `day` (date or YYYY-MM-DD) is due."""
    d = day if isinstance(day, dt.date) else dt.date.fromisoformat(str(day))
    return (d + dt.timedelta(days=CADENCE[event][0])).isoformat()

EM_DASH_RE = re.compile("[\u2014\u2015]|\\s\u2013\\s")


def die(msg, code=2):
    print(f"[career-coach] {msg}", file=sys.stderr)
    sys.exit(code)


def vault_root(args):
    root = getattr(args, "vault", None) or os.environ.get("CAREER_VAULT") or (CFG or {}).get("paths", {}).get("vault")
    if not root:
        die("no vault set. Fix: set [paths] vault in the config (an Obsidian vault or any plain folder), "
            "or pass --vault.")
    root = os.path.expanduser(root)
    if not os.path.isdir(root):
        die(f"vault not found at {root}. Fix: create the folder, or correct [paths] vault in {config_path()}.")
    return root


def vp(root, key):
    return os.path.join(root, PATHS[key])


DEFAULT_PHASE_ADVICE = {
    "relationship": "Build relationships. Ask for a short call to learn how the team hires for this kind of role "
                    "and when reqs for your start date open. If a matching req is already open, use the "
                    "application ask for that role instead.",
    "application": "The application window. Name the specific open req, ask for a referral or a conversation "
                   "with the hiring manager, and say when you can start.",
    "close": "Closing offers. Outreach is follow-up, thank-yous and negotiation, not new prospecting.",
}


def search_phase(day=None):
    """(name, advice) from the config's [[phases]] list: the first phase whose `until` date is on or after
    `day`; a phase with no `until` is the last one. With no phases configured, every day is 'application'."""
    day = day or TODAY
    phases = (CFG or {}).get("phases") or []
    for ph in phases:
        until = ph.get("until")
        if isinstance(until, str) and until:
            until = dt.date.fromisoformat(until)
        if not until or day <= until:
            name = ph.get("name", "application")
            return name, ph.get("advice") or DEFAULT_PHASE_ADVICE.get(name, "")
    if phases:
        name = phases[-1].get("name", "close")
        return name, phases[-1].get("advice") or DEFAULT_PHASE_ADVICE.get(name, "")
    return "application", DEFAULT_PHASE_ADVICE["application"]


# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm = text[4:end]
            body = text[end + 4:]
            if body.startswith("\n"):
                body = body[1:]
            return fm, body
    return None, text


def parse_scalar(v):
    v = v.strip()
    if v == "" or v == "null" or v == "~":
        return ""
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        inner = v[1:-1]
        return inner.replace('\\"', '"') if v[0] == '"' else inner.replace("''", "'")
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    if v.startswith("[") and v.endswith("]"):
        return [parse_scalar(x) for x in v[1:-1].split(",") if x.strip()]
    return v


def parse_frontmatter(fm):
    """Small YAML subset: key: scalar, key: [a, b], and key:\\n  - item lists."""
    data, key = {}, None
    for line in (fm or "").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s+-\s*(.*)$", line)
        if m and key is not None:
            if not isinstance(data.get(key), list):
                data[key] = []
            item = parse_scalar(m.group(1))
            if item != "":
                data[key].append(item)
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            data[key] = parse_scalar(m.group(2)) if m.group(2).strip() else []
    for k, v in list(data.items()):
        if v == []:
            data[k] = ""
    return data


def yaml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "":
        return ""
    if re.search(r"[:#\[\]{},&*!|>'\"%@`]|^[-?\s]|\s$", s) or s.lower() in ("true", "false", "null", "yes", "no") \
            or re.fullmatch(r"-?\d+(\.\d+)?", s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def dump_frontmatter(data, order):
    lines = ["---"]
    keys = [k for k in order if k in data] + [k for k in data if k not in order]
    for k in keys:
        v = data[k]
        if isinstance(v, list):
            if not v:
                lines.append(f"{k}: []")
                continue
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {yaml_value(item)}")
        else:
            val = yaml_value(v)
            lines.append(f"{k}: {val}" if val != "" else f"{k}:")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- managed blocks

def block(name, content):
    return f"<!-- cc:{name} -->\n{content.rstrip()}\n<!-- /cc:{name} -->"


def get_block(body, name):
    m = re.search(rf"<!-- cc:{re.escape(name)} -->\n(.*?)\n?<!-- /cc:{re.escape(name)} -->", body, re.S)
    return m.group(1) if m else None


def set_block(body, name, content):
    pat = re.compile(rf"<!-- cc:{re.escape(name)} -->\n.*?<!-- /cc:{re.escape(name)} -->", re.S)
    new = block(name, content)
    if pat.search(body):
        return pat.sub(lambda _: new, body, count=1)
    return None


# ---------------------------------------------------------------- names

SUFFIXES = {"inc", "llc", "ltd", "corp", "corporation", "co", "company", "the", "technologies",
            "technology", "industries", "labs", "systems", "group", "holdings", "hq"}


def norm_company(name):
    s = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower().replace("&", " and "))
    toks = [t for t in s.split() if t not in SUFFIXES]
    return " ".join(toks)


def company_matches(target, candidate):
    a, b = norm_company(target), norm_company(candidate)
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 4 and re.search(rf"(^| ){re.escape(short)}( |$)", long_) is not None


def text_mentions(text, company):
    core = norm_company(company)
    if not core:
        return False
    variants = {company.strip()}
    if core:
        variants.add(core)
    for v in variants:
        if len(v) <= 5:
            # short names like "Acme" or "Zeta": case sensitive, capitalized, whole word
            cap = v[:1].upper() + v[1:]
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(cap)}(?![A-Za-z0-9])", text):
                return True
        elif re.search(rf"(?<![a-z0-9]){re.escape(v.lower())}(?![a-z0-9])", text.lower()):
            return True
    return False


def safe_filename(name):
    s = re.sub(r'[\\/:*?"<>|#^\[\]]', " ", name).strip()
    return re.sub(r"\s+", " ", s)


# ---------------------------------------------------------------- facts

def read_fact_sheet(root):
    path = os.environ.get("CAREER_FACT_SHEET") or vp(root, "fact_sheet")
    if not os.path.exists(path):
        die(f"Fact Sheet not found at {path}.")
    rows, section, header = [], "", None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("## "):
            section, header = line[3:].strip(), None
            continue
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if header is None:
            header = [c.lower() for c in cells]
            continue
        rec = dict(zip(header, cells))
        status_raw = rec.get("status", "")
        status = re.sub(r"\*", "", status_raw).strip()
        sl = status.lower()
        usable = (sl.startswith("verified") or sl == "decided") and "unconfirmed" not in sl and "conflict" not in sl
        kind = "usable" if usable else ("conflict" if "conflict" in sl else
                                        "estimate" if "estimate" in sl else
                                        "blocked" if re.search(r"blocked|retired|do not print", sl) else "unconfirmed")
        rows.append({
            "section": section,
            "fact": rec.get("fact", ""),
            "value": rec.get("value to use", rec.get("value", "")),
            "status": status,
            "note": rec.get("source / note", rec.get("source", "")),
            "kind": kind,
        })
    return rows


NUM_RE = re.compile(r"(€|\$)?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?(k|K|m|M|B|%|x|st|nd|rd|th|\+)?(?![A-Za-z0-9])")


def number_keys(text):
    """Return (display, key) for each number. key normalizes $225K -> 225000, 3rd -> 3, 4x -> 4x, 20% -> 20%."""
    out = []
    for m in NUM_RE.finditer(text or ""):
        cur, num, suf = m.group(1), m.group(2), m.group(3) or ""
        try:
            val = float(num.replace(",", ""))
        except ValueError:
            continue
        mult = {"k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6, "B": 1e9}.get(suf, 1)
        val *= mult
        key = str(int(val)) if val == int(val) else str(val)
        if suf in ("%", "x"):
            key += suf
        out.append((m.group(0).strip(), key))
    return out


STOP = {"the", "and", "for", "with", "before", "after", "took", "value", "total", "dates", "title", "titles",
        "count", "result", "share", "used", "note", "from", "that", "this", "your", "their"}
# When a blocked row's fact names one of these words, a draft that uses any of the listed words near the
# same number is treated as talking about that row. Extend it for your own Fact Sheet if a blocked number
# slips through.
SYNONYMS = {"size": ["person", "people", "members", "engineers", "students", "team"],
            "raised": ["raise", "raised", "funding", "brought in"],
            "budget": ["budget", "grew", "growth"],
            "revenue": ["revenue", "sales", "arr", "bookings"],
            "events": ["events", "shows", "attendees"],
            "tests": ["tests", "trials", "experiments"],
            "users": ["users", "customers", "people"],
            "clients": ["clients", "customers", "accounts"]}


def row_keywords(r):
    words = [w for w in re.findall(r"[a-z][a-z\-]{3,}", r["fact"].lower()) if w not in STOP]
    extra = []
    for w in words + re.findall(r"[a-z]+", r["fact"].lower()):
        extra += SYNONYMS.get(w, [])
    return set(words + extra)


def fact_number_sets(rows):
    """usable: number keys found in verified values. blocked: per non-usable row, its number keys
    (value and note columns) with the words that signal a draft is talking about that fact."""
    usable, blocked = set(), []
    for r in rows:
        keys = {k for _, k in number_keys(r["value"])}
        if r["kind"] == "usable":
            usable |= keys
        else:
            keys |= {k for _, k in number_keys(r["note"])}
            keys = {k for k in keys if not (k.isdigit() and 1990 <= int(k) <= 2035)}
            blocked.append((keys, row_keywords(r), f"{r['kind']}: {r['section']} / {r['fact']}"))
    return usable, blocked


def cmd_facts(args):
    rows = read_fact_sheet(vault_root(args))
    show = rows if args.all else [r for r in rows if r["kind"] == "usable"]
    if args.json:
        print(json.dumps(show, indent=2))
        return
    section = None
    for r in show:
        if r["section"] != section:
            section = r["section"]
            print(f"\n## {section}")
        flag = "" if r["kind"] == "usable" else f"  [BLOCKED: {r['kind']}]"
        print(f"- {r['fact']}: {r['value']}{flag}")
    usable = sum(1 for r in rows if r["kind"] == "usable")
    print(f"\n{usable} usable facts, {len(rows) - usable} blocked (conflict, estimate, unconfirmed or blocked).")


# ---------------------------------------------------------------- check

SLOP = ["hope this finds you well", "hope this message finds you", "i'm passionate", "i am passionate",
        "delve", "game-changer", "game changer", "synergy", "pick your brain", "i came across your profile",
        "thrilled", "leverage my", "esteemed", "i am writing to", "touch base", "circle back",
        "fast-paced environment", "rockstar", "ninja", "excited to connect"]
LIMITS = {"note": ("chars", 200), "message": ("words", 120), "email": ("words", 160), "answer": ("words", 300)}


def note_limit():
    """LinkedIn connection-note limit: 200 characters on a free account, 300 with Premium ([linkedin] in config)."""
    li = (CFG or {}).get("linkedin") or {}
    return int(li.get("note_limit") or (300 if li.get("premium") else 200))


def lint_text(text, kind, rows, allow=(), strict=False):
    """Errors and warnings for one draft. strict=True (resume bullets, form answers, essays) turns every
    number that is not on a usable Fact Sheet row, not --allow'ed and not a year or a time ask into an ERROR."""
    errors, warns = [], []
    if EM_DASH_RE.search(text):
        errors.append("contains an em dash (or a spaced en dash). Rewrite with a comma, period or colon.")
    unit, limit = LIMITS.get(kind, ("words", 160))
    if kind == "note":
        limit = note_limit()
    size = len(text) if unit == "chars" else len(re.findall(r"\b\w[\w'’-]*\b", text))
    if size > limit:
        errors.append(f"{kind} is {size} {unit}; limit is {limit}.")
    usable, blocked = fact_number_sets(rows)
    allow_keys = set()
    for a in allow:
        allow_keys |= {k for _, k in number_keys(a)} or {a}
    for m in NUM_RE.finditer(text):
        disp = m.group(0).strip()
        key = number_keys(disp)[0][1] if number_keys(disp) else disp
        bare = key.rstrip("%x")
        if key in allow_keys:
            continue
        ctx = text[max(0, m.start() - 45): m.end() + 45].lower()
        hit = next((label for keys, kws, label in blocked
                    if key in keys and any(re.search(rf"\b{re.escape(w)}", ctx) for w in kws)), None)
        if hit:
            errors.append(f"'{disp}' reads as the {hit} row on the Fact Sheet. Use a verified number or drop it "
                          f"(--allow '{disp}' only if it is about something else).")
            continue
        if key in usable:
            continue
        only_blocked = next((label for keys, _, label in blocked if key in keys), None)
        if only_blocked:
            errors.append(f"'{disp}' only appears in a {only_blocked} row on the Fact Sheet. Drop it.")
            continue
        if bare.isdigit() and 1990 <= int(bare) <= 2035:
            continue  # years
        if re.match(r"\s*(-|\s)?(min|minute|minutes|hour|hours|day|days|week|weeks)\b", text[m.end():], re.I):
            continue  # time asks like 15 minutes
        msg = (f"'{disp}' is not on the Fact Sheet. Fine only if it is a sourced fact about the "
               f"company (pass --allow '{disp}'); otherwise remove it.")
        (errors if strict else warns).append(msg)
    low = text.lower()
    for p in SLOP:
        if p in low:
            warns.append(f"stock phrase '{p}'. Say it the way you would say it out loud.")
    return errors, warns, size


def cmd_check(args):
    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    text = text.strip()
    rows = read_fact_sheet(vault_root(args))
    errors, warns, size = lint_text(text, args.kind, rows, args.allow or [], strict=args.strict)
    unit = LIMITS.get(args.kind, ("words",))[0]
    print(f"{args.kind}: {size} {unit}")
    for e in errors:
        print(f"ERROR {e}")
    for w in warns:
        print(f"WARN  {w}")
    if not errors and not warns:
        print("ok")
    sys.exit(1 if errors else 0)


# ---------------------------------------------------------------- jobs

FAMILIES = [
    ("ops", r"business operations|bizops|biz ops|strategy (and|&) operations|strategy & ops|special projects|"
            r"chief of staff|founder'?s associate|strategic (initiatives|projects)|operations (associate|analyst|"
            r"manager|lead|generalist)|program manag|technical program|production planner|supply chain|"
            r"\bprocurement\b|sourcing|business analyst|strategy associate|corporate development|"
            r"deployment strategist|operations\b"),
    ("bd", r"business development|partnerships?\b|alliances|commercial (manager|lead|associate)|"
           r"government relations|capture manager|strategic sales|growth (associate|lead|manager)"),
    ("fin", r"strategic finance|fp&a|finance (and|&) strategy|finance associate|bizfin|investment associate"),
    ("pm", r"product manag|\bapm\b|associate product|product operations|product owner|technical product"),
    ("gtm", r"account executive|\bae\b|sales development|\bsdr\b|\bbdr\b|go[- ]to[- ]market|\bgtm\b|"
            r"solutions (engineer|consultant|architect)|forward[- ]deployed|customer success|sales\b|"
            r"deployment (engineer|lead)"),
]
EXCLUDE = r"software engineer|swe\b|firmware|electrical engineer|mechanical engineer|technician|machinist|" \
          r"scientist|researcher|attorney|counsel|accountant|nurse|recruiter|designer|welder|intern\b|" \
          r"internship|co-?op\b|data engineer|devops|security engineer|test engineer|field engineer|workplace|" \
          r"facilities|\bit operations|security operations|people operations|payroll|\bhr\b|janitor|custodian"
SENIOR = r"\bsenior\b|\bsr\.?\b|\bstaff\b|\bprincipal\b|\bdirector\b|\bhead of\b|\bvp\b|vice president|" \
         r"\blead\b|\bchief\b(?! of staff)|\bii\b|\biii\b|\biv\b|manager,? (senior|sr)"
ENTRY = r"new grad|university grad|early career|entry|associate|analyst|\bjunior\b|\bjr\b|\bi\b|" \
        r"rotational|generalist|fellow|\b20[2-3]\d\b|graduate"


def classify_title(title, location=""):
    t = title.lower()
    family = None
    for name, pat in FAMILIES:
        if re.search(pat, t):
            family = name
            break
    if family is None or (re.search(EXCLUDE, t) and family not in ("pm",)
                          and not re.search(r"program manag|product manag|business|partner", t)):
        family = None
    seniority = "senior" if re.search(SENIOR, t) else ("entry" if re.search(ENTRY, t) else "mid")
    home = bool(re.search(HOME_RE, (location or "").lower()))
    return family, seniority, home


def http_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def http_post_json(url, payload, timeout=15):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"User-Agent": UA, "Accept": "application/json",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def http_text(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def iso_date(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def strip_html(s):
    s = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", s or "", flags=re.I)
    return re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:(?:-|to|\u2013)\s*\d{1,2}\s*\+?\s*)?years?(?:'|’)?(?!\s+(?:ago|old))"
                      r"(?=[^.\n]{0,80}?\b(?:experience|exp|in|of|working|as|managing|leading|building|owning|at)\b)",
                      re.I)


def min_years(text):
    """Smallest 'N years of experience' requirement in a posting, or None."""
    vals = [int(m.group(1)) for m in YEARS_RE.finditer(text or "") if int(m.group(1)) <= 20]
    return min(vals) if vals else None


def fetch_board(ats, slug):
    jobs = []
    if ats == "greenhouse":
        d = http_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
        for j in d.get("jobs", []):
            jobs.append({"title": j.get("title", "").strip(), "location": (j.get("location") or {}).get("name", ""),
                         "posted": iso_date(j.get("first_published") or j.get("updated_at")),
                         "url": j.get("absolute_url", ""), "board_company": j.get("company_name", ""),
                         "id": str(j.get("id", "")),
                         "text": strip_html(html.unescape(j.get("content") or ""))})
    elif ats == "lever":
        d = http_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        for j in d if isinstance(d, list) else []:
            cats = j.get("categories") or {}
            created = j.get("createdAt")
            jobs.append({"title": j.get("text", "").strip(),
                         "location": ", ".join(cats.get("allLocations") or [cats.get("location", "")]),
                         "posted": dt.date.fromtimestamp(created / 1000) if created else None,
                         "url": j.get("hostedUrl", ""), "id": j.get("id", ""),
                         "text": (j.get("descriptionPlain") or "") + "\n" + "\n".join(
                             strip_html(x.get("content", "")) for x in j.get("lists") or [])})
    elif ats == "ashby":
        d = http_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
        for j in d.get("jobs", []):
            if j.get("isListed") is False:
                continue
            locs = [j.get("location", "")] + [x.get("location", "") for x in j.get("secondaryLocations") or []]
            comp = (j.get("compensation") or {}).get("compensationTierSummary") or ""
            jobs.append({"title": j.get("title", "").strip(), "location": "; ".join(l for l in locs if l),
                         "posted": iso_date(j.get("publishedAt")), "url": j.get("jobUrl", ""), "id": j.get("id", ""),
                         "comp": comp, "remote": j.get("isRemote"),
                         "text": j.get("descriptionPlain") or strip_html(j.get("descriptionHtml") or "")})
    elif ats == "bamboohr":
        d = http_json(f"https://{slug}.bamboohr.com/careers/list")
        for j in d.get("result", []):
            jid = str(j.get("id", ""))
            try:
                det = (http_json(f"https://{slug}.bamboohr.com/careers/{jid}/detail").get("result") or {}).get(
                    "jobOpening") or {}
            except Exception:
                det = {}
            jobs.append(bamboo_job(slug, j, det))
    else:
        die(f"unknown ATS '{ats}'. Use greenhouse, lever, ashby or bamboohr.")
    return jobs


def bamboo_job(slug, j, det):
    """One BambooHR list row plus its detail record -> the common job dict."""
    loc = det.get("location") or j.get("location") or {}
    where = ", ".join(x for x in (loc.get("city"), loc.get("state")) if x)
    if j.get("isRemote"):
        where = (where + "; Remote").strip("; ")
    jid = str(j.get("id", ""))
    text = strip_html(html.unescape(det.get("description") or ""))
    if det.get("minimumExperience"):
        text = f"Minimum experience: {det['minimumExperience']}\n" + text
    return {"title": (det.get("jobOpeningName") or j.get("jobOpeningName") or "").strip(), "location": where,
            "posted": iso_date(det.get("datePosted")), "url": f"https://{slug}.bamboohr.com/careers/{jid}",
            "id": jid, "comp": det.get("compensation") or "", "text": text}


ATS_LINK_RE = re.compile(
    r"(?:boards|job-boards)\.greenhouse\.io/(?:embed/job_board\?for=)?([A-Za-z0-9_-]+)|"
    r"boards-api\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)|"
    r"jobs\.lever\.co/([A-Za-z0-9_.-]+)|"
    r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)")


def discover_from_page(url):
    try:
        page = html.unescape(http_text(url))
    except Exception:
        return None
    for m in ATS_LINK_RE.finditer(page):
        gh, gh2, lv, ab = m.groups()
        slug = gh or gh2 or lv or ab
        if not slug or slug.lower() in ("embed", "v1", "api", "jobs"):
            continue
        ats = "greenhouse" if (gh or gh2) else ("lever" if lv else "ashby")
        return ats, slug.split("?")[0]
    return None


def slug_guesses(name):
    core = norm_company(name)
    parts = core.split()
    cands = ["".join(parts), "-".join(parts), re.sub(r"[^a-z0-9]", "", name.lower())]
    seen, out = set(), []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def ats_cache_path(root):
    return os.path.join(vp(root, "data"), "ats.tsv")


def load_ats_cache(root):
    p, cache = ats_cache_path(root), {}
    if os.path.exists(p):
        for row in csv.reader(open(p, encoding="utf-8"), delimiter="\t"):
            if len(row) >= 3 and row[0] != "company":
                cache[norm_company(row[0])] = (row[1], row[2])
    return cache


def save_ats_cache(root, company, ats, slug):
    p = ats_cache_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    new = not os.path.exists(p)
    with open(p, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        if new:
            w.writerow(["company", "ats", "slug", "found"])
        w.writerow([company, ats, slug, TODAY.isoformat()])


def cmd_jobs(args):
    root = vault_root(args)
    found, how = None, ""
    if args.ats:
        ats, _, slug = args.ats.partition(":")
        found, how = (ats, slug), "--ats"
    if not found:
        hit = load_ats_cache(root).get(norm_company(args.company))
        if hit:
            found, how = hit, "cache"
    if not found and args.careers_url:
        found = discover_from_page(args.careers_url)
        how = "careers page"
    if not found:
        for slug in slug_guesses(args.company):
            for ats in ("ashby", "greenhouse", "lever"):
                try:
                    jobs = fetch_board(ats, slug)
                except Exception:
                    continue
                if jobs:
                    found, how = (ats, slug), "slug guess"
                    break
            if found:
                break
    if not found:
        print(f"no public board found for {args.company}. Fix: pass --careers-url <their careers page> "
              f"or --ats ashby:<slug>. Some companies use Workday or Rippling; check those by hand.")
        sys.exit(3)
    ats, slug = found
    try:
        jobs = fetch_board(ats, slug)
    except urllib.error.HTTPError as e:
        die(f"{ats}:{slug} returned HTTP {e.code}. Fix: check the slug on the careers page.")
    except Exception as e:
        die(f"{ats}:{slug} failed: {e}")
    verified = how in ("--ats", "cache", "careers page")
    board_names = {j.get("board_company") for j in jobs if j.get("board_company")}
    if how == "slug guess" and board_names:
        verified = any(company_matches(args.company, b) for b in board_names)
        if not verified:
            print(f"[career-coach] {ats}:{slug} belongs to {', '.join(board_names)}, not {args.company}. "
                  f"Fix: pass --careers-url or --ats.", file=sys.stderr)
            sys.exit(3)
    if verified and how in ("careers page", "slug guess") and jobs:
        save_ats_cache(root, args.company, ats, slug)
    if args.describe:
        hit = [j for j in jobs if args.describe in j.get("url", "") or args.describe.lower() in j["title"].lower()]
        if not hit:
            die(f"no posting matching '{args.describe}' on {ats}:{slug}.")
        for j in hit[:2]:
            print(f"# {j['title']} ({j['location']}), posted {j['posted']}\n{j['url']}\n"
                  f"min years: {min_years(j.get('text'))}\n{j.get('comp','')}\n\n{(j.get('text') or '')[:6000]}\n")
        return
    rows = []
    for j in jobs:
        fam, sen, co = classify_title(j["title"], j["location"])
        yrs = min_years(j.get("text"))
        if yrs is not None:
            sen = "entry" if yrs <= 1 else ("mid" if yrs <= 3 else "senior")
        age = (TODAY - j["posted"]).days if j["posted"] else None
        j.update(family=fam, seniority=sen, home_region=co, age_days=age, years=yrs,
                 posted=j["posted"].isoformat() if j["posted"] else "")
        j.pop("text", None)
        if not args.all and (fam is None or (age is not None and age > args.days)
                             or (sen == "senior" and not args.include_senior)):
            continue
        rows.append(j)
    rows.sort(key=lambda r: (r["family"] is None, r["seniority"] == "senior", r["age_days"] or 9999))
    if not verified:
        print(f"WARNING: {ats}:{slug} came from a name guess and the board does not say whose it is. Open one "
              f"URL below and confirm it is {args.company} before using these roles.")
    if args.json:
        print(json.dumps({"company": args.company, "ats": ats, "slug": slug, "how": how, "verified": verified,
                          "total_open": len(jobs), "matches": rows}, indent=2))
        return
    print(f"{args.company}: {ats}:{slug} (found via {how}). {len(jobs)} open roles, "
          f"{len(rows)} shown (family match{'' if args.all else f', posted within {args.days} days'}"
          f"{'' if args.all or args.include_senior else ', senior hidden'}).")
    print("Level comes from the posting's years of experience when it states them (Yrs), else from the title.")
    print("| Title | Family | Level | Yrs | Location | Posted | Days | URL |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['title']} | {r['family'] or '-'} | {r['seniority']} | "
              f"{r['years'] if r['years'] is not None else '?'} | {r['location'][:60]} | "
              f"{r['posted']} | {r['age_days'] if r['age_days'] is not None else '?'} | {r['url']} |")


# ---------------------------------------------------------------- sweep / questions

def load_ats_rows(root):
    p, rows = ats_cache_path(root), {}
    if os.path.exists(p):
        for row in csv.reader(open(p, encoding="utf-8"), delimiter="\t"):
            if len(row) >= 3 and row[0] != "company" and row[1] in ("greenhouse", "lever", "ashby", "bamboohr"):
                rows[norm_company(row[0])] = (row[0], row[1], row[2])
    return list(rows.values())


NON_US_RE = (r"\b(uk|united kingdom|england|germany|munich|berlin|london|paris|france|india|canada|toronto|"
             r"vancouver|japan|tokyo|singapore|australia|netherlands|benelux|ireland|dublin|mexico|brazil|"
             r"poland|spain|italy|israel|hungary|budapest|new zealand|nz|abu dhabi|uae|dubai|korea|taiwan|"
             r"sweden|denmark|norway|switzerland|emea|apac)\b")
SWEEP_NOISE_RE = (r"talent|recruit|legal|people operations|people partner|marketing|communications|social media|"
                  r"launch|test (specialist|engineer)|mission operations|vehicle operator|spaceport|supervisor|"
                  r"production (manager|planner)|compliance|operations engineer|technical program|"
                  r"\bmba\b|customer success specialist")


def cmd_sweep(args):
    import concurrent.futures as cf
    root = vault_root(args)
    boards = load_ats_rows(root)
    if args.only:
        want = {norm_company(x) for x in args.only.split(",")}
        boards = [b for b in boards if norm_company(b[0]) in want]
    if not boards:
        die("no boards in Data/ats.tsv. Fix: run `jobs --company X --careers-url ...` to add some.")
    families = set(args.families.split(","))
    us_only = bool(CFG["search"].get("us_only", True)) and not args.any_country
    out, failed = [], []

    def one(b):
        try:
            return b, fetch_board(b[1], b[2]), None
        except Exception as e:
            return b, [], str(e)[:80]

    with cf.ThreadPoolExecutor(10) as ex:
        for (name, ats, slug), jobs, err in ex.map(one, boards):
            if err:
                failed.append(f"{name} ({ats}:{slug}): {err}")
                continue
            for j in jobs:
                fam, sen, co = classify_title(j["title"], j["location"])
                if fam not in families or not j["posted"]:
                    continue
                age = (TODAY - j["posted"]).days
                if age > args.days:
                    continue
                yrs = min_years(j.get("text"))
                if yrs is not None:
                    sen = "entry" if yrs <= 1 else ("mid" if yrs <= 3 else "senior")
                if (sen == "senior" and not args.include_senior) or (yrs is not None and yrs > args.max_years):
                    continue
                loc = j["location"].lower()
                if us_only and re.search(NON_US_RE, loc) and not re.search(r"\bus\b|\busa\b|united states", loc):
                    continue
                if not args.loose and re.search(SWEEP_NOISE_RE, j["title"].lower()):
                    continue
                out.append({"company": name, "ats": ats, "slug": slug, "id": j.get("id", ""),
                            "title": j["title"], "family": fam, "level": sen, "years": yrs,
                            "location": j["location"], "home_region": co, "posted": j["posted"].isoformat(),
                            "age_days": age, "url": j["url"], "comp": j.get("comp", "")})
    out.sort(key=lambda r: ({"entry": 0, "mid": 1, "senior": 2}[r["level"]], not r["home_region"], r["age_days"]))
    if args.json:
        print(json.dumps({"boards": len(boards), "failed": failed, "days": args.days, "matches": out}, indent=2))
        return
    lines = [f"Swept {len(boards)} boards ({len(failed)} failed): {len(out)} {'/'.join(sorted(families))} roles "
             f"posted in the last {args.days} days, at most {args.max_years} years required"
             f"{'' if args.include_senior else ', senior hidden'}.", "",
             "| Company | Title | Fam | Level | Yrs | Location | Posted | Link |", "|---|---|---|---|---|---|---|---|"]
    for r in out:
        loc = ("HOME: " if r["home_region"] else "") + r["location"][:50]
        lines.append(f"| {r['company']} | {r['title']} | {r['family']} | {r['level']} | "
                     f"{r['years'] if r['years'] is not None else '?'} | {loc} | {r['posted']} | [apply]({r['url']}) |")
    if failed:
        lines += ["", "Failed boards: " + "; ".join(failed)]
    print("\n".join(lines))


def cmd_questions(args):
    ats, _, slug = args.ats.partition(":")
    if ats == "greenhouse":
        d = http_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{args.id}?questions=true")
        print(f"# {d.get('title')} ({(d.get('location') or {}).get('name','')})\n{d.get('absolute_url')}\n")
        standard = {"first_name", "last_name", "email", "phone", "resume", "resume_text", "cover_letter",
                    "cover_letter_text"}
        for q in d.get("questions", []) + [q for q in d.get("location_questions", []) or []]:
            fields = q.get("fields") or [{}]
            if fields[0].get("name") in standard:
                continue
            opts = [v.get("label") for f in fields for v in (f.get("values") or [])]
            req = "required" if q.get("required") else "optional"
            print(f"- [{req}] {q.get('label')}" + (f"  (options: {', '.join(opts[:12])})" if opts else ""))
        for c in d.get("compliance") or []:
            for q in c.get("questions") or []:
                print(f"- [compliance] {q.get('label')}")
    elif ats == "lever":
        page = html.unescape(http_text(f"https://jobs.lever.co/{slug}/{args.id}/apply"))
        labels = re.findall(r'<div class="application-label[^"]*">(.*?)</div>', page, flags=re.S)
        print(f"# https://jobs.lever.co/{slug}/{args.id}/apply\n")
        for l in labels:
            t = re.sub(r"\s+", " ", strip_html(l)).strip()
            if t and not re.match(r"(resume|full name|email|phone|current company|linkedin url|github url|"
                                  r"portfolio url|other website|twitter url)", t, re.I):
                print(f"- {t}")
    elif ats == "ashby":
        q = ("query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) { "
             "jobPosting(organizationHostedJobsPageName: $organizationHostedJobsPageName, jobPostingId: $jobPostingId) "
             "{ title applicationForm { sections { fieldEntries { field isRequired } } } } }")
        d = http_post_json("https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting",
                           {"operationName": "ApiJobPosting", "query": q,
                            "variables": {"organizationHostedJobsPageName": slug, "jobPostingId": args.id}})
        jp = (d.get("data") or {}).get("jobPosting") or {}
        if not jp:
            die("Ashby returned no posting; check the slug and the posting id (the UUID at the end of the job URL).")
        print(f"# {jp.get('title')}\nhttps://jobs.ashbyhq.com/{slug}/{args.id}\n")
        for line in ashby_form_lines(jp):
            print(line)
    elif ats == "bamboohr":
        d = http_json(f"https://{slug}.bamboohr.com/careers/{args.id}/detail").get("result") or {}
        jo = d.get("jobOpening") or {}
        print(f"# {jo.get('jobOpeningName')} ({', '.join(x for x in ((jo.get('location') or {}).get('city'), (jo.get('location') or {}).get('state')) if x)})\n"
              f"https://{slug}.bamboohr.com/careers/{args.id}\n")
        for line in bamboo_form_lines(d.get("formFields") or {}):
            print(line)
    else:
        die("questions works for greenhouse, lever, ashby and bamboohr.")


ASHBY_STANDARD = {"_systemfield_name", "_systemfield_email", "_systemfield_resume"}
BAMBOO_STANDARD = {"firstName", "lastName", "email", "phone", "resumeFileId", "genderId", "ethnicityId"}


def ashby_form_lines(jp):
    out = []
    for sec in ((jp.get("applicationForm") or {}).get("sections") or []):
        for e in sec.get("fieldEntries") or []:
            f = e.get("field") or {}
            if f.get("path") in ASHBY_STANDARD or f.get("title") in ("Name", "Email", "Resume"):
                continue
            opts = [o.get("label") for o in (f.get("selectableValues") or [])]
            out.append(f"- [{'required' if e.get('isRequired') else 'optional'}] {f.get('title')}"
                       + (f"  (options: {', '.join(opts[:12])})" if opts else ""))
    return out or ["- (only name, email and resume)"]


def bamboo_form_lines(ff):
    out = []
    for k, v in ff.items():
        if k == "customQuestions":
            for q in v or []:
                opts = [str(o.get("option", "")).strip() for o in (q.get("options") or [])]
                label = re.sub(r"\s+", " ", q.get("question") or "").strip()
                if label.lower().startswith("i understand the following voluntary"):
                    continue
                out.append(f"- [{'required' if q.get('isRequired') else 'optional'}] {label[:300]}"
                           + (f"  (options: {', '.join(opts[:12])})" if opts else ""))
        elif isinstance(v, dict) and k not in BAMBOO_STANDARD:
            opts = [o.get("text") for o in (v.get("options") or [])]
            out.append(f"- [{'required' if v.get('isRequired') else 'optional'}] {v.get('label')}"
                       + (f"  (options: {', '.join(opts[:12])})" if opts else ""))
    return out


# ---------------------------------------------------------------- warm

def read_note(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    fm, body = split_frontmatter(text)
    return parse_frontmatter(fm) if fm is not None else {}, body


def connections_path(root):
    data = vp(root, "data")
    for name in ("Connections.csv", "connections.csv"):
        p = os.path.join(data, name)
        if os.path.exists(p):
            return p
    return None


def load_connections(root):
    p = connections_path(root)
    if not p:
        return []
    lines = open(p, encoding="utf-8-sig", errors="replace").read().splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("First Name")), None)
    if start is None:
        return []
    return list(csv.DictReader(lines[start:]))


def load_messaged(root):
    """Names the user has exchanged LinkedIn messages with (Data/messaged.tsv: name, messages, last; no content)."""
    p = os.path.join(vp(root, "data"), "messaged.tsv")
    if not os.path.exists(p):
        return {}
    return {r["name"].lower(): r for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t")}


def cmd_warm(args):
    root = vault_root(args)
    company = args.company
    hits = []
    messaged = load_messaged(root)
    for c in load_connections(root):
        if company_matches(company, c.get("Company", "")):
            name = f"{c.get('First Name','')} {c.get('Last Name','')}".strip()
            detail = f"connected {c.get('Connected On','')}"
            m = messaged.get(name.lower())
            if m:
                detail += f"; you have messaged ({m['messages']} messages, last {m['last']})"
            hits.append(("1st-degree", name, c.get("Position", ""), c.get("URL", ""), detail))
    for pattern in ORG_GLOBS:
        for path in glob.glob(os.path.join(root, pattern), recursive=True):
            fm, _ = read_note(path)
            if company_matches(company, str(fm.get("company", ""))) or \
                    company_matches(company, os.path.splitext(os.path.basename(path))[0]):
                hits.append(("org-contact", str(fm.get("contact_name", "")), str(fm.get("relationship", "")),
                             os.path.relpath(path, root), str(fm.get("contact_email", ""))))
    for d in PEOPLE_DIRS:
        for path in glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True):
            if "/Conversations/" in path:
                continue
            fm, body = read_note(path)
            name = os.path.splitext(os.path.basename(path))[0]
            if company_matches(company, str(fm.get("company", "")).strip("[]")) or text_mentions(body, company):
                label = PEOPLE_LABELS.get(d)
                if label and d != PATHS["people"]:
                    kind = label  # e.g. coworker, club, family: the label you gave this folder in the config
                elif fm.get("warm"):
                    kind = f"already-named ({fm['warm']})"  # a contact this skill wrote earlier
                else:
                    kind = "vault-person"
                line = next((l.strip() for l in body.splitlines() if text_mentions(l, company)), "")
                hits.append((kind, name, str(fm.get("title", "")), os.path.relpath(path, root), line[:160]))
    for key in ("target_companies", "connectors"):
        p = vp(root, key)
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                if line.startswith("|") and text_mentions(line, company):
                    hits.append(("note-row", os.path.basename(p), "", PATHS[key], line.strip()[:200]))
    for path in sorted(glob.glob(PRENAMED_GLOB)) if PRENAMED_GLOB else []:
        for row in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"):
            if company_matches(company, row.get("company", "")):
                hits.append(("prenamed-cold", row.get("name", ""), row.get("title", ""), row.get("source", ""),
                             f"{os.path.basename(path)}; {row.get('why','')}"))
    if args.json:
        print(json.dumps([dict(zip(["type", "name", "title", "source", "detail"], h)) for h in hits], indent=2))
        return
    if not connections_path(root):
        print("note: no LinkedIn Connections.csv in Data/, so 1st-degree matches are not checked.")
    if not hits:
        alumni = ", ".join(CFG["warm"].get("alumni") or []) or "your school and clubs"
        print(f"no warm paths found for {company} in the vault. Next: alumni search ({alumni}), "
              f"then ask a connector (see Connectors.md).")
        return
    order = {"1st-degree": 0, "org-contact": 2, "already-named (connector-intro)": 3, "vault-person": 3,
             "note-row": 4, "prenamed-cold": 5}
    order.update({label: 1 for label in PEOPLE_LABELS.values()})
    for h in sorted(hits, key=lambda h: order.get(h[0], 9)):
        print(f"- [{h[0]}] {h[1]} | {h[2]} | {h[3]} | {h[4]}")


# ---------------------------------------------------------------- companies

COMPANY_ORDER = ["created", "updated", "tags", "company", "domain", "lane", "sector", "stage", "last_round",
                 "hq", "home_region", "fit", "best_role", "roles_open", "signal", "signal_date", "warm",
                 "status", "priority", "next_action", "next_date", "seeded"]


def company_path(root, name):
    return os.path.join(vp(root, "companies"), safe_filename(name) + ".md")


def render_signals(signals):
    if not signals:
        return "_None recorded yet._"
    lines = ["| Date | Kind | What happened | Source |", "|---|---|---|---|"]
    for s in sorted(signals, key=lambda s: s.get("date", ""), reverse=True):
        kind = (s.get("kind") or "") + (" (headline)" if s.get("headline") else "")
        lines.append(f"| {s.get('date','')} | {kind} | {s.get('what','').replace('|','/')} | [link]({s.get('url','')}) |")
    return "\n".join(lines)


def parse_signals(md):
    out = []
    for line in (md or "").splitlines():
        m = re.match(r"^\| (\d{4}-\d{2}-\d{2}) \| ([a-z]*)( \(headline\))? \| (.*) \| \[link\]\((.*)\) \|$", line)
        if m:
            out.append({"date": m.group(1), "kind": m.group(2), "headline": bool(m.group(3)),
                        "what": m.group(4), "url": m.group(5)})
            continue
        m = re.match(r"^\| (\d{4}-\d{2}-\d{2}) \| (.*) \| \[link\]\((.*)\) \|$", line)
        if m:
            out.append({"date": m.group(1), "what": m.group(2), "url": m.group(3)})
    return out


def render_roles(roles, checked):
    if not roles:
        start = profile("start_date", "your start date")
        return f"_No matching open roles as of {checked}. The company may still hire for a {start} start; ask._"
    lines = [f"Checked {checked}.", "", "| Role | Family | Level | Location | Posted | Fit | Resume | Why |",
             "|---|---|---|---|---|---|---|---|"]
    for r in sorted(roles, key=lambda r: -(r.get("fit") or 0)):
        title = f"[{r.get('title','')}]({r['url']})" if r.get("url") else r.get("title", "")
        lines.append(f"| {title} | {r.get('family','')} | {r.get('seniority','')} | {r.get('location','')} | "
                     f"{r.get('posted','')} | {r.get('fit','')} | {r.get('resume','')} | "
                     f"{str(r.get('why','')).replace('|','/')} |")
    return "\n".join(lines)


def validate_no_dashes(obj, where):
    blob = json.dumps(obj, ensure_ascii=False)
    if EM_DASH_RE.search(blob):
        die(f"{where} contains an em dash. Rewrite before writing to the vault.")


def headline_signal(signals):
    """The signal shown in the dashboard: one marked headline, else the newest funding, launch or contract
    inside 60 days (postings are the weakest hook), else the newest of anything."""
    marked = [s for s in signals if s.get("headline")]
    if marked:
        top = max(marked, key=lambda s: s.get("date", ""))
        return top["what"], top["date"]
    cutoff = (TODAY - dt.timedelta(days=60)).isoformat()
    strong = [s for s in signals if s.get("date", "") >= cutoff and
              (s.get("kind") or "") not in ("posting", "") or
              (s.get("date", "") >= cutoff and not s.get("kind") and
               not re.search(r"\bpost(ed|ing|s)?\b|\bhiring\b|\brole", s.get("what", ""), re.I))]
    top = max(strong or signals, key=lambda s: s.get("date", ""))
    return top["what"], top["date"]


def cmd_upsert_company(args):
    root = vault_root(args)
    spec = json.load(open(args.json_file, encoding="utf-8"))
    upsert_company(root, spec, args.force_human)


def upsert_company(root, spec, force_human=False):
    """Create or merge a company note from a spec dict. Returns the note path."""
    name = spec.get("name") or die("company JSON needs 'name'.")
    validate_no_dashes(spec, f"company JSON for {name}")
    for s in spec.get("signals", []):
        if not s.get("url") or not s.get("date"):
            die(f"signal '{s.get('what','')}' needs a date and a url. Every signal is sourced.")
    path = company_path(root, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exists = os.path.exists(path)
    if exists:
        fm, body = read_note(path)
    else:
        fm, body = {}, ""
    now = TODAY.isoformat()
    fm.setdefault("created", now)
    fm["updated"] = now
    fm["tags"] = ["career/research", "type/tracker"]
    fm["company"] = name
    for k in ("domain", "lane", "sector", "stage", "last_round", "hq", "best_role", "warm"):
        if spec.get(k) not in (None, ""):
            fm[k] = spec[k]
    if "home_region" in spec:
        fm["home_region"] = bool(spec["home_region"])
    if spec.get("fit") is not None:
        fm["fit"] = int(spec["fit"])
    if "roles" in spec:
        fm["roles_open"] = len(spec["roles"])
    old_signals = parse_signals(get_block(body, "signals"))
    by_url = {s["url"]: s for s in old_signals}
    for s in spec.get("signals", []):
        by_url[s["url"]] = s
    signals = list(by_url.values())
    if signals:
        fm["signal"], fm["signal_date"] = headline_signal(signals)
    for k in HUMAN_COMPANY_KEYS:
        if k not in fm or fm[k] in ("", None):
            if spec.get(k) not in (None, ""):
                fm[k] = spec[k]
            elif k == "status":
                fm[k] = "research"
            else:
                fm.setdefault(k, "")
        elif force_human and spec.get(k) not in (None, ""):
            fm[k] = spec[k]
    if fm.get("status") not in COMPANY_STATUSES:
        print(f"warn: status '{fm.get('status')}' is not one of {COMPANY_STATUSES}", file=sys.stderr)
    if spec.get("seeded"):
        fm["seeded"] = True
    elif "seeded" in fm and spec.get("fit") is not None:
        fm.pop("seeded")

    sections = {}
    if spec.get("why") is not None:
        sections["snapshot"] = spec["why"]
    sections["signals"] = render_signals(signals)
    if "roles" in spec:
        sections["roles"] = render_roles(spec["roles"], spec.get("roles_checked", now))
    people = list(dict.fromkeys(spec.get("people", [])))
    old_people = re.findall(r"\[\[([^\]|]+)", get_block(body, "people") or "")
    merged_people = list(dict.fromkeys(old_people + people))
    if merged_people:
        sections["people"] = "\n".join(f"- [[{p}]]" for p in merged_people)
    if spec.get("openers"):
        sections["openers"] = spec["openers"]
    log_line = f"- {now}: {spec.get('log', 'updated by career-coach')}"

    if not exists or not body.strip():
        body = (f"# {name}\n\n"
                f"## Snapshot\n{block('snapshot', sections.get('snapshot', '_Not researched yet._'))}\n\n"
                f"## Signals (last 60 days first)\n{block('signals', sections['signals'])}\n\n"
                f"## Open roles\n{block('roles', sections.get('roles', '_Not checked yet._'))}\n\n"
                f"## People\n{block('people', sections.get('people', '_None named yet._'))}\n\n"
                f"## Openers (drafts, never sent by Claude)\n"
                f"{block('openers', sections.get('openers', '_None drafted yet._'))}\n\n"
                f"## Log\n{block('log', log_line)}\n\n"
                f"## Notes\n\n\n---\n[[Job Search Hub]] | [[Pipeline.base|Pipeline]] | [[Target Companies]]\n")
    else:
        for key, content in sections.items():
            new_body = set_block(body, key, content)
            if new_body is None:
                body = body.rstrip() + f"\n\n{block(key, content)}\n"
            else:
                body = new_body
        old_log = get_block(body, "log") or ""
        body = set_block(body, "log", (old_log.rstrip() + "\n" + log_line).strip()) or \
            body.rstrip() + f"\n\n{block('log', log_line)}\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump_frontmatter(fm, COMPANY_ORDER) + body)
    print(f"{'updated' if exists else 'created'} {os.path.relpath(path, root)}")
    return path


# ---------------------------------------------------------------- people

PERSON_ORDER = ["created", "updated", "tags", "company", "title", "kind", "warm", "via", "source", "linkedin",
                "verify", "outreach", "last_contact", "next_touch"]
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def find_person_note(root, name):
    target = safe_filename(name).lower()
    for d in PEOPLE_DIRS:
        for path in glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True):
            if "/Conversations/" in path:
                continue
            base = os.path.splitext(os.path.basename(path))[0].lower()
            if base == target or re.sub(r"\s*\(.*\)$", "", base) == target:
                return path
    return None


def render_person_block(spec, rows, phase):
    lines = [f"**Company:** [[{spec['company']}]]  ", f"**Role:** {spec.get('title','')}  ",
             f"**Why this person:** {spec.get('why','')}  ",
             f"**Source:** {spec['source']}" + (" (title unverified, confirm before sending)" if spec.get("verify") else "")]
    if spec.get("via"):
        lines.append(f"**Warm path:** via [[{spec['via']}]]")
    op = spec.get("opener") or {}
    if op:
        lines += ["", f"### Opener drafts ({TODAY.isoformat()}, phase: {phase})"]
        if op.get("hook"):
            lines.append(f"Hook: {op['hook']} ({op.get('hook_date','')}, {op.get('hook_url','')})")
        for kind in ("note", "message", "email"):
            if op.get(kind):
                errors, warns, size = lint_text(op[kind], kind, rows, op.get("allow", []))
                if errors:
                    die(f"{spec['name']} {kind} opener fails check: " + " | ".join(errors))
                unit = LIMITS[kind][0]
                label = {"note": "LinkedIn connection note", "message": "LinkedIn message",
                         "email": "Email"}[kind]
                lines += ["", f"**{label}** ({size} {unit}):", "", "> " + op[kind].replace("\n", "\n> ")]
                for w in warns:
                    lines.append(f"- check: {w}")
    return "\n".join(lines)


def cmd_upsert_person(args):
    root = vault_root(args)
    spec = json.load(open(args.json_file, encoding="utf-8"))
    for k in ("name", "company", "source"):
        if not spec.get(k):
            die(f"person JSON needs '{k}'. No person is written without a source URL.")
    if not re.match(r"^(https?://|linkedin\.com/|www\.)", spec["source"]) and "/" not in spec["source"]:
        die(f"source for {spec['name']} must be a URL or vault path, got '{spec['source']}'.")
    validate_no_dashes(spec, f"person JSON for {spec['name']}")
    blob = json.dumps({k: v for k, v in spec.items() if k not in ("email_source",)})
    if EMAIL_RE.search(blob) and not spec.get("email_source"):
        die(f"{spec['name']} has an email address with no email_source. Never guess an address.")
    if spec.get("via") and not spec.get("warm"):
        spec["warm"] = "connector-intro"
    rows = read_fact_sheet(root)
    phase = search_phase()[0]
    content = render_person_block(spec, rows, phase)
    existing = find_person_note(root, spec["name"])
    now = TODAY.isoformat()
    if existing and not existing.startswith(vp(root, "people")) or \
            (existing and get_block(open(existing, encoding="utf-8").read(), "career") is None):
        # a note in another people folder, or one the user wrote by hand: add a block, leave the rest alone
        text = open(existing, encoding="utf-8").read()
        new = set_block(text, "career", content)
        if new is None:
            new = text.rstrip() + f"\n\n## Career outreach\n{block('career', content)}\n"
        open(existing, "w", encoding="utf-8").write(new)
        print(f"updated existing note {os.path.relpath(existing, root)} (career block only)")
        return
    path = existing or os.path.join(vp(root, "people"), safe_filename(spec["name"]) + ".md")
    if existing:
        fm, body = read_note(path)
    else:
        fm, body = {}, ""
    fm.setdefault("created", now)
    fm["updated"] = now
    fm["tags"] = ["career/research", "type/reference"]
    fm["company"] = f"[[{spec['company']}]]"
    for k in ("title", "kind", "warm", "via", "linkedin"):
        if spec.get(k):
            fm[k] = f"[[{spec[k]}]]" if k == "via" else spec[k]
    fm["source"] = spec["source"]
    fm["verify"] = bool(spec.get("verify"))
    for k in HUMAN_PERSON_KEYS:
        if not fm.get(k):
            fm[k] = spec.get(k) or ("drafted" if k == "outreach" and spec.get("opener") else
                                    "not-contacted" if k == "outreach" else "")
    if not body.strip():
        body = (f"# {spec['name']}\n\n## Career outreach\n{block('career', content)}\n\n"
                f"## Notes\n\n\n---\n[[{spec['company']}]] | [[Job Search Hub]]\n")
    else:
        body = set_block(body, "career", content) or body.rstrip() + f"\n\n{block('career', content)}\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump_frontmatter(fm, PERSON_ORDER) + body)
    print(f"{'updated' if existing else 'created'} {os.path.relpath(path, root)}")


# ---------------------------------------------------------------- runs, known, status, lint

def cmd_log_run(args):
    root = vault_root(args)
    body = open(args.body_file, encoding="utf-8").read()
    if EM_DASH_RE.search(body):
        die("run log contains an em dash.")
    os.makedirs(vp(root, "runs"), exist_ok=True)
    base = f"Run, {TODAY.isoformat()} {args.mode}"
    path = os.path.join(vp(root, "runs"), base + ".md")
    n = 2
    while os.path.exists(path):
        path = os.path.join(vp(root, "runs"), f"{base} {n}.md")
        n += 1
    fm = {"created": TODAY.isoformat(), "tags": ["career/research", "type/log"], "mode": args.mode,
          "credits_spent": 0}
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump_frontmatter(fm, ["created", "tags", "mode", "credits_spent"]) +
                f"# {base}\n\n{body.strip()}\n\n---\n[[Job Search Hub]] | [[Pipeline.base|Pipeline]]\n")
    print(f"wrote {os.path.relpath(path, root)}")


def load_companies(root):
    out = []
    for path in sorted(glob.glob(os.path.join(vp(root, "companies"), "*.md"))):
        fm, body = read_note(path)
        fm["_name"] = os.path.splitext(os.path.basename(path))[0]
        fm["_path"] = path
        fm["_apps"] = parse_apps(get_block(body, "applications"))
        fm["_people"] = re.findall(r"\[\[([^\]|]+)", get_block(body, "people") or "")
        out.append(fm)
    return out


def load_people(root):
    out = []
    for path in sorted(glob.glob(os.path.join(vp(root, "people"), "*.md"))):
        fm, body = read_note(path)
        if "career/research" in (fm.get("tags") or []):
            fm["_name"] = os.path.splitext(os.path.basename(path))[0]
            out.append(fm)
    return out


def cmd_known(args):
    rows = load_companies(vault_root(args))
    if args.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "_path"} for r in rows], indent=2, default=str))
        return
    for r in rows:
        print(f"- {r['_name']} | updated {r.get('updated','')} | status {r.get('status','')} | fit {r.get('fit','')} "
              f"| home {r.get('home_region','')}{' | seeded' if r.get('seeded') else ''}")
    print(f"{len(rows)} company notes.")


def as_date(v):
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def cmd_status(args):
    root = vault_root(args)
    comps, people = load_companies(root), load_people(root)
    active = [c for c in comps if c.get("status") not in ("closed", "parked")]
    co = [c for c in active if c.get("home_region") is True]
    phase, advice = search_phase()
    print(f"# Career pipeline, {TODAY.isoformat()}\n\nPhase: **{phase}**. {advice}\n")
    print(f"{len(comps)} companies, {len(active)} active, pipeline {HOME_NAME} share (all active notes) "
          f"{(100 * len(co) // len(active)) if active else 0}% (target {round(HOME_SHARE * 100)}%+).")
    by = {}
    for c in comps:
        by.setdefault(c.get("status") or "research", []).append(c["_name"])
    for s in COMPANY_STATUSES:
        if s in by:
            print(f"- {s}: {len(by[s])} ({', '.join(by[s][:8])}{'...' if len(by[s]) > 8 else ''})")
    print("\n## Top by fit")
    for c in sorted([c for c in active if isinstance(c.get("fit"), int)], key=lambda c: -c["fit"])[:10]:
        print(f"- {c['_name']}: {c['fit']} | {c.get('best_role','')} | {HOME_NAME if c.get('home_region') else c.get('hq','')}")
    seeded = [c["_name"] for c in active if c.get("seeded")]
    if seeded:
        print(f"\nSeeded but not researched ({len(seeded)}): {', '.join(seeded)}")
    print("\n## Due (company next_date, person next_touch, application follow_up_on; `due --days 7` looks ahead)")
    due = collect_due(comps, people, 0)
    for i in due:
        print(format_due(i))
    stale = [c for c in active if as_date(c.get("signal_date")) and (TODAY - as_date(c.get("signal_date"))).days > 60]
    if stale:
        print(f"- refresh signals (older than 60 days): {', '.join(c['_name'] for c in stale)}")
    if not due and not stale:
        print("- nothing due")
    counts = {}
    for p in people:
        counts[p.get("outreach") or "not-contacted"] = counts.get(p.get("outreach") or "not-contacted", 0) + 1
    print("\n## People\n" + (", ".join(f"{k}: {v}" for k, v in counts.items()) or "none yet"))
    if not connections_path(root):
        print("\nLinkedIn Connections.csv is not in Data/ yet, so 1st-degree warm paths are unchecked.")


def cmd_lint(args):
    root = vault_root(args)
    problems = 0
    files = glob.glob(os.path.join(vp(root, "companies"), "*.md")) + \
        glob.glob(os.path.join(vp(root, "runs"), "*.md")) + \
        [p for p in glob.glob(os.path.join(root, "**", "*.md"), recursive=True)
         if "<!-- cc:career -->" in open(p, encoding="utf-8", errors="replace").read()]
    for path in sorted(set(files)):
        text = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, root)
        if EM_DASH_RE.search(text):
            print(f"em dash: {rel}")
            problems += 1
        opens = re.findall(r"<!-- cc:([a-z]+) -->", text)
        closes = re.findall(r"<!-- /cc:([a-z]+) -->", text)
        if sorted(opens) != sorted(closes):
            print(f"broken managed markers: {rel}")
            problems += 1
        fm, _ = split_frontmatter(text)
        if fm is None:
            print(f"no frontmatter: {rel}")
            problems += 1
        if "<!-- cc:career -->" in text and "**Source:**" not in text:
            print(f"person block without a source: {rel}")
            problems += 1
    companies_dir = vp(root, "companies")
    enum_files = set(files) | set(glob.glob(os.path.join(vp(root, "people"), "*.md")))
    for path in sorted(enum_files):
        fm, _ = read_note(path)
        rel = os.path.relpath(path, root)
        status = fm.get("status")
        if os.path.dirname(path) == companies_dir and status not in ("", None) and status not in COMPANY_STATUSES:
            print(f"status '{status}' is not one of {', '.join(COMPANY_STATUSES)}: {rel}")
            problems += 1
        outreach = fm.get("outreach")
        if outreach not in ("", None) and outreach not in OUTREACH_STATUSES:
            print(f"outreach '{outreach}' is not one of {', '.join(OUTREACH_STATUSES)}: {rel}")
            problems += 1
    print(f"{len(enum_files)} files checked, {problems} problems.")
    sys.exit(1 if problems else 0)


def cmd_mark(args):
    """Record what the user did: outreach on a person, status on a company. Only on their say-so."""
    root = vault_root(args)
    day = args.date or TODAY.isoformat()
    if args.person:
        path = find_person_note(root, args.person) or die(f"no person note named {args.person}.")
        text = open(path, encoding="utf-8").read()
        fm_raw, body = split_frontmatter(text)
        fm = parse_frontmatter(fm_raw) if fm_raw is not None else {}
        if args.outreach:
            if args.outreach not in OUTREACH_STATUSES:
                die(f"outreach must be one of {OUTREACH_STATUSES}")
            fm["outreach"] = args.outreach
            if args.outreach in ("sent", "replied", "meeting"):
                fm["last_contact"] = day
        if args.next_touch:
            fm["next_touch"] = args.next_touch
        elif args.event or args.outreach == "sent":
            fm["next_touch"] = cadence_date(args.event or "note-sent", day)
        fm["updated"] = TODAY.isoformat()
        open(path, "w", encoding="utf-8").write(dump_frontmatter(fm, PERSON_ORDER) + body)
        print(f"marked {os.path.relpath(path, root)}: outreach {fm.get('outreach')}, last_contact "
              f"{fm.get('last_contact','')}, next_touch {fm.get('next_touch','')}")
        company = args.company or str(fm.get("company", "")).strip("[]")
        if args.outreach == "sent" and company and os.path.exists(company_path(root, company)) and not args.status:
            args.status = "contacted"
            args.company = company
            args.only_if_earlier = True
    if args.company and args.status:
        path = company_path(root, args.company)
        if not os.path.exists(path):
            die(f"no company note for {args.company}.")
        fm, body = read_note(path)
        if args.status not in COMPANY_STATUSES:
            die(f"status must be one of {COMPANY_STATUSES}")
        cur = fm.get("status") or "research"
        if getattr(args, "only_if_earlier", False) and cur not in ("research", "reach-out"):
            return
        fm["status"] = args.status
        if args.next_action is not None:
            fm["next_action"] = args.next_action
        if args.next_date is not None:
            fm["next_date"] = args.next_date
        fm["updated"] = TODAY.isoformat()
        log = (get_block(body, "log") or "").rstrip() + f"\n- {day}: status {cur} -> {args.status}"
        body = set_block(body, "log", log.strip()) or body
        open(path, "w", encoding="utf-8").write(dump_frontmatter(fm, COMPANY_ORDER) + body)
        print(f"marked {os.path.relpath(path, root)}: status {cur} -> {args.status}")


# ---------------------------------------------------------------- applications, due, tracker import

APP_COLS = ["role", "applied", "resume", "referral", "follow_up_on", "url"]
APP_HEADER = "| Role | Applied | Resume | Referral | Follow up | Link |\n|---|---|---|---|---|---|"
STATUS_RANK = {s: i for i, s in enumerate(COMPANY_STATUSES)}


def parse_apps(md):
    out = []
    for line in (md or "").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != len(APP_COLS) or cells[0] == "Role" or all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        out.append({k: ("" if v == "-" else v) for k, v in zip(APP_COLS, cells)})
    return out


def render_apps(apps):
    lines = [APP_HEADER]
    for a in apps:
        lines.append("| " + " | ".join((str(a.get(k) or "").replace("|", "/") or "-") for k in APP_COLS) + " |")
    return "\n".join(lines)


def find_company_note(root, name):
    p = company_path(root, name)
    if os.path.exists(p):
        return p
    want = norm_company(name)
    for path in sorted(glob.glob(os.path.join(vp(root, "companies"), "*.md"))):
        if want and norm_company(os.path.splitext(os.path.basename(path))[0]) == want:
            return path
    return None


def insert_section(body, heading, content, before=("## Log", "## Notes")):
    """Put a new '## heading' plus its cc block before the first of `before` headings, else at the end."""
    section = f"## {heading}\n{content}\n\n"
    for h in before:
        m = re.search(rf"^{re.escape(h)}\s*$", body, re.M)
        if m:
            return body[:m.start()] + section + body[m.start():]
    return body.rstrip() + "\n\n" + section


def cmd_applied(args):
    """Record an application the user submitted. Idempotent; never moves a company status backward."""
    root = vault_root(args)
    role = args.role.strip()
    validate_no_dashes([role, args.company, args.resume, args.referral], "applied arguments")
    day = args.date or TODAY.isoformat()
    if not as_date(day):
        die(f"--date must be YYYY-MM-DD, got '{day}'.")
    path = find_company_note(root, args.company)
    if not path:
        path = upsert_company(root, {"name": args.company, "seeded": True,
                                     "log": "created by cc.py applied (stub, not researched yet)"})
    fm, body = read_note(path)
    rel = os.path.relpath(path, root)
    apps = parse_apps(get_block(body, "applications"))
    follow = cadence_date("application", day)
    new_rows, filled = [], False
    for url in dict.fromkeys([args.url.strip()] + [u.strip() for u in args.also_url if u.strip()]):
        old = next((a for a in apps if a["role"].lower() == role.lower() and a["url"] == url), None)
        if old:
            for k, v in (("resume", args.resume), ("referral", args.referral)):
                if v and not old[k]:
                    old[k], filled = v, True
            continue
        row = {"role": role, "applied": day, "resume": args.resume, "referral": args.referral,
               "follow_up_on": follow, "url": url}
        apps.append(row)
        new_rows.append(row)
    if not new_rows and not filled:
        print(f"already recorded in {rel}: {role}. Nothing changed.")
        return
    cur = fm.get("status") or "research"
    log = (get_block(body, "log") or "").rstrip()
    lines = []
    if new_rows:
        rank = STATUS_RANK.get(cur)
        if rank is None:
            print(f"warn: status '{cur}' is not a known value; left as is.", file=sys.stderr)
        elif rank < STATUS_RANK["applied"]:
            fm["status"] = "applied"
            lines.append(f"- {day}: status {cur} -> applied")
        if rank is not None and rank <= STATUS_RANK["applied"]:
            fm["next_action"] = f"Follow up on the {role} application, naming the req"
            fm["next_date"] = follow
        entry = f"applied: {role}" + (f" ({args.resume})" if args.resume else "")
        if len(new_rows) > 1:
            entry += f", {len(new_rows)} locations"
        if entry not in log:
            lines.append(f"- {day}: {entry}")
    fm["updated"] = TODAY.isoformat()
    table = render_apps(apps)
    body = set_block(body, "applications", table) or insert_section(body, "Applications", block("applications", table))
    if lines:
        body = set_block(body, "log", (log + "\n" + "\n".join(lines)).strip()) or \
            body.rstrip() + f"\n\n{block('log', chr(10).join(lines))}\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump_frontmatter(fm, COMPANY_ORDER) + body)
    moved = f"status {cur} -> {fm.get('status')}" if fm.get("status") != cur else f"status stays {cur}"
    print(f"applied {rel}: {role}, {len(new_rows)} new location(s){', filled blanks' if filled else ''}; "
          f"{moved}; follow up on {follow}")


def collect_due(comps, people, days):
    """Company next_date, person next_touch and application follow-ups due on or before today + days."""
    cutoff = TODAY + dt.timedelta(days=days)
    items = []
    for c in comps:
        if c.get("status") in ("closed", "parked"):
            continue
        nd = as_date(c.get("next_date"))
        if nd:
            items.append({"date": nd, "kind": "company", "name": c["_name"],
                          "what": c.get("next_action") or "next action"})
        for a in c.get("_apps", []):
            fu, applied = as_date(a.get("follow_up_on")), as_date(a.get("applied"))
            if fu and fu != nd:
                items.append({"date": fu, "kind": "application", "name": c["_name"],
                              "what": f"{a['role']} (applied {a['applied']}): {CADENCE['application'][1]}"})
            if applied and not a.get("referral") and not c.get("_people"):
                items.append({"date": applied + dt.timedelta(days=CADENCE["applied-no-human"][0]),
                              "kind": "application", "name": c["_name"],
                              "what": f"{a['role']}: {CADENCE['applied-no-human'][1]}"})
    for p in people:
        o = p.get("outreach") or "not-contacted"
        if o in ("closed", "dormant"):
            continue
        nt = as_date(p.get("next_touch"))
        if not nt and o == "sent" and as_date(p.get("last_contact")):
            nt = as_date(cadence_date("note-sent", as_date(p.get("last_contact"))))
        if nt:
            items.append({"date": nt, "kind": "person", "name": p["_name"],
                          "what": f"follow up (outreach {o}, last contact {p.get('last_contact') or '-'})"})
    items = [i for i in items if i["date"] <= cutoff]
    items.sort(key=lambda i: (i["date"], i["kind"], i["name"]))
    return items


def format_due(i):
    late = (TODAY - i["date"]).days
    when = f"{late} days overdue" if late > 0 else ("today" if late == 0 else f"in {-late} days")
    return f"- {i['date'].isoformat()} ({when}) | {i['kind']} | {i['name']} | {i['what']}"


def cmd_due(args):
    root = vault_root(args)
    items = collect_due(load_companies(root), load_people(root), args.days)
    if args.json:
        print(json.dumps([dict(i, date=i["date"].isoformat()) for i in items], indent=2))
        return
    cutoff = TODAY + dt.timedelta(days=args.days)
    print(f"# Due by {cutoff.isoformat()} ({'today or overdue' if args.days == 0 else f'next {args.days} days'}):"
          f" {len(items)} items")
    for i in items:
        print(format_due(i))


def split_md_row(line):
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def parse_tracker(text):
    """Rows of every table whose header is Company | Role | Lane | Status | Resume sent | Next action | Date.
    Returns (rows as dicts, unparsable lines)."""
    want = ["company", "role", "lane", "status", "resume sent", "next action", "date"]
    rows, bad, header = [], [], None
    for n, line in enumerate(text.splitlines(), 1):
        if not line.startswith("|"):
            header = None
            continue
        cells = split_md_row(line)
        if [c.lower() for c in cells] == want:
            header = want
            continue
        if header is None or all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if len(cells) != len(want):
            bad.append((n, f"{len(cells)} cells, expected {len(want)}", line.strip()[:120]))
            continue
        rows.append(dict(zip(want, cells), line=n))
    return rows, bad


def md_plain(s):
    """Drop bold markers and turn [[Note|alias]] into Note."""
    return re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", s.replace("*", "")).strip()


def tracker_applied_calls(rows):
    """Rows whose Status starts with 'Applied' -> `applied` arguments; rows missing a date go to bad."""
    calls, bad = [], []
    for r in rows:
        status = re.sub(r"\*", "", r["status"]).strip()
        if not status.lower().startswith("applied"):
            continue
        m = re.search(r"\d{4}-\d{2}-\d{2}", status) or re.search(r"\d{4}-\d{2}-\d{2}", r["date"])
        if not m:
            bad.append((r["line"], "applied row with no date", r["company"]))
            continue
        url = re.search(r"https?://[^\s)\]|]+", r["next action"] + " " + r["role"])
        resume = md_plain(r["resume sent"])
        calls.append({"line": r["line"], "company": md_plain(r["company"]), "role": md_plain(r["role"]),
                      "date": m.group(0), "resume": "" if resume in ("-", "") else resume,
                      "url": url.group(0) if url else ""})
    return calls, bad


def cmd_import_tracker(args):
    root = vault_root(args)
    if not args.dry_run:
        die("import-tracker only supports --dry-run in this milestone. Run each printed `applied` call instead.")
    path = args.file or vp(root, "tracker")
    if not os.path.exists(path):
        die(f"tracker not found at {path}.")
    rows, bad = parse_tracker(open(path, encoding="utf-8").read())
    calls, bad_calls = tracker_applied_calls(rows)
    print(f"# import-tracker --dry-run: {os.path.relpath(path, root) if path.startswith(root) else path}")
    print(f"{len(rows)} rows parsed, {len(calls)} applied, {len(bad) + len(bad_calls)} could not be parsed. "
          f"Nothing written.\n")
    q = lambda s: '"' + s.replace('"', '\\"') + '"'
    for c in calls:
        note = "company note exists" if find_company_note(root, c["company"]) else "would create a stub company note"
        cmd = f"cc.py applied --company {q(c['company'])} --role {q(c['role'])} --date {c['date']}"
        if c["resume"]:
            cmd += f" --resume {q(c['resume'])}"
        if c["url"]:
            cmd += f" --url {q(c['url'])}"
        print(f"- line {c['line']} ({note}):\n  {cmd}")
    if bad or bad_calls:
        print("\n## Could not parse")
        for n, why, what in sorted(bad + bad_calls):
            print(f"- line {n}: {why}: {what}")


SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_TARGETS = {  # template file -> PATHS key it is copied to by `setup` (others go to <job_search>/Templates/)
    "Fact Sheet.md": "fact_sheet",
    "Standard Answers.md": "standard_answers",
    "Next Session.md": "next_session",
    "Application Tracker.md": "tracker",
    "Connectors.md": "connectors",
}


def cmd_doctor(args):
    ok = True
    cfg = CFG
    print(f"{'ok ' if cfg['_exists'] else 'MISSING'} config: {cfg['_path']}")
    name = profile("name")
    if not name or name == "Alex Example":
        print("todo profile: set [profile] name, school, degrees, graduation and start_date in the config")
    else:
        print(f"ok  profile: {name}, {profile('school', '?')}, graduating {profile('graduation', '?')}, "
              f"start {profile('start_date', '?')}")
    root = vault_root(args)
    print(f"ok  vault: {root}")
    for key in ("fact_sheet", "standard_answers", "companies", "people", "data", "runs", "resume_dir"):
        p = vp(root, key)
        exists = os.path.exists(p)
        ok &= exists or key in ("runs", "resume_dir", "standard_answers")
        print(f"{'ok ' if exists else 'MISSING'} {key}: {PATHS[key]}")
    if os.path.exists(vp(root, "fact_sheet")):
        rows = read_fact_sheet(root)
        usable = sum(r["kind"] == "usable" for r in rows)
        print(f"{'ok ' if usable else 'todo'} Fact Sheet: {usable} usable facts, {len(rows) - usable} blocked")
    else:
        print("todo Fact Sheet: run `cc.py setup` to copy the template, then fill it in")
    boards = load_ats_rows(root)
    print(f"{'ok ' if boards else 'todo'} job boards for sweep: {len(boards)} in {PATHS['data']}/ats.tsv")
    c = connections_path(root)
    print(f"{'ok ' if c else 'todo'} LinkedIn export: {c or 'drop Connections.csv into ' + PATHS['data']}"
          + (f" ({len(load_connections(root))} connections)" if c else ""))
    if PRENAMED_GLOB:
        pre = glob.glob(PRENAMED_GLOB)
        print(f"{'ok ' if pre else 'todo'} pre-named people files: {len(pre)} ({PRENAMED_GLOB})")
    if HOME_NAME != "home region":
        print(f"ok  home region: {HOME_NAME}, target share {round(HOME_SHARE * 100)}% of every shortlist")
    else:
        print("todo home region: set [search] home_region and home_region_pattern (or set the share to 0)")
    print(f"ok  LinkedIn note limit: {note_limit()} characters")
    for prot in CFG["paths"].get("protected") or []:
        print(f"ok  protected (never edited): {prot}")
    if os.path.isdir(vp(root, "companies")):
        print(f"ok  companies in vault: {len(load_companies(root))}; career contacts: {len(load_people(root))}")
    phase, advice = search_phase()
    print(f"phase: {phase}. {advice}")
    if args.net:
        for ats, slug in (("ashby", "hadrian-automation"), ("lever", "palantir"), ("greenhouse", "anthropic")):
            try:
                n = len(fetch_board(ats, slug))
                print(f"ok  {ats} API reachable ({n} jobs at {slug})")
            except Exception as e:
                ok = False
                print(f"FAIL {ats} API: {e}")
    print("All checks passed." if ok else "Some checks need attention (see above).")


def cmd_init(args):
    """Write a starter config from config.example.toml. Never overwrites."""
    path = config_path(args)
    if os.path.exists(path):
        print(f"config already exists at {path}; nothing written. Edit it by hand.")
        return
    src = os.path.join(SKILL_DIR, "config.example.toml")
    if not os.path.exists(src):
        die(f"config.example.toml not found next to the skill ({src}). Reinstall the skill folder.")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = open(src, encoding="utf-8").read()
    if args.vault_path:
        text = re.sub(r'^vault = ".*"$', 'vault = ' + json.dumps(os.path.expanduser(args.vault_path)), text, count=1,
                      flags=re.M)
    open(path, "w", encoding="utf-8").write(text)
    print(f"wrote {path}. Next: edit [profile], [paths] and [search], then run `cc.py setup` and `cc.py doctor`.")


def cmd_setup(args):
    """Create the folder layout in the vault and copy templates and the seed job boards. Never overwrites."""
    root = vault_root(args)
    made = []
    for key in ("companies", "runs", "data", "people"):
        p = vp(root, key)
        if not os.path.isdir(p):
            os.makedirs(p)
            made.append(PATHS[key] + "/")
    tdir = os.path.join(SKILL_DIR, "templates")
    for fname in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
        if not fname.endswith(".md"):
            continue
        key = TEMPLATE_TARGETS.get(fname)
        dest = vp(root, key) if key else os.path.join(root, CFG["paths"]["job_search"], "Templates", fname)
        if os.path.exists(dest):
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        text = open(os.path.join(tdir, fname), encoding="utf-8").read().replace("{{date}}", TODAY.isoformat())
        open(dest, "w", encoding="utf-8").write(text)
        made.append(os.path.relpath(dest, root))
    seed = os.path.join(SKILL_DIR, "data", "ats.tsv")
    dest = ats_cache_path(root)
    if os.path.exists(seed) and not os.path.exists(dest):
        open(dest, "w", encoding="utf-8").write(open(seed, encoding="utf-8").read())
        made.append(os.path.relpath(dest, root))
    if made:
        print("created:\n" + "\n".join(f"- {m}" for m in made))
    else:
        print("everything already exists; nothing written.")
    print("Next: fill in the Fact Sheet and Standard Answers, then run `cc.py doctor`.")


def main():
    p = argparse.ArgumentParser(prog="cc.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", help=f"config file (default $JOB_KIT_CONFIG or {DEFAULT_CONFIG})")
    p.add_argument("--vault", help="vault root (default $CAREER_VAULT or [paths] vault in the config)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init", help="write a starter config file (never overwrites)")
    s.add_argument("--vault-path", help="folder to use as the vault (an Obsidian vault or any plain folder)")
    s.set_defaults(fn=cmd_init)
    s = sub.add_parser("setup", help="create the vault folders, copy templates and the seed job boards (never overwrites)")
    s.set_defaults(fn=cmd_setup)
    s = sub.add_parser("doctor"); s.add_argument("--net", action="store_true"); s.set_defaults(fn=cmd_doctor)
    s = sub.add_parser("facts"); s.add_argument("--all", action="store_true"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_facts)
    s = sub.add_parser("check", help="lint an opener; text from --file or stdin")
    s.add_argument("--kind", choices=list(LIMITS), default="message"); s.add_argument("--file")
    s.add_argument("--allow", action="append", help="a sourced company number, e.g. '$140M'")
    s.add_argument("--strict", action="store_true",
                   help="any number not on a usable Fact Sheet row is an ERROR (resume bullets, form answers, essays)")
    s.set_defaults(fn=cmd_check)
    s = sub.add_parser("jobs"); s.add_argument("--company", required=True); s.add_argument("--careers-url")
    s.add_argument("--ats", help="greenhouse:<slug> | lever:<slug> | ashby:<slug>")
    s.add_argument("--days", type=int, default=60); s.add_argument("--all", action="store_true")
    s.add_argument("--include-senior", action="store_true", help="also show senior, director and head-of roles")
    s.add_argument("--describe", help="print the full text of the posting whose URL or title contains this")
    s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_jobs)
    s = sub.add_parser("sweep", help="every board in Data/ats.tsv: business roles posted in the last N days")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--families", help="comma list of ops,bd,fin,pm,gtm (default [search] families in the config)")
    s.add_argument("--max-years", type=int,
                   help="drop roles asking for more years than this (default [search] max_years, 2)")
    s.add_argument("--include-senior", action="store_true")
    s.add_argument("--any-country", action="store_true", help="keep non-US roles (default: [search] us_only)")
    s.add_argument("--only", help="comma list of companies")
    s.add_argument("--loose", action="store_true", help="keep talent, legal, launch and other non-business ops titles")
    s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_sweep)
    s = sub.add_parser("questions", help="application questions for one Greenhouse or Lever posting")
    s.add_argument("--ats", required=True, help="greenhouse:<slug> | lever:<slug> | ashby:<slug> | bamboohr:<slug>"); s.add_argument("--id", required=True)
    s.set_defaults(fn=cmd_questions)
    s = sub.add_parser("warm"); s.add_argument("--company", required=True); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_warm)
    s = sub.add_parser("known"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_known)
    s = sub.add_parser("upsert-company"); s.add_argument("json_file")
    s.add_argument("--force-human", action="store_true", help="also overwrite status/next_action (only when the user asked)")
    s.set_defaults(fn=cmd_upsert_company)
    s = sub.add_parser("upsert-person"); s.add_argument("json_file"); s.set_defaults(fn=cmd_upsert_person)
    s = sub.add_parser("log-run"); s.add_argument("--mode", required=True); s.add_argument("--body-file", required=True); s.set_defaults(fn=cmd_log_run)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("mark", help="record what the user did (only when they say so)")
    s.add_argument("--person"); s.add_argument("--outreach"); s.add_argument("--next-touch")
    s.add_argument("--company"); s.add_argument("--status"); s.add_argument("--next-action")
    s.add_argument("--next-date"); s.add_argument("--date", help="YYYY-MM-DD, default today")
    s.add_argument("--event", choices=list(CADENCE),
                   help="set next_touch from the cadence table (default for --outreach sent: note-sent, 7 days)")
    s.set_defaults(fn=cmd_mark)
    s = sub.add_parser("applied", help="record an application the user submitted (only when they say so)")
    s.add_argument("--company", required=True); s.add_argument("--role", required=True)
    s.add_argument("--url", default=""); s.add_argument("--resume", default="", help="exact PDF filename sent")
    s.add_argument("--date", help="YYYY-MM-DD, default today"); s.add_argument("--referral", default="")
    s.add_argument("--also-url", action="append", default=[], help="same role at another location; repeatable")
    s.set_defaults(fn=cmd_applied)
    s = sub.add_parser("due", help="everything due within N days, one list sorted by date")
    s.add_argument("--days", type=int, default=0, help="0 = today or overdue (default)")
    s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_due)
    s = sub.add_parser("lint"); s.set_defaults(fn=cmd_lint)
    s = sub.add_parser("import-tracker", help="read Application Tracker.md; --dry-run prints the applied calls")
    s.add_argument("--dry-run", action="store_true"); s.add_argument("--file", help="tracker path (default: vault)")
    s.set_defaults(fn=cmd_import_tracker)
    args = p.parse_args()
    configure(load_config(args, required=args.cmd not in ("init",)))
    if args.cmd == "sweep":
        if not args.families:
            args.families = ",".join(CFG["search"].get("families") or ["ops", "bd", "fin", "pm", "gtm"])
        if args.max_years is None:
            args.max_years = int(CFG["search"].get("max_years", 2))
    args.fn(args)


if __name__ == "__main__":
    main()
