import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { satteri } from '@astrojs/markdown-satteri';
import { defineConfig } from 'astro/config';
import pagefind from 'astro-pagefind';
import tailwindcss from '@tailwindcss/vite';
import { BASE, DOMAIN, SHIKI_THEMES, URL_PREFIX } from './src/shared/config';
import basePathPlugin from './src/shared/base-path.plugin';
import { getUpdateLastmods } from './src/shared/sitemap-lastmod';

const updateLastmods = getUpdateLastmods();

// https://astro.build/config
export default defineConfig({
  integrations: [
    mdx(),
    sitemap({
      // The search page is an empty shell until Pagefind hydrates it.
      filter: (page) => !page.startsWith(new URL(`${URL_PREFIX}search/`, DOMAIN).href),
      serialize(item) {
        const lastmod = updateLastmods.get(item.url);
        return lastmod ? { ...item, lastmod: lastmod.toISOString() } : item;
      }
    }),
    pagefind()
  ],
  output: 'static',
  redirects: {
    // The upgrade path used to live in the FAQ; inbound Discord and forum
    // links still point there.
    // The target is not base-prefixed by Astro, unlike the source key.
    '/faq/ksw/upgrade-path': `${URL_PREFIX}upgrade-path/ksw`
  },
  site: DOMAIN,
  base: BASE,
  prefetch: {
    defaultStrategy: 'hover'
  },
  image: {
    layout: 'constrained'
  },
  markdown: {
    processor: satteri({ hastPlugins: [basePathPlugin] }),
    shikiConfig: {
      themes: SHIKI_THEMES
    }
  },
  vite: {
    plugins: [tailwindcss()]
  }
});