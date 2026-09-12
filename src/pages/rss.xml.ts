import type { APIContext } from 'astro';

import rss from '@astrojs/rss';
import { getCollection, getEntry } from 'astro:content';

import { DEFAULT_PAGE_DESCRIPTION, DEFAULT_PAGE_TITLE, DOMAIN, URL_PREFIX } from '../shared/config';
import { getAndroidVersion, getUpdateVersion, sortEntriesByDate } from '../shared/utilities';

export async function GET(context: APIContext) {
  const updates = await getCollection('updates');
  const items = await Promise.all(
    updates.sort(sortEntriesByDate).map(async (entry) => {
      const vendor = await getEntry('vendors', entry.data.vendor);
      const platformId = `${entry.data.vendor}/${entry.data.platform}`;
      const platform = await getEntry('platforms', platformId);
      if (!vendor) throw new Error(`Missing vendor: ${entry.data.vendor}`);
      if (!platform) throw new Error(`Missing platform: ${platformId}`);

      return {
        title: `${vendor.data.name} ${platform.data.name} — ${entry.data.id}`,
        pubDate: entry.data.date,
        description:
          `Version ${getUpdateVersion(entry)} based on Android ${getAndroidVersion(entry)} ` +
          `for ${vendor.data.name} devices on the ${platform.data.name} platform.`,
        link: `${URL_PREFIX}${entry.collection}/${entry.id}`
      };
    })
  );

  return rss({
    title: `${DEFAULT_PAGE_TITLE} — firmware updates`,
    description: DEFAULT_PAGE_DESCRIPTION,
    site: new URL(URL_PREFIX, context.site ?? DOMAIN).href,
    items
  });
}
