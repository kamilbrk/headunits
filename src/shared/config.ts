/** Domain setting for publishing */
export const DOMAIN = 'https://kamilbrk.github.io';

/**
 * Base URL for navigation, see {@link https://docs.astro.build/en/guides/deploy/github}
 * If required, set this to `/xyz`
 * If not, make sure it's set to `undefined`
 */
export const BASE = '/ksw'; //

/** Root URL user for home page links */
export const ROOT = BASE || '/';

const prefix = BASE ? `${BASE}/` : '/';
export const NAVIGATION = [
  { name: 'Updates', href: `${prefix}updates` },
  { name: 'Themes', href: `${prefix}themes` },
  { name: 'Factory settings', href: `${prefix}factory-settings` },
  // { name: 'Apps', href: `${prefix}apps` },
  { name: 'FAQ', href: `${prefix}faq` },
  { name: 'About', href: `${prefix}about` }
];

export const DEFAULT_PAGE_TITLE = 'KSW Head Units';
export const DEFAULT_PAGE_DESCRIPTION = '';

export const SHIKI_THEMES = {
  light: 'github-light',
  dark: 'github-dark'
};
