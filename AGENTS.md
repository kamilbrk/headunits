# AGENTS.md

Operator guide for AI assistants (Claude Code, Cursor, etc.) working on this
repo. The conventions below cover what's *implicit* in the codebase — things
that are easy to get wrong without context.

## Repo at a glance

- Astro 7, Tailwind 4, TypeScript 6, MDX, static output, GitHub Pages.
- Content lives in `src/data/<collection>/` and is loaded via
  `src/content.config.ts`. Pages in `src/pages/` consume those collections.
- Site is published at `https://kamilbrk.github.io/headunits` — note the
  base path `/headunits/`. In `.astro` files always build URLs from
  `URL_PREFIX` in `src/shared/config.ts`. In **Markdown content** write
  root-relative links without the base path (`/updates/ksw`);
  `src/shared/base-path.plugin.ts` prefixes `BASE` at build time. Never write
  `/headunits/...` by hand in either place.
- No unit tests. Verification is `npm run lint` + `npx astro check` +
  `npm run build` + `npm run check:html` + `npm run check:links`. The last two
  read `dist/`, so they need a build first.

## Commands you can run

```sh
npm run dev          # local dev
npm run build        # produces dist/
npm run preview      # serves dist/ locally
npm run lint         # eslint
npm run lint:fix     # eslint --fix
npm run prettier     # prettier --write across src/
npx astro check      # type check (.astro + .ts) — runs in CI
npm run check:html   # html-validate over dist/ — runs in CI
npm run check:links  # internal link check over dist/ — runs in CI
```

CI gate (`.github/workflows/ci.yml`) runs lint, `astro check`, build, a
smoke test over the built artifacts, HTML validation and the internal link
check. All must pass before deploy. Don't merge if any is red.

## Conventions to honor

- **Node floor is `>=24.16.0`**, pinned exactly in `.nvmrc` (24.21.0) so CI
  and local agree. The floor comes from `eslint-plugin-astro` /
  `astro-eslint-parser`, which declare `^22.22.3 || ^24.16.0 || >=26.3.0` —
  not from Astro itself, which only needs `>=22.12.0`.
- **Exact-pinned dependencies.** `package.json` has no `^` or `~`. Bump
  versions explicitly via `npm install <pkg>@<version>` or via the
  monthly Dependabot PRs. Don't reintroduce caret ranges.
- **LF line endings, UTF-8, 2-space indent** — enforced by `.editorconfig`,
  Prettier, and ESLint.
- **Vite override** in `package.json` pins transitive Vite to `^8`, matching
  the `vite: ^8.0.13` that `astro@7` depends on directly. It keeps every
  transitive copy of Vite on one major so a stale `^7` can't be hoisted back
  in. Don't lower it below `^8` while on Astro 7.
- **`compressHTML` defaults to `'jsx'` on Astro 7**, not `true`. Any
  whitespace *containing a newline* between two adjacent things in a line of
  markup is stripped, not collapsed to a space. That covers text →
  `{expression}`, text → `<Component />`, **and element → element**
  (`</a>` newline `<span>`). So `for\n{vendor.data.name}` renders `forKSW`,
  and `</a>\n<span>(A13)</span>` renders `…-ota(A13)`.
  Whitespace *without* a newline is preserved, so same-line markup is safe.
  Fix by putting an explicit `{' '}` at the end of the preceding line. The
  sites that need it today: `src/pages/updates/[...slug].astro`,
  `src/pages/updates/[slug].astro`, `src/pages/themes/[...slug].astro` and
  `src/pages/factory-settings/[slug].astro`.
  `src/shared/delimited-links.component.astro` instead keeps its separators
  inside string expressions (`{', '}`, `{' and '}`), which is equivalent and
  survives reformatting.
  Whitespace between flex/grid items is discarded by layout anyway, so
  `.astro` inside a `flex` container (the prev/next buttons, the
  factory-settings `&lpar;…&rpar;` spans) needs no `{' '}`.
  **Nothing in CI catches this** — not `astro check`, not ESLint, not the
  smoke test. Diff the built HTML in `dist/` when touching inline markup.
