import alpinejs from '@astrojs/alpinejs';
import mdx from '@astrojs/mdx';
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import { BASE, DOMAIN, SHIKI_THEMES } from './src/shared/config';

// https://astro.build/config
export default defineConfig({
  integrations: [alpinejs(), mdx()],
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
  },
  vite: {
    plugins: [tailwindcss()]
  },
  experimental: {
    preserveScriptOrder: true
  }
});