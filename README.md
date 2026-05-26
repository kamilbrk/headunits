# Android Head Units

Community-driven information site about third-party Android replacement car
screens from KSW and ZXW vendors — firmware updates, themes, factory settings
and FAQ entries for car brands like Audi, Benz, BMW, Mini, and others.

Live at <https://kamilbrk.github.io/headunits>.

Built with [Astro](https://astro.build/), Tailwind, MDX content collections,
and deployed as a static site to GitHub Pages.

Page-view analytics via [Umami](https://cloud.umami.is/share/8R1nnmhhvAB4cMYj/kamilbrk.github.io).

---

## Development

```sh
nvm use       # picks up .nvmrc (Node 24)
npm install
npm run dev   # local dev server
npm run build # static build into dist/
npm run preview
```

Other useful scripts:

| Command            | What it does                                    |
| ------------------ | ----------------------------------------------- |
| `npm run lint`     | Run ESLint over `src/`                          |
| `npm run lint:fix` | Apply autofixable ESLint rules                  |
| `npm run prettier` | Run Prettier across all source files            |
| `npx astro check`  | Type-check `.astro` and `.ts` files             |

CI runs `lint` + `astro check` on every push and PR. Build and deploy
gate on those passing.

---

## Contributing content

All content lives under `src/data/<collection>/`. Each entry is a
Markdown (or MDX, for updates) file with frontmatter that has to match
the collection's zod schema in `src/data/<collection>/index.ts`.

### Themes — `src/data/themes/<vendor>/<theme-folder>/index.md`

```yaml
---
id: Audi_mib3            # required, matches the folder name
display: Audi MIB3       # optional, friendlier label
number: 23               # optional, ZXW theme number
tags: [audi, audi-mib3]  # optional, used for filtering/styling
images:                  # optional, screenshots colocated in the folder
  - ./home.png
  - ./settings.png
since: 'Ksw-Q-...-ota'   # optional, update ID(s) where the theme was introduced
client: ''               # optional, required factory-config client value
invalid: ''              # optional, marker that the theme is broken
---
```

### Updates — `src/data/updates/<vendor>/<platform>/<id>.md` (or `.mdx`)

```yaml
---
id: Ksw-Q-Userdebug_OS_v4.3.3-ota
vendor: ksw
platform: m501
date: 2024-12-01
android: 10
version: '4.3.3'
signatures:
  md5: '...'
  sha1: '...'
  sha256: '...'
---
```

Markdown body describes what's new in the update.

### FAQ — `src/data/faq/<vendor>/<slug>.md`

```yaml
---
question: How do I pull the factory config from my unit?
---
```

Body is the answer, in Markdown.

### Factory settings — `src/data/factory-settings/<vendor>/<slug>.md`

```yaml
---
section: Sound
settings:
  - name: Balance
    configKey: BAL
    control: range
    min: -10
    max: 10
    children: []
---
```

`settings[]` is recursive — items can contain `children: [...]` with the
same shape.

### Vendors and platforms

`vendors` (`ksw`, `zxw`) and `platforms` (`m501`, `m600`, `m700`, `m701`,
`gt6`, `gt7`) are stable — edit only if you're adding a new vendor or
platform.

---

## Project layout

```
.github/workflows/deploy.yml   CI: verify (lint + check) → build → deploy
.github/dependabot.yml         Monthly grouped dependency PRs
public/                        Static assets served as-is (XML configs,
                               OG image, robots.txt, helper scripts)
src/data/                      Content collections (themes, updates,
                               faq, factory-settings, platforms, vendors)
src/pages/                     Astro routes, including dynamic [slug]
src/shared/                    Layout, components, helpers, site config
src/content.config.ts          Collection registration
astro.config.ts                Astro config (integrations, output, image)
```

---

## Deployment

Pushing to `main` runs the GitHub Actions workflow in
`.github/workflows/deploy.yml`:

1. **verify** — `npm ci`, `npm run lint`, `npx astro check`.
2. **build** — `withastro/action` produces the static site.
3. **deploy** — `actions/deploy-pages` publishes to GitHub Pages.

Pull requests run the verify job only.

---

## Helper scripts in `public/`

- `script.sh` plus `bin/` (`ext4fuse`, `sdat2img.py`) — utility for
  unpacking OTA updates locally on macOS/Linux. See the comments inside
  `script.sh` for prerequisites and usage. These files ship at
  `/script.sh` and `/bin/<file>` from the deployed site.
- `factory_config.xml`, `zxw_factory_config.xml` — example factory
  configs surfaced inside the factory-settings pages.

---

## License

MIT — see `package.json`.
