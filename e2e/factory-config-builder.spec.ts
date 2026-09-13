import { readFileSync } from 'node:fs';
import type { Page } from '@playwright/test';

import { expect, test } from '@playwright/test';

const KSW_FILE = 'public/factory_config.xml';
const original = readFileSync(KSW_FILE, 'utf8');

// The listing is raw file text with no accessible representation of its own,
// so it is the one thing reached by attribute rather than by role.
const LISTING = '[data-listing-code] code';

// The <details> holding the change table. A <details> exposes its summary as
// content rather than as an accessible name, so it is found by that text; the
// only other group on the page is the paste box, which never mentions changes.
const changes = (page: Page) => page.getByRole('group').filter({ hasText: /change/ });

test.beforeEach(async ({ page }) => {
  await page.goto('factory-settings/ksw/');
});

test('the page works without loading anything', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Factory settings for KSW' })).toBeVisible();
  await expect(page.getByRole('heading', { name: /An example .* file/ })).toBeVisible();

  // Controls mirror the car screen until a file arrives; they are out of the
  // accessibility tree so nothing claims to be interactive.
  await expect(page.getByRole('checkbox', { name: 'USB HOST' })).toHaveCount(0);
  await expect(page.getByRole('combobox', { name: 'UI Selection' })).toHaveCount(0);
});

test('a loaded file drives the controls, the diff and the listing', async ({ page }) => {
  await page.getByLabel('Choose your factory_config.xml').setInputFiles(KSW_FILE);

  await expect(page.getByRole('status')).toContainText('31 settings found');

  // <USB_HOST>1</USB_HOST> in the file, so the box arrives ticked and live.
  const usbHost = page.getByRole('checkbox', { name: 'USB HOST' });
  await expect(usbHost).toBeChecked();
  await expect(usbHost).toBeEnabled();

  // <UI_type>BMW_EVO_ID7_V2</UI_type>, shown by its human label.
  const theme = page.getByRole('combobox', { name: 'UI Selection' });
  await expect(theme).toHaveValue('BMW_EVO_ID7_V2');

  await expect(changes(page)).toContainText('No changes yet');

  await usbHost.uncheck();
  await theme.selectOption({ label: 'Audi MIB3' });

  await expect(changes(page)).toContainText('2 changes');
  await changes(page).getByText('show them').click();

  const rows = page.getByRole('row');
  await expect(rows.filter({ hasText: 'USB_HOST' })).toContainText(['USB HOST']);
  await expect(rows.filter({ hasText: 'UI_type' })).toContainText(['UI Selection']);

  // The guarantee: the listing is the file that arrived, with those two values
  // rewritten and nothing else touched.
  const expected = original
    .replace('<USB_HOST>1</USB_HOST>', '<USB_HOST>0</USB_HOST>')
    .replace('<UI_type>BMW_EVO_ID7_V2</UI_type>', '<UI_type>Audi_mib3</UI_type>');

  expect(expected).not.toBe(original);
  await expect(page.locator(LISTING)).toHaveText(expected);
});

test('undo goes back to the loaded file, remove goes back to the example', async ({ page }) => {
  await page.getByLabel('Choose your factory_config.xml').setInputFiles(KSW_FILE);
  await page.getByRole('checkbox', { name: 'USB HOST' }).uncheck();
  await expect(changes(page)).toContainText('1 change');

  await page.getByRole('button', { name: 'Undo my changes' }).click();
  await expect(changes(page)).toContainText('No changes yet');
  await expect(page.getByRole('checkbox', { name: 'USB HOST' })).toBeChecked();
  await expect(page.locator(LISTING)).toHaveText(original);

  await page.getByRole('button', { name: 'Remove file' }).click();
  await expect(page.getByRole('heading', { name: /An example .* file/ })).toBeVisible();
  await expect(page.getByRole('checkbox', { name: 'USB HOST' })).toHaveCount(0);
});

test('a value the file does not offer keeps an option of its own', async ({ page }) => {
  await page.goto('factory-settings/zxw/');
  await page
    .getByLabel('Choose your zxw_factory_config.xml')
    .setInputFiles('public/zxw_factory_config.xml');

  // canProtocolSelection is 0, and 0 only appears in a protocol list that is
  // commented out. Without an option of its own this would read as a change.
  const protocol = page.getByRole('combobox', { name: 'Current Selection' }).nth(1);
  await expect(protocol).toHaveValue('0');
  await expect(protocol.locator('option').first()).toHaveText(/not in your file/);
  await expect(changes(page)).toContainText('No changes yet');
});

test('the file never leaves the browser', async ({ page }) => {
  const offSite: string[] = [];
  const withBody: string[] = [];

  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.hostname !== 'localhost') offSite.push(request.url());
    if (request.postData()) withBody.push(request.url());
  });

  await page.getByLabel('Choose your factory_config.xml').setInputFiles(KSW_FILE);
  await page.getByRole('checkbox', { name: 'USB HOST' }).uncheck();
  await expect(changes(page)).toContainText('1 change');

  expect(withBody).toEqual([]);
  // The analytics script is the only third party this site loads at all.
  expect(offSite.filter((url) => !url.includes('umami.is'))).toEqual([]);
});

test('copying hands over the whole file', async ({ page, context, browserName }) => {
  test.skip(browserName !== 'chromium', 'clipboard permissions are Chromium-only');
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);

  await page.getByLabel('Choose your factory_config.xml').setInputFiles(KSW_FILE);
  await page.getByRole('button', { name: 'Copy the whole file' }).click();

  await expect(page.getByRole('status')).toContainText('Copied the whole file');

  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied).toBe(original);
});

test('the page does not scroll sideways once a file is loaded', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto('factory-settings/zxw/');
  await page
    .getByLabel('Choose your zxw_factory_config.xml')
    .setInputFiles('public/zxw_factory_config.xml');

  await expect(page.getByRole('combobox', { name: 'Current Selection' }).first()).toBeVisible();

  // The long option labels in CarDisplayParam once pushed the page 208px wider
  // than the viewport.
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  expect(overflow).toBeLessThanOrEqual(0);
});
