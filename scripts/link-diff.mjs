// Compares two files written by scripts/link-snapshot.mjs. One-off migration
// tooling: it exists to prove that deleting the hand-written entity links and
// letting the plugin regenerate them changed nothing a reader can see.
import { readFileSync } from 'node:fs';

const [beforePath, afterPath] = process.argv.slice(2);
if (!beforePath || !afterPath) {
  console.error('Usage: node scripts/link-diff.mjs <before.json> <after.json>');
  process.exit(1);
}

const before = JSON.parse(readFileSync(beforePath, 'utf8'));
const after = JSON.parse(readFileSync(afterPath, 'utf8'));

const pages = [...new Set([...Object.keys(before), ...Object.keys(after)])].sort();
const differing = [];
let identical = 0;

for (const page of pages) {
  const one = JSON.stringify(before[page] ?? null);
  const other = JSON.stringify(after[page] ?? null);

  if (one === other) {
    identical += 1;
    continue;
  }

  differing.push({
    page,
    before: before[page] ?? [],
    after: after[page] ?? []
  });
}

console.log(`${identical} of ${pages.length} pages have an identical link sequence.`);

if (differing.length === 0) {
  console.log('No link changed.');
  process.exit(0);
}

console.log(`\n${differing.length} page(s) differ:`);
for (const { page, before: was, after: now } of differing) {
  console.log(`\n  ${page}`);
  const longest = Math.max(was.length, now.length);
  for (let index = 0; index < longest; index += 1) {
    const one = JSON.stringify(was[index] ?? null);
    const other = JSON.stringify(now[index] ?? null);
    if (one !== other) console.log(`    ${index}\n      before ${one}\n      after  ${other}`);
  }
}

process.exit(1);
