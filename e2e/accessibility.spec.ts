import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

/**
One page per template, rather than per route: the templates are what differ,
and the site has 250 pages built from a dozen of them.
*/
const PAGES = [
  ['home', ''],
  ['safety', 'safety/'],
  ['glossary', 'glossary/'],
  ['contribute', 'contribute/'],
  ['search', 'search/'],
  ['themes hub', 'themes/'],
  ['theme brand list', 'themes/bmw/'],
  ['theme detail', 'themes/zxw/16-ksw_bmw_id7/'],
  ['help wanted', 'themes/help-wanted/'],
  ['updates list', 'updates/ksw/'],
  ['update detail', 'updates/ksw/m600/ksw-t-m600_os_v138-ota/'],
  ['platforms hub', 'platforms/'],
  ['platform detail', 'platforms/ksw/m600/'],
  ['faq list', 'faq/ksw/'],
  ['faq detail', 'faq/ksw/install-updates/'],
  ['upgrade path', 'upgrade-path/ksw/'],
  ['factory settings', 'factory-settings/ksw/'],
  ['404', '404.html']
] as const;

for (const [name, path] of PAGES) {
  test(`${name} has no accessibility violations`, async ({ page }) => {
    await page.goto(path);

    const { violations } = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(violations.map((violation) => `${violation.id}: ${violation.help}`)).toEqual([]);
  });
}

test('the factory settings page stays clean once its controls are live', async ({ page }) => {
  await page.goto('factory-settings/ksw/');
  await page
    .getByLabel('Choose your factory_config.xml')
    .setInputFiles('public/factory_config.xml');
  await expect(page.getByRole('checkbox', { name: 'USB HOST' })).toBeEnabled();

  const { violations } = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  expect(violations.map((violation) => `${violation.id}: ${violation.help}`)).toEqual([]);
});
