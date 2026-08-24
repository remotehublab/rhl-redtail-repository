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
  await page.route(/youtube\.com|youtube-nocookie\.com|youtu\.be/, (route) =>
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
    await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible();
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

  await page.context().clearCookies();
  await page.goto('/login?url=https://example.test');
  await page.getByLabel('Username').fill('admin-user');
  await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await expect(page).toHaveURL('http://127.0.0.1:5010/');
});

test('auth header links stay clean and preserve legitimate return paths', async ({ page }) => {
  for (const path of [
    '/login',
    '/login?url=/register?url%3D/login?',
    '/register',
    '/register?url=/login?url%3D/register?',
  ]) {
    await page.goto(path);
    const accountNavigation = page.locator('.nav-account');
    await expect(
      accountNavigation.getByRole('link', { name: 'Log in', exact: true }),
    ).toHaveAttribute('href', '/login');
    await expect(
      accountNavigation.getByRole('link', { name: 'Register', exact: true }),
    ).toHaveAttribute('href', '/register');
  }

  await page.goto('/devices?framework=native');
  const accountNavigation = page.locator('.nav-account');
  const loginLink = accountNavigation.getByRole('link', { name: 'Log in', exact: true });
  const loginHref = await loginLink.getAttribute('href');
  expect(loginHref).not.toBeNull();
  const loginUrl = new URL(loginHref!, page.url());
  expect(loginUrl.pathname).toBe('/login');
  expect(loginUrl.searchParams.get('url')).toBe('/devices?framework=native');
  await expect(
    accountNavigation.getByRole('link', { name: 'Register', exact: true }),
  ).toHaveAttribute('href', '/register');

  await loginLink.click();
  await page.getByLabel('Username').fill('admin-user');
  await page.getByLabel('Password').fill('test-password');
  await page.getByRole('button', { name: 'Log in' }).click();
  await expect(page).toHaveURL(/\/devices\?framework=native$/);
  await expect(page.getByText('Test Board', { exact: true })).toBeVisible();
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
  await expect(
    page.getByRole('link', { name: `Browser Guide ${testInfo.project.name}`, exact: true }).first(),
  ).toBeVisible();
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
  await expect(
    page.getByRole('navigation', { name: 'Primary navigation' })
      .getByRole('link', { name: 'Simulations', exact: true }),
  ).toBeVisible();
});