- **Four `.astro` files are ignored by ESLint**
  (`navigation.component.astro`, `color-scheme.component.astro`,
  `color-scheme-bootstrap.component.astro`, `pages/search.astro`).
  `eslint-plugin-prettier` mis-parses inline `<script>` blocks and reports
  spurious "Unexpected token" errors.
  Plain `prettier-plugin-astro` still formats them via `npm run
  prettier`. If you add another `<script>` block that trips the same
  parser bug, add it to the ignore list rather than fighting it.
- **Search is provided by Pagefind**, wired through the `astro-pagefind`
  integration in `astro.config.ts` — not a separate step in the build
  script. It indexes `dist/` into `dist/pagefind/` and `/search` loads the
  Default UI at runtime. Search facets come from `data-pagefind-filter`
  attributes emitted by `base-layout.astro`: **one element per facet**.
  Pagefind does not parse a comma-separated list in a single attribute — it
  stores the whole string as one literal value.
- **`getEntry` returns `T | undefined`** under Astro 7. Pages use a
  `if (!x) throw new Error(...)` narrow after each lookup — keep that
  pattern; don't sprinkle non-null assertions.
- **Collection-specific helpers in `src/shared/utilities.ts`** are typed
  narrowly to the collection they're called for
  (`sortEntriesByDate` → `'updates'`, `sortEntriesByDataId` → `'themes'`,
  `getAndroidVersion`/`getUpdateVersion` → `'updates'`,
  `getEntryWithPrevNext` → `'updates'`). Don't re-widen them to
  `<E extends CollectionKey>` — the bodies access collection-specific
  fields that don't exist on other schemas.
- **Image `alt` text must be meaningful** for content images (theme
  screenshots, the home hero). Decorative-only images can keep `alt=""`,
  but err on the side of describing.
- **No Alpine.js** — sidebar toggle is plain JS in
  `navigation.component.astro`. Re-binds on `astro:page-load` for view
  transition support.
- **OG image lives at `public/og-image.jpg`** (stable URL) and is wired
  through `base-layout.astro`. If you swap the home hero, update both
  references.
- **Colour scheme is applied twice, on purpose.**
  `color-scheme-bootstrap.component.astro` runs an `is:inline` script in
  `<head>` so the theme is set before first paint;
  `color-scheme.component.astro` owns the toggle and the `astro:after-swap`
  re-apply. `<html>` carries no default class — adding one back reintroduces
  a flash of the wrong theme for every visitor whose preference differs.
- **Markdown is processed by Sätteri, not remark/rehype.** Plugins go in
  `satteri({ hastPlugins: [...] })` in `astro.config.ts`. Setting
  `markdown.rehypePlugins` fails the build unless `@astrojs/markdown-remark`
  is installed, which would switch the whole pipeline back to unified.
- **`doctype-style` is off in `.htmlvalidate.json`.** Astro writes the doctype,
  not us, and it emits `<!doctype html>` on generated redirect pages while
  normalising authored pages to `<!DOCTYPE html>`. The casing has no effect on
  HTML5 parsing, so the rule only produced a failure nobody could act on.
- **Check the exit code of the `check:*` scripts, not their last line of
  output.** `npm run check:html | tail -1` prints a blank line on failure and
  discards the status, which is how a real `html-validate` failure reached CI.
- **`:::warning` callouts** come from `src/shared/callout.plugin.ts`, a Sätteri
  mdast plugin, with `features: { directive: true }` enabled in
  `astro.config.ts`. That flag changes how `:::` parses in *every* content
  file, so check `grep -rn ':::' src/data/` before changing it. Unknown
  directive names are left untouched rather than swallowed. Styling is plain
  CSS in `global.css`, not utility classes — Tailwind does not scan markup
  generated inside a plugin.
