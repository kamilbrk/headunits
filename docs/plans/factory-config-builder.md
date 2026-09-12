# Factory config builder

Status: draft plan, not started.
Scope: `src/pages/factory-settings/*`, `src/data/factory-settings/*`,
`src/shared/factory-config/*` (new).
Written against the working tree at the time (branch `fix/site-audit-round-1`,
with uncommitted changes to `_setting.component.astro`, `base-layout.astro` and
`[slug].astro` already applied) — re-check section 8 if those land differently.

---

## 1. Goal, user stories, non-goals

### Goal

Turn `/factory-settings/ksw` and `/factory-settings/zxw` from a page of
*decorative, disabled* controls into a client-side editor for the user's own
`factory_config.xml` / `zxw_factory_config.xml`. The user supplies their file,
the site reads the real values into the controls, the user changes what they
want, and the site hands back a modified file plus a readable list of what
changed.

Hard constraint: the site is `output: 'static'` on GitHub Pages under base
`/headunits/`. There is no server. The file never leaves the browser.

### User stories

1. As an owner of a KSW M600, I drop my `factory_config.xml` onto the
   factory-settings page and see that `USB_HOST` is currently `0`, `GoogleAPP`
   is `1`, and `UI_type` is `BMW_EVO_ID7_V2` — reflected in the checkboxes and
   selects that today are dead.
2. I tick "USB HOST", pick "Android Interface" under Boot Mode Memory, and the
   page marks both rows as changed.
3. I open the diff panel and read
   `USB_HOST: 0 → 1` and `Default_PowerBoot: 0 → 2` before I commit to
   anything.
4. I press Download and get a file that is byte-identical to the one I supplied
   except for those two element values — same comments, same indentation, same
   `name = "com.waze"` attribute spacing, same `″` characters.
5. I press Reset and go back to my uploaded file's values without re-uploading.
6. I have JavaScript off (or the script fails). The page still shows exactly
   what it shows today: the documented settings, the config key names, and the
   example XML listing.
7. I am nervous about bricking the unit. Before I can download anything, the
   page has told me to back up the original file and linked
   `/faq/ksw/pull-factory-config`.

### Non-goals

- No writing to the head unit. No ADB, no WebUSB, no network of any kind.
- No validation that a given value is *safe for your car*. We surface the
  vendor's own comments; we do not claim a combination is correct.
- No editing of list sections (`<SupportNaviAppList>`, `<AppsWhiteList>`,
  `<SupportUIList>`, `<CarDisplayParam>`, `<CANBusProtocol>`). Phase 1-4 read
  those lists to populate dropdown options but never rewrite them. Adding a
  navigation app stays a manual text edit.
- No account, no server-side persistence, no share links containing config.
- No support for arbitrary head unit vendors beyond KSW and ZXW.
- No attempt to *create* a config file from nothing. The builder always starts
  from a user-supplied file. (The shipped example files are fixtures for
  demo/test mode, not a starting point we encourage — `public/factory_config.xml`
  already carries "Never use this entire file as-is".)
- Not a replacement for the existing example-XML listing at the bottom of
  `src/pages/factory-settings/[slug].astro`. That stays.

---

## 2. The real XML format, and how it maps to the markdown schema

### 2.1 Shape

Both files parse clean (verified with a real XML parser against
`public/factory_config.xml` and `public/zxw_factory_config.xml`). Root is
`<ConfigInfo>` in both. Direct children:

| File | Children of `<ConfigInfo>` |
| --- | --- |
| `factory_config.xml` (KSW) | `SupportNaviAppList`, `AppsWhiteList`, `SupportDvrAppList`, `CarDisplayParam`, `CANBusProtocol`, `SupportLanguageList`, `SupportUIList`, `setings`, `factory` |
| `zxw_factory_config.xml` (ZXW) | `basic`, `SupportNaviAppList`, `SupportDvrAppList`, `CarDisplayParam`, `CarDisplayParamMipiScreen`, `CANBusProtocol`, `SupportUIList`, `setings`, `factory` |

Two kinds of content:

**Lists** — repeated children carrying attributes, no editable scalar:

```xml
<SupportNaviAppList>
    <Item name = "com.google.android.apps.maps" /><!-- Google Maps -->
    <Item name = "com.waze" /><!-- Waze -->
</SupportNaviAppList>
```

```xml
<CarDisplayParam>
    <model id = "1"  >[01]NBT_F30/F20/F15/F22/F48(6.5″,HalfScreen)</model>
    <model id = "7"  >[02]NBT_F30/F20/F15/F22/F48(6.5″,FullScreen)</model>
</CarDisplayParam>
```

```xml
<SupportUIList>
    <Item id="1" name="BMW_EVO_ID7_V2" display="BMW ID7 EVO V2" /><!-- requires client ALS_6208 -->
</SupportUIList>
```

ZXW's `SupportUIList` uses a different attribute set entirely:

```xml
<Item id="45" ui="KSW_ALFA_ROMEO" /><!-- GT6-20240613 / GT7-20240525 -->
<Item id="23" ui="KSW_AUDI" />
```

**Scalars** — leaf elements under `<setings>` (sic — the typo is in the real
format, do not "fix" it), `<factory>`, and on ZXW also `<basic>`:

```xml
<!-- Google APP  0:Off  1:On -->
<GoogleAPP>1</GoogleAPP>

<!-- Reverse Camera time  "0-0":disabled "1-1":1 sec up to "1-10" for 10 seconds -->
<!-- do NOT change to "0" it will block Factory settings -->
<Reverse_time>0-0</Reverse_time>

<UI_type>BMW_EVO_ID7_V2</UI_type>
<TXZ_Wakeup>Hello, Serena</TXZ_Wakeup>
```

Only scalars are in scope for editing.

### 2.2 How `configKey` maps today

`configKey` in `src/data/factory-settings/**/*.md` is a **bare element name**,
with no path. Resolution today is "find the element with this tag name". That
happens to work: across both fixture files, no scalar leaf tag name occurs more
than once (checked doc-wide, excluding the list item tags `Item`, `model`,
`Protocol`). But it is luck, not a guarantee — `<ver>`, `<client>` and
`<password>` sit in `<factory>` on KSW and `<ver>`/`<client>` sit in `<basic>`
on ZXW, so one vendor adding the other's block would collide immediately.

Section membership is also not uniform. Of KSW's 34 markdown `configKey`
values, 28 resolve, and two of those live in `<setings>` rather than
`<factory>`:

- `DoNotPlayVideosWhileDriving` → `<setings>` (line 301)
- `Front_view_camera` → `<setings>` (line 313)
- everything else → `<factory>`

