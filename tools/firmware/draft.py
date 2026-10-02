#!/usr/bin/env python3
"""Turn an fw.py diff folder into a changelog draft in the site's format, with no model.

  draft.py <diff-dir> [--frontmatter FILE] [--site-data DIR] [-o OUT]

<diff-dir> holds REPORT.md and facts.json from `fw.py diff`. The draft has the
frontmatter, a short summary, the mechanical changes (themes, languages, screen
sizes, factory settings, apps, build properties) in the wording of the existing
update pages, and a "Needs a human" list of findings no template can phrase.
Output is sorted and has no timestamps, so the same input gives the same file.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE_DATA = HERE.parent.parent / "src" / "data"

# The firmware maker's own apps, listed first; other vendor-namespace apps (Zlink, TXZ, the 360 camera) are third-party.
MAKER = ("com.wits.", "com.szchoiceway.", "com.choiceway.", "com.ksw.")
ANDROID = ("com.android.", "android", "com.google.", "com.qualcomm.", "com.qti.", "org.codeaurora.", "com.example.")

LANGUAGES = {  # code: (English name, name in the language itself)
    "ar": ("Arabic", "العربية"), "bg": ("Bulgarian", "Български"), "cs": ("Czech", "Čeština"),
    "da": ("Danish", "Dansk"), "de": ("German", "Deutsch"), "el": ("Greek", "Ελληνικά"),
    "es": ("Spanish", "Español"), "fa": ("Persian", "فارسی"), "fi": ("Finnish", "Suomi"),
    "fr": ("French", "Français"), "he": ("Hebrew", "עברית"), "iw": ("Hebrew", "עברית"),
    "hi": ("Hindi", "हिन्दी"), "hr": ("Croatian", "Hrvatski"), "hu": ("Hungarian", "Magyar"),
    "id": ("Indonesian", "Bahasa Indonesia"), "in": ("Indonesian", "Bahasa Indonesia"),
    "it": ("Italian", "Italiano"), "ja": ("Japanese", "日本語"), "ko": ("Korean", "한국어"),
    "ms": ("Malay", "Bahasa Melayu"), "nl": ("Dutch", "Nederlands"), "nb": ("Norwegian", "Norsk"),
    "pl": ("Polish", "Polski"), "pt": ("Portuguese", "Português"), "ro": ("Romanian", "Română"),
    "ru": ("Russian", "Русский"), "sk": ("Slovak", "Slovenčina"), "sl": ("Slovenian", "Slovenščina"),
    "sr": ("Serbian", "Српски"), "sv": ("Swedish", "Svenska"), "th": ("Thai", "ไทย"),
    "tr": ("Turkish", "Türkçe"), "uk": ("Ukrainian", "Українська"), "vi": ("Vietnamese", "Tiếng Việt"),
    "zh": ("Chinese", "中文"),
}

APP_ROW = re.compile(r"^- \*\*(added|removed|changed)\*\* `([^`]+)` (.*?)(?: \[([^\]]*)\])? \(`([^`]+)`(.*)\)$")
RESOLUTION = re.compile(r"(?<![\w.])(\d{3,4})x(\d{3,4})(?![\w.])")
TICKS = re.compile(r"`([^`]+)`")
BUILD_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}[:_-]\d{2}|\d{6}-\d{2}:\d{2}")  # ZXW versions are build times: 1.0-2024-07-02:16-10


def code(x: str) -> str:
    return f"`{x}`"


def join_and(items: list[str]) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def capped(items: list[str], limit: int) -> str:
    shown = join_and(items[:limit]) if len(items) <= limit else ", ".join(items[:limit])
    return shown + (f" and {len(items) - limit} more" if len(items) > limit else "")


# --------------------------------------------------------------------------- reading


def sections(report: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = ""
    for line in report.splitlines():
        if line.startswith("## "):
            current = re.sub(r" \(.*\)$", "", line[3:].strip())
            out[current] = []
        elif current and line.strip():
            out[current].append(line)
    return out


def highlight(rows: list[str], label: str) -> tuple[str | None, list[str]]:
    """The highlight row starting with `label` and its indented children."""
    for i, row in enumerate(rows):
        if row.startswith(f"- {label}"):
            children = []
            for child in rows[i + 1:]:
                if not child.startswith("  "):
                    break
                children.append(child.strip())
            return row, children
    return None, []


def per_app(children: list[str]) -> dict[str, list[str]]:
    """`- Label:` rows followed by `  - `app`: `a`, `b`` children."""
    out: dict[str, list[str]] = {}
    for child in children:
        if m := re.match(r"^- `([^`]+)`(?: \(\d+\))?(?: added)?: (.*)$", child):
            out.setdefault(m[1], []).extend(TICKS.findall(m[2]))
    return out


def apps(secs: dict[str, list[str]]) -> list[dict]:
    out = []
    for section in ("Vendor apps", "Android apps"):
        for row in secs.get(section, []):
            m = APP_ROW.match(row)
            if not m:
                continue
            action, key, version, kinds, path, rest = m.groups()
            package = key.split(" (")[0]
            app = {"action": action, "package": package, "path": path, "name": Path(path).stem,
                   "kinds": [k.strip() for k in (kinds or "").split(",") if k.strip()], "old": None, "new": None,
                   "replaces": (re.search(r"diffed against removed `([^`]+)`", rest) or [None, None])[1],
                   "moved_from": (re.search(r"moved from `([^`]+)`", rest) or [None, None])[1],
                   "section": section}
            if action == "changed":
                if " -> " in version:
                    app["old"], app["new"] = version.split(" -> ", 1)
                else:
                    app["old"] = app["new"] = version.replace(" (version unchanged)", "")
            elif action == "added":
                app["new"] = version
            else:
                app["old"] = version
            out.append(app)
    # fw.py keys a package by path only while it sits at several paths, so the same package can show up as
    # removed at one path and added at another (a move), or removed and added at the same path (one copy dropped).
    both = {a["package"] for a in out if a["action"] == "added"} & {a["package"] for a in out if a["action"] == "removed"}
    merged = []
    for pkg in sorted(both):
        added = sorted((x for x in out if x["package"] == pkg and x["action"] == "added"), key=lambda x: x["path"])
        gone = sorted((x for x in out if x["package"] == pkg and x["action"] == "removed"), key=lambda x: x["path"])
        stayed = {x["path"] for x in added} & {x["path"] for x in gone}
        for a in added:
            if a["path"] in stayed:
                r = next(x for x in gone if x["path"] == a["path"])
                merged.append(dict(a, action="changed", old=r["old"], kinds=[]))
        new_paths = [x for x in added if x["path"] not in stayed]
        old_paths = [x for x in gone if x["path"] not in stayed]
        for a, r in zip(new_paths, old_paths):
            merged.append(dict(a, action="changed", old=r["old"], moved_from=r["path"], kinds=["moved"]))
        merged += new_paths[len(old_paths):] + [dict(r, copy=True) for r in old_paths[len(new_paths):]]
    return [a for a in out if a["package"] not in both] + merged


def app_group(app: dict) -> str:
    p = app["package"]
    if p.startswith(MAKER):
        return "vendor"
    if app["section"] == "Android apps" and (p == "android" or p.startswith(ANDROID)):
        return "android"
    return "third-party"


def load_frontmatter(diff: Path, explicit: str | None, new_id: str) -> str:
    candidates = [Path(explicit)] if explicit else [diff.parent / "frontmatter.generated.md", diff / "frontmatter.generated.md"]
    for f in candidates:
        if f.is_file():
            return f.read_text().strip() + "\n"
    # fw.py only needs the extracted tree's meta.json for this, which exists until the tree is cleaned up.
    spec = importlib.util.spec_from_file_location("fw", HERE / "fw.py")
    fw = importlib.util.module_from_spec(spec)
    sys.modules["fw"] = fw  # dataclasses look their module up while fw.py loads
    spec.loader.exec_module(fw)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fw.cmd_frontmatter(argparse.Namespace(id=new_id))
    return buf.getvalue().strip() + "\n"


def site_theme_tokens(site: Path, vendor: str | None) -> set[str]:
    """Words that occur in known theme names (bmw, id7, mbux...); a new UI_ constant sharing none is not a theme."""
    tokens = set()
    for d in (site / "themes").glob("*/*") if (site / "themes").is_dir() else []:
        if d.is_dir() and (vendor is None or d.parent.name == vendor):
            tokens |= {t for t in d.name.lower().split("_") if len(t) > 1 and t not in {"ui", "v2", "v3"}}
    return tokens


def site_theme_prefixes(site: Path, vendor: str | None) -> tuple[str, ...]:
    """A first word most of the vendor's known theme names share (KSW_ on ZXW), if there is one."""
    names = [re.sub(r"^\d+-", "", d.name) for d in (site / "themes" / (vendor or "")).glob("*") if d.is_dir()] if vendor else []
    firsts: dict[str, int] = {}
    for n in names:
        firsts[n.split("_")[0] + "_"] = firsts.get(n.split("_")[0] + "_", 0) + 1
    return tuple(sorted(p for p, n in firsts.items() if names and n * 2 > len(names)))


