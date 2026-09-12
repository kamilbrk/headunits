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
- **Use `astro/zod`, not `astro:schema`** — the latter is deprecated in
  Astro 7 and removed in Astro 8.
- **Controls on the factory-settings pages are decorative.** They mirror
  what the car screen looks like and serve no form purpose, so they carry
  `disabled`, `tabindex="-1"` and `aria-hidden="true"` and deliberately have
  no `id`, `name` or `<label>`. The only `id` in a settings row is on the
  `<span>` holding the name, for anchor linking. Putting ids back on the
  inputs produced 90 duplicate ids on a single page.

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
