# Theme discovery

87 themes, two flat vendor grids, no filtering, and a sort order that scrambles the
one collection that has a natural order. This plan fixes the sort, adds brand
landing pages that cut across vendors, and turns the 23 screenshot-less themes into
a contribution target.

Related plans: [`home-page-and-entry-points.md`](./home-page-and-entry-points.md)
(the "recently added themes" block and the nav array) and
[`platform-pages.md`](./platform-pages.md) (the `since` index shared with the
platform pages).

## What exists today

- `src/pages/themes/index.astro` — a `<VendorLinks>` chooser, six lines.
- `src/pages/themes/[slug].astro` — `/themes/ksw` and `/themes/zxw`, one flat grid
  of every theme for that vendor. 47 and 40 cards respectively.
- `src/pages/themes/[...slug].astro` — the detail page.
- `src/pages/themes/_list-item.component.astro` — the card.

Counts, from `find src/data/themes -name index.md`: **87** entries, not 89 — 47 KSW
and 40 ZXW. Worth correcting wherever the 89 figure came from.

### The unused tag machinery

`_list-item.component.astro` line 11:

```ts
const tagClassNames = theme.data.tags?.map((x) => `tag--${x}`).join(' ');
```

applied to the card's wrapper `<div class={`group relative ${tagClassNames}`}>`.
Nothing styles `.tag--bmw`, nothing queries it, and no CSS file mentions `tag--`.
Tailwind 4 would not emit anything for it anyway — these are runtime-built strings
that the content scanner never sees. Until the previous commit the same file carried
a stray `// Top div had 'hidden' class` comment, which is the fingerprint of an
abandoned client-side filter that toggled `hidden` on these classes.

So the class names are real, already correct, and currently inert. Whatever the
filtering approach ends up being, they either get used or deleted — not left as is.

### Tag vocabulary

Every one of the 87 themes has `tags`. Counts across the whole collection:

| Brand-level | Count | Sub-tags | Count |
| --- | --- | --- | --- |
| `bmw` | 29 | `bmw-evo` 12, `bmw-id7` 11, `bmw-id8` 10, `bmw-id6` 5, `bmw-id9` 2, `bmw-pemp` 2, `bmw-id5` 1, `bmw-id4` 1, `bmw-nbt` 1, `bmw-gs` 1 |
| `benz` | 26 | `benz-mbux` 13, `benz-ntg6` 5, `benz-ntg5` 1, `benz-vito` 1, `benz-glc` 1, `benz-ngt6` 1, `benz-ngt7` 1 |
| `audi` | 13 | `audi-mib3` 8, `audi-mmi` 2 |
| `lexus` | 5 | `ls` 1 |
| `landrover` | 4 | — |
| `alfaromeo` | 3 | — |
| `common` (not a brand) | 7 | — |

Non-brand modifier tags: `gs` 9, `ksw` 5, `pemp` 3, `als` 3, `cusp` 1.

Three defects block clean filtering, all one-line content fixes:

1. **`benz-ngt6` / `benz-ngt7` are typos for `ntg`** — `src/data/themes/zxw/21-KSW_BENZ_NTG6_0_2021/index.md`
   and `src/data/themes/zxw/51-KSW_BENZ_NTG7/index.md`. The sibling
   `src/data/themes/zxw/31-KSW_BENZ_NTG6_0_2021_V1/index.md` spells it `benz-ntg6`,
   so 21 and 31 are the same UI under two different tags.
2. **`bmw-pemp` vs `pemp`, `bmw-gs` vs `gs`** — ZXW files use the brand-prefixed
   form (`19-KSW_PEMP_BMW_ID7`, `20-KSW_PEMP_BMW_ID8`, `53-KSW_BMW_ID8_GS_DOUBLE`)
   where KSW files use the bare modifier (`PEMP_ID7_UI`, `BMW_EVO_ID6_GS`). Two
   vocabularies for the same concept, split by vendor.
3. **`src/data/themes/zxw/44-KSW_COMMON_ID7/index.md` is tagged `[common, bmw-id7]`**
   with no `bmw`. Any `tags.includes('bmw')` filter misses it.

Normalising the vocabulary is a prerequisite, not a nice-to-have. It is phase 1.

### The sort bug

`src/pages/themes/[slug].astro` line 27 sorts with `sortEntriesByDataId` from
`src/shared/utilities.ts`:

```ts
export function sortEntriesByDataId(entryA, entryB) {
  return entryA.data.id.localeCompare(entryB.data.id);
}
```

