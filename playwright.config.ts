import { defineConfig, devices } from '@playwright/test';

// The site is served under a base path, so every relative URL in a spec is
// resolved against it rather than the server root.
const BASE_URL = 'http://localhost:4321/headunits/';

/**
Tests run against `npm run preview`, i.e. the real build in `dist/`, as the
Astro docs recommend — the dev server transforms modules differently and would
not catch a problem that only shows up in the shipped output.
*/
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  // A committed `.only` should fail the build rather than quietly skip the rest.
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  // One worker on CI; locally Playwright picks a sensible number. The key is
  // omitted rather than set to undefined, which `exactOptionalPropertyTypes`
  // rejects.
  ...(process.env.CI ? { workers: 1 } : {}),
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    // The second engine that matters for this audience: most readers arrive on
    // a phone, and the builder leans on the clipboard and file APIs.
    { name: 'mobile-safari', use: { ...devices['iPhone 14'] } }
  ],
  webServer: {
    command: 'npm run preview',
    url: BASE_URL,
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI
  }
});
