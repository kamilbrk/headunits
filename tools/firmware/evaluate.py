#!/usr/bin/env python3
"""Regression test for fw.py: does REPORT.md find what the evidence files say changed?

  evaluate.py run [--diffs-root DIR] [--out EVAL.md]   recall per category and pair, top miss patterns
  evaluate.py snapshot                                  store a normalised copy of every REPORT.md
  evaluate.py compare <diffs-root>                      line diffs of each REPORT.md against the snapshot

Ground truth is every `claude.evidence.md` under ANALYSIS/<vendor>/<platform>/<id>/. Each finding row
is reduced to its checkable identifiers (backticked terms, quoted labels, keys, paths, versions), and a
finding counts as found when enough of them appear in REPORT.md. The same check against the changed
lines of diff/**/*.diff says whether a miss was at least reachable.

--diffs-root points at fw.py output laid out as <old>..<new>/REPORT.md (fw.py's WORK/diffs) or as the
analysis tree itself; pairs are matched on `<old>..<new>`, and when no folder has that pair, on the new
firmware id alone, with a warning.

ANALYSIS is --analysis, else $FW_ANALYSIS, else ~/Dev/firmwares/_analysis (in the Docker image, pass it).
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ANALYSIS = Path(os.environ.get("FW_ANALYSIS", Path.home() / "Dev/firmwares/_analysis"))
GOLDEN = ANALYSIS / "_golden" / "reports"
FOUND_SHARE = 2 / 3  # share of a finding's identifiers REPORT.md must carry to count as found

CATEGORIES = [
    "app added/removed/version", "network endpoint/privacy", "security/OS config", "theme", "language",
    "factory/config key", "system property", "permission/manifest", "resolution/layout", "UI string/setting",
    "native/binary", "behaviour-only",
]
# First match wins, so the specific kinds come before the broad ones ("manifest versionName" is a version
# bump, not a manifest entry; "new <string> in a settings screen" is a UI string, not behaviour). The
# how-found text is tried first, then the bullet with its identifiers.
CATEGORY_RULES = [
    ("app added/removed/version", r"versionname|versioncode|version ?(bump|change|string)|new apk|apk (added|removed)|"
                                  r"app (added|removed)|(added|removed|new) (app|package)\b|\bpreinstall|\.apk\b"),
    ("network endpoint/privacy", r"https?://|\burl\b|endpoint|domain|host ?name|\bserver\b|upload|telemetry|"
                                 r"privacy|\bimei\b|analytics|tracking|\bip address|mqtt|network_security"),
    ("security/OS config", r"chmod|chown|selinux|sepolicy|setenforce|\.rc\b|init script|\bsu\b|\broot\b|\badb\b|"
                           r"verity|userdebug|test-keys|release-keys|certificate|keystore|debuggable|install_packages"),
    ("theme", r"\btheme|\bui_[a-z0-9]|_ui\b|m_iuiindex|ui ?index|\bid[5-9]\b|\bntg\d|\bnbt\b|\bevo\b|\bcic\b|"
              r"launcher style|\bskin"),
    ("language", r"language|locale|translation|values-[a-z]{2}\b"),
    ("factory/config key", r"factory|config_?key|sysprovideropt|ksw_data_|fatset|\.cfg\b|\.ini\b|config file|"
                           r"key=value|settings\.(global|system|secure)|settings key|provider key|contentobserver|"
                           r"putint|getint|xmlutils"),
    ("system property", r"build\.prop|\bprops?\b|systemproperties|getprop|setprop|\bro\.[a-z]|persist\.|"
                        r"system property"),
    ("permission/manifest", r"permission|manifest(?!\.tsv)|<receiver|<activity|<service|exported|testonly|"
                            r"intent-filter|intent filter|shareduserid|broadcast action"),
    ("resolution/layout", r"resolution|\b\d{3,4}x\d{3,4}\b|layout-|screen size|\bdpi\b|\bdp\b|density|orientation|"
                          r"dimens|qualifier"),
    ("UI string/setting", r"<string|string name|\blabel|\bstrings?\.xml|preference|switch|checkbox|\bmenu\b|"
                          r"setting|\bdialog|\btoast|\bbutton|\bui string|new string|<item>|arrays?\.xml|layout"),
    ("native/binary", r"\.so\b|\.ko\b|native|binary|\bstrings\b|firmware|\bmcu\b|\bdsp\b|\bhal\b|kernel|"
                      r"\bvendor/(bin|lib)|\belf\b|bootloader|manifest\.tsv|\bcrc\b|/lib"),
]

# How-found wording turned into concrete rule candidates. Checked in order; the first match names the miss.
MISS_PATTERNS = [
    ("init .rc / init script line (chmod, exec, service)", r"chmod|chown|\.rc\b|init script|\binit\b"),
    ("SELinux policy rule (sepolicy / .te / file_contexts)", r"sepolicy|\.te\b|file_contexts|selinux"),
    ("line in a shell script", r"\.sh\b|shell (script|function)"),
    ("key=value line in a .cfg/.ini/.conf file", r"key=value|\.cfg\b|\.ini\b|\.conf\b|\.properties\b"),
    ("other text config file (mixer_paths, apns-conf, /system/etc XML)",
     r"mixer_paths|apns|network_security|/system/etc|text file|text\.diff"),
    ("URL / host literal in code", r"https?://|\burl\b|\bhost|domain|endpoint"),
    ("SystemProperties key read or set in code",
     r"systemproperties|system property|property key|prop(erty)? (get|set)"),
    ("Settings.System/Global key in code (get/put, ContentObserver)",
     r"settings\.(system|global|secure)|settings[- ]key|contentobserver|putint|getint|sysprovideropt|ksw_data_|"
     r"sharedpreferences"),
    ("factory_config.xml item / factory menu entry", r"factory|xmlutils"),
    ("theme name / UI id string or constant", r"theme|ui_type|uiname|\bui_[a-z0-9]"),
    ("new id or widget in a layout XML",
     r"layout.*\b(id|switch|item|checkbox|textview|view)\b|settingswitchitem|click-handler id|"
     r"(view|new) ids? in layout|@\+id"),
    ("new layout file or resource qualifier folder", r"new layout|qualifier|layout-\w|res/layout|resolution-qualified"),
    ("layout attribute / dimens value change", r"layout attribute|changed layout|layout diff|dimens|"
     r"attribute change|layout: |ellipsize|visibility="),
    ("new <item> in an arrays.xml array", r"<item>|\barray"),
    ("new <string> resource (UI label)",
     r"<string|string name|strings\.xml|string resource|\blabel|android:text|hard-coded"),
    ("broadcast action / intent string in code", r"broadcast|intent action|action string"),
    ("package name string in code or dex", r"package[- ]name|new package names"),
    ("command sent to MCU / BT module (sendCommand, bit fields)", r"sendcommand|command|\bmcu\b|bit-field"),
    ("asset / drawable / raw file", r"asset|drawable|\.png|\.jpg|\braw/|mipmap|image"),
    ("native library / binary / APK entry change",
     r"\.so\b|native|binary|\bstrings\b|\.ko\b|\belf\b|crc|hash|unzip|manifest\.tsv|/lib"),
    ("new constant / enum value in code", r"constant|static final|\benum\b|ui_num|mode id|case \d"),
    ("new string literal in code or dex", r"string literal|literal|string in (the )?dex|new string"),
    ("changed literal value (option, flag default, multiplier)", r"option|flag default|multiplier|value change|changed int"),
    ("new branch / condition / early return in code",
     r"branch|condition|\bif\b|early return|switch on|returns|null check|bounds check"),
    ("removed code (method, call, condition)", r"\bremoved\b|deleted|dropped"),
    ("new class / method / field / call in decompiled code",
     r"new (java )?(class|method|file|function|helper|field|call)|new \w+\.java|added (class|method)|call-site|"
     r"new calls?\b|listener|handler"),
    ("manifest entry (component, permission, flag)", r"manifest(?!\.tsv)|permission|receiver|activity|<service|startservice"),
    ("build.prop / prop file value", r"build\.prop|\bprops?\b|\.prop\b"),
    ("translation (values-xx folder)", r"values-[a-z]{2}\b|translation|language|locale"),
    ("version name/code", r"version"),
    ("manual reading, no rule candidate", r"manual|reading|reasoning|inferred|by hand|^\s*code( diff)?\b"),
    ("no how-found given", r"^\s*$"),
]

STOP = {"true", "false", "null", "none", "return", "this", "void", "public", "private", "static", "final", "string",
        "int", "boolean", "new", "else", "case", "break", "high", "medium", "low", "unset", "(none)", "class",
        "import", "package", "override", "super", "throw", "catch", "diff", "code", "resources", "manifest",
        # attribute and widget names every layout or manifest hunk carries
        "android", "versionname", "versioncode", "layout_width", "layout_height", "layout_margin", "text", "src",
        "linearlayout", "relativelayout", "framelayout", "constraintlayout", "textview", "imageview", "button",
        "visibility", "setvisibility", "shareduserid", "name", "value", "item", "string", "integer", "bool"}
RES_PREFIX = re.compile(r"^(@\+?id/|@?(id|string|drawable|layout|color|dimen|style|array|mipmap)/|android:|"
                        r"R\.(id|string|layout|drawable)\.)")


@dataclass
class Finding:
    pair: str
    evidence: Path
    bullet: str
    where: str
    quote: str
    confidence: str
    how: str
    idents: list[str] = field(default_factory=list)
    category: str = ""
    report: str = ""  # found / partly / not / n-a (no identifiers)
    diffs: str = ""
    matched: list[str] = field(default_factory=list)


def split_row(line: str) -> list[str]:
    # `\|` is a literal pipe inside a cell; pipes inside backticks are not escaped in every file.
    cells, cur, tick = [], "", False
    i = 0
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if c == "`":
            tick = not tick
        if c == "|" and not tick:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    cells.append(cur.strip())
    return cells


def column_roles(header: list[str]) -> dict[str, int] | None:
    roles: dict[str, int] = {}
    for i, h in enumerate(header):
        h = h.lower()
        if h in ("bullet", "item"):
            roles["bullet"] = i
        elif "quote" in h:
            roles["quote"] = i
        elif h in ("evidence file", "diff file", "source", "evidence"):
            roles["where"] = i
        elif "confidence" in h:
            roles["confidence"] = i
        elif "how found" in h:
            roles["how"] = i
        elif "why left out" in h:
            return None  # a "checked and left out" table, not findings
    return roles if "bullet" in roles else None


def parse_evidence(path: Path, pair: str) -> list[Finding]:
    lines = path.read_text(errors="replace").splitlines()
    out: list[Finding] = []
    i = 0
    while i < len(lines):
        if (lines[i].lstrip().startswith("|") and i + 1 < len(lines)
                and re.fullmatch(r"\s*\|[\s:|-]+\|\s*", lines[i + 1])):
            roles = column_roles(split_row(lines[i]))
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                if roles:
                    cells = split_row(lines[i])
                    get = lambda r: cells[roles[r]] if r in roles and roles[r] < len(cells) else ""
                    if get("bullet"):
                        out.append(Finding(pair, path, get("bullet"), get("where"), get("quote"),
                                           get("confidence"), get("how")))
                i += 1
            continue
        i += 1
    return out


def clean_token(t: str) -> str:
    t = t.strip()
    t = re.sub(r"^[+-](?=\S)", "", t)
    t = t.strip(" \t,;:.'\"()[]{}<>/=")
    t = RES_PREFIX.sub("", t)
    t = re.sub(r"\(\)$", "", t)
    if "*" in t:  # btnSignal_AHD*, zxw_v_fragment_calibrate_*.xml: keep the longest literal piece
        t = max(t.split("*"), key=len).strip("_-.")
    return t


def useful(t: str) -> bool:
    if len(t) < 4 or t.lower() in STOP or t.isdigit():
        return False
    if re.fullmatch(r"[\d\s.,x:%-]+", t) and not re.fullmatch(r"\d+(\.\d+){2,}|\d{3,4}x\d{3,4}", t):
        return False
    # Evidence locations, not findings.
    if re.search(r"\.diff\b|^REPORT\.md$|^(apps|files|fs)/?$", t):
        return False
    if re.fullmatch(r"\d+(\.\d+)?(dp|sp|px|f|l|ms)", t, re.I) or re.fullmatch(r"[a-z]{1,8}", t):
        return False  # sizes and plain short words match anywhere
    if t.startswith("this.") or re.search(r"[(){};\s]", t) and not re.search(r"[A-Za-z]{3,} [A-Za-z]{3,}", t):
        return False  # member access and code fragments, not names
    return True


def distinctive(tok: str) -> bool:
    """A token inside a code snippet worth checking: constants, keys, paths, snake ids, packages, versions."""
    return bool(re.fullmatch(r"[A-Z][A-Z0-9]*(_[A-Z0-9]+)+", tok)            # UI_NUM_KSW_BMW_ID9
                or re.fullmatch(r"[a-z][\w-]*(\.[\w-]+){2,}", tok)           # com.x.y, ro.boot.x
                or re.fullmatch(r"(ro|persist|sys|vendor|debug|cpuinfo)\.[\w.]+", tok)
                or re.fullmatch(r"[a-z][a-z0-9]*(_[a-zA-Z0-9]+)+", tok)      # qualcomm_chip_type_M785
                or "/" in tok and len(tok) > 6
                or re.fullmatch(r"\d+(\.\d+){2,}(_\d+)?", tok))


def identifiers(f: Finding) -> list[str]:
    quote = re.split(r"\bContext:", f.quote)[0]
    text = " ".join([f.bullet, quote])
    if not f.quote:
        text += " " + f.where  # four-column files put the quotes in the evidence cell
    text = text.replace("\\|", "|")
    found: list[str] = []
    for span in re.findall(r"`([^`]+)`", text):
        span = span.strip()
        if re.fullmatch(r"[+-]?[^\s\"'=(),;]+", span):
            found.append(clean_token(span))
            continue
        kv = re.fullmatch(r"[+-]?([\w.\-/]+)\s*[=:]\s*([^\s\"]+)", span)
        if kv:
            found += [clean_token(kv[1]), clean_token(kv[2])]
            continue
        found += [clean_token(s) for s in re.findall(r'"([^"\n]{3,80})"', span)]
        found += [clean_token(s) for s in re.findall(r'="([^"\s]{3,80})$', span)]  # quote cut by the span
        found += re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", span)
        found += [clean_token(s) for s in re.findall(r">([^<>\n]{3,80})<", span + "<")
                  if not re.search(r"[{};=]", s)]
        found += [clean_token(t) for t in re.findall(r"[\w.$/-]+", span) if distinctive(clean_token(t))]
    bare = re.sub(r"`[^`]+`", " ", text)
    found += [clean_token(s) for s in re.findall(r'"([^"\n]{3,80})"', bare)]
    found += re.findall(r"https?://[^\s`)\"']+", text)
    found += re.findall(r"\b\d+\.\d+(?:\.\d+)+(?:_\d+)?\b", bare)
    found += [t for t in re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", bare)]
    seen, out = set(), []
    for t in found:
        if useful(t) and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


def categorise(f: Finding) -> str:
    for text in (f.how, f"{f.bullet} {f.quote}"):
        low = text.lower()
        for name, rx in CATEGORY_RULES:
            if re.search(rx, low):
                return name
    return "behaviour-only"


def miss_pattern(f: Finding) -> str:
    how = f.how.lower()
    for name, rx in MISS_PATTERNS:
        if re.search(rx, how):
            return name
    return "other"


def variants(t: str) -> list[str]:
    """A path also counts when the report names only its file (layout/foo.xml -> foo.xml, foo)."""
    t = t.lower()
    out = [t]
    if "/" in t:
        base = t.rstrip("/").rsplit("/", 1)[-1]
        out.append(base)
        stem = base.rsplit(".", 1)[0]
        if "." in base and len(stem) >= 5:
            out.append(stem)
    return [v for v in out if len(v) >= 4]


def contains(text: str, tok: str) -> bool:
    r"""`tok` in lower-cased `text` as a whole name, as (?<![\w.])tok(?![\w.]): `id7` is not in `id7_v2` and
    `1.3` is not in `1.3.1`. A dot next to letters is a qualifier or an extension, not more of the same
    name, so `set_wallpaper` still counts in `android.permission.set_wallpaper` and `update_engine` in
    `update_engine.rc`."""
    def joined(c: str, beyond: str, own: str) -> bool:
        if c == ".":  # a full stop ending a sentence is not part of the name either
            return (beyond.isalnum() or beyond == "_") and not (beyond.isalpha() and own.isalpha())
        return bool(c) and (c.isalnum() or c == "_")

    i = text.find(tok)
    while i != -1:
        j = i + len(tok)
        if not joined(text[i - 1:i], text[i - 2:i - 1], tok[:1]) and not joined(text[j:j + 1], text[j + 1:j + 2], tok[-1:]):
            return True
        i = text.find(tok, i + 1)
    return False


def in_title(tok: str, title: str) -> bool:
    """Platform, model and build names every report's title carries (M600, NEXAI, GT7) match for free."""
    t = tok.lower()
    return contains(title, t) or t in set(re.split(r"[^a-z0-9]+", title)) | set(re.findall(r"[a-z]+|\d+", title))


