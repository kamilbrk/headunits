# Plans

Design documents for work that is planned but not started. Each one is written
against the repo as it stands, cites real files and real content, and breaks
into phases that ship something useful on their own. None of them have been
implemented.

| Plan | What it covers |
| ---- | -------------- |
| [factory-config-builder.md](./factory-config-builder.md) | Turn the decorative factory-settings controls into a client-side editor for the user's own `factory_config.xml`, with a diff and a download. Parsing stays in the browser. |
| [home-page-and-entry-points.md](./home-page-and-entry-points.md) | Replace the static home page with latest updates, recent themes and a "which unit do I have" entry point; promote the upgrade path out of the FAQ. |
| [platform-pages.md](./platform-pages.md) | Render the `platforms` collection, whose `build.prop` dumps and SoC details currently appear nowhere. |
| [theme-discovery.md](./theme-discovery.md) | Brand filtering and landing pages across 87 themes, fix the ZXW sort order, and surface the 23 themes with no screenshots. |
| [changelog-automation.md](./changelog-automation.md) | Generate the "Changes since X built N days earlier" line from collection data instead of hand-writing it. |
| [glossary-and-safety.md](./glossary-and-safety.md) | A glossary for the terms newcomers hit immediately, and the safety warnings the site currently has none of. |
| [contributing-and-edit-links.md](./contributing-and-edit-links.md) | An in-site contribute page, "edit on GitHub" links, and issue templates for people who don't use git. |

## Open questions carried across the plans

- **m701.** `src/data/updates/ksw/m701/` holds two icon images and nothing else
  — no platform entry, no update markdown, and the files are untracked, so CI
  never sees them. Is `WITSTEK-T-M701-OS_EN_v1.5.5_20241227` a real release?
- **ZXW upgrade path.** KSW has a documented version chain; ZXW firmware is
  datestamped with no chain, so a ZXW equivalent may not be meaningful.
- **Theme tag vocabulary is inconsistent** and has to be settled before any
  tag-driven filtering works: `benz-ngt7` is a typo for `benz-ntg7`, ZXW uses
  `bmw-pemp`/`bmw-gs` where KSW uses bare `pemp`/`gs`, and
  `44-KSW_COMMON_ID7` has no `bmw` tag at all.
- **Two ZXW themes are referenced but missing.** `KSW_SAILOR_T002` (id 101) and
  `KSW_SAILOR_T003` (id 102) are described in
  `src/data/updates/zxw/gt6/20240131GT_KSW.md` but have no entry in the themes
  collection, so the links to them were removed rather than left broken.