- **Glossary terms are linked automatically.** `src/shared/autolink.plugin.ts`
  links the first mention of each glossary term in a Markdown body to its
  anchor on `/glossary`; the dictionary is read off disk by
  `src/shared/entity-dictionary.ts`, since `getCollection` isn't available
  while the Astro config resolves. Don't hand-write `[MCU](/glossary#mcu)` in
  content. A term that only appears inside a larger identifier, or that
  collides with an ordinary word, opts out with `autolink: false` in its
  frontmatter (`nexai`, `platform`, `gs` do today). `npm run check:autolinks`
  guards the output and carries an expected site-wide count — update
  `EXPECTED_TOTAL` in the script when content moves it on purpose.
- **Firmware version ids and theme ids are linked automatically too.** Write
  `` `Ksw-T-M600_OS_v1.4.8-ota` `` or `UI_GS_ID8` in prose and the plugin links
  it; don't hand-write the link. Unlike glossary terms these link at *every*
  mention, because each is an exact identifier. A page never links its own id,
  and a name belonging to two entries (KSW and ZXW both have a `LEXUS_UI`) is
  left unlinked rather than guessed at. Links whose visible text is *not* the
  id — `[1.3.5](…)`, `[first GT7](…)` — stay hand-written; there is nothing to
  regenerate them from.
- **`scripts/link-snapshot.mjs` + `scripts/link-diff.mjs` answer "did any link
  on the site change?"** Build, snapshot, make the change, build, snapshot,
  diff. Snapshots go in the scratchpad, never in the repo. They are what proved
  the 123 hand-written entity links could be deleted: 6753 links across 251
  pages, byte-identical before and after.
- **A plugin change alone may not show up in `dist/`.** Astro caches rendered
  Markdown in `node_modules/.astro/data-store.json`, keyed on the content
  files, so editing `callout.plugin.ts` or `autolink.plugin.ts` and rebuilding
  can silently reuse the old HTML. Editing `astro.config.ts` or the content
  itself does invalidate it. Delete that file before trusting a local build of
  a plugin change; CI starts from a clean checkout and is unaffected.
- **Use `astro/zod`, not `astro:schema`** — the latter is deprecated in
  Astro 7 and removed in Astro 8.
- **Factory-settings `configKey` values are checked at build time.**
  `src/shared/factory-config/validate-keys.ts` runs from
  `src/pages/factory-settings/[slug].astro` against the example XML in
  `public/`, and throws on a key that file does not carry, a key claimed by two
  settings, a checkbox with a key but no `onValue`/`offValue`, or a radio group
  whose children have no `configValue`. A key we have documented but never seen
  in a real file says so with `unverified: true`; a row that must never become
  a live control says `editable: false` and usually carries a `warning`.
  Checkbox on/off values are never inferred — the vendor writes
  `0: allow  1: Prohibited` in places.
- **Tailwind scans prose, not just markup** — TypeScript comments, Markdown
  bodies, and files like this one. A doc comment that happens to contain a
  utility's name adds that utility to the built CSS and changes its hash. It is
  harmless, and it is the answer when the stylesheet moves and nobody touched a
  class.
- **The factory-settings pages can read a reader's own config file.**
  `_builder.component.astro` holds the panel and the only client script;
  `_setting.component.astro` emits the `data-config-key` / `data-control` /
  `data-on-value` / `data-config-value` attributes it reads. The file never
  leaves the browser and there is no server to send it to — keep it that way.
  The panel is server-rendered `hidden` and unhidden by the script, so with
  JavaScript off the page is exactly what it was before. Like the other files
  with an inline `<script>`, it is in the ESLint ignore list. A control becomes
  live only for a key the reader's own file carries and that the markdown has
  not marked `editable: false`; enabling one swaps `disabled` /
  `tabindex="-1"` / `aria-hidden` for a real tab stop named by
  `aria-labelledby`. Radios carry a `name` so the group behaves as one — the
  exception to the no-`id`/no-`name` rule below. A `select` gets its choices
  from a list section of the reader's own file via `optionsFrom` in the
  markdown, never from anything we ship, so a firmware carrying themes we have
  never seen still gets a correct dropdown; a current value the list does not
  offer keeps an option of its own rather than being silently swapped for the
  first one. There is no download: the
  example listing at the foot of the page becomes the reader's own file with
  their changes in it, reusing the Shiki `<pre>` so it keeps that block's
  colours and padding and only loses the highlighting. The original markup is
  stashed on load and put back by "Remove file".
