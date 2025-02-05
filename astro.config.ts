import alpinejs from '@astrojs/alpinejs';
import mdx from '@astrojs/mdx';
import tailwind from '@astrojs/tailwind';
import { defineConfig } from 'astro/config';

import { BASE, DOMAIN, SHIKI_THEMES } from './src/shared/config';

// https://astro.build/config
export default defineConfig({
  integrations: [tailwind(), alpinejs(), mdx()],
  output: 'static',
  site: DOMAIN,
  base: BASE,
  image: {
    layout: 'responsive'
  },
  markdown: {
    shikiConfig: {
      themes: SHIKI_THEMES
    }
  }
});