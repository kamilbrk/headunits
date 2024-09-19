import tailwind from '@astrojs/tailwind';
import alpinejs from '@astrojs/alpinejs';
import { defineConfig } from 'astro/config';

import { BASE, DOMAIN, SHIKI_THEMES } from './src/shared/config';

const IGNORED = [
  'src/content/updates/*/*/*.zip',
  'src/content/updates/*/*/*/**',
  'public/bin/*'
];

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
  },
  vite: {
    server: {
      fs: {
        deny: IGNORED
      },
      watch: {
        ignored: IGNORED
      }
    },
    build: {
      rollupOptions: {
        // Ignore specific files from the build
        external: IGNORED
      }
    }
  }
});
