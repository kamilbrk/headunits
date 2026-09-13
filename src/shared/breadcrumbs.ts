import { getCollection } from 'astro:content';

import { THEME_BRANDS } from './brands';
import { DOMAIN, URL_PREFIX } from './config';

/**
Names for the top-level sections, which are routes rather than content and so
have no title to read.
*/
const SECTIONS: Record<string, string> = {
  contribute: 'Contribute',
  'factory-settings': 'Factory settings',
  faq: 'FAQ',
  glossary: 'Glossary',
  platforms: 'Platforms',
  safety: 'Safety',
  search: 'Search',
  themes: 'Themes',
  updates: 'Updates',
  'upgrade-path': 'Upgrade path'
};

const humanise = (slug: string) => {
  const spaced = slug.replaceAll('-', ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
};

const absolute = (path: string) => new URL(`${URL_PREFIX}${path}`, DOMAIN).href;

/**
The trail Google reads to show a page's place in the site rather than its bare
URL.

Only the first two segments become links. Deeper ones are not always pages:
`/updates/ksw/m600/<build>` is a route but `/updates/ksw/m600` is not, and a
breadcrumb pointing at a 404 is worse than no breadcrumb. Every one of the 249
built pages has a real page at its first and second segment, which is what
makes the rule safe.
*/
export async function getBreadcrumbJsonLd(pathname: string, title: string) {
  const segments = pathname.slice(URL_PREFIX.length).split('/').filter(Boolean);

  // Home alone is not a trail, and Google wants at least two entries.
  if (segments.length === 0) return;

  const vendors = await getCollection('vendors');
  const label = (slug: string, depth: number) => {
    if (depth === 0) return SECTIONS[slug] ?? humanise(slug);

    const vendor = vendors.find((entry) => entry.id === slug);
    return vendor?.data.name ?? THEME_BRANDS[slug] ?? humanise(slug);
  };

  const ancestors = segments.slice(0, Math.min(segments.length - 1, 2));
  const trail = [
    { name: 'Home', item: absolute('') },
    ...ancestors.map((slug, depth) => ({
      name: label(slug, depth),
      item: absolute(segments.slice(0, depth + 1).join('/'))
    })),
    { name: title }
  ];

  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: trail.map((entry, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: entry.name,
      ...('item' in entry && entry.item && { item: entry.item })
    }))
  };
}
