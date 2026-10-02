# Generalising fw.py beyond KSW/ZXW

How `fw.py` could find meaningful changes in other Android units (Unisoc,
Rockchip, MediaTek, Allwinner, Amlogic head units, phones, TV boxes) and in
non-Android embedded Linux (routers, cameras, IoT). The design keeps the
current shape: unpack to a plain directory tree, write a manifest, diff two
manifests, then spend effort only on the files that matter.

## 1. Formats: detect by magic, unpack with a pinned tool

Detection must never trust the file name. Read the first few KB and match
magic bytes, then recurse into whatever comes out (a zip holding a sparse
image holding `super` holding ext4 is normal).

### Android containers

| Format | Magic (offset) | Unpacker | Python / Docker |
|---|---|---|---|
| OTA payload | `CrAU` (0) | payload-dumper-go (already used) | Go binary; Docker trivial |
| Block OTA | `*.transfer.list` + `*.new.dat(.br)` | built in (`sdat2img`) | stdlib + brotli |
| Sparse image | `3a ff 26 ed` (0) | simg2img, or ~60 lines of stdlib | stdlib port easy |
| `super.img` (dynamic partitions) | `67 44 6c 61` "gDla" (4096) | lpunpack, or ~150 lines of stdlib | stdlib port easy |
| ext2/3/4 | `53 ef` (1080) | debugfs (already used) | e2fsprogs, brew/apt |
| EROFS | `e2 e1 f5 e0` (1024) | fsck.erofs (already used) | erofs-utils, brew/apt |
| Boot / recovery | `ANDROID!` (0) | AOSP `unpack_bootimg.py` | single Python file |
| vendor_boot | `VNDRBOOT` (0) | AOSP `unpack_bootimg.py` | single Python file |
| vbmeta | `AVB0` (0) | `avbtool info_image` | single Python file |
| DTBO table | `d7 b7 ab 1e` (0) | `mkdtboimg.py dump`, then `dtc -I dtb` | Python + dtc (brew) |
| Unisoc PAC | UTF-16LE version string, e.g. `BP_R1.0.0` (0) | pacextractor (C) or a stdlib port | small format, port it |
| Unisoc signed blob | `DHTB` (0) | strip 512-byte header, then strings | stdlib |
| Unisoc DTB bundle | `SPRD` (0) | table of FDTs, split on `d0 0d fe ed` | stdlib |
| Unisoc modem | `SCI1` (0) | treat as opaque; hash + version strings | stdlib |
| Rockchip update.img | `RKFW` (0), inner `RKAF` | afptool / img_unpack (rkbin, C) | simple table, port it |
| Allwinner LiveSuit | `IMAGEWTY` (0) | awimage or OpenixCard (C/C++) | builds on macOS/Linux |
| MediaTek image | `88 16 88 58` (0), 512-byte header | strip header; scatter file lists the rest | stdlib |
| Amlogic burn image | `56 19 b5 27` (0), verify on a sample | aml_image_v2_packer, or Python aml-imgpack | pip or binary |
| Huawei UPDATE.APP | `55 aa 5a a5` (92) | splituapp | single Python file |
| Samsung | `.tar.md5`, inner `.lz4` | tar + lz4 | stdlib tar, lz4 via pip |

### Embedded Linux containers

| Format | Magic (offset) | Unpacker | Python / Docker |
|---|---|---|---|
| SquashFS | `hsqs` LE / `sqsh` BE (0) | unsquashfs; sasquatch for vendor-patched LZMA | brew `squashfs`; sasquatch in unblob image |
| UBI | `UBI#` (0 of each erase block) | ubireader (`ubireader_extract_files`) | pip `ubi_reader`, pure Python |
| UBIFS | `31 18 10 06` (0) | ubireader | pip |
| JFFS2 | `85 19` LE / `19 85` BE (0) | jefferson | pip `jefferson` |
| cpio (initramfs) | `070701` / `070702` / `070707` (0) | bsdtar or `cpio -idm` | macOS ships bsdtar |
| CramFS | `45 3d cd 28` (0) | cramfsck, 7z | unblob image |
| YAFFS2 | none; heuristic on OOB layout | yaffshiv (inside unblob) | unblob image |
| U-Boot legacy uImage | `27 05 19 56` BE (0) | dumpimage, or parse the 64-byte header | brew `u-boot-tools`; header is stdlib |
| FIT image | `d0 0d fe ed` (0) with `/images` node | `dumpimage -l`, `dumpimage -T flat_dt -p N` | u-boot-tools; pip `fdt` |
| Broadcom TRX | `HDR0` (0) | unblob / binwalk | Docker |
| Compression | gzip `1f 8b`, xz `fd 37 7a 58 5a 00`, zstd `28 b5 2f fd`, lz4 `04 22 4d 18`, bzip2 `BZh`, lzma `5d 00 00` | stdlib (gzip, lzma, bz2) + pip zstandard, lz4 | pip |

