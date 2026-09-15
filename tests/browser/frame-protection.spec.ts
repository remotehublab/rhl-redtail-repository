import { expect, test } from '@playwright/test';

test('same-origin framing works but an external parent is blocked', async ({ page, baseURL, browserName }) => {
  const markup = `<iframe title="Repository" src="${baseURL}/login"></iframe>`;
  await page.route(`${baseURL}/_frame-check`, route => route.fulfill({ contentType: 'text/html', body: markup }));
  await page.goto('/_frame-check');
  await expect(page.frameLocator('iframe').getByRole('heading', { name: 'Log in', exact: true })).toBeVisible();

  // Both origins are loopback so private-network protections cannot mask our policy.
  const externalParent = baseURL!.replace('127.0.0.1', 'localhost') + '/_frame-check';
  await page.route(externalParent, route => route.fulfill({ contentType: 'text/html', body: markup }));
  const response = await page.request.get('/login');
  expect(response.headers()['content-security-policy']).toBe("frame-ancestors 'self'");
  expect(response.headers()['x-frame-options']).toBe('SAMEORIGIN');
  // Positive control: this exact cross-origin harness works without the headers.
  await page.route(`${baseURL}/login`, async route => {
    const original = await route.fetch();
    const headers = original.headers();
    delete headers['content-security-policy'];
    delete headers['x-frame-options'];
    await route.fulfill({ response: original, headers });
  });
  await page.goto(externalParent);
  await expect(page.frameLocator('iframe').getByRole('heading', { name: 'Log in', exact: true })).toBeVisible();
  await page.unroute(`${baseURL}/login`);
  // Firefox's blocked frame has no inspectable execution context; assert its
  // explicit CSP rejection instead. Other engines expose an empty error frame.
  const blocked = browserName === 'firefox' ? page.waitForEvent('console', {
    predicate: message => /frame-ancestors|X-Frame-Options/i.test(message.text()),
  }) : null;
  await page.goto(externalParent);
  if (blocked) await blocked;
  else await expect(page.frameLocator('iframe').getByRole('heading', { name: 'Log in', exact: true })).toHaveCount(0);
});

test('frame-ancestor protection does not block the outgoing video embed', async ({ page }) => {
  // Isolate our policy from third-party video availability and consent state.
  await page.route('https://www.youtube-nocookie.com/embed/**', route => route.fulfill({
    contentType: 'text/html', body: '<h1>Video provider loaded</h1>',
  }));
  await page.goto('/');
  await page.getByRole('button', { name: 'Watch the introduction' }).click();
  await expect(page.frameLocator('iframe.video-embed').getByRole('heading', { name: 'Video provider loaded' })).toBeVisible();
});
