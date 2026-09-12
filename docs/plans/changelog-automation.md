# Generating the "Changes since ..." sentence from collection data

## Problem

Every update page that documents its contents opens the detail list with a
hand-written sentence of the shape:

```
Changes since `20250325GT_KSW` built 115 days earlier:
```

(`src/data/updates/zxw/gt7/20250718GT_KSW.md:15`)

The site already owns both halves of that sentence. `getEntryWithPrevNext` in
`src/shared/utilities.ts:156` resolves the previous entry, and
`src/pages/updates/[...slug].astro` already renders it as a prev/next button
pair. `entry.data.date` is a parsed `Date` on both entries, so the interval is
a subtraction. What the sentence adds over the generated version is: nothing,
except six deliberate exceptions and a link that is currently not there at all
(the id sits in a code span, not an anchor).

## What the data actually looks like

Measured over `src/data/updates/**/*.md` on branch `fix/site-audit-round-1`.
There are no `.mdx` files, despite the loader pattern in
`src/data/updates/index.ts:12` allowing them.

| Fact | Count |
| --- | --- |
| Markdown entries | 117 |
| Entries with an empty body (frontmatter only) | 40 |
| Entries with a body | 77 |
| `Changes since` lines | 74, in 73 files |
| Lines whose reference equals the computed platform-previous entry | 68 |
| Lines whose reference does not | 6 |
| Lines carrying an interval clause | 48 |
| Lines with no interval clause | 26 |
| Entries with no line at all | 44 (40 of them empty-bodied) |

So the honest headline is not "the sentence is repetitive". It is: **44 of 117
update pages have no baseline statement at all**, and the 73 that do are
inconsistent with each other. Generating the sentence is a content gain before
it is a deduplication.

### Phrasing consistency

The reference half is uniform: always a backtick code span containing the
entry's `data.id`, always the words `Changes since`. No variants.

The interval half is not:

- 38 of 48 use an exact day count: `built 115 days earlier`, `built 77 days
  earlier`, `built 3 days earlier`.
- 10 use a rounded unit: `built 5 months earlier` (x2), `built 2 months
  earlier` (x2), `built one month earlier` (x2), `built 1 month earlier` (x2),
  `built 4 months earlier` (x1), `built 3 weeks earlier` (x1).
- The rounding threshold is not consistent. 21 days is written as `21 days` in
  several files and as `3 weeks` in `src/data/updates/zxw/gt6/20240919GT_KSW.md`.
  30 days is `30 days` in `Witstek-T-M600_OS_v1.8.5-ota.md` and `1 month` in
  `zxw/gt6/20241129GT_KSW.md`. 115 days is written as days; 122 days is written
  as `4 months`. There is no cut-off to reverse-engineer.
- `one` vs `1` is split 2/2.

Trailing punctuation: 71 of 74 end with a colon. Three do not —
`Ksw-Q-Userdebug_OS_v4.2.0-ota.md:12`, `Ksw-Q-Userdebug_OS_v4.1.6-ota.md:8`,
`Ksw-Q-Userdebug_OS_v4.0.7-ota.md:8`.

Every exact day count checked matches the frontmatter dates exactly. The
rounded ones round sanely (57d and 64d both became "2 months"; 150d and 153d
both became "5 months"). No factual errors found in the interval numbers.

### The six lines that are not the previous entry

These are the cases a generated sentence would get wrong, and the reason a
frontmatter override is needed rather than a pure derivation:

1. `src/data/updates/ksw/m600/Ksw-T-M600_OS_v1.4.4-ota.md` compares against
   `Ksw-T-M600_OS_v1.4.0-ota`. The date-previous is
   `Ksw-T-M600_OS_v1.4.2-ota` (2023-12-13), whose body is empty. The author
   skipped an undocumented build.
2. `src/data/updates/ksw/m600/Ksw-S-M600_OS_v1.5.4NEXAI-ota.md` compares
   against `Ksw-S-M600_OS_v1.2.1NEXAI-ota`, skipping five undocumented builds
   (1.2.8, 1.3.0, 1.3.2, 1.3.6, 1.3.9).
3. and 4. `src/data/updates/ksw/m700/Ksw-T-M700_OS_v1.3.1-ota.md` carries **two**
   `Changes since` lines with two different bullet lists under them: one against
   `Ksw-T-M700_OS_v1.1.5-ota` (same platform, skipping `Ksw-T-M700_OS_v1.3.0-ota`)
   and one against `Ksw-T-M600_OS_v1.6.1-ota` — a different platform directory,
   which `getEntryWithPrevNext`'s `entry.id.startsWith(platformSlug)` filter can
   never produce.
