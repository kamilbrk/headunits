# Glossary and safety surface

Two additions that share a mechanism: both need a way to put a short,
reusable block of prose into markdown bodies that are otherwise plain bullet
lists, and both are aimed at the reader who arrived from a forum link and has
never seen this hardware before.

## Part A — Glossary

### What the content actually uses

Measured over `src/data/**/*.md` on branch `fix/site-audit-round-1`. Counts are
case-sensitive with word boundaries unless noted, because the naive
case-insensitive counts are badly inflated — `grep -ric ota` returns 234 hits,
but almost all of them are the `-ota` suffix inside firmware identifiers, not
prose.

| Term | Occurrences | Files |
| --- | --- | --- |
| Zlink | 65 | 35 |
| Bluetooth | 52 | 27 |
| Witstek | 31 | 16 |
| ID8 | 27 | 18 |
| HiCar | 26 | 15 |
| Qualcomm | 25 | 12 |
| Snapdragon | 25 | 11 |
| MCU | 18 | 10 |
| ID7 | 18 | 18 |
| SM6225 | 18 | 7 |
| CarPlay | 14 | 10 |
| adb | 14 | 4 |
| OTA | 13 | 10 |
| DVR | 12 | 5 |
| `build.prop` | 10 | 5 |
| MIB3 | 10 | 10 |
| EVO | 10 | 10 |
| ID6 | 9 | 8 |
| CAN | 7 | 4 |
| NTG6 | 6 | 6 |
| Android Auto | 6 | 3 |
| ID9 | 5 | 5 |
| GPS | 5 | 5 |
| FIBO | 4 | 3 |
| CPM | 3 | 3 |
| NTG5 / NTG7 / DSP / DAB / fastboot | 1 each | 1 each |

Terms from the original wish-list that the content does **not** contain:

- **FYT** — zero hits anywhere in `src/data/`.
- **NEXAI** — zero prose hits. All 16 substring hits in 14 files are inside
  firmware identifiers such as `Ksw-S-M600_OS_v1.5.4NEXAI-ota`. It still belongs
  in the glossary precisely because a reader sees it in a filename and has
  nowhere to look it up, but it cannot be auto-linked without linking the middle
  of a version string.
- **canbus** / **CAN decoder** — the site writes "CAN Protocol"
  (`src/data/factory-settings/ksw/04-can-protocol.md:2`,
  `src/data/factory-settings/zxw/05-can-protocol.md:2`), "CAN Bus Data
  Acquisition" (`src/data/factory-settings/ksw/02-vehicle.md:157`), and
  "Mercedes NTG7.0 Decoder" (`src/data/updates/zxw/gt7/20250718GT_KSW.md:20`).
  The word "canbus" as one token appears once, "decoder" as a standalone word
  zero times.
- **dongle** — zero hits. "CarPlay dongle" is forum vocabulary, not site
  vocabulary.

Useful negative finding: the highest-frequency terms are not the ones a
newcomer trips on first. `Zlink` at 65 hits is never defined anywhere on the
site; it is the name of the app that provides CarPlay and Android Auto, and the
only place it is explained at all is a settings description inside
`src/data/factory-settings/ksw/01-function.md`, which a reader has to already
know to go looking for. Same for `MCU` (18 hits) — `src/data/faq/ksw/install-mcu-updates.md`
tells you how to update it without ever saying what it is.

### Shape

A `glossary` collection at `src/data/glossary/`, registered in
`src/content.config.ts` alongside the other six, following the existing pattern
in `src/data/faq/index.ts`:

```ts
export default defineCollection({
  loader: glob({ pattern: '**\/[^_]*.md', base: './src/data/glossary' }),
  schema: z.object({
    term: z.string(),
    // Other spellings that should resolve to this entry, e.g. "CAN bus".
    aliases: z.array(z.string()).optional(),
    // Suppresses auto-linking for terms that only ever appear inside
    // identifiers (NEXAI) or that would produce noise (CAN).
    autolink: z.boolean().optional(),
    see: z.array(z.string()).optional()
  })
});
```

Flat, not vendor-partitioned. Every term in the table above is shared between
KSW and ZXW, and the two vendor-specific ones (`FIBO`, `CPM` — ZXW hardware
platform names) are better served by a note in the definition than by a
directory split.

