// Verifies every internal link in the built site resolves to a real file, and
// that no development URLs leaked into content. Run against `dist/` after a
// build. Nothing else in the pipeline catches either problem.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

import { BASE } from '../src/shared/config.ts';

const DIST = 'dist';
const ATTRIBUTE = /(?:href|src)="([^"]*)"/g;
// Breadcrumb trails carry URLs inside a <script> tag, where the attribute
// sweep below cannot see them, and a breadcrumb pointing at a 404 is worse
// than no breadcrumb.
const JSON_LD = /<script[^>]*application\/ld\+json[^>]*>([\s\S]*?)<\/script>/g;
const DEV_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0'];
const IGNORED_SCHEMES = ['mailto:', 'tel:', 'data:', 'javascript:'];

const walk = (directory) =>
  readdirSync(directory).flatMap((name) => {
    const entry = path.join(directory, name);
    return statSync(entry).isDirectory() ? walk(entry) : [entry];
  });

const exists = (target) => {
  try {
    return statSync(target).isFile();
  } catch {
    return false;
  }
};

// A link may name the file itself, a directory served by its index.html, or an
// extensionless route. All three resolve for root-relative and relative links
// alike — checking only the first reports working links as dead.
const resolvesTo = (distRelativePath) => {
  const target = path.join(DIST, distRelativePath);
  return exists(target) || exists(path.join(target, 'index.html')) || exists(`${target}.html`);
};

const resolvesInDist = (urlPath) =>
  resolvesTo(BASE && urlPath.startsWith(BASE) ? urlPath.slice(BASE.length) : urlPath);

const breadcrumbUrls = (html) => {
  const urls = [];

  for (const [, block] of html.matchAll(JSON_LD)) {
    let parsed;
    try {
      parsed = JSON.parse(block);
    } catch {
      continue;
    }

    if (parsed?.['@type'] !== 'BreadcrumbList') continue;
    for (const entry of parsed.itemListElement ?? []) {
      if (typeof entry?.item === 'string') urls.push(entry.item);
    }
  }

  return urls;
};

const failures = [];
const htmlFiles = walk(DIST).filter((file) => file.endsWith('.html'));

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  const where = path.relative(DIST, file);

  for (const url of breadcrumbUrls(html)) {
    const { pathname } = new URL(url);
    if (!resolvesInDist(pathname)) failures.push(`${where}: breadcrumb points at "${url}"`);
  }

  for (const [, rawValue] of html.matchAll(ATTRIBUTE)) {
    const value = rawValue.trim();
    if (!value || value.startsWith('#')) continue;
    if (IGNORED_SCHEMES.some((scheme) => value.startsWith(scheme))) continue;

    if (DEV_HOSTS.some((host) => value.includes(`//${host}`))) {
      failures.push(`${where}: development URL "${value}"`);
      continue;
    }

    if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.startsWith('//')) continue;

    const [linkPath] = value.split(/[?#]/);
    if (!linkPath) continue;

    if (linkPath.startsWith('/')) {
      if (BASE && !linkPath.startsWith(`${BASE}/`) && linkPath !== BASE) {
        failures.push(`${where}: root-relative link misses the base path — "${value}"`);
        continue;
      }
      if (!resolvesInDist(linkPath)) failures.push(`${where}: dead link "${value}"`);
      continue;
    }

    const fromDist = path.normalize(path.join(path.relative(DIST, path.dirname(file)), linkPath));
    if (fromDist.startsWith('..')) {
      failures.push(`${where}: relative link escapes the site — "${value}"`);
    } else if (!resolvesTo(fromDist)) {
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
