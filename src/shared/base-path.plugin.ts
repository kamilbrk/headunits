import type { Element } from 'hast';

import { defineHastPlugin } from 'satteri';

import { BASE } from './config';

const ATTRIBUTES_BY_TAG: Record<string, string[]> = {
  a: ['href'],
  img: ['src', 'srcset'],
  source: ['src', 'srcset'],
  video: ['src', 'poster'],
  audio: ['src']
};

const withBase = (value: string) => {
  // Protocol-relative and absolute URLs, anchors and query-only links are left alone.
  if (!value.startsWith('/') || value.startsWith('//')) return value;
  if (value === BASE || value.startsWith(`${BASE}/`)) return value;
  return `${BASE}${value}`;
};

// `srcset` is a comma-separated list of `url descriptor` pairs, so it cannot
// be rewritten as a single URL.
const withBaseSrcset = (value: string) =>
  value
    .split(',')
    .map((candidate) => {
      const [url, ...descriptors] = candidate.trim().split(/\s+/);
      return url ? [withBase(url), ...descriptors].join(' ') : candidate.trim();
    })
    .join(', ');

/**
 * Rewrites root-relative links in Markdown/MDX content so they respect the
 * deployment base path. Content authors write `/updates/ksw`, readers get
 * `/headunits/updates/ksw`. Without this the base path has to be repeated in
 * every content file, and changing it silently breaks every link.
 */
export default defineHastPlugin({
  name: 'base-path',
  element: {
    filter: Object.keys(ATTRIBUTES_BY_TAG),
    visit(node: Readonly<Element>, ctx) {
      if (!BASE) return;

      const attributes = ATTRIBUTES_BY_TAG[node.tagName] ?? [];

      for (const attribute of attributes) {
        const value = node.properties[attribute];
        if (typeof value !== 'string') continue;

        const rewritten = attribute === 'srcset' ? withBaseSrcset(value) : withBase(value);
        if (rewritten !== value) ctx.setProperty(node, attribute, rewritten);
      }
    }
  }
});