5. `src/data/updates/zxw/gt6/20231205GT_KSW.md` compares against
   `20231027GT_KSW`, skipping `20231108GT_KSW` (empty body).
6. `src/data/updates/zxw/gt6/20231017GT_KSW.md` compares against
   `20230715GT_KSW`, which **is not any entry's `data.id`**. See the data bugs
   below.

Pattern: five of the six exist to skip an entry whose body is empty. That is a
real editorial decision and it has to survive the migration.

### Two data bugs found while surveying

Neither is caused by this work, but both block a generated interval and should
be fixed first.

- `src/data/updates/ksw/m600/Ksw-S-M600_OS_v1.5.4NEXAI-ota.md:6` has
  `date: 2023-06-31T01:10:14Z`. June has 30 days. Whatever the YAML layer does
  with it, the rendered date and any computed interval will be off by at least
  a day and possibly silently rolled into July.
- `src/data/updates/zxw/gt6/20230715GT_KSW.md:2` has `id: "20231015GT_KSW"`
  while the filename, the route slug and `date: 2023-07-15T08:00:22Z` all say
  July. `20231017GT_KSW.md` then references `20230715GT_KSW`, which resolves to
  nothing. Either the `id` is a typo for `20230715GT_KSW` or the file is named
  and dated wrongly. Someone with the original ZIP needs to decide which.

### Ids versus slugs

The hand-written lines quote `data.id` (`Ksw-T-M600_OS_v1.7.1-ota`). The route
slug is the glob loader's generated id — lowercased with dots removed
(`ksw/m600/ksw-t-m600_os_v171-ota`), as the hand-written links in
`src/data/faq/ksw/upgrade-path.md` already show. So the generated sentence
needs `previous.id` for the `href` and `previous.data.id` for the label. That is
exactly what `getUpdateReferences` in `src/shared/utilities.ts:179` already does
for the themes `since` field, and the same helper can be reused.

## The structural obstacle

The sentence is not at the top of the body. Of the 77 non-empty bodies:

- 59 start with a `Summary:` block, then a blank line, then the
  `Changes since` line, then the detail list.
- 13 start with the `Changes since` line directly.
- 1 (`src/data/updates/zxw/gt6/20240801GT_KSW.md:11`) starts with `Summary`
  without a colon.
- 4 have prose and no `Changes since` line at all:
  `ksw/m501/Ksw-Q-Userdebug_OS_v3.9.6-ota.md`,
  `ksw/m700/Ksw-T-M700_OS_v1.1.5-ota.md`,
  `zxw/gt6/20230715GT_KSW.md`, `zxw/gt7/20240525GT_KSW.md`. The last three are
  chain heads with bespoke opening paragraphs that must be kept verbatim.

So a component rendered above `<Content />` cannot land between the summary and
the detail list. The page order after the change becomes:

1. "Version 1.7.4 based on Android 13 ... built on Thursday, September 19, 2024."
   (already rendered by `src/pages/updates/[...slug].astro`)
2. **Generated**: "Changes since `Ksw-T-M600_OS_v1.7.1-ota`, built 35 days earlier:"
3. Summary bullets (from the body)
4. Detail bullets (from the body)

That reads correctly — the baseline scopes the whole body, and the summary is a
summary of those changes — but it does reorder two elements on 59 pages. It
should be eyeballed on a couple of real pages before the migration phase is
committed to. The alternative, moving `Summary` into frontmatter so the page
controls the order precisely, is deferred to phase 4 because it is only worth
doing if something else wants the summary as data.

## Design

### Schema

Add one optional field to `src/data/updates/index.ts`:

```ts
// Comparison baseline for the "Changes since" line on the update page.
//   absent -> the previous entry on the same platform, by date
//   []     -> no meaningful baseline, render nothing
//   ids    -> these entries instead (collection ids, e.g. ksw/m600/...)
comparedTo: z.array(z.string()).optional()
```

An array rather than the `z.union([z.array, z.string])` shape the themes
`since` field uses (`src/data/themes/index.ts:15`), because the multi-baseline
case is real (`Ksw-T-M700_OS_v1.3.1-ota`) and because `undefined` must stay
distinguishable from `[]`. The themes field transforms both into `[]` and so
cannot express "explicitly none".

