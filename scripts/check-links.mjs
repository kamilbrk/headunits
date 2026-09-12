// Verifies every internal link in the built site resolves to a real file, and
// that no development URLs leaked into content. Run against `dist/` after a
// build. Nothing else in the pipeline catches either problem.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, posix, relative, resolve } from 'node:path';

import { BASE } from '../src/shared/config.ts';

const DIST = 'dist';
const ATTRIBUTE = /(?:href|src)="([^"]*)"/g;
const DEV_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0'];
const IGNORED_SCHEMES = ['mailto:', 'tel:', 'data:', 'javascript:'];

const walk = (directory) =>
  readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });

const exists = (path) => {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
};

const resolvesInDist = (urlPath) => {
  const withoutBase = BASE && urlPath.startsWith(BASE) ? urlPath.slice(BASE.length) : urlPath;
  const target = join(DIST, withoutBase);
  return exists(target) || exists(join(target, 'index.html')) || exists(`${target}.html`);
};

const failures = [];
const htmlFiles = walk(DIST).filter((file) => file.endsWith('.html'));

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  const where = relative(DIST, file);

  for (const [, rawValue] of html.matchAll(ATTRIBUTE)) {
    const value = rawValue.trim();
    if (!value || value.startsWith('#')) continue;
    if (IGNORED_SCHEMES.some((scheme) => value.startsWith(scheme))) continue;

    if (DEV_HOSTS.some((host) => value.includes(`//${host}`))) {
      failures.push(`${where}: development URL "${value}"`);
      continue;
    }

    if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.startsWith('//')) continue;

    const [path] = value.split(/[?#]/);
    if (!path) continue;

    if (path.startsWith('/')) {
      if (BASE && !path.startsWith(`${BASE}/`) && path !== BASE) {
        failures.push(`${where}: root-relative link misses the base path — "${value}"`);
        continue;
      }
      if (!resolvesInDist(path)) failures.push(`${where}: dead link "${value}"`);
      continue;
    }

    const absolute = posix.normalize(posix.join('/', relative(DIST, dirname(file)), path));
    if (!exists(resolve(DIST, absolute.slice(1)))) {
      failures.push(`${where}: dead relative link "${value}"`);
    }
  }
}

console.log(`Checked ${htmlFiles.length} pages.`);

if (failures.length > 0) {
  console.error(`\n${failures.length} broken link(s):`);
  for (const failure of failures) console.error(`  ${failure}`);
  process.exit(1);
}

console.log('All internal links resolve.');
