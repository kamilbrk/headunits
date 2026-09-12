# Platform pages

The `platforms` collection holds the most search-valuable technical content on the
site — full `build.prop` dumps, SoC model numbers, board names, the Qualcomm
`soc_id` lookup table — and none of it is rendered anywhere. This plan adds the
routes.

Related plans: [`home-page-and-entry-points.md`](./home-page-and-entry-points.md)
(the "find your unit" entry point and nav slot that point here) and
[`theme-discovery.md`](./theme-discovery.md) (the `since`-based theme cross-links).

## What exists today

Five entries, loaded by `src/data/platforms/index.ts`:

| Entry id | `data.name` | Updates | Body content |
| --- | --- | --- | --- |
| `ksw/m501` | `M501 (SD625/MSM8953)` | 10 | 2 SoC lines, `build.prop` + `vendor/build.prop` dump |
| `ksw/m600` | `M600 (SD662/SM6115) and M606 (SD460/SM4250)` | 61 | 2 SoC lines, both dumps |
| `ksw/m700` | `M700 (SD680/SM6225) and M785 (SD685/SM6225-AD)` | 18 | 2 SoC lines, both dumps, plus the `soc_id` → `soc_model` shell snippet |
| `zxw/gt6` | `GT6 (SD665/SM6125)` | 20 | 1 SoC line, both dumps |
| `zxw/gt7` | `GT7 (SD680/SM6225) and GT7PRO (SD685/SM6225-AD)` | 8 | 2 SoC lines, both dumps |

The schema is two fields:

```ts
schema: z.object({ id: z.string(), name: z.string() })
```

The collection is consumed in exactly two places, both for the name only:

- `src/pages/updates/[slug].astro` — `getCollectionGroupedByCollection('updates', 'platforms', …)`
  renders `<h3>{group.data.name}</h3>` as plain text above each update list.
- `src/pages/updates/[...slug].astro` — `platform.data.name` interpolated into the
  prose sentence and into the `about` field of the `TechArticle` JSON-LD.

`render(entry)` is never called on a platform, so the bodies are dead weight in the
repo: not on the site, not in the Pagefind index, not in the sitemap. `dist/` has no
`platforms/` directory.

This is the gap worth closing. Someone who pulls `ro.board.platform=bengal` off
their unit, or reads `SM6115` off an AIDA64 screen, has no page on this site to
land on — and those are exactly the strings people paste into a search box.

## Routes

Three files, mirroring the shape every other section already uses.

### `src/pages/platforms/index.astro` → `/platforms`

Deliberately *not* a `<VendorLinks>` chooser. This is the one section where the
cross-vendor view is the useful one: a reader who knows their SoC does not yet know
their vendor. Render a single table over all five entries, grouped by vendor,
columns: platform name, SoC model(s), `ro.board.platform`, update count, newest
update date. Reuse `src/shared/unit-finder.component.astro` from
[`home-page-and-entry-points.md`](./home-page-and-entry-points.md) above the table.

### `src/pages/platforms/[slug].astro` → `/platforms/ksw`, `/platforms/zxw`

```ts
export async function getStaticPaths() {
  return await getFirstLevelStaticPathsFromCollection('platforms');
}
```

Note the collection key. The other `[slug].astro` pages pass `'vendors'`, which is
correct for them. Passing `'platforms'` here means the route set is derived from the
data that is actually being listed, so an added platform folder produces its page
with no second edit — and, relevant below, an `m701` entry appears the moment its
markdown exists.

Lists that vendor's platforms with their update counts, and links to
`${URL_PREFIX}updates/${vendor.id}` for the flat firmware list.

### `src/pages/platforms/[...slug].astro` → `/platforms/ksw/m600` etc.

```ts
export async function getStaticPaths() {
  return await getEntryStaticPathsFromCollection('platforms');
}
```

Same `getEntry` + `if (!x) throw new Error(...)` narrowing pattern as
`src/pages/updates/[...slug].astro`, per `AGENTS.md`. `getVendorSlug(slug)` from
`src/shared/utilities.ts` gives the vendor id.

## What the detail page shows

Ordered by what a confused owner needs first.

**1. Title.** `title={platform.data.name}` — so the `<h2>` that `base-layout.astro`
renders already contains `M600 (SD662/SM6115) and M606 (SD460/SM4250)`. That heading
carries `data-pagefind-weight="100"`, which means every SoC code in the name becomes
a top-weighted Pagefind term for free.

**2. Spec table.** One row per hardware model, from the new `models[]` schema field
below: model, Snapdragon marketing name, SoC model, core count, clock, CPU core.