All 33 of ZXW's markdown `configKey` values resolve, all inside `<factory>`
except `backlightBrightnessNightShow` which is in `<setings>` (line 538).

The value convention, implicit in `_setting.component.astro`, is:

- `control: checkbox` with no `children` → the element holds `0` or `1`.
  (`_setting.component.astro` literally says this in its tooltip text.)
- A setting with a `configKey` **and** `radio` children → single-select. The
  element holds the selected child's `configValue`.
- `control: range` with `min`/`max` → the element holds an integer in range.

That convention is currently only enforced by whoever writes the markdown. The
builder has to make it a schema rule (section 3).

### 2.3 Where the mapping is incomplete or wrong — be honest

These are real, verified gaps. Every one of them has to be either fixed in the
markdown or explicitly marked "documented but not editable" before the
corresponding control can go live.

**(a) Six KSW `configKey` values name elements that do not exist in
`public/factory_config.xml`:**

| `configKey` | Where | Note |
| --- | --- | --- |
| `APK360` | `ksw/01-function.md`, "360APK" | Not in the file. The file *does* have `<APK_Install>0</APK_Install>` — "Installation of third-party apps 0:allow 1:Prohibited" — which is a different setting and is undocumented in markdown. |
| `forwardCamMirror` | `ksw/01-function.md`, "Front view mirror setting" | Not present. ZXW has `frontCameraMirror`; KSW may use a different name or store it outside the file. |
| `Speed_type` | `ksw/02-vehicle.md` | Not present. ZXW has `speedType`. |
| `DirtTravelSelection` | `ksw/02-vehicle.md`, already annotated `# KeyConfig.DRIVE_TRACK` | Not present. ZXW has `wheelTrack`. |
| `BootUpCamera` | `ksw/02-vehicle.md`, "360 boot up camera" | Not present. ZXW has `bootCamera`. |
| `MicControl` | `ksw/02-vehicle.md` | Not present. ZXW has `micType`. |

The pattern is clear: these six look like ZXW names or decompiled Android
`KeyConfig` constants that were copied into the KSW page. They are guesses, not
observed XML. They must render as **documented-only** rows, not as live
controls, until someone confirms the real KSW element name on a device.

**(b) `BT_Type` is claimed twice in `ksw/01-function.md`** — once as a bare
`control: checkbox` ("BT") and once as a radio group ("Bluetooth Selection",
`1` = Original Car Bluetooth, `0` = Additional Bluetooth). These are the same
XML element with two incompatible control models. Today nothing breaks because
nothing is wired. In a builder they would fight over one value. One of them has
to go, or one has to be marked read-only. **This is a blocker for Phase 2 on
KSW.**

**(c) KSW MIC Gain has no `configKey` at all, and there are three candidate
elements.** `ksw/05-mic-gain.md` declares `control: range, min: 0, max: 20`
with the comment `# 8 on Android 10, 20 on others`. The XML has:

```xml
<!-- M501 (SD625) Mic gain range: 0~8 -->
<mic_gain_m501>2</mic_gain_m501>
<!-- M506 (SD425) MIC gain range: 0~8 -->
<mic_gain_m506>2</mic_gain_m506>
<!-- M600 (SD662) MIC gain range: 0~20 -->
<mic_gain_m600>12</mic_gain_m600>
```

Three keys, three different ranges, and no element for M700 (which
`src/data/platforms/ksw/m700.md` says exists). The builder cannot pick one. It
must either render all present keys as separate sliders (each with the range
from its own comment) or ask the user which platform they have. Recommendation:
render every `mic_gain_*` element found in the user's file, labelled by the
suffix. No platform question. See open question Q3.

**(d) `Reverse_time` is a compound string, not a number.**

```xml
<!-- Reverse Camera time  "0-0":disabled "1-1":1 sec up to "1-10" for 10 seconds -->
<!-- do NOT change to "0" it will block Factory settings -->
<Reverse_time>0-0</Reverse_time>
```

`ksw/06-reverse-exit-time.md` models it as two radios with no `configKey` and a
stray `min: 0 / max: 10` on the second. So the real value is
`"{enabled}-{seconds}"`. The schema has no way to express that today. ZXW splits
the same concept into two elements, `backcarTimeSelection` (0/1) and
`backcarTime` (3) — and `zxw/02-vehicle.md` has `backcarTime` **commented out**
in the frontmatter. The XML's own second comment ("do NOT change to `0`, it
will block Factory settings") is a bricking hazard that the builder must
surface verbatim next to the control.

**(e) Theme selection is a different value type per vendor.**

- KSW: `<UI_type>BMW_EVO_ID7_V2</UI_type>` — a **string**, valid values are
  `SupportUIList/Item/@name`. KSW *also* has `<UI>1</UI>` for Android 7-8,
  which the markdown does not mention at all.
- ZXW: `<uiSelection>23</uiSelection>` — an **integer**, valid values are
  `SupportUIList/Item/@id`, and the human label is `@ui` not `@display`.

`ksw/07-ui-configuration.md` has `configKey: UI_type` and no options.
`zxw/06-ui-configuration.md` has no `configKey` at all ("Current Selection").
Both need `optionsFrom` (section 3) so the dropdown is built from the user's
own file, which is the only correct source — a user's `SupportUIList` may not
match ours.

**(f) Car display and CAN protocol selection have no key on KSW.**
`ksw/03-car-display.md` and `ksw/04-can-protocol.md` have no `settings:` block
at all — just prose. ZXW has `carTypeSelection` ("Original car model display
selection") and `canProtocolSelection` in `<factory>`, but
`zxw/04-car-display.md` and `zxw/05-can-protocol.md` model them as a nameless
"Current Selection" row with no `configKey`. So on both vendors the two most
consequential settings in the whole file are currently unmapped. ZXW is a
one-line markdown fix (`configKey: carTypeSelection`, `optionsFrom:
CarDisplayParam/model`). KSW needs someone to read a real device. **Open
question Q1.**

Also note ZXW ships **three** `<CarDisplayParam>` blocks and **three**
`<CANBusProtocol>` blocks in the file, but two of each are inside XML comments
(lines 181-230 Benz, 232-269 Audi; lines 301-312 Benz, 314-333 Audi). Only one
of each is live. Any parser that regex-scans for `<CarDisplayParam>` without
understanding comments will pick the wrong list. This is the single best
argument for the comment-aware scanner in section 5.

**(g) Several markdown rows are pure UI description with no XML backing**, and
that is fine — they just must not become live controls. Examples:
`ksw/08-profile-import.md` ("Import Configuration", "Restart"),
`ksw/09-boot-logo.md`, `zxw/08-logo-settings.md`, ZXW's "Splitting machine LVDS
mode" (the XML *does* have `<lvdsMode>0</lvdsMode>` — that one is a fixable
gap, not an inherent one), KSW's "Txzing Assistant" (XML has `Support_TXZ`,
another fixable gap), KSW's "Equaliser App" (XML has `EQ_app`), KSW's "CAN Bus
Data Acquisition" (nothing in XML), KSW's "Driver's seat" (nothing; ZXW has
`driverSeat`), KSW's "Gear Selection" (nothing; ZXW has `gearType`), KSW's
"Turn signal control" (nothing; ZXW has `corneringLampControl`), KSW's
"Original radar display reverse" (nothing), KSW's "Automatic Backlight Control"
(XML has `Backlight_auto_set`), KSW's "360 Camera Type" (nothing; ZXW has
`cameraType`).

