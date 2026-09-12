# AGENTS.md

Operator guide for AI assistants (Claude Code, Cursor, etc.) working on this
repo. The conventions below cover what's *implicit* in the codebase — things
that are easy to get wrong without context.

## Repo at a glance

- Astro 7, Tailwind 4, TypeScript 6, MDX, static output, GitHub Pages.
- Content lives in `src/data/<collection>/` and is loaded via
  `src/content.config.ts`. Pages in `src/pages/` consume those collections.
- Site is published at `https://kamilbrk.github.io/headunits` — note the
  base path `/headunits/`. Always build URLs from `URL_PREFIX` in
  `src/shared/config.ts`, never hardcode `/foo`.
- No tests. Verification is `npm run lint` + `npx astro check` + `npm run build`.

## Commands you can run

```sh
npm run dev          # local dev
npm run build        # produces dist/
npm run preview      # serves dist/ locally
npm run lint         # eslint
npm run lint:fix     # eslint --fix
npm run prettier     # prettier --write across src/
npx astro check      # type check (.astro + .ts) — runs in CI
```

CI gate (`.github/workflows/ci.yml`) runs lint, `astro check`, build and a
smoke test over the built artifacts. All must pass before deploy. Don't
merge if any is red.

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
  four sites that need it: `src/pages/updates/[...slug].astro`,
  `src/pages/updates/[slug].astro`, `src/pages/themes/[...slug].astro` and
  `src/shared/delimited-links.component.astro`.
  Whitespace between flex/grid items is discarded by layout anyway, so
  `.astro` inside a `flex` container (the prev/next buttons, the
  factory-settings `&lpar;…&rpar;` spans) needs no `{' '}`.
  **Nothing in CI catches this** — not `astro check`, not ESLint, not the
  smoke test. Diff the built HTML in `dist/` when touching inline markup.
- **Three `.astro` files are ignored by ESLint**
  (`navigation.component.astro`, `color-scheme.component.astro`,
  `pages/search.astro`). `eslint-plugin-prettier` mis-parses inline
  `<script>` blocks and reports spurious "Unexpected token" errors.
  Plain `prettier-plugin-astro` still formats them via `npm run
  prettier`. If you add another `<script>` block that trips the same
  parser bug, add it to the ignore list rather than fighting it.
- **Search is provided by Pagefind.** `npm run build` runs
  `astro build && pagefind --site dist`, which indexes the built site
  into `dist/pagefind/`. The `/search` page loads the Default UI at
  runtime. Don't drop the `pagefind` step from the build script or
  `/search` becomes inert.
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

## Patterns for adding a new page

1. Register a collection in `src/data/<name>/index.ts` and add it to
   `src/content.config.ts`.
2. Add content files under `src/data/<name>/`.
3. Create the page in `src/pages/<route>.astro`. For dynamic routes, use
   `getEntryStaticPathsFromCollection` or
   `getFirstLevelStaticPathsFromCollection` from `src/shared/utilities.ts`.
4. Use the `<Layout>` from `src/shared/layout/base-layout.astro` for
   consistent head meta and styling. Pass `title` and (optionally)
   `description`.
5. Build URLs via `URL_PREFIX`. Never hardcode the base path.
6. Run `npm run lint && npx astro check && npm run build` before
   pushing.

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