**3. "Is this my unit?"** — the section that makes the page worth linking to. Three
identification routes, in increasing order of effort:

- **From Android settings.** Settings → About → build number shows
  `ro.build.display.id`, e.g. `Ksw-T-M600_OS_v1.6.1` (in `ksw/m600.md`) or
  `GT7-EAU-T16.000500-user-20240525.142000` (in `zxw/gt7.md`). The prefix is the
  platform.
- **From `build.prop`.** `ro.board.platform` is the discriminator: `msm8953` = M501,
  `bengal` = M600/M606/M700/M785/GT7/GT7PRO, `trinket` = GT6. Note explicitly that
  `bengal` alone does **not** identify the unit — four platforms share it — and that
  `ro.product.system.*` is `qssi` on every Android 11+ unit and identifies nothing.
  This distinction is currently invisible to readers and is the single most useful
  thing these dumps can tell someone.
- **From `soc_id`.** `cat /sys/devices/soc0/soc_id`, then the mapping lifted out of
  the shell snippet in `src/data/platforms/ksw/m700.md`:

  | `soc_id` | `soc_model` |
  | --- | --- |
  | 417 | SM4250 |
  | 441 | SM4125 |
  | 444 | SM6115 |
  | 469 / 470 | QCM4290 / QCS4290 |
  | 473 / 474 | QCM2290 / QCS2290 |
  | 497 / 498 | QCM6490 / QCS6490 |
  | 518 / 561 | SM6225 |
  | 585 | SG4150P |

  This table belongs on a shared page, not buried in the M700 body — it is the same
  table for every Qualcomm unit. Put it in a
  `src/pages/platforms/_soc-ids.component.astro` and render it on `/platforms`, with
  the per-platform pages highlighting their own row.

**4. `build.prop` dump.** The rendered markdown body, inside a `<details>` so it
does not dominate the page. It stays indexed by Pagefind either way (the whole
`<main>` is `data-pagefind-body`).

**5. Firmware for this platform.**
`getCollection('updates', (e) => e.id.startsWith(platform.id))`, sorted with the
existing `sortEntriesByDate`, showing the newest ten with version, Android level and
date via `getUpdateVersion` / `getAndroidVersion`, then a link to the full vendor
list. For `ksw/m600` that is 61 entries, hence the cap.

**6. Upgrade path.** Link to `${URL_PREFIX}upgrade-path/${vendor.id}` once
[`home-page-and-entry-points.md`](./home-page-and-entry-points.md) phase 3 lands.
The KSW upgrade path is already written per platform (M700, M600, M501 headings), so
a deep link to the matching anchor is possible — the headings are `####`, and
`github-slugger` is already a devDependency if stable anchor ids are wanted.

**7. Themes introduced on this platform.** Themes whose `since` references start
with the platform id. Roughly 25 themes carry resolvable references; e.g.
`ksw/m501/ksw-q-userdebug_os_v394-ota` appears on seven KSW themes. See
[`theme-discovery.md`](./theme-discovery.md) for the inverse index.

**8. Factory settings.** Link to `${URL_PREFIX}factory-settings/${vendor.id}`.

Every href built from `URL_PREFIX` per `AGENTS.md`.

## Schema additions

`src/data/platforms/index.ts`. Everything new is optional so the five existing files
keep validating while they are migrated one at a time, and so a name-only entry
stays legal (needed for the m701 question below).

```ts
schema: z.object({
  id: z.string(),
  name: z.string(),
  vendor: z.string().optional(),
  models: z
    .array(
      z.object({
        model: z.string(),           // 'M600'
        soc: z.string(),             // 'Snapdragon 662'
        socModel: z.string(),        // 'SM6115'
        socId: z.number().optional(),// 444
        cores: z.number().optional(),// 8
        clockGhz: z.number().optional(),
        cpu: z.string().optional()   // 'Cortex-A73'
      })
    )
    .optional(),
  boards: z.array(z.string()).optional(),   // ro.board.platform values, e.g. ['bengal']
  androidVersions: z.array(z.number()).optional(),
  aliases: z.array(z.string()).optional()   // extra search terms not in `name`
})
```

Every value needed to populate `models[]`, `boards[]` and `aliases[]` is already
written in the five bodies as prose — `M600: Qualcomm Snapdragon 662 (SM6115),
8-core 2.0GHz, Cortex-A73` becomes one object, `ro.board.platform=bengal` becomes
one `boards` entry. This is a transcription, not new research. Nothing is invented.

