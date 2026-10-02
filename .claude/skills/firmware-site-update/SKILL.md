---
name: firmware-site-update
description: Turn finished firmware analysis (claude.md, claude.evidence.md, sitecheck output, FINDINGS.md) into edits of the headunits site data under src/data - fill empty update pages, correct wrong changelog claims, fix theme `since` values and add factory settings. Use when the owner asks to put firmware findings on the site, fill in an update page, or fix a theme or factory setting from a diff.
---

# Firmware site update

Every sentence you add to the site must trace to a row in a `claude.evidence.md`
or a line in a diff. If the evidence does not say it, the site does not say it.

## Sources, in order of trust

1. `claude.evidence.md` beside each analysis: the claim, the diff quote and the
   confidence. This is what you cite.
2. `claude.md` beside it: the same claims already in site wording.
3. `fw.py sitecheck <diff>` output: themes, factory keys and frontmatter the
   site lacks or has wrong. Mechanical; about 87% of its findings were right
   when measured, so confirm each against the evidence file.
4. `~/Dev/firmwares/_analysis/FINDINGS.md`: the cross-firmware summary.
   Section 3 lists wrong hand-written claims, section 4 theme `since`
   corrections, section 5 missing factory settings, section 6 frontmatter
   mismatches, section 7 empty pages that now have a draft.
5. `draft.md` from `fw.py draft`: mechanical only. Never publish its
   "Needs a human" list.

The existing hand-written pages are not ground truth; correct them when the
evidence contradicts them. Do not use them to fill gaps in the evidence.

## Update pages (`src/data/updates/<vendor>/<platform>/<id>.md`)

- Frontmatter: keep what is there. Change a field only when sitecheck or
  FINDINGS section 6 reports a mismatch with evidence (usually `date`). Use
  `comparedTo` only when the real baseline is not the previous page on the
  platform.
- Empty page (frontmatter only): paste the body of `claude.md` (`#### Summary`,
  `#### Changes`). Do not paste its frontmatter over the existing one.
- Page with content: keep the owner's bullets that the evidence confirms or does
  not address. Rewrite a bullet the "vs hand-written" section or FINDINGS
  section 3 shows is wrong. Add omitted changes that are high confidence.
  Move a change credited to the wrong release to the right page.
- An analysis that skipped site releases: a change goes on a skipped release's
  page only if the evidence names that release. Otherwise it stays on the page
  that was analysed, worded "since X" or "between X and Y" as the evidence has it.
- Medium-confidence claims keep their hedge in the wording ("appears to",
  "not tested"). Low-confidence ones and "Checked and left out" items stay off the site.
- Third-party apps: version lines only.
- A new firmware with no page: create it with the frontmatter from
  `fw.py frontmatter <id>` (or `frontmatter.md` in the diff folder) and the body
  of `claude.md`.

## Writing rules (from AGENTS.md)

- Write firmware ids and theme ids as backticked text
  (`` `Ksw-T-M600_OS_v1.4.8-ota` ``, `` `UI_GS_ID8` ``) and glossary terms as
  plain words; `autolink.plugin.ts` links them. Do not hand-write those links.
- Other links: root-relative, no base path, e.g. `/factory-settings/zxw`,
  `/updates/ksw`. Never `/headunits/...`.
- LF, UTF-8, 2-space indent in YAML.

## Themes (`src/data/themes/<vendor>/<folder>/index.md`)

- Fix `since` from FINDINGS section 4 or sitecheck. Use the slug form the
  newer files use, the update page's collection id in lower case without dots
  (`zxw/gt6/20250331gt_ksw`, `ksw/m501/ksw-q-userdebug_os_v391-ota`). A theme on
  several lines takes a list.
- A theme that is only an id or a placeholder is not "since" that build; use the
  first build where it is usable, as the evidence says.
- A missing theme: add a folder with `index.md` (`id`, `number` for ZXW,
  `display`, `tags`, `client` when locked to one vendor, `since`). Leave
  `images` out rather than invent them; say in your reply that screenshots are needed.

## Factory settings (`src/data/factory-settings/<vendor>/NN-section.md`)

`src/shared/factory-config/validate-keys.ts` fails the build unless:

- `configKey` exists in the vendor's example XML in `public/` (named by
  `factoryConfigFileName` in `src/data/vendors/<vendor>.md`:
  `factory_config.xml` for KSW, `zxw_factory_config.xml` for ZXW). Check with
  `rg -n '<keyName>' public/zxw_factory_config.xml`. A key seen only in code
  gets `unverified: true`.
- No two settings claim the same key.
- A `checkbox` with a key has explicit `onValue` and `offValue`. Never infer
  them: the vendor writes `0: allow  1: Prohibited` in places. If the evidence
  does not give both, use `editable: false`.
- A radio group's children each have `configValue` (unless the key is `unverified`).

Use `editable: false` for rows that are actions, or whose meaning the evidence
rates below high, usually with a `warning`. Put the row in the section matching
where the factory menu shows it; the evidence names the fragment
(`FragmentFunction` is "Function", `FragmentVehicle` is "Vehicle").
`description` says only what the evidence says the value does.

## Verify

Run from the repo root, and check each exit code, not the last line of output:

```sh
npm run lint
npx astro check
npm run build
npm run check:html
npm run check:links
npm run check:autolinks
npm run check:spacing
```

`check:autolinks` carries an expected site-wide link count with a 20%
tolerance. If new content moves the count past it on purpose, update
`EXPECTED_TOTAL` in `scripts/check-autolinks.mjs` and say so in the reply. For factory-settings
edits also run `npm test`, and `npm run test:e2e` after the build.

## Hand-off

- Show the owner the diff (`git diff --stat` and the changed pages) and wait for
  a go before committing. Never push without being asked.
- One release per commit, or a small batch of related ones (one theme `since`
  sweep, one factory section). Message style from `git log`, for example
  `docs(updates): fill ZXW GT6 20241129 from firmware diff`.
- In the reply, list any claim you left out because the evidence was too weak,
  and anything that needs the owner (screenshots, a judgement call).
