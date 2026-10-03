# Firmware tools

`fw.py` unpacks KSW / ZXW OTA zips (and, with less detail, other makers'
Android OTAs) and reports what changed between two of them. It replaced the old `public/script.sh`: no `sudo`, no macFUSE, no compiled
`ext4fuse`, and it decompiles only the apps that actually changed.

## Install

macOS (Homebrew):

```sh
brew install uv payload-dumper-go e2fsprogs jadx ripgrep lz4
brew install erofs-utils   # only for firmwares that ship EROFS partitions
```

Debian / Ubuntu / WSL:

```sh
sudo apt install e2fsprogs erofs-utils openjdk-21-jre git ripgrep lz4
# plus uv (https://docs.astral.sh/uv/), payload-dumper-go and jadx from their GitHub releases
```

Anywhere with Docker:

```sh
docker build -t headunits-fw tools/firmware
alias fw='docker run --rm --user "$(id -u):$(id -g)" -v ~/Dev/firmwares:/fw -e FW_WORK=/fw/_work headunits-fw'
```

The image has no checkout of the site or analysis tree, so mount them and name
them: `fw sitecheck <diff> --site /site` with `-v "$PWD":/site`, and
`fw evaluate --analysis /fw/_analysis run`. Both stop with an error when the
folder is missing rather than checking against nothing. `fw draft` takes
`--site-data /site/src/data` the same way, but without it runs on silently
with no known theme names.

`uv` fetches the two Python dependencies (`brotli`, `pyaxmlparser`) on first
run; nothing is installed globally.

Versions the reports were checked against: jadx 1.5.6, payload-dumper-go
2.1.0, git 2.43, ripgrep 14.1, e2fsprogs 1.47.0, erofs-utils 1.7.1, Python
3.11. The Dockerfile pins jadx and payload-dumper-go by version and checksum
and the base image and uv by digest. A different jadx version decompiles
differently, so compare reports only when they come from the same one.

## Use

Output goes to `~/Dev/firmwares/_work` unless `FW_WORK` says otherwise.

```sh
tools/firmware/fw.py extract ~/Dev/firmwares/zxw\ gt7/*.zip
tools/firmware/fw.py frontmatter 20250718GT_KSW        # paste into src/data/updates/...
tools/firmware/fw.py diff 20250325GT_KSW 20250718GT_KSW
tools/firmware/fw.py score 20250325GT_KSW 20250718GT_KSW  # vs src/data/updates/.../20250718GT_KSW.md
tools/firmware/fw.py batch ~/Dev/firmwares/zxw\ gt7 ~/Dev/firmwares/ksw   # everything, pair by pair
tools/firmware/fw.py rules <diff-dir> --min-severity medium   # security and privacy findings
tools/firmware/fw.py sitecheck <diff-dir>                     # vs the site's themes, factory settings, frontmatter
tools/firmware/fw.py draft <diff-dir> -o draft.md             # site-format changelog draft
tools/firmware/fw.py evaluate run                             # recall against the analysed evidence files
```

`rules`, `sitecheck`, `draft` and `evaluate` read a finished diff folder and
take their own flags; `fw.py <subcommand> -h` lists them.

`extract` skips a firmware that is already extracted unless given `--force`,
and deletes the raw partition images once unpacked unless given
`--keep-images`. It writes `<id>/fs/<partition>/`, `<id>/manifest.tsv` (every file's
hash or symlink target), `<id>/meta.json` (vendor, platform, Android
version, build date, zip hashes) and `<id>/images.json` (see below). About a
minute per firmware and ~5 GB of disk each.

It takes OTA zips with `payload.bin`, block OTAs (`*.new.dat(.br)` +
`*.transfer.list`) and flash kits with `super.img` or plain `*.img`
partitions. Partitions are picked out of the zip by name, then typed by
their magic bytes: Android sparse images are expanded and `super.img` is split
into its partitions in plain Python (`formats.py`), then ext4 and EROFS are
unpacked as before. `batch` still skips `super.img` flash kits, since a KSW
kit would slot into its OTA line and change every pair after it; run
`extract` and `diff` on them by hand.

