import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import { BASE, DOMAIN, SHIKI_THEMES } from './src/shared/config';

// https://astro.build/config
export default defineConfig({
  integrations: [mdx(), sitemap()],
  output: 'static',
  site: DOMAIN,
  base: BASE,
  prefetch: {
    defaultStrategy: 'hover'
  },
  image: {
    layout: 'constrained'
  },
  markdown: {
    shikiConfig: {
      themes: SHIKI_THEMES
    }
  },
  vite: {
    plugins: [tailwindcss()]
  }
});