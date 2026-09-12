# Contributing: in-site page, edit links, and a no-git path

## Problem

`README.md` documents the content model properly — the directory layout, the
frontmatter shape for each of the six collections, which fields are required.
None of it is reachable from the site. The deployed pages never mention GitHub,
never link to the repository, and contain exactly one invitation to contribute:

> "We don't have any screenshots of this theme yet. You can try to activate
> this theme, take some screenshots and contribute!"
> — `src/pages/themes/[...slug].astro:63-66`

with no link on the word "contribute", and no hint of where to send a
screenshot. The gallery tile has the same dead end: a "No screenshot yet"
placeholder at `src/pages/themes/_list-item.component.astro:34`.

The cost is measurable. **23 of the 87 theme entries have no `images:` field
at all.** One is KSW (`src/data/themes/ksw/BMW_EVO_ID6_CUSP/index.md`); the
other 22 are ZXW. The gap is not spread evenly — **every ZXW theme numbered 43
and above is missing screenshots** (`43-KSW_AUDI_PORSCHE` through
`56-KSW_BMW_ID9`, 14 consecutive entries), plus `19`, `20`, `26`, `29`, `34`,
`35`, `39` and `40`. That newest block is precisely the set a GT7 owner on
current firmware is choosing between, and
`src/data/updates/zxw/gt7/20250718GT_KSW.md:21` documents new BMW settings on
the `KSW_BMW_ID9` theme that nobody can see.

Screenshots are also the single cheapest contribution anyone can make. They
need a phone camera and no git.

## Part 1 — "Edit this page on GitHub"

### `filePath` is available, and this is verified

Astro 7's glob loader stores a repository-root-relative POSIX path on every
entry and it survives to userland:

- The loader sets it:
  `node_modules/astro/dist/content/loaders/glob.js:103` computes
  `posixRelative(fileURLToPath(config.root), filePath)` and assigns it as
  `filePath` on the stored entry (lines 150, 160, 169).
- `getCollection` spreads the stored entry, so the field is not stripped:
  `node_modules/astro/dist/content/runtime.js:80-84`.
- It is typed. The generated `.astro/content.d.ts` declares
  `filePath?: string` on the entry type of all six collections (lines 144, 153,
  162, 171, 180, 189), so `CollectionEntry<'updates'>['filePath']` is
  `string | undefined`.
- Confirmed against real data rather than only the types: decoding
  `.astro/data-store.json` yields `src/data/factory-settings/ksw/01-function.md`
  for the `ksw/01-function` entry. Repository-root relative, forward slashes,
  file extension included.

Two consequences for implementation:

- The type is optional and `tsconfig.json` extends `astro/tsconfigs/strictest`,
  so it needs a real guard. AGENTS.md forbids adding non-null assertions, so the
  component renders nothing when `filePath` is absent rather than asserting.
- It already includes the extension, so the URL is a plain concatenation. No
  reconstruction from `entry.id`, which would be wrong anyway: `entry.id` is the
  slugified route segment (`ksw/m600/ksw-t-m600_os_v174-ota`), not the filename
  (`Ksw-T-M600_OS_v1.7.4-ota.md`).

### Config

Add to `src/shared/config.ts`, next to `DOMAIN` and `BASE`:

```ts
export const REPOSITORY = 'https://github.com/kamilbrk/headunits';
export const REPOSITORY_BRANCH = 'main';
```

The repository URL is already in `package.json` under `repository.url`, but
importing `package.json` into runtime code to get one string is not worth the
resolution and typing noise.

Important and worth a comment in the file: this is an **external** URL, so
`URL_PREFIX` does not apply to it and must not be prepended. The AGENTS.md rule
about never hardcoding the base path is about site-internal links; someone
applying it mechanically here would produce
`https://github.com/headunits/kamilbrk/...`.

### Component

`src/shared/edit-on-github.component.astro`:

```astro
interface Props {
  filePath?: string | undefined;
}
```

Renders nothing when `filePath` is falsy. Otherwise a small link to
`` `${REPOSITORY}/edit/${REPOSITORY_BRANCH}/${filePath}` ``, marked
`data-pagefind-ignore` so it does not pollute search excerpts, and
`target="_blank"` to match the external-link handling already used for the
Discord entry in `src/shared/layout/navigation.component.astro:102`.

