"""Container formats inside OTA zips, detected by magic bytes rather than file names.

Plain-Python ports of the small Android ones: sparse images (simg2img), dynamic-partition
super images (lpunpack) and the boot image header (unpack_bootimg). Used by fw.py to turn
whatever a zip carries into raw filesystem images, and by images.py to read boot images.
"""

from __future__ import annotations

import shutil
import struct
import sys
from pathlib import Path

SPARSE_MAGIC = 0xED26FF3A
LP_GEOMETRY_MAGIC = 0x616C4467  # "gDla" at 4096
LP_METADATA_MAGIC = 0x414C5030  # "0PLA"
LP_SECTOR = 512
LP_RESERVED = 4096
LP_GEOMETRY_SIZE = 4096

# (offset, magic, name), checked in order; the first match wins.
MAGICS = (
    (0, b"\x3a\xff\x26\xed", "sparse"),
    (0, b"ANDROID!", "boot"),
    (0, b"VNDRBOOT", "vendor_boot"),
    (0, b"AVB0", "vbmeta"),
    (0, b"\xd7\xb7\xab\x1e", "dtbo"),
    (0, b"\xd0\x0d\xfe\xed", "dtb"),
    (0, b"DHTB", "unisoc_signed"),
    (0, b"SPRD", "unisoc_dtb"),
    (0, b"SCI1", "unisoc_modem"),
    (0, b"\x7fELF", "elf"),
    (0, b"\x27\x05\x19\x56", "uimage"),
    (0, b"\x1f\x8b", "gzip"),
    (0, b"\xfd7zXZ\x00", "xz"),
    (0, b"\x02\x21\x4c\x18", "lz4_legacy"),
    (0, b"\x04\x22\x4d\x18", "lz4"),
    (0, b"hsqs", "squashfs"),
    (0, b"UBI#", "ubi"),
    (0, b"RKFW", "rockchip_update"),
    (0, b"IMAGEWTY", "allwinner_image"),
    (0, b"\x88\x16\x88\x58", "mediatek_image"),
    (1024, b"\xe2\xe1\xf5\xe0", "erofs"),
    (1080, b"\x53\xef", "ext4"),
    (LP_RESERVED, struct.pack("<I", LP_GEOMETRY_MAGIC), "super"),
)
NAMES = {
    "sparse": "Android sparse image", "boot": "Android boot image", "vendor_boot": "Android vendor_boot image",
    "vbmeta": "AVB vbmeta", "dtbo": "DTBO table", "dtb": "device tree blob", "unisoc_signed": "Unisoc signed image",
    "unisoc_dtb": "Unisoc DTB bundle", "unisoc_modem": "Unisoc modem image", "elf": "ELF", "uimage": "U-Boot uImage",
    "gzip": "gzip", "xz": "xz", "lz4_legacy": "lz4", "lz4": "lz4", "squashfs": "SquashFS", "ubi": "UBI",
    "rockchip_update": "Rockchip update image", "allwinner_image": "Allwinner image", "mediatek_image": "MediaTek image",
    "erofs": "EROFS", "ext4": "ext4", "super": "dynamic partitions (super)",
}


def detect(path: Path) -> str | None:
    with path.open("rb") as fh:
        head = fh.read(LP_RESERVED + 4)
    for offset, magic, name in MAGICS:
        if head[offset:offset + len(magic)] == magic:
            return name
    return None


