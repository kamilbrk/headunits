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
# The block of a factory file that holds user-settings defaults (the vendor's spelling).
USER_BLOCK = "setings"
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
    example_leaves: dict[str, set[str]]  # tags that hold a value, not a list
    user_keys: dict[str, set[str]]  # leaves of the example's <setings> block: the reader's own settings, not factory ones


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
    example, leaves, user = {}, {}, {}
    for vendor, name in EXAMPLE_XML.items():
        f = root / "public" / name
        if f.is_file():
            text = f.read_text(errors="replace")
            example[vendor] = set(re.findall(r"<(\w+)[\s>/]", text))
            leaves[vendor] = set(re.findall(r"<(\w+)>[^<]*</\1>", text))
            user[vendor] = {k for block in re.findall(rf"<{USER_BLOCK}>(.*?)</{USER_BLOCK}>", text, re.S)
                            for k in re.findall(r"<(\w+)>[^<]*</\1>", block)}
    return Site(releases, themes, keys, example, leaves, user)


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
# Words in theme ids that say nothing about which theme it is: makers, the vendor and version tags.
THEME_WORDS = {"ui", "ksw", "num", "v1", "v2", "v3", "bmw", "benz", "audi", "lexus", "landrover", "ford", "toyota"}
# A home screen of its own ships more images than this; fewer is an id or a stub.
STUB_IMAGES = 10
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
        # fw.py compared every app's whole theme class, old against new, so no vote is needed. A theme
        # exists once the launcher dispatches on it; Bluetooth or media apps gaining the name first is not it.
        by_app = facts.get("theme_strings_by_app") or {}
        launchers = launcher_apps(facts, lines) if "theme_strings_by_app" in facts else set()
        new_names = sorted({n for app in launchers for n in by_app.get(app, [])}) if launchers else facts.get("theme_strings", [])
        named = {n: list(dict.fromkeys([ev for app in sorted(launchers) for ev in per_app.get(app, {}).get(n, [])]
                                       + [ev for names in per_app.values() for ev in names.get(n, [])]))[:2]
                 + ["facts.json theme_strings" + (f" ({', '.join(sorted(launchers))})" if launchers else "")]
                 for n in new_names if usable(n)}
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


def launcher_apps(facts: dict, lines: list[DiffLine]) -> set[str]:
    """Apps that are the home screen: named so by their package or APK, or keeping their theme class under a
    launcher package. Empty when the build gives no sign of which one it is."""
    named = {a["key"] for a in facts.get("apps") or [] if "launcher" in f"{a.get('key', '')} {a.get('name', '')}".lower()}
    return named | {app_of(ln.file) for ln in lines if THEME_FILE.search(ln.inner) and "/launcher/" in ln.inner}


def theme_footprint(name: str, lines: list[DiffLine]) -> tuple[int, int, int]:
    """(layouts, images, uses) this diff adds for a theme: layouts and images whose names carry the theme's
    own words (`BMW_ID8_UI` -> `id8`), and lines outside the theme classes that name it or its constant.
    A theme with a home screen ships its own artwork; an id or a stub screen ships next to none."""
    words = {w for w in name.lower().split("_") if w not in THEME_WORDS} or set(name.lower().split("_"))
    fields = {m[1] for ln in lines for m in re.finditer(rf'static final String (\w+) = "{re.escape(name)}";', ln.text)}
    fields |= {re.match(r"\w+", m[0])[0] for ln in lines for m in NUM_THEME.finditer(ln.text) if num_theme(m)[0] == name}
    named = re.compile(r"\b(?:is)?(?:" + "|".join(map(re.escape, sorted(fields | {name}))) + r")\b")
    declared = re.compile(r"static final \w+ (?:" + "|".join(map(re.escape, sorted(fields))) + r") =") if fields else re.compile(r"(?!)")

    def ours(res: str) -> bool:
        return words <= set(res.lower().split("_"))
    layouts, images, uses = set(), set(), 0
    for ln in lines:
        if ln.sign != "+":
            continue
        if ".resources" in ln.file:
            if (layout := re.search(r"res/layout[\w-]*/(\w+)\.xml$", ln.inner)) and ours(layout[1]):
                layouts.add(layout[1])
            images.update(r for r in re.findall(r"@(?:drawable|mipmap)/(\w+)", ln.text) if ours(r))
        elif not THEME_FILE.search(ln.inner):
            images.update(r for r in re.findall(r"\bR\.(?:drawable|mipmap)\.(\w+)", ln.text) if ours(r))
            uses += bool(named.search(ln.text)) and not declared.search(ln.text)
    return len(layouts), len(images), uses


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


