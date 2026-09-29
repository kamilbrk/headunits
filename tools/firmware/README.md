# Firmware tools

`fw.py` unpacks KSW / ZXW OTA zips and reports what changed between two of
them. It replaces `public/script.sh`: no `sudo`, no macFUSE, no compiled
`ext4fuse`, and it decompiles only the apps that actually changed.

## Install

macOS (Homebrew):

```sh
brew install uv payload-dumper-go e2fsprogs jadx
brew install erofs-utils   # only for firmwares that ship EROFS partitions
```

Debian / Ubuntu / WSL:

```sh
sudo apt install e2fsprogs erofs-utils openjdk-21-jre git
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
```

`extract` writes `<id>/fs/<partition>/`, `<id>/manifest.tsv` (every file's
hash or symlink target) and `<id>/meta.json` (vendor, platform, Android
version, build date, zip hashes). About a minute per firmware and ~5 GB of
disk each.

`diff` writes `diffs/<old>..<new>/`:

- `REPORT.md`: build property changes, apps added/removed/changed with
  versions and *what* changed inside each (code, resources, manifest, native
  libs), changed JARs, and added/removed/changed files. Files rebuilt on every
  build (`.odex`, `.vdex`, `build.prop`) and APKs that were only re-signed
  are left out.
- `files/text.diff`: unified diff of every changed text file (XML, `.rc`,
  configs), including `zxw_factory_config.xml`.
- `apps/<package>.diff`: decompiled-source diff for each changed app or JAR.
  Decompiled trees are cached under `<id>/src/`, so the next diff against the
  same firmware is quicker.

The diffs are plain `git diff` output. To browse one side by side, point a
diff tool at the two cached trees, e.g.
`git difftool --dir-diff --no-index <old>/src/<apk> <new>/src/<apk>` or
`code --diff`.