Values are collection ids, matching what `getEntry('updates', id)` takes and
what `getUpdateReferences` already resolves.

### Interval formatting

One rule: **always exact days**, singular at 1. `built 35 days earlier`,
`built 115 days earlier`, `built 150 days earlier`. Reasons:

- 38 of the 48 existing intervals are already exact days, so it matches the
  dominant house style.
- The corpus provides no consistent day/month threshold to reproduce, so any
  rounding rule invented here would disagree with roughly half the existing
  lines anyway.
- The exact number is the useful number. "4 months" and "122 days" cost the
  reader the same glance; only one of them answers "how much work is in here".

Add to `src/shared/utilities.ts`, next to the other `'updates'`-narrow helpers
and typed the same way (see the AGENTS.md note about not re-widening them):

```ts
export function getBuildIntervalDays(
  entry: CollectionEntry<'updates'>,
  baseline: CollectionEntry<'updates'>
) { ... }
```

Return a number, not a string, so the component owns the wording and the value
can also feed a `<time>` element or a `title` attribute later.

### Component

`src/pages/updates/_compared-with.component.astro`, following the existing
page-local underscore convention set by
`src/pages/updates/_file-signatures.component.astro`.

Props: the current entry plus the resolved baseline entries. It renders one
paragraph per baseline:

> Changes since [`Ksw-T-M600_OS_v1.7.1-ota`](...), built 35 days earlier:

The link is built as `` `${URL_PREFIX}updates/${baseline.id}` `` — never a
hardcoded `/headunits/...`, per AGENTS.md. Reusing `getUpdateReferences` gets
this for free, including the `ZXW GT7 ` prefix it adds for zxw entries.

Two gotchas from AGENTS.md that apply directly to this component:

- `compressHTML` defaults to `'jsx'` on Astro 7. This paragraph is exactly the
  shape that breaks: text, then `<a>`, then text, each on its own source line.
  Every line that ends before an inline element needs a trailing `{' '}`. The
  same file, `src/pages/updates/[...slug].astro`, is already on the list of
  four files that need this. Diff the built HTML in `dist/` for one KSW and one
  ZXW page before merging.
- `getEntry` returns `T | undefined`; narrow with an explicit
  `if (!x) throw new Error(...)`, no non-null assertions.

### Page wiring

In `src/pages/updates/[...slug].astro`, after the existing intro paragraph and
before `<Content />`:

- If `entry.data.comparedTo` is `undefined`, use `previous` (already destructured
  from `getEntryWithPrevNext`).
- If it is `[]`, render nothing.
- Otherwise resolve each id through `getUpdateReferences`.
- If there is no baseline at all (chain heads), render nothing.

The existing empty-body fallback — "We do not have any information about what's
new in this update." — stays, but now sits under a real, linked baseline
sentence on all 40 empty-bodied entries.

### What happens to `src/shared/relative-time.component.astro`

Replace it, do not repurpose it. It is imported nowhere (`grep -rn
"relative-time" src/` returns no usages) and it is the wrong tool three times
over:

- Its unit ladder returns the largest unit that fits, so 115 days renders as
  "3 months ago". That destroys the exact day count that 38 of the 48 existing
  lines carry.
- `Intl.RelativeTimeFormat` with `numeric: 'auto'` produces the "N days ago"
  register, not "built N days earlier". Bending it into the second phrasing
  means discarding its output and keeping only the arithmetic.
- Its props are `from: string; to?: string`, but `entry.data.date` is a `Date`
  (zod `z.date()`), so every caller has to stringify first. It also contains a
  `UNITS[u]!` non-null assertion, which AGENTS.md explicitly asks new code not
  to introduce.

What is worth keeping is the millisecond table, which can move into
`getBuildIntervalDays` as a single `MS_PER_DAY` constant. See the open questions
about deleting the file.

## Phases

Each phase is independently shippable.

### Phase 1 — fix the two data bugs

`Ksw-S-M600_OS_v1.5.4NEXAI-ota.md`'s impossible date and the
`20230715GT_KSW` / `20231015GT_KSW` id mismatch. Both need a human decision
(see open questions), and both would otherwise produce a wrong or missing
interval the moment it is computed. No code change.

### Phase 2 — generate the sentence, touch no markdown

Schema field, helper, component, page wiring. The hand-written lines stay where
they are and temporarily say the same thing twice on 73 pages.

Ships on its own: 44 entries that have never had a baseline statement get one,
with a working link, and the prev/next chevrons at the top of the page get a
sentence explaining what they mean. The duplication on the other 73 is visible
but not wrong.