**(h) Inverted booleans exist and the schema cannot express them.** At least
three:

```xml
<!-- Installation of third-party apps 0:allow  1:Prohibited  -->
<APK_Install>0</APK_Install>
<!-- Whether to use the left front speaker: 0: Use 1: Not use -->
<Front_left>1</Front_left>
```
plus ZXW `useHorn` (0 = Enable, 1 = Disable). A naive "checked means 1" would
silently invert the user's intent. `Front_left` and `useHorn` are already
modelled as radio groups with explicit `configValue`, which is safe;
`APK_Install` is not modelled at all. Rule: **never infer 0/1 semantics.** A
checkbox must carry explicit on/off values (section 3).

**(i) KSW `<factory>` has 62 scalar elements; markdown documents 28 of them.**
ZXW `<factory>` has 63 and `<setings>` 39; markdown documents 33 total. Roughly
half of each file is undocumented. Undocumented elements are still parsed and
still round-tripped untouched — they just get no control. Phase 4 can offer an
opt-in "advanced / undocumented keys" table so power users are not forced back
into a text editor.

---

## 3. Schema changes in `src/data/factory-settings/index.ts`

Current:

```ts
const BaseSettingItemSchema = z.object({
  name: z.string(),
  nameOld: z.string().optional(),
  description: z.string().optional(),
  configKey: z.string().optional(),
  configValue: z.union([z.string(), z.number()]).optional(),
  control: z.string().optional(),
  min: z.number().optional(),
  max: z.number().optional()
});
```

Proposed. Keep the recursive-type pattern exactly as-is (the
`BaseSettingItemSchema` + `z.lazy` split is required and is already commented
with the upstream zod issue link).

```ts
const ControlSchema = z.enum(['checkbox', 'radio', 'range', 'select', 'text']);

const ValueTypeSchema = z.enum(['int', 'string', 'compound']);

const OptionSchema = z.object({
  label: z.string(),
  value: z.union([z.string(), z.number()]),
  note: z.string().optional()
});

// Build select options from a list section of the user's own file rather
// than from anything we ship. `attribute` supplies the value, `labelAttribute`
// the visible text; `text` means use the element's text content.
const OptionsFromSchema = z.object({
  path: z.string(),            // e.g. 'SupportUIList/Item' or 'CarDisplayParam/model'
  attribute: z.string(),       // e.g. 'name' (KSW) | 'id' (ZXW)
  labelAttribute: z.string().optional()  // 'display' (KSW) | 'ui' (ZXW) | omit for text
});

const BaseSettingItemSchema = z.object({
  name: z.string(),
  nameOld: z.string().optional(),
  description: z.string().optional(),

  configKey: z.string().optional(),
  // Full path from the document root when the bare key is ambiguous, e.g.
  // 'ConfigInfo/setings/Front_view_camera'. Optional; resolution falls back
  // to a unique tag-name match.
  configPath: z.string().optional(),
  configValue: z.union([z.string(), z.number()]).optional(),

  control: ControlSchema.optional(),
  valueType: ValueTypeSchema.optional(),   // default 'int'
  min: z.number().optional(),
  max: z.number().optional(),
  step: z.number().optional(),

  // checkbox only — never inferred. See section 2.3(h).
  onValue: z.union([z.string(), z.number()]).optional(),
  offValue: z.union([z.string(), z.number()]).optional(),

  options: OptionSchema.array().optional(),
  optionsFrom: OptionsFromSchema.optional(),

  // Documented but deliberately not wired: the key is unverified, the
  // setting lives outside the XML, or it is a UI action (Restart, Import).
  editable: z.boolean().optional(),        // default true when a key resolves
  // Shown as a red callout next to the control. Use for the vendor's own
  // bricking warnings, e.g. Reverse_time.
  warning: z.string().optional()
});
```

Notes on each change:

- **`control` becomes an enum.** Today it is `z.string()` and the three values
  actually in use are `checkbox` (33), `radio` (117), `range` (1). Typos
  currently pass validation and silently render nothing.
  `_setting.component.astro` compares against string literals, so a typo is
  invisible. Adding `select` and `text` covers `UI_type`, `carTypeSelection`,
  `canProtocolSelection`, `client`, `TXZ_Wakeup`.
- **`valueType`** distinguishes KSW `UI_type` (string) from ZXW `uiSelection`
  (int) and flags `Reverse_time` as `compound`. The XML is untyped, so without
  this the builder cannot know whether to write `2` or `"2"` — it matters
  because the value is spliced as literal text.
- **`onValue` / `offValue`** make checkbox semantics explicit. Migration: add
  `onValue: 1, offValue: 0` to every existing checkbox row. For `APK_Install`,
  if it ever gets documented, `onValue: 0, offValue: 1`.
- **`options` / `optionsFrom`** replace the "look at the example file yourself"
  prose in `ksw/07-ui-configuration.md` and `zxw/06-ui-configuration.md`.
  `optionsFrom` is the important one — it reads the user's *own* list section,
  so a firmware with themes we have never seen still gets a correct dropdown.
- **`editable: false`** is how sections 2.3(a), 2.3(b) and 2.3(g) ship without
  lying to the user. Those rows keep today's look: a label, a description, and
  the `(</> key)` badge, but no interactive control.
- **`configPath`** is belt-and-braces for the `<ver>`/`<client>`/`<password>`
  collision risk. Not needed today by any row.

### Build-time validation

Add a small script run from CI (`npm run validate:config-keys`) that, for each
vendor, loads the collection and the matching fixture from `public/`, then
fails on:

1. `configKey` that resolves to zero elements in the fixture (would catch all
   six from 2.3(a) today).
