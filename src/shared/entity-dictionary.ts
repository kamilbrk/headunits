import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

import { slug } from 'github-slugger';

const GLOSSARY_DIRECTORY = 'src/data/glossary';

export type AutoLinkKind = 'glossary';

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