def unsparse(src: Path, dst: Path) -> None:
    """Expand an Android sparse image (simg2img)."""
    with src.open("rb") as fh, dst.open("wb") as out:
        magic, _major, _minor, file_hdr, chunk_hdr, block, total_blocks, chunks, _ = struct.unpack("<I4H4I", fh.read(28))
        if magic != SPARSE_MAGIC:
            raise ValueError(f"{src.name} is not a sparse image")
        fh.seek(file_hdr)
        for _ in range(chunks):
            kind, _, blocks, total = struct.unpack("<2H2I", fh.read(12))
            fh.seek(chunk_hdr - 12, 1)
            size = blocks * block
            if kind == 0xCAC1:  # raw
                remaining = size
                while remaining:
                    data = fh.read(min(remaining, 8 << 20))
                    if not data:
                        raise ValueError(f"{src.name} ended early")
                    out.write(data)
                    remaining -= len(data)
            elif kind == 0xCAC2:  # fill with a 4-byte pattern
                pattern = fh.read(4)
                if pattern == b"\0\0\0\0":
                    out.seek(size, 1)
                else:
                    chunk = pattern * (min(size, 8 << 20) // 4)
                    remaining = size
                    while remaining:
                        out.write(chunk[:remaining])
                        remaining -= min(remaining, len(chunk))
            elif kind == 0xCAC3:  # don't care
                out.seek(size, 1)
            elif kind == 0xCAC4:  # crc32 of what came before
                fh.seek(total - chunk_hdr, 1)
            else:
                raise ValueError(f"{src.name}: unknown sparse chunk type {kind:#x}")
        out.truncate(total_blocks * block)


def lp_partitions(super_img: Path) -> list[tuple[str, list[tuple[int, int]]]]:
    """(name, [(byte offset, byte length)...]) for each partition in a raw super image's first metadata slot.
    A zero extent has offset -1."""
    with super_img.open("rb") as fh:
        fh.seek(LP_RESERVED)
        magic, _size = struct.unpack("<2I", fh.read(8))
        if magic != LP_GEOMETRY_MAGIC:
            raise ValueError(f"{super_img.name} has no dynamic partition geometry")
        fh.seek(32, 1)  # checksum
        max_size, _slots, _block = struct.unpack("<3I", fh.read(12))
        base = LP_RESERVED + 2 * LP_GEOMETRY_SIZE
        fh.seek(base)
        head = fh.read(max_size)
    magic, _major, _minor, header_size = struct.unpack_from("<I2HI", head, 0)
    if magic != LP_METADATA_MAGIC:
        raise ValueError(f"{super_img.name} has no dynamic partition metadata")
    # header: magic, major, minor, header_size, sha256, tables_size, sha256, then four table descriptors.
    descriptors = [struct.unpack_from("<3I", head, 80 + 12 * i) for i in range(4)]
    tables = head[header_size:]
    (p_off, p_num, p_size), (e_off, e_num, e_size) = descriptors[0], descriptors[1]
    extents = []
    for i in range(e_num):
        sectors, target_type, target_data, source = struct.unpack_from("<QIQI", tables, e_off + i * e_size)
        if target_type == 0 and source != 0:
            raise ValueError(f"{super_img.name} spans several block devices; only single-device super images are supported")
        extents.append((target_data * LP_SECTOR if target_type == 0 else -1, sectors * LP_SECTOR))
    parts = []
    for i in range(p_num):
        raw_name, _attrs, first, count, _group = struct.unpack_from("<36s4I", tables, p_off + i * p_size)
        parts.append((raw_name.split(b"\0", 1)[0].decode(), extents[first:first + count]))
    return parts


def lpunpack(super_img: Path, out_dir: Path, wanted: list[str]) -> list[Path]:
    """Write the `wanted` partitions of a raw super image to out_dir/<name>.img (lpunpack).
    Virtual A/B images name them system_a/system_b: the first slot with data is used, without the suffix.
    A partition the zip also carries as its own image keeps that image."""
    written = []
    by_name: dict[str, list[tuple[int, int]]] = {}
    for name, extents in lp_partitions(super_img):
        base = name[:-2] if name.endswith(("_a", "_b")) else name
        if base in wanted and base not in by_name and extents and not (out_dir / f"{base}.img").exists():
            by_name[base] = extents
    with super_img.open("rb") as src:
        for name, extents in sorted(by_name.items()):
            dst = out_dir / f"{name}.img"
            with dst.open("wb") as out:
                for offset, length in extents:
                    if offset < 0:
                        out.seek(length, 1)
                        continue
                    src.seek(offset)
                    remaining = length
                    while remaining:
                        data = src.read(min(remaining, 8 << 20))
                        if not data:
                            raise ValueError(f"{super_img.name} ended inside partition {name}")
                        out.write(data)
                        remaining -= len(data)
                out.truncate(sum(length for _, length in extents))
            written.append(dst)
    return written


def normalise(img_dir: Path, wanted: list[str]) -> None:
    """Turn every *.img in img_dir into a raw filesystem image fw.py can unpack: expand sparse images and
    split super images into their partitions. Recurses, since a sparse image can hold a super image."""
    for _ in range(3):
        changed = False
        for img in sorted(img_dir.glob("*.img")):
            kind = detect(img)
            if kind == "sparse":
                print(f"  sparse: {img.name}")
                raw = img.with_suffix(".raw")
                unsparse(img, raw)
                raw.replace(img)
                changed = True
            elif kind == "super":
                try:
                    parts = lpunpack(img, img_dir, wanted)
                except ValueError as exc:
                    sys.exit(f"error: {exc}")
                if not parts and not any(p != img for p in img_dir.glob("*.img")):
                    sys.exit(f"error: {img.name} holds none of {', '.join(wanted)}")
                print(f"  super: {', '.join(p.stem for p in parts) or 'nothing the zip did not carry already'}")
                img.unlink()
                changed = True
        if not changed:
            return


def boot_header(data: bytes) -> dict | None:
    """Fields of an Android boot image header (versions 0-4): kernel bytes, os version and patch level, cmdline."""
    if data[:8] != b"ANDROID!":
        return None
    version = struct.unpack_from("<I", data, 40)[0]
    # Before Android 9 some makers put other fields at offset 40 (Qualcomm's dt_size), so only 3 and 4 count as new.
    if version in (3, 4):
        kernel_size, _ramdisk, os_version = struct.unpack_from("<3I", data, 8)
        page = 4096
        cmdline = data[44:44 + 1536]
    else:
        kernel_size = struct.unpack_from("<I", data, 8)[0]
        page, _, os_version = struct.unpack_from("<3I", data, 36)
        cmdline = data[64:64 + 512] + data[608:608 + 1024]
    info = {"header_version": version, "kernel": data[page:page + kernel_size],
            "cmdline": cmdline.split(b"\0", 1)[0].decode(errors="replace").strip()}
    if os_version:
        ver, patch = os_version >> 11, os_version & 0x7FF
        info["os_version"] = f"{ver >> 14}.{(ver >> 7) & 0x7F}.{ver & 0x7F}"
        info["patch_level"] = f"{2000 + (patch >> 4)}-{patch & 0xF:02d}"
    return info


def decompress_kernel(kernel: bytes) -> bytes:
    """The kernel image as plain bytes where stdlib (or an lz4 binary) can decompress it; otherwise as given.
    An arm zImage carries its gzip payload after a small decompressor, so look past the start too."""
    import lzma
    import subprocess
    import zlib

    if kernel[:2] == b"\x1f\x8b":
        # Not gzip.decompress: Image.gz-dtb carries device trees after the stream, which it rejects.
        try:
            return zlib.decompressobj(31).decompress(kernel)
        except zlib.error:
            pass
    if kernel[:6] == b"\xfd7zXZ\x00":
        try:
            return lzma.decompress(kernel)
        except lzma.LZMAError:
            pass
    if kernel[:4] in (b"\x02\x21\x4c\x18", b"\x04\x22\x4d\x18") and (lz4 := shutil.which("lz4")):
        res = subprocess.run([lz4, "-dc"], input=kernel, capture_output=True)
        if res.stdout:
            return res.stdout
    if b"Linux version " not in kernel:
        start = kernel.find(b"\x1f\x8b\x08\x00", 1, 1 << 20)
        if start > 0:
            try:
                return zlib.decompressobj(31).decompress(kernel[start:])
            except zlib.error:
                pass
    return kernel


def fdt_root_props(data: bytes, names: tuple[str, ...] = ("model", "compatible")) -> dict[str, str]:
    """String properties of a flattened device tree's root node."""
    if data[:4] != b"\xd0\x0d\xfe\xed":
        return {}
    _magic, _total, off_struct, off_strings = struct.unpack_from(">4I", data, 0)
    i, depth, props = off_struct, 0, {}
    try:
        while True:
            (token,) = struct.unpack_from(">I", data, i)
            i += 4
            if token == 1:  # begin node
                depth += 1
                i = (data.index(b"\0", i) + 4) & ~3
                if depth > 1:
                    return props  # the root's own properties come before its first child
            elif token == 3:  # property
                length, nameoff = struct.unpack_from(">2I", data, i)
                name = data[off_strings + nameoff:data.index(b"\0", off_strings + nameoff)].decode(errors="replace")
                if depth == 1 and name in names:
                    props[name] = ", ".join(s.decode(errors="replace") for s in data[i + 8:i + 8 + length].split(b"\0") if s)
                i = (i + 8 + length + 3) & ~3
            elif token in (2, 9):
                return props
            elif token != 4:
                return props
    except (struct.error, ValueError):
        return props