- **`npm test` runs `node --test` over `scripts/*.test.mjs`** — no test runner
  and no new dependency, since Node 24 strips the types. It exists for one
  guarantee: `applyEdits` only ever rewrites the bytes between `>` and
  `</key>`, so a reader's comments, indentation and unknown elements come back
  untouched. The tests read the real files in `public/`, so they track what
  ships. `tsconfig` sets `allowImportingTsExtensions` so those modules can
  import each other with an explicit `.ts`, which is what Node's own resolver
  needs.
- **`npm run test:e2e` runs Playwright over the builder**, the one part of the
  site with real client state. It tests the **built** site: `playwright.config.ts`
  starts `npm run preview`, so run `npm run build` first or the server has
  nothing to serve. Specs live in `e2e/` and use role-based locators, per
  Playwright's own guidance — the single exception is the file listing, which is
  raw text with no accessible representation and is reached by attribute. Two
  projects, desktop Chromium and mobile WebKit; the clipboard test is Chromium
  only, since that permission does not exist elsewhere. It runs as its own CI
  job so a flaky browser cannot hold up the deploy, which `verify` alone gates.
  That job runs inside `mcr.microsoft.com/playwright:v<version>-noble`, which
  ships the browsers and their system dependencies, so there is no
  `playwright install` step — Playwright's own CI guide recommends this over
  caching browser binaries, which takes about as long to restore as to
  download. **Bump the image tag whenever `@playwright/test` moves**; a step in
  the job fails loudly if the two drift apart, which is what Dependabot will
  otherwise cause.
- **`e2e/accessibility.spec.ts` runs axe-core over one page per template**,
  against WCAG 2.1 AA, plus the factory-settings page with its controls live.
  All 19 pass today, so a violation in a new page means that page, not a
  backlog. Add a row to `PAGES` whenever a template is added.
- **Controls on the factory-settings pages start decorative.** They mirror
  what the car screen looks like, so until a reader loads their own file they
  carry `disabled`, `tabindex="-1"` and `aria-hidden="true"` and have no `id`
  or `<label>`. The only `id` in a settings row is on the `<span>` holding the
  name, for anchor linking. Putting ids back on the inputs produced 90
  duplicate ids on a single page.

## Patterns for adding a new page

1. Register a collection in `src/data/<name>/index.ts` and add it to
   `src/content.config.ts`.
2. Add content files under `src/data/<name>/`.
3. Create the page in `src/pages/<route>.astro`. For dynamic routes, use
   `getEntryStaticPathsFromCollection` or
   `getFirstLevelStaticPathsFromCollection` from `src/shared/utilities.ts`.
   Per-vendor landing pages derive their paths from the **`vendors`**
   collection, not from whichever collection they happen to list.
4. Use the `<Layout>` from `src/shared/layout/base-layout.astro` for
   consistent head meta and styling. Pass `title` and (optionally)
   `description`.
5. Build URLs via `URL_PREFIX`. Never hardcode the base path.
6. Run `npm run lint && npx astro check && npm run build &&
   npm run check:html && npm run check:links` before pushing.

## Things to avoid

- Removing the `vite: ^8` override.
- Hardcoding `/headunits/...` URLs.
- Adding `// @ts-ignore`, `@ts-expect-error`, non-null assertions, or
  `as any` casts unless there's a specific reason (and a comment).
- Reintroducing CRLF line endings.
- Mutating files outside `src/`, `public/`, or config (except for the
  changes the task explicitly asks for).
- Touching `.astro` / `.git` / `node_modules` directly.

## References

- [Astro docs](https://docs.astro.build/)
- [Astro content collections](https://docs.astro.build/en/guides/content-collections/)
- [Tailwind v4 docs](https://tailwindcss.com/docs)
- [Upgrade to Astro v7](https://docs.astro.build/en/guides/upgrade-to/v7/) — `compressHTML`, the Rust compiler, and the Sätteri Markdown processor.