One page, `src/pages/glossary.astro`, rendering every entry alphabetically with
an `id` anchor per term. Anchors via `slug` from `github-slugger`, which is
already a dependency and already used for exactly this in
`src/pages/factory-settings/_setting.component.astro:5` and
`src/shared/sitemap-lastmod.ts:4`.

Trade-off to accept knowingly: `data-pagefind-body` sits on `<main>` in
`src/shared/layout/base-layout.astro`, so the whole glossary indexes as one
Pagefind result rather than one per term. With roughly 30 short entries that is
the right call — 30 stub pages would dilute search worse than one dense page
does. Revisit only if the glossary grows past a screen or two.

Nav entry goes in the `General` section of the `menu` array in
`src/shared/layout/navigation.component.astro:15`, next to Search. Path is
`'glossary'`; `getLink` prepends `URL_PREFIX` for anything not starting with
`http`, so the base path is handled and must not be written by hand.

### Auto-linking first occurrences

Optional, and it should be phased separately because it is the only part that
can go wrong invisibly.

The mechanism is a Sätteri mdast plugin, directly parallel to the existing
`src/shared/base-path.plugin.ts`. Verified against the installed packages:

- `defineMdastPlugin` is exported from `satteri`
  (`node_modules/satteri/dist/index.d.ts:3`).
- A `text?: MdastVisitorFn<Text>` visitor exists
  (`node_modules/satteri/dist/mdast/mdast-visitor.d.ts:146`).
- The visitor context offers `replaceNode(node, newNode | newNode[])`,
  `parent(node)` and `textContent(node)`
  (`node_modules/satteri/dist/mdast/mdast-visitor.d.ts:68`, and the hast
  equivalents at `node_modules/satteri/dist/hast/hast-visitor.d.ts:47`).
- `before` / `after` hooks run once per document
  (`node_modules/satteri/dist/hast/hast-visitor.d.ts:115`), which is where the
  "first occurrence only" set lives.

Register it in `astro.config.ts` as `satteri({ mdastPlugins: [glossaryPlugin],
hastPlugins: [basePathPlugin] })`. Emitting the link as a root-relative
`/glossary#mcu` in mdast means `base-path.plugin.ts` adds the deployment prefix
on the hast pass, so the base-path rule is honoured by reuse rather than by a
second implementation.

The term list has to be available while the Astro config is still resolving,
which is before `getCollection` exists. The repo already solves this exact
problem: `src/shared/sitemap-lastmod.ts` reads `src/data/updates/**` frontmatter
off disk with `node:fs` for the same reason, and says so in its doc comment.
The glossary plugin factory does the same over `src/data/glossary/*.md`, reading
only `term`, `aliases` and `autolink`. Note the comment in that file about
reading line-by-line rather than with a frontmatter regex — the obvious pattern
trips `sonarjs/super-linear-regex` and ESLint is a CI gate.

Rules the visitor needs, all learned from the data above:

- Skip text inside `link`, `inlineCode`, `code` and `heading` nodes. Most
  occurrences of `Zlink` in update bodies are inside code spans
  (`` `com.zjinnova.zlink` ``) or already-linked theme names.
- Match on word boundaries and case-sensitively. `CAN` unbounded matches
  "can"; `EVO` matches nothing useful once bounded but everything inside
  "EVO_ID6" without a boundary rule.
- One link per term per document, in document order.
- Honour `autolink: false` for `NEXAI` and anything else that only occurs inside
  identifiers.

Failure mode to watch for: `src/data/factory-settings/**` bodies are mostly YAML
`settings[]` arrays, not prose, so the plugin will see very little text there —
which is correct, but means the terms a reader most wants defined while reading
factory settings (`CAN Protocol`, `Zlink`, `DSP`) will not be auto-linked on
those pages. A static "Glossary" link in the page chrome covers that case and is
cheaper than making the plugin walk frontmatter.

### Phases

1. **Collection + page + nav link.** Roughly 30 entries, definitions written by
   hand. Ships alone: there is a place to send someone who asks what Zlink is.
2. **Static cross-links.** Add a glossary link to the FAQ index and the factory
   settings pages. Still no plugin.
3. **Auto-linking plugin.** Behind the `autolink` flag so individual terms can
   be switched off without a code change. Diff `dist/` before merging — per
   AGENTS.md nothing in CI catches markup regressions in rendered content.