# --------------------------------------------------------------------------- templates


def split_words(name: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", name)]


def label_for(key: str, strings: list[dict]) -> str | None:
    """The new UI string that most likely names a new config key: most shared words, and unambiguous."""
    words = [w for w in split_words(key) if w not in {"visible", "show", "switch", "enable", "selection"}] or split_words(key)
    scored = []
    for s in strings:
        text = s["text"]
        if len(text) > 60 or not text.strip():
            continue
        pool = set(re.split(r"[_\W]+", s["name"].lower())) | set(re.split(r"\W+", text.lower()))
        pool.discard("")
        hits = sum(any(w == p or (len(w) >= 3 and len(p) >= 3 and (p.startswith(w) or w.startswith(p))) for p in pool)
                   for w in words)
        if hits:
            scored.append((hits, s["name"], text))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], x[1]))
    best = scored[0]
    if best[0] < min(2, len(words)):
        return None
    if len(scored) > 1 and scored[1][0] == best[0] and scored[1][2] != best[2]:
        return None
    return best[2]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\\n", " ").replace("\\'", "'").replace('\\"', "'")).strip()


def label_like(s: dict) -> bool:
    """Short UI labels (setting names, options, buttons), not sentences or tips."""
    text = clean_text(s["text"])
    name = s["name"]
    if not text or len(text) > 40 or len(text.split()) > 6 or text.endswith((".", "!", "?", ":", "...", "…")):
        return False
    if re.search(r"%\d*\$?[sd]|\{\d\}|https?://|^\W+$|^\d+$", text) or name in ("app_name",):
        return False
    if re.search(r"(^|_)(tip|tips|toast|msg|message|hint|desc|summary|error|err|warn|content)(_|\d|$)", name):
        return False
    # Chinese-only text, resource references, class names and the Android Studio placeholder are not labels.
    if re.search(r"[\u3000-\u9fff]|@string/|^[\w.]+\.[\w.]+$|^[A-Za-z]+[a-z][A-Z]\w*$", text) or text == "Hello blank fragment":
        return False
    return len(text) >= 3 and bool(re.search(r"[A-Za-z]", text))