ZXW themes live in numbered folders (`16-KSW_BMW_ID7` … `56-KSW_BMW_ID9`) and carry
`number: 16` … `number: 56` in frontmatter, but `data.id` is the *unnumbered* name
(`KSW_BMW_ID7`). So the grid sorts alphabetically on the name while every card
displays `ID#16`, `ID#45`, `ID#23` in whatever order the alphabet lands them —
`KSW_ALFA_ROMEO` (45) first, `KSW_AUDI` (23) second, `KSW_BMW_ID9` (56) in the
middle. The numbers are not decoration: they are the `id` attribute a user types
into `<Item id="56" ui="KSW_BMW_ID9" />` in their factory config, which
`src/pages/themes/[...slug].astro` tells them to do. Presenting them shuffled is the
worst case.

Numbers present: 16 through 56 with **28 missing**, 40 entries. No KSW theme has a
`number` at all — KSW factory config uses the `<Item id="1" name="…" display="…" />`
form instead, per the same detail page.

Fix — a sibling comparator, typed narrowly to `'themes'` per the `AGENTS.md` rule
against re-widening collection-specific helpers:

```ts
export function sortEntriesByThemeNumber(
  entryA: CollectionEntry<'themes'>,
  entryB: CollectionEntry<'themes'>
) {
  const a = entryA.data.number;
  const b = entryB.data.number;
  if (a !== undefined && b !== undefined) return a - b;
  if (a !== undefined) return -1;
  if (b !== undefined) return 1;
  return entryA.data.id.localeCompare(entryB.data.id);
}
```

Ascending, so the grid matches the order of the `<SupportUIList>` block users read
off their own config file. Numbered themes sort before unnumbered ones, which only
matters on mixed pages (the brand pages below). Keep `sortEntriesByDataId` — it
stays the right comparator for the KSW grid, and the home page's "recently added"
block wants descending-by-date instead
(see [`home-page-and-entry-points.md`](./home-page-and-entry-points.md)).

## Filtering: static routes, client JS, or Pagefind

**Recommendation: static brand routes, with Pagefind filters as a cheap add-on.
Not client-side JS.**

| | Static routes | Client-side JS | Pagefind filters |
| --- | --- | --- | --- |
| Shareable URL per brand | yes | no | no |
| Indexed, ranks for "BMW head unit theme" | yes | no | no |
| Works with JS off | yes | no | no |
| Build cost | 6 extra pages | none | none |
| New moving parts | a route file | inline `<script>`, re-bind on `astro:page-load` | attributes only |
| Fits the codebase | yes | fights it | yes |

Reasoning, in order of weight:

1. **The URLs are the product.** These pages get linked from Discord and Bimmerpost
   threads. "Here are all the BMW themes" needs to be a link someone can paste. A
   JS filter produces no link and Pagefind produces one only for a search query.
2. **SEO.** `/themes/bmw` with 29 screenshots and a heading naming the brand is the
   single highest-value page this section can produce. Neither alternative creates a
   page at all.
3. **Scale says static is free.** 87 entries across 6 brands is 6 extra builds.
   There is no scenario at this size where the build cost matters.
4. **The site ships no client JS for content.** The only scripts are the sidebar
   toggle, the colour-scheme switch, and the Pagefind loader — and `AGENTS.md`
   records that all three files had to be added to the ESLint ignore list because
   `eslint-plugin-prettier` mis-parses inline `<script>` blocks. A filter script
   would be a fourth. It would also need re-binding on `astro:page-load` for view
   transitions, exactly as `navigation.component.astro` does. That is real
   maintenance for a worse result.
5. **Pagefind is worth having anyway, as a second surface.** `astro-pagefind`
   2.0.1 is already a dependency and `/search` already runs the Default UI, which
   renders filter checkboxes when the index has filters. Adding
   `data-pagefind-filter="brand:BMW"` to an element inside the `data-pagefind-body`
   region of each theme detail page costs one attribute and gives faceted search for
   free. It complements the static pages; it does not replace them.

### URL shape

`/themes/bmw` is the URL worth having. `src/pages/themes/[slug].astro` is the only
route that can serve a single segment under `/themes/`, so brand pages have to come
out of that same file. Its `getStaticPaths` currently returns the two vendors:

```ts
export async function getStaticPaths() {
  return await getFirstLevelStaticPathsFromCollection('vendors');
}
```

Extend it to return both sets with a discriminator in `props`:

```ts
export async function getStaticPaths() {
  const vendors = await getCollection('vendors');
  return [
    ...vendors.map((v) => ({ params: { slug: v.id }, props: { kind: 'vendor' as const } })),
    ...Object.keys(THEME_BRANDS).map((b) => ({ params: { slug: b }, props: { kind: 'brand' as const } }))
  ];
}
```

and branch on `Astro.props.kind` for the title, the lead paragraph and the
collection filter. The grid markup itself is shared.