`androidVersions` is the one field that needs a judgement call rather than a copy:
it can be derived at build time from the updates under the platform
(`getAndroidVersion` over `getCollection('updates', …)`) instead of being authored.
Prefer deriving it — it cannot go stale.

The fenced `build.prop` blocks stay in the body. They are reference material, not
structured data, and modelling them as fields would be a lot of schema for no query.

## SEO

The value here is specific: people search `SM6115 head unit`, `bengal android head
unit`, `msm8953 car radio firmware`. Today the site has no page that ranks for those
because the strings only exist in un-rendered markdown.

- **Title** is already the SoC-bearing `data.name`. Good as-is.
- **Description** — pass an explicit `description` prop to `<Layout>`. Without it
  `base-layout.astro` falls back to `DEFAULT_PAGE_DESCRIPTION` for all five pages,
  which produces five identical meta descriptions. Build it from the models:
  `"M600 and M606 Android head units — Snapdragon 662 (SM6115) and Snapdragon 460
  (SM4250), 61 documented firmware updates."`
- **JSON-LD** — follow the existing pattern
  (`src/pages/updates/[...slug].astro` uses `TechArticle`,
  `src/pages/themes/[...slug].astro` uses `CreativeWork`). Use `TechArticle` with
  `about` naming the SoCs and `keywords` joining every alias: the platform name,
  each `socModel`, each marketing `soc`, each board name, plus `qssi`. Pass it
  through the `jsonLd` prop `base-layout.astro` already accepts.
- **Sitemap** — `@astrojs/sitemap` picks up the new static routes with no config.
- **Canonical** — handled by `base-layout.astro` from `Astro.url.pathname`.

## Cross-links from existing pages

Small edits that make the new routes reachable from where the data already appears:

- `src/pages/updates/[slug].astro` line 33: wrap `<h3>{group.data.name}</h3>` in a
  link to `${URL_PREFIX}platforms/${group.id}`.
- `src/pages/updates/[...slug].astro` line ~86: `{platform.data.name}` is currently
  plain text inside the "Version X based on Android Y for KSW devices running on
  M600 platform" sentence. Make it a link. Watch the `compressHTML: 'jsx'` trap
  documented in `AGENTS.md` — this file is on the list of four that already need
  explicit `{' '}`, and turning text into an element adds another element-to-element
  boundary.
- `src/data/faq/ksw/platforms.md` and `src/data/faq/zxw/platforms.md` answer "What
  platforms are available?" with a flat SoC list. Once `/platforms` exists, these
  should link to it rather than duplicate it. They also mention platforms with no
  entry at all: `M506`, `M511`, `M720`, `501A-`, `M606`, `GT7Pro`. Those are model
  variants that belong in `models[]`, not new platform pages — except M506, M511 and
  M720, which have no home at all. See open questions.

## The m701 problem

`src/data/updates/ksw/m701/` exists on disk and contains, in full:

```
src/data/updates/ksw/m701/.DS_Store
src/data/updates/ksw/m701/WITSTEK-T-M701-OS_EN_v1.5.5_20241227/icon-apkinstaller-m701.webp
src/data/updates/ksw/m701/WITSTEK-T-M701-OS_EN_v1.5.5_20241227/icon-apkinstaller-m700.png
```

Facts, not inferences:

- There is no `.md` or `.mdx` under that folder, so the `updates` glob loader
  (`**\/[^_]*.{md,mdx}`) yields nothing and the platform never appears in
  `getCollectionGroupedByCollection`.
- There is no `src/data/platforms/ksw/m701.md`, so there is no platform entry either.
- `git ls-files` returns nothing for the directory — every file in it, `.DS_Store`
  included, is untracked. `.DS_Store` is in `.gitignore` (line 125); the two images
  are not ignored, they were simply never added.
- `README.md` line 112 lists `m701` among the stable platform ids, so the intent to
  document it existed.
- The two asset filenames are `icon-apkinstaller-m701.webp` and
  `icon-apkinstaller-m700.png` — an M701 icon next to an M700 icon, which is the
  shape of a before/after comparison in an update body. That is a reading of the
  filenames, not a claim about the firmware.

**No firmware facts are invented here.** I do not know the SoC, the release date,
the file hashes, or whether `WITSTEK-T-M701-OS_EN_v1.5.5_20241227` is a real
distributed OTA. Those all have to come from you.

Handling, in order of preference:

- **(a) Do nothing, phase 1.** The new `/platforms` routes derive from the
  `platforms` collection, so m701 is simply absent. Nothing breaks. This is the
  default and it is why `getFirstLevelStaticPathsFromCollection('platforms')` is the
  right key for the vendor route — m701 appears automatically once its markdown
  lands, with no code change.