### Generic carvers, as a fallback only

- **unblob** (pip `unblob`, but it shells out to ~20 native extractors, so use
  the Docker image `ghcr.io/onekey-sec/unblob`, pinned by digest). Best for
  router/camera blobs with vendor headers. Measured below: it does not
  understand Android boot images and just carves them into chunks.
- **binwalk v3** (Rust, `brew install binwalk` or `cargo install binwalk`,
  also Docker). Good at signature scanning (`binwalk -E` for entropy, which
  shows encrypted firmware at once). Extraction quality below unblob.
- Rule: run a known unpacker when the magic matches; call a carver only for
  a blob no rule matched, and record "carved" in the manifest so its diffs
  are read with suspicion.

### Pinning

- Python tools: pin in the PEP 723 header (`ubi_reader==x`, `jefferson==x`).
- Native tools: pin by Docker image digest in `tools/firmware/Dockerfile`; on
  macOS rely on brew and print the version into `meta.json` so a changed
  tool version explains a changed diff.
- Prefer a stdlib port for the small Android formats (sparse, super, PAC,
  DHTB, boot header, RKAF, MTK header). Each is a fixed header plus a table
  and costs less than managing another binary.

## 2. Deciding what is "vendor" without `VENDOR_NAMESPACES`

Score each APK (or file) on several signals and sort into four tiers:
**platform** (AOSP/GMS), **SoC** (Unisoc, MediaTek, Qualcomm, Rockchip,
Allwinner layer), **OEM** (the unit maker, decompile and diff in full),
**third-party preload** (version only, never decompile).

Signals, strongest first:

1. **Not in a platform baseline.** Keep a shipped list of package names in
   AOSP + GMS per Android version (taken once from a GSI of each version),
   plus a list of SoC prefixes (`com.sprd`, `plugin.sprd`, `addon.sprd`,
   `com.unisoc`, `com.spreadtrum`, `com.mediatek`, `com.rockchip`,
   `com.softwinner`, `com.amlogic`, `com.qualcomm`, `com.qti`). Anything
   outside both is OEM or third-party.
2. **Namespace shared by several apps.** A prefix (first two labels) owning
   two or more non-baseline apps is almost always the OEM. On the s9863a
   unit `com.george` owns 10 apps; nothing else non-baseline owns more
   than 2.
3. **Namespace matches build identity.** Compare prefixes with
   `ro.build.user`, `ro.build.host`, `ro.product.manufacturer`,
   `ro.product.brand` and the zip name. On s9863a `ro.build.user=george`
   and the zip says `ota-eng.george`, matching `com.george`.
4. **Signed with the platform key and not in the baseline.** The platform
   certificate is the one on `framework-res.apk`. Measured on s9863a: all
   OEM apps, all SoC plugins and even the Adups FOTA client are signed with
   the platform key (85 APKs share it). So "differs from platform cert"
   does *not* find OEM code; it finds third-party preloads (Mapgoo,
   AutoNavi, Tencent, NetEase: each has its own cert). Platform-signed and
   not in the baseline is the highest-risk set, because it runs with system
   privileges.
5. **Frequency across the corpus.** A package present in firmwares from
   several unrelated vendors is platform or a common preload; one seen only
   in one vendor's line is OEM. Cheap once there are 3+ vendors in `_work`.
6. **Location.** `/vendor/app`, `/product/app`, `/odm/app`, `/system_ext`
   hint at non-AOSP code on Treble-clean builds. Weak on cheap units: on
   s9863a every OEM app sits in `/system/app`, `/system/priv-app`,
   `/system/preloadapp` or `/system/multimedia/OEM`, while `/vendor/app`
   holds only SoC test tools. Use as a tie-breaker only.

`VENDOR_NAMESPACES` then becomes a per-firmware computed list stored in
`meta.json`, with the hand-written list kept as an override for KSW/ZXW.

### Non-Android

