# Home page and entry points

Turn `src/pages/index.astro` from a static brochure into a landing page that answers
the three questions a visitor actually arrives with: *what changed recently*,
*what does my unit look like*, and *what am I allowed to install*.

Related plans: [`platform-pages.md`](./platform-pages.md) (the `/platforms` routes the
"identify your unit" entry point eventually targets) and
[`theme-discovery.md`](./theme-discovery.md) (theme sorting, brand pages, the
help-wanted list this page links to).

## What exists today

`src/pages/index.astro` is 31 lines: a `<Layout>` with no `title` prop, three
paragraphs of prose inside `.prose`, and one `<Image>` of `src/shared/pic.jpg`.
Because `title` is omitted, `base-layout.astro` falls back to `DEFAULT_PAGE_TITLE`
and its `title !== DEFAULT_PAGE_TITLE` guard suppresses the `<h2>` — so the home
page currently renders no headings at all. Anything added here has to bring its own
heading levels.

The second paragraph says "Start by selecting your vendor from the menu", which is
an accurate description of the current information architecture and the problem:
every section index (`updates/index.astro`, `themes/index.astro`,
`faq/index.astro`, `factory-settings/index.astro`) is a `<VendorLinks>` chooser, so
the first three clicks are always navigation, never content.

Data available to fix that:

- `updates` — 117 markdown files under `src/data/updates/<vendor>/<platform>/`,
  every one with a required `date` in frontmatter (`src/data/updates/index.ts`).
  Newest six across both vendors as of writing:

  | Date | Entry | Vendor / platform |
  | --- | --- | --- |
  | 2025-07-18 | `20250718GT_KSW` | zxw / gt7 |
  | 2025-04-18 | `Witstek-T-M700_OS_v1.6.5-ota` | ksw / m700 |
  | 2025-04-11 | `Witstek-T-M600_OS_v1.8.6-ota` | ksw / m600 |
  | 2025-03-31 | `20250331GT_KSW` | zxw / gt6 |
  | 2025-03-25 | `20250325GT_KSW` | zxw / gt7 |
  | 2025-02-13 | `Witstek-T-M700_OS_v1.6.4-ota` | ksw / m700 |

  A plain top-6 by date is already vendor-balanced (3 KSW, 3 ZXW), so no
  interleaving logic is needed.

- `themes` — 87 entries (47 KSW, 40 ZXW). No date field, but 42 carry `since`,
  of which roughly 25 use resolvable `<vendor>/<platform>/<update-id>` references
  that `getUpdateReferences` already turns into links. That reference is the only
  timestamp a theme has.

- `src/data/faq/ksw/upgrade-path.md` — 3.1 KB, the densest and most consequential
  page on the site. It is the only place that documents the mandatory intermediate
  firmware versions (M600 needs a nine-step chain from `Ksw-R-M600_OS_v1.3.1-ota`
  through `Witstek-T-M600_OS_v1.7.8-ota`; M700 needs `Ksw-T-M700_OS_v1.4.2-ota`
  before `1.5.6`). It lives at `/faq/ksw/upgrade-path`, three clicks from the home
  page, and is one `<FaqItem>` among seven on `/faq/ksw`.

- There is no `src/data/faq/zxw/upgrade-path.md`. See "ZXW content gap" below.

## Components

New page-local components follow the existing `_`-prefixed convention
(`src/pages/themes/_list-item.component.astro`, `src/pages/faq/_item.component.astro`):

| File | Purpose |
| --- | --- |
| `src/pages/updates/_list-item.component.astro` | The `<li>` currently inlined in `src/pages/updates/[slug].astro` lines 35-46, extracted so the home page and the vendor page render identically. Props: `entry: CollectionEntry<'updates'>`, `showVendor?: boolean`. |
| `src/pages/_section.component.astro` | Section wrapper: `<h2>` heading, optional lead paragraph, a "see all" link in the corner, `<slot />`. Used by every home block so the spacing is defined once. |
| `src/shared/unit-finder.component.astro` | The "which unit do I have / what should I install" card. In `src/shared/` rather than `src/pages/` because [`platform-pages.md`](./platform-pages.md) reuses it on `/platforms`. |

