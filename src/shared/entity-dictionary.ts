import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

import { slug } from 'github-slugger';

const DATA_DIRECTORY = 'src/data';
const GLOSSARY_DIRECTORY = path.join(DATA_DIRECTORY, 'glossary');
const UPDATES_DIRECTORY = path.join(DATA_DIRECTORY, 'updates');

// Collections whose entries are published one-per-page under a route named
// after the collection, so a file path alone gives the href.
const ROUTED_COLLECTIONS = new Set(['updates']);

export type AutoLinkKind = 'glossary' | 'entity';

export interface AutoLinkLabel {
  /**
  The text as it is written in prose.
  */
  text: string;
  /**
  Root-relative href with no base path; `base-path.plugin.ts` adds that.
  */
  href: string;
  kind: AutoLinkKind;
  /**
  Number of tokens in `text`, used to try longer labels first.
  */
  tokenCount: number;
}

/**
Labels bucketed by their first token, each bucket longest-first.
*/
export type AutoLinkDictionary = ReadonlyMap<string, readonly AutoLinkLabel[]>;

/**
A token is a run of alphanumerics in which `.`, `_` and `-` are internal only.
Matching whole tokens rather than `\b` boundaries is what keeps the term `OTA`
out of `Ksw-T-M600_OS_v1.6.1-ota` and `ID9` out of `EVOID9_ALS`.

Only ever used with `match`/`matchAll`, which leave `lastIndex` alone.
*/
export const TOKEN_PATTERN = /[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*/g;

const walk = (directory: string): string[] =>
  readdirSync(directory).flatMap((name) => {
    const entry = path.join(directory, name);
    return statSync(entry).isDirectory() ? walk(entry) : [entry];
  });

const unquote = (value: string) => value.trim().replaceAll(/^['"]|['"]$/g, '');

// Read line by line rather than with a frontmatter regex: the equivalent
// patterns trip `sonarjs/super-linear-regex` on backtracking. Covers the two
// shapes used in this repo — `key: value`, and a `key:` followed by `  - item`.
const readFrontmatter = (source: string) => {
  const block = source.split('---', 2)[1] ?? '';
  const values = new Map<string, string[]>();
  let key: string | undefined;

  for (const line of block.split('\n')) {
    const trimmed = line.trim();

    if (trimmed.startsWith('- ')) {
      if (key) values.get(key)?.push(unquote(trimmed.slice(2)));
      continue;
    }

    // Indented keys belong to a nested mapping and are not read here.
    if (trimmed === '' || line.startsWith(' ')) continue;

    const colon = line.indexOf(':');
    if (colon === -1) continue;

    key = line.slice(0, colon);
    const value = line.slice(colon + 1).trim();
    values.set(key, value === '' ? [] : [unquote(value)]);
  }

  return values;
};

const markdownFiles = (directory: string) =>
  walk(directory).filter((file) => file.endsWith('.md') || file.endsWith('.mdx'));

const countTokens = (text: string) => text.match(TOKEN_PATTERN)?.length ?? 0;

/**
Terms and aliases from the glossary collection, pointing at their anchor on
`/glossary`. Entries opting out with `autolink: false` are left out.

Read from disk rather than `getCollection`, which isn't available while the
Astro config is still being resolved.
*/
export function getGlossaryLabels(): AutoLinkLabel[] {
  const labels: AutoLinkLabel[] = [];
  const anchors = new Map<string, string>();

  for (const file of markdownFiles(GLOSSARY_DIRECTORY)) {
    const frontmatter = readFrontmatter(readFileSync(file, 'utf8'));
    const term = frontmatter.get('term')?.[0];
    if (!term) continue;

    // `glossary.astro` derives its heading ids the same way. Two terms
    // slugging alike would give both headings the same id and send every
    // generated link to whichever one the browser picked.
    const anchor = slug(term);
    const claimed = anchors.get(anchor);
    if (claimed)
      throw new Error(`Glossary terms "${claimed}" and "${term}" share anchor #${anchor}`);
    anchors.set(anchor, term);

    if (frontmatter.get('autolink')?.[0] === 'false') continue;

    for (const text of [term, ...(frontmatter.get('aliases') ?? [])]) {
      labels.push({
        text,
        href: `/glossary#${anchor}`,
        kind: 'glossary',
        tokenCount: countTokens(text)
      });
    }
  }

  return labels;
}

/**
The collection id Astro's glob loader derives from a file path, which is also
the route the entry is published at. Verified against `dist/`:
`ksw/m600/Ksw-R-M600_OS_v1.3.1-ota.md` becomes `ksw/m600/ksw-r-m600_os_v131-ota`.
*/
const entryId = (directory: string, file: string) =>
  path
    .relative(directory, file)
    .replace(/\.mdx?$/, '')
    .replace(/[/\\]index$/, '')
    .split(path.sep)
    .map((segment) => slug(segment))
    .join('/');

/**
Where a content file is published, or an empty string for a collection that
isn't published one entry per page. Takes a path relative to the repository
root or an absolute one.
*/
export function getEntryHref(file: string) {
  const relative = path.relative(path.resolve(DATA_DIRECTORY), path.resolve(file));
  const collection = relative.split(path.sep)[0];
  if (!collection || !ROUTED_COLLECTIONS.has(collection)) return '';

  return `/${collection}/${entryId(path.join(DATA_DIRECTORY, collection), file)}`;
}

/**
Firmware version ids from the `updates` collection, pointing at the page for
that build. Unlike glossary terms these are exact identifiers, so every mention
is linked, matching what the hand-written links did.
*/
export function getUpdateLabels(): AutoLinkLabel[] {
  const labels: AutoLinkLabel[] = [];

  for (const file of markdownFiles(UPDATES_DIRECTORY)) {
    const id = readFrontmatter(readFileSync(file, 'utf8')).get('id')?.[0];
    if (!id) continue;

    const href = getEntryHref(file);
    if (!href) continue;

    labels.push({ text: id, href, kind: 'entity', tokenCount: countTokens(id) });
  }

  return labels;
}

/**
Buckets labels by their first token and sorts each bucket longest-first, so
`CAN protocol` is tried before `CAN` at the same position.
*/
export function buildDictionary(labels: readonly AutoLinkLabel[]): AutoLinkDictionary {
  const dictionary = new Map<string, AutoLinkLabel[]>();

  for (const label of labels) {
    const firstToken = label.text.match(TOKEN_PATTERN)?.[0];
    if (!firstToken) continue;

    const bucket = dictionary.get(firstToken);
    if (bucket) bucket.push(label);
    else dictionary.set(firstToken, [label]);
  }

  for (const bucket of dictionary.values()) {
    bucket.sort((a, b) => b.tokenCount - a.tokenCount || b.text.length - a.text.length);
  }

  return dictionary;
}