def same_branch(a: str, b: str) -> bool:
    """Whether two builds of one line are on the same branch: `v1.7.2NEXAI` branches off the plain `v2.0.3` line."""
    def branch(fw_id: str) -> str:
        m = re.search(r"v[\d.]+([a-z]*)-ota$", slug(fw_id))
        return m[1] if m else ""
    return branch(a) == branch(b)


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
    # The pair may skip site releases; then the theme first appears in one of them or in this build.
    skipped_releases = [r for r in order[order.index(old_slug) + 1:order.index(new_slug)]
                        if line_of(r) == line_of(new_id) and same_branch(r, new_id)] \
        if old_slug in order and new_slug in order else []
    adds = f"it first appears after `{old_id}`, in `{here}` or one of the {len(skipped_releases)} site release(s) " \
           f"this comparison skips: {', '.join(f'`{r}`' for r in skipped_releases[:6])}" if skipped_releases else f"this build adds it: `{here}`"
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
        layouts, images, uses = theme_footprint(name, lines)
        id_only = " (id only in this build: nothing uses it yet)" if not (layouts or images or uses) else ""
        if not theme["since"]:
            out.append(Finding("themes", "since-blank", name, f"{label}: `since` is blank; {adds}{id_only}", ev[:2]))
        elif not same_line:
            out.append(Finding("themes", "since-missing-line", name,
                               f"{label}: `since` names no {line_of(new_id).replace('#', '*')} release; {adds}{id_only}", ev[:2]))
        else:
            for s in same_line:
                ss = slug(s.split("/")[-1])
                if ss == new_slug or ss not in order or new_slug not in order:
                    continue
                i_s, i_new = order.index(ss), order.index(new_slug)
                i_old = order.index(old_slug) if old_slug in order else i_new - 1
                if i_s > i_new and images < STUB_IMAGES and layouts < STUB_IMAGES:
                    # An id, or a screen without artwork of its own: the site dates the theme from when it works.
                    out.append(Finding("themes", "note", name, f"{label}: site says `{s}`; `{here}` already has "
                                       f"{'only its id' if id_only else f'a stub ({layouts} layouts, {images} images)'}, so that stands"))
                elif i_s > i_new:
                    out.append(Finding("themes", "since-too-late", name,
                                       f"{label}: site says `{s}`, but it is already added in `{here}`", ev[:2]))
                elif i_s <= i_old:
                    out.append(Finding("themes", "since-too-early", name,
                                       f"{label}: site says `{s}`, but the code first adds it in `{here}` (compared with {old_id})", ev[:2]))
    if skipped:
        out.append(Finding("themes", "note", "", f"{skipped} numbered theme id(s) outside the site's numbering ({bottom} to {top}) were skipped"))
    return out


# Tag names the factory parser compares, and the plain fields of the class it fills.
COMPARED = re.compile(r'case "([A-Za-z]\w*)":|\.equals(?:IgnoreCase)?\("([A-Za-z]\w*)"\)')
FIELD = re.compile(r'^\s*public (?:int|long|boolean|String) ([A-Za-z]\w*)(?: = [^;]+)?;')
CONSTANT = re.compile(r'static final String \w+ = "([A-Za-z]\w*)";')
# A method of a top-level class, as jadx indents it.
METHOD = re.compile(r'^ {4}[\w<>\[\],. ]*?\b(\w+)\([^;]*\)\s*(?:throws [\w., ]+)?\{\s*$')


def scoped_names(lines: list[DiffLine]) -> dict[tuple[str, str, str], list[tuple[str, DiffLine]]]:
    """Compared tag names per method, and plain fields per class: {(diff file, source file, scope): [(name, line)]}.
    A line's method is the last declaration the diff shows above it in the same file."""
    out: dict[tuple[str, str, str], list[tuple[str, DiffLine]]] = {}
    where, method, closed, prev = ("", ""), "", False, 0
    for ln in lines:
        if (ln.file, ln.inner) != where:
            where, method, closed = (ln.file, ln.inner), "", False
        elif ln.no != prev + 1 and closed:
            # A new hunk after the method ended in view: whatever method it is in, it is not that one.
            method, closed = "", False
        prev = ln.no
        if m := METHOD.match(ln.text):
            method, closed = m[1], False
        elif re.fullmatch(r" {4}\}\s*", ln.text):
            closed = True
        for m in COMPARED.finditer(ln.text):
            out.setdefault((ln.file, ln.inner, method), []).append((m[1] or m[2], ln))
        if m := FIELD.match(ln.text):
            out.setdefault((ln.file, ln.inner, "<fields>"), []).append((m[1], ln))
    return out


