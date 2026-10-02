---
name: firmware-diff
description: Analyse one or more new head-unit firmware OTA zips (KSW, ZXW or another maker) and write a site-format changelog plus an evidence file, spending as few tokens as possible. Use when the owner hands you new firmware zips, asks what changed between two builds, or asks for a changelog or evidence for a firmware release.
---

# Firmware diff

The scripts do the finding; you only judge what they cannot phrase. Never read a
whole diff. Every claim you write must rest on a line you read in a diff.

## Where things are

- Tool: `tools/firmware/fw.py` (subcommands `extract`, `frontmatter`, `diff`,
  `score`, `batch`, `rules`, `sitecheck`, `draft`, `evaluate`). Full reference:
  `tools/firmware/README.md`. Run `fw.py <subcommand> -h` rather than guessing flags.
- Work folder: `~/Dev/firmwares/_work` (or `FW_WORK`). A diff lands in
  `_work/diffs/<old>..<new>/` with `REPORT.md`, `facts.json`, `files/text.diff`
  and `apps/<name>.code.diff` / `.resources.diff` (big apps are split into
  `apps/<name>/<file>.diff` or `.code.large.diff`).
- Finished analyses to copy the style from:
  `~/Dev/firmwares/_analysis/<vendor>/<platform>/<id>/claude.md` and
  `claude.evidence.md`, for example `_analysis/zxw/gt6/20241129GT_KSW/`.

## Steps

1. Diff. For several zips: `tools/firmware/fw.py batch --dry-run <folder-or-zips>`
   to see the pairs, then the same without `--dry-run`. It pairs each build with
   the one before it in its line, resumes if stopped, and writes
   `_work/diffs/INDEX.md` (which site releases between the two builds were never
   downloaded). For one pair: `fw.py extract <old.zip> <new.zip>`, then
   `fw.py diff <old-id> <new-id>`. Extraction needs about 5 GB per build.
2. For each `<diff>` folder run the three checkers and save their output there:
   - `tools/firmware/fw.py rules <diff> --min-severity medium > <diff>/rules.md`
   - `tools/firmware/fw.py sitecheck <diff> > <diff>/sitecheck.md`
   - `tools/firmware/fw.py draft <diff> --frontmatter <diff>/frontmatter.md -o <diff>/draft.md`
     (in the `_analysis` layout, leave `--frontmatter` off; it finds
     `frontmatter.generated.md` itself).
   - If the site already has a page for the new build, also
     `fw.py score <old-id> <new-id>` for the "vs hand-written" section.
3. Read only these:
   - `draft.md`: the `#### Summary` and `#### Changes` bullets are already
     mechanical and usually right; skim them. Work through `#### Needs a human`.
   - `rules.md`: the High and Medium findings. Each cites
     `apps/<file>.diff (<source file>):<line>`; the line number is a line of the
     diff file.
   - `sitecheck.md`: themes and factory keys the site lacks, frontmatter mismatches.
4. For each item worth a claim, jump to the hunk: `rg -n '<identifier>' <diff>/apps/<app>.code.diff`,
   then read about 40 lines around the hit (Read with offset and limit). Follow a
   call to its caller with another `rg`, not by scrolling.
5. Write `claude.md` and `claude.evidence.md` in the diff folder, beside `REPORT.md`
   (in the `_analysis` layout, beside `diff/`).

## claude.md (site format)

Frontmatter from `draft.md` unchanged, then `#### Summary` (3 to 5 bullets, the
changes a reader cares about) and `#### Changes` (one bullet per change). Plain
English, user-visible effect first, identifiers in backticks, UI labels in
double quotes. Follow the site conventions in `AGENTS.md`:

- Write firmware ids and theme ids as plain backticked text
  (`` `KSW_BENZ_VITO` ``, `` `Ksw-T-M600_OS_v1.4.8-ota` ``); the site links them.
  Do not hand-write glossary links either.
- Other links are root-relative without the base path:
  `[zxw_factory_config.xml](/factory-settings/zxw)`. Never write `/headunits/`.
- If the pair skips site releases, the first Summary bullet says so and names them.

## claude.evidence.md

- A header naming the diff root, the new tree, and the skipped releases.
- A table: `# | Bullet | Evidence file | Short quote | Confidence | How found`.
  The quote is copied from a `+` or `-` line of the diff. Confidence is high,
  medium or low, split per part when parts differ ("high (code), medium (sender)").
  "How found" names the script or pattern (rules finding, `rg` on a key, REPORT line).
- `## Checked and left out`: everything you looked at and did not claim, one line
  each with the reason (rebuild noise, refactor, dead code, no call site, not
  user-visible, could not verify).
- `## vs hand-written` when the site page has content: what it has that you do
  not, what it gets wrong or credits to the wrong release, what it omits.

## Rules learned the hard way

- Third-party apps (Google, Kugou, TingCar, MX Player...) get a version line
  only: "X updated from a to b". They are not decompiled; do not describe their insides.
- A string or URL in an app may come from a bundled library (blankj utilcode,
  androidx, okhttp, Tencent, Umeng...). Before claiming the vendor added it, check
  the hunk's file path is in the vendor's own package.
- Credit a change to a skipped site release only when that release's site page
  already describes it ("since 20240919"). Otherwise write that it happened
  "between X and Y".
- Hand-written changelogs are not ground truth. They have claimed apps
  "pre-installed" that were byte-identical, and downgrades that were not in the
  build. Check them against the diff like any other claim.
- Verify before claiming. A new string, key or permission is not a feature
  until code uses it: find the call site. A receiver with no sender, a setting
  with no reader, a feature you did not run: say medium or leave it out and put
  it under "Checked and left out".
- Rebuild noise is not a change: odex/vdex, re-signed APKs, kernel modules with
  new hashes only, decompiler reordering in stock Android apps.
- Removed things matter too (a removed URL, permission or setting slider).

## Unrecognised maker

REPORT marks apps whose package fw.py does not know as "unrecognised maker".
If several share one namespace and it matches `ro.build.user`,
`ro.product.manufacturer` or the zip name, it is the maker. Add it in slash form
(for example `"com/george"`) to `VENDOR_NAMESPACES` in `fw.py` and run `fw.py diff`
again; until then its code outside the app's own package is treated as library
code and only counted. A preload with its own signing certificate is third-party;
add it to `THIRD_PARTY_PACKAGES` instead. Changes to `fw.py` go to its owner as a
proposed diff.

## Other firmware types

For non-KSW/ZXW Android units, block OTAs, Unisoc/Rockchip/MediaTek/Allwinner
images or embedded Linux, read `tools/firmware/GENERALISING.md` first: it lists
formats by magic bytes, how to tell OEM from platform code without
`VENDOR_NAMESPACES`, and what `fw.py` currently misses (blank vendor/platform,
nothing outside the filesystem partitions, such as kernel, U-Boot or modem).
Say in the evidence file which parts of the image were not examined.

## Token budget

Read:
- `draft.md` Needs a human, `rules.md` High and Medium, `sitecheck.md`: a few
  thousand tokens per pair.
- `REPORT.md` Highlights only if the draft leaves a gap.
- About 40 diff lines per claim, found with `rg -n`.
- `facts.json` with `jq` for one key (`jq '.factory_settings' <diff>/facts.json`), never whole.

Never read:
- A whole `*.diff`, `files/text.diff`, `REPORT.md` or `facts.json`.
- Decompiled trees under `_work/<id>/src/`, unless a hunk is too short to judge;
  then one file, with `rg` first.
- Third-party app diffs, translations, `R.java`, `public.xml`, smali, binaries.
- Rules findings at low or info, unless checking something specific.