2. `configKey` that resolves to more than one element and has no `configPath`.
3. The same `configKey` claimed by two different settings with different
   `control` values (would catch `BT_Type` today).
4. A setting with `configKey` whose `radio` children lack `configValue`.
5. `control: checkbox` with a `configKey` and no `onValue`/`offValue`.
6. `min`/`max` on a setting whose `control` is not `range`.

This is the cheapest possible guard and it is the reason the markdown gaps stop
regressing. It runs in Node against the built collection, so it slots into the
existing CI job between `astro check` and `build`.

Because the fixtures in `public/` are examples, a resolve failure is a
*warning* for keys explicitly marked `editable: false` and an *error*
otherwise.

---

## 4. Architecture

### What stays static Astro

Everything that exists today. `getStaticPaths` still emits
`/factory-settings/ksw` and `/factory-settings/zxw` at build time.
`_section.component.astro` still renders `<h3>` + `<Content />`.
`_setting.component.astro` still renders the row, the label, the description,
the `(</> key)` badge, and the nested children. The example-XML `<Code>` block
at the bottom of `[slug].astro` stays.

The only change to server-rendered markup: controls gain `id`/`name`/`value`/
`data-*` attributes and a `disabled` attribute that the client removes, and the
whole settings area is wrapped in a `<form>` that the client takes over.

### What becomes client-side

A single module graph, loaded via one `<script>` in a new
`_builder.component.astro`. Astro bundles and hashes it; no `is:inline`, so it
gets type-checked by `astro check` and linted.

```
src/shared/factory-config/
  types.ts             shared types (BuilderModel, FieldSpec, Edit, DiffRow)
  model.ts             build-time: settings tree -> flat BuilderModel
  xml-index.ts         raw-text scanner -> ElementIndex (offsets, paths)
  xml-read.ts          read a value / list options from raw + index
  xml-edit.ts          apply sorted splices to raw text
  entities.ts          decode/encode the 5 predefined + numeric refs
  diff.ts              BuilderModel + original + current -> DiffRow[]
  store.ts             client state + subscribe/notify
  builder.client.ts    entry point: DOM wiring, drop zone, download, reset
```

`model.ts` and `types.ts` are imported by both the `.astro` frontmatter and the
client bundle. `xml-*.ts`, `diff.ts`, `store.ts`, `builder.client.ts` are
client-only and also the unit-test surface (section 10) — they are pure
functions over strings, no DOM except in `builder.client.ts`.

Path aliases already exist in `tsconfig.json` (`@shared/*`), so imports read
`import { indexElements } from '@shared/factory-config/xml-index';`.

### State

One module-level object in `store.ts`, no framework:

```ts
type BuilderState = {
  fileName: string | null;
  raw: string | null;          // the uploaded text, never mutated
  index: ElementIndex | null;  // offsets into raw
  original: Map<string, string>;  // fieldId -> value as read from raw
  current: Map<string, string>;   // fieldId -> value after user edits
};
```

`raw` is the single source of truth and is **never** mutated. Every download is
`applyEdits(raw, editsFor(current))` computed fresh. Reset is
`current = new Map(original)`. That makes the round-trip guarantee a property of
one pure function instead of an invariant scattered across event handlers.

No `localStorage`, no `sessionStorage`, no IndexedDB. A user's factory config
can contain their factory password (`<password>0000</password>`); persisting it
would be a privacy regression and would survive the tab. If Phase 5 wants
"remember my file", it is an explicit opt-in with a clear warning — see open
question Q6.

### Serialising the settings tree into the page

In `[slug].astro` frontmatter, build the model and emit it as JSON in a
non-executable script tag:

```astro
---
const model = buildBuilderModel(vendor.id, entries);
---
<script
  type="application/json"
  id="factory-config-model"
  set:html={JSON.stringify(model).replaceAll('<', '\\u003c')}
></script>
```

Why this and not `define:vars`:

- `define:vars` forces the script to be inline, which means no bundling, no
  tree-shaking, and it is excluded from `astro check`.
- `type="application/json"` is inert, so the `<` escaping is belt-and-braces
  against a `</script>` in a setting description.
- It keeps the client bundle identical across both vendor pages — the only
  difference is the JSON payload — so the browser caches one hashed file.

Watch the Astro 7 `compressHTML: 'jsx'` trap documented in `AGENTS.md`:
whitespace containing a newline between adjacent markup is *stripped*, not
collapsed. Anything added to `_setting.component.astro` that puts an element on
the line after text (a changed-badge `<span>` after the label, say) needs an
explicit `{' '}`. Nothing in CI catches it — diff `dist/factory-settings/ksw/index.html`
when touching that file.

`BuilderModel` is flat, one entry per addressable field:

```ts
type FieldSpec = {
  id: string;              // github-slugger id, same as today's `uniqueId`
  label: string;
  section: string;
  key: string;             // configKey
  path?: string;           // configPath when present
  control: 'checkbox' | 'radio' | 'range' | 'select' | 'text';
  valueType: 'int' | 'string' | 'compound';
  onValue?: string; offValue?: string;
  options?: { label: string; value: string }[];
  optionsFrom?: { path: string; attribute: string; labelAttribute?: string };
  min?: number; max?: number; step?: number;
  warning?: string;
};
```

Radio groups collapse to one `FieldSpec` with `control: 'radio'` and an
`options` array built from the children's `configValue`/`name`. That is exactly
the implicit convention from section 2.2, made explicit at build time so the
client never has to walk a tree.

---

## 5. XML parse and serialise in the browser

This is the part that decides whether the feature is trustworthy. A user who
round-trips their file and gets back something structurally different will —
correctly — never use the tool again.

### 5.1 Why `DOMParser` + `XMLSerializer` is not enough

`DOMParser` is fine for *reading*. `XMLSerializer` is disqualified for
*writing*, because it re-serialises from the DOM and the DOM does not retain:

| Source | `XMLSerializer` output |
| --- | --- |
| `<?xml version="1.0" encoding="utf-8"?>` | dropped (not a DOM node) |
| `<Item name = "com.waze" />` | `<Item name="com.waze"/>` |
| `<model id = "1"  >[01]NBT…</model>` | `<model id="1">[01]NBT…</model>` |
| original indentation / blank-line grouping | preserved only as text nodes, but any normalization elsewhere shifts it |
| `″` (U+2033) vs a numeric entity | normalized to one form |
| CRLF line endings | normalized |
| trailing newline at EOF | may be dropped |

Comments and attribute order *are* preserved by `XMLSerializer`, so the naive
approach half-works — which is worse than failing, because the damage is subtle.
The KSW file alone has ~90 `name = "…"` attributes that would all silently
change.

