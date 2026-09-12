// Catches the `compressHTML: 'jsx'` whitespace trap documented in AGENTS.md:
// whitespace containing a newline next to an inline element is stripped, not
// collapsed, so `theme's\n<code>index.md</code>` ships as `theme'sindex.md`
// and `<span>Warning</span>\nYour file` ships as `WarningYour file`. Nothing
// else in the pipeline sees it.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

const DIST = 'dist';
const GLUED_BEFORE = /[A-Za-z0-9'’]<(?:code|a|strong|em)\b[^>]*>/g;
// The same trap the other way round: `</span>` newline `Your file` ships as
// `WarningYour file`. An empty element (`…"true"></span>Title`) is excluded,
// since nothing visible precedes the closing tag.
const GLUED_AFTER = /[^>\s]<\/(?:code|a|strong|em|span)>[A-Za-z0-9]/g;

const walk = (directory) =>
  readdirSync(directory).flatMap((name) => {
    const entry = path.join(directory, name);
    return statSync(entry).isDirectory() ? walk(entry) : [entry];
  });

const failures = [];
const htmlFiles = walk(DIST).filter((file) => file.endsWith('.html'));

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');

  for (const [pattern, what] of [
    [GLUED_BEFORE, 'before'],
    [GLUED_AFTER, 'after']
  ]) {
    for (const match of html.matchAll(pattern)) {
      const context = html
        .slice(Math.max(0, match.index - 50), match.index + match[0].length + 30)
        .replaceAll(/<[^>]+>/g, '')
        .replaceAll(/\s+/g, ' ')
        .trim();
      failures.push(
        `${path.relative(DIST, file)}: missing space ${what} inline element — "${context}"`
      );
    }
  }
}

console.log(`Checked ${htmlFiles.length} pages for glued inline elements.`);

if (failures.length > 0) {
  console.error(
    `\n${failures.length} missing space(s). Add an explicit {' '} at the end of the preceding line:`
  );
  for (const failure of failures) console.error(`  ${failure}`);
  process.exit(1);
}

console.log('No glued inline elements.');