- **Owned by a package manager.** Parse `/usr/lib/opkg/status` or
  `/var/lib/opkg/status` (OpenWrt), `/var/lib/dpkg/status` (Debian-based),
  `/var/lib/rpm` (rare). Every file listed there has an upstream name and
  version; everything else is vendor or build-system output.
- **BusyBox applets.** Symlinks to `busybox` are upstream; a real binary in
  `/bin`, `/sbin`, `/usr/bin`, `/usr/sbin` that is not a BusyBox applet and
  not package-owned is vendor code.
- **Buildroot images** have no package DB. Fall back to a known-files list
  from a stock Buildroot/OpenWrt build of the same version, or to
  frequency across the corpus.
- **Always-vendor locations:** web UI (`/www`, `/web`, `/htdocs`,
  `/usr/www`, `cgi-bin`, `*.lua` under `luci`), init scripts
  (`/etc/init.d`, `/etc/rc.d`, `/etc/inittab`, `/etc/rcS`), `/opt`,
  `/app`, `/usr/local`, `/mnt/*` overlays, and any config tree named after
  the vendor.

## 3. Generic signals worth diffing on any Linux firmware

Each should produce a short list in `facts.json`, so the report stays
deterministic and small.

| Signal | Where | How (free tools) |
|---|---|---|
| Startup services | Android `*.rc`; `/etc/init.d`, `inittab`, systemd units, `procd` | text diff; list `service` names, `exec` lines, `class`, `user root` |
| Scheduled jobs | `/etc/crontab`, `/etc/crontabs/*`, `/var/spool/cron` | text diff |
| Accounts | `/etc/passwd`, `/etc/shadow`, `/etc/group` | flag new users, UID 0 accounts, empty or changed hashes (never print hashes) |
| Keys and certs | `*.pem`, `*.crt`, `*.key`, `cacerts/`, `authorized_keys`, dropbear/ssh host keys | hash + subject/issuer via `openssl x509`; flag private keys shipped in the image |
| Listening services | `telnetd`, `dropbear`, `sshd`, `adbd` props (`ro.adb.secure`, `ro.debuggable`), inetd | grep init + props; binaries present |
| Hard-coded hosts | URLs, IPs, MQTT/HTTP endpoints in configs and binaries | `strings` + regex, diff the set; the existing highlight code already does this for APKs |
| setuid / capabilities | mode bits; Android `fs_config` | the manifest already walks every file; add mode |
| SELinux | `sepolicy`, `*_contexts` | text diff; flag new `permissive` domains |
| Kernel | `Linux version` string in boot image or kernel; `/proc/config.gz` equivalent (`IKCFG_ST` marker) | `strings`; the config is gzip after the marker |
| Bootloader | U-Boot version string, env block (`bootcmd=`, `bootargs=`) | `strings`; diff the env |
| Security patch level | `ro.build.version.security_patch`, vendor equivalent | prop diff (already there) |
| ELF exports | every `.so` and executable | `nm -D --defined-only` (Apple `nm` reads ELF, measured: 480 symbols from `libcurl.so`); pip `pyelftools` for a pure-Python path |
| Library versions | `OpenSSL 1.`, `libcurl/7.`, `SQLite`, `BusyBox v1.` strings | `strings` + a small regex table; more useful on Android than an SBOM (see below) |
| SBOM | package DBs, binaries | `syft` (brew/Docker, free). Useful on OpenWrt/Debian images, nearly useless on Android |
| Known CVEs | the SBOM | `grype` or `osv-scanner` over the syft JSON (both free, brew/Docker); only as good as the version data |
| Deep code diff | a vendor binary that changed | radare2 `radiff2 -C` (brew, free) for function-level diffs; Ghidra headless only on demand, it is slow and heavy |

Keep the NOISE rule idea: build dates, fingerprints, `*.odex`, signature
files. For embedded Linux add `/etc/version`, `/etc/banner`, `*.pyc`,
`/lib/modules/*/modules.*` indexes.

## 4. Test: Unisoc SC9863A OTA

File: `/Volumes/tank-misc/CH MBP/Downloads/KSW/Firmwares/s9863a1h10__bmw02_2g-ota-eng.george_V3.0.2.zip`
(1.49 GB; it is under `Firmwares/`, not the `KSW/` root).

