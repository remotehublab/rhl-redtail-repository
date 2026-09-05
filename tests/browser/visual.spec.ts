import { expect, test, type Page } from '@playwright/test';

async function loadLazyImages(page: Page) {
  const lazyImages = page.locator('img[loading="lazy"]');
  for (let index = 0; index < await lazyImages.count(); index += 1) {
    const image = lazyImages.nth(index);
    await image.scrollIntoViewIfNeeded();
    await expect.poll(() => image.evaluate(
      (element) => element.complete && element.naturalWidth > 0,
    )).toBe(true);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
}

test.beforeEach(async ({ page }) => {
  await page.route(/youtube\.com|youtu\.be/, (route) =>
    route.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html>' }),
  );
});

const pages = [
  ['home', '/'],
  ['exercise-catalog', '/laboratory-exercises'],
  ['exercise-detail', '/laboratory-exercises/test-exercise'],
  ['simulation-catalog', '/simulations'],
  ['simulation-detail', '/simulations/test-simulation'],
  ['simulation-documentation', '/simulations/test-simulation/docs/1-simulation-guide.md'],
  ['device-documentation', '/simulations/test-simulation/devices/test-board/docs/1-board-guide.md'],
  ['device-catalog', '/devices'],
  ['device-detail', '/devices/test-board'],
  ['login', '/login'],
  ['registration', '/register'],
  ['authors', '/authors'],
  ['author-detail', '/authors/1'],
  ['error-403', '/_test/errors/403'],
  ['error-404', '/missing-page'],
  ['error-500', '/_test/errors/500'],
] as const;

for (const [name, url] of pages) {
  test(`@visual ${name}`, async ({ page }) => {
    await page.goto(url);

    if (name === 'home') {
      await loadLazyImages(page);
    }

    await expect(page).toHaveScreenshot(`${name}.png`, {
      fullPage: true,
    });
  });
}

test('@visual invalid login state', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('not-a-user');
  await page.getByLabel('Password').fill('bad-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await expect(page.getByText('Invalid username or password')).toHaveCount(1);
  await expect(page.getByRole('alert')).toHaveText('Invalid username or password');
  await expect(page).toHaveScreenshot('login-error.png', { fullPage: true });
});

test('@visual anonymous submission denial', async ({ page }) => {
  await page.goto('/file_submission');
  await expect(page).toHaveURL(/\/login\?next=/);
  await expect(page.getByRole('alert')).toHaveText('Please log in to access this page.');
  await expect(page).toHaveScreenshot('login-access-denied.png', { fullPage: true });
});

test('@visual admin submission form', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin-user');
  await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.goto('/file_submission');
  await expect(page).toHaveScreenshot('admin-submission.png', { fullPage: true });
});

test('@visual mobile navigation open', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'visual-mobile');
  await page.goto('/');
  await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await expect(
    page.getByRole('navigation', { name: 'Primary navigation' })
      .getByRole('link', { name: 'Simulations', exact: true }),
  ).toBeVisible();
  await loadLazyImages(page);
  await expect(page).toHaveScreenshot('mobile-navigation-open.png', { fullPage: true });
});