Reused as-is: `src/pages/themes/_list-item.component.astro` for the theme grid,
`src/shared/date-time.component.astro` and `src/shared/relative-time.component.astro`
for dates, `src/shared/layout/base-layout.astro` for head meta.

### `unit-finder.component.astro`

Three numbered steps, each a link, no JavaScript:

1. **Which vendor?** — KSW units boot a `Ksw-*` / `Witstek-*` build; ZXW units
   report `GT6-*` / `GT7-*`. Links to `${URL_PREFIX}faq/ksw/platforms` and
   `${URL_PREFIX}faq/zxw/platforms` in phase 2, retargeted to
   `${URL_PREFIX}platforms` once those routes exist.
2. **Which platform?** — read `ro.build.display.id` from Android settings, or
   `ro.board.platform`. The mapping table lives on the platform pages.
3. **What can I install?** — links to `${URL_PREFIX}upgrade-path/ksw` (phase 3).

Every href is built as `` `${URL_PREFIX}...` `` per the base-path rule in
`AGENTS.md`; `URL_PREFIX` comes from `src/shared/config.ts`.

## Utilities

Add to `src/shared/utilities.ts`. Keep the collection-narrow typing convention
documented in `AGENTS.md` — do not widen anything to `<E extends CollectionKey>`.

```ts
export async function getLatestUpdates(limit: number) {
  const entries = await getCollection('updates');
  return entries.sort(sortEntriesByDate).slice(0, limit);
}
```

`sortEntriesByDate` already exists and sorts descending, so no new comparator.

For themes, a derived date:

```ts
// A theme has no date of its own. The `since` references point at the updates
// that introduced it, so the newest of those is the closest thing to one.
export async function getThemeDate(entry: CollectionEntry<'themes'>) {
  const ids = entry.data.since.filter((ref) => ref.includes('/'));
  const updates = await Promise.all(ids.map((id) => getEntry('updates', id)));
  const dates = updates.filter((u) => u !== undefined).map((u) => +u.data.date);
  return dates.length > 0 ? new Date(Math.max(...dates)) : undefined;
}

export async function getRecentThemes(limit: number) { /* sort by getThemeDate desc */ }
```

Note `since` is already normalised to an array by the zod transform in
`src/data/themes/index.ts`, and the plain-string form (four occurrences, e.g.
`"Ksw-Q-Userdebug_OS_v3.8.6-ota"` in `src/data/themes/ksw/BMW_ID8_UI/index.md`)
has no `/` and is correctly skipped — same guard `getUpdateReferences` uses.

Themes with no resolvable `since` get `undefined` and sort last. That is 45 of 87
entries, all older KSW themes, which is the correct outcome for a "recently added"
block.

## Sorting and limiting rules

| Block | Source | Sort | Limit |
| --- | --- | --- | --- |
| Latest firmware | `getLatestUpdates` | `sortEntriesByDate`, descending | 6 |
| Recently added themes | `getRecentThemes`, filtered to `data.images?.length` | derived date descending, tie-break `data.number` descending, then `data.id` | 6 |
| Help wanted | count only on this page | n/a | n/a |

The `images` filter on the theme block is not cosmetic. The 23 themes with no
screenshots are almost exactly the newest ZXW ones (numbers 19, 20, 26, 29, 34, 35,
39, 40, 43-56), so an unfiltered "recently added" grid would be six empty
placeholders. Filtering to themes that have a screenshot keeps the grid useful, and
the count of the excluded ones becomes the hook for the help-wanted link
(see [`theme-discovery.md`](./theme-discovery.md)).

## Promoting the upgrade path

Move the content out of the FAQ collection into its own top-level section.

1. New collection `src/data/upgrade-paths/index.ts`:

   ```ts
   loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/upgrade-paths' }),
   schema: z.object({ title: z.string() })
   ```

   Register it in `src/content.config.ts` alongside the other six.

2. `git mv src/data/faq/ksw/upgrade-path.md src/data/upgrade-paths/ksw.md` and
   swap the `question:` key for `title:`.