**Other makers.** KSW and ZXW are recognised from the display id. For any
other firmware the vendor and platform come from build properties
(`vendors.py`): the vendor is the app namespace that matches
`ro.build.user`, `ro.build.host`, the manufacturer, the brand or a word of the
zip name; failing that, the first of `ro.build.user`, manufacturer and brand
that is not a chip maker or a generic name (`sprd`, `alps`, `root`...). The
platform is `ro.board.platform`. The fingerprint is never used, since cheap units copy
another device's. `meta.json` then also carries `vendor_namespaces`: the
maker's app namespaces, computed from the firmware. A namespace qualifies
when, outside the AOSP, Google and chip-maker prefixes in
`platform_packages.json` and `THIRD_PARTY_PACKAGES`, it owns two or more apps
and one of them is signed with the platform key (or no platform key was
found), or when it matches the build identity. A namespace is the package's
first two labels, three under a registry label (`cn.com.maker`). On the Unisoc s9863a OTA that is `com.george` (10 apps, matches
`ro.build.user`). `diff` uses those namespaces in place of
`VENDOR_NAMESPACES` unless both firmwares are KSW or ZXW, and names them at
the top of "Vendor apps".

**Images outside the filesystems** (boot, dtb/dtbo, vbmeta, bootloaders,
trusted firmware, modems: every top-level `*.img`/`*.bin`/`*.mbn`/`*.elf`/`*.fv` in a block
OTA or flash kit, every non-filesystem partition in `payload.bin`) are hashed
into `images.json` with their format and version strings: the kernel's
`Linux version` (without the builder's `user@host`; gzip and xz kernels
decompressed in Python, lz4 through the `lz4` binary when installed), Android
version and patch level from the boot header,
`U-Boot 20xx.xx`, Arm trusted firmware and `Built:` stamps, Qualcomm
`QC_IMAGE_VERSION_STRING`, Unisoc modem `Platform Version`, per-partition
security patch from vbmeta, the device tree's `model`. `images.json` stays
when the tree is freed. `diff` lists every image in "Images outside the
filesystems" as added, removed, changed or unchanged, with old -> new for any
version string that moved; a firmware extracted before this existed says
"not recorded".

`diff` writes `diffs/<old>..<new>/`:

- `REPORT.md`, which opens with **Highlights**: new theme ids and names, new
  and renamed UI labels, factory config keys, settings keys, system
  properties, screen types, model names, media extensions, new layouts and
  resource folders, manifest changes, Android `config_*` values and factory
  defaults. Per app, from its own code and layouts: settings, SharedPreferences
  and system property keys it starts or stops using, new constants and enum
  values, view ids added to existing layouts, views shown, hidden or
  relabelled, and changed string arrays. From the changed lines of its own
  code: the literals, constants and theme checks its conditions start or stop
  testing, the intent actions, extras and components it starts or stops
  using, and the settings and property keys passed on changed lines. Then the
  changed lines of shell scripts and init `.rc` files, and native binaries
  whose strings changed (or that were only rebuilt). All of it is pattern
  matching over the decompiled trees, the apps' dex string tables, the diffs
  and the ELF string tables, so it needs no model. After that come build properties,
  vendor and Android apps with versions and *what* changed inside each, JARs,
  and files. Files rebuilt on every build (`.odex`, `.vdex`, `build.prop`) and
  APKs that were only re-signed are left out.
- `facts.json`: the highlights as data.
- `files/text.diff`: unified diff of every changed text file (XML, `.rc`,
  configs), including `zxw_factory_config.xml`.
- `apps/<name>.code.diff` / `.resources.diff`: decompiled vendor code and
  resources for each changed app and JAR that is not third-party. Library
  code, translations and binaries are only counted. Decompiled trees are
  cached under `<id>/src/`; jadx gives up on one app after 20 minutes.

Each app falls in one group, shown in `facts.json` and, for third-party and
unrecognised apps, in the report's app line:

- **third-party**: its package is on `THIRD_PARTY_PACKAGES` (Google, Kugou,
  TingCar, MX Player...), or it is not a vendor or stock package and is not
  signed with the same certificate as `framework-res.apk`. Version line only,
  not decompiled.
- **vendor**: a package under `VENDOR_NAMESPACES` (`com.wits`, `com.szchoiceway`,
  `com.zjinnova`...). Listed under "Vendor apps". The certificate is not
  checked for these: ZLink carries its own key on KSW units.
- **stock**: AOSP and chip-maker packages (`com.android.`, `com.qualcomm.`,
  `com.mediatek.`...). AOSP signs its apps with several keys, so the
  certificate is not checked for these either.
- **unrecognised**: everything else, decompiled. On KSW and ZXW a new
  maker's namespace shows up here first; add it to `VENDOR_NAMESPACES`.
  Other makers' namespaces are computed (see above).