- **(b) Name-only stub.** Add `src/data/platforms/ksw/m701.md` with `id` and `name`
  and no body. The platform page renders with an empty state in the style of the
  existing ones ("We don't have information about updates for this platform yet."),
  the orphaned assets get a home, and the gap becomes visible to contributors rather
  than invisible on disk. Requires only that M701 is a real platform — one bit of
  information from you, no firmware detail.
- **(c) Remove the folder.** Only if the assets are a dead end. They are untracked,
  so git cannot restore them — this needs an explicit decision from you, and I will
  not do it unprompted.

## Latent issue worth noting

`getCollectionGroupedByCollection` in `src/shared/utilities.ts` groups children with
`entry.id.startsWith(parent.id)`. With today's ids (`ksw/m600`, `ksw/m700`,
`ksw/m701`) there is no collision, because `ksw/m701/...` does not start with
`ksw/m700`. But the match is a raw string prefix with no separator guard, so a
future pair like `ksw/m70` and `ksw/m700` would silently merge. A one-character fix
(`entry.id.startsWith(`${parent.id}/`)`) removes the hazard. Not urgent, not in
scope, flagged because this plan adds a second caller of the same idea.

## Phases

**Phase 1 — routes over existing data.** All three route files, rendering
`data.name`, the markdown body, and the per-platform update list. Zero schema
change, zero content change. Five new pages, five previously-dead `build.prop` dumps
now indexed by Pagefind and listed in the sitemap. This is most of the SEO win and
it ships alone.

**Phase 2 — schema and spec tables.** Add the optional fields, transcribe the five
bodies into `models[]` / `boards[]`, derive `androidVersions` from the updates,
render the spec table, add the per-page `description` and the JSON-LD `keywords`.

**Phase 3 — identification.** The "Is this my unit?" section and the shared
`_soc-ids.component.astro`, with the `bengal`-is-ambiguous warning. Retarget the
`Find your unit` nav item and `unit-finder.component.astro` from the FAQ pages to
`/platforms`. Link the two FAQ `platforms.md` entries here.

**Phase 4 — cross-links.** Platform names become links on both updates pages; the
themes-introduced-here list, which depends on the `since` index from
[`theme-discovery.md`](./theme-discovery.md).

**Phase 5 — m701.** Blocked on you.

## Verification

`npm run lint && npx astro check && npm run build`, then:

- `dist/platforms/index.html`, `dist/platforms/ksw/index.html`,
  `dist/platforms/ksw/m600/index.html` exist and are non-empty.
- Add `dist/platforms/index.html` and `dist/platforms/ksw/m600/index.html` to the
  smoke-test list in `.github/workflows/deploy.yml`.
- Grep the built HTML for `SM6115` and `bengal` to confirm the dumps actually render
  rather than being swallowed by the `<details>`.
- Diff `dist/updates/ksw/index.html` and one `dist/updates/ksw/m600/*.html` after the
  cross-link edits, for the `compressHTML` whitespace trap.

## Open questions

1. **Is M701 a real platform?** One bit — yes or no. If yes, option (b) above; if
   no, the folder is dead and you decide whether it goes.
2. **What is `WITSTEK-T-M701-OS_EN_v1.5.5_20241227`?** A released OTA with a date and
   hashes, or a working note? If it is real, it needs an update markdown file and
   the two icons need a body that uses them.
3. **What are the two icons for?** `icon-apkinstaller-m701.webp` next to
   `icon-apkinstaller-m700.png` looks like an APK-installer icon comparison between
   two platforms. Which update body were they meant for?
4. **M506, M511, M720.** `src/data/faq/ksw/platforms.md` names them; they have no
   platform entry and no updates. Are they real shipping platforms that deserve
   pages, variants that belong in `models[]` on an existing page, or speculation
   from firmware strings that should stay in the FAQ?
5. **M606 and GT7PRO naming.** Both are folded into a sibling platform's `name`
   (`M600 (…) and M606 (…)`). Should `/platforms/ksw/m600` be one page covering both,
   or should each model get its own URL for search? One page is cheaper and matches
   the firmware, which is shared; separate pages rank better for `M606`. My
   recommendation is one page plus `aliases`, but this is a call about how people
   search, which you know better than I do.
6. **Is `soc_id` readable without root** on these units? The snippet in `m700.md`
   runs as an init script. If a normal user cannot `cat /sys/devices/soc0/soc_id`,
   that identification route needs an ADB caveat or should be demoted below the
   `build.prop` route.