`/edit/` rather than `/blob/`: GitHub's edit route opens the web editor and
silently forks for anyone without write access, which is the whole point — a
drive-by typo fix becomes a pull request without the contributor cloning
anything.

Watch the `compressHTML: 'jsx'` behaviour documented in AGENTS.md if the link
sits inline next to text; a trailing `{' '}` is needed on the preceding line.

### Where it goes

Detail pages, where exactly one content file backs the page:

| Page | Entry in scope |
| --- | --- |
| `src/pages/updates/[...slug].astro` | `entry` from `getEntryWithPrevNext` |
| `src/pages/themes/[...slug].astro` | `entry` from `getEntry('themes', slug)` |
| `src/pages/faq/[...slug].astro` | `entry` from `getEntry('faq', slug)` |
| `src/pages/factory-settings/_section.component.astro` | the section entry it already fetches |

The factory-settings case is per-section rather than per-page:
`src/pages/factory-settings/[slug].astro` renders every section for a vendor
through `_section.component.astro`, so one link per section heading is both
achievable and more precise than one link for the page.

Aggregate pages have no single source file and should not get an edit link:
`src/pages/faq/[slug].astro`, `src/pages/factory-settings/[slug].astro`,
`src/pages/themes/[slug].astro`, `src/pages/updates/[slug].astro`,
`src/pages/index.astro`. They get a link to the Contribute page instead.

## Part 2 — an in-site Contribute page

`src/pages/contribute.astro`, route `/contribute`, linked from the `General`
section of the `menu` array in `src/shared/layout/navigation.component.astro:15`
alongside Home, Search and Discord.

Content, in the order a reader needs it:

1. **What the site is.** One paragraph: community notes assembled by owners,
   everything in a public repository, anyone can change it. Link to the
   repository.
2. **The easiest three things.** Theme screenshots, a firmware changelog for an
   update we have no notes on, and corrections. Each with a one-click issue
   link (see Part 3) and a note that no git is required.
3. **Screenshots, specifically.** State the number — currently 23 of 87 themes
   have none — and link the list. Say what a usable screenshot is: the home
   screen with the theme active, full screen, no phone glare, PNG or WebP.
4. **If you use git.** The collection layout and frontmatter shape, lifted from
   the "Contributing content" section of `README.md` rather than rewritten, so
   the two cannot drift. Link straight to `README.md` on GitHub for the full
   version and keep the on-site copy to the two collections outside
   contributors actually touch: `themes` and `updates`.
5. **What we cannot take.** Firmware binaries — the site describes firmware and
   does not host it. Anything with a real name attached to it. Link to
   [`glossary-and-safety.md`](./glossary-and-safety.md)'s safety page for the
   reasons.

Do not restate the development workflow (`nvm use`, `npm run dev`, the CI gate)
on this page. That is in `README.md` and belongs to people who already cloned
the repository.

### The screenshot gap needs a list, not a number

A sentence saying "23 themes need screenshots" is not actionable. The page
should render the actual list, computed at build time — no hand-maintained
copy that goes stale the moment someone contributes one:

```ts
const themes = await getCollection('themes');
const missing = themes.filter((theme) => !theme.data.images?.length);
```

Grouped by vendor, each linking to its theme page. That gives a GT7 owner a
list of fourteen consecutive themes they can activate and photograph in one
sitting, and it shrinks visibly as people contribute — which is a better
incentive than a static plea.

Cross-reference [`theme-discovery.md`](./theme-discovery.md) before building
this: if that plan adds filtering to the theme gallery, "has no screenshot"
should be one of its filters and this page should link to that filtered view
rather than duplicating the list.

### Wire up the two dead ends

- `src/pages/themes/[...slug].astro:63-66` — make "contribute" a link to
  `/contribute` (built from `URL_PREFIX`).
- `src/pages/themes/_list-item.component.astro:34` — the "No screenshot yet"
  tile. Leave it as a non-interactive placeholder; the whole tile is already a
  link to the theme page via the `absolute inset-0` overlay at line 42, and
  nesting a second link inside it would break that.

## Part 3 — a path for people who will not use git

GitHub issue forms under `.github/ISSUE_TEMPLATE/`. The directory does not
exist yet; `.github/` currently holds only `dependabot.yml` and
`workflows/ci.yml`.

### `theme-screenshots.yml`

Fields: vendor (dropdown: KSW / ZXW), theme id or number, which firmware build
the screenshots were taken on, and a required textarea saying "drag your
screenshots into this box".

