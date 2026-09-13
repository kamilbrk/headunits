import { expect, test } from '@playwright/test';

/**
The three client-side features outside the config builder. None had a test, and
a CSP experiment showed search can stop working while the page still renders
perfectly — the kind of break nobody notices until someone tries to use it.
*/

const PHONE = { width: 390, height: 780 };
const DESKTOP = { width: 1280, height: 900 };

test.describe('colour scheme', () => {
  test('follows the system preference when nothing is stored', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('');
    await expect(page.locator('html')).toHaveClass(/dark/);

    await page.emulateMedia({ colorScheme: 'light' });
    await page.goto('');
    await expect(page.locator('html')).not.toHaveClass(/dark/);
  });

  test('the switch flips the scheme and says what it will do next', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    await page.setViewportSize(DESKTOP);
    await page.goto('');

    const toggle = page.getByRole('button', { name: /switch to dark mode/i });
    await expect(toggle).toBeVisible();

    await toggle.click();
    await expect(page.locator('html')).toHaveClass(/dark/);
    await expect(page.getByRole('button', { name: /switch to light mode/i })).toBeVisible();
  });

  test('a chosen scheme outlives a reload and beats the system preference', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    await page.setViewportSize(DESKTOP);
    await page.goto('');
    await page.getByRole('button', { name: /switch to dark mode/i }).click();

    await page.reload();
    await expect(page.locator('html')).toHaveClass(/dark/);
    expect(await page.evaluate(() => localStorage.getItem('theme'))).toBe('dark');
  });

  test('it survives a client-side navigation', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    await page.setViewportSize(DESKTOP);
    await page.goto('');
    await page.getByRole('button', { name: /switch to dark mode/i }).click();

    // ClientRouter swaps the document, so the scheme has to be re-applied.
    await page.getByRole('link', { name: 'Glossary' }).click();
    await expect(page).toHaveURL(/glossary/);
    await expect(page.locator('html')).toHaveClass(/dark/);
  });
});

test.describe('sidebar', () => {
  const sidebar = '#primary-nav';

  test('is out of the way on a phone until asked for', async ({ page }) => {
    await page.setViewportSize(PHONE);
    await page.goto('');

    await expect(page.locator(sidebar)).toBeHidden();

    // The header's button is the one a reader can actually reach: the sidebar
    // carries a "Close sidebar" button of its own, but the sticky header
    // paints over it, so the same control opens and closes.
    const toggle = page.getByRole('button', { name: 'Open sidebar' });

    await toggle.click();
    await expect(page.locator(sidebar)).toBeVisible();

    await toggle.click();
    await expect(page.locator(sidebar)).toBeHidden();
  });

  test('a tap beside it closes it', async ({ page }) => {
    await page.setViewportSize(PHONE);
    await page.goto('');
    await page.getByRole('button', { name: 'Open sidebar' }).click();
    await expect(page.locator(sidebar)).toBeVisible();

    // The panel is 288px wide, so the page beyond it is the "outside".
    await page.mouse.click(PHONE.width - 20, PHONE.height / 2);
    await expect(page.locator(sidebar)).toBeHidden();
  });

  test('is always there on a wide screen', async ({ page }) => {
    await page.setViewportSize(DESKTOP);
    await page.goto('');

    await expect(page.locator(sidebar)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Open sidebar' })).toBeHidden();
  });
});

test.describe('search', () => {
  test('finds pages and puts the query in the URL', async ({ page }) => {
    await page.goto('search/');

    const box = page.locator('#search input').first();
    await expect(box).toBeVisible();

    await box.fill('glossary');
    await expect(page.locator('.pagefind-ui__result').first()).toBeVisible();
    await expect(page).toHaveURL(/[?&]q=glossary/);
  });

  test('a shared search link arrives with its results', async ({ page }) => {
    await page.goto('search/?q=theme');

    await expect(page.locator('#search input').first()).toHaveValue('theme');
    await expect(page.locator('.pagefind-ui__result').first()).toBeVisible();
  });

  test('says so plainly when nothing matches', async ({ page }) => {
    await page.goto('search/');
    await page.locator('#search input').first().fill('zzzznotathingzzzz');

    await expect(page.locator('.pagefind-ui__message')).toContainText(/no results/i);
    await expect(page.locator('.pagefind-ui__result')).toHaveCount(0);
  });
});