def verdict(idents: list[str], text: str) -> tuple[str, list[str]]:
    if not idents:
        return "n/a", []
    hit = [t for t in idents if any(contains(text, v) for v in variants(t))]
    if len(hit) == len(idents) or len(hit) >= FOUND_SHARE * len(idents):
        return "found", hit
    return ("partly" if hit else "not"), hit


def changed_lines(diff_dir: Path) -> str:
    """Changed lines and file headers only: context lines carry identifiers the change did not touch."""
    parts = []
    for p in sorted(diff_dir.rglob("*.diff")):
        with p.open(errors="replace") as fh:
            for line in fh:
                if line.startswith(("+", "-", "diff ", "Only in", "Binary files", "rename ")):
                    parts.append(line)
    return "".join(parts).lower()


def pair_key(folder: Path) -> str:
    """`<old>..<new>` for an analysis folder: one new id can be diffed against more than one old one."""
    old = (folder / "compared-with.txt").read_text().split()[0] if (folder / "compared-with.txt").is_file() else "?"
    return f"{old}..{folder.name}"


def pairs(root: Path) -> dict[str, Path]:
    """`<old>..<new>` -> folder holding REPORT.md, for either layout."""
    out = {}
    for rep in sorted(root.rglob("REPORT.md")):
        if "_golden" in rep.parts:
            continue
        d = rep.parent
        out[pair_key(d.parent) if d.name == "diff" else d.name] = d
    return out


