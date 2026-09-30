#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["brotli==1.1.0", "pyaxmlparser==0.3.31"]
# ///
"""Unpack head-unit OTA zips and report what changed between two of them.

  fw.py extract <ota.zip>...            unpack into WORK/<id>/fs/<partition>/
  fw.py frontmatter <id>                print the YAML frontmatter for src/data/updates
  fw.py diff <old-id> <new-id>          write WORK/diffs/<old>..<new>/ (report + source diffs)
  fw.py score <old-id> <new-id>         how much of the hand-written changelog the report finds

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


def _uleb128(b: bytes, i: int) -> int:
    while b[i] & 0x80:
        i += 1
    return i + 1


def _read_uleb128(b: bytes, i: int) -> tuple[int, int]:
    value = shift = 0
    while True:
        byte = b[i]
        i += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return value, i


def _static_strings(b: bytes, i: int, found: set[int]) -> int:
    """Walk one encoded_array (a class's static field values), collecting string indices."""
    size, i = _read_uleb128(b, i)
    for _ in range(size):
        i = _encoded_value(b, i, found)
    return i


def _encoded_value(b: bytes, i: int, found: set[int]) -> int:
    header = b[i]
    kind, arg = header & 0x1F, header >> 5
    i += 1
    if kind == 0x17:  # VALUE_STRING
        found.add(int.from_bytes(b[i:i + arg + 1], "little"))
    if kind == 0x1C:  # VALUE_ARRAY
        return _static_strings(b, i, found)
    if kind == 0x1D:  # VALUE_ANNOTATION
        _, i = _read_uleb128(b, i)
        size, i = _read_uleb128(b, i)
        for _ in range(size):
            _, i = _read_uleb128(b, i)
            i = _encoded_value(b, i, found)
        return i
    if kind in (0x1E, 0x1F):  # null, boolean: no payload
        return i
    return i + arg + 1


def dex_literals(path: Path) -> set[str]:
    """String constants in an APK/JAR's dex files: every string that isn't a type, method, field or proto name.

    Read straight from the dex string table, so it still works where jadx fails to decompile a method.
    """
    import struct

    out: set[str] = set()
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return out
    with zf:
        for name in zf.namelist():
            if not re.fullmatch(r"classes\d*\.dex", name):
                continue
            b = zf.read(name)
            ssz, soff, tsz, toff, psz, poff, fsz, foff, msz, moff, csz, coff = struct.unpack_from("<12I", b, 0x38)
            names = {struct.unpack_from("<I", b, toff + 4 * k)[0] for k in range(tsz)}
            names |= {struct.unpack_from("<I", b, poff + 12 * k)[0] for k in range(psz)}
            names |= {struct.unpack_from("<I", b, foff + 8 * k + 4)[0] for k in range(fsz)}
            names |= {struct.unpack_from("<I", b, moff + 8 * k + 4)[0] for k in range(msz)}
            # `static final String KSW_X = "KSW_X"` shares one table entry between the field's name and
            # its value, which is how the vendor writes nearly every settings key: keep those.
            values: set[int] = set()
            for k in range(csz):
                source_file, _, _, static_values = struct.unpack_from("<4I", b, coff + 32 * k + 16)
                names.add(source_file)
                if static_values:
                    _static_strings(b, static_values, values)
            names -= values
            for k in range(ssz):
                if k not in names:
                    (data,) = struct.unpack_from("<I", b, soff + 4 * k)
                    start = _uleb128(b, data)
                    out.add(b[start:b.index(0, start)].decode("utf-8", "replace"))
    return out


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
    # --no-debug-info drops line numbers, which otherwise shift on every rebuild and bury real changes.
    # --show-bad-code keeps methods jadx can't fully decompile instead of replacing them with a stub.
    flags = ["--no-debug-info", "--show-bad-code", "--comments-level", "none"]
    done = out / ".done"
    if done.exists() and done.read_text() == " ".join(flags):
        return out
    shutil.rmtree(out, ignore_errors=True)
    env = {**os.environ, "JAVA_OPTS": os.environ.get("JAVA_OPTS", "-Xmx4g")}
    res = subprocess.run([tool("jadx"), "-q", *flags, "--threads-count", "2", "-d", str(out), str(src)],
                         env=env, capture_output=True, text=True, errors="replace")
    # jadx exits non-zero for every method it can't decompile, so the exit code alone means little.
    log = res.stdout + res.stderr
    if res.returncode < 0 or "OutOfMemoryError" in log or 'Exception in thread "main"' in log or not (
            (out / "sources").exists() or (out / "resources").exists()):
        shutil.rmtree(out, ignore_errors=True)
        return None
    done.write_text(" ".join(flags))
    return out


def mb_size(n: int) -> str:
    return f"{n / (1 << 20):.1f} MB"


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
        # jadx files some AOSP apps under their source root: sources/src/com/android/settings/...
        rel = path[len("sources/"):].removeprefix("src/")
        return "code" if rel.startswith(own_prefixes) else "libraries"
    if LOCALE_VALUES.match(path):
        return "translations"
    if path.startswith("resources/"):
        return "resources"
    return "other"


def write_app_diff(name: str, package: str | None, a_src: Path, b_src: Path, out: Path) -> str:
    """Write <slug>.code.diff / .resources.diff and return a one-paragraph summary for the report."""
    own = VENDOR_NAMESPACES + ((package.replace(".", "/"),) if package else ())
    # SystemUI carries com.android.wm.shell and com.android.keyguard, Launcher3 com.android.quickstep:
    # platform code the vendor patches, not libraries.
    if package and package.startswith(("com.android.", "android")):
        own += ("com/android/", "android/")
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
                # Core vendor files (EventService, EvtModel) are routinely this big: keep them, apart.
                big = out / slugify(name) / f"{slugify(path)}.diff"
                big.parent.mkdir(parents=True, exist_ok=True)
                big.write_text(chunk)
                oversized.append(f"{path}` -> `apps/{slugify(name)}/{big.name}")
            else:
                tiers[t].append((path, chunk))
    slug = slugify(name)
    parts = []
    for t, chunks in tiers.items():
        if not chunks:
            continue
        n = sum(c.count("\n") for _, c in chunks)
        if n > MAX_TIER_DIFF_LINES:
            # Keep the main file readable; the larger per-file hunks go next to it, not away.
            large = [(p, c) for p, c in chunks if c.count("\n") > 200]
            chunks = [(p, c) for p, c in chunks if c.count("\n") <= 200]
            (out / f"{slug}.{t}.large.diff").write_text("".join(c for _, c in large))
            parts.append(f"{t}: {len(tiers[t])} files, {n} lines; files over 200 lines in `{slug}.{t}.large.diff`")
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
        parts.append(f"large files diffed separately (>{MAX_FILE_DIFF_LINES} lines): " + ", ".join(f"`{p}`" for p in oversized[:12])
                     + (f" +{len(oversized) - 12} more" if len(oversized) > 12 else ""))
    return "; ".join(parts) or "no source-level changes"


# --------------------------------------------------------------------------- highlights
# Patterns that turned up in every hand-written and agent-written changelog so far. Each one is
# a plain regex over the diffs, so the section costs nothing to produce.

STRING_RE = re.compile(r'<string name="([^"]+)"[^>/]*>(.*?)</string>', re.S)
# Library strings that ride along with every androidx/Material bump.
LIBRARY_STRING = re.compile(r"^(abc_|mtrl_|material_|m3_|exo_|common_google|fab_|bottomsheet|bottom_sheet|side_sheet|appbar|"
                            r"androidx|call_notification|search_menu|status_bar_notification|character_counter|clear_text|"
                            r"error_icon|password_toggle|hide_bottom|icon_content|item_view_role|path_password|nav_app_bar|"
                            r"fallback_menu|mtrl|searchbar|searchview|default_error|copy_toast|project_id|gcm_|fcm_|"
                            r"google_|library_|srl_|brvah_|ucrop_|picture_)")
PROP_KEY = re.compile(r"^(persist|ro|sys|vendor|debug|service|ctl|init|cpuinfo|wifi|bluetooth|net|hw|dev|media|audio|"
                      r"camera|gsm|dalvik|log)\.[\w.]+$")
URL_REF = re.compile(r"^(https?|wss?|mqtt|tcp)://\S+$")
# KEYCODE_SYSRQ, android.intent.action.MEDIA_MOUNTED, com.wits.ksw.action.FOO
INTENT_OR_KEY = re.compile(r"^(KEYCODE_[A-Z0-9_]+|[a-z][\w.]*\.(action|intent)\.[A-Z0-9_]+)$")
SETTINGS_KEY = re.compile(r"^(KSW|ZXW|WITS|CAR|SAILOR|BENZ|BMW|AUDI|LEXUS|LANDROVER)[-_][A-Z0-9_-]+$")
THEME_NAME = re.compile(r"^UI_[A-Z0-9_]+$")  # KSW names themes as strings: UI_NTG6_FY_V3, UI_GS_ID8
# M785, SD685, rk3562_t, and device names such as "GT7PRO-CAR(QCOM 685)".
# ...and camera decoder / display chips such as XS9922B, PR2000.
MODEL_NAME = re.compile(r"^(M\d{3}|[Ss][DdMm]\d{3,4}\w*|GT\d[\w-]*|rk\d{4}\w*|[A-Z]{2,3}\d{4,5}[A-Z]?)([\s(-][^\n]{0,30})?$")
FILE_REF = re.compile(r"^(/(mnt|data|sdcard|storage|system|vendor|product|odm|oem|sys|proc|dev)/\S+|[\w.-]+\.(zip|ini|xml|txt|bin|json|cfg|conf|img|apk|ko|db))$")
# Other apps the vendor code now names: com.ucloudlink.cloudsim, ru.yandex.yandexnavi.
PACKAGE_REF = re.compile(r"^(?!(android|java|javax|kotlin|kotlinx|androidx|dalvik|sun|org\.(json|xml|w3c))\.)"
                         r"[a-z][a-z0-9_]*(\.[a-z0-9_]+){2,}$")
MANIFEST_FLAG = re.compile(r'android:(testOnly|persistent|sharedUserId|directBootAware|debuggable|largeHeap|'
                           r'resizeableActivity|requestLegacyExternalStorage)="([^"]*)"')
SCREEN_TYPE = re.compile(r"^\d{3,4}x\d{3,4}(_\w+)?$")
MEDIA_EXT = re.compile(r"^(\.[a-z0-9]{2,4}){3,}\.?$")  # ".mp3.wma.flac." style extension lists
THEME_CONST = re.compile(r"\b(UI_NUM_\w+|UI_\w+_ID\w*)\s*=\s*(\d+);")
MANIFEST_ITEM = re.compile(r'<(uses-permission|activity|service|receiver|provider|action)\b[^>]*?android:name="([^"]+)"')
CONFIG_VALUE = re.compile(r'<(bool|integer|string|dimen|integer-array|string-array) name="(config_\w+)"[^>]*>(.*?)</\1>', re.S)
XML_LEAF = re.compile(r"<(\w+)>([^<>]*)</\1>")


def read_strings(src: Path) -> dict[str, str]:
    f = src / "resources/res/values/strings.xml"
    if not f.is_file():
        return {}
    return {k: re.sub(r"\s+", " ", v).strip() for k, v in STRING_RE.findall(f.read_text(errors="replace"))
            if not LIBRARY_STRING.match(k)}


def fmt_list(items, limit: int = 30) -> str:
    items = sorted(items)
    shown = ", ".join(f"`{i}`" for i in items[:limit])
    return shown + (f" +{len(items) - limit} more" if len(items) > limit else "")


CONFIG_KEY = re.compile(r"^[a-z][a-z0-9]*[A-Z][A-Za-z0-9]*$")  # camelCase: factory XML tags such as externalMicOutput


def collect_highlights(out: Path, pa: dict, pb: dict, fa: Path, fb: Path, apps: list[tuple[str, tuple[Path, Path]]],
                       lits: list[tuple[str, str | None, set[str], set[str]]], added_files: list[str],
                       removed_files: list[str]) -> list[str]:
    rows: list[str] = []
    facts: dict = {}

    # Build identity: the type/user flip (userdebug -> user, ubuntu -> jenkins) matters to readers.
    for key in ("ro.build.display.id", "ro.build.type", "ro.build.user", "ro.build.version.security_patch",
                "ro.build.version.sdk"):
        va, vb = prop(pa, key), prop(pb, key)
        if va != vb:
            rows.append(f"- Build `{key}`: `{va}` -> `{vb}`")
        elif key in ("ro.build.type", "ro.build.user") and vb:
            rows.append(f"- Build `{key}` still `{vb}`")


    # Theme ids from the whole decompiled trees, not the diff: shared code copying a constant into
    # one more app would otherwise look like a new theme.
    def theme_consts(trees: list[Path]) -> set[str]:
        found = set()
        for tree in trees:
            res = subprocess.run(["grep", "-rhoE", r"UI_[A-Za-z0-9_]+ = [0-9]+;", str(tree / "sources")],
                                 capture_output=True, text=True, errors="replace")
            found |= {f"{m[1]} = {m[2]}" for m in THEME_CONST.finditer(res.stdout)}
        return found

    new_themes = theme_consts([b for _, (_, b) in apps]) - theme_consts([a for _, (a, _) in apps])
    if new_themes:
        rows.append(f"- Theme ids added: {fmt_list(new_themes)}")
        facts["themes"] = sorted(new_themes)

    # String constants straight from the dex files, compared across all changed apps at once so a
    # shared library moving a key from one app to another doesn't count as a change.
    old_all = {x for *_, la, _ in lits for x in la}
    new_all = {x for *_, _, lb in lits for x in lb}
    added_lits, removed_lits = new_all - old_all, old_all - new_all
    # Factory XML tags: new strings in the apps that name factory_config.xml, which new code also
    # compares a tag name against (`name.equals("externalMicOutput")`). Either signal alone is noisy.
    readers = [(la, lb) for *_, la, lb in lits if any(x.endswith("factory_config.xml") for x in lb)]
    config_added = {x for _, lb in readers for x in lb} - {x for la, _ in readers for x in la}
    compared_re = re.compile(r'\.equals\("(\w+)"\)|\bcase "(\w+)":')
    compared = {a or b for f in (out / "apps").glob("*.code.diff") for line in f.read_text(errors="replace").splitlines()
                if line.startswith("+") for a, b in compared_re.findall(line)}
    config_added &= compared
    for label, pattern, key, pool_add, pool_rem in (
            ("System properties", PROP_KEY, "props", added_lits, removed_lits),
            ("Settings keys", SETTINGS_KEY, "settings_keys", added_lits, removed_lits),
            ("Theme names", THEME_NAME, "theme_names", added_lits, removed_lits),
            ("Platform/model names", MODEL_NAME, "models", added_lits, removed_lits),
            ("File paths and names", FILE_REF, "files", added_lits, removed_lits),
            ("Other apps' package names", PACKAGE_REF, "packages", {x for x in added_lits if not PROP_KEY.match(x)},
             {x for x in removed_lits if not PROP_KEY.match(x)}),
            ("Intent actions and key codes", INTENT_OR_KEY, "intents", added_lits, removed_lits),
            ("URLs", URL_REF, "urls", added_lits, removed_lits),

            ("Factory config keys", CONFIG_KEY, "config_keys", config_added, set()),
            ("Screen types", SCREEN_TYPE, "screens", added_lits, removed_lits)):
        add = {x for x in pool_add if pattern.match(x)}
        rem = {x for x in pool_rem if pattern.match(x)}
        if add:
            rows.append(f"- {label} added: {fmt_list(add, 60)}")
        if rem:
            rows.append(f"- {label} removed: {fmt_list(rem, 60)}")
        facts[key] = {"added": sorted(add), "removed": sorted(rem)}
    # Native libraries bundled into apps: new codecs, SDKs, app packers (libshella = a packed app).
    # Skipped when the old APK next to it already carried the same library (now just shipped unpacked).
    def packed_before(so: str) -> bool:
        app_dir = (fa / so).parent
        while app_dir != fa and not any(app_dir.glob("*.apk")):
            app_dir = app_dir.parent
        names = {n for apk in app_dir.glob("*.apk") for n in (zip_entries(apk) or {})}
        return any(n.endswith("/" + Path(so).name) for n in names)

    libs = sorted({Path(p).name for p in added_files
                   if p.endswith(".so") and re.search(r"/(priv-app|app|PreInstall)/", p) and not packed_before(p)})
    if libs:
        rows.append(f"- Native libraries added to apps: {fmt_list(libs)}")

    # Executables are few and every one matters (su -> ksu); the rest of the binaries stay counted per folder.
    exe = re.compile(r"/(s?bin|xbin)/[^/]+$")
    exe_added = sorted(p for p in added_files if exe.search(p))
    exe_removed = sorted(p for p in removed_files if exe.search(p))
    if exe_added:
        rows.append(f"- Executables added: {fmt_list(exe_added)}")
    if exe_removed:
        rows.append(f"- Executables removed: {fmt_list(exe_removed)}")

    # Framework/services starting to read a property the vendor apps already used is still news:
    # Android itself now honours it.
    for name, _, la, lb in lits:
        if name.endswith(".jar"):
            newly = {x for x in lb - la if PROP_KEY.match(x)} - added_lits
            if newly:
                rows.append(f"- System properties now read by `{name}`: {fmt_list(newly)}")

    def extensions(pool: set[str]) -> set[str]:
        return {e for x in pool if MEDIA_EXT.match(x) for e in x.strip(".").split(".")}

    new_ext = {e for *_, la, lb in lits for e in extensions(lb) - extensions(la)}
    if new_ext:
        rows.append(f"- File extensions added to media lists: {fmt_list('.' + e for e in new_ext)}")

    # UI strings per app, from the full decompiled trees: a label moved between lines isn't "new".
    by_text: dict[tuple[str, str], list[str]] = {}
    renamed: list[str] = []
    for name, (a_src, b_src) in apps:
        sa, sb = read_strings(a_src), read_strings(b_src)
        for k in sb.keys() - sa.keys():
            by_text.setdefault((k, sb[k]), []).append(name)
        for k in sb.keys() & sa.keys():
            if sa[k] != sb[k] and sa[k] and sb[k]:
                renamed.append(f'  - `{name}` `{k}`: "{sa[k]}" -> "{sb[k]}"')
    if by_text:
        rows.append(f"- New UI strings ({len(by_text)}):")
        for (k, v), names in sorted(by_text.items(), key=lambda kv: (kv[1][0], kv[0][0]))[:600]:
            where = names[0] if len(names) == 1 else f"{names[0]} +{len(names) - 1} apps"
            rows.append(f'  - "{v[:120]}" (`{k}`, {where})')
        if len(by_text) > 600:
            rows.append(f"  - ... {len(by_text) - 600} more, all in facts.json")
    if renamed:
        rows.append(f"- Changed UI strings ({len(renamed)}):")
        rows += renamed[:60]
    facts["strings"] = [{"name": k, "text": v, "apps": n} for (k, v), n in by_text.items()]

    # Resource folders an app didn't have before: layout-1024x592 means a new screen size is handled.
    new_dirs = []
    for name, (a_src, b_src) in apps:
        old = {d.name for d in (a_src / "resources/res").glob("*") if d.is_dir()}
        new = {d.name for d in (b_src / "resources/res").glob("*") if d.is_dir()}
        added_dirs = {d for d in new - old if not LOCALE_VALUES.match(f"resources/res/{d}/")}
        if added_dirs and old:
            new_dirs.append(f"  - `{name}`: {fmt_list(added_dirs, 15)}")
    if new_dirs:
        rows += ["- New resource folders (screen sizes, orientations, themes):", *new_dirs]

    # New layouts name new screens: kesaiwei_id6_activity_main, layout_bmw_hw_screen_reverse.
    new_layouts = []
    for name, (a_src, b_src) in apps:
        def layouts(src: Path) -> set[str]:
            return {f.stem for f in (src / "resources/res").glob("layout*/*.xml")}
        added_layouts = layouts(b_src) - layouts(a_src)
        if added_layouts and layouts(a_src):
            new_layouts.append(f"  - `{name}` ({len(added_layouts)}): {fmt_list(added_layouts, 12)}")
    if new_layouts:
        rows += ["- New layouts:", *new_layouts]

    # Manifests and config values from the whole files: jadx puts each attribute on its own line,
    # so an element rarely fits in one diff line.
    def read(path: Path) -> str:
        return path.read_text(errors="replace") if path.is_file() else ""

    items_added, items_removed, flag_rows, cfg_rows = set(), set(), [], []
    for name, (a_src, b_src) in apps:
        ma_, mb_ = read(a_src / "resources/AndroidManifest.xml"), read(b_src / "resources/AndroidManifest.xml")
        ia, ib = {m[1] for m in MANIFEST_ITEM.findall(ma_)}, {m[1] for m in MANIFEST_ITEM.findall(mb_)}
        items_added |= ib - ia
        items_removed |= (ia - ib) if mb_ else set()
        fa_, fb_ = {f"{k}={v}" for k, v in MANIFEST_FLAG.findall(ma_)}, {f"{k}={v}" for k, v in MANIFEST_FLAG.findall(mb_)}
        if ma_ and fa_ != fb_:
            flag_rows.append(f"  - `{name}`: added {fmt_list(fb_ - fa_)}; removed {fmt_list(fa_ - fb_)}")

        def configs(src: Path) -> dict[str, str]:
            return {k: re.sub(r"\s+", " ", v).strip() for f in sorted((src / "resources/res/values").glob("*.xml"))
                    for _, k, v in CONFIG_VALUE.findall(read(f))}
        ca, cb = configs(a_src), configs(b_src)
        for k in sorted(cb):
            if ca and ca.get(k) != cb[k]:
                cfg_rows.append(f"- Android `{k}` (`{name}`): `{ca.get(k, '(unset)')}` -> `{cb[k]}`")
    if flag_rows:
        rows += ["- Manifest flags changed:", *flag_rows]
    if items_added:
        rows.append(f"- Manifest entries added (permissions, activities, services): {fmt_list(items_added, 40)}")
    if items_removed:
        rows.append(f"- Manifest entries removed: {fmt_list(items_removed, 40)}")
    rows += cfg_rows

    # key=value config files (Wi-Fi driver .ini, .conf, .prop): which keys changed.
    kv_rows = []
    for path, chunk in split_diff((out / "files" / "text.diff").read_text(errors="replace")):
        if not path.endswith((".ini", ".conf", ".cfg", ".prop", ".properties")):
            continue
        kv = re.compile(r"^([+-])\s*([\w.]+)\s*=\s*(.*?)\s*$")
        old, new = {}, {}
        for line in chunk.splitlines()[4:]:
            if m := kv.match(line):
                (new if m[1] == "+" else old)[m[2]] = m[3]
        changes = [f"`{k}` {old.get(k, '(unset)')} -> {new.get(k, '(removed)')}" for k in sorted(old.keys() | new.keys())
                   if old.get(k) != new.get(k)]
        if changes:
            kv_rows.append(f"  - `{path}`: " + ", ".join(changes[:20]) + (f" +{len(changes) - 20} more" if len(changes) > 20 else ""))
    if kv_rows:
        rows += ["- Config file settings changed:", *kv_rows]

    # Factory settings: leaf elements of the vendor's config XML (zxw_factory_config.xml and the like).
    for rel in sorted({p.relative_to(fb).as_posix() for p in fb.glob("*/**/*factory_config*.xml")}):
        a_file, b_file = fa / rel, fb / rel
        old = dict(XML_LEAF.findall(a_file.read_text(errors="replace"))) if a_file.is_file() else {}
        new = dict(XML_LEAF.findall(b_file.read_text(errors="replace")))
        added = {k for k in new.keys() - old.keys()}
        if added:
            rows.append(f"- Factory settings added in `{rel}`: {fmt_list(f'<{k}>' for k in added)}")
        if old.keys() - new.keys():
            rows.append(f"- Factory settings removed in `{rel}`: {fmt_list(f'<{k}>' for k in old.keys() - new.keys())}")
        for k in sorted(old.keys() & new.keys()):
            if old[k] != new[k]:
                rows.append(f"- Factory default `<{k}>` in `{rel}`: `{old[k]}` -> `{new[k]}`")

    (out / "facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
    return rows


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
            size = f", {mb_size(ma[a[0]].size)} -> {mb_size(mb[b[0]].size)}" if abs(ma[a[0]].size - mb[b[0]].size) > 1 << 20 else ""
            app_rows.append(f"- **changed** `{pkg}` {ver} [{', '.join(kinds)}] (`{b[0]}`{moved}{size})")
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
        la = dex_literals(fa / pa_) if pa_ else set()
        lb = dex_literals(fb / pb_)
        lits = (name, package, la, lb)
        if a_src is None or b_src is None:
            return name, "**decompile failed** (jadx crashed or ran out of memory; try a larger JAVA_OPTS=-Xmx)", None, lits
        return name, write_app_diff(name, package, a_src, b_src, out / "apps"), (a_src, b_src), lits

    with cf.ThreadPoolExecutor(args.jobs) as pool:
        stats = list(pool.map(decompile, to_decompile))
    lines += ["## Decompiled source diffs", "", "Full diffs in `apps/<name>.code.diff` and `apps/<name>.resources.diff`.", "",
              *[f"- `{n}`: {s}" for n, s, _, _ in stats], ""]

    highlights = collect_highlights(out, pa, pb, fa, fb, [(n, srcs) for n, _, srcs, _ in stats if srcs],
                                    [lits for *_, lits in stats], added, removed)
    shutil.rmtree(out / ".empty", ignore_errors=True)
    lines[2:2] = ["## Highlights", "", *(highlights or ["- nothing matched the known patterns"]), ""]
    (out / "REPORT.md").write_text("\n".join(lines))
    print(f"report: {out / 'REPORT.md'}")


def changelog_terms(md: str) -> list[str]:
    """The checkable bits of a hand-written changelog: `identifiers`, "labels" and version numbers."""
    body = md.split("---", 2)[-1]
    body = re.sub(r"\]\([^)]*\)", "]", body)  # drop link targets
    terms = []
    for t in re.findall(r"`([^`\n]+)`", body):
        t = re.split(r"\[?…|\[\.\.\.", t)[0]  # `GT7-EAU-T16.000500-[…]`: keep the known prefix
        t = t.strip().strip("<>/-")
        if re.search(r'[\s="<>]', t):
            # A pasted snippet such as <Item id="1" name="UI_NTG6_FY_V3" ... />: check its identifier.
            idents = [w for w in re.findall(r"[\w.]+", t) if len(w) >= 5 and re.search(r"[_\d]|[a-z][A-Z]", w)]
            t = max(idents, key=len) if idents else ""
        terms.append(t)
    # Quoted labels: backtick spans with quotes inside (`id="41"`) would pair up quotes across spans, so
    # those go; others keep their text, since a label can contain code ("Put it in the `OEM` folder").
    unticked = re.sub(r"`([^`\n]+)`", lambda m: "" if '"' in m[1] else m[1], body)
    terms += re.findall(r'"([^"\n]{3,80})"', unticked)
    terms += re.findall(r"\b\d+\.\d+(?:\.\d+)+\b", body)
    seen, out = set(), []
    for t in terms:
        # Two- or three-letter terms and bare numbers ("40", "KSW") match anything, the title included.
        if len(t) >= 4 and not t.isdigit() and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


def cmd_score(args) -> None:
    """How much of a hand-written changelog the report finds, with no model involved."""
    out = WORK / "diffs" / f"{args.old}..{args.new}"
    changelog = Path(args.changelog) if args.changelog else next(
        Path(__file__).resolve().parents[2].glob(f"src/data/updates/*/*/{args.new}.md"), None)
    if not changelog or not changelog.is_file():
        sys.exit(f"error: no changelog found for {args.new}; pass one with --changelog")
    report = (out / "REPORT.md").read_text(errors="replace").lower()
    evidence = report + "".join(f.read_text(errors="replace").lower() for f in out.rglob("*.diff"))
    terms = changelog_terms(changelog.read_text())
    in_report = [t for t in terms if t.lower() in report]
    rest = [t for t in terms if t.lower() not in report]
    # Terms a bullet mentions for comparison (an older theme, an existing vendor id) exist in the old
    # firmware already; they aren't changes, so they don't count against the report.
    old_literals: set[str] = set()
    if rest:
        ma = load_manifest(args.old)
        for p in ma:
            if p.endswith((".apk", ".jar")) and ma[p].kind == "file":
                old_literals |= {x.lower() for x in dex_literals(WORK / args.old / "fs" / p)}
    in_diffs = [t for t in rest if t.lower() in evidence]

    def in_old_sources(term: str) -> bool:
        # Constant names such as UI_NUM_KSW_BENZ_NTG7 aren't dex literals; the old decompiled code has them.
        src = WORK / args.old / "src"
        return src.is_dir() and subprocess.run(["grep", "-rqiF", term, str(src)]).returncode == 0

    # Anything the old firmware already had is context: the score is about new identifiers.
    context = [t for t in rest if t.lower() in old_literals or in_old_sources(t)]
    in_diffs = [t for t in in_diffs if t not in context]
    missing = [t for t in rest if t not in context and t not in in_diffs]
    n = (len(terms) - len(context)) or 1
    print(f"{args.old} -> {args.new}: {len(terms)} terms in {changelog.name}")
    print(f"  in report:        {len(in_report):3} ({100 * len(in_report) // n}% of {n} change terms)")
    print(f"  only in diffs:    {len(in_diffs):3}  {', '.join(in_diffs)}")
    print(f"  context (in old): {len(context):3}  {', '.join(context)}")
    print(f"  not found at all: {len(missing):3}  {', '.join(missing)}")


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
    p = sub.add_parser("score", help="check a hand-written changelog against a diff report")
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--changelog", help="defaults to src/data/updates/*/*/<new>.md")
    p.set_defaults(func=cmd_score)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