3. Routes:
   - `src/pages/upgrade-path/index.astro` — `<VendorLinks name="upgrade paths"
     route="upgrade-path" />`, matching the other four section indexes.
   - `src/pages/upgrade-path/[slug].astro` — `getFirstLevelStaticPathsFromCollection('vendors')`
     (the pattern the other `[slug].astro` pages now use), `getEntry('vendors', slug)`
     with the `if (!x) throw` narrow, `getEntry('upgrade-paths', slug)`, `render()`,
     and a vendor-appropriate empty state when the entry is missing — which is what
     ZXW hits until the gap below is filled.

4. Redirect the old URL so inbound Discord and Bimmerpost links keep working. Astro
   static output emits meta-refresh pages from `redirects` in `astro.config.ts`:

   ```ts
   redirects: { '/faq/ksw/upgrade-path': '/upgrade-path/ksw' }
   ```

   **Verify in `dist/`** that the emitted `dist/faq/ksw/upgrade-path/index.html`
   points at `/headunits/upgrade-path/ksw` and not `/upgrade-path/ksw`. The base
   path is applied by Astro here rather than by our own `URL_PREFIX`, so this is the
   one place in the plan where the rule is enforced by the framework instead of by
   us. If it comes out wrong, drop the config redirect and keep the FAQ entry as a
   one-line stub linking to the new page instead.

5. Add a cross-link from `/faq/ksw` to the new section — `src/pages/faq/[slug].astro`
   renders every FAQ entry inline, so removing one silently shrinks that page.

Content note: the file previously hardcoded `/headunits/...` in every link, and one
line pointed at `http://localhost:4321/headunits/...`. The working tree already
fixes this by rewriting the links root-relative and adding
`src/shared/base-path.plugin.ts`, wired through `markdown.processor` in
`astro.config.ts`. The move must preserve the root-relative form — do not
reintroduce the prefix.

## ZXW content gap

There is no ZXW equivalent of the upgrade path, and this is a content gap, not a
code gap. It should be called out in the plan and filled by a human who owns a unit
or has forum sources.

What makes it non-trivial: KSW firmware IDs carry a semantic version and an Android
letter (`Ksw-R-M600_OS_v1.3.1-ota` → Android 11, version 1.3.1), which is what the
chain in `upgrade-paths/ksw.md` is built from. ZXW IDs are datestamps
(`20240112GT_KSW` … `20250718GT_KSW`) with `android: 13` in frontmatter and no
version thread, so a "you must install X before Y" chain may not exist at all for
ZXW, or may be expressed as "any build after date D". Do not invent one. The page
should ship with an explicit empty state until someone confirms the shape.

