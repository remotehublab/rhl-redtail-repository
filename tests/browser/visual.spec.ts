import { expect, test } from '@playwright/test';

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
  ['device-catalog', '/devices'],
  ['device-detail', '/devices/test-board'],
  ['login', '/login'],
  ['registration', '/register'],
] as const;

for (const [name, url] of pages) {
  test(`@visual ${name}`, async ({ page }) => {
    await page.goto(url);
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
  await expect(page.getByText('Invalid username or password').first()).toBeVisible();
  await expect(page).toHaveScreenshot('login-error.png', { fullPage: true });
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
  await expect(page).toHaveScreenshot('mobile-navigation-open.png', { fullPage: true });
});
