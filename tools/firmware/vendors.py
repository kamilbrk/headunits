"""Who made a firmware, for makers fw.py has no hand-written rules for.

KSW and ZXW are recognised from the display id and use fw.py's VENDOR_NAMESPACES. For anything else
the maker's identity comes from build properties and its app namespaces are computed from the
firmware itself: packages outside the platform and chip-maker prefixes in platform_packages.json,
grouped by their first two labels, kept when a namespace owns two or more of them or when it matches
the build's identity (ro.build.user, the manufacturer, the zip name).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path

DATA = json.loads(Path(__file__).with_name("platform_packages.json").read_text())
PLATFORM_PREFIXES = tuple(DATA["platform"])
SOC_PREFIXES = tuple(DATA["soc"])
GENERIC = set(DATA["generic_identity"])
# ro.product.fingerprint and ro.build.fingerprint are left out: cheap units copy another device's (the
# Unisoc s9863a claims rockchip/rk312x).
IDENTITY_KEYS = ("ro.build.user", "ro.product.manufacturer", "ro.product.vendor.manufacturer", "ro.product.brand",
                 "ro.product.vendor.brand", "ro.build.host")


# Second labels that belong to a country or registry rather than a maker: cn.com.maker, com.cn.maker.
REGISTRY = {"com", "co", "net", "org", "gov", "edu", "ac", "cn", "tw", "hk", "uk"}


def namespace(package: str) -> str:
    parts = package.split(".")
    return ".".join(parts[:3] if len(parts) > 3 and parts[1] in REGISTRY else parts[:2])


def is_platform(package: str) -> bool:
    return package == "android" or package.startswith(PLATFORM_PREFIXES + SOC_PREFIXES)


def identity_tokens(get: Callable[..., str], fw_id: str) -> dict[str, str]:
    """Lower-case words that could name the maker -> where each came from."""
    tokens: dict[str, str] = {}
    for key in IDENTITY_KEYS:
        value = get(key).lower()
        if len(value) >= 3 and value not in GENERIC:
            tokens.setdefault(value, key)
    for word in re.split(r"[^a-z]+", fw_id.lower()):
        if len(word) >= 3 and word not in GENERIC:
            tokens.setdefault(word, "the zip name")
    return tokens


def scan(fs: Path, read_info: Callable[[Path], dict], read_cert: Callable[[Path], str | None]
         ) -> tuple[list[tuple[str | None, str | None]], str | None]:
    """(package, signing cert) for every APK in an extracted tree, and the platform certificate (framework-res.apk's)."""
    apps = [(read_info(p).get("package"), read_cert(p)) for p in sorted(fs.rglob("*.apk"))
            if p.is_file() and not p.is_symlink()]
    return apps, next((cert for package, cert in apps if package == "android"), None)


def vendor_namespaces(apps: Iterable[tuple[str | None, str | None]], platform_cert: str | None,
                      get: Callable[..., str], fw_id: str, third_party: tuple[str, ...]) -> list[dict]:
    """The maker's namespaces as [{namespace, apps, platform_signed, reasons}], from (package, signing cert) pairs.

    A namespace shared by several apps counts only when one of them is signed like framework-res.apk, or the
    certificates are unknown: a third-party suite brings its own key, the maker's apps run as the platform.
    """
    by_ns: dict[str, dict[str, str | None]] = {}
    for package, cert in apps:
        if package and package != "?" and not is_platform(package) and not package.startswith(third_party):
            by_ns.setdefault(namespace(package), {})[package] = cert
    tokens = identity_tokens(get, fw_id)
    found = []
    for ns, packages in sorted(by_ns.items()):
        signed = sum(1 for c in packages.values() if platform_cert and c == platform_cert)
        reasons = []
        if len(packages) >= 2 and (signed or not platform_cert):
            reasons.append(f"{len(packages)} apps")
        if source := tokens.get(ns.split(".")[-1].lower()):
            reasons.append(f"matches {source}")
        if reasons:
            found.append({"namespace": ns, "apps": len(packages), "platform_signed": signed, "reasons": reasons})
    return found


def identity(get: Callable[..., str], namespaces: list[dict]) -> tuple[str, str]:
    """(vendor, platform) from build properties: the namespace that matches the build's identity, else the first
    non-generic manufacturer, brand or build user; the board platform, else the board or device."""
    matched = sorted((n for n in namespaces if any(r.startswith("matches") for r in n["reasons"])), key=lambda n: -n["apps"])
    vendor = matched[0]["namespace"].split(".")[-1] if matched else ""
    if not vendor:
        vendor = next((v for k in IDENTITY_KEYS[:5] if (v := get(k).lower()) and v not in GENERIC), "")
    platform = get("ro.board.platform", "ro.product.board", "ro.product.device")
    return slug(vendor), slug(platform)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def describe(namespaces: list[dict]) -> str:
    return ", ".join(f"`{n['namespace']}` ({'; '.join(n['reasons'])})" for n in namespaces) or "none found"
