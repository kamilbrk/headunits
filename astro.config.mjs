import tailwind from '@astrojs/tailwind';
import alpinejs from "@astrojs/alpinejs";
import { defineConfig } from 'astro/config';

import { DOMAIN, BASE, SHIKI_THEMES } from './src/shared/config'

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
