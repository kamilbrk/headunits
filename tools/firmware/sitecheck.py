#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check a `fw.py diff` folder against the site's own data.

  sitecheck.py <diff-dir>                   print Markdown findings
  sitecheck.py <diff-dir> --json out.json   also write them as JSON

Three checks, all read-only:
  - themes the new build adds that src/data/themes lacks, or whose `since` is blank or disagrees;
  - factory-config keys the new build reads or ships that src/data/factory-settings does not document;
  - the generated frontmatter (WORK/<id>/meta.json, or frontmatter.generated.md beside the diff
    folder) against the site page's frontmatter.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(os.environ.get("FW_WORK", Path.home() / "Dev/firmwares/_work"))
# This checkout when the script sits in it; inside the Docker image there is none, so --site is needed.
SITE = Path(os.environ["HEADUNITS_SITE"]) if os.environ.get("HEADUNITS_SITE") else Path(__file__).resolve().parents[2]
# The example factory file each vendor's settings page is written against. Data, not logic.
EXAMPLE_XML = {"ksw": "factory_config.xml", "zxw": "zxw_factory_config.xml"}
# Numbered themes far above the site's highest number belong to other customers' builds.
NUMBER_SLACK = 20


# --------------------------------------------------------------------------- frontmatter


def frontmatter(text: str) -> dict:
    """Just enough YAML for this site: scalars, lists of scalars and one level of maps."""
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    out: dict = {}
    if not m:
        return out
    key = None
    for line in m[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            value = value.strip().strip('"\'')
            out[key] = value if value else None
        elif key and (item := re.match(r"\s+-\s+(.*)", line)):
            if not isinstance(out.get(key), list):
                out[key] = []
            out[key].append(item[1].strip().strip('"\''))
        elif key and (sub := re.match(r"\s+(\w+):\s*(.*)", line)):
            if not isinstance(out.get(key), dict):
                out[key] = {}
            out[key][sub[1]] = sub[2].strip().strip('"\'')
    return out


def slug(fw_id: str) -> str:
    """The site's reference form of a release id: Ksw-Q-Userdebug_OS_v3.9.4-ota -> ksw-q-userdebug_os_v394-ota."""
    return fw_id.lower().replace(".", "")


# --------------------------------------------------------------------------- site


@dataclass
class Release:
    id: str
    vendor: str
    platform: str
    date: str
    path: Path
    meta: dict


@dataclass
class Site:
    releases: dict[str, Release]  # by slug
    themes: dict[str, list[dict]]  # by vendor
    keys: dict[str, dict[str, str]]  # vendor -> key -> "documented" | "commented out" | "unverified"
    example_keys: dict[str, set[str]]


def load_site(root: Path) -> Site:
    releases = {}
    for p in sorted((root / "src/data/updates").glob("*/*/*.md")):
        meta = frontmatter(p.read_text(errors="replace"))
        releases[slug(p.stem)] = Release(p.stem, p.parent.parent.name, p.parent.name, meta.get("date") or "", p, meta)
    themes: dict[str, list[dict]] = {}
    for p in sorted((root / "src/data/themes").glob("*/*/index.md")):
        meta = frontmatter(p.read_text(errors="replace"))
        since = meta.get("since") or []
        meta["since"] = [since] if isinstance(since, str) else since
        meta["path"] = p.relative_to(root).as_posix()
        themes.setdefault(p.parent.parent.name, []).append(meta)
    keys: dict[str, dict[str, str]] = {}
    for p in sorted((root / "src/data/factory-settings").glob("*/*.md")):
        vendor = p.parent.name
        lines = p.read_text(errors="replace").splitlines()
        for i, line in enumerate(lines):
            if m := re.match(r"\s*(#\s*)?configKey:\s*\"?([\w.-]+)", line):
                end = next((j for j in range(i + 1, len(lines)) if re.match(r"\s*#?\s*-\s+name:", lines[j])), len(lines))
                status = "commented out" if m[1] else \
                    "unverified" if any("unverified: true" in x for x in lines[i + 1:end]) else "documented"
                keys.setdefault(vendor, {}).setdefault(m[2], status)
    example = {}
    for vendor, name in EXAMPLE_XML.items():
        f = root / "public" / name
        if f.is_file():
            example[vendor] = set(re.findall(r"<(\w+)[\s>/]", f.read_text(errors="replace")))
    return Site(releases, themes, keys, example)


# --------------------------------------------------------------------------- diff


@dataclass
class DiffLine:
    file: str
    inner: str
    no: int
    sign: str  # "+", "-" or " "
    text: str


def read_diffs(root: Path) -> list[DiffLine]:
    out = []
    for path in sorted(root.rglob("*.diff")):
        rel, inner = path.relative_to(root).as_posix(), ""
        with path.open(errors="replace") as fh:
            for no, raw in enumerate(fh, 1):
                if raw.startswith("diff --git "):
                    inner = ""
                elif raw.startswith("+++ "):
                    inner = "" if raw.startswith("+++ /dev/null") else raw[6:].rstrip()
                elif raw.startswith("--- "):
                    if not inner and not raw.startswith("--- /dev/null"):
                        inner = raw[6:].rstrip()
                elif raw[:1] in "+- ":
                    out.append(DiffLine(rel, inner, no, raw[0], raw[1:].rstrip("\n")))
    return out


@dataclass
class Finding:
    check: str
    kind: str
    subject: str
    detail: str
    evidence: list[str] = field(default_factory=list)


def cite(ln: DiffLine) -> str:
    return f"{ln.file} ({ln.inner}):{ln.no}: {ln.sign}{ln.text.strip()[:200]}"


THEME_FILE = re.compile(r"theme", re.I)
STR_CONST = re.compile(r'static final String \w+ = "([A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+)";')
# The same constants as fw.py's THEME_CONST: UI_NUM_KSW_BMW_ID9 = 56 and UI_INDEX_KSW_BWM_ID6 = 9.
# The name is group 1 or 2 (UI_NUM_ dropped, as the site names these themes), the number group 3.
NUM_THEME = re.compile(r"\bUI_(?:NUM_(\w+?)|(\w+_ID\w*?))\s*=\s*(\d+);")


def num_theme(m: re.Match) -> tuple[str, int]:
    return m[1] or m[2], int(m[3])


def app_of(rel: str) -> str:
    parts = rel.split("/")
    return parts[1] if len(parts) > 2 else re.sub(r"\.(code|resources)(\.large)?\.diff$", "", parts[-1])


def new_themes(lines: list[DiffLine], facts: dict, report: str) \
        -> tuple[dict[str, list[str]], dict[str, tuple[int, list[str]]], list[str]]:
    """Theme names and numbered theme ids this build adds: {name: evidence}, {name: (number, evidence)},
    and notes on anything the check could not decide."""
    def usable(name: str) -> bool:
        return not re.search(r"_(DATA|INDEX|KEY|ACTION|URI|PATH)(_|$)", name)

    notes: list[str] = []
    per_app: dict[str, dict[str, list[str]]] = {}
    known_before: set[str] = set()
    context: dict[str, int] = {}
    for ln in lines:
        if THEME_FILE.search(ln.inner) and (m := STR_CONST.search(ln.text)):
            if ln.sign != "+":
                known_before.add(m[1])
                context[app_of(ln.file)] = context.get(app_of(ln.file), 0) + 1
            elif usable(m[1]):
                per_app.setdefault(app_of(ln.file), {}).setdefault(m[1], []).append(cite(ln))
    if "theme_strings_before" in facts:
        # fw.py compared every app's whole theme class, old against new, so no vote is needed.
        named = {n: [ev for names in per_app.values() for ev in names.get(n, [])][:2] + ["facts.json theme_strings"]
                 for n in facts.get("theme_strings", []) if usable(n)}
    else:
        # Every app carries its own copy of the theme-name class, and one copy catching up with names the
        # launcher has had for years is not a new theme. A name counts when no copy shows it as old and at
        # least two copies gain it, or one copy gains a few names against a large unchanged part (a small
        # edit, not a copy being rewritten to catch up).
        section = report.split("Theme names added (UiThemeUtils)", 1)
        if len(section) > 1:
            body = section[1].split("\n- ", 1)[0]
            rows = re.findall(r"^  - `([\w.]+)`: (.*)$", body, re.M) or [("(report)", body)]
            for app, row in rows:
                for name in re.findall(r"`(\w+)`", row):
                    if usable(name):
                        per_app.setdefault(app, {}).setdefault(name, []).append(f"REPORT.md theme names added ({app})")
        votes: dict[str, list[str]] = {}
        for app, names in per_app.items():
            for n, ev in names.items():
                votes.setdefault(n, []).extend(ev)
        apps_with = {n: sum(n in names for names in per_app.values()) for n in votes}
        small_edit = {app for app, names in per_app.items() if 3 * len(names) <= context.get(app, 0)}
        named = {n: ev for n, ev in votes.items() if n not in known_before
                 and (apps_with[n] >= 2 or any(n in per_app[app] for app in small_edit))}
        # Older fw.py listed names new to any one app; a name it did not list at all is still not new.
        if "theme_strings" in facts:
            named = {n: ev for n, ev in named.items() if n in facts["theme_strings"]}
    for name in facts_list(facts, "theme_names"):
        if name in named:
            named[name].append("facts.json theme_names")
    numbered: dict[str, tuple[int, list[str]]] = {}
    # fw.py computes these over the complete decompiled trees, so they are trusted as they are...
    # ...unless the diff shows the constant only in files that are new as a whole (code moved, not added).
    has_old = {ln.inner for ln in lines if ln.sign != "+"}
    seen_in: dict[str, set[bool]] = {}
    for ln in lines:
        if ln.sign == "+":
            for m in NUM_THEME.finditer(ln.text):
                seen_in.setdefault(num_theme(m)[0], set()).add(ln.inner in has_old)
    for entry in facts_list(facts, "themes"):
        if (m := NUM_THEME.search(entry + ";")) and seen_in.get(num_theme(m)[0]) != {False}:
            name, num = num_theme(m)
            numbered.setdefault(name, (num, []))[1].append(f"facts.json themes: {entry}")
    if "themes" not in facts:
        # Older facts.json: only the diff lines. A name on a context or '-' line in any app is not new;
        # when the apps that carry theme ids disagree about the rest, say so rather than pick one.
        old_names = {num_theme(m)[0] for ln in lines if ln.sign != "+" for m in NUM_THEME.finditer(ln.text)}
        num_app: dict[str, dict[str, tuple[int, list[str]]]] = {}
        carriers: set[str] = set()
        for ln in lines:
            for m in NUM_THEME.finditer(ln.text):
                carriers.add(app_of(ln.file))
                name, num = num_theme(m)
                if ln.sign == "+" and name not in old_names:
                    num_app.setdefault(app_of(ln.file), {}).setdefault(name, (num, []))[1].append(cite(ln))
        agreed = [set(num_app.get(app, {})) for app in carriers]
        if num_app and all(x == agreed[0] for x in agreed):
            numbered = {n: v for names in num_app.values() for n, v in names.items()}
        elif num_app:
            notes.append("facts.json predates theme ids; re-run fw.py diff. The diff adds numbered theme ids in "
                         + ", ".join(sorted(num_app)) + " but not in every app that carries them: "
                         + ", ".join(f"`{n}`" for n in sorted({n for v in num_app.values() for n in v})[:12]))
    return named, numbered, notes


def facts_list(facts: dict, key: str, part: str = "added") -> list:
    """facts[key][part], or facts[key] itself when an older facts.json stored a flat list of additions."""
    v = facts.get(key)
    if isinstance(v, dict):
        return list(v.get(part) or [])
    return list(v or []) if part == "added" else []


def release_order(site: Site, vendor: str, platform: str) -> list[str]:
    """Slugs of one platform's releases, oldest first by build date."""
    rel = [r for r in site.releases.values() if r.vendor == vendor and r.platform == platform]
    return [slug(r.id) for r in sorted(rel, key=lambda r: (r.date, r.id))]


def line_of(fw_id: str) -> str:
    """The release line a build belongs to: its id with the version number and brand prefix taken out."""
    return re.sub(r"^[a-z]+-", "", re.sub(r"v\d+\w*?(?=-ota$)|^\d{8}", "#", slug(fw_id)))


def line_key(site: Site, ref: str) -> tuple[str, str]:
    """(platform, line) for a `since` entry: `zxw/gt6/20240613gt_ksw` or a bare `Ksw-Q-..._v3.4.1-ota`."""
    parts = ref.split("/")
    rel = site.releases.get(slug(parts[-1]))
    platform = parts[1] if len(parts) == 3 else rel.platform if rel else ""
    return platform, line_of(parts[-1])


def check_themes(site: Site, vendor: str, platform: str, old_id: str, new_id: str, lines: list[DiffLine], facts: dict,
                 report: str) -> list[Finding]:
    named, numbered, notes = new_themes(lines, facts, report)
    out = [Finding("themes", "stale-facts", "", note) for note in notes]
    by_id = {t["id"].lower(): t for t in site.themes.get(vendor, []) if t.get("id")}
    by_num = {int(t["number"]): t for t in site.themes.get(vendor, []) if (t.get("number") or "").isdigit()}
    top = max(by_num) if by_num else 0
    bottom = min(by_num) if by_num else 0
    order = release_order(site, vendor, platform)
    new_slug, old_slug = slug(new_id), slug(old_id)
    here = f"{vendor}/{platform}/{new_slug}"
    skipped = 0
    candidates = [(n, None, ev) for n, ev in named.items()] + [(n, num, ev) for n, (num, ev) in numbered.items()]
    for name, num, ev in candidates:
        theme = by_id.get(name.lower()) or (by_num.get(num) if num is not None else None)
        if num is not None and (
                (theme is None and not bottom <= num <= top + NUMBER_SLACK)
                or (theme is not None and (theme.get("id") or "").lower() != name.lower() and name.lower() not in by_id)):
            # Another customer's numbering: outside the site's range, or reusing a number the site gives
            # to a different theme name.
            skipped += 1
            continue
        label = f"`{name}`" + (f" ({num})" if num is not None else "")
        if theme is None:
            out.append(Finding("themes", "missing", name, f"{label} is new in {new_id} but has no page in src/data/themes/{vendor}", ev[:3]))
            continue
        same_line = [s for s in theme["since"] if line_key(site, s)[1] == line_of(new_id) and line_key(site, s)[0] in ("", platform)]
        if not theme["since"]:
            out.append(Finding("themes", "since-blank", name, f"{label}: `since` is blank; this build adds it: `{here}`", ev[:2]))
        elif not same_line:
            out.append(Finding("themes", "since-missing-line", name,
                               f"{label}: `since` names no {line_of(new_id).replace('#', '*')} release; this build adds it: `{here}`", ev[:2]))
        else:
            for s in same_line:
                ss = slug(s.split("/")[-1])
                if ss == new_slug or ss not in order or new_slug not in order:
                    continue
                i_s, i_new = order.index(ss), order.index(new_slug)
                i_old = order.index(old_slug) if old_slug in order else i_new - 1
                if i_s > i_new:
                    out.append(Finding("themes", "since-too-late", name,
                                       f"{label}: site says `{s}`, but it is already added in `{here}`", ev[:2]))
                elif i_s <= i_old:
                    out.append(Finding("themes", "since-too-early", name,
                                       f"{label}: site says `{s}`, but the code first adds it in `{here}` (compared with {old_id})", ev[:2]))
    if skipped:
        out.append(Finding("themes", "other-range", "", f"{skipped} numbered theme id(s) outside the site's numbering ({bottom} to {top}) were skipped"))
    return out


def factory_keys(lines: list[DiffLine], facts: dict, report: str, known: set[str], example_only: set[str],
                 not_keys: set[str]) -> dict[str, tuple[bool, list[str]]]:
    """Factory-config keys this build reads or ships: {key: (only in a file new to this diff, evidence)}."""
    keys: dict[str, tuple[bool, list[str]]] = {}

    def add(k: str, fresh_file: bool, ev: str) -> None:
        if k in not_keys or re.fullmatch(r"[A-Z0-9_]+", k):
            return
        old_fresh, evs = keys.get(k, (True, []))
        keys[k] = (old_fresh and fresh_file, evs + [ev])

    # Files that are wholly new in this diff: every key in them looks added, whether or not it is.
    has_old = {ln.inner for ln in lines if ln.sign != "+"}
    added_text = set(re.findall(r"^- `([^`]+)`$", report.split("## Added text files", 1)[1].split("\n## ", 1)[0], re.M)) \
        if "## Added text files" in report else set()
    for k in facts_list(facts, "config_keys"):
        add(k, False, "facts.json config_keys")
    # facts.json has the full lists; REPORT.md stops at 30 names with "+N more".
    for entry in facts.get("factory_settings") or []:
        for k in entry.get("added", []):
            add(k, bool(entry.get("file_added")), f"facts.json factory_settings: {entry.get('file')}")
    rows = r"^- Factory config keys added.*$" if "factory_settings" in facts else r"^- Factory (?:config keys|settings) added.*$"
    for row in re.findall(rows, report, re.M):
        rel = re.search(r"added in `([^`]+)`", row)
        for k in re.findall(r"`<?(\w+)>?`", row.split(":", 1)[1]):
            add(k, bool(rel and rel[1] in added_text), "REPORT.md: " + row[:120])
    xml_old = {m[1] for ln in lines if ln.sign != "+" and "factory" in ln.inner.lower() for m in [re.match(r"\s*<(\w+)>", ln.text)] if m}
    for ln in lines:
        if ln.sign == "+" and "factory" in ln.inner.lower() and ln.inner.endswith(".xml") and (m := re.match(r"\s*<(\w+)>[^<]*</\1>", ln.text)):
            if m[1] not in xml_old:
                add(m[1], ln.inner not in has_old, cite(ln))
    # Code that names the factory keys, as constants, switch cases or tag comparisons while parsing the
    # XML. A file counts once it already names several keys the site knows, so no class or vendor name
    # is needed.
    literal = re.compile(r'static final String (\w+) = "([A-Za-z][\w]*)";|case "([A-Za-z][\w]*)":|'
                         r'\.equals(?:IgnoreCase)?\("([A-Za-z][\w]*)"\)')
    names: dict[str, list[tuple[str, str, DiffLine]]] = {}
    for ln in lines:
        for m in literal.finditer(ln.text):
            names.setdefault(ln.inner, []).append((m[1] or "", m[2] or m[3] or m[4], ln))
    # Outside such files, a literal still counts when the example XML has the tag and the old code never named it.
    old_literals = {v for found in names.values() for _, v, ln in found if ln.sign != "+"}
    for inner, found in names.items():
        for _, v, ln in found:
            if ln.sign == "+" and v in example_only and v not in old_literals:
                add(v, inner not in has_old, cite(ln))
    for inner, found in names.items():
        if len({v for _, v, _ in found if v in known}) < 3:
            continue
        gone = {v for _, v, ln in found if ln.sign != "+"}
        for field_name, v, ln in found:
            if ln.sign == "+" and v not in gone and not re.search(r"(^|_)(TAG|CLASS|ACTION|PKG|PATH|URL|CLS|NAME)$", field_name):
                add(v, inner not in has_old, cite(ln))
    return keys


def check_factory(site: Site, vendor: str, lines: list[DiffLine], facts: dict, report: str) -> list[Finding]:
    documented = site.keys.get(vendor, {})
    example = site.example_keys.get(vendor, set())
    out = []
    themes = {t.get(f) for ts in site.themes.values() for t in ts for f in ("id", "client")} - {None}
    fresh: list[str] = []
    for key, (in_new_file, ev) in sorted(factory_keys(lines, facts, report, set(documented) | example,
                                                              example - set(documented), themes).items()):
        status = documented.get(key)
        if status == "documented":
            continue
        if status == "unverified":
            out.append(Finding("factory", "unverified-confirmed", key, f"`{key}` is marked `unverified: true`, but this build's code or file carries it", ev[:2]))
            continue
        if in_new_file:
            fresh.append(key)
            continue
        where = "commented out on the site" if status == "commented out" else "absent from the settings pages"
        where += "; in the example XML" if key in example else ""
        out.append(Finding("factory", "undocumented", key, f"`{key}`: {where}", ev[:3]))
    if fresh:
        out.append(Finding("factory", "undocumented-in-new-file", "",
                           f"{len(fresh)} undocumented key(s) sit in files that are new to this comparison, so they may not be new "
                           f"to the firmware: " + ", ".join(f"`{k}`" for k in fresh[:40]) + (" ..." if len(fresh) > 40 else "")))
    return out


def generated_frontmatter(diff_dir: Path, new_id: str) -> dict:
    meta = WORK / new_id / "meta.json"
    if meta.is_file():
        m = json.loads(meta.read_text())
        return {"id": m["id"], "vendor": m["vendor"], "platform": m["platform"], "android": str(m["android"]),
                "date": datetime.fromtimestamp(m["date"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "signatures": m["signatures"], "source": str(meta)}
    f = diff_dir.parent / "frontmatter.generated.md"
    if f.is_file():
        return frontmatter(f.read_text()) | {"source": str(f)}
    return {}


def check_frontmatter(site: Site, diff_dir: Path, old_id: str, new_id: str) -> list[Finding]:
    gen = generated_frontmatter(diff_dir, new_id)
    page = site.releases.get(slug(new_id))
    if not page:
        return [Finding("frontmatter", "no-page", new_id, f"No page for {new_id} in src/data/updates")]
    if not gen:
        return [Finding("frontmatter", "no-generated", new_id, "No meta.json or frontmatter.generated.md to compare with")]
    out, site_fm = [], page.meta
    where = page.path.as_posix().split("src/data/updates/")[-1]
    for k in ("id", "vendor", "platform", "android"):
        if str(site_fm.get(k, "")) != str(gen.get(k, "")):
            out.append(Finding("frontmatter", k, where, f"`{k}`: site `{site_fm.get(k)}`, firmware `{gen.get(k)}`"))
    try:
        a = datetime.fromisoformat(str(site_fm.get("date", "")).replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(gen.get("date", "")).replace("Z", "+00:00"))
        if abs((a - b).total_seconds()) >= 60:
            out.append(Finding("frontmatter", "date", where, f"`date`: site {site_fm.get('date')}, firmware {gen.get('date')} "
                                                          f"({abs(a - b).total_seconds() / 60:.0f} minutes apart; firmware value is ro.build.date.utc)"))
    except ValueError:
        out.append(Finding("frontmatter", "date", where, f"`date` unreadable: site {site_fm.get('date')!r}, firmware {gen.get('date')!r}"))
    sig_site, sig_gen = site_fm.get("signatures") or {}, gen.get("signatures") or {}
    if not sig_site:
        out.append(Finding("frontmatter", "signatures", where, "`signatures` missing on the site page"))
    else:
        for k in ("md5", "sha1", "sha256"):
            if sig_gen.get(k) and sig_site.get(k) != sig_gen.get(k):
                out.append(Finding("frontmatter", "signatures", where, f"`signatures.{k}`: site {sig_site.get(k)}, firmware {sig_gen.get(k)}"))
    # comparedTo: the site's own choice of base, checked for releases skipped in between.
    compared = site_fm.get("comparedTo") or []
    compared = [compared] if isinstance(compared, str) else compared
    order = release_order(site, page.vendor, page.platform)
    for c in compared:
        cs = slug(c.split("/")[-1])
        if cs in order and slug(new_id) in order:
            between = [s for s in order[order.index(cs) + 1:order.index(slug(new_id))] if line_of(s) == line_of(new_id)]
            if between:
                out.append(Finding("frontmatter", "comparedTo", where, f"`comparedTo` is `{c}`; {len(between)} release(s) of this line lie in between: "
                                   + ", ".join(between[:6]), []))
    return out


# --------------------------------------------------------------------------- main


def run(diff_dir: Path, site_root: Path) -> tuple[str, str, list[Finding]]:
    report = (diff_dir / "REPORT.md").read_text(errors="replace") if (diff_dir / "REPORT.md").is_file() else ""
    facts = json.loads((diff_dir / "facts.json").read_text()) if (diff_dir / "facts.json").is_file() else {}
    m = re.match(r"# (\S+) -> (\S+)", report)
    if not m:
        sys.exit(f"error: {diff_dir}/REPORT.md has no '# <old> -> <new>' title")
    old_id, new_id = m[1], m[2]
    site = load_site(site_root)
    page = site.releases.get(slug(new_id))
    vendor, platform = (page.vendor, page.platform) if page else ("", "")
    if not page:
        # A build without a page yet: borrow the vendor/platform of the build it was compared with.
        base = site.releases.get(slug(old_id))
        vendor, platform = (base.vendor, base.platform) if base else ("", "")
    lines = read_diffs(diff_dir)
    findings = check_themes(site, vendor, platform, old_id, new_id, lines, facts, report) if vendor else []
    findings += check_factory(site, vendor, lines, facts, report) if vendor else []
    findings += check_frontmatter(site, diff_dir, old_id, new_id)
    return old_id, new_id, findings


def markdown(old_id: str, new_id: str, findings: list[Finding]) -> str:
    out = [f"# Site check: {old_id} -> {new_id}", ""]
    titles = {"themes": "Themes", "factory": "Factory settings", "frontmatter": "Frontmatter"}
    for check, title in titles.items():
        rows = [f for f in findings if f.check == check]
        out += [f"## {title}", ""]
        if not rows:
            out += ["- nothing to report", ""]
            continue
        for f in rows:
            out.append(f"- **{f.kind}**: {f.detail}")
            out += [f"  - `{e.replace('`', chr(39))}`" for e in f.evidence]
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("diff_dir", type=Path)
    ap.add_argument("--site", type=Path, default=SITE, help="headunits repo root (default: $HEADUNITS_SITE, else this checkout)")
    ap.add_argument("--json", type=Path, help="also write the findings as JSON here")
    args = ap.parse_args()
    if not (args.site / "src/data/updates").is_dir():
        sys.exit(f"error: {args.site / 'src/data/updates'} is missing; pass --site <headunits checkout> (or set HEADUNITS_SITE)")
    if not args.diff_dir.is_dir():
        sys.exit(f"error: {args.diff_dir} is not a folder")
    old_id, new_id, findings = run(args.diff_dir, args.site)
    print(markdown(old_id, new_id, findings))
    if args.json:
        args.json.write_text(json.dumps({"old": old_id, "new": new_id, "findings": [f.__dict__ for f in findings]},
                                        indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