def resolutions_in(names: list[str]) -> list[str]:
    found = set()
    for n in names:
        if n.split("-")[0] not in ("layout", "values", "drawable", "mipmap"):
            continue
        for w, h in RESOLUTION.findall(n.replace("-", " ")):
            if 800 <= max(int(w), int(h)) <= 2600 and min(int(w), int(h)) >= 400:
                found.add(f"{w}x{h}")
    return sorted(found, key=lambda r: tuple(int(x) for x in r.split("x")))


def newly_quoted(diff: Path) -> set[str]:
    """String literals that only added lines of the decompiled source diffs contain."""
    added, removed = set(), set()
    for f in (diff / "apps").rglob("*.diff"):
        for line in f.read_text(errors="replace").splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added |= set(re.findall(r'"(\w+)"', line))
            elif line.startswith("-") and not line.startswith("---"):
                removed |= set(re.findall(r'"(\w+)"', line))
    return added - removed


def old_theme_names(diff: Path) -> set[str]:
    """Theme names on the old side (removed or unchanged lines) of any app's UiThemeUtils diff."""
    names: set[str] = set()
    for f in (diff / "apps").rglob("*.diff"):
        in_utils = False
        for line in f.read_text(errors="replace").splitlines():
            if line.startswith("+++ "):
                in_utils = "UiThemeUtils" in line
            elif in_utils and line[:1] in " -" and not line.startswith("---"):
                names |= set(re.findall(r'"(\w+)"', line))
    return names