test('learning goals card is padded and contains long content', async ({ page }) => {
  for (const viewport of [
    { width: 390, height: 844 },
    { width: 1440, height: 1000 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto('/laboratory-exercises/test-exercise');

    const dimensions = await page.locator('.learning-goals-sidebar .card').evaluate((card) => {
      const body = card.querySelector('.card-body') as HTMLElement;
      const goals = body.firstElementChild as HTMLElement;
      goals.textContent =
        'Translate rain-driven behavior into deterministic controller logic; ' +
        'map every signal to the remote hardware interface; distinguish ' +
        'controller-owned movement from simulation-owned reversal; stop safely ' +
        'on contradictory endpoint feedback; and test pause, resume, automatic ' +
        'reversal, optional-button isolation, fault, and recovery.';

      const cardBounds = card.getBoundingClientRect();
      const bodyBounds = body.getBoundingClientRect();
      const bodyStyle = getComputedStyle(body);
      return {
        cardBottom: cardBounds.bottom,
        bodyBottom: bodyBounds.bottom,
        cardScrollHeight: card.scrollHeight,
        cardClientHeight: card.clientHeight,
        paddingLeft: Number.parseFloat(bodyStyle.paddingLeft),
        paddingRight: Number.parseFloat(bodyStyle.paddingRight),
      };
    });

    expect(dimensions.paddingLeft).toBeGreaterThanOrEqual(16);
    expect(dimensions.paddingRight).toBeGreaterThanOrEqual(16);
    expect(dimensions.bodyBottom).toBeLessThanOrEqual(dimensions.cardBottom + 1);
    expect(dimensions.cardScrollHeight).toBeLessThanOrEqual(dimensions.cardClientHeight + 1);
  }
});

test('home video facade loads the privacy-enhanced embed on demand', async ({ page }) => {
  await page.goto('/');
  const playButton = page.getByRole('button', { name: 'Watch the introduction' });
  await expect(playButton).toBeVisible();
  await expect(playButton).toHaveCount(1);
  await expect(playButton.locator('img')).toHaveAttribute(
    'src',
    /redtail-introduction-poster\.jpg$/,
  );
  await expect(
    page.getByRole('link', { name: 'Explore the Parking Lot simulation' }),
  ).toBeVisible();

  const demonstrationButton = page.getByRole('button', {
    name: 'Watch the demonstration',
  });
  await expect(demonstrationButton.locator('img')).toHaveAttribute(
    'src',
    /redtail-parking-lot-demo-poster\.jpg$/,
  );

  await playButton.click();
  await expect(
    page.locator('iframe[src*="youtube-nocookie.com/embed/cfuF6VmhtMM"]'),
  ).toBeVisible();
});

test('home introduction stays widescreen across responsive breakpoints', async ({ page }) => {
  await page.goto('/');

  for (const width of [390, 767, 768, 991, 992, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    const dimensions = await page.locator('.hero-video-stage .video-facade').evaluate((facade) => {
      const bounds = facade.getBoundingClientRect();
      return {
        clientWidth: document.documentElement.clientWidth,
        ratio: bounds.width / bounds.height,
        scrollWidth: document.documentElement.scrollWidth,
      };
    });

    expect(dimensions.ratio).toBeCloseTo(16 / 9, 2);
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
  }
});

test('pages ship lightweight inline icons and dimensioned images', async ({ page }) => {
  for (const [, url] of publicPages) {
    await page.goto(url);
    await expect(page.locator('link[href*="fontawesome"]')).toHaveCount(0);
    await expect(page.locator('script[src*="fontawesome"], script[src*="vendor"]')).toHaveCount(0);

    const imagesWithoutDimensions = await page.locator('img').evaluateAll((images) =>
      images
        .filter((image) => !image.hasAttribute('width') || !image.hasAttribute('height'))
        .map((image) => image.getAttribute('src')),
    );
    expect(imagesWithoutDimensions).toEqual([]);
  }

  await page.goto('/');
  await expect(page.locator('svg.rt-icon')).toHaveCount(6);
  const frontendResources = await page.evaluate(() =>
    performance.getEntriesByType('resource').map((entry) => entry.name),
  );
  expect(frontendResources.some((url) => /fontawesome|jquery|vendor\./i.test(url))).toBe(false);
});

for (const [name, url] of [
  ['simulation documentation', '/simulations/test-simulation/docs/1-simulation-guide.md'],
  ['device documentation', '/simulations/test-simulation/devices/test-board/docs/1-board-guide.md'],
] as const) {
  test(`${name} preserves the simulation cover aspect ratio`, async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));

    const response = await page.goto(url);
    expect(response?.status()).toBe(200);

    const cover = page.locator('img.documentation-cover');
    await expect
      .poll(() => cover.evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0))
      .toBe(true);

    const dimensions = await cover.evaluate((image) => {
      const element = image as HTMLImageElement;
      const bounds = element.getBoundingClientRect();
      return {
        naturalRatio: element.naturalWidth / element.naturalHeight,
        renderedRatio: bounds.width / bounds.height,
        renderedWidth: bounds.width,
        widthAttribute: element.getAttribute('width'),
        heightAttribute: element.getAttribute('height'),
        objectFit: getComputedStyle(element).objectFit,
      };
    });

    expect(dimensions.renderedWidth).toBeLessThanOrEqual(200);
    expect(dimensions.naturalRatio).toBeGreaterThan(0);
    expect(dimensions.renderedRatio).toBeCloseTo(1, 2);
    expect(dimensions.widthAttribute).toBe('200');
    expect(dimensions.heightAttribute).toBe('200');
    expect(dimensions.objectFit).toBe('contain');
    expect(errors).toEqual([]);
  });
}

