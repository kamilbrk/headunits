import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

import { slug } from 'github-slugger';

import { DOMAIN, URL_PREFIX } from './config';

const UPDATES_DIRECTORY = 'src/data/updates';

const walk = (directory: string): string[] =>
  readdirSync(directory).flatMap((name) => {
    const entry = path.join(directory, name);
    return statSync(entry).isDirectory() ? walk(entry) : [entry];
  });

// Read line by line rather than with a frontmatter regex: the equivalent
// pattern trips `sonarjs/super-linear-regex` on backtracking.
const readDate = (source: string) => {
  const frontmatter = source.split('---', 2)[1] ?? '';
  const line = frontmatter.split('\n').find((candidate) => candidate.startsWith('date:'));

  return line
    ?.slice('date:'.length)
    .trim()
    .replaceAll(/^['"]|['"]$/g, '');
};

/**
 * Build dates for the `updates` collection, keyed by the URL the sitemap emits.
 * Read from disk rather than `getCollection`, which isn't available while the
 * Astro config is still being resolved.
 */
export function getUpdateLastmods() {
  const lastmods = new Map<string, Date>();

  for (const file of walk(UPDATES_DIRECTORY)) {
    if (!file.endsWith('.md') && !file.endsWith('.mdx')) continue;

    const date = readDate(readFileSync(file, 'utf8'));
    if (!date) continue;

    const parsed = new Date(date);
    if (Number.isNaN(parsed.getTime())) continue;

    const entryId = path
      .relative(UPDATES_DIRECTORY, file)
      .replace(/\.mdx?$/, '')
      .split(path.sep)
      .map((segment) => slug(segment))
      .join('/');

    lastmods.set(new URL(`${URL_PREFIX}updates/${entryId}/`, DOMAIN).href, parsed);
  }

  return lastmods;
}