def factory_keys(lines: list[DiffLine], facts: dict, report: str, known: set[str], factory_tags: set[str],
                 user_keys: set[str], site_keys: set[str], not_keys: set[str]) -> dict[str, tuple[bool, list[str]]]:
    """Factory-config keys this build reads or ships: {key: (only in a file new to this diff, evidence)}.
    A key counts when the factory parser reads it, when it is a factory-section tag of a factory XML, or when
    the code names a tag the example XML has in its factory section."""
    keys: dict[str, tuple[bool, list[str]]] = {}

    def add(k: str, fresh_file: bool, ev: str) -> None:
        if k in not_keys or re.fullmatch(r"[A-Z0-9_]+", k):
            return
        old_fresh, evs = keys.get(k, (True, []))
        keys[k] = (old_fresh and fresh_file, evs if ev in evs else evs + [ev])

    # Files that are wholly new in this diff: every key in them looks added, whether or not it is.
    has_old = {ln.inner for ln in lines if ln.sign != "+"}
    added_text = set(re.findall(r"^- `([^`]+)`$", report.split("## Added text files", 1)[1].split("\n## ", 1)[0], re.M)) \
        if "## Added text files" in report else set()
    # fw.py's config keys are new strings compared anywhere in an app that names the factory file, which
    # also catches preference names and intent extras; they count only with one of the signals below.
    claimed: list[tuple[str, str]] = [(k, "facts.json config_keys") for k in facts_list(facts, "config_keys")]
    # facts.json has the full lists; REPORT.md stops at 30 names with "+N more".
    for entry in facts.get("factory_settings") or []:
        for k in entry.get("added", []):
            if k not in user_keys:
                add(k, bool(entry.get("file_added")), f"facts.json factory_settings: {entry.get('file')}")
    rows = r"^- Factory config keys added.*$" if "factory_settings" in facts else r"^- Factory (?:config keys|settings) added.*$"
    for row in re.findall(rows, report, re.M):
        rel = re.search(r"added in `([^`]+)`", row)
        for k in re.findall(r"`<?(\w+)>?`", row.split(":", 1)[1]):
            if not rel:
                claimed.append((k, "REPORT.md: " + row[:120]))
            elif k not in user_keys:
                add(k, rel[1] in added_text, "REPORT.md: " + row[:120])
    xml_old = {m[1] for ln in lines if ln.sign != "+" and "factory" in ln.inner.lower() for m in [re.match(r"\s*<(\w+)>", ln.text)] if m}
    where, in_user, prev = "", None, 0
    for ln in lines:
        if not ("factory" in ln.inner.lower() and ln.inner.endswith(".xml")):
            continue
        if ln.inner != where or ln.no != prev + 1:
            where, in_user = ln.inner, None
        prev = ln.no
        if block := re.match(r"\s*<(/?)(\w+)>\s*$", ln.text):
            if block[2] == USER_BLOCK:
                in_user = not block[1]
        elif ln.sign == "+" and (m := re.match(r"\s*<(\w+)>[^<]*</\1>", ln.text)) and m[1] not in xml_old:
            # The diff may not show which block a tag sits in; the example's own layout decides then.
            if not (in_user or (in_user is None and m[1] in user_keys)):
                add(m[1], ln.inner not in has_old, cite(ln))
    # Code naming, for the first time, a tag the example has in its factory section or a key the site
    # already lists: the question for those is only whether this build carries them.
    literals = [(m[1], ln) for ln in lines for m in CONSTANT.finditer(ln.text)] + \
               [(m[1] or m[2], ln) for ln in lines for m in COMPARED.finditer(ln.text)]
    old_literals = {v for v, ln in literals if ln.sign != "+"}
    for v, ln in literals:
        if ln.sign == "+" and (v in factory_tags or v in site_keys) and v not in old_literals:
            add(v, ln.inner not in has_old, cite(ln))
    # The parser itself: a method that compares tag names, or a class whose plain fields are the keys, once
    # several of its names are keys the site or the example already knows. No class or vendor name is needed,
    # and a constant declared beside such code is not a read.
    for (_, inner, _), found in scoped_names(lines).items():
        if len({v for v, _ in found if v in known}) < 3:
            continue
        gone = {v for v, ln in found if ln.sign != "+"}
        for v, ln in found:
            if ln.sign == "+" and v not in gone:
                add(v, inner not in has_old, cite(ln))
    for k, ev in claimed:
        if k in keys or k in site_keys or k in factory_tags:
            _, evs = keys.get(k, (False, []))
            keys[k] = (False, evs if ev in evs else evs + [ev])
    return keys


def check_factory(site: Site, vendor: str, lines: list[DiffLine], facts: dict, report: str) -> list[Finding]:
    documented = site.keys.get(vendor, {})
    example = site.example_keys.get(vendor, set())
    out = []
    themes = {t.get(f) for ts in site.themes.values() for t in ts for f in ("id", "client")} - {None}
    fresh: list[str] = []
    user = site.user_keys.get(vendor, set())
    leaves = site.example_leaves.get(vendor, set())
    for key, (in_new_file, ev) in sorted(factory_keys(lines, facts, report, set(documented) | leaves, leaves - user - set(documented),
                                                      user, set(documented), themes).items()):
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
            between = [s for s in order[order.index(cs) + 1:order.index(slug(new_id))]
                       if line_of(s) == line_of(new_id) and same_branch(s, new_id)]
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
        rows = [f for f in findings if f.check == check and f.kind != "note"]
        out += [f"## {title}", ""]
        if not rows:
            out.append("- nothing to report")
        for f in rows:
            out.append(f"- **{f.kind}**: {f.detail}")
            out += [f"  - `{e.replace('`', chr(39))}`" for e in f.evidence]
        notes = [f.detail for f in findings if f.check == check and f.kind == "note"]
        out += ["", *(f"Note: {n}" for n in notes)] if notes else []
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
        args.json.write_text(json.dumps({"old": old_id, "new": new_id, "findings": [f.__dict__ for f in findings if f.kind != "note"],
                                         "notes": [f.__dict__ for f in findings if f.kind == "note"]},
                                        indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