Guard: a brand slug must never collide with a vendor id. With `ksw`/`zxw` and six
car brands that cannot happen today, but the collision would be silent (duplicate
`params.slug` — Astro errors, which is the good outcome). Add an explicit throw in
`getStaticPaths` so the failure names the cause.

The alternative, `/themes/brands/bmw` via a new `src/pages/themes/brands/[slug].astro`,
keeps the two concerns in separate files at the cost of a longer, less linkable URL.
Worth taking only if the branching in `[slug].astro` turns out uglier than it reads
here.

### Brand definitions

New `src/shared/brands.ts` (not `utilities.ts` — this is data, and `utilities.ts` is
already 190 lines):

```ts
export const THEME_BRANDS = {
  bmw: 'BMW',
  benz: 'Mercedes-Benz',
  audi: 'Audi',
  lexus: 'Lexus',
  landrover: 'Land Rover',
  alfaromeo: 'Alfa Romeo'
} as const;
```

`common` is deliberately excluded — the 7 themes tagged `common` are vendor-generic
UIs, not a car brand. They stay reachable from the vendor grids and from the themes
hub. `gs`, `ksw`, `pemp`, `als`, `cusp` are modifiers, not brands, and stay
out too.

Selector in `src/shared/utilities.ts`:

```ts
export async function getThemesByBrand(brand: string) {
  return await getCollection('themes', (entry) => entry.data.tags?.includes(brand) ?? false);
}
```

After the phase 1 tag fixes this gives BMW 30 (29 + `44-KSW_COMMON_ID7`), Benz 26,
Audi 13, Lexus 5, Land Rover 4, Alfa Romeo 3 — 81 of 87, with the 6 remaining being
`common`-only entries.

Each brand page sorts with `sortEntriesByThemeNumber`, which puts the 40 numbered
ZXW themes in factory-config order followed by the KSW ones alphabetically. Label
each card's vendor, since the page mixes both — `_list-item.component.astro` gets an
optional `showVendor` prop, derivable from `theme.id.split('/')[0]` or
`getVendorSlug(theme.id)`.

## The themes hub

`src/pages/themes/index.astro` stops being a vendor chooser and becomes the entry
point:

- One line of counts: 87 themes, 47 KSW, 40 ZXW.
- Brand tiles, one per `THEME_BRANDS` key, each showing the brand name, the count,
  and the first screenshot of its newest theme as the tile image.
- The two vendor links, kept.
- A callout linking the help-wanted list with its live count.

## Help wanted: themes with no screenshots

23 entries have no `images` key. One KSW
(`src/data/themes/ksw/BMW_EVO_ID6_CUSP/index.md`) and 22 ZXW: numbers 19, 20, 26,
29, 34, 35, 39, 40, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56. The
pattern is stark — everything ZXW added from number 43 onward is undocumented,
which means the newest and most interesting themes are the blank ones.

The card already handles this well: `_list-item.component.astro` renders a
`aspect-1920/720` grey box with "No screenshot yet" and an
`aria-label` of `No screenshot available for the {name} theme`. The detail page
(`src/pages/themes/[...slug].astro`, the `entry.data.images?.length` ternary) already
says *"We don't have any screenshots of this theme yet. You can try to activate this
theme, take some screenshots and contribute!"* — but that invitation is only visible
to someone who already navigated to a blank theme. Nobody goes looking for the
blanks.

New route `src/pages/themes/help-wanted.astro` (a static page, no collision with
`[slug].astro` — Astro prefers the static route):

```ts
const missing = await getCollection('themes', (entry) => !entry.data.images?.length);
```

grouped by vendor, sorted with `sortEntriesByThemeNumber`, rendered as the same card
grid so the blanks are visually obvious. Above it, concrete instructions: which
`<Item>` line to add to the factory config to activate the theme (the detail page
already generates that snippet), how to take a screenshot on the unit, and where to
send the files — Discord, or a PR adding `./home.png` and `./settings.png` next to
the theme's `index.md`, which is exactly the layout the other 64 themes use.

Link it from: the themes hub callout, the "No screenshot yet" card (make the card's
existing full-card `<a>` the only link and put the help-wanted pointer in the hub
instead, so the card keeps one target), the detail-page empty state, and the home
page (see [`home-page-and-entry-points.md`](./home-page-and-entry-points.md)).

This is the cheapest contribution funnel available: 23 named, specific, small asks
instead of a general "contributions welcome".

## Pagefind facet

On `src/pages/themes/[...slug].astro`, inside the `data-pagefind-body` region:

```astro
<span hidden data-pagefind-filter="brand">{brandLabel}</span>
<span hidden data-pagefind-filter="vendor">{vendor.data.name}</span>
```

`base-layout.astro` puts `data-pagefind-body` on `<main>`, so anything inside the
page body qualifies. The Default UI in `src/pages/search.astro` renders filter
checkboxes automatically once the index carries filters — no JS changes.