### 5.2 The approach: read with a parser, write by splicing the original text

Never serialise. Edit the original string in place.

**Step 1 — read the text.** `await file.text()` for uploads (UTF-8, no line
ending normalization). Detect and preserve a UTF-8 BOM if present: strip it for
parsing, re-prepend it on download.

**Step 2 — validate.** Run `new DOMParser().parseFromString(text, 'application/xml')`
and check `doc.querySelector('parsererror')`. This costs nothing and gives a
real error message for a truncated or corrupted file, which is exactly the
failure mode of `adb pull` gone wrong. The resulting `Document` is used for
nothing else.

**Step 3 — index.** A purpose-written scanner in `xml-index.ts` (~200 lines,
no dependency) walks the raw string once and produces:

```ts
type IndexedElement = {
  name: string;              // 'GoogleAPP'
  path: string;              // 'ConfigInfo/factory/GoogleAPP'
  occurrence: number;        // nth sibling with this name under this parent
  attributes: Record<string, string>;
  tagStart: number;          // offset of '<'
  valueStart: number;        // offset just after the opening tag's '>'
  valueEnd: number;          // offset of '<' of the closing tag
  selfClosing: boolean;
  hasElementChildren: boolean;
};
type ElementIndex = { elements: IndexedElement[]; byPath: Map<string, IndexedElement[]> };
```

The scanner must correctly skip, and not index:

- `<?xml … ?>` and any other processing instruction.
- `<!-- … -->` **including comments that contain markup.** This is not
  hypothetical: `zxw_factory_config.xml` lines 181-230 and 232-269 each contain
  a complete commented-out `<CarDisplayParam>` block, and lines 301-312 and
  314-333 contain commented-out `<CANBusProtocol>` blocks. A scanner that does
  not handle comments would index three `CarDisplayParam` where the document
  has one, and would produce corrupt offsets.
- `<![CDATA[ … ]]>` (not present in either fixture, but cheap to handle and it
  is the classic way this kind of scanner breaks).
- `<!DOCTYPE …>` (not present; handle by skipping to the matching `>` outside
  quotes).
- `>` inside an attribute value — attribute parsing must be quote-aware.

Self-closing detection must not be fooled by `/` inside an attribute value
(`<model id="1">[03]NBT_F30/F20…` has slashes in *text*, and
`SupportNaviAppList` has none in attributes, but `AppsWhiteList` package names
and `CarDisplayParam` text are full of them — the check is "the character
immediately before the closing `>`, outside quotes, is `/`").

**Step 4 — read values.** `decodeEntities(raw.slice(valueStart, valueEnd))`.
Only for elements with `hasElementChildren === false`.

**Step 5 — read option lists.** For `optionsFrom: { path: 'SupportUIList/Item',
attribute: 'name', labelAttribute: 'display' }`, filter the index by path and
pull attributes. Because the index skipped comments, the commented-out ZXW
blocks are correctly invisible.

**Step 6 — write.** Collect one splice per changed field:

```ts
type Edit = { start: number; end: number; text: string };

export function applyEdits(raw: string, edits: Edit[]): string {
  const sorted = [...edits].sort((a, b) => b.start - a.start); // descending
  let out = raw;
  for (const e of sorted) out = out.slice(0, e.start) + e.text + out.slice(e.end);
  return out;
}
```

Descending order so earlier splices do not invalidate later offsets. `start`/
`end` are always `valueStart`/`valueEnd` of a leaf element, so the opening tag,
its attributes, the closing tag, all comments, all whitespace and every byte of
every element we do not understand are untouched by construction.

**Step 7 — encode.** On write, escape only what XML requires inside character
data: `&` → `&amp;`, `<` → `&lt;`, and `]]>` → `]]&gt;`. Do **not** escape `>`
generally, do not escape non-ASCII, do not re-encode `″`. Values written by the
builder are numbers or values drawn from the user's own file, so in practice
escaping is a no-op — but the function exists so a future free-text field
(`TXZ_Wakeup`, `client`) cannot inject markup.

**Step 8 — download.**

```ts
const blob = new Blob([bom + text], { type: 'application/xml' });
const url = URL.createObjectURL(blob);
// <a download={fileName}> click, then URL.revokeObjectURL(url)
```

Filename: the uploaded name, unchanged. The head unit looks for exactly
`/OEM/factory_config.xml`, so renaming to `factory_config-modified.xml` would
be actively harmful. Instead, warn in the UI that the download will land in the
Downloads folder next to any earlier copy and the user must keep their backup
separate.

### 5.3 The round-trip guarantee, stated as a test

The contract is one line and it is the first test written:

```
applyEdits(raw, []) === raw            // for every fixture
applyEdits(raw, editsFor(original)) === raw   // re-writing unchanged values is a no-op
```

The second is the stronger one: it proves read → write of *every* mapped field
produces a byte-identical file. Run it over both `public/*.xml` and over a
corpus of real user-supplied files (open question Q5).

### 5.4 The paste path caveat

A `<textarea>` normalizes line endings: per the HTML spec the element's API
value has CRLF converted to LF. So a user who pastes a CRLF file gets an LF
file back. Both fixtures are LF and `.editorconfig` enforces LF in this repo,
but a file pulled onto a Windows machine could be CRLF.

Handling: the drop zone / file picker is the primary path and is CRLF-safe.
The paste box is secondary, and when pasted text contains no `\r` but the user
is on Windows we cannot tell. Simplest honest fix: after parsing pasted text,
show a one-line note — "pasted text is normalized to Unix line endings; upload
the file instead to preserve the original exactly". Do not silently guess.

### 5.5 Dependencies

None. `DOMParser` and `Blob` are platform. `xml-index.ts` is hand-written.
`fast-xml-parser`, `xmldom`, `sax` are all rejected: they either normalize on
write (defeating the entire point) or add a dependency to a repo whose
`package.json` has exactly nine runtime deps and pins every one exactly.

---

## 6. UX flow

### Layout on `/factory-settings/{vendor}`

```
[ Safety callout — red, always visible, above everything ]

[ Builder panel ]
   ( no file yet )  Drop your factory_config.xml here, or Choose file…
                    Or paste the file contents  [ textarea, collapsed ]
                    [ Try it with the example file ]   <- loads public/*.xml
   ( file loaded )  factory_config.xml · 686 lines · 28 of 34 settings matched
                    [ Download modified file ]  [ Reset ]  [ Remove file ]
                    3 changes  [ Show changes ]

[ Section: Function ]     <- existing <h3>, existing <Content />
   [x] USB HOST                         (</> USB_HOST)
       Allow USB devices to be…
   [ ] Zlink                            (</> zlink_auto_start)   • changed
   …
[ Section: Vehicle ]
…

[ An example factory_config.xml file ]   <- unchanged, existing <Code> block
```

### States

1. **No file (default, and the JS-off state).** Every control renders exactly
   as today: present, `disabled`, decorative. The drop zone is visible. Nothing
   claims to be interactive.
2. **File loaded.** The client removes `disabled`, `tabindex="-1"` and
   `aria-hidden="true"` from every control whose field resolved in the index.
   Controls that did *not* resolve (the six KSW phantom keys, everything with
   `editable: false`) keep all three and get a small "not found in your file"
   note. This is honest, it is how the feature degrades across firmware
   versions we have never seen, and it keeps unusable controls out of the
   accessibility tree rather than exposing them as unlabelled inputs.
3. **Changed.** A row whose current value differs from the value read from the
   file gets a left border accent and a "changed" badge. Use a border + text
   badge, not colour alone (section 8).
4. **Diff.** "Show changes" toggles a `<details>`/`<dialog>` listing
   `section · label · key · from → to`, e.g.
   `Function · USB HOST · USB_HOST · 0 → 1`. Plain table, copyable. This is
   what a user pastes into Discord when asking whether a change is sane.
5. **Download.** Enabled only when there is at least one change. Produces the
   spliced file.
6. **Reset.** Restores every control to the value read from the file. Does not
   drop the file.
7. **Remove file.** Clears state entirely, returns to state 1. Worth having
   explicitly so a user on a shared machine can clear the page without a reload.

### Degradation with JS disabled

The page is server-rendered and complete without the builder. Concretely:

- The `<script>` in `_builder.component.astro` is the only new client code, and
  everything it touches is additive.
- The drop zone is inside `<noscript>`-aware markup: render it with a
  `data-builder-root` attribute and `hidden`, and have the script unhide it.
  With JS off it never appears, so there is no dead upload UI.
- Controls stay `disabled` + `aria-hidden` because only the script removes
  those attributes — i.e. exactly today's decorative behaviour.
- The example XML listing and every description remain.

Net: JS-off is today's page, unchanged. That is the right floor for a
documentation site.

### View transitions

`base-layout.astro` renders `<ClientRouter />`, so navigating between
`/factory-settings/ksw` and `/factory-settings/zxw` is a client-side swap. Two
consequences:

- The builder script must initialise on `astro:page-load`, not only on
  `DOMContentLoaded` — the same pattern `src/pages/search.astro` and
  `color-scheme.component.astro` already use.
- State must be **discarded** on navigation between vendors. A KSW file loaded
  against the ZXW page would match almost nothing and mislead. Key the store by
  vendor id and clear on mismatch.

---

## 7. Safety and privacy

Three messages, and they are not optional garnish — a wrong `Reverse_time` is
documented in the file itself as something that "will block Factory settings".

**(a) Bricking warning.** A persistent callout at the top of the builder,
rendered server-side so it is present with JS off:

> Changing factory settings can leave your head unit unusable or stuck out of
> the factory menu. Back up your original file before you change anything, and
> only change settings you understand. This site cannot verify that a value is
> correct for your car.

with links to `${URL_PREFIX}faq/{vendor}/pull-factory-config` and
`${URL_PREFIX}faq/{vendor}/apply-factory-config` — the FAQ entries already
exist and `pull-factory-config.md` already opens with "please make a backup of
the original file".

Per-setting warnings come from the new `warning` field. `Reverse_time` gets the
XML's own comment verbatim: *do NOT change to "0", it will block Factory
settings*. Render it as a red inline note, not a tooltip — the current
`configXmlRef` tooltip in `_setting.component.astro` is `title=`-only and is
invisible on touch and to most screen readers.

**(b) Backup-first gating.** Before the first download, require an explicit
acknowledgement: a checkbox reading "I have a backup of my original file"
that enables the Download button. One checkbox, session-only, not persisted.
This is friction on purpose and it is proportionate to "factory reset will not
undo this" (from `apply-factory-config.md`: *Once you apply a new file, it will
persist even through a factory reset*).

