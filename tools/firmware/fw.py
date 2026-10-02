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
  fw.py batch <zip-folder>...           diff every zip against its predecessor; write WORK/diffs/INDEX.md

WORK defaults to ~/Dev/firmwares/_work and can be changed with FW_WORK.
Nothing here needs root, FUSE or a mounted filesystem: ext4 images are read by
e2fsprogs' debugfs, EROFS images by erofs-utils' fsck.erofs.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import functools
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile
from dataclasses import dataclass
from pathlib import Path

import formats
import images
import vendors

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
        if "super.img" in names:
            found = True
            zf.extract("super.img", img_dir)
        if not found:
            sys.exit(f"error: {zip_path.name} has no payload.bin, *.new.dat(.br), super.img or *.img partitions")


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
    # Anchored on the vendors' own id shapes, so another maker's "-m100" or "GT5x" is not taken for them.
    if m := re.match(r"GT(\d)-", display_id):
        return "zxw", f"gt{m[1]}"
    if m := re.match(r"(?:Ksw|Witstek)-[A-Z]-(M\d{3})_OS", display_id):
        return "ksw", m[1].lower()
    if re.match(r"(?:Ksw|Witstek)-Q-Userdebug_OS", display_id):
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
        if extracted(fw_id) and not args.force:
            print(f"{fw_id}: already extracted, skipping (use --force to redo)")
            continue
        extract(zip_path, args.keep_images)


def extract(zip_path: Path, keep_images: bool = False) -> None:
    """Unpack one zip into WORK/<id>/, replacing whatever is there. meta.json is written last."""
    fw_id = zip_path.name.removesuffix(".zip")
    dest = WORK / fw_id
    print(f"{fw_id}: extracting")
    shutil.rmtree(dest, ignore_errors=True)
    img_dir = dest / "img"
    img_dir.mkdir(parents=True)
    with cf.ThreadPoolExecutor(1) as pool:
        signatures = pool.submit(hash_file, zip_path)
        images_from_zip(zip_path, img_dir)
        formats.normalise(img_dir, FS_PARTITIONS)
        images.extract(zip_path, img_dir / "raw", FS_PARTITIONS, functools.partial(tool, "payload-dumper-go"))
        images.write(img_dir / "raw", dest)
        for img in sorted(img_dir.glob("*.img")):
            print(f"  unpacking {img.stem}")
            unpack_image(img, dest / "fs" / img.stem)
        if not keep_images:
            shutil.rmtree(img_dir)
        props = all_props(dest / "fs")
        display_id = prop(props, "ro.build.display.id")
        vendor, platform = vendor_platform(display_id or fw_id)
        namespaces = None
        if not vendor:
            apps, platform_cert = vendors.scan(dest / "fs", apk_info, signing_cert)
            get = functools.partial(prop, props)
            namespaces = vendors.vendor_namespaces(apps, platform_cert, get, fw_id, THIRD_PARTY_PACKAGES)
            vendor, platform = vendors.identity(get, namespaces)
        meta = {
            "id": fw_id,
            "vendor": vendor,
            "platform": platform,
            "android": prop(props, "ro.system.build.version.release", "ro.build.version.release"),
            "date": int(prop(props, "ro.build.date.utc", "ro.system.build.date.utc") or 0),
            "display_id": display_id,
            "signatures": signatures.result(),
        }
        if namespaces is not None:
            meta["vendor_namespaces"] = namespaces
    write_manifest(dest / "fs", dest / "manifest.tsv")
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"  done: {meta['vendor']} {meta['platform']} android {meta['android']}")


def cmd_frontmatter(args) -> None:
    print(frontmatter(args.id), end="")


def frontmatter(fw_id: str) -> str:
    m = json.loads((WORK / fw_id / "meta.json").read_text())
    sig = m["signatures"]
    return (f'---\nid: "{m["id"]}"\nvendor: {m["vendor"]}\nplatform: {m["platform"]}\nandroid: {m["android"]}\n'
            f"date: {utc(m['date'])}\nsignatures:\n  md5: {sig['md5']}\n  sha1: {sig['sha1']}\n  sha256: {sig['sha256']}\n---\n")


def utc(ts: int) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


# Bundled libraries, as dex class descriptor prefixes. A string literal that only these classes use is
# the library's (blankj's list of ROM version properties, okhttp's URLs), not the vendor's.
LIBRARY_PACKAGES = (
    "android/support/", "androidx/", "kotlin/", "kotlinx/", "javax/", "org/apache/", "org/json/", "org/xmlpull/",
    "org/intellij/", "org/jetbrains/", "com/google/", "com/android/volley/", "okhttp3/", "okio/", "retrofit2/",
    "com/squareup/", "io/reactivex/", "rx/", "com/blankj/", "com/tencent/", "com/umeng/", "com/alibaba/",
    "com/bumptech/glide/", "org/greenrobot/", "de/greenrobot/", "com/airbnb/lottie/", "com/facebook/",
    "com/jakewharton/", "butterknife/", "dagger/", "com/github/", "com/chad/library/", "com/scwang/",
    "com/orhanobut/", "com/nostra13/", "com/lzy/", "com/liulishuo/", "com/yalantis/", "com/luck/", "com/hjq/",
    "com/zhy/", "com/danikula/", "tv/danmaku/ijk/", "com/shuyu/", "org/videolan/", "io/netty/", "org/eclipse/",
    "org/jsoup/", "org/litepal/", "net/sqlcipher/", "com/j256/ormlite/", "cn/jpush/", "cn/jiguang/",
    "com/baidu/", "com/amap/", "com/autonavi/", "com/iflytek/", "com/xiaomi/push/", "me/jessyan/",
)

# Code units per Dalvik opcode (1 unless listed), to walk a method's instructions.
_WIDTH = bytearray([1] * 256)
for _ops, _w in (([0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1A, 0x1C, 0x1F, 0x20, 0x22, 0x23, 0x29, 0xFE, 0xFF,
                   *range(0x2D, 0x3E), *range(0x44, 0x6E), *range(0x90, 0xB0), *range(0xD0, 0xE3)], 2),
                 ([0x03, 0x06, 0x09, 0x14, 0x17, 0x1B, 0x24, 0x25, 0x26, 0x2A, 0x2B, 0x2C, 0xFC, 0xFD,
                   *range(0x6E, 0x73), *range(0x74, 0x79)], 3),
                 ([0xFA, 0xFB], 4), ([0x18], 5)):
    for _op in _ops:
        _WIDTH[_op] = _w