Caveat worth stating: Pagefind filters only apply within `/search`. They do not give
brand pages, do not produce linkable URLs, and do not work with JS disabled. That is
why they are an add-on and not the plan.

## What happens to `tag--<tag>`

Once brands are real routes, the inert class names have two honest options:

- **Use them** — style `.tag--bmw` etc. as coloured badges on the card's tag line.
  Requires a Tailwind `@source inline(...)` safelist or hand-written CSS in
  `src/shared/layout/global.css`, because Tailwind 4 cannot see runtime-built class
  strings.
- **Delete them** — drop line 11 and the interpolation, keeping the `#bmw #bmw-id7`
  text list that already renders below the card title, and make each tag a link to
  its brand page where one exists.

Recommend deleting the classes and linking the tag text. The links are the feature;
the classes were scaffolding for an approach this plan rejects.

## Phases

**Phase 1 — sort and vocabulary.** Add `sortEntriesByThemeNumber`, switch
`src/pages/themes/[slug].astro` to it, and fix the four content defects
(`benz-ngt6`→`benz-ntg6`, `benz-ngt7`→`benz-ntg7`, `bmw-pemp`→`pemp`,
`bmw-gs`→`gs`, add `bmw` to `44-KSW_COMMON_ID7`). Ships alone and immediately fixes
the most visible wrongness on `/themes/zxw`. No new routes, no new components.

**Phase 2 — themes hub.** Rewrite `src/pages/themes/index.astro` with counts, brand
tiles and vendor links. Brand tiles link nowhere yet, or link to `/search?q=bmw` as
an interim.

**Phase 3 — brand pages.** `src/shared/brands.ts`, `getThemesByBrand`, extended
`getStaticPaths`, the `showVendor` prop, tag text linked to brand pages. Point the
hub tiles at the real routes.

**Phase 4 — help wanted.** `src/pages/themes/help-wanted.astro` plus the four
inbound links.

**Phase 5 — Pagefind facet and tag-class cleanup.**

## Verification

`npm run lint && npx astro check && npm run build`, then:

- `dist/themes/zxw/index.html` lists `ID#16` first and `ID#56` last.
- `dist/themes/bmw/index.html`, `dist/themes/benz/index.html`,
  `dist/themes/help-wanted/index.html` exist and are non-empty; add at least
  `dist/themes/bmw/index.html` and `dist/themes/help-wanted/index.html` to the
  smoke-test path list in `.github/workflows/deploy.yml`.
- `dist/themes/bmw/index.html` contains 30 cards (29 `bmw`-tagged plus
  `44-KSW_COMMON_ID7` after the tag fix).
- `dist/pagefind/` contains filter data after the phase 5 attributes land.
- `AGENTS.md`'s `compressHTML: 'jsx'` warning applies to the tag-links change —
  `</a>` on one line followed by `<span>` on the next renders with no space. The
  themes detail page is already on the list of four files that need explicit
  `{' '}`.

## Open questions

1. **Ascending or descending by `number`?** Ascending matches the `<SupportUIList>`
   order in a user's factory config, which is why I picked it. Descending puts the
   newest themes first, which is what a browsing visitor probably wants. One of the
   two is right and it depends on who the grid is for.
2. **Is `28` a deliberate gap or a missing theme?** ZXW numbers run 16-56 with 28
   absent. If a theme with `number: 28` exists and is simply undocumented, it belongs
   on the help-wanted list.
3. **Are `benz-ngt6` and `benz-ntg6` the same thing?** `21-KSW_BENZ_NTG6_0_2021` and
   `31-KSW_BENZ_NTG6_0_2021_V1` are named as variants of each other but tagged
   differently. I am reading it as a typo; confirm before I normalise it away.
4. **`bmw-pemp` vs `pemp`, `bmw-gs` vs `gs`** — same question. Is PEMP BMW-specific
   in a way the bare `pemp` tag on the KSW themes loses?
5. **Should `common` get a landing page?** 7 themes, not a car brand, currently
   unreachable except through the vendor grids. `/themes/common` is trivial to add
   if it is useful.
6. **`lexus` and `ls`.** `48-KSW_BENZ_LS` is tagged `[benz, ls]` and
   `37-LEXUS_LS_UI` is tagged `[lexus]` — so `ls` means "LS" on a Mercedes and
   nothing on a Lexus named LS. Is `ls` a model reference, a layout style, or a
   vendor code? It is the one tag I could not decode from the data.
7. **Screenshot naming for contributions.** 62 themes use `./home.png` and 58 use
   `./settings.png`. Should the help-wanted page mandate those two filenames, or
   accept whatever a contributor sends and let the reviewer rename?
