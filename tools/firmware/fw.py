#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["brotli==1.1.0", "pyaxmlparser==0.3.31"]
# ///
"""Unpack head-unit OTA zips and report what changed between two of them.

  fw.py extract <ota.zip>...            unpack into WORK/<id>/fs/<partition>/
  fw.py frontmatter <id>                print the YAML frontmatter for src/data/updates
  fw.py diff <old-id> <new-id>          write WORK/diffs/<old>..<new>/ (report + source diffs)

WORK defaults to ~/Dev/firmwares/_work and can be changed with FW_WORK.
Nothing here needs root, FUSE or a mounted filesystem: ext4 images are read by
e2fsprogs' debugfs, EROFS images by erofs-utils' fsck.erofs.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

WORK = Path(os.environ.get("FW_WORK", Path.home() / "Dev/firmwares/_work"))
FS_PARTITIONS = ["system", "system_ext", "product", "vendor", "odm", "system_dlkm", "vendor_dlkm", "odm_dlkm", "oem"]
EXT4_MAGIC = b"\x53\xef"  # at offset 1080
EROFS_MAGIC = b"\xe2\xe1\xf5\xe0"  # at offset 1024
# Rebuilt on every build whatever the source did, so they only drown the report.
NOISE = re.compile(r"\.(odex|vdex|art|oat|prof)$|/oat/|/build\.prop$|/prop\.default$|/default\.prop$|/lost\+found/")
TEXT_SUFFIXES = {".xml", ".rc", ".prop", ".conf", ".cfg", ".txt", ".json", ".sh", ".ini", ".list", ".csv", ".properties"}


def tool(name: str, *brew_paths: str) -> str:
    """Resolve an external binary, including Homebrew's keg-only locations."""
    for candidate in (shutil.which(name), *brew_paths):
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit(f"error: `{name}` not found. See tools/firmware/README.md for install steps.")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, **kw)


# --------------------------------------------------------------------------- extract


def hash_file(path: Path) -> dict[str, str]:
    hashes = {name: hashlib.new(name) for name in ("md5", "sha1", "sha256")}
    with path.open("rb") as fh:
        while chunk := fh.read(8 << 20):
            for h in hashes.values():
                h.update(chunk)
    return {name: h.hexdigest() for name, h in hashes.items()}


def sdat2img(transfer_list: Path, dat: Path, out: Path) -> None:
    """Rebuild a raw image from an Android block-based OTA (system.new.dat + transfer.list)."""
    lines = transfer_list.read_text().splitlines()
    version = int(lines[0])
    commands = lines[4:] if version >= 2 else lines[2:]
    block, max_end = 4096, 0
    with dat.open("rb") as src, out.open("wb") as dst:
        for line in commands:
            op, _, ranges = line.partition(" ")
            if op not in ("new", "erase", "zero"):
                sys.exit(f"error: {transfer_list.name} has a `{op}` command: this is an incremental OTA, not a full one")
            nums = [int(n) for n in ranges.split(",")[1:]]
            for start, end in zip(nums[::2], nums[1::2]):
                max_end = max(max_end, end)
                if op != "new":
                    continue
                dst.seek(start * block)
                remaining = (end - start) * block
                while remaining:
                    chunk = src.read(min(remaining, 8 << 20))
                    if not chunk:
                        sys.exit(f"error: {dat.name} ended early; the zip is probably truncated")
                    dst.write(chunk)
                    remaining -= len(chunk)
        # erase/zero ranges past the last "new" block still belong to the filesystem.
        dst.truncate(max_end * block)


