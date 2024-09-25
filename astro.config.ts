import alpinejs from '@astrojs/alpinejs';
import tailwind from '@astrojs/tailwind';
import { defineConfig } from 'astro/config';

import { BASE, DOMAIN, SHIKI_THEMES } from './src/shared/config';

// https://astro.build/config
export default defineConfig({
  integrations: [tailwind(), alpinejs()],
  output: 'static',
  site: DOMAIN,
  base: BASE,
  markdown: {
    shikiConfig: {
      themes: SHIKI_THEMES
    }
  }
});