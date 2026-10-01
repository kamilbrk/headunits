#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Flag security- and privacy-relevant changes in a `fw.py diff` folder, with no model in the loop.

  rules.py <diff-dir>                       print Markdown findings
  rules.py <diff-dir> --json out.json       also write them as JSON
  rules.py <diff-dir> --min-severity medium hide low and info findings

<diff-dir> is WORK/diffs/<old>..<new>/ (or any folder holding REPORT.md, facts.json, files/text.diff
and apps/*.diff). Every rule is a pattern over Android/Linux concepts; identifiers seen in one
vendor's code live in the data tables below, not in the rules.
When WORK/<id>/manifest.tsv exists for both builds, removed and added executables with the same
hash are reported as renames.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

WORK = Path(os.environ.get("FW_WORK", Path.home() / "Dev/firmwares/_work"))
SEVERITIES = ["high", "medium", "low", "info"]
MAX_SHOWN = 8

# Vendor names are data only: they label apps in the output and never decide whether a rule fires.
VENDOR_LABELS = {
    "com.wits": "KSW/Witstek",
    "com.szchoiceway": "ZXW/Choiceway",
    "com.txznet": "TXZ",
    "com.zjinnova": "Zlink",
    "com.ivicar": "iVicar",
}

# Identifiers one vendor's code uses to fake version, RAM or storage figures. Data: add a vendor's
# own names here rather than to the patterns in rule_fake.
VENDOR_FAKE_MARKERS = {
    "com.wits (KSW)": [r"memoryvalue", r"getChangeRAM", r"getChange\w*(?-i:Version|version|verison|RAM|Ram|ROM|Rom)\(",
                       r'"\w*android_?1\d\w*"', r"android1\d_update_date"],
}

# Benchmark and system-info apps: firmware that names them in framework or Settings code is
# usually changing what they display.
BENCHMARK_PACKAGES = re.compile(r"com\.antutu|com\.finalwire\.aida64|com\.primatelabs\.geekbench|com\.cpuid\.cpu_z|"
                                r"com\.ludashi|com\.futuremark|com\.glbenchmark|com\.andromeda\.androbench|"
                                r"ru\.andr7e\.deviceinfohw|com\.inkwired\.droidinfo|com\.sysinfo|"
                                r"flar2\.devcheck|com\.kiwi\.cpuinfo|com\.cpuinfo|com\.ioncannon\.cpuburn|"
                                r"BenchmarkNewService|ABenchMark", re.I)
# Analytics, crash-report and ad SDK endpoints.
TRACKER_HOSTS = re.compile(r"umeng|bugly|app-measurement|google-analytics|crashlytics|firebaselogging|appsflyer|"
                           r"adjust\.com|mobstat|mtj\.baidu|hmma\.baidu|talkingdata|sensorsdata|getui|jpush|"
                           r"growingio|tingyun|mixpanel|amplitude|flurry|applovin|doubleclick|admob|exceptionlog|"
                           r"mobilelog|nbcollect|rt-m\.|collect", re.I)
# Hosts that show up as documentation, XML namespaces or licence links, not as traffic.
INERT_HOSTS = re.compile(r"(^|\.)(schemas\.android\.com|w3\.org|xml\.org|apache\.org|schema\.org|github\.com|"
                         r"xmlpull\.org|ns\.adobe\.com|purl\.org|example\.(com|org)|localhost|127\.0\.0\.1|"
                         r"xml\.apache\.org|json-schema\.org|id3\.org|musicbrainz\.org|tukaani\.org|"
                         r"developer\.android\.com|support\.google\.com|goo\.gl|javax\.xml\.XMLConstants|"
                         r"www\.apple\.com|java\.sun\.com|opensource\.org|creativecommons\.org|"
                         r"google\.com|www\.google\.com|www\.baidu\.com|metadata\.google\.internal|metadata|"
                         r"mozilla\.org|publicsuffix\.org|eclipse\.org|junit\.org|gnu\.org|llvm\.org|unicode\.org|"
                         r"wikipedia\.org|jetbrains\.(com|org)|sonatype\.org|opensource\.apple\.com|unlicense\.org|"
                         r"sgi\.com|source\.android\.com|cmu\.edu|codingstandard\.com|sil\.org|aegisub\.org|"
                         r"googlecode\.com|ncac\.gov\.cn|miit\.gov\.cn|beian\.gov\.cn|android\.com|"
                         r"whatwg\.org|ietf\.org|rfc-editor\.org|chromium\.org|webkit\.org|khronos\.org|"
                         r"\d+\.\d+\.\d+\.\d+)$", re.I)


@dataclass
class Line:
    file: str   # diff file, relative to the diff folder
    inner: str  # path inside that diff (the source or config file)
    no: int     # 1-based line number in the diff file
    sign: str   # "+" or "-"
    text: str
    app: str
    hunk: int = 0  # which @@ hunk of its diff file the line sits in

    def cite(self) -> str:
        where = self.file if self.inner in ("", self.file) else f"{self.file} ({self.inner})"
        return f"{where}:{self.no}: {self.sign}{self.text.strip()[:220]}"


@dataclass
class Hit:
    rule: str
    severity: str
    title: str
    lines: list[str] = field(default_factory=list)
    app: str = ""
    detail: str = ""


@dataclass
class Diff:
    root: Path
    report: str
    facts: dict
    lines: list[Line]
    by_app: dict[str, list[Line]]
    old_id: str
    new_id: str
    context_urls: set[str] = field(default_factory=set)  # URLs on unchanged (context) lines


# --------------------------------------------------------------------------- loading


def app_of(rel: str) -> str:
    """apps/com.foo.code.diff -> com.foo; apps/com.foo/<file>.diff -> com.foo; files/text.diff -> (files)."""
    parts = rel.split("/")
    if parts[0] != "apps":
        return "(files)"
    if len(parts) > 2:
        return parts[1]
    return re.sub(r"\.(code|resources|manifest|assets|other)(\.large)?\.diff$", "", parts[1])


def read_diff(path: Path, rel: str) -> list[Line]:
    out, inner, app, hunk = [], "", app_of(rel), 0
    with path.open(errors="replace") as fh:
        for no, raw in enumerate(fh, 1):
            if raw.startswith("diff --git "):
                inner = ""
                continue
            if raw.startswith("@@"):
                hunk += 1
                continue
            if raw.startswith("+++ "):
                inner = "" if raw.startswith("+++ /dev/null") else raw[6:].rstrip("\n\t")
                continue
            if raw.startswith("--- "):
                if not inner and not raw.startswith("--- /dev/null"):
                    inner = raw[6:].rstrip("\n\t")
                continue
            if raw[:1] in "+-" and len(raw) > 1:
                out.append(Line(rel, inner, no, raw[0], raw[1:].rstrip("\n"), app, hunk))
    return out


def load(root: Path) -> Diff:
    report = (root / "REPORT.md").read_text(errors="replace") if (root / "REPORT.md").is_file() else ""
    facts = json.loads((root / "facts.json").read_text()) if (root / "facts.json").is_file() else {}
    lines: list[Line] = []
    for path in sorted(root.rglob("*.diff")):
        lines += read_diff(path, path.relative_to(root).as_posix())
    context: set[str] = set()
    for path in root.rglob("*.diff"):
        with path.open(errors="replace") as fh:
            for raw in fh:
                if raw.startswith(" ") and "://" in raw:
                    context.update(URL.findall(raw))
    by_app: dict[str, list[Line]] = {}
    for ln in lines:
        by_app.setdefault(ln.app, []).append(ln)
    m = re.match(r"# (\S+) -> (\S+)", report)
    old_id, new_id = (m[1], m[2]) if m else (root.name.split("..") + ["", ""])[:2]
    return Diff(root, report, facts, lines, by_app, old_id, new_id, context)


def facts_list(facts: dict, key: str, part: str = "added") -> list:
    """facts[key][part], or facts[key] itself when an older facts.json stored a flat list of additions."""
    v = facts.get(key)
    if isinstance(v, dict):
        return list(v.get(part) or [])
    return list(v or []) if part == "added" else []


def report_section(report: str, title: str) -> list[str]:
    m = re.search(rf"^## {re.escape(title)}.*?\n(.*?)(?=^## |\Z)", report, re.M | re.S)
    return [ln for ln in (m[1].splitlines() if m else []) if ln.startswith("-")]


def report_lines(report: str, pattern: str) -> list[str]:
    return [ln.strip() for ln in report.splitlines() if re.search(pattern, ln)]


def added(d: Diff, pattern: re.Pattern, where: re.Pattern | None = None, sign: str = "+") -> list[Line]:
    # Kotlin @Metadata annotations carry every identifier of a class as one escaped string.
    return [ln for ln in d.lines if ln.sign == sign and (where is None or where.search(ln.file + " " + ln.inner))
            and pattern.search(ln.text) and not ln.text.lstrip().startswith("@Metadata")]


def net_added(d: Diff, pattern: re.Pattern, where: re.Pattern | None = None) -> list[Line]:
    """'+' lines whose stripped text has no identical '-' line in the same app: moved code is not new."""
    plus = added(d, pattern, where)
    minus = {(ln.app, ln.text.strip()) for ln in added(d, pattern, where, "-")}
    return [ln for ln in plus if (ln.app, ln.text.strip()) not in minus]


def hit(rule: str, severity: str, title: str, lines: list[Line] | list[str], app: str = "", detail: str = "") -> Hit:
    cited = [x.cite() if isinstance(x, Line) else x for x in lines]
    return Hit(rule, severity, title, cited, app, detail)


def per_app(rule: str, severity: str, title: str, lines: list[Line]) -> list[Hit]:
    return [hit(rule, severity, title, g, app) for app, g in group(lines).items()]


# --------------------------------------------------------------------------- rules
# Each rule takes the loaded diff and returns hits. Severity: high = weakens a protection or sends
# personal data; medium = worth a line in the changelog; low = context; info = counted, not argued.

INIT_TEXT = re.compile(r"\.rc\b|ueventd|\.sh\b|/bin/[^/ ]+$")
CODE = re.compile(r"\.java\b|\.kt\b|\.smali\b")
CHMOD = re.compile(r"\bchmod\s+(-R\s+)?0?([0-7]?[0-7][0-7]([2367]))\b(\s+-R)?\s*(?P<target>\S*)")
# Symbolic modes that give 'other' (o or a) write access: chmod o+w, chmod -R a+rw.
CHMOD_SYM = re.compile(r"\bchmod\s+(-R\s+)?([ugo]*,)*[ugo]*[oa][ugoa]*[+=][rwxXst]*w[rwxXst]*(\s+-R)?\s+(?P<target>\S*)")
# Java/Kotlin calls: jadx prints the mode in decimal (511 = 0777, 438 = 0666), source may use octal.
CODE_CHMOD = re.compile(r"\b(?:Os\.chmod|Libcore\.os\.chmod|FileUtils\.setPermissions|\w*\.chmod)\(\s*(?P<target>(?:[^,()]|\([^()]*\))+?)\s*,\s*"
                        r"(?P<mode>0[0-7]{3,4}|[1-9]\d{2,3})\b")
WORLD_ACCESS = re.compile(r"\bset(?P<what>Writable|Readable)\(\s*true\s*,\s*false\s*\)")
UEVENTD_MODE = re.compile(r"^\s*(/dev/\S+|/sys/\S+)\s+0?[0-7]?[0-7][0-7][2367]\s+\w+")
MKDIR_MODE = re.compile(r"^\s*mkdir\s+(\S+)\s+0?[0-7]?[0-7][0-7][2367]\b")


def ww_severity(target: str) -> str:
    if re.match(r'/dev/(block|smd|diag|mem|kmem|at|ttyHS|mtd|mmcblk|sd[a-z])|/dev/block', target) or \
            re.search(r"imei|/by-name/", target, re.I):
        return "high"
    if re.search(r"privdata|persist", target):
        return "medium"
    if target.startswith(("/dev/", "/sys/", "/proc/")) or target.startswith("/system/bin"):
        return "medium"
    return "low"


def clean_target(raw: str) -> str:
    t = raw.strip('"\');&)')
    return t.removesuffix("\\n").strip('"\');&)')


def code_mode_world_writable(mode: str) -> bool:
    n = int(mode, 8) if mode.startswith("0") else int(mode)
    return n <= 0o7777 and bool(n & 0o002)


def rule_world_writable(d: Diff) -> list[Hit]:
    groups: dict[tuple[str, str, str], list[Line]] = {}
    for ln in d.lines:
        if ln.sign != "+" or ln.text.lstrip().startswith(("#", "//", "*")):
            continue
        rule, target = "world-writable", ""
        if m := CHMOD.search(ln.text) or CHMOD_SYM.search(ln.text):
            target = clean_target(m["target"])
        elif CODE.search(ln.inner) and (m := CODE_CHMOD.search(ln.text)) and code_mode_world_writable(m["mode"]):
            target = clean_target(m["target"])
        elif CODE.search(ln.inner) and (m := WORLD_ACCESS.search(ln.text)):
            rule, target = ("world-writable" if m["what"] == "Writable" else "world-readable"), ""
        elif INIT_TEXT.search(ln.inner) and ((m := UEVENTD_MODE.match(ln.text)) or (m := MKDIR_MODE.match(ln.text))):
            target = m[1]
        else:
            continue
        if not (INIT_TEXT.search(ln.inner) or CODE.search(ln.inner)):
            continue  # a layout or string that merely mentions chmod
        if CODE.search(ln.inner) and not target.startswith("/"):
            target = "(path computed at run time)"
        sev = ww_severity(target) if target.startswith("/") else "low"
        groups.setdefault((rule, ln.file + "|" + ln.inner, sev), []).append(ln)
    hits = []
    titles = {"world-writable": "Files or device nodes made writable by every app (chmod/ueventd mode with the 'other' write bit, "
                                "setWritable(true, false))",
              "world-readable": "Files made readable by every app (setReadable(true, false))"}
    for (rule, where, sev), lines in groups.items():
        hits.append(hit(rule, sev, titles[rule], lines, lines[0].app,
                        f"{len(lines)} line(s) in {where.split('|')[-1] or where.split('|')[0]}"))
    return hits


def rule_fstab(d: Diff) -> list[Hit]:
    hits = []
    fstab = re.compile(r"fstab")
    enc_old = [ln for ln in d.lines if ln.sign == "-" and fstab.search(ln.inner) and re.search(r"fileencryption=|forceencrypt=|metadata_encryption=", ln.text)]
    enc_new = {ln.text.split()[1] if len(ln.text.split()) > 1 else "" for ln in d.lines
               if ln.sign == "+" and fstab.search(ln.inner) and re.search(r"fileencryption=|forceencrypt=", ln.text)}
    dropped = [ln for ln in enc_old if (ln.text.split()[1] if len(ln.text.split()) > 1 else "") not in enc_new]
    if dropped:
        hits.append(hit("fstab-encryption-removed", "high", "Storage encryption options removed from an fstab entry", dropped))
    rw = [ln for ln in d.lines if ln.sign == "+" and fstab.search(ln.inner) and re.search(r"(^|\s|,)rw(,|\s)", ln.text)
          and re.search(r"firmware|modem|persist|system|vendor|efs|dsp", ln.text)]
    old_rw = {ln.text.split()[1] for ln in d.lines if ln.sign == "-" and fstab.search(ln.inner) and len(ln.text.split()) > 1
              and re.search(r"(^|\s|,)ro(,|\s)", ln.text)}
    rw = [ln for ln in rw if len(ln.text.split()) > 1 and ln.text.split()[1] in old_rw]
    if rw:
        hits.append(hit("fstab-read-write", "medium", "A partition that was mounted read-only is now mounted read-write", rw))
    return hits


def rule_verification(d: Diff) -> list[Hit]:
    pat = re.compile(r"DEFAULT_VERIFY_ENABLE\s*=\s*false|package_verifier_enable\"?\s*,\s*0|"
                     r"verifier_verify_adb_installs\"?\s*,\s*0|isVerificationEnabled\([^)]*\)\s*\{?\s*return false|"
                     r"ensure_verify_apps\"?\s*,\s*0|config_verifierEnable\">?false", re.I)
    # A bare `mVerifyX = false` means package verification only in the package manager or a verifier;
    # `firstVerify = false` in an app is a UI flag.
    field = re.compile(r"\b(m?[Vv]erif\w*|DEFAULT_VERIFY\w*)\s*=\s*false;")
    lines = added(d, pat) + [ln for ln in added(d, field, re.compile(r"PackageManager|[Vv]erif|PackageInstaller"))
                             if not pat.search(ln.text)]
    return per_app("package-verification-off", "high", "Package verification (the install-time app check) is switched off", lines)


def rule_flag_secure(d: Diff) -> list[Hit]:
    pat = re.compile(r"(==|!=)\s*8192\b|FLAG_SECURE\b.*(setFlags\(0|&= ?~|ignore|remove)|\b8192\b.*setFlags\(0|"
                     r"(flags|i\d?)\s*&=\s*-8193")
    lines = [ln for ln in added(d, pat) if re.search(r"Window|Surface|Screenshot|ScreenCapture|View", ln.inner)]
    return per_app("flag-secure-ignored", "high", "Apps' FLAG_SECURE (block screenshots/recording) is ignored or stripped", lines)


def rule_capture_prompt(d: Diff) -> list[Hit]:
    where = re.compile(r"MediaProjection|ScreenCapture|ScreenRecord")
    pat = re.compile(r'"[a-z][\w]*(\.[\w]+)+"|\.contains\("[\w.]+"\)|hashSet\.add\("|ignoreCheckPermission|hasProjectionPermission.*\|\|')
    lines = [ln for ln in added(d, pat, where) if not re.search(r"android\.permission\.|\"android\.|com\.android\.systemui", ln.text)]
    return per_app("capture-without-prompt", "high", "Screen capture (MediaProjection) is granted to named packages without the consent prompt", lines)


def rule_usb_prompt(d: Diff) -> list[Hit]:
    hits = []
    cfg = added(d, re.compile(r'config_disableUsbPermissionDialogs">\s*true'))
    if cfg:
        hits.append(hit("usb-prompt-off", "high", "USB permission dialogs are disabled for the whole system", cfg))
    auto = [ln for ln in added(d, re.compile(r"\bonConfirm\(\)|setPermission|grantPermission|mPermissionGranted\s*=\s*true|"
                                                 r"permissionGranted\(|setResult\(-1"), re.compile(r"Usb(Permission|Confirm)Activity"))]
    if auto:
        hits += per_app("usb-prompt-auto", "high", "The USB permission/confirm screen accepts on its own", auto)
    return hits


def rule_lockscreen(d: Diff) -> list[Hit]:
    pat = re.compile(r'config_disableLockscreenByDefault">\s*true|def_lockscreen_disabled">\s*true|lockscreen\.disabled\S*\s*[,=]\s*"?(1|true)|'
                     r"setLockScreenDisabled\(true|Don't show any circumstances|locksettings\.db")
    lines = added(d, pat)
    # The keyguard skipping its own show call (not just moved inside a try block).
    keyguard = [ln for ln in d.lines if re.search(r"KeyguardViewMediator", ln.inner) and re.search(r"^\s*showLocked\(", ln.text)]
    removed_show = [ln for ln in keyguard if ln.sign == "-"]
    if len(removed_show) <= sum(ln.sign == "+" for ln in keyguard):
        removed_show = []
    return per_app("lockscreen-off", "high", "The lock screen is disabled, skipped or its database deleted", lines + removed_show)


# Whole names only: `su`, `ksu`, `witsu`, `wits_sudo`, `root_helper`; not `surfaceflinger`, `chroot` or `rootfs`.
ROOT_WORD = r"(?:(?:wit|k|daemon)?su|\w+_su|su_\w+|\w*sudo\w*|magisk\w*|(?:\w+_)?root(?!fs|dir|path)\w*)"
SU_NAME = re.compile(rf"/(s?bin|xbin)/({ROOT_WORD}|busybox)(\.sh)?$")


def manifest(fw_id: str) -> dict[str, str]:
    """path -> the full manifest.tsv row (path, kind, size, sha256) for files."""
    f = WORK / fw_id / "manifest.tsv"
    if not f.is_file():
        return {}
    return {line.split("\t", 1)[0]: line for line in f.read_text().splitlines() if "\tfile\t" in line}


def rule_root(d: Diff) -> list[Hit]:
    hits = []
    # facts.json has the full lists; REPORT.md stops at 30 names with "+N more".
    if "executables" in d.facts:
        exe_add, exe_rem = facts_list(d.facts, "executables"), facts_list(d.facts, "executables", "removed")
    else:
        exe_add = re.findall(r"`([^`]+)`", " ".join(report_lines(d.report, r"^- Executables added")))
        exe_rem = re.findall(r"`([^`]+)`", " ".join(report_lines(d.report, r"^- Executables removed")))
    old, new = manifest(d.old_id), manifest(d.new_id)
    renamed = set()
    for r in exe_rem:
        for a in exe_add:
            if old and new:
                if old.get(r) and new.get(a) and old[r].split("\t")[2:] == new[a].split("\t")[2:]:
                    renamed.add(a)
                    hits.append(hit("root-helper-renamed", "high" if SU_NAME.search(r) else "medium",
                                    "An executable was renamed with identical contents (same size and SHA-256)",
                                    [f"old manifest.tsv: {old[r]}", f"new manifest.tsv: {new[a]}"]))
            elif Path(a).parent == Path(r).parent and Path(a).name.endswith(Path(r).name) and SU_NAME.search(r):
                renamed.add(a)
                hits.append(hit("root-helper-renamed", "high", "A su-style binary looks renamed (no manifests here to compare hashes)",
                                [f"REPORT.md: removed {r}, added {a}"]))
    for a in exe_add:
        if a not in renamed and SU_NAME.search(a):
            hits.append(hit("root-helper-added", "high", "A su/sudo-style root helper binary or script was added", [f"REPORT.md: added {a}"]))
    for r in exe_rem:
        if SU_NAME.search(r) and not any(r in h.lines[0] for h in hits):
            hits.append(hit("root-helper-removed", "low", "A su/sudo-style binary was removed (check it was not renamed)", [f"REPORT.md: removed {r}"]))
    for p in facts_list(d.facts, "files"):
        if SU_NAME.search(p) and p not in exe_add:
            hits.append(hit("root-helper-referenced", "medium", "Code now names a su/sudo-style path", [f"facts.json files.added: {p}"]))
    svc = [ln for ln in d.lines if ln.sign == "+" and re.search(r"\.rc\b", ln.inner) and
           re.search(rf"^\s*service\s+{ROOT_WORD}\s", ln.text)]
    svc += added(d, re.compile(rf'ctl\.start"?\s*,\s*"(?:\w+[_.])?{ROOT_WORD}[:"]'))
    svc += added(d, re.compile(r'^\s*(sh|/system/bin/sh)\s+-c\s+"?\$'), re.compile(r"\.sh\b"))
    hits += per_app("root-command-runner", "high", "A root service or script that runs whatever command it is given", svc)
    return hits


def rule_build(d: Diff) -> list[Hit]:
    hits = []
    props = report_section(d.report, "Build properties")
    for ln in props:
        if re.search(r"`ro\.[\w.]*build\.(tags|type)`", ln):
            hits.append(hit("build-type-changed", "medium", "Build type or signing tags changed (user/userdebug, release-keys/test-keys)", [f"REPORT.md: {ln[2:]}"]))
    for ln in report_lines(d.report, r"^- Build `ro\.build\.type`"):
        if re.search(r"`(userdebug|eng)`$", ln):
            hits.append(hit("build-userdebug", "low" if "still" in ln else "medium",
                            "The build is userdebug/eng: debuggable, root-capable by design", [f"REPORT.md: {ln[2:]}"]))
        else:
            hits.append(hit("build-type", "info", "Build type", [f"REPORT.md: {ln[2:]}"]))
    def now(ln: str) -> str:
        return ln.rsplit("->", 1)[-1]

    fp = [ln for ln in props if "fingerprint" in ln and "test-keys" in now(ln)]
    tags_release = any("release-keys" in now(ln) and "tags" in ln for ln in props)
    if tags_release and fp:
        hits.append(hit("build-tags-mismatch", "medium", "Tags now say release-keys but the fingerprint still says test-keys", [f"REPORT.md: {x[2:]}" for x in fp]))
    # Platform certificate swaps show up in SELinux mac_permissions or package signature lists.
    sig = [ln for ln in d.lines if re.search(r"mac_permissions\.xml|platform\.x509|\.pem$|keys\.conf", ln.inner)
           and re.search(r'signature="?[0-9a-f]{40,}', ln.text, re.I)]
    if sig:
        test = [ln for ln in sig if ln.sign == "+" and re.search(AOSP_TEST_CERT, ln.text, re.I)]
        hits.append(hit("signing-key-changed", "high" if test else "medium",
                        "The platform signing certificate changed" + (" to Android's public test key" if test else ""),
                        [ln for ln in sig][:4]))
    for ln in report_lines(d.report, r"^- Build `ro\.build\.version\.security_patch`"):
        hits.append(hit("security-patch-changed", "low", "Security patch level changed", [f"REPORT.md: {ln[2:]}"]))
    return hits


# Leading bytes of the AOSP test-key platform certificate (build/target/product/security/platform.x509.pem).
AOSP_TEST_CERT = r"308204a830820390a003020102020900b3998086d056cffa|308204a830820390a003020102020900f2b98e6123572c4e"


def rule_wipe(d: Diff) -> list[Hit]:
    pat = re.compile(r"rm\s+(-\w+\s+)*/data/?(\*|media\b|user\b|[\s\";]|$)|rm:-rf:/data|ACTION_FACTORY_RESET|MASTER_CLEAR\"|FACTORY_RESET\"|"
                     r"rebootWipeUserData|--wipe_data|wipe_data|wipeData\s*=\s*true|reboot recovery|reboot\(\"recovery|"
                     r"uninstall-system-updates|deletePackage\(|\.wipeData\(|MasterClear", re.I)
    lines = [ln for ln in added(d, pat) if not ln.text.lstrip().startswith(("#", "//", "*", "import "))
             and not re.search(r"<string|<item|<permission|android:name=\"android\.permission", ln.text)]
    hits = []
    for app, g in group(lines).items():
        # A reset button on a settings screen is expected; the same call from a service or receiver is not.
        strong = [ln for ln in g if re.search(r"^\s*rm\b|rm:-rf|WipeUserData|wipe_data|wipeData\s*=\s*true", ln.text, re.I)
                  or (re.search(r"FACTORY_RESET|MasterClear", ln.text, re.I)
                      and not re.search(r"Activity|Fragment|Dialog|Preference|Controller", ln.inner))]
        ui_only = all(re.search(r"Activity|Fragment|Dialog|Preference|Controller", ln.inner) and "FACTORY_RESET" in ln.text for ln in g)
        hits.append(hit("wipe-or-reset", "high" if strong else "low" if ui_only else "medium",
                        "Code or scripts that wipe /data, factory-reset, reboot to recovery or remove packages", g, app))
    # File-name triggers next to an install/reset path: "if name contains X then wipe/force".
    trig = added(d, re.compile(r'getName\(\)\.(contains|startsWith|endsWith)\("[\w.-]+"\)|ls /\S+/[\w.-]*(reset|wipe|clear)[\w.-]*'), CODE)
    trig = [ln for ln in trig if re.search(r"reset|wipe|clear|force|update|ota", ln.text, re.I)]
    trig += added(d, re.compile(r"ls /\S*(udisk|usb|sdcard|storage)\S*(reset|wipe|clear)", re.I))
    hits += per_app("file-name-trigger", "medium", "A file name on storage or in an update triggers a reset or forced install", trig)
    return hits


def rule_silent_install(d: Diff) -> list[Hit]:
    pat = re.compile(r"\bpm\s+install\b|\bpm\s+uninstall\b|\"pm\",\s*\"(install|uninstall)\"|PackageInstaller\.Session|installPackage\w*\(|"
                     r"\.commit\(PendingIntent|session\.commit\(|INSTALL_REPLACE_EXISTING")
    lines = [ln for ln in added(d, pat) if not ln.text.lstrip().startswith(("#", "//", "*", "import "))]
    perms = added(d, re.compile(r'uses-permission android:name="android\.permission\.(INSTALL_PACKAGES|DELETE_PACKAGES)"'))
    hits = per_app("silent-install", "medium", "Apps installed or removed without the user (pm install, PackageInstaller sessions)", lines)
    hits += per_app("install-permission", "medium", "An app gains the permission to install or delete packages", perms)
    return hits


def rule_grants(d: Diff) -> list[Hit]:
    hits = []
    loop = added(d, re.compile(r"\bpm\s+grant\b|grantRuntimePermission\(|updatePermissionFlags|appops\s+set|"
                               r"setUidMode\(|setMode\([^)]*(MANAGE_EXTERNAL|OP_|\d+)[^)]*,\s*0\)|"
                               r"MANAGE_EXTERNAL_STORAGE.*(setMode|allow)|confirmPermissionsReview\(|"
                               r"grantAllPermission|autoGrant|grant\w*RuntimePermissions?\w*\(|grantPermissionsTo\w+\(", re.I))
    loop = [ln for ln in loop if not ln.text.lstrip().startswith(("#", "//", "*", "import ")) and not re.search(r"<string", ln.text)]
    for app, g in group(loop).items():
        code = [ln for ln in g if CODE.search(ln.inner) or INIT_TEXT.search(ln.inner)]
        # An app's bundled script granting only itself its own permissions is context, not a finding.
        own = all(re.search(rf"\b(pm grant|appops set)\s+{re.escape(app)}\s", ln.text) for ln in g)
        hits.append(hit("permission-grant", "low" if own else "high" if code else "medium",
                        "Runtime permissions granted by code, not by the user (grant loops, appops, auto-confirmed review)", code or g, app))
    # default-permissions XML exceptions and privapp permission lists.
    xml = [ln for ln in d.lines if ln.sign == "+" and re.search(r"default-permissions|privapp-permissions|permissions/.*\.xml", ln.inner)
           and re.search(r"<(exception|permission|privapp-permissions) ", ln.text)]
    hits += per_app("default-grant-xml", "medium", "Packages added to default-permission or privileged-permission XML", xml)
    # Framework/overlay arrays that list packages for special treatment.
    resource_only = {app for app in d.by_app if app != "(files)" and not any(ln.file.endswith(".code.diff") for ln in d.by_app[app])}
    arr = []
    current: dict[str, str] = {}
    for ln in d.lines:
        if not ln.inner.endswith("arrays.xml"):
            continue
        # A list name seen in one hunk says nothing about the next hunk.
        key = f"{ln.file}|{ln.inner}|{ln.hunk}"
        if m := re.search(r'<(string-)?array name="([^"]+)"', ln.text):
            current[key] = m[2]
        name = current.get(key, "")
        if ln.sign != "+" or not re.search(r"<item>[a-z][\w]*(\.[\w]+){1,}</item>", ln.text):
            continue
        # The list's name is often outside the hunk; in a resource-only framework package any package
        # list is a list of apps singled out for system treatment.
        if re.search(r"permission|grant|whitelist|allowlist|system_app|location|privileged|auto", name, re.I) or \
                (not name and ln.app in resource_only):
            arr.append(Line(ln.file, f"{ln.inner} [{name or 'list name not in the diff'}]", ln.no, ln.sign, ln.text, ln.app))
    hits += per_app("package-allowlist", "medium", "Packages added to a framework list that grants permissions or system treatment", arr)
    return hits


DANGEROUS_PERMS = re.compile(r'uses-permission android:name="android\.permission\.(INJECT_EVENTS|REBOOT|MASTER_CLEAR|WRITE_SECURE_SETTINGS|'
                             r'READ_PRIVILEGED_PHONE_STATE|READ_PHONE_STATE|ACCESS_FINE_LOCATION|ACCESS_BACKGROUND_LOCATION|RECORD_AUDIO|'
                             r'CAMERA|READ_CONTACTS|READ_CALL_LOG|READ_SMS|MANAGE_EXTERNAL_STORAGE|CAPTURE_\w+|'
                             r'MANAGE_MEDIA_PROJECTION|DEVICE_POWER|MANAGE_USB|GRANT_RUNTIME_PERMISSIONS|INTERACT_ACROSS_USERS_FULL)"')


def rule_permissions(d: Diff) -> list[Hit]:
    lines = [ln for ln in net_added(d, DANGEROUS_PERMS) if ln.inner.endswith("AndroidManifest.xml")]
    hits = []
    for app, g in group(lines).items():
        names = sorted({DANGEROUS_PERMS.search(ln.text)[1] for ln in g})
        sev = "medium" if set(names) & {"INJECT_EVENTS", "REBOOT", "MASTER_CLEAR", "WRITE_SECURE_SETTINGS", "READ_PRIVILEGED_PHONE_STATE",
                                         "MANAGE_EXTERNAL_STORAGE", "GRANT_RUNTIME_PERMISSIONS", "MANAGE_MEDIA_PROJECTION"} else "low"
        hits.append(hit("sensitive-permission", sev, "An app now requests sensitive permissions: " + ", ".join(names), g, app))
    sys_uid = added(d, re.compile(r'android:sharedUserId="android\.uid\.system"'))
    hits += per_app("system-uid", "medium", "An app now runs as the system user (sharedUserId android.uid.system)", sys_uid)
    exported = added(d, re.compile(r"exported fix to true|setExported\(true\)|\.exported\s*=\s*true"), CODE)
    hits += per_app("forced-export", "medium", "Framework code forces components to be exported", exported)
    return hits


def group(lines: list[Line]) -> dict[str, list[Line]]:
    out: dict[str, list[Line]] = {}
    for ln in lines:
        out.setdefault(ln.app, []).append(ln)
    return out


def rule_fake(d: Diff) -> list[Hit]:
    hits = []
    bench = [ln for ln in added(d, BENCHMARK_PACKAGES) if not ln.inner.endswith(("strings.xml", "public.xml"))]
    hits += per_app("benchmark-spoof", "high", "Code names benchmark/system-info apps: usually to change what they report", bench)
    fake_prop = re.compile(r"persist\.[\w.]*(size|ram|rom|flash|memory|mem|storage|capacity|cpu_?model|chip|version|release|resolution)[\w.]*", re.I)
    props = [p for p in facts_list(d.facts, "props") if (fake_prop.fullmatch(p) or re.search(r"fake|spoof|change_?(ram|rom|resolution|version)", p, re.I))
             and not re.search(r"camera|sensor|video|audio|mic|display|lcd|screen\.", p, re.I)]
    if props:
        users = [ln for ln in added(d, re.compile("|".join(re.escape(p) for p in props))) if CODE.search(ln.inner)]
        hits.append(hit("fake-hw-prop", "medium", "New properties that set storage/RAM/version figures shown to the user or apps",
                        [f"facts.json props.added: {', '.join(props)}"] + [ln.cite() for ln in users[:MAX_SHOWN]]))
    # The Android version or patch date written as a literal where the system value would be read.
    ver = added(d, re.compile(r'(RELEASE|release|VERSION|version)\w*\s*(=|\.set\(\w*,?)\s*"1[0-9]"|return "1[0-9]";|'
                              r'<string name="\w*(android|security|patch)\w*(date|patch|version)\w*">[A-Z][a-z]+ \d{1,2}, 20\d\d<|'
                              r'fake_?(sd|stat|size|ram|rom|storage|mem|version|cpu|chip|model)|spoof|change_?(ram|resolution|memory)|'
                              r'persist/\S*(change|memory|ram|resolution)\w*|'
                              + "".join(f"{m}|" for ms in VENDOR_FAKE_MARKERS.values() for m in ms) +
                              r'Integer\.parseInt\(\w+\) > Integer\.parseInt\(Build\.VERSION\.RELEASE|'
                              r'SystemProperties\.get\w*\("persist\.[\w.]*(flash|ram|rom|mem|storage)[\w.]*"', re.I),
                   CODE)
    ver += [ln for ln in d.lines if ln.sign == "+" and not CODE.search(ln.inner)
            and re.search(r'<string name="\w*(android\d+|patch|security)\w*">[A-Z][a-z]+ \d{1,2}, 20\d\d<', ln.text)]
    ver = [ln for ln in ver if not re.search(r"^\s*(import|//|\*|public static final int \w+ = (0x)?[0-9a-f]+;)|\bS?Log\.\w\(", ln.text)]
    hits += per_app("fake-version-or-hw", "high", "Version, patch date, RAM, storage or resolution values faked or overridden", ver)
    return hits


URL = re.compile(r"""\b((?:https?|wss?|mqtt|tcp|ftp)://[^\s"'<>\\)]+)""")
# Calls and dotted property names only: a bare "imei" string is as often a JSON field or a log label.
IMEI = re.compile(r"getImei\(|getDeviceId\(|getSubscriberId\(|getSimSerialNumber\(|getMeid\(|Build\.getSerial\(|"
                  r"\"\w+\.[\w.]*imei[\w.]*\"|ro\.serialno|getLine1Number\(", re.I)
LOCATION = re.compile(r"getLastKnownLocation\(|requestLocationUpdates\(|requestSingleUpdate\(|getLatitude\(\)|getLongitude\(\)|"
                      r"getCellLocation\(|getAllCellInfo\(|getScanResults\(|getSSID\(")
UPLOAD = re.compile(r"multipart/form-data|MultipartBody|FileBody|uploadFile\(|\.upload\(|setMailServerHost|javax\.mail|"
                    r"smtp\.|Transport\.send|FTPClient|storeFile\(", re.I)


def data_reads(d: Diff) -> dict[str, dict[str, list[Line]]]:
    """Per app, which kinds of personal data the new code reads."""
    out: dict[str, dict[str, list[Line]]] = {}
    for kind, pat in (("IMEI/device id", IMEI), ("location/Wi-Fi", LOCATION), ("file upload/mail", UPLOAD)):
        for ln in net_added(d, pat, CODE):
            # Method definitions (a bean's own getDeviceId()) are not reads.
            if re.match(r"\s*(public|private|protected)\s+[\w<>\[\], ]+\s+\w+\([^)]*\)\s*(throws [\w., ]+)?\{", ln.text):
                continue
            if ln.text.lstrip().startswith(("//", "*", "import ")) or re.search(r"[Ee]vent\w*\.getDeviceId|InputDevice|"
                                                                          r"\bdevice\w*\.getDeviceId", ln.text):
                continue
            out.setdefault(ln.app, {}).setdefault(kind, []).append(ln)
    return out


def host_of(u: str) -> str:
    """Lower-case host of a URL, "" when it has none or does not parse (`http://[` in a format string)."""
    try:
        return (urlsplit(u).hostname or "").lower()
    except ValueError:
        return ""


def domain(host: str) -> str:
    """Registrable domain, roughly: a.b.example.com -> example.com, x.qq.com.cn -> qq.com.cn."""
    parts = host.split(".")
    if len(parts) > 2 and len(parts[-1]) == 2 and parts[-2] in ("com", "net", "org", "gov", "edu", "co", "ac"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def real_host(host: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}", host)) and not INERT_HOSTS.search(host)


# Where a URL is something the app calls rather than a licence or a help page.
URL_SOURCE = re.compile(r"\.java\b|\.kt\b|res/values/strings\.xml|res/xml/|AndroidManifest\.xml|\.json$|\.properties$|\.conf$|\.rc$|\.sh$|\.xml$")
URL_NOT_SOURCE = re.compile(r"assets/.*\.(html?|txt)$|META-INF|LICENSE|NOTICE|licen[cs]e", re.I)


def rule_network(d: Diff) -> list[Hit]:
    facts_urls = set(facts_list(d.facts, "urls"))
    facts_removed = set(facts_list(d.facts, "urls", "removed"))
    reads = data_reads(d)
    seen: dict[tuple[str, str], list[tuple[str, Line]]] = {}
    urls_in_diff: set[str] = set()
    minus = {m for ln in d.lines if ln.sign == "-" for m in URL.findall(ln.text)}
    for ln in d.lines:
        if ln.sign != "+" or "://" not in ln.text:
            continue
        if ln.text.lstrip().startswith(("//", "*", "#")) or "xmlns" in ln.text or "schemas.android" in ln.text:
            continue
        if not URL_SOURCE.search(ln.inner) or URL_NOT_SOURCE.search(ln.inner):
            continue
        for u in URL.findall(ln.text):
            urls_in_diff.add(u)
            if u in minus:
                continue
            host = host_of(u)
            if real_host(host):
                seen.setdefault((ln.app, domain(host)), []).append((host, ln))
    app_domains: dict[str, int] = {}
    for app, _ in seen:
        app_domains[app] = app_domains.get(app, 0) + 1
    hits = []
    for (app, dom), found in seen.items():
        hosts = sorted({h for h, _ in found})
        lines = [ln for _, ln in found]
        plain = any(re.search(r"(http|ftp)://", ln.text) for ln in lines)
        tracker = any(TRACKER_HOSTS.search(h) for h in hosts)
        test = all(re.search(r"test|dev|staging|sandbox", h) for h in hosts)
        kinds = sorted(reads.get(app, {}))
        # Personal data and a host in one class, or in an app that talks to few places, is the pattern to flag.
        near = [k for k in kinds if any(r.inner == ln.inner for r in reads[app][k] for ln in lines)]
        if (near or (kinds and app_domains[app] <= 5)) and app != "(files)" and not test:
            sev = "high"
        elif plain or tracker or kinds:
            sev = "medium" if not test else "low"
        else:
            sev = "low"
        what = []
        if plain:
            what.append("plain HTTP")
        if tracker:
            what.append("analytics/crash-report SDK")
        if kinds:
            what.append("same app newly reads " + ", ".join(kinds))
        title = f"New network host {', '.join(hosts[:4])}{' +' + str(len(hosts) - 4) if len(hosts) > 4 else ''}" \
                + (f" ({'; '.join(what)})" if what else "")
        extra = [f"also reads {k}: {v[0].cite()}" for k, v in sorted(reads.get(app, {}).items())]
        hits.append(hit("network-host", sev, title, extra + lines, app))
    # URLs only known from facts.json: apps that were not decompiled (third-party, Google).
    leftover: dict[str, list[str]] = {}
    # A facts URL cut from a longer string, or a diff URL longer than the literal, is the same URL.
    for u in sorted(facts_urls - urls_in_diff):
        if any(x.startswith(u) or u.startswith(x) for x in urls_in_diff):
            continue
        host = host_of(u)
        if real_host(host):
            leftover.setdefault(domain(host), []).append(u)
    for dom, us in sorted(leftover.items()):
        plain = any(u.startswith(("http:", "ftp:")) for u in us)
        tracker = any(TRACKER_HOSTS.search(u) for u in us)
        hits.append(hit("network-host-undecompiled", "medium" if tracker else "low" if len(leftover) <= 10 else "info",
                        f"New host(s) under {dom} in an app that was not decompiled"
                        + (" (plain HTTP)" if plain else "") + (" (analytics/crash-report SDK)" if tracker else ""),
                        [f"facts.json urls.added: {u}" for u in sorted(us)[:4]] + ([f"... {len(us) - 4} more"] if len(us) > 4 else [])))
    # A domain is gone only when nothing on the new side still names it: added lines, unchanged context
    # lines and facts.json urls that were not removed.
    remaining = facts_urls | d.context_urls | {u for ln in d.lines if ln.sign == "+" for u in URL.findall(ln.text)}
    gone = {domain(host_of(u)) for u in facts_removed} - {domain(host_of(u)) for u in remaining}
    gone = {h for h in gone if real_host(h)}
    if gone:
        hits.append(hit("network-host-removed", "info", "Domains no longer named anywhere in the firmware's code",
                        [f"facts.json urls.removed: {h}" for h in sorted(gone)]))
    cleartext = added(d, re.compile(r'<base-config cleartextTrafficPermitted="true"|usesCleartextTraffic="true"'))
    hits += per_app("cleartext-allowed", "medium", "Plain-HTTP traffic allowed to any host", cleartext)
    # Cleartext for named domains: the domain lines follow the domain-config line.
    named = [ln for ln in d.lines if ln.sign == "+" and "network_security_config" in ln.inner
             and re.search(r'<domain-config cleartextTrafficPermitted="true"|<domain [^>]*>[\w.-]+</domain>', ln.text)]
    hits += per_app("cleartext-domains", "low", "Plain-HTTP traffic allowed to named domains", named)
    sdk = added(d, re.compile(r'android:name="(BaiduMobAd_\w+|UMENG_\w+|BUGLY_\w+|TD_APP_ID|TD_CHANNEL_ID|JPUSH_\w+|GETUI_\w+|'
                              r'com\.google\.firebase\.\w+|firebase_\w+_collection_enabled|com\.crashlytics\.\w+|'
                              r'com\.baidu\.mobstat\.\w+|com\.umeng\.\w+|com\.tencent\.bugly\.\w+|io\.sentry\.\w+)"'))
    for app, g in group(sdk).items():
        loc = [ln for ln in g if re.search(r"GPS|LOCATION|CELL|WIFI", ln.text)]
        hits.append(hit("tracking-sdk", "medium" if loc else "low",
                        "Analytics/crash-report SDK configured in the manifest" + (" with location collection" if loc else ""), g, app))
    # Per app: endpoints the old code had and the new code drops.
    plus = {(ln.app, u) for ln in d.lines if ln.sign == "+" for u in URL.findall(ln.text)}
    gone_lines = [ln for ln in d.lines if ln.sign == "-" and URL_SOURCE.search(ln.inner) and not URL_NOT_SOURCE.search(ln.inner)
                  and any((ln.app, u) not in plus and real_host(host_of(u)) for u in URL.findall(ln.text))]
    hits += per_app("network-url-removed", "info", "URLs the app no longer carries", gone_lines)
    return hits


def rule_identifiers(d: Diff) -> list[Hit]:
    hits = []
    # The logged value itself, right after a '+', must be the identifier or secret, not a name that mentions one.
    log = added(d, re.compile(r"(Log\.\w|Slog\.\w|println)\(.*\+\s*[\w.]*?(?<![a-z])(get)?(imei|Imei|IMEI|password|Password|passwd|"
                              r"passphrase|Passphrase|preSharedKey|simSerialNumber|SimSerialNumber|getSerial\(\)|serialno)\w*(\(\w*\))?\s*[),+]"), CODE)
    log = [ln for ln in log if not re.search(r"\+\s*[\w.]*(Time|Count|View|Util|Port|Flag|State|Status|Enable|Len)\b", ln.text)]
    hits += per_app("secret-logged", "high", "IMEI, serial or a password written to the system log", log)
    reads = data_reads(d)
    for app, kinds in reads.items():
        if "IMEI/device id" in kinds:
            lines = kinds["IMEI/device id"]
            hits.append(hit("reads-imei", "medium", "New code reads the IMEI, serial or phone/SIM identifiers", lines, app))
    for app, g in group([ln for ln in added(d, LOCATION, CODE, "-") if re.search(r"requestLocationUpdates|getLastKnownLocation|GPSLocation|LocationManager", ln.text)]).items():
        still = [ln for ln in d.by_app.get(app, []) if ln.sign == "+" and LOCATION.search(ln.text)]
        if not still:
            hits.append(hit("location-read-removed", "info", "The app no longer asks for location in the changed code", g, app))
    trunc = [ln for ln in d.lines if ln.sign == "-" and re.search(r"substring\(0,\s*14\)", ln.text) and re.search(r"[Ii]mei|Phone", ln.inner + ln.text)]
    hits += per_app("imei-full", "medium", "The IMEI is no longer truncated before being handed out", trunc)
    return hits


def rule_credentials(d: Diff) -> list[Hit]:
    pat = re.compile(r'(pass(word|wd)?|pwd|secret|app_?key|appSecret|access_?key|(access|auth|api)_?token)\w*"?\s*[:=,(]\s*"[^"\s]{4,}"|'
                     r'set(Password|UserName|MailServerHost)\("[^"]+"|smtp\.[\w.-]+|ftp://[^\s"@]+:[^\s"@]+@', re.I)
    lines = [ln for ln in added(d, pat, CODE) if not re.search(r'"(password|pwd|token|secret)"\s*[,)]|R\.string|getString', ln.text, re.I)]
    hits = []
    for app, g in group(lines).items():
        mail = [ln for ln in g if re.search(r"smtp|mail|ftp", ln.text, re.I)]
        sev = "high" if mail else "low"
        hits.append(hit("hardcoded-credential", sev, "Hard-coded passwords, keys or mail-server logins in code", g, app))
    return hits


def rule_remote_access(d: Diff) -> list[Hit]:
    pat = re.compile(r"service\.adb\.tcp\.port\"?\s*,\s*\"\d+|setprop\s+(service|persist)\.adb\.tcp\.port\s+\d+|adb tcpip|"
                     r"\"adb_wifi_enabled\"\s*,\s*1|\"adb_enabled\"\s*,\s*1|ADB_ENABLED\s*,\s*1|ctl\.start\"?\s*,\s*\"adbd")
    return per_app("adb-network", "high", "ADB over the network (port 5555 style) can be switched on", added(d, pat))


def rule_privacy_config(d: Diff) -> list[Hit]:
    hits = []
    mac = added(d, re.compile(r'config_wifi_connected_mac_randomization_supported">\s*false|mac_randomization\w*"?\s*[,=]\s*"?0|'
                              r'config_wifi_(connected|scan)_mac_randomization\w*">\s*false'))
    hits += per_app("mac-randomisation-off", "medium", "Wi-Fi MAC randomisation switched off: networks see the real MAC", mac)
    loc = added(d, re.compile(r'def_location_providers_allowed">\s*\S*gps|location_providers_allowed"?\s*,\s*"[^"]*gps|'
                              r'def_location_mode">\s*3|LOCATION_MODE\w*\s*,\s*3'))
    hits += per_app("location-default-on", "medium", "Location is switched on by default", loc)
    backup = added(d, re.compile(r'def_backup_transport">[^<]*google|backup\.BackupTransportService|def_backup_enabled">\s*true'))
    hits += per_app("backup-to-google", "medium", "Default backup transport or backup switch changed", backup)
    settings = added(d, re.compile(r'(screen_off_timeout|SCREEN_OFF_TIMEOUT)\w*"?\s*,\s*(Integer\.MAX_VALUE|2147483647|-1)|'
                                   r'setOverlaySettingsEnabled\([^)]*true|install_non_market_apps"?\s*,\s*1|'
                                   r'development_settings_enabled"?\s*,\s*1'), CODE)
    hits += per_app("security-setting-forced", "medium", "A security-relevant setting is forced by code", settings)
    kill = added(d, re.compile(r"forceStopPackage\(|am force-stop"))
    kill = [ln for ln in kill if not re.search(r"^\s*(public|private|protected)?\s*\w+ forceStopPackage\(", ln.text)
            and not re.search(r"Activity|Fragment|Dialog", ln.inner)]
    hits += per_app("force-stop", "low", "A system service force-stops other apps", kill)
    dropped = [ln for ln in d.lines if ln.sign == "-" and (
        re.search(r'android:key="(screen_pinning|lockscreen|encryption|credential|security|device_admin|unknown_sources|'
                  r'install_unknown|app_pinning)\w*"', ln.text) or re.search(r"setForceAppStandby\([^)]*,\s*(1|true)\)", ln.text))]
    plus_keys = {m[0] for ln in d.lines if ln.sign == "+" for m in re.findall(r'android:key="(\w+)"', ln.text)}
    dropped = [ln for ln in dropped if not any(k in plus_keys for k in re.findall(r'android:key="(\w+)"', ln.text))]
    hits += per_app("security-control-removed", "medium", "A security setting or background restriction is removed", dropped)
    regulatory = [ln for ln in d.lines if ln.sign == "+" and re.search(r"\.(ini|conf|cfg)$|WCNSS|wlan", ln.inner)
                  and re.search(r"^\s*(\w*(country|etsi|srd|dfs|regdomain|reg_domain|indoor)\w*)\s*=", ln.text, re.I)]
    hits += per_app("wifi-regulatory", "low", "Wi-Fi regulatory settings (country, DFS, SRD channels) changed", regulatory)
    return hits


RULES = [rule_world_writable, rule_fstab, rule_verification, rule_flag_secure, rule_capture_prompt, rule_usb_prompt,
         rule_lockscreen, rule_root, rule_build, rule_wipe, rule_silent_install, rule_grants, rule_permissions, rule_fake,
         rule_network, rule_identifiers, rule_credentials, rule_remote_access, rule_privacy_config]


# --------------------------------------------------------------------------- output


def label(app: str) -> str:
    for prefix, name in VENDOR_LABELS.items():
        if app.startswith(prefix):
            return f"{app} ({name})"
    return app


def run(root: Path) -> tuple[Diff, list[Hit]]:
    d = load(root)
    hits = [h for rule in RULES for h in rule(d)]
    hits.sort(key=lambda h: (SEVERITIES.index(h.severity), h.rule, h.app))
    return d, hits


def markdown(d: Diff, hits: list[Hit]) -> str:
    out = [f"# Rule findings: {d.old_id} -> {d.new_id}", ""]
    counts = {s: sum(h.severity == s for h in hits) for s in SEVERITIES}
    out += ["Counts: " + ", ".join(f"{s} {n}" for s, n in counts.items()), ""]
    for sev in SEVERITIES:
        chosen = [h for h in hits if h.severity == sev]
        if not chosen:
            continue
        out += [f"## {sev.capitalize()}", ""]
        for h in chosen:
            app = f" [{label(h.app)}]" if h.app and h.app != "(files)" else ""
            detail = f" ({h.detail})" if h.detail else ""
            out.append(f"- **{h.rule}**{app}: {h.title}{detail}")
            for line in h.lines[:MAX_SHOWN]:
                shown = line.replace("`", "'")
                out.append(f"  - `{shown}`")
            if len(h.lines) > MAX_SHOWN:
                out.append(f"  - ... {len(h.lines) - MAX_SHOWN} more")
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("diff_dir", type=Path)
    ap.add_argument("--json", type=Path, help="also write the findings as JSON here")
    ap.add_argument("--min-severity", choices=SEVERITIES, default="info")
    args = ap.parse_args()
    if not args.diff_dir.is_dir():
        sys.exit(f"error: {args.diff_dir} is not a folder")
    d, hits = run(args.diff_dir)
    hits = [h for h in hits if SEVERITIES.index(h.severity) <= SEVERITIES.index(args.min_severity)]
    print(markdown(d, hits))
    if args.json:
        args.json.write_text(json.dumps({"old": d.old_id, "new": d.new_id, "findings": [h.__dict__ for h in hits]},
                                        indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
