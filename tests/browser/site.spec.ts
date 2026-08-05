import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const publicPages = [
  ['home', '/'],
  ['exercises', '/laboratory-exercises'],
  ['simulations', '/simulations'],
  ['devices', '/devices'],
  ['authors', '/authors'],
  ['exercise detail', '/laboratory-exercises/test-exercise'],
  ['simulation detail', '/simulations/test-simulation'],
  ['device detail', '/devices/test-board'],
  ['login', '/login'],
  ['registration', '/register'],
] as const;

test.beforeEach(async ({ page }) => {
  await page.route(/youtube\.com|youtu\.be/, (route) =>
    route.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html>' }),
  );
});

for (const [name, url] of publicPages) {
  test(`${name} page loads without browser errors`, async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));

    const response = await page.goto(url);
    expect(response?.status()).toBe(200);
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test('catalog navigation and filtering work', async ({ page }) => {
  await page.goto('/laboratory-exercises');
  await expect(page.getByText('Test Exercise', { exact: true })).toBeVisible();
  await page.getByText('Test Exercise', { exact: true }).click();
  await expect(page).toHaveURL(/laboratory-exercises\/test-exercise$/);
  await expect(page.getByText('Exercise Guide', { exact: true })).toBeVisible();

  await page.goto('/simulations?category=digital-twin');
  await expect(page.getByText('Test Simulation', { exact: true })).toBeVisible();
  await page.goto('/devices?framework=native');
  await expect(page.getByText('Test Board', { exact: true })).toBeVisible();
});

test('login protects admin submission and rejects external redirects', async ({ page }) => {
  await page.goto('/file_submission');
  await expect(page).toHaveURL(/\/login\?next=/);

  await page.getByLabel('Username').fill('admin-user');
  await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await expect(page).toHaveURL(/\/file_submission$/);
  await expect(page.getByText('Upload Document & Update Exercise')).toBeVisible();

  await page.context().clearCookies();
  await page.goto('/login?next=//example.test');
  await page.getByLabel('Username').fill('admin-user');
  await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await expect(page).toHaveURL('http://127.0.0.1:5010/');
});

test('admin can upload a simulation document in the browser', async ({ page }, testInfo) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin-user');
  await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.goto('/file_submission');

  await page.locator('#targetType').selectOption('simulation');
  await page.locator('select[name="simulation_id"]').selectOption('1');
  await page.locator('input[name="title"]').fill(`Browser Guide ${testInfo.project.name}`);
  await page.locator('input[name="file"]').setInputFiles({
    name: 'browser-guide.md',
    mimeType: 'text/markdown',
    buffer: Buffer.from('# Browser-uploaded guide'),
  });
  await page.getByRole('button', { name: 'Apply Changes' }).click();
  await expect(page.getByRole('status')).toContainText('Successfully updated');

  await page.goto('/simulations/test-simulation');
  await expect(page.getByText(`Browser Guide ${testInfo.project.name}`)).toBeVisible();
});

test('mobile navigation opens and every key page avoids horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const [, url] of publicPages) {
    await page.goto(url);
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
  }

  await page.goto('/');
  await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await expect(page.getByRole('link', { name: 'Simulations' })).toBeVisible();
});

for (const [name, url] of publicPages) {
  test(`${name} has no WCAG A/AA accessibility violations`, async ({ page }) => {
    await page.goto(url);
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