**(c) Privacy.** State it on the page, not just in a plan:

> Your file is read in your browser. It is never uploaded, and this site has no
> server that could receive it.

Make it true and keep it true:

- No `fetch`/`XMLHttpRequest`/`sendBeacon` anywhere in
  `src/shared/factory-config/**`. Add an ESLint `no-restricted-globals` /
  `no-restricted-properties` rule scoped to that directory so a future change
  cannot quietly add one.
- No `localStorage`/`sessionStorage`/IndexedDB. Config files contain
  `<password>` and `<client>`.
- Note the existing third-party script: `base-layout.astro` loads Umami
  analytics from `cloud.umami.is`. It does not and must not see file contents.
  If Phase 3 adds any event tracking for the builder, track **counts only**
  (e.g. "builder_file_loaded"), never a key name, never a value, never a
  filename. Prefer tracking nothing.
- Because the site is on GitHub Pages we cannot set response headers, so a CSP
  would have to be a `<meta http-equiv>` tag. Worth considering as a separate
  change, but note it would need to allow `cloud.umami.is` and would not
  retroactively constrain anything. Out of scope here.

---

## 8. Accessibility

The current `_setting.component.astro` handles "decorative" the correct way for
what it is: every `<input>` carries `disabled`, `tabindex="-1"` and
`aria-hidden="true"`, so the controls are removed from the tab order and from
the accessibility tree entirely. A screen reader hears the setting name and
description as prose and never encounters a phantom checkbox. Nothing is
mislabelled because nothing is exposed.

That approach stops working the moment the controls become real, and the parts
it was papering over come due:

- **The inputs have no `id` and no `name`.** They are unreachable from a
  `<label for>` and, for radios, ungrouped — the component no longer computes a
  shared `name`, so two radio members are not even mutually exclusive. Fine
  while `aria-hidden`; broken the instant it is removed.
- **`uniqueId` is on the name `<span>`, not on a control.** The builder needs it
  on the control (and derived ids for radio members), with the span becoming a
  `<label for>`.
- **There is no `<fieldset>`/`<legend>`.** Once radio members are focusable, the
  group's purpose ("Boot Mode Memory") has to be announced when focus lands on
  a member; nothing currently carries it.
- **The `(</> key)` badge is `title`-only.** `title` is not reliably exposed on
  touch and is inconsistently announced. The information — which XML key this
  is, and what value to write — is genuinely useful and should be real text
  wired through `aria-describedby`.