## Part B — Safety and disclaimer surface

### What exists today

Nothing site-wide. `src/shared/layout/base-layout.astro` has no footer element
at all. The only risk-adjacent sentences in the whole repo are:

- `src/data/faq/ksw/apply-factory-config.md:4` and its ZXW twin: "Before making
  any changes, make sure you have a backup of your original file. Once you apply
  a new file, it will persist even through a factory reset."
- `src/data/faq/ksw/pull-factory-config.md:4`: "Before you make any changes,
  please make a backup of the original file, so that you can always revert to
  it."
- `src/data/faq/ksw/upgrade-path.md:4`: "Some updates require certain prior
  versions to ensure compatibility ... make sure that you follow the upgrade
  path to avoid issues."
- `src/pages/themes/[...slug].astro:73`: "This theme appears to be invalid, so
  we do not recommend activating it."

Notably, `src/data/faq/ksw/install-updates.md` and
`src/data/faq/zxw/install-updates.md` — the two pages that tell someone to copy
a firmware image onto a USB stick and confirm a prompt — contain no caution at
all, and `install-updates.md` does not link to `upgrade-path.md` even though
skipping the upgrade path is the documented way to break a unit.

### Where warnings belong

Three surfaces, doing three different jobs.

**1. A footer line on every page.** One sentence, in
`src/shared/layout/base-layout.astro`, below `<main>`. It is the only place
that reaches the reader who landed on a single update page from Google.

> Community notes, not vendor documentation. Firmware and factory-config
> changes can leave a head unit unusable — read [Before you change
> anything](/safety) first.

The link is built from `URL_PREFIX`, not written literally. Mark the footer
`data-pagefind-ignore` so the sentence does not appear in every search result's
excerpt.

**2. A callout component usable from markdown bodies.** So the two
`install-updates.md` entries and the two `apply-factory-config.md` entries can
carry a specific warning where the instruction is, instead of a generic one in
the footer.

This is implementable today without MDX. Sätteri supports container directives:
`node_modules/satteri/dist/compile.d.ts:121` declares `directive?: boolean`
(default `false`), and the `satteri()` option type at
`node_modules/@astrojs/markdown-satteri/dist/processor.d.ts` documents
`satteri({ features: { directive: true } })` as its worked example. Enabling it
gives the markdown a `:::warning` block, and a
`defineMdastPlugin({ containerDirective(node, ctx) { ... } })` visitor
(`node_modules/satteri/dist/mdast/mdast-visitor.d.ts:165`) rewrites it into the
styled markup, using `ctx.wrapNode` or `ctx.replaceNode` with the `{ raw }`
escape hatch.

Author-facing syntax:

```md
:::warning
An OTA built for a different platform, or installed out of order, can leave
the unit stuck at boot.
:::
```

Check before enabling: `features: { directive: true }` changes how `:::` is
parsed in every existing markdown file. `grep -rn ':::' src/data/` currently
returns nothing, so the change is inert on today's content, but re-run that
check at implementation time.

The alternative — converting the four FAQ files to `.mdx` and importing an
Astro component — also works (`@astrojs/mdx` is installed and the faq loader
pattern would need `.mdx` added). It is worse: it makes four content files
structurally different from the other seven for no gain, and MDX bodies stop
being editable by someone who only knows markdown, which works against
[`contributing-and-edit-links.md`](./contributing-and-edit-links.md).

**3. A dedicated page, `src/pages/safety.astro`** (route `/safety`), linked
from the footer, from the `General` nav section, and from each callout. This is
where the detail that does not fit in a callout lives.

### Draft wording

#### Footer (every page)

> Community notes, not vendor documentation. Firmware and factory-config
> changes can leave a head unit unusable — read *Before you change anything*
> first.

#### `/safety` — "Before you change anything"