def draft(diff: Path, frontmatter_file: str | None, site: Path) -> str:
    report = (diff / "REPORT.md").read_text(errors="replace")
    facts = json.loads((diff / "facts.json").read_text())
    title = report.splitlines()[0].lstrip("# ").strip()
    old_id, new_id = title.split(" -> ")
    secs = sections(report)
    hl = secs.get("Highlights", [])
    frontmatter = load_frontmatter(diff, frontmatter_file, new_id)
    vendor = (re.search(r"^vendor: (\w+)", frontmatter, re.M) or [None, None])[1]
    all_apps = apps(secs)
    by_pkg = {a["package"]: a for a in all_apps}
    added_pkgs = {a["package"] for a in all_apps if a["action"] == "added"}
    strings = [dict(s, text=clean_text(s["text"])) for s in facts.get("strings", [])]
    maker_strings = [s for s in strings if s["apps"][0].startswith(MAKER) and s["apps"][0] not in added_pkgs]
    changes: list[str] = []
    summary: list[str] = []
    human: list[str] = []
    used_labels: set[str] = set()
    phrased = set()  # highlight labels a template turned into a bullet

    # Themes. ZXW numbers its themes (UI_NUM_KSW_BENZ_FY3 = 55); KSW names them in UiThemeUtils.
    themes: dict[str, str | None] = {}
    for t in facts.get("themes", []):
        name, _, num = t.partition(" = ")
        themes[re.sub(r"^UI_NUM_", "", name)] = num or None
    theme_rows, theme_children = highlight(hl, "Theme names added (UiThemeUtils)")
    # Newer facts.json files carry the per-app lists in full; older ones only have the REPORT rows.
    per_app_themes = facts.get("theme_strings_by_app") or per_app(theme_children)
    if "theme_strings_before" in facts:
        # Names new to every app combined; an app catching up with a name another app had is not a new theme.
        ui_themes = set(facts.get("theme_strings", []))
    else:
        had_before = old_theme_names(diff)
        ui_themes = (set(facts.get("theme_strings", [])) | {t for v in per_app_themes.values() for t in v}) - had_before
        per_app_themes = {k: [t for t in v if t not in had_before] for k, v in per_app_themes.items()}
    if theme_rows and not theme_children:
        ui_themes |= set(TICKS.findall(theme_rows))
    tokens = site_theme_tokens(site, vendor)
    known_site = {d.name for d in (site / "themes").glob("*/*")} if (site / "themes").is_dir() else set()
    known_names = {re.sub(r"^\d+-", "", n) for n in known_site}

    def theme_like(name: str) -> bool:
        words = {w for w in name.lower().split("_") if w not in {"ui", "ksw", "v2", "v3", "num"}}
        return name in known_names or bool(words & tokens)

    ui_themes = {t for t in ui_themes if theme_like(t) and not re.search(r"(^|_)(DATA|INDEX|SAVE|PKG|KEY)(_|$)", t)}
    # Numbered themes come from a library shared with other brands' firmware (Sailor, Carcool...): keep the
    # ones named like this vendor's known themes (KSW_ on ZXW) and below 100, where the site's ids live.
    prefixes = site_theme_prefixes(site, vendor)
    for t in [t for t, num in themes.items() if num]:
        if t not in known_names and (int(themes[t]) >= 100 or (prefixes and not t.startswith(prefixes))):
            del themes[t]
    for t in facts.get("theme_names", {}).get("added", []):
        if theme_like(t):
            ui_themes.add(t)
    for t in ui_themes:
        themes.setdefault(t, None)
    theme_apps: dict[str, list[str]] = {}
    for pkg, names in per_app_themes.items():
        for n in names:
            theme_apps.setdefault(n, []).append(pkg)
    catch_up = {n: pkgs for n, pkgs in theme_apps.items() if n not in themes and theme_like(n)}
    for t in sorted(themes, key=lambda t: (int(themes[t]) if themes[t] else 1 << 30, t)):
        line = f"- New theme {code(t)}" + (f' with `id="{themes[t]}"`' if themes[t] else "")
        changes.append(line)
    if themes:
        phrased |= {"Theme names added", "Theme ids added"}
        names = sorted(themes, key=lambda t: (int(themes[t]) if themes[t] else 1 << 30, t))
        summary.append(("New theme " if len(names) == 1 else f"{len(names)} new themes: ") + capped([code(n) for n in names], 6))

    # Languages: a new language name in the maker's own settings, or a new values-<lang> folder.
    langs: dict[str, set[str]] = {}
    endonyms = {v[1].lower(): k for k, v in LANGUAGES.items()}
    for s in maker_strings:
        if (k := endonyms.get(s["text"].lower())) and re.search(r"lang", s["name"], re.I):
            langs.setdefault(LANGUAGES[k][0], set())
    row, _ = highlight(hl, "New translation languages")
    if "languages" in facts:
        locales = facts["languages"]
    else:  # the row names only the first app of each language
        locales = {loc: [app_.split(" ")[0]] for loc, app_ in re.findall(r"`([^`]+)` \(([^)]+)\)", row or "")}
    unknown = []
    for loc, pkgs in sorted(locales.items()):
        base = loc.split("-")[0]
        pkgs = [p for p in pkgs if p not in added_pkgs]
        if not pkgs or re.search(r"-\d|-v\d", loc):
            continue
        if base in LANGUAGES:
            langs.setdefault(LANGUAGES[base][0], set()).update(pkgs)
        else:
            unknown.append(f"{code(loc)} ({join_and(sorted(pkgs))})")
    if unknown:
        human.append(f"- New translation folders for languages the templates do not know: {', '.join(unknown)}")
    phrased.add("New translation languages")
    # A system language is one the maker's own apps gain; Zlink alone adding a translation is only a sub-bullet.
    system_langs = sorted(lang for lang, pkgs in langs.items() if not pkgs or any(p.startswith(MAKER) for p in pkgs))
    for lang in system_langs:
        where = sorted(by_pkg[p]["name"] if p in by_pkg else p for p in langs[lang])
        changes.append(f"- {lang} language" + (f", with translations in {join_and(where)}" if where else ""))
    if system_langs:
        summary.append(f"{join_and(system_langs)} language" + ("s" if len(system_langs) > 1 else ""))

    # Screen sizes: a bare WxH that no app carried before; new per-app layout folders become sub-bullets below.
    bare = [s for s in facts.get("screens", {}).get("added", []) if re.fullmatch(r"\d{3,4}x\d{3,4}", s)]
    screens = resolutions_in([f"layout-{s}" for s in bare])
    if set(bare) - set(screens):
        human.append(f"- Sizes that look like images rather than screens: {', '.join(code(x) for x in sorted(set(bare) - set(screens)))}")
    if screens:
        changes.append(f"- Support for {join_and(screens)} screens")
        summary.append(f"Support for {join_and(screens)} screens")
    # Screen variants (1920x720_D1) are the LCD types a vendor's screen config file offers.
    lcd = [s for s in facts.get("screens", {}).get("added", []) if "_" in s]
    if lcd:
        changes.append(f"- New screen type{'s' if len(lcd) > 1 else ''} {capped([code(s) for s in lcd], 12)}")
    if screens or lcd:
        phrased.add("Screen types added")

    # Factory settings: keys the factory XML or the apps reading it gained, named by a new UI string where one fits.
    config_keys = set(facts.get("config_keys", {}).get("added", []))
    added_text = secs.get("Added text files", [])
    # facts.json lists every key; the REPORT row stops after 30.
    factory = facts.get("factory_settings")
    if factory is None:
        factory = []
        for row in hl:
            if m := re.match(r"^- Factory settings added in `([^`]+)`: (.*)$", row):
                factory.append({"file": m[1], "added": [k.strip("<>") for k in TICKS.findall(m[2])], "changed": []})
            elif m := re.match(r"^- Factory default `<([^>`]+)>` in `([^`]+)`: `([^`]*)` -> `([^`]*)`$", row):
                entry = next((f for f in factory if f["file"] == m[2]), None)
                if entry is None:
                    factory.append(entry := {"file": m[2], "added": [], "changed": []})
                entry["changed"].append({"key": m[1], "old": m[3], "new": m[4]})
    xml_name = Path(factory[0]["file"]).name if factory else None
    newly = None
    for f in factory:
        if f["added"] and any(f["file"] in r for r in added_text):
            changes.append(f"- The firmware now includes a default {code(Path(f['file']).name)}")
            # A newly shipped file lists every key; the new ones are those new code starts to look up.
            newly = newly_quoted(diff) if newly is None else newly
            config_keys |= set(f["added"]) & newly
        else:
            config_keys |= set(f["added"])
    phrased |= {"Factory settings added in", "Factory default"}
    link = f"/factory-settings/{vendor}" if vendor else None
    cfg_file = xml_name or ("zxw_factory_config.xml" if vendor == "zxw" else "factory_config.xml")
    for key in sorted(config_keys, key=lambda x: (x.lower(), x)):
        label = label_for(key, maker_strings)
        shown = f"<{key}>" if vendor == "zxw" else key
        if label:
            used_labels.add(label)
            changes.append(f'- New "{label}" ({code(shown)}) factory setting')
        else:
            changes.append(f"- New {code(shown)} setting in [{cfg_file}]({link})" if link else f"- New {code(shown)} factory setting")
    if config_keys:
        labelled = [f'"{label_for(k, maker_strings)}"' for k in sorted(config_keys, key=lambda x: (x.lower(), x)) if label_for(k, maker_strings)]
        summary.append("New factory settings" + (f", including {capped(labelled, 3)}" if labelled else ""))
        phrased.add("Factory config keys added")
    for f in factory:
        for c in f.get("changed", []):
            tag = f"<{c['key']}>"
            changes.append(f"- Default {code(tag)} in {code(Path(f['file']).name)} changed from {code(c['old'])} to {code(c['new'])}")

    # Apps: the maker's own first, then third-party, then stock Android.
    res_row, res_children = highlight(hl, "New resource folders")
    res_by_app = facts.get("resource_dirs") or per_app(res_children)  # the row stops after 15 folders
    strings_by_app: dict[str, list[dict]] = {}
    for s in strings:
        strings_by_app.setdefault(s["apps"][0], []).append(s)
    manifest_row, manifest_children = highlight(hl, "Manifest entries (permissions, activities, services, receivers, actions), per app")
    perms_by_app: dict[str, list[str]] = {}
    if "manifest" in facts:
        for name, entry in facts["manifest"].items():
            perms_by_app[name] = [p for p in entry.get("added", []) if p.startswith("android.permission.")]
    else:
        for child in manifest_children:
            if m := re.match(r"^- `([^`]+)` added: (.*)$", child):
                perms_by_app[m[1]] = [p for p in TICKS.findall(m[2]) if p.startswith("android.permission.")]

    if "strings_changed" in facts:
        changed_strings = [(c["app"], c["old"], c["new"]) for c in facts["strings_changed"]]
    else:
        changed_strings = [(m[1], m[2], m[3]) for row in hl
                           if (m := re.match(r'^  - `([^`]+)` `[^`]+`: "(.*)" -> "(.*)"$', row))]

    def plain(x: str) -> str:
        return re.sub(r"\W", "", x).lower()

    renamed: dict[str, list[tuple[str, str]]] = {}
    for app_, before, after in changed_strings:
        before, after = clean_text(before), clean_text(after)
        # Only short labels: a changed sentence or tip needs a person to say what changed.
        if len(before) <= 40 and len(after) <= 40 and plain(before) != plain(after) \
                and not re.search(r"[\u3000-\u9fff]|@string/|%\d*\$?[sd]", before + after) \
                and not any(re.fullmatch(r"[\da-f.]+", x) for x in (before, after)) \
                and (before, after) not in renamed.get(app_, []):
            renamed.setdefault(app_, []).append((before, after))
    # Two keys swapping texts ("Enable"/"Disable") is a reordered list, not a rename.
    renamed = {k: [(a, b) for a, b in v if (b, a) not in v] for k, v in renamed.items()}

    def sub_bullets(app: dict) -> list[str]:
        subs = []
        p = app["package"]
        for t in sorted(t for t, pkgs in theme_apps.items() if p in pkgs and t in themes):
            subs.append(f"    - Added support for {code(t)} theme")
        for t in sorted(t for t, pkgs in catch_up.items() if p in pkgs):
            subs.append(f"    - Picked up the {code(t)} theme, which other apps already carried")
        for lang in sorted(lang for lang, pkgs in langs.items() if p in pkgs):
            subs.append(f"    - Added {lang} translations")
        if app_group(app) != "android":
            for before, after in renamed.get(p, [])[:10]:
                subs.append(f'    - "{before}" renamed to "{after}"')
        res = resolutions_in(res_by_app.get(p, []))
        if res:
            subs.append(f"    - New layouts for {join_and(res)} screens")
        # A third-party app with hundreds of new strings was rewritten or swapped; its labels say nothing.
        if app["action"] == "changed" and (app_group(app) == "vendor" or
                                           app_group(app) == "third-party" and len(strings_by_app.get(p, [])) <= 80):
            labels = sorted({s["text"] for s in strings_by_app.get(p, []) if label_like(s)} - used_labels, key=lambda x: (x.lower(), x))
            if labels:
                quoted = [f'"{x}"' for x in labels]
                subs.append(f"    - New labels: {capped(quoted, 25)}")
        perms = [x.removeprefix("android.permission.").strip() for x in perms_by_app.get(p, [])]
        if perms and app["action"] == "changed" and app_group(app) != "android":
            human.append(f"- {app['name']} asks for new {join_and([code(x) for x in sorted(perms)])} permission"
                         + ("s" if len(perms) > 1 else ""))
        return subs

    def title_of(app: dict) -> str:
        return f"{app['name']} ({code(Path(app['package']).name if '/' in app['package'] else app['package'])})"

    def folder(path: str) -> str:
        return str(Path(path).parent.parent if Path(path).parent.name == Path(path).stem else Path(path).parent)

    groups = {"vendor": [], "third-party": [], "android": []}
    for a in all_apps:
        groups[app_group(a)].append(a)
    removed = {a["path"]: a for a in all_apps if a["action"] == "removed"}
    replaced_paths = {a["replaces"] for a in all_apps if a["replaces"]}
    updated_names = []
    third_updates, android_updates, rebuilt, unversioned = [], [], [], []
    for group in ("vendor", "third-party", "android"):
        for a in sorted(groups[group], key=lambda a: (a["name"].lower(), a["package"])):
            subs = sub_bullets(a)
            if a["action"] == "added":
                if a["replaces"] and a["replaces"] in removed:
                    old = removed[a["replaces"]]
                    changes.append(f"- {title_of(a)} app `{a['new']}` replaces {title_of(old)}")
                else:
                    changes.append(f"- Added {title_of(a)} app" + (f" {code(a['new'])}" if a["new"] not in (None, "None") else ""))
                changes += subs
            elif a["action"] == "removed":
                if a["path"] in replaced_paths:
                    continue
                if a.get("copy"):
                    changes.append(f"- The extra copy of {title_of(a)} in {code(folder(a['path']))} removed")
                    continue
                changes.append(f"- {title_of(a)} app" + (f" {code(a['old'])}" if a["old"] not in (None, "None") else "") + " removed")
            elif a["moved_from"] and folder(a["moved_from"]) != folder(a["path"]) and a["old"] == a["new"]:
                changes.append(f"- {title_of(a)} app moved from {code(folder(a['moved_from']))} to {code(folder(a['path']))}")
                changes += subs
                if group != "android" and "code" in a["kinds"]:
                    unversioned.append(a["name"])
            elif a["old"] != a["new"]:
                if a["moved_from"] and folder(a["moved_from"]) != folder(a["path"]):
                    subs.insert(0, f"    - Moved from {code(folder(a['moved_from']))} to {code(folder(a['path']))}")
                if group != "vendor" and not subs:
                    (third_updates if group == "third-party" else android_updates).append(
                        f"{title_of(a)} from {code(a['old'])} to {code(a['new'])}")
                    continue
                if BUILD_STAMP.search(a["new"] or "") and not subs:
                    rebuilt.append(a["name"])
                    continue
                if BUILD_STAMP.search(a["new"] or ""):
                    changes.append(f"- {title_of(a)} app updated")
                else:
                    changes.append(f"- {title_of(a)} app updated from {code(a['old'])} to {code(a['new'])}")
                changes += subs
                updated_names.append(a["name"])
            elif subs:
                changes.append(f"- {title_of(a)} app updated, version still {code(a['new'])}")
                changes += subs
            elif group != "android" and "code" in a["kinds"]:
                unversioned.append(a["name"])
    if rebuilt:
        changes.append(f"- Also updated: {join_and(rebuilt)}")
    if third_updates:
        changes.append("- Third-party apps updated: " + "; ".join(third_updates))
    if android_updates:
        changes.append("- Android apps updated: " + "; ".join(android_updates))
    if unversioned:
        human.append(f"- Code changed with the version number unchanged: {join_and(unversioned)}")
    added_names = sorted({a["name"] for a in all_apps if a["action"] == "added" and app_group(a) != "android"})
    if added_names:
        summary.append(f"New {capped(sorted(added_names, key=lambda x: (x.lower(), x)), 5)} app" + ("s" if len(added_names) > 1 else ""))
    if updated_names:
        summary.append(f"{capped(list(dict.fromkeys(updated_names)), 5)} updated")

    # Build properties that say who built it and how: user, type, keys, host, product names.
    props: dict[tuple[str, str, str], list[str]] = {}
    for row in secs.get("Build properties", []):
        if m := re.match(r"^- `([^`]+)` `([^`]+)`: `([^`]*)` -> `([^`]*)`", row):
            key = m[2]
            if key in ("ro.boot.oem.pkg",) or re.search(r"\d{8}\.\d{6}", m[3] + m[4]):
                continue
            general = re.sub(r"^ro\.product\.(system_ext|system_dlkm|system|product|vendor|odm|vendor_dlkm|odm_dlkm)\.", "ro.product.*.", key)
            props.setdefault((general, m[3], m[4]), []).append(key)
    for row in hl:
        if m := re.match(r"^- Build `([^`]+)`: `([^`]*)` -> `([^`]*)`", row):
            if m[1] not in ("ro.build.display.id",):
                props.setdefault((m[1], m[2], m[3]), []).append(m[1])
    for (key, a, b) in sorted(props):
        a, b = a or "(empty)", b or "(empty)"
        if a == "(none)":
            changes.append(f"- New {code(key)} property, set to {code(b)}")
        elif b == "(none)":
            changes.append(f"- {code(key)} property removed (was {code(a)})")
        else:
            changes.append(f"- {code(key)} changed from {code(a)} to {code(b)}")

    # Android's own defaults (framework-res config values): short values only, lists are for a person to read.
    done_rows = set()
    for row in hl:
        if m := re.match(r"^- Android `(\w+)` \(`([^`]+)`\): `([^`]{1,40})` -> `([^`]{1,40})`$", row):
            changes.append(f"- Android default {code(m[1])} changed from {code(m[3])} to {code(m[4])}")
            done_rows.add(row)

    # Properties the apps start to read or set: switches like persist.flash.size.giga or vendor.wits.hicarWired.connected.
    # New ro.* names come from phone-detection libraries (ro.build.MiFavor_version) far more often than from the unit.
    new_props = [x for x in facts.get("props", {}).get("added", []) if re.match(r"(persist|vendor|sys)\.", x)]
    if new_props:
        changes.append(f"- New system propert{'ies' if len(new_props) > 1 else 'y'} used by the apps: "
                       f"{capped([code(x) for x in sorted(new_props)], 20)}")
        phrased.add("System properties added")

    # Everything else the report found, for a person to read and phrase.
    skip = phrased | {"Build ", "New UI strings", "New layouts", "New resource folders",
                      "Manifest entries (permissions, activities, services, receivers, actions), per app"}
    def shorten(text: str) -> str:
        return text if len(text) <= 400 else text[:400].rsplit(",", 1)[0] + ", ..."

    for i, row in enumerate(hl):
        if row.startswith("  ") or row in done_rows or any(row.startswith(f"- {s}") for s in skip):
            continue
        human.append(f"- {shorten(row[2:])}")
        if row.endswith(":"):
            children = []
            for child in hl[i + 1:]:
                if not child.startswith("  "):
                    break
                children.append(f"    {shorten(child.strip())}")
            human += children[:40] + ([f"    - ... {len(children) - 40} more in REPORT.md"] if len(children) > 40 else [])
    decompiled = {m[1]: m[2] for r in secs.get("Decompiled source diffs", []) if (m := re.match(r"^- `([^`]+)`: (.*)$", r))}
    for key, stat in sorted(decompiled.items()):
        name = key.split(" (")[0]
        if "code:" in stat and (name.endswith(".jar") or name.startswith(MAKER) or name in by_pkg and app_group(by_pkg[name]) != "android"):
            lines = re.search(r"code: (\d+) files, (\d+) lines", stat)
            where = f" at `{key.split(' (', 1)[1].rstrip(')')}`" if " (" in key else ""
            diff_name = re.sub(r"[^\w.-]", "_", key)  # fw.py's slugify
            human.append(f"- {code(name)}{where} code changed ({lines[1]} files, {lines[2]} lines): read "
                         f"`apps/{diff_name}.code.diff`"
                         if lines else f"- {code(name)} code changed")

    # A package installed at several paths shows up once per path: drop repeated bullets with their sub-bullets.
    seen, kept, keep = set(), [], True
    for c in changes:
        if not c.startswith("  "):
            keep = c not in seen
            seen.add(c)
        if keep:
            kept.append(c)
    changes = kept
    out = [frontmatter.rstrip(), "#### Summary", *(f"- {s}" for s in summary or ["Needs a human: nothing mechanical to summarise"]), "",
           "#### Changes", *(changes or ["- No changes found by the templates"]), ""]
    out += ["#### Needs a human", "", *(human or ["- nothing"]), ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("diff", help="folder with REPORT.md and facts.json")
    ap.add_argument("--frontmatter", help="defaults to frontmatter.generated.md next to the diff folder, else fw.py frontmatter")
    ap.add_argument("--site-data", default=str(SITE_DATA), help="src/data of the site, for known theme names")
    ap.add_argument("-o", "--output", help="write here instead of stdout")
    args = ap.parse_args()
    text = draft(Path(args.diff), args.frontmatter, Path(args.site_data))
    if args.output:
        Path(args.output).write_text(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
