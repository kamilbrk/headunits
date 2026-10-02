"""The images in an OTA that are not filesystems: boot, dtb/dtbo, vbmeta, bootloaders, trusted firmware, modems.

extract() writes them to a folder, describe() hashes each and pulls its version strings into
WORK/<id>/images.json (which outlives the extracted tree), and report() compares two of those for
the diff: a changed kernel, U-Boot or modem build is otherwise invisible, since none of it sits in
a filesystem.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from collections.abc import Callable
from pathlib import Path

import formats

# Partitions that are data, not firmware, or that fw.py already unpacks as filesystems.
SKIP = {"super", "userdata", "persist", "metadata", "cache", "misc", "frp", "cust"}
RAW_SUFFIXES = (".img", ".bin", ".mbn", ".elf", ".fv")
MAX_SCAN = 256 << 20  # version strings are read from images up to this size; bigger ones are only hashed

# label -> pattern; the first match of each label is kept.
VERSION_PATTERNS = (
    ("kernel", rb"Linux version \d[^\x00\n]{0,200}"),
    ("u-boot", rb"U-Boot (?:SPL )?\d{4}\.\d{2}[^\x00\n]{0,80}"),
    ("trusted firmware", rb"v\d+\.\d+(?:\.\d+)?-[0-9a-f]{6,}\((?:release|debug)\)"),
    ("built", rb"(?<![\w])Built ?: ?[0-9:, ]*[A-Z][a-z]{2} [ \d]\d \d{4}"),
    ("qualcomm image", rb"QC_IMAGE_VERSION_STRING=([^\x00\n]{1,100})"),
    ("oem image", rb"OEM_IMAGE_VERSION_STRING=([^\x00\n]{1,100})"),
    ("modem platform", rb"Platform Version: *([^\x00\n]{1,80})"),
    ("modem project", rb"Project Version: *([^\x00\n]{1,80})"),
    ("build date", rb"(?<![\d-])\d{2}-\d{2}-20\d{2} \d{2}:\d{2}:\d{2}(?![\d])"),
)


def wanted(name: str, fs_partitions: list[str]) -> bool:
    base = Path(name).name
    stem = base.rsplit(".", 1)[0]
    return (base == name and base.endswith(RAW_SUFFIXES) and stem not in SKIP and stem not in fs_partitions
            and not base.startswith("._"))


def extract(zip_path: Path, out: Path, fs_partitions: list[str], payload_dumper: Callable[[], str]) -> list[str]:
    """Write the zip's non-filesystem images to out/. Top-level files only, so META-INF tools stay out."""
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        if "payload.bin" in names:
            dumper = payload_dumper()
            listing = subprocess.run([dumper, "-l", str(zip_path)], capture_output=True, text=True, check=True).stdout
            parts = sorted(p for p in set(re.findall(r"(\w+) \(", listing)) if p not in fs_partitions and p not in SKIP)
            if parts:
                res = subprocess.run([dumper, "-q", "-c", str(os.cpu_count() or 4), "-p", ",".join(parts), "-o", str(out),
                                      str(zip_path)], capture_output=True, text=True)
                if res.returncode:
                    sys.exit(f"error: payload-dumper-go failed on {', '.join(parts)}:\n{res.stderr.strip()}")
            return sorted(p.name for p in out.iterdir())
        for name in sorted(n for n in names if wanted(n, fs_partitions)):
            zf.extract(name, out)
    return sorted(p.name for p in out.iterdir())


def strings_of(data: bytes) -> dict[str, str]:
    found = {}
    for label, pattern in VERSION_PATTERNS:
        if m := re.search(pattern, data):
            value = (m[1] if m.re.groups else m[0]).decode(errors="replace").strip()
            # A kernel banner names the person who built it: (george@ubuntuT430). Keep the version, not the login.
            found[label] = re.sub(r" \([^()\s]+@[^()\s]+\)", "", value) if label == "kernel" else value
    return found