- **Range inputs have no accessible name and no visible current value.**
- **`aria-hidden`/`tabindex="-1"` must be removed per control, not globally**,
  and only for controls whose key resolved in the user's file. A control that
  stays decorative (the six phantom KSW keys, `editable: false` rows) must keep
  all three attributes — otherwise the builder re-introduces exactly the
  unlabelled-phantom-checkbox problem the current code avoids.

The builder version:

```astro
<fieldset>
  <legend>Boot Mode Memory</legend>
  <p id={`${uniqueId}-desc`}>You can choose what system is automatically launched…</p>
  <div>
    <input type="radio" id={`${uniqueId}-0`} name={uniqueId} value="0"
           aria-describedby={`${uniqueId}-desc`} disabled />
    <label for={`${uniqueId}-0`}>Enable</label>
  </div>
  …
</fieldset>
```

Rules for the reworked `_setting.component.astro`:

1. One id per element, and ids move onto the controls. Inputs get `{uniqueId}`
   (single control) or `{uniqueId}-{index}` (radio members, sharing
   `name={uniqueId}`). The description gets `{uniqueId}-desc`. The key badge
   gets `{uniqueId}-key`. The name `<span>` becomes a `<label for>` and carries
   no id.
2. `<fieldset>` + `<legend>` for every radio group; `<legend>` is the parent
   setting's `name`. Tailwind resets `fieldset`, so add explicit spacing.
3. `aria-describedby` chains description and key badge onto the control, so the
   XML key and the "value should be N" text are announced, replacing `title`.
   Keep a visible `<code>` badge too — it is one of the more useful things on
   the page.
4. `control: range` gets `<label for>`, `aria-valuetext` where the raw number
   is not the meaningful unit (Bass `0~24` maps to `-12…+12`), and a live
   `<output for={id}>` showing the current number. `aria-live="polite"` on the
   output.
5. `control: select` uses a native `<select>`. The ZXW theme list is ~50
   options and the KSW one ~60; a native select handles that with type-ahead
   for free. No custom combobox.
6. **Changed state is not colour-only.** A "changed" text badge plus a left
   border, and `aria-describedby` pointing at a visually-hidden
   "changed from 0 to 1" span. Contrast must hold in both themes — the theme
   class is applied to `<html>` before first paint by the inline script in
   `base-layout.astro`, so a changed row must be legible under both.
7. Keyboard: everything is native, so tab/space/arrow behaviour is free. The
   drop zone must also be a real `<button>` wrapping a visually-hidden
   `<input type="file">` so it is reachable and activatable by keyboard — a
   `div` with a `drop` handler alone is not.
8. Status changes (file loaded, N changes, parse error) go in one
   `role="status"` `aria-live="polite"` region near the builder panel, so a
   screen reader user learns the file was accepted.