**Structure (read in place).** Signed block-based OTA, Android 9, build
`01_user_W19.11.5_P2_20220124`, `ro.board.platform=sp9863a`,
`ro.build.user=george`. It carries `system`, `vendor`, `product` as
`.new.dat.br` + `.transfer.list`, plus raw partitions written by the
updater script: `boot.img` (`ANDROID!`), `dtb.img` (`SPRD`), `dtbo.img`
(`d7b7ab1e`), `vbmeta.img` (`AVB0`), `u-boot.bin` / `u-boot-spl-16k.bin` /
`sml.bin` / `tos.bin` (all `DHTB`, Unisoc signed), `ltemodem.bin` (`SCI1`),
GNSS/WCN modems and an NV merge tool. `ro.build.fingerprint` claims
`rockchip/rk312x:6.0.1`, a spoof; the security patch is `2019-07-01` on a
January 2022 build.

**What worked (measured).**
- `fw.py extract` succeeded in 69 s: three ext4 partitions, 4473 files,
  151 APKs, 2.6 GB tree. Tree deleted afterwards.
- `fw.py frontmatter` ran and printed empty `vendor` and `platform`.
- `fw.py diff` of the build against itself ran cleanly in 21 s (the only
  code path available with one firmware; there is no second s9863a build).

**What breaks or is missed.**
- `vendor_platform()` only knows KSW/ZXW display ids, so vendor and
  platform are blank. A generic fallback would use
  `ro.product.manufacturer`/`ro.build.user` and `ro.board.platform`.
- `VENDOR_NAMESPACES` does not contain `com.george`, so the 10 OEM apps
  (`McuService`, `Launcher`, `CarSetting`, `Reversing`, `Auxin`,
  `license.client` ...) are not tiered as vendor and
  `worth_decompiling()` returns false for them; neither are the 13
  `plugin.sprd` / `addon.sprd` SoC apps. A real diff would list them as
  changed and never show code.
- `com.txznet` is in `VENDOR_NAMESPACES`, but here it is a third-party
  music preload (own certificate), so it would be decompiled needlessly.
- Everything outside the three filesystem partitions is ignored: kernel,
  U-Boot, TrustOS, modem and DTB changes are invisible. They are cheap to
  cover: hash each, and pull version strings. From this build:
  `Linux version 4.4.147+ (george@ubuntuT430) ... Jan 24 2022` straight
  from `boot.img` (kernel is uncompressed) and
  `U-Boot 2015.07-g6f15b2b-dirty (Jan 24 2022)` from `u-boot.bin`.
- Props-based identity must avoid `ro.build.fingerprint` (spoofed here).

**Generic tools tried.**
- **syft 1.52.0** (brew): 2.7 s over the tree, 46 packages, all framework
  JARs with version `UNKNOWN`; no ELF libraries recognised. Not worth
  running on Android; grype/osv-scanner would have nothing to match.
- **unblob 26.6.4** (Docker): bind mounts from the sandboxed shell failed
  with permission denied; piping the file into the container works. On
  `boot.img` it carved 7 chunks (unknown, gzip, an ELF) with no notion of
  the Android boot header. A 20-line header parser does better.
- Signing-cert probe (scratch script, pyaxmlparser + openssl): 85 APKs on
  the Unisoc platform key (`O=Zhantang`), 24 on Google or AOSP keys, the
  rest spread over other Unisoc keys and one certificate per third-party app. This is the evidence for section 2, point 4.

## 5. Order of work

1. Generic identity fallback in `vendor_platform()` from props, never the fingerprint (1 h).
2. Computed vendor tiers: baseline list + shared-namespace + build-user match + cert, stored in `meta.json` (half a day).
3. Hash and version-string every non-filesystem image in the OTA (boot, U-Boot, modem, DTB) into the report (2 h).
4. Magic-byte dispatcher with recursion, replacing name-based detection in `images_from_zip` (half a day).
5. Stdlib sparse + `super.img` + boot-header unpackers (half a day).
6. Generic signals pass: rc/init services, accounts, certs, hosts, setuid, SELinux, kernel version (1 day).
7. ELF export and library-version diff via `nm -D` and a regex table (half a day).
8. Embedded Linux: squashfs, UBI/UBIFS, JFFS2, cpio, uImage/FIT via pinned tools in the Dockerfile (1 day).
9. opkg/dpkg ownership and BusyBox applet split for non-Android vendor detection (half a day).
10. Unisoc PAC, Rockchip RKFW/RKAF, Allwinner IMAGEWTY, MTK header, Amlogic unpackers, each only when a real sample arrives (2 h each).
11. unblob Docker fallback for unmatched blobs, marked "carved" (2 h).
12. syft + grype/osv-scanner for embedded Linux images only (2 h).
