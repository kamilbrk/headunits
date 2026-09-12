// Records every link the built site renders, page by page, in document order.
// Two snapshots taken either side of a change say exactly which links moved,
// which is how the hand-written entity links were migrated onto
// src/shared/autolink.plugin.ts without trusting that they matched.
import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const DIST = 'dist';
const ANCHOR = /<a\b([^>]*)>([\s\S]*?)<\/a>/g;
const HREF = /\bhref="([^"]*)"/;

const walk = (directory) =>
  readdirSync(directory).flatMap((name) => {
    const entry = path.join(directory, name);
    return statSync(entry).isDirectory() ? walk(entry) : [entry];
  });

// Compared on href and visible text alone. `<a><code>ID</code></a>` and
// `<a>ID</a>` read the same to a reader, and the generated links carry a
// `data-autolink` attribute the hand-written ones never had.
const visibleText = (html) =>
  html
    .replaceAll(/<[^>]+>/g, '')
    .replaceAll(/\s+/g, ' ')
    .trim();

const [output] = process.argv.slice(2);
if (!output) {
  console.error('Usage: node scripts/link-snapshot.mjs <out.json>');
  process.exit(1);
}

const snapshot = {};
const htmlFiles = walk(DIST).filter((file) => file.endsWith('.html')).sort();

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  snapshot[path.relative(DIST, file)] = html
    .matchAll(ANCHOR)
    .map(([, attributes, inner]) => [HREF.exec(attributes)?.[1] ?? '', visibleText(inner)])
    .toArray();
}

mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
writeFileSync(output, JSON.stringify(snapshot, undefined, 2));

const total = Object.values(snapshot).reduce((sum, links) => sum + links.length, 0);
console.log(`Wrote ${total} links across ${htmlFiles.length} pages to ${output}.`);