The textarea is not a stylistic choice. **GitHub issue forms have no
file-upload field type.** Attachments only work by dragging files into a
markdown textarea, so the template has to say so explicitly or people will look
for an upload button that is not there.

### `firmware-changelog.yml`

Fields matching the `updates` schema in `src/data/updates/index.ts` so a
maintainer can transcribe an issue into a file without a follow-up
conversation: vendor (dropdown), platform (dropdown: m501, m600, m700, gt6,
gt7), firmware id as it appears on the unit, build date, md5 / sha1 / sha256 if
known, and a free-text "what changed". Note in the description that 40 of the
117 update entries currently have no notes at all — the "We do not have any
information about what's new in this update" pages are the ones this form
exists to fill.

### `correction.yml`

Page URL, what is wrong, what it should say. Small.

### `config.yml`

```yaml
blank_issues_enabled: true
contact_links:
  - name: Ask on Discord
    url: https://discord.gg/Ex8e6qE2eR
    about: Questions, help with a unit, and where firmware files circulate.
```

The Discord invite is already in
`src/shared/layout/navigation.component.astro:21` — take it from there rather
than from memory, and keep the two in sync.

Deliberately **not** proposed: an issue form for factory settings. The
`factory-settings` schema is a recursive `settings[]` YAML array
(`src/data/factory-settings/index.ts`), and transcribing one from prose is
error-prone enough that it wants its own tooling. See
[`factory-config-builder.md`](./factory-config-builder.md).

Also not proposed: a pull-request template. There are few enough external PRs
that a template is ceremony; revisit if that changes.

## Phases

### Phase 1 — Contribute page and nav entry

`src/pages/contribute.astro` with the build-time list of themes missing
screenshots, plus the nav entry and the two theme-page links. No `.github/`
changes, no new config constants beyond `REPOSITORY`.

Ships alone, and is the phase that actually moves the screenshot number: it is
the first time the site tells anyone that contributing is possible.

### Phase 2 — Issue templates

`.github/ISSUE_TEMPLATE/` with the three forms and `config.yml`. Link them from
the Contribute page and from the screenshot list. Nothing in `src/` changes
except the hrefs.

Ships alone: the forms work from the repository's Issues tab whether or not
anything links to them.

### Phase 3 — Edit links

`REPOSITORY` / `REPOSITORY_BRANCH` in `src/shared/config.ts`,
`src/shared/edit-on-github.component.astro`, and the four render sites.

Verify with `npm run lint && npx astro check && npm run build`, then check the
built HTML for one page per collection — in particular that `filePath` survived
into the URL with its original casing and extension
(`.../edit/main/src/data/updates/ksw/m600/Ksw-T-M600_OS_v1.7.4-ota.md`), since
the route slug is lowercased and dot-stripped and a mistake here produces a
plausible-looking 404.

### Phase 4 — optional: a README pointer back

Add a short "Where this shows up on the site" line to `README.md`'s
"Contributing content" section pointing at `/contribute`, so the two directions
are linked. One line, not a section.

## Open questions

1. Should the edit link say "Edit this page on GitHub", "Suggest an edit", or
   "Improve this page"? The first is the convention; the second is more honest
   about what happens for someone without write access (a fork and a PR).
2. `/contribute` or `/contributing`? The nav label matters more than the route,
   but the route is permanent.
3. Should the theme-screenshot list live on `/contribute`, or become a filter on
   the theme gallery that `/contribute` links to? Depends on what
   [`theme-discovery.md`](./theme-discovery.md) lands.
4. Is `blank_issues_enabled: true` right? Leaving it on means people can open
   anything, which is friendlier but means the forms get bypassed.
5. Does the Discord community want issue links pointed at them, or is Discord
   deliberately the front door with GitHub kept for maintainers? This changes
   whether `config.yml`'s contact link is first or last in the chooser.
6. `REPOSITORY_BRANCH` is hardcoded to `main`. Editing from a page built off a
   feature branch would send contributors to `main`, which is almost always what
   is wanted — but confirm that is intentional rather than reading the current
   branch.
7. `src/data/updates/ksw/m701/` holds two icon assets with no entry file, and
   `m701` has no file in `src/data/platforms/`, so the platform dropdown in
   `firmware-changelog.yml` omits it. Is m701 a real platform that is simply
   undocumented, or leftover assets? Noticed while enumerating platforms; not
   touched.