9. Errors (unparseable XML, wrong vendor's file) go in `role="alert"`.

None of this needs a library. It does need `_setting.component.astro` rewritten
rather than patched — it currently emits a different shape per control type
inside one flex row, and fieldsets do not fit that.

---

## 9. Incremental delivery

Five phases. Each is independently shippable and independently reviewable.

### Phase 1 — Schema, mapping audit, and the key-validation gate

No UI change. Pure groundwork, and it is the phase that makes the rest safe.

- Apply the schema from section 3 (`control` enum, `valueType`, `onValue`/
  `offValue`, `options`, `optionsFrom`, `editable`, `warning`, `configPath`).
- Migrate all 18 markdown files to the new fields: add `onValue: 1 / offValue: 0`
  to the 33 checkboxes, mark the six phantom KSW keys `editable: false`, resolve
  the `BT_Type` duplicate, add `configKey` to the rows that have an obvious XML
  match (`lvdsMode`, `Support_TXZ`, `EQ_app`, `Backlight_auto_set`,
  `carTypeSelection`, `canProtocolSelection`).
- Add `npm run validate:config-keys` and wire it into `.github/workflows/ci.yml`
  between `astro check` and `build`.
- Value: the documentation gets measurably more correct today, and the gaps in
  section 2.3 stop being invisible. Also the only phase that touches content, so
  it reviews cleanly on its own.

### Phase 2 — Read-only inspector

Upload or paste a file; see your real values in the existing (still disabled)
controls. No editing, no download.

- `xml-index.ts`, `xml-read.ts`, `entities.ts`, `types.ts`, `model.ts`.
- `_builder.component.astro` with drop zone, file picker, paste box, status
  region, and the safety callout.
- Client populates `checked`/`value` from the parsed file; controls stay
  disabled; rows that did not resolve get "not found in your file".
- Value on its own: this already answers the most common Discord question,
  "what is my unit set to?", without the user reading 686 lines of XML. It also
  proves the parser against real files before anything can write.

### Phase 3 — Editing, diff and download

The core feature.

- `xml-edit.ts`, `diff.ts`, `store.ts`.
- Enable resolved controls, track changes, changed-row styling, diff panel,
  backup-acknowledgement checkbox, download, reset, remove.
- The accessibility rewrite of `_setting.component.astro` (section 8) lands
  here, because this is where the controls become real.
- Value: the feature as pitched.

### Phase 4 — Option lists from the user's own file

- Implement `optionsFrom`; wire `UI_type` / `uiSelection` (themes),
  `carTypeSelection` (`CarDisplayParam/model`), `canProtocolSelection`
  (`CANBusProtocol/Protocol`), `Language` (`SupportLanguageList/Item`).
- Replaces "look at `<SupportUIList>` yourself" with a real dropdown built from
  what the user actually has.
- Value: the four settings people most want to change, and the ones where a
  hand-typed value is most likely to be wrong.

### Phase 5 — Advanced / undocumented keys (optional)

- A collapsed table of every scalar element in the user's file that no markdown
  setting claims — roughly half of each file (section 2.3(i)) — rendered as
  editable text inputs with the element's preceding XML comment as the
  description.
- Value: power users stop needing a text editor; and in practice it becomes the
  pipeline for documenting new keys, since a user can point at one and ask.
- Ship only if Phases 2-4 hold up. It is the phase most likely to let someone
  break their unit, so it needs its own warning and probably its own toggle.

---

## 10. Testing

The repo has no tests and `AGENTS.md` says so explicitly: *"No tests.
Verification is `npm run lint` + `npx astro check` + `npm run build`."* The
answer is not "add a test pyramid to a static documentation site". It is: the
XML round-trip is the one thing here that can silently corrupt a user's file,
so test that properly, smoke-test the flow, and stop.

### Unit tests — `node:test`, no new dependency

Node 24 is the floor (`.nvmrc` pins 24.21.0), so `node:test` + `node:assert`
are built in. TypeScript sources run directly under Node 24's type-stripping,
so the runner is:

```json
"test": "node --test 'src/shared/factory-config/*.test.ts'"
```

Zero new dependencies, which matters in a repo that pins nine runtime deps
exactly and has a `vite: ^8` override to stop drift. If type-stripping proves
awkward with the `@shared/*` path alias, the fallback is `tsx` as a single
devDependency — still far lighter than vitest + its Vite peer, which would
collide with the existing override.

What to test, in priority order:

1. **`applyEdits(raw, []) === raw`** for both `public/*.xml`. The null
   round-trip.
2. **Re-writing every mapped field with its own current value is a no-op.**
   The real guarantee.
3. **`indexElements` against the ZXW file finds exactly one `CarDisplayParam`
   and one `CANBusProtocol`**, not three of each. This is the comment-handling
   regression test and it has a real bug behind it.
4. Scanner edge cases as string fixtures: comment containing `<tag>`, comment
   containing `-->`-adjacent text, CDATA, attribute value containing `>`,
   self-closing with a `/` in an attribute value, `<?xml?>` declaration,
   BOM, CRLF.
5. **Single-field edits produce exactly the expected diff** — assert on
   `applyEdits` output being the original with one substring replaced, computed
   independently.
6. `decodeEntities` / `encodeText` symmetry, including `″`, `：` (the full-width
   colon used throughout the vendor comments) and `&amp;`.
7. `buildBuilderModel` flattens a radio group with `configValue` children into
   one `FieldSpec` with the right options, and rejects a group whose children
   lack `configValue`.
8. `diff.ts` produces one row per changed field, none for unchanged.

Fixtures: read `public/factory_config.xml` and `public/zxw_factory_config.xml`
directly rather than copying them, so the tests track the shipped examples.

### Key-mapping validation — `validate:config-keys`

Described in section 3. Not a unit test but a CI gate; it is the thing that
catches a markdown typo, which is the most likely future defect.

### End-to-end — Playwright, one spec

The Playwright MCP server is already available in this environment, and
`eslint.config.mjs` already ignores `test-results/`, which suggests someone
intended this. Add `@playwright/test` as a devDependency and one spec:

- Navigate to `/factory-settings/ksw` on the preview server.
- Upload `public/factory_config.xml` via `setInputFiles`.
- Assert the USB HOST checkbox reflects `<USB_HOST>` from the file.
- Toggle it; assert the row is marked changed and the diff shows `0 → 1`.
- Tick the backup acknowledgement, download, and assert the downloaded bytes
  equal the fixture with exactly that one substring changed.
- Assert no network request leaves the page during the flow (route
  interception, allowing the Umami script) — this is the privacy guarantee as
  an executable assertion, and it is worth more than any paragraph in the docs.
- One a11y pass: `@axe-core/playwright` on the loaded state.

Run it in CI as a separate job so it cannot block the deploy job on flake;
gate the deploy on `verify` only, as today.

### What not to add

No component snapshot tests for `.astro` files. No coverage thresholds. No
testing that Astro renders markdown. The existing CI smoke test (`test -s` over
`dist/**`) already covers "the page built".

---

## 11. Open questions

1. **KSW car display and CAN protocol selection: which element holds the
   choice?** `<CarDisplayParam>` and `<CANBusProtocol>` list the options, and
   `ksw/03-car-display.md` / `ksw/04-can-protocol.md` have no `settings:` at
   all. ZXW uses `carTypeSelection` and `canProtocolSelection`. Nothing in
   `public/factory_config.xml` looks equivalent. Does KSW store these outside
   the XML (Android settings provider?), or is the key just missing from our
   example file? Needs someone with a device. Blocks Phase 4 for KSW.

2. **`BT_Type` claimed twice in `ksw/01-function.md`** — checkbox "BT" and
   radio group "Bluetooth Selection". Which one is real? The XML comment near
   `<BT_Type>0</BT_Type>` would settle it; I did not find one stating the
   semantics. Blocks Phase 2/3 for KSW's Function section.

3. **MIC gain: one control or three?** Three keys (`mic_gain_m501` 0-8,
   `mic_gain_m506` 0-8, `mic_gain_m600` 0-20), no M700 key, and the markdown
   models one slider 0-20. Proposal: render one slider per `mic_gain_*` element
   present in the user's file, each with its own range read from... nowhere, so
   the ranges have to be hardcoded per key in markdown. Confirm? And does M700
   use `mic_gain_m600` or an undocumented key?

4. **The six phantom KSW keys** (`APK360`, `forwardCamMirror`, `Speed_type`,
   `DirtTravelSelection`, `BootUpCamera`, `MicControl`). Were these observed on
   a real device and simply absent from our example file, or were they inferred
   from ZXW / decompiled sources? If observed, Phase 1 should add them to
   `public/factory_config.xml` rather than mark them `editable: false`.

5. **Is there a corpus of real user-supplied config files to test against?**
   The two files in `public/` are curated examples with our own comments in
   them. The round-trip guarantee is only as good as the variety it is tested
   on — different firmware versions, possibly CRLF, possibly BOM, possibly
   Chinese-language comments we have stripped from ours. Even five real files
   from Discord (with `<password>` redacted) would materially raise confidence.

6. **Should the builder remember the loaded file across a reload?** My
   recommendation is no — the file contains `<password>` and `<client>`, and
   this is a public documentation site people open on shared machines. But
   losing your work on an accidental refresh is a real annoyance. If yes, it
   needs an explicit opt-in and a visible "stored in this browser" indicator.

7. **`Reverse_time` compound value.** `"0-0"` = disabled, `"1-10"` = 10 seconds.
   Is the first field strictly `0`/`1`, and is the second range strictly 1-10?
   The XML comment implies both but does not state the bounds for the disabled
   case (is `"0-5"` legal?). Getting this wrong is the documented bricking path,
   so I would rather ship it `editable: false` with the warning text than guess.

8. **Does the head unit tolerate a file whose element *order* is unchanged but
   whose values changed mid-file?** Almost certainly yes, but the splice
   approach is also what makes a "we only ever touch the bytes between `>` and
   `</key>`" claim defensible, so it is worth one confirmation on a real unit
   before Phase 3 ships.

9. **Should the example-file "Try it" button exist?** It makes the feature
   demonstrable without a device and makes testing trivial. It also risks
   someone downloading a modified *example* and flashing it, which
   `public/factory_config.xml` explicitly warns against ("Never use this entire
   file as-is"). Proposal: keep it, but disable Download entirely in demo mode
   and label the panel "Example file — download disabled".