def evidence_files() -> list[tuple[str, Path]]:
    return [(pair_key(p.parent), p) for p in sorted(ANALYSIS.glob("*/*/*/claude.evidence.md"))]


def pct(a: float, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "-"


def cmd_run(args) -> None:
    reports = pairs(Path(args.diffs_root)) if args.diffs_root else pairs(ANALYSIS)
    by_new: dict[str, list[str]] = defaultdict(list)
    for key in reports:
        by_new[key.split("..")[-1]].append(key)
    findings: list[Finding] = []
    parsed: list[tuple[str, int, int]] = []
    for pair, ev in evidence_files():
        fs = parse_evidence(ev, pair)
        d = reports.get(pair)
        if not d and args.diffs_root and len(by_new.get(pair.split("..")[-1], [])) == 1:
            key = by_new[pair.split("..")[-1]][0]
            d = reports[key]
            print(f"warning: no {pair} under {args.diffs_root}; scoring {key}, matched on the new id only", file=sys.stderr)
        report = (d / "REPORT.md").read_text(errors="replace").lower() if d else ""
        title = report.split("\n", 1)[0]
        diffs = changed_lines(d) if d else ""
        for f in fs:
            f.idents = [t for t in identifiers(f) if not in_title(t, title)]
            f.category = categorise(f)
            f.report, f.matched = verdict(f.idents, report)
            f.diffs, _ = verdict(f.idents, report + diffs)
        parsed.append((pair, len(fs), sum(1 for f in fs if f.idents)))
        findings += fs
        if not d:
            print(f"warning: no REPORT.md for {pair}", file=sys.stderr)

    total = len(findings)
    checkable = [f for f in findings if f.report != "n/a"]
    print(f"parsed {total} findings from {len(parsed)} evidence files ({len(checkable)} with identifiers, "
          f"{sum(len(f.idents) for f in findings)} identifiers)")
    for pair, n, c in parsed:
        print(f"  {pair:72} {n:3} findings, {c:3} checkable")

    def row(fs: list[Finding]) -> tuple[int, int, int, int, int]:
        c = [f for f in fs if f.report != "n/a"]
        return (len(fs), len(c), sum(f.report == "found" for f in c), sum(f.report == "partly" for f in c),
                sum(f.report != "found" and f.diffs in ("found", "partly") for f in c))

    md = ["# fw.py recall against the evidence files", "",
          f"Generated by `tools/firmware/evaluate.py run`. {total} findings parsed from {len(parsed)} "
          f"`claude.evidence.md` files; {len(checkable)} carry checkable identifiers "
          f"(backticked terms, quoted labels, keys, paths, versions). A finding is **found** when REPORT.md "
          f"holds at least two thirds of its identifiers, **partly** when it holds some. **In diffs** counts "
          f"findings REPORT.md does not fully find whose identifiers are on changed lines of `diff/**/*.diff`: "
          f"reachable, not highlighted.", ""]

    n, c, fo, pa, rd = row(findings)
    md += ["## Overall", "", "| Findings | Checkable | Found | Partly | Found or partly | Not highlighted, in diffs |",
           "|---|---|---|---|---|---|",
           f"| {n} | {c} | {fo} ({pct(fo, c)}) | {pa} ({pct(pa, c)}) | {pct(fo + pa, c)} | {rd} ({pct(rd, c)}) |", ""]
    print(f"\noverall: found {fo}/{c} ({pct(fo, c)}), found or partly {pct(fo + pa, c)}, "
          f"not highlighted but in diffs {rd}")

    md += ["## By category", "", "| Category | Findings | Checkable | Found | Found or partly | In diffs only |",
           "|---|---|---|---|---|---|"]
    print("\nby category:")
    for cat in CATEGORIES:
        fs = [f for f in findings if f.category == cat]
        if not fs:
            continue
        n, c, fo, pa, rd = row(fs)
        md.append(f"| {cat} | {n} | {c} | {pct(fo, c)} | {pct(fo + pa, c)} | {rd} |")
        print(f"  {cat:28} {n:4} findings, {c:4} checkable, found {pct(fo, c):>4}, found/partly {pct(fo + pa, c):>4}")
    md.append("")

    misses = [f for f in checkable if f.report == "not"]
    by_pattern: dict[str, list[Finding]] = defaultdict(list)
    for f in misses:
        by_pattern[miss_pattern(f)].append(f)
    top = sorted(by_pattern.items(), key=lambda kv: -len(kv[1]))
    md += ["## Top miss patterns", "",
           f"How the evidence found the {len(misses)} checkable findings REPORT.md misses entirely, grouped by "
           f"the wording of their \"how found\" column. Each is a candidate rule.", ""]
    print(f"\ntop miss patterns ({len(misses)} misses):")
    for name, fs in top[:args.top]:
        rd = sum(f.diffs != "not" for f in fs)
        md.append(f"**{name}**: {len(fs)} misses, {rd} with identifiers on changed diff lines")
        print(f"  {len(fs):4}  {name}  ({rd} in diffs)")
        for f in sorted(fs, key=lambda f: -len(f.idents))[:3]:
            rel = f.evidence.relative_to(ANALYSIS)
            ids = ", ".join(f"`{t}`" for t in f.idents[:3])
            md.append(f"- `{rel}`: {trim(f.bullet, 70)} ({ids}). How found: {trim(f.how, 90)}")
        md.append("")

    md += ["## By pair", "", "| Pair | Findings | Checkable | Found | Found or partly | In diffs only |",
           "|---|---|---|---|---|---|"]
    for pair, _, _ in parsed:
        n, c, fo, pa, rd = row([f for f in findings if f.pair == pair])
        md.append(f"| {pair.split('..')[-1]} | {n} | {c} | {pct(fo, c)} | {pct(fo + pa, c)} | {rd} |")
    md.append("")
    Path(args.out).write_text("\n".join(md))
    print(f"\nwrote {args.out}")
    if args.dump:
        with open(args.dump, "w") as fh:
            for f in findings:
                fh.write(f"{f.pair}\t{f.category}\t{f.report}\t{f.diffs}\t{miss_pattern(f)}\t{f.bullet}\t"
                         f"{'; '.join(f.idents)}\t{f.how}\n")


def trim(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s.replace("|", "/")).strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def normalise(report: str) -> str:
    """Strip what differs between machines and runs but says nothing about the firmware."""
    lines = [re.sub(r"/(Users|home)/[^/\s`]+/", "~/", l.rstrip()) for l in report.splitlines()]
    return "\n".join(lines).strip() + "\n"


def cmd_snapshot(args) -> None:
    src = pairs(Path(args.diffs_root)) if args.diffs_root else pairs(ANALYSIS)
    GOLDEN.mkdir(parents=True, exist_ok=True)
    for key, d in src.items():
        (GOLDEN / f"{key}.md").write_text(normalise((d / "REPORT.md").read_text(errors="replace")))
    print(f"stored {len(src)} normalised reports in {GOLDEN}")


def cmd_compare(args) -> None:
    current = pairs(Path(args.diffs_root))
    golden = {p.stem: p for p in GOLDEN.glob("*.md")}
    if not golden:
        sys.exit(f"error: no snapshot in {GOLDEN}; run `evaluate.py snapshot` first")
    same = changed = 0
    for key in sorted(set(current) & set(golden)):
        a = golden[key].read_text().splitlines()
        b = normalise((current[key] / "REPORT.md").read_text(errors="replace")).splitlines()
        if a == b:
            same += 1
            continue
        changed += 1
        diff = list(difflib.unified_diff(a, b, f"golden/{key}", f"current/{key}", n=0, lineterm=""))
        added = sum(l.startswith("+") and not l.startswith("+++") for l in diff)
        removed = sum(l.startswith("-") and not l.startswith("---") for l in diff)
        print(f"== {key}: +{added} -{removed}")
        if not args.quiet:
            print("\n".join(diff[2:]))
    only_golden = sorted(set(golden) - set(current))
    print(f"\n{same} identical, {changed} changed, {len(only_golden)} in snapshot but not in {args.diffs_root}, "
          f"{len(set(current) - set(golden))} new")
    if changed and args.strict:
        sys.exit(1)


def main() -> None:
    global ANALYSIS, GOLDEN
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", type=Path, default=ANALYSIS, help=f"analysed firmware tree (default: {ANALYSIS})")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run", help="score REPORT.md files against the evidence files")
    p.add_argument("--diffs-root", help="fw.py output to score (default: the analysis tree's own diff/ folders)")
    p.add_argument("--out", help="default: ANALYSIS/EVAL.md")
    p.add_argument("--top", type=int, default=12, help="miss patterns to list")
    p.add_argument("--dump", help="write one TSV row per finding here")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("snapshot", help="store normalised REPORT.md copies in ANALYSIS/_golden/reports")
    p.add_argument("--diffs-root", help="take reports from here instead of the analysis tree")
    p.set_defaults(fn=cmd_snapshot)
    p = sub.add_parser("compare", help="diff REPORT.md files against the snapshot")
    p.add_argument("diffs_root")
    p.add_argument("--quiet", action="store_true", help="per-pair counts only")
    p.add_argument("--strict", action="store_true", help="exit 1 when any report changed")
    p.set_defaults(fn=cmd_compare)
    args = ap.parse_args()
    ANALYSIS, GOLDEN = args.analysis, args.analysis / "_golden" / "reports"
    if not ANALYSIS.is_dir():
        sys.exit(f"error: analysis tree {ANALYSIS} not found; pass --analysis <dir> (or set FW_ANALYSIS)")
    if getattr(args, "out", "unset") is None:
        args.out = str(ANALYSIS / "EVAL.md")
    args.fn(args)


if __name__ == "__main__":
    main()