def images_from_zip(zip_path: Path, img_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        if "payload.bin" in names:
            dumper = tool("payload-dumper-go")
            listing = run([dumper, "-l", str(zip_path)], capture_output=True).stdout
            present = set(re.findall(r"(\w+) \(", listing))
            wanted = [p for p in FS_PARTITIONS if p in present]
            print(f"  payload.bin: {', '.join(wanted)}")
            run([dumper, "-q", "-c", str(os.cpu_count() or 4), "-p", ",".join(wanted), "-o", str(img_dir), str(zip_path)])
            return

        import brotli

        found = False
        for part in FS_PARTITIONS:
            tl = f"{part}.transfer.list"
            dat = next((n for n in (f"{part}.new.dat.br", f"{part}.new.dat") if n in names), None)
            if tl in names and dat:
                found = True
                print(f"  block OTA: {part}")
                with tempfile.TemporaryDirectory(dir=img_dir) as tmp:
                    raw = Path(tmp) / f"{part}.new.dat"
                    with zf.open(dat) as src, raw.open("wb") as dst:
                        if dat.endswith(".br"):
                            dec = brotli.Decompressor()
                            while chunk := src.read(8 << 20):
                                dst.write(dec.process(chunk))
                            if not dec.is_finished():
                                sys.exit(f"error: {dat} is truncated")
                        else:
                            shutil.copyfileobj(src, dst, 8 << 20)
                    tl_path = Path(tmp) / tl
                    tl_path.write_bytes(zf.read(tl))
                    sdat2img(tl_path, raw, img_dir / f"{part}.img")
            elif f"{part}.img" in names:
                found = True
                zf.extract(f"{part}.img", img_dir)
        if not found:
            sys.exit(f"error: {zip_path.name} has no payload.bin, *.new.dat(.br) or *.img partitions")


def unpack_image(img: Path, dest: Path) -> None:
    with img.open("rb") as fh:
        head = fh.read(1084)
    dest.mkdir(parents=True, exist_ok=True)
    if head[1080:1082] == EXT4_MAGIC:
        debugfs = tool("debugfs", "/opt/homebrew/opt/e2fsprogs/sbin/debugfs", "/usr/local/opt/e2fsprogs/sbin/debugfs", "/sbin/debugfs")
        # rdump can't chown to Android's uids as a normal user and says so per file; the data is intact.
        res = subprocess.run([debugfs, "-R", f'rdump / "{dest}"', str(img)], capture_output=True, text=True)
        errors = [l for l in res.stderr.splitlines() if l and not l.startswith("debugfs ") and "changing ownership" not in l]
        if res.returncode or errors:
            sys.exit(f"error: debugfs failed on {img.name}:\n" + "\n".join(errors[:20]))
    elif head[1024:1028] == EROFS_MAGIC:
        run([tool("fsck.erofs"), f"--extract={dest}", "--no-preserve", str(img)], capture_output=True)
    else:
        sys.exit(f"error: {img.name} is neither ext4 nor EROFS")
    # Android images carry modes like 0600 files and 0700 dirs; make everything readable to us.
    for root, dirs, files in os.walk(dest):
        for name in dirs + files:
            p = Path(root, name)
            if not p.is_symlink():
                mode = p.stat().st_mode
                # Dirs need u+w so the tree can be deleted; files only need to be readable.
                wanted = mode | (0o700 if p.is_dir() else 0o400)
                if wanted != mode:
                    p.chmod(wanted)


def read_props(path: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                props[k.strip()] = v.strip()
    return props


def all_props(fs: Path) -> dict[str, dict[str, str]]:
    found = {}
    for name in ("build.prop", "prop.default", "default.prop"):
        for p in fs.glob(f"*/**/{name}"):
            found[str(p.relative_to(fs))] = read_props(p)
    return dict(sorted(found.items()))


def prop(props: dict[str, dict[str, str]], *keys: str) -> str:
    """First value found, system build.prop before vendor, matching the old script."""
    order = ["system/system/build.prop", "system/build.prop", "vendor/build.prop"]
    for key in keys:
        for file in order + [f for f in props if f not in order]:
            if value := props.get(file, {}).get(key):
                return value
    return ""


def vendor_platform(display_id: str) -> tuple[str, str]:
    if m := re.match(r"GT(\d)", display_id):
        return "zxw", f"gt{m[1]}"
    if m := re.search(r"-(M\d{3})", display_id, re.I):
        return "ksw", m[1].lower()
    if "Userdebug" in display_id:
        return "ksw", "m501"
    return "", ""


def write_manifest(fs: Path, out: Path) -> None:
    rows = []
    for root, dirs, files in os.walk(fs):
        dirs.sort()
        for name in sorted(files) + [d for d in dirs if Path(root, d).is_symlink()]:
            p = Path(root, name)
            rel = p.relative_to(fs).as_posix()
            if p.is_symlink():
                rows.append(f"{rel}\tlink\t0\t{os.readlink(p)}")
            else:
                rows.append(f"{rel}\tfile\t{p.stat().st_size}\t{hashlib.sha256(p.read_bytes()).hexdigest()}")
    out.write_text("\n".join(sorted(rows)) + "\n")


def cmd_extract(args) -> None:
    for zip_path in map(Path, args.zips):
        fw_id = zip_path.name.removesuffix(".zip")
        dest = WORK / fw_id
        if (dest / "meta.json").exists() and not args.force:
            print(f"{fw_id}: already extracted, skipping (use --force to redo)")
            continue
        print(f"{fw_id}: extracting")
        shutil.rmtree(dest, ignore_errors=True)
        img_dir = dest / "img"
        img_dir.mkdir(parents=True)
        with cf.ThreadPoolExecutor(1) as pool:
            signatures = pool.submit(hash_file, zip_path)
            images_from_zip(zip_path, img_dir)
            for img in sorted(img_dir.glob("*.img")):
                print(f"  unpacking {img.stem}")
                unpack_image(img, dest / "fs" / img.stem)
            if not args.keep_images:
                shutil.rmtree(img_dir)
            props = all_props(dest / "fs")
            display_id = prop(props, "ro.build.display.id")
            vendor, platform = vendor_platform(display_id or fw_id)
            meta = {
                "id": fw_id,
                "vendor": vendor,
                "platform": platform,
                "android": prop(props, "ro.system.build.version.release", "ro.build.version.release"),
                "date": int(prop(props, "ro.build.date.utc", "ro.system.build.date.utc") or 0),
                "display_id": display_id,
                "signatures": signatures.result(),
            }
        write_manifest(dest / "fs", dest / "manifest.tsv")
        (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(f"  done: {meta['vendor']} {meta['platform']} android {meta['android']}")


def cmd_frontmatter(args) -> None:
    from datetime import datetime, timezone

    m = json.loads((WORK / args.id / "meta.json").read_text())
    date = datetime.fromtimestamp(m["date"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sig = m["signatures"]
    print(f'---\nid: "{m["id"]}"\nvendor: {m["vendor"]}\nplatform: {m["platform"]}\nandroid: {m["android"]}\ndate: {date}')
    print(f"signatures:\n  md5: {sig['md5']}\n  sha1: {sig['sha1']}\n  sha256: {sig['sha256']}\n---")


# --------------------------------------------------------------------------- diff


@dataclass
class Entry:
    kind: str
    size: int
    value: str  # sha256 for files, target for links


def load_manifest(fw_id: str) -> dict[str, Entry]:
    out = {}
    for line in (WORK / fw_id / "manifest.tsv").read_text().splitlines():
        path, kind, size, value = line.split("\t", 3)
        out[path] = Entry(kind, int(size), value)
    return out


def apk_info(path: Path) -> dict:
    from pyaxmlparser import APK

    try:
        apk = APK(str(path))
        return {"package": apk.package, "version_name": apk.version_name, "version_code": apk.version_code,
                "label": apk.application}
    except Exception as exc:  # noqa: BLE001 - a broken manifest shouldn't sink the whole report
        return {"package": "?", "error": str(exc)}


SIGNATURE_FILE = re.compile(r"META-INF/([^/]+\.(SF|RSA|EC|DSA)|MANIFEST\.MF)$")


def zip_entries(path: Path) -> dict[str, int] | None:
    try:
        with zipfile.ZipFile(path) as zf:
            return {i.filename: i.CRC for i in zf.infolist()}
    except zipfile.BadZipFile:
        return None


def classify_zip_change(a: Path, b: Path) -> list[str]:
    """Which parts of an APK/JAR really changed, ignoring the signature block. Empty means re-signed only."""
    ea, eb = zip_entries(a), zip_entries(b)
    if ea is None or eb is None:
        return ["unreadable zip"]
    changed = {n for n in ea.keys() | eb.keys() if ea.get(n) != eb.get(n) and not SIGNATURE_FILE.match(n)}
    kinds = set()
    for n in changed:
        if re.fullmatch(r"classes\d*\.dex", n):
            kinds.add("code")
        elif n == "AndroidManifest.xml":
            kinds.add("manifest")
        elif n == "resources.arsc" or n.startswith("res/"):
            kinds.add("resources")
        elif n.startswith("lib/"):
            kinds.add("native")
        elif n.startswith("assets/"):
            kinds.add("assets")
        else:
            kinds.add("other")
    return sorted(kinds)


def jadx(src: Path, out: Path) -> Path | None:
    """Decompile once per firmware and cache under WORK/<id>/src/. None if jadx crashed."""
    if (out / ".done").exists():
        return out
    shutil.rmtree(out, ignore_errors=True)
    env = {**os.environ, "JAVA_OPTS": os.environ.get("JAVA_OPTS", "-Xmx4g")}
    # --no-debug-info drops line numbers, which otherwise shift on every rebuild and bury real changes.
    res = subprocess.run([tool("jadx"), "-q", "--no-debug-info", "--comments-level", "none", "--threads-count", "2",
                          "-d", str(out), str(src)], env=env, capture_output=True, text=True, errors="replace")
    # jadx exits non-zero for every method it can't decompile, so the exit code alone means little.
    log = res.stdout + res.stderr
    if res.returncode < 0 or "OutOfMemoryError" in log or 'Exception in thread "main"' in log or not (
            (out / "sources").exists() or (out / "resources").exists()):
        shutil.rmtree(out, ignore_errors=True)
        return None
    (out / ".done").touch()
    return out


def slugify(name: str) -> str:
    return re.sub(r"[^\w.-]", "_", name)


def git_diff(a: Path, b: Path, *extra: str, roots: tuple[Path, Path] | None = None) -> str:
    """git diff --no-index with paths shown relative to `roots` (default: a and b themselves)."""
    res = subprocess.run(["git", "-c", "core.quotepath=off", "diff", "--no-index", "--no-color", "--no-ext-diff",
                          "--src-prefix=a/", "--dst-prefix=b/", "-M", *extra, str(a), str(b)],
                         capture_output=True, text=True, errors="replace")
    if res.returncode > 1:
        sys.exit(f"error: git diff failed: {res.stderr.strip()}")
    # --no-index prints absolute paths, and added/deleted files name the same side under both prefixes.
    text = res.stdout
    for root in roots or (a, b):
        for prefix in ("a", "b"):
            text = text.replace(f"{prefix}{root}/", f"{prefix}/")
        text = text.replace(f"{str(root).lstrip('/')}/", "")
    return text


# Code outside these namespaces (or the app's own package) is bundled libraries: androidx, Kotlin, Material...
VENDOR_NAMESPACES = ("com/szchoiceway", "com/zjinnova", "com/ksw", "com/wits", "com/ivicar", "com/txznet", "com/sykj")
MAX_FILE_DIFF_LINES = 1500
MAX_TIER_DIFF_LINES = 20000


def chunk_path(chunk: str) -> str:
    """The file a single-file diff chunk is about: the new path, or the old one for a deletion."""
    old = new = None
    for line in chunk.splitlines()[1:8]:
        line = line.rstrip("\t")
        if line.startswith("+++ "):
            new = None if line == "+++ /dev/null" else line[6:]
        elif line.startswith("--- "):
            old = None if line == "--- /dev/null" else line[6:]
        elif line.startswith(("rename to ", "copy to ")):
            new = line.split(" to ", 1)[1]
        elif line.startswith(("rename from ", "copy from ")):
            old = line.split(" from ", 1)[1]
        elif m := re.match(r"Binary files (?:a/(.*)|/dev/null) and (?:b/(.*)|/dev/null) differ", line):
            old, new = m[1], m[2]
    if new or old:
        return new or old
    rest = chunk.split("\n", 1)[0][len("diff --git a/"):]
    return rest[: (len(rest) - 3) // 2]  # "P b/P" when both sides share the path


def split_diff(text: str) -> list[tuple[str, str]]:
    """Cut a multi-file git diff into (path, chunk) pairs."""
    starts = [m.start() for m in re.finditer(r"^diff --git ", text, re.M)] + [len(text)]
    return [(chunk_path(text[s:e]), text[s:e]) for s, e in zip(starts, starts[1:])]


# values-de, values-pt-rBR, values-b+sr+Latn; not values-land, values-night, values-v21 or values-car (UI mode).
LOCALE_VALUES = re.compile(r"resources/res/values-(?!car[-/])([a-z]{2,3}(-r[A-Z]{2})?|b\+[\w+]+)[-/]")


def tier(path: str, own_prefixes: tuple[str, ...]) -> str:
    if SIGNATURE_FILE.search(path) or path.endswith(("/values/public.xml", "/R.java")):
        return "skip"
    if path.startswith("sources/"):
        return "code" if path[len("sources/"):].startswith(own_prefixes) else "libraries"
    if LOCALE_VALUES.match(path):
        return "translations"
    if path.startswith("resources/"):
        return "resources"
    return "other"


def write_app_diff(name: str, package: str | None, a_src: Path, b_src: Path, out: Path) -> str:
    """Write <slug>.code.diff / .resources.diff and return a one-paragraph summary for the report."""
    own = VENDOR_NAMESPACES + ((package.replace(".", "/"),) if package else ())
    # framework.jar / services.jar: every class is platform code the vendor may have patched.
    if name.endswith(".jar"):
        own = ("",)
    tiers: dict[str, list[str]] = {"code": [], "resources": []}
    counts: dict[str, int] = {}
    library_pkgs: dict[str, int] = {}
    oversized: list[str] = []
    for path, chunk in split_diff(git_diff(a_src, b_src)):
        t = tier(path, own)
        counts[t] = counts.get(t, 0) + 1
        if t == "libraries":
            pkg = ".".join(path.split("/")[1:-1][:3]) or "(default package)"
            library_pkgs[pkg] = library_pkgs.get(pkg, 0) + 1
        elif t in tiers:
            if "\nBinary files " in chunk:
                counts["binary"] = counts.get("binary", 0) + 1
            elif chunk.count("\n") > MAX_FILE_DIFF_LINES:
                oversized.append(path)
            else:
                tiers[t].append((path, chunk))
    slug = slugify(name)
    parts = []
    for t, chunks in tiers.items():
        if not chunks:
            continue
        n = sum(c.count("\n") for _, c in chunks)
        if n > MAX_TIER_DIFF_LINES:
            oversized += [p for p, c in chunks if c.count("\n") > 200]
            chunks = [(p, c) for p, c in chunks if c.count("\n") <= 200]
            parts.append(f"{t}: {len(tiers[t])} files, only hunks under 200 lines kept ({n} lines in full)")
        else:
            parts.append(f"{t}: {len(chunks)} files, {n} lines")
        (out / f"{slug}.{t}.diff").write_text("".join(c for _, c in chunks))
    for t in ("translations", "binary", "other"):
        if counts.get(t):
            parts.append(f"{t}: {counts[t]} files")
    if library_pkgs:
        top = sorted(library_pkgs.items(), key=lambda kv: -kv[1])[:6]
        parts.append("libraries: " + ", ".join(f"{k} ({v})" for k, v in top)
                     + (f" +{len(library_pkgs) - 6} more" if len(library_pkgs) > 6 else ""))
    if oversized:
        parts.append(f"not shown (binary or >{MAX_FILE_DIFF_LINES} lines): " + ", ".join(f"`{p}`" for p in oversized[:8])
                     + (f" +{len(oversized) - 8} more" if len(oversized) > 8 else ""))
    return "; ".join(parts) or "no source-level changes"


def cmd_diff(args) -> None:
    a_id, b_id = args.old, args.new
    fa, fb = WORK / a_id / "fs", WORK / b_id / "fs"
    ma, mb = load_manifest(a_id), load_manifest(b_id)
    out = WORK / "diffs" / f"{a_id}..{b_id}"
    shutil.rmtree(out, ignore_errors=True)
    (out / "apps").mkdir(parents=True)
    (out / "files").mkdir()

    added = sorted(p for p in mb.keys() - ma.keys() if not NOISE.search("/" + p))
    removed = sorted(p for p in ma.keys() - mb.keys() if not NOISE.search("/" + p))
    changed = sorted(p for p in ma.keys() & mb.keys() if ma[p].value != mb[p].value and not NOISE.search("/" + p))

    lines = [f"# {a_id} -> {b_id}", ""]

    # build.prop: noisy keys (dates, fingerprints) are kept because the version strings live there too.
    pa, pb = all_props(fa), all_props(fb)
    prop_lines = []
    for file in sorted(pa.keys() | pb.keys()):
        a, b = pa.get(file, {}), pb.get(file, {})
        for k in sorted(a.keys() | b.keys()):
            if a.get(k) != b.get(k) and not re.search(r"(^|\.)date(\.utc)?$|fingerprint|incremental|display\.id$|build\.id$|description$", k):
                prop_lines.append(f"- `{file}` `{k}`: `{a.get(k, '(none)')}` -> `{b.get(k, '(none)')}`")
    lines += ["## Build properties", "", *(prop_lines or ["- no changes besides build dates/fingerprints"]), ""]

    # Apps: inventory by package so a moved/renamed APK still pairs up.
    def apks(fs: Path, manifest: dict[str, Entry]) -> dict[str, tuple[str, dict]]:
        by_pkg: dict[str, list[tuple[str, dict]]] = {}
        for p in manifest:
            if p.endswith(".apk") and manifest[p].kind == "file":
                info = apk_info(fs / p)
                pkg = info.get("package")
                by_pkg.setdefault(pkg if pkg and pkg != "?" else p, []).append((p, info))
        # A package shipped at several paths (overlays, per-model variants) pairs up by path instead.
        return {k if len(v) == 1 else f"{k} ({p})": (p, info) for k, v in by_pkg.items() for p, info in v}

    print("reading app manifests")
    with cf.ThreadPoolExecutor(2) as pool:
        fa_apks, fb_apks = pool.map(apks, (fa, fb), (ma, mb))
    app_rows, to_decompile = [], []
    for pkg in sorted(fa_apks.keys() | fb_apks.keys()):
        a, b = fa_apks.get(pkg), fb_apks.get(pkg)
        if not a:
            app_rows.append(f"- **added** `{pkg}` {b[1].get('version_name')} (`{b[0]}`)")
            to_decompile.append((pkg, b[1].get("package"), None, b[0]))
        elif not b:
            app_rows.append(f"- **removed** `{pkg}` {a[1].get('version_name')} (`{a[0]}`)")
        elif ma[a[0]].value != mb[b[0]].value:
            kinds = classify_zip_change(fa / a[0], fb / b[0])
            if not kinds:
                continue  # re-signed only
            va, vb = a[1].get("version_name"), b[1].get("version_name")
            ver = f"{va} -> {vb}" if va != vb else f"{va} (version unchanged)"
            moved = f", moved from `{a[0]}`" if a[0] != b[0] else ""
            app_rows.append(f"- **changed** `{pkg}` {ver} [{', '.join(kinds)}] (`{b[0]}`{moved})")
            to_decompile.append((pkg, b[1].get("package"), a[0], b[0]))
    is_vendor = lambda row: any(f"`{ns.replace('/', '.')}" in row for ns in VENDOR_NAMESPACES)
    vendor_rows = [r for r in app_rows if is_vendor(r)]
    android_rows = [r for r in app_rows if not is_vendor(r)]
    lines += ["## Vendor apps", "", *(vendor_rows or ["- none"]), "",
              "## Android apps", "", *(android_rows or ["- none"]), ""]

    # JARs (framework, services): code changes only.
    jar_rows = []
    for p in changed:
        if p.endswith(".jar") and (kinds := classify_zip_change(fa / p, fb / p)):
            jar_rows.append(f"- `{p}` [{', '.join(kinds)}]")
            to_decompile.append((p, None, p, p))
    lines += ["## Framework and other JARs", "", *(jar_rows or ["- none"]), ""]

    # Plain files: text files are listed and diffed; binaries are only counted per folder.
    def is_text(p: str) -> bool:
        return Path(p).suffix in TEXT_SUFFIXES

    def by_folder(paths: list[str]) -> list[str]:
        folders: dict[str, int] = {}
        for p in paths:
            # Three levels deep: kernel module folders are named after the build hash, one level down.
            folder = "/".join(Path(p).parent.parts[:3])
            folders[folder] = folders.get(folder, 0) + 1
        return [f"- `{d}/`: {n}" for d, n in sorted(folders.items())]

    others = [p for p in changed if not p.endswith((".apk", ".jar"))]
    for title, paths in (("Added", added), ("Removed", removed), ("Changed", others)):
        text = [p for p in paths if is_text(p)]
        binary = [p for p in paths if not is_text(p)]
        if text:
            lines += [f"## {title} text files ({len(text)})", "", *[f"- `{p}`" for p in text], ""]
        if binary:
            lines += [f"## {title} binaries and other files ({len(binary)}, by folder)", "", *by_folder(binary), ""]

    roots = (fa, fb)
    text_diffs = [git_diff(fa / p, fb / p, roots=roots) for p in others if is_text(p) and ma[p].kind == mb[p].kind == "file"]
    text_diffs += [git_diff(Path(os.devnull), fb / p, roots=roots) for p in added if is_text(p) and mb[p].kind == "file"]
    (out / "files" / "text.diff").write_text("".join(text_diffs))

    # Decompile both sides of every app whose code/resources changed, then diff the sources.
    print(f"decompiling {len(to_decompile)} changed apps/jars")

    def decompile(item):
        name, package, pa_, pb_ = item
        b_src = jadx(fb / pb_, WORK / b_id / "src" / pb_)
        if pa_:
            a_src = jadx(fa / pa_, WORK / a_id / "src" / pa_)
        else:
            a_src = out / ".empty"
            a_src.mkdir(exist_ok=True)
        if a_src is None or b_src is None:
            return name, "**decompile failed** (jadx crashed or ran out of memory; try a larger JAVA_OPTS=-Xmx)"
        return name, write_app_diff(name, package, a_src, b_src, out / "apps")

    with cf.ThreadPoolExecutor(args.jobs) as pool:
        stats = list(pool.map(decompile, to_decompile))
    shutil.rmtree(out / ".empty", ignore_errors=True)
    lines += ["## Decompiled source diffs", "", "Full diffs in `apps/<name>.code.diff` and `apps/<name>.resources.diff`.", "",
              *[f"- `{n}`: {s}" for n, s in stats], ""]

    (out / "REPORT.md").write_text("\n".join(lines))
    print(f"report: {out / 'REPORT.md'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("extract")
    p.add_argument("zips", nargs="+")
    p.add_argument("--force", action="store_true")
    p.add_argument("--keep-images", action="store_true")
    p.set_defaults(func=cmd_extract)
    p = sub.add_parser("frontmatter")
    p.add_argument("id")
    p.set_defaults(func=cmd_frontmatter)
    p = sub.add_parser("diff")
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--jobs", type=int, default=3)
    p.set_defaults(func=cmd_diff)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