> This site is written by owners of these units, from reading firmware images
> and comparing them. It is not from KSW, ZXW, Witstek, or any car
> manufacturer, and nobody here can repair a unit that stops working.
>
> **What actually goes wrong**
>
> - An OTA built for a different platform, or installed out of the documented
>   upgrade path, can leave the unit stuck before it finishes booting. There is
>   no user-accessible recovery from that state: the unit comes out of the dash
>   and goes back to the seller or to someone with the hardware to reflash it.
>   The upgrade paths we know about are on the KSW upgrade path page.
> - The factory config file persists through a factory reset. Applying one
>   taken from a different unit can change the screen resolution, the CAN
>   protocol, and what the unit assumes about the amplifier, the camera and the
>   steering wheel buttons. A unit left with a blank or wrongly sized screen
>   still has to be given a correct config file over USB before it is usable
>   again.
> - Changing CAN protocol or vehicle settings will not damage the car, but it
>   can quietly stop steering-wheel buttons, parking sensors or the reversing
>   camera from working, and the connection between the setting and the symptom
>   is not obvious weeks later.
> - An MCU update that is interrupted is harder to recover from than an
>   interrupted OTA. Do not start one with the ignition about to time out.
>
> **What reduces the risk**
>
> - Pull your `factory_config.xml` and keep a copy before you change anything.
>   Keep it on a FAT32 USB stick in the car, not only on a laptop at home.
> - Write down your current firmware version and MCU version, from Settings and
>   System information, before you update. You need both to work out which
>   update is next and to describe the problem if one appears.
> - Check the upgrade path for your platform. Several updates are only
>   installable from a specific earlier build.
> - Compare the md5 or sha256 of your download against the values on the update
>   page. Where we have them, they are the only link between a file circulating
>   on Discord and the file we looked at.
> - Update with the engine running or on a charger, and stay with the car. Most
>   failed OTAs are units that lost power mid-write.
>
> **What this site does and does not have**
>
> We describe firmware; we do not host it. Downloads circulate on Discord and
> on forums, and we have no control over what is in them. Where an update page
> shows no checksum, it means nobody has published one — not that the file is
> known to be good.

#### Callout — `install-updates.md` (both vendors)

> Installing an OTA that was not built for your platform, or installing one out
> of order, can leave the unit stuck at boot with no user-accessible recovery.
> Check your platform and the upgrade path before copying anything to the USB
> drive.

#### Callout — `apply-factory-config.md` (both vendors)

> A factory config survives a factory reset. If the file you apply is wrong for
> your unit, the only way back is applying your own backup the same way — so
> pull your original file first and keep it somewhere you can reach from the
> car.

Deliberately absent: "at your own risk", "we accept no liability", "for
informational purposes only", and anything else that takes a paragraph to say
that a hobbyist website is a hobbyist website. The MIT licence in
`package.json` already carries the no-warranty text, and a reader who skims past
three sentences of boilerplate will skim past the fourth sentence that actually
mattered.

### Phases

1. **`/safety` page + footer line + nav entry.** No content-file changes, no
   markdown-pipeline changes. Ships alone and is the single highest-value item
   here, because right now a first-time visitor gets no warning on any route.
2. **Cross-links.** Link `install-updates.md` to `upgrade-path.md` and to
   `/safety` with plain markdown links. Still no pipeline change, and it closes
   the worst gap (the flashing instructions not mentioning the upgrade path).
3. **Callout directive.** Enable `features: { directive: true }`, add the mdast
   plugin and the Tailwind styling, convert the four cross-links into callouts.
   Diff `dist/` for the four FAQ pages; AGENTS.md is explicit that nothing in CI
   catches rendered-markup regressions.

## Open questions

1. Is `/safety` the right route and "Before you change anything" the right
   title? "Safety" reads like a legal page; the title is the thing people
   actually click.
2. Should the footer line appear on every page, including `/`, `/search` and
   the theme gallery, or only on FAQ, updates and factory-settings routes?
   Site-wide is simpler and is what a footer is for, but it does put a warning
   under a page of screenshots.
3. Glossary as one page with anchors, or one route per term? One page is
   recommended above; the counter-argument is that per-term routes give
   Pagefind 30 targeted results instead of one, and give forum posters a URL to
   paste.
4. Is the auto-linking plugin wanted at all, or is a static glossary link in the
   nav enough? It is the only part of this plan that silently rewrites 117
   update bodies at build time.
5. Which terms get `autolink: false`? `CAN` and `EVO` are short enough to
   produce noise; `NEXAI` and `FIBO` only occur inside identifiers.
6. The definitions have to be written by someone who knows the hardware. Is
   there an existing Discord pinned message or forum post to lift them from,
   rather than writing 30 definitions from scratch?
7. `src/data/faq/ksw/install-mcu-updates.md` has two steps numbered `3`. Noticed
   while reading for the callout wording. Not touched.