The string highlights (system properties, paths, URLs, package names, intent
actions) come from the apps' dex string tables. A string that only classes
under `LIBRARY_PACKAGES` load (blankj utilcode, androidx, Google, okhttp,
Tencent, Umeng...) is left out, so a bundled library's list of ROM version
properties is not reported as the vendor's. `score` still uses every string.

The per-app code and layout rows compare the app's whole old tree with its
whole new tree, not diff lines, so a key or constant that only moved between
classes is not new. They skip library classes (`LIBRARY_PACKAGES`),
build-generated ones (`BuildConfig`, data binding's `BR` and mapper), logging
tags, AIDL transaction codes, inlined resource ids, and apps added without a
predecessor. A key passed as a constant is resolved through the app's own
declarations. The strings of a stock app added whole (an AOSP app the
vendor started shipping) are counted in one line instead of listed.

The rows from changed code lines work the other way round: they read
`apps/*.diff`, and a term counts as added when a `+` line of the app's own
code carries it and no `-` line of the same kind (condition, intent call, key
call) anywhere in that app does, so code that moved between classes cancels
out. They catch a known key or theme newly tested in
one more place, which the whole-tree rows cannot. Files added or removed
whole are skipped (every line in them is new), and so are generated classes,
obfuscated ones (`a.java`), logging calls, literals that are a single
plain word (`"status"`), names any Java code has (member fields such as
`mPageIndex`, `data1`, `keyCode`, charset names) and Java's own constants
(`Integer.MIN_VALUE`, `Build.VERSION.SDK_INT`). A term the report already
names elsewhere is not repeated, and each app shows at most 40 added and
40 removed; all are in `facts.json`. Intent and key terms come from the call's own arguments, and a
theme check from a static call on a `...Theme...` / `...UI...` class. A
script line whose only change is a checksum (the recovery image hash in
`install-recovery.sh`) is left out. Native
binaries are compared by their name-like strings (symbols, snake_case or
camelCase names, dotted keys, paths, `%s` formats; no spaces), with dates,
build stamps and hashes left out, and so are names the toolchain links in
(`__cxa_*`, fortified `__*_chk`, `pthread_*`, stdio `*_unlocked`, symbol
version tags, C++ standard library and Chromium `base` symbols, mangled or
as typeinfo); the vendor's own mangled names stay. Those with the fewest
changes come first, since a handful of new symbols is a feature and
thousands are an upstream rebuild.
Manifest rows leave out what the build merges in from Jetpack
(`androidx.profileinstaller`, `androidx.startup`,
`*.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`); any other SDK's components
(Firebase, Play services, blankj) stay.

Two runs over the same trees give byte-identical output: every list is
sorted, and jadx runs single-threaded with `--no-finally`, since jadx 1.5.6
otherwise decompiles some methods differently from run to run. Parallelism
comes from `--jobs` (apps decompiled at once) instead.

`batch` takes folders of OTA zips (or zips) and, for each product line, diffs
every build against the one before it:

- The build date and line come from the zip's `META-INF/com/android/metadata`
  without unpacking (`post-timestamp`; the line from KSW's id, such as
  `R-M600`, or else `pre-device`, such as `GT7-CAR`). A zip without that date
  is extracted to read it. Zips without a system partition fw.py can read
  (persist backups) and `super.img` flash kits are skipped.
- A letter suffix on the version starts a line of its own (`R-M600 NEXAI`),
  whose first build is compared with the latest earlier build of the base line.
- A pair whose `diffs/<old>..<new>/frontmatter.md` exists is skipped, so a
  stopped batch resumes where it left off. A pair that fails is noted and
  the batch moves on.
- Each finished pair also gets `frontmatter.md` and, when the site has a page
  for the new firmware, `score.txt`.
- Extracted trees are deleted (`fs/`, `src/`, `img/`; `meta.json` and
  `manifest.tsv` stay) once no remaining pair needs them, and the batch stops
  before an extraction that would start below `--min-free-gb` (25).
- `diffs/INDEX.md` lists every pair with its build date, the site releases
  between the two builds that were never downloaded, the site page's bullet
  count and the number of highlights.

`batch --dry-run` lists the pairs without extracting anything. A zip with no
date in its metadata that was never extracted is listed with date 0, so its
place in the order is only known after a real run extracts it.

### facts.json

The highlights as data, for scripts that read a diff without parsing
REPORT.md. Every top-level key is always present, and every list comes in a
fixed order (sorted, or in app and file order).

| Key | Contents |
|---|---|
| `old`, `new` | `meta.json` of each side without signatures: `id`, `vendor`, `platform`, `android`, `date`, `display_id`, and `vendor_namespaces` for makers other than KSW/ZXW |
| `vendor_namespaces` | `source` (`VENDOR_NAMESPACES` or `computed`) and the `namespaces` the diff treated as vendor |
| `images` | per image outside the filesystems: `name`, `action`, `format`, `sha256_old`, `sha256_new`, `versions_old`, `versions_new` |
| `apps` | one object per added, removed or changed app: `key`, `package`, `action`, `name`, `path`, `old_path` (moved from, or the removed app it was diffed against), `version_old`, `version_new`, `kinds`, `group`, `is_vendor`, `decompiled` (false for third-party apps and when jadx failed) |
| `build_props` | changed build properties: `file`, `key`, `old`, `new` |
| `decompiled` | per decompiled app or JAR: `code_files`, `code_lines`, `resources_files`, `resources_lines`, `diff_file`, `large_files`, or `failed` |
| `build` | `ro.build.display.id`, `.type`, `.user`, `.version.security_patch`, `.version.sdk`: `old`, `new` |
| `themes`, `themes_removed` | theme id constants (`UI_NUM_KSW_X = 41`) |
| `theme_sources` | per added theme id: the `app: source file` lines that define it |
| `theme_strings`, `theme_strings_by_app`, `theme_strings_removed`, `theme_strings_before` | theme names from `UiThemeUtils.java`; `_before` is every name the old build had |
| `props`, `settings_keys`, `theme_names`, `models`, `files`, `packages`, `intents`, `urls`, `config_keys`, `screens` | dex string highlights: `added`, `removed` |
| `jar_props` | per JAR: system properties it reads for the first time |
| `native_libs`, `native_libs_removed` | `.so` files added to or removed from app folders |
| `executables` | `added`, `removed` under `bin/`, `sbin/`, `xbin/` |
| `media_extensions` | extensions added to media file lists |
| `strings`, `strings_removed` | UI strings: `name`, `text`, `apps` |
| `code_settings_keys`, `code_prefs_keys`, `code_props`, `code_enums` | per app: `added`, `removed` keys its own code passes to `Settings.System/Global/Secure` (and KSW's `getSettingsInt` / `SysProviderOpt` wrappers), `SharedPreferences`, `SystemProperties` (and `getprop`/`setprop` strings); enum values as `Enum.VALUE` |
| `code_constants` | per app: `static final` constants in its own code as `NAME = value`: `added`, `removed`, `changed` (`NAME: old -> new`) |
| `view_ids` | per app: layout name -> ids added to a layout the app already had |
| `layout_labels` | per app: existing `@string` labels newly used in its layouts |
| `layout_variants` | per app: `folder/layout` files for a layout it already had in another folder |
| `layout_views` | per app: views whose `visibility` or `@string` text changed: `view` (`folder/layout: id`, or `Tag around <first named child>`), `attribute`, `old`, `new` |
| `arrays` | per app: `values/` arrays that changed or are new: `name`, `added`, `removed` items (`@string` resolved) |
| `strings_changed` | UI strings whose text changed: `app`, `name`, `old`, `new` |
| `resource_dirs`, `resource_dirs_removed`, `layouts`, `layouts_removed` | per app: resource folders and layouts |
| `languages`, `languages_removed` | per locale: apps |
| `manifest` | per app: `added`, `removed` (permissions, components, actions, meta-data names), `flags_added`, `flags_removed` |
| `android_config` | Android `config_*` values: `app`, `key`, `old`, `new` |
| `config_files` | key=value config files: `path`, `key`, `old`, `new` |
| `factory_settings` | per factory config XML: `file`, `file_added`, `added`, `removed`, `changed` (`key`, `old`, `new`) |
| `script_changes` | per changed `.sh` / `.rc` file both sides carry: `path`, `added`, `removed` lines |
| `native_strings` | per changed ELF file both sides carry whose name-like strings changed: `added`, `removed`, or `added_count`, `removed_count` past 300 changes |
| `native_rebuilt` | changed ELF files whose name-like strings did not change, or only in toolchain symbols: `count`, and the first 100 `paths` |
| `code_terms` | `conditions`, `intents`, `keys`, each per app: `added`, `removed` terms on changed lines of its own code |

`score` checks a hand-written changelog against the report: the share of its
`identifiers`, "labels" and version numbers that the report finds, which ones
only the diffs contain, which were already in the old firmware (context rather
than changes), and which appear nowhere.

The diffs are plain `git diff` output. To browse one side by side, point a
diff tool at the two cached trees, e.g.
`git difftool --dir-diff --no-index <old>/src/<apk> <new>/src/<apk>` or
`code --diff`.