def describe_one(path: Path) -> dict:
    kind = formats.detect(path)
    size = path.stat().st_size
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(8 << 20):
            sha.update(chunk)
    info: dict = {"format": formats.NAMES.get(kind, "unknown"), "size": size, "sha256": sha.hexdigest(), "versions": {}}
    if size > MAX_SCAN:
        return info
    data = path.read_bytes()
    versions: dict[str, str] = {}
    if kind == "boot" and (header := formats.boot_header(data)):
        info["format"] += f" v{header['header_version']}"
        if "patch_level" in header:
            versions["os version"] = header["os_version"]
            versions["patch level"] = header["patch_level"]
        kernel = formats.decompress_kernel(header["kernel"])
        versions |= strings_of(kernel)
    elif kind == "vbmeta":
        # Property descriptors hold key\0value\0, e.g. com.android.build.boot.security_patch.
        for m in re.finditer(rb"com\.android\.build\.([\w.]+?)\.(security_patch|os_version)\x00([^\x00]{1,40})\x00", data):
            versions[f"{m[1].decode()} {m[2].decode().replace('_', ' ')}"] = m[3].decode(errors="replace")
    elif kind in ("dtb", "unisoc_dtb"):
        start = data.find(b"\xd0\x0d\xfe\xed")
        count = data.count(b"\xd0\x0d\xfe\xed")
        if start >= 0 and (model := formats.fdt_root_props(data[start:]).get("model")):
            versions["model"] = model
        versions["device trees"] = str(count)
    elif kind == "dtbo" and len(data) >= 20:
        versions["overlays"] = str(int.from_bytes(data[16:20], "big"))
    if kind != "boot":
        # Qualcomm firmware ELFs quote some unrelated Linux banner; a kernel only counts from a boot image.
        versions |= {k: v for k, v in strings_of(data).items() if k not in versions and not (k == "kernel" and kind == "elf")}
    info["versions"] = versions
    return info


def describe(folder: Path) -> dict[str, dict]:
    return {p.name: describe_one(p) for p in sorted(folder.iterdir()) if p.is_file()}


def write(folder: Path, dest: Path) -> None:
    (dest / "images.json").write_text(json.dumps(describe(folder) if folder.is_dir() else {}, indent=2) + "\n")


def load(fw_dir: Path) -> dict[str, dict] | None:
    f = fw_dir / "images.json"
    return json.loads(f.read_text()) if f.is_file() else None


def report(old: dict | None, new: dict | None) -> tuple[list[str], list[dict]]:
    """REPORT.md lines and facts.json rows: one per image, with its version strings."""
    title = ["## Images outside the filesystems", ""]
    if old is None or new is None:
        return title + ["- not recorded: extracted before fw.py read these images; re-extract to compare them", ""], []
    lines, facts = [], []
    for name in sorted(old.keys() | new.keys()):
        a, b = old.get(name), new.get(name)
        cur = b or a
        if not a:
            action = "added"
        elif not b:
            action = "removed"
        else:
            action = "unchanged" if a["sha256"] == b["sha256"] else "changed"
        va, vb = (a or {}).get("versions", {}), (b or {}).get("versions", {})
        parts = []
        for label in [*vb, *(k for k in va if k not in vb)]:
            if action == "changed" and va.get(label) != vb.get(label):
                parts.append(f"{label} `{va.get(label, '(none)')}` -> `{vb.get(label, '(none)')}`")
            else:
                parts.append(f"{label} `{(vb if label in vb else va)[label]}`")
        size = f"{cur['size'] / (1 << 20):.1f} MB"
        lines.append(f"- `{name}` ({cur['format']}, {size}): **{action}**" + ("; " + "; ".join(parts) if parts else ""))
        facts.append({"name": name, "action": action, "format": cur["format"],
                      "sha256_old": a and a["sha256"], "sha256_new": b and b["sha256"],
                      "versions_old": va, "versions_new": vb})
    return title + (lines or ["- none in this OTA"]) + [""], facts