Until then `src/pages/upgrade-path/[slug].astro` renders for `zxw` with a message in
the style of the existing empty states ("We don't have any themes for this
{vendor} vendor yet."), and the ZXW nav entry stays out.

## Navigation

`src/shared/layout/navigation.component.astro` holds a static `menu` array, lines
12-41. Changes:

- **General section** gains one entry between `Home` and `Search`:
  `{ name: 'Find your unit', path: 'platforms', icon: CpuChip }`. In phase 2 the
  target is the FAQ platform pages; from phase 3 of
  [`platform-pages.md`](./platform-pages.md) it is `/platforms`. Use
  `astro-heroicons/outline/CpuChip.astro`.
- **KSW section** gains `{ name: 'Upgrade path', path: 'upgrade-path/ksw', icon: ArrowTrendingUp }`,
  placed directly under `Updates` since that is what it qualifies.
- **ZXW section** gets the same entry only once ZXW content exists. The commented-out
  `// { name: 'Apps', path: 'apps', icon: BuildingStorefront }` on line 25 is the
  precedent for staging a nav item ahead of its content.

Two behaviours to respect:

- `isActive` compares with `startsWith` against `` `${URL_PREFIX}${path}` ``, so
  `upgrade-path/ksw` stays highlighted on any child route, and the `Home` special
  case (`href === URL_PREFIX`) already prevents Home from matching everything.
- This file is in the ESLint ignore list (`AGENTS.md`: `eslint-plugin-prettier`
  mis-parses its inline `<script>`). Format it with `npm run prettier`, not
  `npm run lint:fix`.

Sidebar length: adding two entries takes the sidebar from 12 to 14 links. That still
fits above the fold on a laptop; the `overflow-y-auto` on the container handles
narrower viewports. If it grows further, the General section is the one to split.

## Home page structure

```
<Layout>                         title omitted → no auto <h2>, blocks bring their own
  hero: <h1>-weight lead paragraph + existing pic.jpg <Image>
  <Section title="Latest firmware" href="updates">      6 × UpdatesListItem, vendor labelled
  <Section title="Find your unit">                      <UnitFinder />
  <Section title="Upgrade path">                        one-paragraph teaser → /upgrade-path/ksw
  <Section title="Recently added themes" href="themes"> 6 × ThemesListItem grid
  footer prose: Discord + Bimmerpost links (kept verbatim from today's third paragraph)
</Layout>
```

The hero image keeps `loading="eager" fetchpriority="high"`; the theme grid images
must not, or the six theme screenshots compete with the hero for the LCP. Leave the
`<Image>` defaults alone in `_list-item.component.astro`.

`AGENTS.md` flags the Astro 7 `compressHTML: 'jsx'` behaviour: whitespace containing
a newline between adjacent inline things is stripped, not collapsed. Every new
inline construct here — `<a>…</a>` newline `<span>(A13)</span>` in the update list
item, the vendor label next to the entry ID — needs an explicit `{' '}`. Nothing in
CI catches it; diff the built `dist/index.html`.

## Phases

Each phase is independently shippable and independently revertable.

**Phase 1 — latest firmware block.** Extract
`src/pages/updates/_list-item.component.astro` from `src/pages/updates/[slug].astro`,
add `getLatestUpdates` and `_section.component.astro`, render six on the home page.
No schema change, no nav change, no content change. Verifies the section scaffolding
against real data.

**Phase 2 — find your unit.** Add `src/shared/unit-finder.component.astro` pointing
at the existing `/faq/<vendor>/platforms` entries, plus the `Find your unit` nav
item. Delivers the entry point before the platform routes exist.

**Phase 3 — upgrade path promotion.** New `upgrade-paths` collection, the two
routes, the redirect, the KSW nav item, the FAQ cross-link, and the home teaser.
Blocked only on verifying the redirect base path.

**Phase 4 — recently added themes.** Add `getThemeDate` / `getRecentThemes` and the
grid. Lands after the sort fix in [`theme-discovery.md`](./theme-discovery.md)
phase 1 so the two do not fight over comparator naming.

**Phase 5 — ZXW upgrade path.** Content only, blocked on the human.

## Verification

`npm run lint && npx astro check && npm run build`, then check `dist/`:

- `dist/index.html` contains six update links and no `forKSW`-style whitespace
  collapse.
- New routes exist: `dist/upgrade-path/index.html`, `dist/upgrade-path/ksw/index.html`.
- Add `dist/upgrade-path/ksw/index.html` to the smoke-test path list in
  `.github/workflows/deploy.yml` (the `for path in \` block, currently 15 paths).
- `dist/sitemap-0.xml` picks up the new routes automatically via `@astrojs/sitemap`.

## Open questions

1. **Redirect base path.** Does Astro 7 prefix `base` onto `redirects` targets in
   static output? If not, the fallback is to keep a stub FAQ entry. Needs one build
   to settle — flagged rather than assumed.
2. **Does the ZXW upgrade path exist as a concept?** ZXW firmware is datestamped
   with no version chain. Is there any known "must install X first" constraint, or
   is any newer build installable over any older one? Nothing in the repo answers
   this and I will not invent it.
3. **Should the FAQ entry be deleted or kept as a stub?** Deleting is cleaner for
   Pagefind (no duplicate body indexed twice) but loses the entry from the `/faq/ksw`
   inline list. Your call on which matters more.
4. **`number` for KSW themes.** No KSW theme has a `number`, so the "recently added"
   tie-break degrades to `data.id` for them. Acceptable, or should KSW themes get an
   explicit `added` date in the schema instead of deriving from `since`?
5. **Hero image.** `src/shared/pic.jpg` is also the basis of `public/og-image.jpg`
   (`AGENTS.md`). If the landing page restructure changes the hero, both need
   updating. Keep the current image, or is a new one coming?
6. **Discord/forum links in the footer block** — keep them on the home page as
   today, or move them to a dedicated "Community" page now that the home page has
   competing content?
