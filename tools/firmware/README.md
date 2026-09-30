# Firmware tools

`fw.py` unpacks KSW / ZXW OTA zips and reports what changed between two of
them. It replaces `public/script.sh`: no `sudo`, no macFUSE, no compiled
`ext4fuse`, and it decompiles only the apps that actually changed.

## Install

macOS (Homebrew):

```sh
brew install uv payload-dumper-go e2fsprogs jadx ripgrep
brew install erofs-utils   # only for firmwares that ship EROFS partitions
```

Debian / Ubuntu / WSL:

```sh
sudo apt install e2fsprogs erofs-utils openjdk-21-jre git ripgrep
# plus uv (https://docs.astral.sh/uv/), payload-dumper-go and jadx from their GitHub releases
```

Anywhere with Docker:

```sh
docker build -t headunits-fw tools/firmware
alias fw='docker run --rm --user "$(id -u):$(id -g)" -v ~/Dev/firmwares:/fw -e FW_WORK=/fw/_work headunits-fw'
```

`uv` fetches the two Python dependencies (`brotli`, `pyaxmlparser`) on first
run; nothing is installed globally.

## Use

Output goes to `~/Dev/firmwares/_work` unless `FW_WORK` says otherwise.

```sh
tools/firmware/fw.py extract ~/Dev/firmwares/zxw\ gt7/*.zip
tools/firmware/fw.py frontmatter 20250718GT_KSW        # paste into src/data/updates/...
tools/firmware/fw.py diff 20250325GT_KSW 20250718GT_KSW
tools/firmware/fw.py score 20250325GT_KSW 20250718GT_KSW  # vs src/data/updates/.../20250718GT_KSW.md
```

`extract` writes `<id>/fs/<partition>/`, `<id>/manifest.tsv` (every file's
hash or symlink target) and `<id>/meta.json` (vendor, platform, Android
version, build date, zip hashes). About a minute per firmware and ~5 GB of
disk each.

`diff` writes `diffs/<old>..<new>/`:

- `REPORT.md`, which opens with **Highlights**: new theme ids and names, new
  and renamed UI labels, factory config keys, settings keys, system
  properties, screen types, model names, media extensions, new layouts and
  resource folders, manifest changes, Android `config_*` values and factory
  defaults. All of it is pattern matching over the diffs and the apps' dex
  string tables, so it needs no model. After that come build properties,
  vendor and Android apps with versions and *what* changed inside each, JARs,
  and files. Files rebuilt on every build (`.odex`, `.vdex`, `build.prop`) and
  APKs that were only re-signed are left out.
- `facts.json`: the highlights as data.
- `files/text.diff`: unified diff of every changed text file (XML, `.rc`,
  configs), including `zxw_factory_config.xml`.
- `apps/<name>.code.diff` / `.resources.diff`: decompiled vendor code and
  resources for each changed vendor or Android app and JAR. Third-party
  preinstalls (TingCar, Kugou...) get a version line only. Library code,
  translations and binaries are only counted. Decompiled trees are cached
  under `<id>/src/`; jadx gives up on one app after 20 minutes.

`score` checks a hand-written changelog against the report: the share of its
`identifiers`, "labels" and version numbers that the report finds, which ones
only the diffs contain, which were already in the old firmware (context rather
than changes), and which appear nowhere.

The diffs are plain `git diff` output. To browse one side by side, point a
diff tool at the two cached trees, e.g.
`git difftool --dir-diff --no-index <old>/src/<apk> <new>/src/<apk>` or
`code --diff`.