Add `comparedTo` to the six exception entries in this phase so the generated
sentence is correct everywhere from day one.

Verify with `npm run lint && npx astro check && npm run build`, plus a manual
diff of `dist/updates/zxw/gt7/20250718gt_ksw/index.html` and
`dist/updates/ksw/m600/ksw-t-m600_os_v174-ota/index.html`.

### Phase 3 — remove the hand-written lines

Mechanical, and the only phase where nuance can be lost. Per file:

1. Match `/^Changes since `([^`]+)`.*$/m`.
2. Resolve the backticked `data.id` to its slug.
3. If it equals the baseline the component will pick, delete the line and the
   blank line that follows it.
4. Promote a bare `Summary:` / `Summary` paragraph to `#### Summary` and insert
   `#### Detailed changes` where the deleted line was, so the two adjacent
   bullet lists stay distinguishable.

Do this as a throwaway script (`scripts/strip-changes-since.mjs`, deleted in the
same PR) and then read every diff hunk. One PR per platform directory keeps the
review tractable: `ksw/m501` (6 lines), `ksw/m600` (26), `ksw/m700` (17),
`zxw/gt6` (18), `zxw/gt7` (7).

Three files must be hand-edited, not scripted:

- `ksw/m700/Ksw-T-M700_OS_v1.3.1-ota.md` — two baselines, two distinct bullet
  lists. The component can render two baseline paragraphs, but it cannot know
  which list belongs to which. Keep the second heading as prose, or split the
  body under two `####` headings, or leave this file exactly as it is with
  `comparedTo: []` to suppress the generated line entirely.
- `zxw/gt6/20230715GT_KSW.md` — chain head with a bespoke opener ("This is the
  first firmware we're aware of, so here are differences between this ZXW
  firmware and older KSW A12 ...").
- `zxw/gt7/20240525GT_KSW.md` — chain head with three paragraphs of
  platform-introduction prose.

Nuance that must not be scripted away: several bodies carry cross-references in
the sentences around the deleted line, for example
`ksw/m600/Ksw-T-M600_OS_v1.7.4-ota.md:16`, whose only detail bullet is "See both
M700 1.4.5 and M700 1.5.0 updates, as they were built from the same source". The
script deletes one line and nothing else.

### Phase 4 — optional: `summary` as frontmatter

Only if the updates index (`src/pages/updates/index.astro`) or the home page
wants it. Moving the 61 `Summary:` blocks into
`summary: z.array(z.string()).optional()` lets the page control the exact order
of intro / baseline / summary / detail, and makes a one-line "what changed"
available to listing pages. Coordinate with
[`home-page-and-entry-points.md`](./home-page-and-entry-points.md) and
[`platform-pages.md`](./platform-pages.md) before doing this; on its own it buys
nothing.

## Open questions

1. `Ksw-S-M600_OS_v1.5.4NEXAI-ota.md` is dated 2023-06-31. Should it be
   2023-06-30 or 2023-07-01? The neighbours are 2023-05-26 and 2023-08-10, so
   either is plausible.
2. `zxw/gt6/20230715GT_KSW.md` carries `id: "20231015GT_KSW"` with a July date
   and a July filename. Is the `id` the typo, or are the filename and date
   wrong? This also determines whether `20231017GT_KSW`'s broken reference
   becomes valid or needs repointing.
3. Exact days everywhere, or exact days with a rounded form in a `title`
   attribute? The second costs nothing but adds markup that only hover reveals.
4. Is reordering summary-above-baseline to baseline-above-summary on 59 pages
   acceptable, or is phase 4 (summary in frontmatter) a prerequisite for
   phase 3?
5. `src/shared/relative-time.component.astro` is dead code and the replacement
   makes it permanently dead. Delete it, or leave it? It is tracked, so git can
   restore it either way, but nothing should be deleted without a yes.
6. `Ksw-T-M700_OS_v1.3.1-ota.md`'s cross-platform comparison against an M600
   build: should `comparedTo` be allowed to point outside the platform
   directory at all? Allowing it is one line of code, but it makes the prev/next
   chevrons and the baseline sentence disagree about what "previous" means.
7. `src/data/updates/ksw/m701/` contains two icon assets and no entry, and
   `m701` has no file in `src/data/platforms/`. Out of scope here, but a
   `comparedTo` pointing into `m701` would silently fail. Noted, not touched.
