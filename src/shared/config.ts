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

/** Use this for other links across the site */
export const URL_PREFIX = BASE ? `${BASE}/` : '/';

export const NAVIGATION = [
  { name: 'Updates', href: `${URL_PREFIX}updates` },
  { name: 'Themes', href: `${URL_PREFIX}themes` },
  { name: 'Factory settings', href: `${URL_PREFIX}factory-settings` },
  // { name: 'Apps', href: `${URL_PREFIX}apps` },
  { name: 'FAQ', href: `${URL_PREFIX}faq` },
  { name: 'About', href: `${URL_PREFIX}about` }
];

export const DEFAULT_PAGE_TITLE = 'KSW Head Units';
export const DEFAULT_PAGE_DESCRIPTION = '';

export const SHIKI_THEMES = {
  light: 'github-light',
  dark: 'github-dark'
};