test('markdown tables remain accessible on narrow screens', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/simulations/test-simulation/devices/test-board/docs/1-board-guide.md');

  const dimensions = await page.locator('.markdown-block').evaluate((block) => {
    block.innerHTML = `
      <table>
        <thead><tr><th>Signal</th><th>Description</th><th>HAL name</th></tr></thead>
        <tbody><tr><td>personSensor</td><td>A person is waiting at the door</td><td>GPIO_PIN_WITH_AN_INTENTIONALLY_LONG_UNBROKEN_NAME</td></tr></tbody>
      </table>
    `;
    const table = block.querySelector('table') as HTMLTableElement;
    const tableBounds = table.getBoundingClientRect();
    return {
      documentClientWidth: document.documentElement.clientWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      overflowX: getComputedStyle(table).overflowX,
      tableClientWidth: table.clientWidth,
      tableScrollWidth: table.scrollWidth,
      tableRight: tableBounds.right,
    };
  });

  expect(dimensions.overflowX).toBe('auto');
  expect(dimensions.tableScrollWidth).toBeGreaterThan(dimensions.tableClientWidth);
  expect(dimensions.tableRight).toBeLessThanOrEqual(dimensions.documentClientWidth + 1);
  expect(dimensions.documentScrollWidth).toBeLessThanOrEqual(dimensions.documentClientWidth + 1);
});

const instructorMailto = 'mailto:rhlab@uw.edu?subject=REDTAIL%20instructor%20inquiry';

test('homepage and footer expose the instructor contact path', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('a[href*="rhlab.ece.uw.edu/join-us"]')).toHaveCount(0);

  const contactLinks = page.getByRole('link', { name: 'Email the REDTAIL team', exact: true });
  await expect(contactLinks).toHaveCount(2);
  for (const link of await contactLinks.all()) {
    await expect(link).toHaveAttribute('href', instructorMailto);
    await expect(link).not.toHaveAttribute('target', '_blank');
  }

  await expect(
    page.locator('footer').getByRole('link', { name: 'Contact', exact: true }),
  ).toHaveAttribute('href', instructorMailto);

  for (const [name, href] of [
    ['RHLab at the University of Washington', 'https://rhlab.ece.uw.edu/'],
    ['LabsLand', 'https://labsland.com/'],
  ] as const) {
    const partnerLink = page.locator('footer').getByRole('link', { name, exact: true });
    await expect(partnerLink).toHaveAttribute('href', href);
    await expect(partnerLink).toHaveAttribute('target', '_blank');
    await expect(partnerLink).toHaveAttribute('rel', 'noopener noreferrer');
  }

  await expect(
    page.getByRole('navigation', { name: 'On this page' })
      .getByRole('link', { name: 'Work with us', exact: true }),
  ).toHaveAttribute('href', '#support');

  await expect(page.locator('#support')).toContainText(
    'rhlab@uw.edu · Remote Hub Lab, University of Washington',
  );

  for (const name of [
    'Explore laboratory exercises',
    'Browse simulations',
    'Explore the simulation library',
    'View the source on GitHub',
    'Browse current exercises',
    'Register',
  ]) {
    await expect(page.getByRole('link', { name, exact: true }).first()).toBeVisible();
  }

  await expect(page.getByRole('link', { name: 'Create an instructor account' })).toHaveCount(0);
  await expect(page.locator('body')).not.toContainText('verified academic account');
  await expect(page.locator('body')).not.toContainText('instructor-only solution materials');
});

test('registration directs university instructors to the REDTAIL team', async ({ page }) => {
  await page.goto('/register');

  await expect(page.locator('body')).toContainText('Instructor access is arranged separately');
  await expect(
    page.getByRole('link', { name: 'Email the REDTAIL team about instructor access.' }),
  ).toHaveAttribute('href', instructorMailto);
  await expect(page.locator('body')).not.toContainText('Use your academic email');
  await expect(page.locator('body')).not.toContainText('laboratory solutions');
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