def _code_strings(b: bytes, off: int, found: set[int]) -> None:
    """String indices a code_item loads with const-string or const-string/jumbo."""
    import struct

    (units,) = struct.unpack_from("<I", b, off + 12)
    i, end = off + 16, off + 16 + 2 * units
    while i < end:
        op = b[i]
        if op == 0x1A:
            found.add(b[i + 2] | b[i + 3] << 8)
        elif op == 0x1B:
            found.add(struct.unpack_from("<I", b, i + 2)[0])
        elif op == 0 and b[i + 1] in (1, 2, 3):  # switch and array-data payloads sit inline in the code
            size = struct.unpack_from("<H", b, i + 2)[0]
            if b[i + 1] == 1:
                i += (size * 2 + 4) * 2
            elif b[i + 1] == 2:
                i += (size * 4 + 2) * 2
            else:
                i += ((struct.unpack_from("<I", b, i + 4)[0] * size + 1) // 2 + 4) * 2
            continue
        i += _WIDTH[op] * 2


def _dex_strings(b: bytes, libraries: bool) -> set[str]:
    import struct

    ssz, soff, tsz, toff, psz, poff, fsz, foff, msz, moff, csz, coff = struct.unpack_from("<12I", b, 0x38)

    def string(k: int) -> str:
        start = _uleb128(b, struct.unpack_from("<I", b, soff + 4 * k)[0])
        return b[start:b.index(0, start)].decode("utf-8", "replace")

    types = [struct.unpack_from("<I", b, toff + 4 * k)[0] for k in range(tsz)]
    names = set(types)
    names |= {struct.unpack_from("<I", b, poff + 12 * k)[0] for k in range(psz)}
    names |= {struct.unpack_from("<I", b, foff + 8 * k + 4)[0] for k in range(fsz)}
    names |= {struct.unpack_from("<I", b, moff + 8 * k + 4)[0] for k in range(msz)}
    # `static final String KSW_X = "KSW_X"` shares one table entry between the field's name and
    # its value, which is how the vendor writes nearly every settings key: keep those.
    values: set[int] = set()
    own: set[int] = set()
    lib: set[int] = set()
    for k in range(csz):
        class_idx, _, _, _, source_file, _, class_data, static_values = struct.unpack_from("<8I", b, coff + 32 * k)
        names.add(source_file)
        refs = lib if string(types[class_idx])[1:].startswith(LIBRARY_PACKAGES) else own
        if static_values:
            found: set[int] = set()
            _static_strings(b, static_values, found)
            values |= found
            refs |= found
        if class_data and not libraries:
            i = class_data
            counts = []
            for _ in range(4):
                n, i = _read_uleb128(b, i)
                counts.append(n)
            for _ in range(counts[0] + counts[1]):
                i = _uleb128(b, _uleb128(b, i))
            for _ in range(counts[2] + counts[3]):
                i = _uleb128(b, _uleb128(b, i))
                code, i = _read_uleb128(b, i)
                if code:
                    _code_strings(b, code, refs)
    keep = set(range(ssz)) - (names - values)
    if not libraries:
        keep -= lib - own
    return {string(k) for k in keep}


def dex_literals(path: Path, libraries: bool = False) -> set[str]:
    """String constants in an APK/JAR's dex files: every string that isn't a type, method, field or proto name.
    Unless `libraries`, strings that only LIBRARY_PACKAGES classes load (in code or static field values) are
    left out.

    Read straight from the dex, so it still works where jadx fails to decompile a method.
    """
    import struct

    out: set[str] = set()
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return out
    with zf:
        for name in sorted(zf.namelist()):
            if not re.fullmatch(r"classes\d*\.dex", name):
                continue
            try:
                out |= _dex_strings(zf.read(name), libraries)
            except (struct.error, IndexError, ValueError):
                print(f"warning: {path.name} {name} is not a dex fw.py can read; its strings are left out", file=sys.stderr)
    return out


def _der(b: bytes, i: int) -> tuple[int, int, int]:
    """One DER element at i: (tag, content start, content end)."""
    tag, n, i = b[i], b[i + 1], i + 2
    if n & 0x80:
        k = n & 0x7F
        n, i = int.from_bytes(b[i:i + k], "big"), i + k
    return tag, i, i + n


def signing_cert(path: Path) -> str | None:
    """sha256 of an APK's first signing certificate, from the v2/v3 signing block or else the v1 PKCS#7."""
    import struct

    try:
        with path.open("rb") as fh:
            size = fh.seek(0, 2)
            fh.seek(max(0, size - 65558))
            tail = fh.read()
            eocd = tail.rfind(b"PK\x05\x06")
            cd = struct.unpack_from("<I", tail, eocd + 16)[0] if eocd >= 0 else 0
            fh.seek(max(0, cd - 24))
            head = fh.read(24)
            if cd >= 32 and head[8:] == b"APK Sig Block 42":
                block_size = struct.unpack_from("<Q", head)[0]
                fh.seek(cd - block_size - 8 + 8)
                pairs, i = fh.read(block_size - 24), 0
                while i + 12 <= len(pairs):
                    n, pid = struct.unpack_from("<QI", pairs, i)
                    if pid in (0x7109871A, 0xF05368C0):  # v2, v3
                        def lp(b: bytes, j: int) -> tuple[bytes, int]:
                            k = struct.unpack_from("<I", b, j)[0]
                            return b[j + 4:j + 4 + k], j + 4 + k
                        signed = lp(lp(lp(pairs[i + 12:i + 8 + n], 0)[0], 0)[0], 0)[0]
                        _, j = lp(signed, 0)  # digests
                        return hashlib.sha256(lp(lp(signed, j)[0], 0)[0]).hexdigest()
                    i += 8 + n
        with zipfile.ZipFile(path) as zf:
            sig = next((n for n in sorted(zf.namelist()) if re.fullmatch(r"META-INF/[^/]+\.(RSA|DSA|EC)", n)), None)
            if not sig:
                return None
            b = zf.read(sig)
        # ContentInfo { oid, [0] { SignedData { version, digestAlgorithms, contentInfo, [0] certificates ... } } }
        _, i, _ = _der(b, 0)
        _, i, _ = _der(b, _der(b, i)[2])
        _, i, end = _der(b, i)
        while i < end:
            tag, start, stop = _der(b, i)
            if tag == 0xA0:
                return hashlib.sha256(b[start:_der(b, start)[2]]).hexdigest()
            i = stop
    except (OSError, ValueError, zipfile.BadZipFile, struct.error, IndexError):
        pass
    return None


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


_jadx_locks: dict[Path, threading.Lock] = {}
_jadx_locks_guard = threading.Lock()


def jadx(src: Path, out: Path) -> Path | str:
    """Decompile once per firmware and cache under WORK/<id>/src/. A reason string if jadx failed."""
    # Two added apps can share one removed predecessor (media -> music and video).
    with _jadx_locks_guard:
        lock = _jadx_locks.setdefault(out, threading.Lock())
    with lock:
        return _jadx(src, out)


def _jadx(src: Path, out: Path) -> Path | str:
    # --no-debug-info drops line numbers, which otherwise shift on every rebuild and bury real changes.
    # --show-bad-code keeps methods jadx can't fully decompile instead of replacing them with a stub.
    # --no-finally: jadx 1.5.6 places extracted finally blocks differently from run to run on the same
    # input (SettingsProvider.apk), which made two diffs of one pair disagree.
    flags = ["--no-debug-info", "--show-bad-code", "--no-finally", "--comments-level", "none"]
    done = out / ".done"
    if done.exists() and done.read_text() == " ".join(flags):
        return out
    shutil.rmtree(out, ignore_errors=True)
    env = {**os.environ, "JAVA_OPTS": os.environ.get("JAVA_OPTS", "-Xmx4g")}
    try:
        res = subprocess.run([tool("jadx"), "-q", *flags, "--threads-count", "1", "-d", str(out), str(src)],
                             env=env, capture_output=True, text=True, errors="replace", timeout=JADX_TIMEOUT)
    except subprocess.TimeoutExpired:
        shutil.rmtree(out, ignore_errors=True)
        return f"jadx timed out after {JADX_TIMEOUT // 60} min"
    # jadx exits non-zero for every method it can't decompile, so the exit code alone means little.
    log = res.stdout + res.stderr
    if res.returncode < 0 or "OutOfMemoryError" in log or 'Exception in thread "main"' in log or not (
            (out / "sources").exists() or (out / "resources").exists()):
        shutil.rmtree(out, ignore_errors=True)
        return "jadx crashed or ran out of memory; try a larger JAVA_OPTS=-Xmx"
    done.write_text(" ".join(flags))
    return out


JADX_TIMEOUT = 20 * 60


# Preinstalled apps from outside the firmware's makers: a version line only, since they cost the most to
# decompile and matter least. Built from the third-party apps in the KSW and ZXW reports.
THIRD_PARTY_PACKAGES = (
    "com.google.", "com.android.chrome", "com.android.vending", "com.spotify.", "com.ximalaya.", "com.kugou.",
    "com.tencent.", "com.autonavi.", "com.baidu.", "com.mxtech.", "com.estrongs.", "com.sohu.inputmethod.",
    "com.iflytek.inputmethod", "com.zoulou.", "com.dede.android_eggs", "com.waze", "ru.yandex.", "com.netease.",
    "cn.kuwo.", "com.ss.android.", "com.here.", "com.sygic.", "com.tomtom.", "org.telegram.", "com.whatsapp",
    "com.facebook.", "com.microsoft.", "com.amazon.", "org.mozilla.",
)
# AOSP and the chip makers' own apps.
STOCK_PACKAGES = ("com.android.", "android", "com.qualcomm.", "com.qti.", "org.codeaurora.", "vendor.qti.",
                  "com.quicinc.", "com.mediatek.", "com.sprd.", "com.unisoc.") + vendors.SOC_PREFIXES


def app_group(package: str | None, cert: str | None, platform_cert: str | None) -> str:
    """stock, vendor, third-party or unrecognised (a maker fw.py doesn't know yet). Third-party apps are not decompiled.

    Vendor and stock names come before the certificate: KSW's ZLink carries its own key, and AOSP signs
    its apps with four (platform, shared, media, testkey). Anything else not signed like framework-res.apk
    was built outside the firmware.
    """
    package = package or ""
    if package.startswith(THIRD_PARTY_PACKAGES):
        return "third-party"
    if package.startswith(tuple(ns.replace("/", ".") for ns in _namespaces)):
        return "vendor"
    if package.startswith(STOCK_PACKAGES):
        return "stock"
    if platform_cert and cert and cert != platform_cert:
        return "third-party"
    return "unrecognised"


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
# The namespaces of the diff in progress: VENDOR_NAMESPACES for KSW and ZXW, computed from the firmware otherwise.
_namespaces = VENDOR_NAMESPACES
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


def own_prefixes(name: str, package: str | None) -> tuple[str, ...]:
    """Source roots that are the vendor's or the app's own code; everything else under sources/ is libraries."""
    own = _namespaces + ((package.replace(".", "/"),) if package else ())
    # SystemUI carries com.android.wm.shell and com.android.keyguard, Launcher3 com.android.quickstep:
    # platform code the vendor patches, not libraries.
    if package and package.startswith(("com.android.", "android")):
        own += ("com/android/", "android/")
    # framework.jar / services.jar: every class is platform code the vendor may have patched.
    if name.endswith(".jar"):
        own = ("",)
    return own


def write_app_diff(name: str, package: str | None, a_src: Path, b_src: Path, out: Path) -> tuple[str, dict]:
    """Write <slug>.code.diff / .resources.diff; return a one-paragraph summary for the report and its numbers."""
    own = own_prefixes(name, package)
    tiers: dict[str, list[str]] = {"code": [], "resources": []}
    counts: dict[str, int] = {}
    library_pkgs: dict[str, int] = {}
    oversized: list[str] = []
    large_files: list[str] = []
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
                large_files.append(f"apps/{slugify(name)}/{big.name}")
            else:
                tiers[t].append((path, chunk))
    slug = slugify(name)
    parts = []
    info: dict = {f"{t}_{k}": 0 for t in tiers for k in ("files", "lines")} | {"diff_file": None, "large_files": []}
    for t, chunks in tiers.items():
        if not chunks:
            continue
        n = sum(c.count("\n") for _, c in chunks)
        info[f"{t}_files"], info[f"{t}_lines"] = len(chunks), n
        if t == "code":
            info["diff_file"] = f"apps/{slug}.code.diff"
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
        top = sorted(library_pkgs.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
        parts.append("libraries: " + ", ".join(f"{k} ({v})" for k, v in top)
                     + (f" +{len(library_pkgs) - 6} more" if len(library_pkgs) > 6 else ""))
    if oversized:
        parts.append(f"large files diffed separately (>{MAX_FILE_DIFF_LINES} lines): " + ", ".join(f"`{p}`" for p in oversized[:12])
                     + (f" +{len(oversized) - 12} more" if len(oversized) > 12 else ""))
    info["large_files"] = large_files
    return "; ".join(parts) or "no source-level changes", info


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
URL_REF = re.compile(r"(?:https?|wss?|mqtt|tcp|ftp)://[^\s\"'<>\\]+")
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

# Keys the app's own code reads or writes, by call shape: (call up to its "(", index of the key argument).
CONST_DECL = re.compile(r"\bstatic final (String|int|long|short|byte|boolean|float|double|char) ([A-Za-z_]\w*) = ([^;]{1,200});")
SETTINGS_CALLS = (
    (re.compile(r"\bSettings\.(?:System|Global|Secure)\.(?:get(?!UriFor)|put)\w*\("), 1),
    (re.compile(r"\bSettings\.(?:System|Global|Secure)\.getUriFor\("), 0),
    # KSW wrappers: PowerManagerApp.getSettingsInt("key"), mEvtService.putSettingInt("key", v),
    # SysProviderOpt.getRecordInteger("key", d) / updateRecord("key", v).
    (re.compile(r"\.(?:get|put|set)Settings?(?:Int|String|Long|Float|Boolean)\("), 0),
    (re.compile(r"\.(?:getRecord(?:Integer|Value|Boolean|Float|Long|String)?|updateRecord)\("), 0),
)
PREFS_CALL = re.compile(r"(?:\b(\w+)|(edit\(\)|[gG]et(?:Default)?SharedPreferences\([^()]*(?:\([^()]*\))?[^()]*\)))"
                        r"\.(?:get|put)(?:String|Int|Boolean|Long|Float|StringSet)\(")
# sp.getInt, SpfUtils.getBoolean, sharedPreferences.getString, editor.putString: not jSONObject.getString.
PREFS_RECEIVER = re.compile(r"(?i)^(m?sps?|\w*spf\w*|\w*sputils?|\w*pref\w*|\w*editor\w*)$")
SYSPROP_CALLS = ((re.compile(r"\b\w*SystemProperties\w*\.(?:get|set)\w*\("), 0),)
SHELL_PROP = re.compile(r'"(?:getprop|setprop)\s+([\w.\-]+)')
KEY_SHAPE = re.compile(r"^[A-Za-z_][\w.\-]{1,79}$")
ENUM_HEAD = re.compile(r"\benum (\w+)[^{\n]*\{\n")
ENUM_ITEM = re.compile(r"^\s+([A-Z][A-Za-z0-9_]*)\s*(?:\(.*\))?\s*([,;])\s*$")
# Logging tags, AIDL transaction codes and BuildConfig fields change with every build and say nothing.
NOISE_CONST = re.compile(r"^(TAG|\w*_TAG|TAG_\w*|serialVersionUID|DEBUG|TRANSACTION_\w+|VERSION_NAME|VERSION_CODE|APPLICATION_ID|"
                         r"BUILD_TYPE|FLAVOR|LIBRARY_PACKAGE_NAME|BUILD_(TIME|DATE)\w*|LAST_COMMIT|PACKTIME|SVNVERSION|COMPUTER|"
                         r"GIT_\w+|[A-Za-z]\d?|\$\w*)$")
# Build-generated classes renumber their constants on every build: BuildConfig, data binding's BR and mapper.
GENERATED_CLASS = re.compile(r"/(BuildConfig|BR|DataBinderMapperImpl|DataBindingComponent)\.java$")
LITERAL = re.compile(r'^("[^"\\]{0,78}"|-?[\d.]+[LlFfDd]?|0x[0-9a-fA-F]+[Ll]?|true|false|\'.\')$')  # not expressions
RESOURCE_ID = re.compile(r"^(21[34]\d{7}|16[89]\d{5})$")  # 0x7f......, 0x0101.... inlined resource ids
CODE_SCAN = (r"Settings\.|Settings?(Int|String|Long|Float|Boolean)\(|Record\w*\(|SystemProperties|getprop|setprop|"
             r"static final |\.(get|put)(String|Int|Boolean|Long|Float|StringSet)\(|\benum \w+")


def call_args(text: str, i: int) -> list[str]:
    """Top-level arguments of the call whose "(" is just before text[i]; jadx keeps a call on one line."""
    args, depth, cur, quote = [], 1, [], False
    while i < len(text) and text[i] != "\n":
        c = text[i]
        cur.append(c)
        if quote:
            if c == "\\":
                i += 1
                cur.append(text[i:i + 1])
            elif c == '"':
                quote = False
        elif c == '"':
            quote = True
        elif c == "'":
            end = text.find("'", i + 2 if text[i + 1:i + 2] == "\\" else i + 1)
            if end == -1:
                break
            cur.append(text[i + 1:end + 1])
            i = end
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                args.append("".join(cur[:-1]).strip())
                return args
        elif c == "," and depth == 1:
            args.append("".join(cur[:-1]).strip())
            cur = []
        i += 1
    if "".join(cur).strip():
        args.append("".join(cur).strip())  # a call that wraps onto the next line: keep what this line has
    return args


def key_of(arg: str, consts: dict[str, str]) -> str | None:
    """A key argument as text: a literal, or a constant resolved through the app's own declarations."""
    if re.fullmatch(r'"[^"\\]*"', arg):
        key = arg[1:-1]
    elif m := re.fullmatch(r"(?:[A-Za-z_]\w*\.)*([A-Za-z_]\w*)", arg):
        value = consts.get(m[1])
        if value is not None and re.fullmatch(r'"[^"\\]*"', value):
            key = value[1:-1]
        elif value is None and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", m[1]):
            key = m[1]  # declared outside the scanned code (Settings.System.SCREEN_BRIGHTNESS): the name says enough
        else:
            return None  # a local variable
    else:
        return None
    return key if KEY_SHAPE.match(key) else None


def call_keys(text: str, consts: dict[str, str], calls) -> set[str]:
    found = set()
    for pattern, n in calls:
        for m in pattern.finditer(text):
            args = call_args(text, m.end())
            if len(args) > n and (key := key_of(args[n], consts)):
                found.add(key)
    return found


def code_facts(src: Path, own: tuple[str, ...]) -> dict[str, set[str]]:
    """What an app's own code uses, from the whole decompiled tree: settings, SharedPreferences and
    system property keys, string/number constants and enum values. Library classes are left out."""
    facts: dict[str, set[str]] = {k: set() for k in ("settings", "prefs", "props", "constants", "enums")}
    if not (src / "sources").is_dir():
        return facts
    res = subprocess.run([tool("rg", "/opt/homebrew/bin/rg"), "-N", "--no-heading", "--with-filename", "--null",
                          "--sort", "path", "-g", "*.java", "-e", CODE_SCAN, str(src / "sources")],
                         capture_output=True, text=True, errors="replace")
    lines: dict[str, list[str]] = {}
    for row in res.stdout.split("\n"):
        if "\0" not in row:
            continue
        path, _, text = row.partition("\0")
        rel = Path(path).relative_to(src).as_posix()
        cls = rel[len("sources/"):].removeprefix("src/")
        if tier(rel, own) == "code" and not cls.startswith(LIBRARY_PACKAGES) and not GENERATED_CLASS.search(cls):
            lines.setdefault(rel, []).append(text)
    text = "\n".join(t for rel in sorted(lines) for t in lines[rel])
    consts = {m[2]: m[3].strip() for m in CONST_DECL.finditer(text)}
    facts["settings"] = call_keys(text, consts, SETTINGS_CALLS)
    facts["props"] = call_keys(text, consts, SYSPROP_CALLS) | set(SHELL_PROP.findall(text))
    for m in PREFS_CALL.finditer(text):
        if (m[2] or PREFS_RECEIVER.match(m[1])) and (args := call_args(text, m.end())) and (key := key_of(args[0], consts)):
            facts["prefs"].add(key)
    for m in CONST_DECL.finditer(text):
        if not NOISE_CONST.match(m[2]) and LITERAL.match(m[3].strip()) and not RESOURCE_ID.match(m[3].strip()):
            facts["constants"].add(f"{m[2]} = {m[3].strip()}")
    for rel in sorted(r for r, ts in lines.items() if any(ENUM_HEAD.search(t + "\n") for t in ts)):
        body = (src / rel).read_text(errors="replace")
        for m in ENUM_HEAD.finditer(body):
            for line in body[m.end():].split("\n", 2000)[:2000]:
                if not (item := ENUM_ITEM.match(line)):
                    break
                facts["enums"].add(f"{m[1]}.{item[1]}")
                if item[2] == ";":
                    break
    return facts


ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
RESOURCE_VALUE = re.compile(r"^(#[0-9a-fA-F]{3,8}|@(drawable|color|dimen|mipmap|anim|raw)/\w+|-?\d+(\.\d+)?(dp|sp|px|dip)?)$")


def layout_facts(src: Path) -> dict:
    """Per app: view ids per layout name ("main: btn"), @string labels its layouts use, layout files by folder, and the visibility and
    text of each named view, keyed by file and the view's id (or label, or its first named child)."""
    import xml.etree.ElementTree as ET
    out = {"ids": set(), "labels": set(), "files": set(), "views": {}}
    for f in sorted((src / "resources/res").glob("layout*/*.xml")):
        rel = f"{f.parent.name}/{f.stem}"
        out["files"].add(rel)
        text = f.read_text(errors="replace")
        out["ids"] |= {f"{f.stem}: {i}" for i in re.findall(r'android:id="@\+id/(\w+)"', text)}
        out["labels"] |= set(re.findall(r'"@string/(\w+)"', text))
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            continue
        seen: dict[str, int] = {}
        for el in root.iter():
            def name_of(e) -> str | None:
                ident = e.get(ANDROID_NS + "id", "").removeprefix("@+id/").removeprefix("@id/")
                return ident or e.get(ANDROID_NS + "text")
            name = name_of(el)
            if not name:
                # A row container: name it by the first child that has an id or a label.
                if not (child := next((n for n in (name_of(c) for c in el.iter()) if n), None)):
                    continue
                name = f"{el.tag.rsplit('.', 1)[-1]} around {child}"
            n = seen[name] = seen.get(name, 0) + 1
            key = f"{rel}: {name}" + (f" #{n}" if n > 1 else "")
            # No visibility attribute means visible.
            out["views"][key] = {"visibility": el.get(ANDROID_NS + "visibility") or "visible", "text": el.get(ANDROID_NS + "text")}
    return out


def array_items(src: Path, strings: dict[str, str]) -> dict[str, list[str]]:
    """values/arrays.xml and friends: each named array's items, @string references resolved."""
    arrays = {}
    for f in sorted((src / "resources/res/values").glob("*.xml")):
        for kind, name, body in re.findall(r'<(string-array|array|integer-array) name="(\w+)"[^>]*>(.*?)</\1>',
                                           f.read_text(errors="replace"), re.S):
            items = [re.sub(r"\s+", " ", x).strip() for x in re.findall(r"<item>(.*?)</item>", body, re.S)]
            arrays[name] = [strings.get(x[len("@string/"):], x) if x.startswith("@string/") else x for x in items]
    return arrays


def usage_highlights(apps: list[tuple[str, tuple[Path, Path]]], facts: dict) -> list[str]:
    """Highlights rows for what each app's own code and layouts use, and the matching facts.json keys.
    Whole old tree against whole new tree, so a key moved from one class to another is not new. Apps added
    without a predecessor are skipped: everything in them is new, and the app's own line already says so."""
    rows: list[str] = []
    app_info = {a["key"]: a for a in facts["apps"]}
    code_rows: dict[str, list[str]] = {k: [] for k in ("settings", "prefs", "props", "constants", "enums")}
    for key in ("code_settings_keys", "code_prefs_keys", "code_props", "code_constants", "code_enums", "view_ids",
                "layout_labels", "layout_variants", "layout_views", "arrays"):
        facts[key] = {}
    view_rows, label_rows, variant_rows, change_rows, array_rows = [], [], [], [], []
    for name, (a_src, b_src) in apps:
        if not any((a_src / d).is_dir() for d in ("sources", "resources")):
            continue
        own = own_prefixes(name, app_info.get(name, {}).get("package"))
        ca, cb = code_facts(a_src, own), code_facts(b_src, own)
        if not (a_src / "sources").is_dir() or not (b_src / "sources").is_dir():
            ca = cb = {k: set() for k in ca}  # one side has no code to compare with
        # A stock app's own constants, enums and new arrays change with every Android update (com.android.egg);
        # its settings and property keys and changed arrays are still where a vendor patch shows.
        stock = not name.endswith(".jar") and app_info.get(name, {}).get("group") != "vendor"
        if stock:
            for kind in ("constants", "enums"):
                ca[kind] = cb[kind] = set()
        for kind, fact_key in (("settings", "code_settings_keys"), ("prefs", "code_prefs_keys"), ("props", "code_props"),
                               ("enums", "code_enums")):
            add, rem = cb[kind] - ca[kind], ca[kind] - cb[kind]
            if add or rem:
                facts[fact_key][name] = {"added": sorted(add), "removed": sorted(rem)}
                code_rows[kind].append(f"  - `{name}`: {fmt_list(add, 40) or '-'}" + (f"; no longer: {fmt_list(rem, 20)}" if rem else ""))
        add, rem = cb["constants"] - ca["constants"], ca["constants"] - cb["constants"]
        # NAME = 1 -> NAME = 2 is one change, not an addition and a removal.
        by_name: dict[str, tuple[list[str], list[str]]] = {}
        for side, pool in ((0, add), (1, rem)):
            for c in pool:
                by_name.setdefault(c.split(" = ", 1)[0], ([], []))[side].append(c.split(" = ", 1)[1])
        once = {n: (a[0], r[0]) for n, (a, r) in by_name.items() if len(a) == len(r) == 1}
        changed = sorted(f"{n}: {r} -> {a}" for n, (a, r) in once.items())
        add = {c for c in add if c.split(" = ", 1)[0] not in once}
        rem = {c for c in rem if c.split(" = ", 1)[0] not in once}
        if add or rem or changed:
            facts["code_constants"][name] = {"added": sorted(add), "removed": sorted(rem), "changed": changed}
            # Strings first: keys, actions and names say more than message numbers.
            shown = sorted(add, key=lambda c: (not c.split(" = ", 1)[1].startswith('"'), c))[:15]
            parts = [", ".join(f"`{c}`" for c in shown) + (" ..." if len(add) > 15 else "")] if add else []
            if changed:
                parts.append("changed: " + ", ".join(f"`{c}`" for c in changed[:10]) + (" ..." if len(changed) > 10 else ""))
            if rem and not add:
                parts.append(f"removed: {fmt_list(rem, 10)}")
            code_rows["constants"].append(f"  - `{name}` ({len(add)} added, {len(changed)} changed, {len(rem)} removed): "
                                          + "; ".join(parts))

        sa, sb = read_strings(a_src), read_strings(b_src)
        arr_a, arr_b = array_items(a_src, sa), array_items(b_src, sb)
        for arr in sorted(arr_a.keys() & arr_b.keys()):
            plus = [x for x in arr_b[arr] if x not in arr_a[arr]]
            minus = [x for x in arr_a[arr] if x not in arr_b[arr]]
            if plus or minus:
                facts["arrays"].setdefault(name, []).append({"name": arr, "added": plus, "removed": minus})
                array_rows.append(f"  - `{name}` `{arr}`: added {fmt_list(plus, 15) or '-'}; removed {fmt_list(minus, 15) or '-'}")
        for arr in sorted(arr_b.keys() - arr_a.keys()):
            if stock or all(RESOURCE_VALUE.match(x) for x in arr_b[arr]):
                continue  # colours, sizes and drawables of a new screen, not settings
            facts["arrays"].setdefault(name, []).append({"name": arr, "added": arr_b[arr], "removed": []})
            array_rows.append(f"  - `{name}` `{arr}` (new): {fmt_list(arr_b[arr], 15)}")

        la, lb = layout_facts(a_src), layout_facts(b_src)
        if not la["files"]:
            continue
        # Ids added to a layout the app already had (in any folder): a new button on an existing screen.
        # Ids in brand-new layouts come with the layout's own row.
        stems = {f.split("/", 1)[1] for f in la["files"]}
        by_layout: dict[str, list[str]] = {}
        for pair in sorted(lb["ids"] - la["ids"]):
            stem, ident = pair.split(": ")
            if stem in stems:
                by_layout.setdefault(stem, []).append(ident)
        if by_layout:
            facts["view_ids"][name] = by_layout
            # One id added to every size variant of a screen is one row.
            same: dict[tuple[str, ...], list[str]] = {}
            for stem, ids in by_layout.items():
                same.setdefault(tuple(ids), []).append(stem)
            groups = sorted(same.items(), key=lambda kv: kv[1][0])
            view_rows += [f"  - `{name}`: {fmt_list(ids, 12)} in {fmt_list(stems_, 6)}" for ids, stems_ in groups[:15]]
            if len(groups) > 15:
                view_rows.append(f"  - `{name}`: ... {len(groups) - 15} more layouts, all in facts.json")
        # Existing labels put on screen somewhere new; brand-new strings are already under New UI strings.
        if labels := {x for x in lb["labels"] - la["labels"] if x in sa}:
            facts["layout_labels"][name] = sorted(labels)
            label_rows.append(f"  - `{name}`: " + ", ".join(f'`{x}` "{sb.get(x, sa[x])[:60]}"' for x in sorted(labels)[:30])
                              + (f" +{len(labels) - 30} more" if len(labels) > 30 else ""))
        if variants := {f for f in lb["files"] - la["files"] if f.split("/", 1)[1] in stems}:
            facts["layout_variants"][name] = sorted(variants)
            variant_rows.append(f"  - `{name}` ({len(variants)}): {fmt_list(variants, 20)}")

        def label(v: str | None) -> str:
            if v and v.startswith("@string/"):
                return f'{v} "{sb.get(v[8:], sa.get(v[8:], "?"))[:60]}"'
            return v or "(unset)"

        views = []
        for k in sorted(la["views"].keys() & lb["views"].keys()):
            old, new = la["views"][k], lb["views"][k]
            for attr in ("visibility", "text"):
                # Literal text in a layout is the designer's placeholder; the screen shows what code sets.
                if old[attr] != new[attr] and (attr == "visibility" or "@string/" in f"{old[attr]}{new[attr]}"):
                    views.append({"view": k, "attribute": attr, "old": old[attr], "new": new[attr]})
        if views:
            facts["layout_views"][name] = views
            # The same change in every size variant of a layout is one row.
            folders: dict[tuple, list[str]] = {}
            for v in views:
                folder, _, rest = v["view"].partition("/")
                folders.setdefault((rest, v["attribute"], v["old"] or "", v["new"] or ""), []).append(folder)
            for (view, attr, old, new), where in list(folders.items())[:40]:
                change_rows.append(f"  - `{name}` `{view}`: {attr} `{label(old)}` -> `{label(new)}` (in {fmt_list(where, 4)})")
            if len(folders) > 40:
                change_rows.append(f"  - `{name}`: ... {len(folders) - 40} more, all in facts.json")

    for title, kind in (("Settings keys newly used in code (Settings.System/Global/Secure, vendor settings providers)", "settings"),
                        ("SharedPreferences keys newly used in code", "prefs"),
                        ("System properties newly read or set in code", "props"),
                        ("Constants in vendor code (15 per app, strings first; all in facts.json)", "constants"),
                        ("Enum values added", "enums")):
        if code_rows[kind]:
            rows += [f"- {title}:", *code_rows[kind]]
    for title, block in (("View ids added to existing layouts", view_rows), ("Existing labels newly used in layouts", label_rows),
                         ("Layout variants added (a layout the app had, in a new folder)", variant_rows),
                         ("Views shown, hidden or relabelled in layouts", change_rows),
                         ("String arrays changed", array_rows)):
        if block:
            rows += [f"- {title}:", *block]
    return rows


def collect_highlights(out: Path, pa: dict, pb: dict, fa: Path, fb: Path, apps: list[tuple[str, tuple[Path, Path]]],
                       lits: list[tuple[str, str | None, set[str], set[str]]], added_files: list[str],
                       removed_files: list[str], facts: dict) -> list[str]:
    """The Highlights rows; writes them, with `facts` from cmd_diff, to facts.json."""
    rows: list[str] = []
    facts["build"] = {}

    # Build identity: the type/user flip (userdebug -> user, ubuntu -> jenkins) matters to readers.
    for key in ("ro.build.display.id", "ro.build.type", "ro.build.user", "ro.build.version.security_patch",
                "ro.build.version.sdk"):
        va, vb = prop(pa, key), prop(pb, key)
        facts["build"][key] = {"old": va, "new": vb}
        if va != vb:
            rows.append(f"- Build `{key}`: `{va}` -> `{vb}`")
        elif key in ("ro.build.type", "ro.build.user") and vb:
            rows.append(f"- Build `{key}` still `{vb}`")


    # Theme ids from the whole decompiled trees, not the diff: shared code copying a constant into
    # one more app would otherwise look like a new theme.
    def theme_consts(trees: list[tuple[str, Path]]) -> dict[str, set[str]]:
        """"UI_X = 41" -> {"<app>: <source file>", ...}"""
        found: dict[str, set[str]] = {}
        for name, tree in trees:
            res = subprocess.run(["grep", "-rHoE", r"UI_[A-Za-z0-9_]+ = [0-9]+;", str(tree / "sources")],
                                 capture_output=True, text=True, errors="replace")
            for line in res.stdout.splitlines():
                file, _, text = line.rpartition(":")
                if m := THEME_CONST.search(text):
                    found.setdefault(f"{m[1]} = {m[2]}", set()).add(f"{name}: {Path(file).relative_to(tree / 'sources')}")
        return found

    new_consts = theme_consts([(n, b) for n, (_, b) in apps])
    old_consts = theme_consts([(n, a) for n, (a, _) in apps])
    new_themes = new_consts.keys() - old_consts.keys()
    facts["themes_removed"] = sorted(old_consts.keys() - new_consts.keys())

    # KSW keeps theme names as `static final String BMW_EVO_ID7_V2 = "BMW_EVO_ID7_V2";` in a UiThemeUtils
    # class per app; plenty of them don't start with UI_, so the class is the signal, not the name.
    def theme_strings(trees: list[Path]) -> set[str]:
        found = set()
        for tree in trees:
            if (tree / "sources").is_dir():
                # The value is the theme name; the constant name sometimes differs (ID7_ALS_V2 = "PEMP_ID7_UI_V2").
                res = subprocess.run([tool("rg", "/opt/homebrew/bin/rg"), "-o", "-N", "--no-filename",
                                      "--glob", "UiThemeUtils.java", r'static final String \w+ = "[A-Za-z][A-Za-z0-9_]*_[A-Za-z0-9_]+";',
                                      str(tree / "sources")], capture_output=True, text=True, errors="replace")
                found |= set(re.findall(r'= "(\w+)";', res.stdout))
        return found

    # A name is new only when no app had it before: the Bluetooth app catching up with names the
    # launcher already carried is not a new theme. The per-app detail stays in facts.json.
    theme_rows, by_app, names_old, names_new = [], {}, set(), set()
    for name, (a_src, b_src) in apps:
        old_here, new_here = theme_strings([a_src]), theme_strings([b_src])
        names_old |= old_here
        names_new |= new_here
        if new_here - old_here:
            by_app[name] = sorted(new_here - old_here)
            theme_rows.append(f"  - `{name}`: {fmt_list(new_here - old_here)}")
    if names_new - names_old:
        rows += [f"- Theme names added (UiThemeUtils): {fmt_list(names_new - names_old)}"]
    elif theme_rows:
        rows += ["- Theme names added to some apps' UiThemeUtils, already in others:", *theme_rows]
    facts["theme_strings"] = sorted(names_new - names_old)
    facts["theme_strings_by_app"] = by_app
    facts["theme_strings_removed"] = sorted(names_old - names_new)
    facts["theme_strings_before"] = sorted(names_old)
    if new_themes:
        rows.append(f"- Theme ids added: {fmt_list(new_themes)}")
    facts["themes"] = sorted(new_themes)
    facts["theme_sources"] = {t: sorted(new_consts[t]) for t in sorted(new_themes)}

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
    compared = {a or b for f in sorted((out / "apps").rglob("*.diff")) for line in f.read_text(errors="replace").splitlines()
                if line.startswith("+") for a, b in compared_re.findall(line)}
    config_added &= compared
    # URLs inside longer strings ("http://host/api?id=" + id) count too, compared as whole sets so a
    # changed string around an unchanged URL adds nothing.
    urls_old = {u for x in old_all for u in URL_REF.findall(x)}
    urls_new = {u for x in new_all for u in URL_REF.findall(x)}
    url_add, url_rem = urls_new - urls_old, urls_old - urls_new
    for label, pattern, key, pool_add, pool_rem in (
            ("System properties", PROP_KEY, "props", added_lits, removed_lits),
            ("Settings keys", SETTINGS_KEY, "settings_keys", added_lits, removed_lits),
            ("Theme names", THEME_NAME, "theme_names", added_lits, removed_lits),
            ("Platform/model names", MODEL_NAME, "models", added_lits, removed_lits),
            ("File paths and names", FILE_REF, "files", added_lits, removed_lits),
            ("Other apps' package names", PACKAGE_REF, "packages", {x for x in added_lits if not PROP_KEY.match(x)},
             {x for x in removed_lits if not PROP_KEY.match(x)}),
            ("Intent actions and key codes", INTENT_OR_KEY, "intents", added_lits, removed_lits),
            ("URLs", URL_REF, "urls", url_add, url_rem),

            ("Factory config keys", CONFIG_KEY, "config_keys", config_added, set()),
            ("Screen types", SCREEN_TYPE, "screens", added_lits, removed_lits)):
        add = {x for x in pool_add if pattern.match(x)} if key != "urls" else pool_add
        rem = {x for x in pool_rem if pattern.match(x)} if key != "urls" else pool_rem
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
    facts["native_libs"] = libs
    facts["native_libs_removed"] = sorted({Path(p).name for p in removed_files
                                           if p.endswith(".so") and re.search(r"/(priv-app|app|PreInstall)/", p)})

    # Executables are few and every one matters (su -> ksu); the rest of the binaries stay counted per folder.
    exe = re.compile(r"/(s?bin|xbin)/[^/]+$")
    exe_added = sorted(p for p in added_files if exe.search(p))
    exe_removed = sorted(p for p in removed_files if exe.search(p))
    if exe_added:
        rows.append(f"- Executables added: {fmt_list(exe_added)}")
    if exe_removed:
        rows.append(f"- Executables removed: {fmt_list(exe_removed)}")
    facts["executables"] = {"added": exe_added, "removed": exe_removed}

    # Framework/services starting to read a property the vendor apps already used is still news:
    # Android itself now honours it.
    facts["jar_props"] = {}
    for name, _, la, lb in lits:
        if name.endswith(".jar"):
            newly = {x for x in lb - la if PROP_KEY.match(x)} - added_lits
            if newly:
                rows.append(f"- System properties now read by `{name}`: {fmt_list(newly)}")
                facts["jar_props"][name] = sorted(newly)

    def extensions(pool: set[str]) -> set[str]:
        return {e for x in pool if MEDIA_EXT.match(x) for e in x.strip(".").split(".")}

    new_ext = {e for *_, la, lb in lits for e in extensions(lb) - extensions(la)}
    if new_ext:
        rows.append(f"- File extensions added to media lists: {fmt_list('.' + e for e in new_ext)}")
    facts["media_extensions"] = sorted(new_ext)

    # UI strings per app, from the full decompiled trees: a label moved between lines isn't "new".
    by_text: dict[tuple[str, str], list[str]] = {}
    gone_text: dict[tuple[str, str], list[str]] = {}
    renamed: list[dict] = []
    for name, (a_src, b_src) in apps:
        sa, sb = read_strings(a_src), read_strings(b_src)
        for k in sorted(sb.keys() - sa.keys()):
            by_text.setdefault((k, sb[k]), []).append(name)
        if sb:
            for k in sorted(sa.keys() - sb.keys()):
                gone_text.setdefault((k, sa[k]), []).append(name)
        for k in sorted(sb.keys() & sa.keys()):
            if sa[k] != sb[k] and sa[k] and sb[k]:
                renamed.append({"app": name, "name": k, "old": sa[k], "new": sb[k]})
    # A stock app arriving whole (com.android.emergency: 846 strings) would crowd out the vendor's labels.
    app_info = {a["key"]: a for a in facts["apps"]}

    def whole_app(name: str) -> bool:
        return app_info.get(name, {}).get("action") == "added" and app_info[name].get("group") == "stock"

    if by_text:
        rows.append(f"- New UI strings ({len(by_text)}):")
        listed = sorted(((k, v), n) for (k, v), n in by_text.items() if not all(map(whole_app, n)))
        for (k, v), names in sorted(listed, key=lambda kv: (kv[1][0], kv[0]))[:600]:
            where = names[0] if len(names) == 1 else f"{names[0]} +{len(names) - 1} apps"
            rows.append(f'  - "{v[:120]}" (`{k}`, {where})')
        if len(listed) > 600:
            rows.append(f"  - ... {len(listed) - 600} more, all in facts.json")
        bulk: dict[str, int] = {}
        for names in by_text.values():
            if all(map(whole_app, names)):
                bulk[names[0]] = bulk.get(names[0], 0) + 1
        rows += [f"  - `{n}` (added app): {c} strings, all in facts.json" for n, c in sorted(bulk.items())]
    gone_listed = sorted((n[0], k, v) for (k, v), n in gone_text.items() if app_info.get(n[0], {}).get("group") == "vendor")
    if gone_listed:
        rows.append(f"- Removed UI strings in vendor apps ({len(gone_listed)}):")
        rows += [f'  - "{v[:80]}" (`{k}`, {n})' for n, k, v in gone_listed[:60]]
        if len(gone_listed) > 60:
            rows.append(f"  - ... {len(gone_listed) - 60} more, all in facts.json")
    if renamed:
        rows.append(f"- Changed UI strings ({len(renamed)}):")
        rows += [f'  - `{r["app"]}` `{r["name"]}`: "{r["old"]}" -> "{r["new"]}"' for r in renamed[:60]]
    facts["strings"] = [{"name": k, "text": v, "apps": n} for (k, v), n in sorted(by_text.items())]
    facts["strings_changed"] = renamed
    facts["strings_removed"] = [{"name": k, "text": v, "apps": n} for (k, v), n in sorted(gone_text.items())]

    # Resource folders an app didn't have before: layout-1024x592 means a new screen size is handled.
    new_dirs = []
    facts["resource_dirs"], facts["resource_dirs_removed"] = {}, {}
    for name, (a_src, b_src) in apps:
        old = {d.name for d in (a_src / "resources/res").glob("*") if d.is_dir()}
        new = {d.name for d in (b_src / "resources/res").glob("*") if d.is_dir()}
        added_dirs = {d for d in new - old if not LOCALE_VALUES.match(f"resources/res/{d}/")}
        if added_dirs and old:
            new_dirs.append(f"  - `{name}`: {fmt_list(added_dirs, 15)}")
            facts["resource_dirs"][name] = sorted(added_dirs)
        if new and (gone_dirs := {d for d in old - new if not LOCALE_VALUES.match(f"resources/res/{d}/")}):
            facts["resource_dirs_removed"][name] = sorted(gone_dirs)
    if new_dirs:
        rows += ["- New resource folders (screen sizes, orientations, themes):", *new_dirs]

    # New locale folders: a language the app didn't have before (Ukrainian, Croatian...).
    langs: dict[str, list[str]] = {}
    langs_gone: dict[str, list[str]] = {}
    for name, (a_src, b_src) in apps:
        def locales(src: Path) -> set[str]:
            return {m[1] for d in (src / "resources/res").glob("values-*")
                    if d.is_dir() and (m := LOCALE_VALUES.match(f"resources/res/{d.name}/"))}
        old, new = locales(a_src), locales(b_src)
        if not old:
            continue
        for lang in new - old:
            langs.setdefault(lang, []).append(name)
        for lang in old - new if new else ():
            langs_gone.setdefault(lang, []).append(name)
    facts["languages"] = dict(sorted(langs.items()))
    facts["languages_removed"] = dict(sorted(langs_gone.items()))
    if langs:
        rows.append("- New translation languages: " + ", ".join(
            f"`{lang}` ({apps_[0]}{f' +{len(apps_) - 1}' if len(apps_) > 1 else ''})" for lang, apps_ in sorted(langs.items())))

    # New layouts name new screens: kesaiwei_id6_activity_main, layout_bmw_hw_screen_reverse.
    new_layouts = []
    facts["layouts"], facts["layouts_removed"] = {}, {}
    for name, (a_src, b_src) in apps:
        def layouts(src: Path) -> set[str]:
            return {f.stem for f in (src / "resources/res").glob("layout*/*.xml")}
        la_, lb_ = layouts(a_src), layouts(b_src)
        if lb_ - la_ and la_:
            new_layouts.append(f"  - `{name}` ({len(lb_ - la_)}): {fmt_list(lb_ - la_, 12)}")
            facts["layouts"][name] = sorted(lb_ - la_)
        if la_ - lb_ and lb_:
            facts["layouts_removed"][name] = sorted(la_ - lb_)
    if new_layouts:
        rows += ["- New layouts:", *new_layouts]

    rows += usage_highlights(apps, facts)

    # Manifests and config values from the whole files: jadx puts each attribute on its own line,
    # so an element rarely fits in one diff line.
    def read(path: Path) -> str:
        return path.read_text(errors="replace") if path.is_file() else ""

    item_rows, flag_rows, cfg_rows = [], [], []
    facts["manifest"], facts["android_config"] = {}, []
    for name, (a_src, b_src) in apps:
        ma_, mb_ = read(a_src / "resources/AndroidManifest.xml"), read(b_src / "resources/AndroidManifest.xml")
        ia, ib = {m[1] for m in MANIFEST_ITEM.findall(ma_)}, {m[1] for m in MANIFEST_ITEM.findall(mb_)}
        entry = {"added": sorted(ib - ia), "removed": sorted(ia - ib) if mb_ else [], "flags_added": [], "flags_removed": []}
        if ib - ia:
            item_rows.append(f"  - `{name}` added: {fmt_list(ib - ia, 30)}")
        if mb_ and ia - ib:
            item_rows.append(f"  - `{name}` removed: {fmt_list(ia - ib, 30)}")
        fa_, fb_ = {f"{k}={v}" for k, v in MANIFEST_FLAG.findall(ma_)}, {f"{k}={v}" for k, v in MANIFEST_FLAG.findall(mb_)}
        if ma_ and fa_ != fb_:
            flag_rows.append(f"  - `{name}`: added {fmt_list(fb_ - fa_)}; removed {fmt_list(fa_ - fb_)}")
            entry["flags_added"], entry["flags_removed"] = sorted(fb_ - fa_), sorted(fa_ - fb_)
        if any(entry.values()):
            facts["manifest"][name] = entry

        def configs(src: Path) -> dict[str, str]:
            return {k: re.sub(r"\s+", " ", v).strip() for f in sorted((src / "resources/res/values").glob("*.xml"))
                    for _, k, v in CONFIG_VALUE.findall(read(f))}
        ca, cb = configs(a_src), configs(b_src)
        for k in sorted(cb):
            if ca and ca.get(k) != cb[k]:
                cfg_rows.append(f"- Android `{k}` (`{name}`): `{ca.get(k, '(unset)')}` -> `{cb[k]}`")
                facts["android_config"].append({"app": name, "key": k, "old": ca.get(k), "new": cb[k]})
    if flag_rows:
        rows += ["- Manifest flags changed:", *flag_rows]
    if item_rows:
        rows += ["- Manifest entries (permissions, activities, services, receivers, actions), per app:", *item_rows]
    rows += cfg_rows

    # key=value config files (Wi-Fi driver .ini, .conf, .prop): which keys changed.
    kv_rows = []
    facts["config_files"] = []
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
        facts["config_files"] += [{"path": path, "key": k, "old": old.get(k), "new": new.get(k)}
                                  for k in sorted(old.keys() | new.keys()) if old.get(k) != new.get(k)]
        if changes:
            kv_rows.append(f"  - `{path}`: " + ", ".join(changes[:20]) + (f" +{len(changes) - 20} more" if len(changes) > 20 else ""))
    if kv_rows:
        rows += ["- Config file settings changed:", *kv_rows]

    # Factory settings: leaf elements of the vendor's config XML (zxw_factory_config.xml and the like).
    facts["factory_settings"] = []
    for rel in sorted({p.relative_to(fb).as_posix() for p in fb.glob("*/**/*factory_config*.xml")}):
        a_file, b_file = fa / rel, fb / rel
        old = dict(XML_LEAF.findall(a_file.read_text(errors="replace"))) if a_file.is_file() else {}
        new = dict(XML_LEAF.findall(b_file.read_text(errors="replace")))
        added = {k for k in new.keys() - old.keys()}
        if added:
            rows.append(f"- Factory settings added in `{rel}`: {fmt_list(f'<{k}>' for k in added)}")
        if old.keys() - new.keys():
            rows.append(f"- Factory settings removed in `{rel}`: {fmt_list(f'<{k}>' for k in old.keys() - new.keys())}")
        changed = [{"key": k, "old": old[k], "new": new[k]} for k in sorted(old.keys() & new.keys()) if old[k] != new[k]]
        for c in changed:
            rows.append(f"- Factory default `<{c['key']}>` in `{rel}`: `{c['old']}` -> `{c['new']}`")
        if added or old.keys() - new.keys() or changed:
            facts["factory_settings"].append({"file": rel, "file_added": not a_file.is_file(), "added": sorted(added),
                                              "removed": sorted(old.keys() - new.keys()),
                                              "changed": changed})

    (out / "facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
    return rows


def vendor_namespaces_of(a_id: str, b_id: str, pa: dict, pb: dict, *sides) -> list[dict] | None:
    """None when both firmwares are KSW or ZXW (VENDOR_NAMESPACES applies), else the maker's namespaces found in either."""
    metas = [json.loads((WORK / i / "meta.json").read_text()) for i in (a_id, b_id)]
    if all(vendor_platform(m["display_id"] or m["id"])[0] for m in metas):
        return None
    found: dict[str, dict] = {}
    for fw_id, props, (apks, platform_cert) in zip((a_id, b_id), (pa, pb), sides):
        apps = [(info.get("package"), info.get("cert")) for _, info in apks.values()]
        for n in vendors.vendor_namespaces(apps, platform_cert, functools.partial(prop, props), fw_id, THIRD_PARTY_PACKAGES):
            found[n["namespace"]] = n  # the new side's counts win
    return [found[k] for k in sorted(found)]


def cmd_diff(args) -> None:
    tool("rg", "/opt/homebrew/bin/rg")  # needed by the highlights, after all the decompiling
    a_id, b_id = args.old, args.new
    for fw_id in (a_id, b_id):
        if not extracted(fw_id):
            sys.exit(f"error: {fw_id} is not extracted (or its tree was freed); run `fw.py extract` on its zip")
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
    prop_lines, prop_facts = [], []
    for file in sorted(pa.keys() | pb.keys()):
        a, b = pa.get(file, {}), pb.get(file, {})
        for k in sorted(a.keys() | b.keys()):
            if a.get(k) == b.get(k) or re.search(r"(^|\.)date(\.utc)?$|incremental|display\.id$|build\.id$|description$", k):
                continue
            # A fingerprint changes every build; only its last part, the build type and signing keys
            # (userdebug/test-keys -> user/release-keys), is news.
            if "fingerprint" in k and a.get(k, "").rpartition(":")[2] == b.get(k, "").rpartition(":")[2]:
                continue
            prop_lines.append(f"- `{file}` `{k}`: `{a.get(k, '(none)')}` -> `{b.get(k, '(none)')}`")
            prop_facts.append({"file": file, "key": k, "old": a.get(k), "new": b.get(k)})
    lines += ["## Build properties", "", *(prop_lines or ["- no changes besides build dates/fingerprints"]), ""]
    image_lines, image_facts = images.report(images.load(WORK / a_id), images.load(WORK / b_id))
    lines += image_lines

    # Apps: inventory by package so a moved/renamed APK still pairs up.
    def apks(fs: Path, manifest: dict[str, Entry]) -> dict[str, tuple[str, dict]]:
        by_pkg: dict[str, list[tuple[str, dict]]] = {}
        for p in manifest:
            if p.endswith(".apk") and manifest[p].kind == "file":
                info = apk_info(fs / p) | {"cert": signing_cert(fs / p)}
                pkg = info.get("package")
                by_pkg.setdefault(pkg if pkg and pkg != "?" else p, []).append((p, info))
        # A package shipped at several paths (overlays, per-model variants) pairs up by path instead.
        return {k if len(v) == 1 else f"{k} ({p})": (p, info) for k, v in by_pkg.items() for p, info in v}

    print("reading app manifests")
    with cf.ThreadPoolExecutor(2) as pool:
        fa_apks, fb_apks = pool.map(apks, (fa, fb), (ma, mb))
    platform_a, platform_b = (next((i["cert"] for _, i in side.values() if i.get("package") == "android"), None)
                              for side in (fa_apks, fb_apks))
    global _namespaces
    computed = vendor_namespaces_of(a_id, b_id, pa, pb, (fa_apks, platform_a), (fb_apks, platform_b))
    # Computed ones end in "/" so com.car never takes in com.carrot.
    _namespaces = VENDOR_NAMESPACES if computed is None else tuple(n["namespace"].replace(".", "/") + "/" for n in computed)
    app_rows, to_decompile, app_facts = [], [], []

    # A vendor app split or renamed (com.wits.ksw.media -> .music and .video) is diffed against the app
    # it replaced, not against nothing, or every string in it looks new.
    def family(package: str | None) -> str | None:
        parts = (package or "").split(".")
        return ".".join(parts[:-1]) if len(parts) >= 4 else None

    removed_by_family: dict[str, list[str]] = {}
    for k, v in fa_apks.items():
        if k not in fb_apks and (fam := family(v[1].get("package"))):
            removed_by_family.setdefault(fam, []).append(v[0])
    # Two apps gone from one family leaves no way to tell which one an added app replaced.
    removed_by_family = {fam: paths[0] for fam, paths in removed_by_family.items() if len(paths) == 1}
    labels = {"third-party": ", third-party: not decompiled", "unrecognised": ", unrecognised maker"}
    for pkg in sorted(fa_apks.keys() | fb_apks.keys()):
        a, b = fa_apks.get(pkg), fb_apks.get(pkg)
        path, info = b or a
        group = app_group(info.get("package"), info.get("cert"), platform_b if b else platform_a)
        fact = {"key": pkg, "package": info.get("package"), "name": Path(path).stem, "path": path, "old_path": None,
                "version_old": a and a[1].get("version_name"), "version_new": b and b[1].get("version_name"),
                "kinds": [], "group": group, "is_vendor": group == "vendor", "decompiled": group != "third-party"}
        if not a:
            predecessor = removed_by_family.get(family(info.get("package"))) if group == "vendor" else None
            note = f", diffed against removed `{predecessor}`" if predecessor else ""
            app_rows.append((group, f"- **added** `{pkg}` {info.get('version_name')} (`{path}`{note}{labels.get(group, '')})"))
            fact |= {"action": "added", "old_path": predecessor}
            if group != "third-party":
                to_decompile.append((pkg, info.get("package"), predecessor, path))
        elif not b:
            app_rows.append((group, f"- **removed** `{pkg}` {info.get('version_name')} (`{path}`{labels.get(group, '')})"))
            fact |= {"action": "removed", "decompiled": False}
        elif ma[a[0]].value != mb[b[0]].value:
            kinds = classify_zip_change(fa / a[0], fb / b[0])
            if not kinds:
                continue  # re-signed only
            va, vb = a[1].get("version_name"), b[1].get("version_name")
            ver = f"{va} -> {vb}" if va != vb else f"{va} (version unchanged)"
            moved = f", moved from `{a[0]}`" if a[0] != b[0] else ""
            size = f", {mb_size(ma[a[0]].size)} -> {mb_size(mb[b[0]].size)}" if abs(ma[a[0]].size - mb[b[0]].size) > 1 << 20 else ""
            app_rows.append((group, f"- **changed** `{pkg}` {ver} [{', '.join(kinds)}] (`{path}`{moved}{size}{labels.get(group, '')})"))
            fact |= {"action": "changed", "old_path": a[0] if a[0] != b[0] else None, "kinds": kinds}
            if group != "third-party":
                to_decompile.append((pkg, info.get("package"), a[0], path))
        else:
            continue
        app_facts.append(fact)
    vendor_rows = [r for g, r in app_rows if g == "vendor"]
    android_rows = [r for g, r in app_rows if g != "vendor"]
    found = [] if computed is None else [f"Namespaces computed from the firmware: {vendors.describe(computed)}.", ""]
    lines += ["## Vendor apps", "", *found, *(vendor_rows or ["- none"]), "",
              "## Android apps", "", *(android_rows or ["- none"]), ""]

    # JARs (framework, services): code changes only.
    jar_rows = []
    for p in changed:
        if p.endswith(".jar") and (kinds := classify_zip_change(fa / p, fb / p)):
            jar_rows.append(f"- `{p}` [{', '.join(kinds)}]")
            to_decompile.append((p, None, p, p))
    lines += ["## Framework and other JARs", "", *(jar_rows or ["- none"]), ""]

    # Plain files: text files are listed and diffed; binaries are only counted per folder.
    @functools.cache
    def is_text(p: str) -> bool:
        if Path(p).suffix in TEXT_SUFFIXES:
            return True
        # Any other small file without NUL bytes, e.g. vendor/etc/fstab.emmc (where /data encryption is switched off).
        f = fb / p if (fb / p).is_file() else fa / p
        if f.is_symlink() or not f.is_file() or f.stat().st_size > 1 << 20 or Path(p).suffix in (".so", ".ko", ".apk", ".jar"):
            return False
        with f.open("rb") as fh:
            head = fh.read(8192)
        return bool(head) and b"\0" not in head

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
        if isinstance(a_src, str) or isinstance(b_src, str):
            reason = a_src if isinstance(a_src, str) else b_src
            return name, (f"**decompile failed** ({reason})", {"failed": reason}), None, lits
        return name, write_app_diff(name, package, a_src, b_src, out / "apps"), (a_src, b_src), lits

    with cf.ThreadPoolExecutor(args.jobs) as pool:
        stats = list(pool.map(decompile, to_decompile))
    lines += ["## Decompiled source diffs", "", "Full diffs in `apps/<name>.code.diff` and `apps/<name>.resources.diff`.", "",
              *[f"- `{n}`: {s}" for n, (s, _), _, _ in stats], ""]

    identity = [{k: v for k, v in json.loads((WORK / i / "meta.json").read_text()).items() if k != "signatures"}
                for i in (a_id, b_id)]
    for fact in app_facts:
        if fact["decompiled"] and not next(srcs for n, _, srcs, _ in stats if n == fact["key"]):
            fact["decompiled"] = False
    facts = {"old": identity[0], "new": identity[1], "apps": app_facts, "build_props": prop_facts,
             "decompiled": {n: info for n, (_, info), _, _ in stats}, "images": image_facts,
             "vendor_namespaces": {"source": "VENDOR_NAMESPACES" if computed is None else "computed",
                                   "namespaces": list(_namespaces)}}
    highlights = collect_highlights(out, pa, pb, fa, fb, [(n, srcs) for n, _, srcs, _ in stats if srcs],
                                    [lits for *_, lits in stats], added, removed, facts)
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


SITE_UPDATES = Path(__file__).resolve().parents[2] / "src/data/updates"


def site_page(fw_id: str) -> Path | None:
    """The site's changelog for a firmware, when fw.py runs from a checkout of the site."""
    return next(iter(sorted(SITE_UPDATES.glob(f"*/*/{fw_id}.md"))), None)


def cmd_score(args) -> None:
    """How much of a hand-written changelog the report finds, with no model involved."""
    out = WORK / "diffs" / f"{args.old}..{args.new}"
    changelog = Path(args.changelog) if args.changelog else site_page(args.new)
    if not changelog or not changelog.is_file():
        sys.exit(f"error: no changelog found for {args.new}; pass one with --changelog")
    report = (out / "REPORT.md").read_text(errors="replace").lower()
    evidence = report + "".join(f.read_text(errors="replace").lower() for f in sorted(out.rglob("*.diff")))
    terms = changelog_terms(changelog.read_text())
    in_report = [t for t in terms if t.lower() in report]
    rest = [t for t in terms if t.lower() not in report]
    # Terms a bullet mentions for comparison (an older theme, an existing vendor id) exist in the old
    # firmware already; they aren't changes, so they don't count against the report.
    old_literals: set[str] = set()
    if rest:
        ma = load_manifest(args.old)
        for p in ma:
            f = WORK / args.old / "fs" / p
            if p.endswith((".apk", ".jar")) and ma[p].kind == "file" and f.is_file():
                old_literals |= {x.lower() for x in dex_literals(f, libraries=True)}
    in_diffs = [t for t in rest if t.lower() in evidence]

    # Constant names such as UI_NUM_KSW_BENZ_NTG7 aren't dex literals, but the old decompiled code has
    # them. One search for all remaining terms: a search per term rescanned the whole tree each time.
    unresolved = [t for t in rest if t.lower() not in old_literals]
    in_old_src: set[str] = set()
    src = WORK / args.old / "src"
    if unresolved and src.is_dir():
        with tempfile.NamedTemporaryFile("w", suffix=".txt") as patterns:
            patterns.write("\n".join(unresolved) + "\n")
            patterns.flush()
            # ripgrep: BSD grep takes minutes on a case-insensitive multi-pattern search of a big tree.
            # Whole lines, not -o: -o reports one of two overlapping terms (UI_NUM_KSW in UI_NUM_KSW_BENZ_NTG7).
            res = subprocess.run([tool("rg", "/opt/homebrew/bin/rg", "/usr/bin/rg"), "-i", "-F", "-N",
                                  "--no-filename", "-f", patterns.name, str(src)],
                                 capture_output=True, text=True, errors="replace")
            hits = res.stdout.lower()
            in_old_src = {t.lower() for t in unresolved if t.lower() in hits}

    # Anything the old firmware already had is context: the score is about new identifiers.
    context = [t for t in rest if t.lower() in old_literals or t.lower() in in_old_src]
    in_diffs = [t for t in in_diffs if t not in context]
    missing = [t for t in rest if t not in context and t not in in_diffs]
    n = (len(terms) - len(context)) or 1
    print(f"{args.old} -> {args.new}: {len(terms)} terms in {changelog.name}")
    print(f"  in report:        {len(in_report):3} ({100 * len(in_report) // n}% of {n} change terms)")
    print(f"  only in diffs:    {len(in_diffs):3}  {', '.join(in_diffs)}")
    print(f"  context (in old): {len(context):3}  {', '.join(context)}")
    print(f"  not found at all: {len(missing):3}  {', '.join(missing)}")


# --------------------------------------------------------------------------- batch


def zip_build(zip_path: Path) -> tuple[int, str] | None:
    """Build date (UTC seconds, 0 if unknown) and product line, from the OTA metadata without unpacking.
    None for a zip without a system partition fw.py can read (a persist backup) or a super.img flash kit: `extract`
    reads those, but a kit would otherwise slot into its OTA line and change every pair after it."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            text = zf.read("META-INF/com/android/metadata").decode(errors="replace") if "META-INF/com/android/metadata" in names else ""
    except zipfile.BadZipFile:
        return None
    if not names & {"payload.bin", "system.transfer.list", "system.img"}:
        return None
    meta = dict(line.partition("=")[::2] for line in text.splitlines())
    fw_id = zip_path.name.removesuffix(".zip")
    # KSW names the line in the id (Ksw-R-M600_OS_v1.8.6-ota, Witstek-T-M600_OS_v1.8.6-ota) and every
    # M600/M700 is `bengal`; ZXW ids are dates, but the device name tells GT6-CAR from GT7-CAR.
    return int(meta.get("post-timestamp") or 0), ksw_line(fw_id) or meta.get("pre-device") or fw_id


def ksw_line(fw_id: str) -> str | None:
    """R-M600, or R-M600 NEXAI: a letter suffix on the version (v1.7.2NEXAI) is a variant with its own line."""
    m = re.search(r"-([A-Z]-M\d{3}|Q-Userdebug)_OS_v[\d.]+([A-Za-z]*)", fw_id)
    return f"{m[1]} {m[2]}".strip() if m else None


def pair_up(builds: dict[str, tuple[str, int, Path]]) -> list[tuple[str, str, str]]:
    """(line, old, new): each build against the one before it in its line, by build date. The first build of
    a variant line ("R-M600 NEXAI") is compared with the latest earlier build of its base line ("R-M600")."""
    pairs = []
    for line in sorted({v[0] for v in builds.values()}):
        ids = [i for _, i in sorted((d, i) for i, (l, d, _) in builds.items() if l == line)]
        base = line.split(" ")[0]
        if base != line:
            first = builds[ids[0]][1]
            earlier = sorted((d, i) for i, (l, d, _) in builds.items() if l == base and d < first)
            if earlier:
                pairs.append((line, earlier[-1][1], ids[0]))
        pairs += [(line, a, b) for a, b in zip(ids, ids[1:])]
    return pairs


def extracted(fw_id: str) -> bool:
    # extract() wipes the folder first and writes meta.json last, so both together mean complete.
    return (WORK / fw_id / "fs").is_dir() and (WORK / fw_id / "meta.json").is_file()


def free_trees(ids: set[str], needed: set[str]) -> None:
    for fw_id in sorted(ids - needed):
        if (WORK / fw_id / "fs").exists():
            for sub in ("fs", "src", "img"):
                shutil.rmtree(WORK / fw_id / sub, ignore_errors=True)
            print(f"freed {fw_id}")


def site_date(page: Path | None) -> str:
    m = re.search(r"^date:\s*(\S+)", page.read_text(), re.M) if page else None
    return m[1] if m else ""


def skipped_releases(old: str, new: str) -> list[str]:
    """Site changelogs dated strictly between two firmwares of one platform: releases never downloaded."""
    old_page, new_page = site_page(old), site_page(new)
    if not old_page or not new_page:
        return []
    lo, hi = site_date(old_page), site_date(new_page)
    # One site folder holds several lines (ksw/m600: R, S, T and NEXAI).
    return [p.stem for d, p in sorted((site_date(p), p) for p in new_page.parent.glob("*.md"))
            if lo < d < hi and ksw_line(p.stem) == ksw_line(new)]


def bullet_count(md: Path | None) -> int | None:
    if not md or not md.is_file():
        return None
    return sum(1 for line in md.read_text().split("---", 2)[-1].splitlines() if re.match(r"\s*- ", line))


def cmd_batch(args) -> None:
    import contextlib
    import io
    import time

    zips = sorted({z for d in map(Path, args.folders) for z in (sorted(d.glob("*.zip")) if d.is_dir() else [d])})
    builds: dict[str, tuple[str, int, Path]] = {}
    for z in zips:
        fw_id = z.name.removesuffix(".zip")
        if not (build := zip_build(z)):
            print(f"{z.name}: not an OTA zip, skipped")
            continue
        date, line = build
        meta = WORK / fw_id / "meta.json"
        if not date and not meta.is_file() and not args.dry_run:
            if shutil.disk_usage(WORK).free < args.min_free_gb << 30:
                sys.exit(f"error: less than {args.min_free_gb} GB free under {WORK}; can't extract {z.name} for its date")
            try:
                extract(z)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 - one broken zip shouldn't stop the rest
                print(f"{z.name}: no build date and extraction failed ({exc}), skipped")
                continue
        if not date and meta.is_file():
            date = json.loads(meta.read_text())["date"]
        builds[fw_id] = (line, date, z)
    pairs = pair_up(builds)
    print(f"{len(builds)} zips, {len(pairs)} pairs")
    if args.dry_run:
        for line, a, b in pairs:
            done = (WORK / "diffs" / f"{a}..{b}" / "frontmatter.md").exists()
            unknown = [x for x in (a, b) if not builds[x][1]]
            print(f"  {line}: {a} -> {b}{' (done)' if done else ''}"
                  + (f" (no build date for {', '.join(unknown)} until extracted; order may change)" if unknown else ""))
        return

    def log(msg: str) -> None:
        print(time.strftime("%H:%M:%S"), msg, flush=True)

    status: dict[tuple[str, str], str] = {}
    for n, (line, a, b) in enumerate(pairs):
        out = WORK / "diffs" / f"{a}..{b}"
        # frontmatter.md is written after REPORT.md, so it marks a finished pair.
        if (out / "frontmatter.md").exists():
            status[a, b] = "done before"
        else:
            missing = [x for x in (a, b) if not extracted(x)]
            if missing:
                free_trees(set(builds), {x for _, p, q in pairs[n:] for x in (p, q) if (p, q) not in status})
                if shutil.disk_usage(WORK).free < args.min_free_gb << 30:
                    log(f"less than {args.min_free_gb} GB free under {WORK}; stopping before {a} -> {b}")
                    break
            try:
                for fw_id in missing:
                    log(f"extract {fw_id}")
                    extract(builds[fw_id][2])
                log(f"diff {a} -> {b}")
                cmd_diff(argparse.Namespace(old=a, new=b, jobs=args.jobs))
                if site_page(b):
                    text = io.StringIO()
                    with contextlib.redirect_stdout(text):
                        cmd_score(argparse.Namespace(old=a, new=b, changelog=None))
                    (out / "score.txt").write_text(text.getvalue())
                (out / "frontmatter.md").write_text(frontmatter(b))
                status[a, b] = "done"
            except (Exception, SystemExit) as exc:  # noqa: BLE001 - one broken zip shouldn't stop the rest
                status[a, b] = f"failed: {(str(exc).splitlines() or [type(exc).__name__])[0][:200]}"
                log(f"FAILED {a} -> {b}: {exc}")
        free_trees(set(builds), {x for _, p, q in pairs if (p, q) not in status for x in (p, q)})

    rows = ["# Firmware diffs", "",
            "One row per pair from `fw.py batch`. **Skipped** = site releases between the two builds that "
            "were never downloaded; **site** = bullets in the site's changelog (0 = frontmatter only); "
            "**highlights** = top-level lines in the report's Highlights.", "",
            "| Line | Old | New | Built | Skipped | Site | Highlights | Status |", "|---|---|---|---|---|---|---|---|"]
    for line, a, b in pairs:
        report = WORK / "diffs" / f"{a}..{b}" / "REPORT.md"
        highlights = ""
        if report.is_file():
            section = report.read_text().split("## Highlights", 1)[-1].split("\n## ", 1)[0]
            highlights = str(sum(1 for l in section.splitlines() if l.startswith("- ")))
        site = bullet_count(site_page(b))
        rows.append(f"| {line} | {a} | [{b}]({a}..{b}/REPORT.md) | {utc(builds[b][1])[:10]} | "
                    f"{', '.join(skipped_releases(a, b))} | {'' if site is None else site} | {highlights} | {status.get((a, b), 'not run')} |")
    (WORK / "diffs").mkdir(parents=True, exist_ok=True)
    (WORK / "diffs" / "INDEX.md").write_text("\n".join(rows) + "\n")
    print(f"index: {WORK / 'diffs' / 'INDEX.md'}")


SCRIPTS = {
    "rules": "security and privacy checks over a diff folder",
    "sitecheck": "compare a diff folder with the site's themes, factory settings and frontmatter",
    "draft": "write a site-format changelog draft from a diff folder",
    "evaluate": "score reports against the analysed evidence files; snapshot and compare reports",
}


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
    p = sub.add_parser("batch", help="extract and diff every zip against its predecessor in its product line")
    p.add_argument("folders", nargs="+", help="folders of OTA zips, or zips")
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--min-free-gb", type=int, default=25, help="stop before an extraction below this much free disk")
    p.add_argument("--dry-run", action="store_true", help="list the pairs and stop")
    p.set_defaults(func=cmd_batch)
    # The checks that read a finished diff folder live in their own scripts; fw.py only passes the arguments on.
    for script, help_ in SCRIPTS.items():
        sub.add_parser(script, help=help_, add_help=False)
    if len(sys.argv) > 1 and sys.argv[1] in SCRIPTS:
        sys.exit(subprocess.run([sys.executable, str(Path(__file__).resolve().with_name(f"{sys.argv[1]}.py")), *sys.argv[2:]]).returncode)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
