import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

const repositoryRoot = __dirname;
const python = process.env.REDTAIL_PYTHON ?? path.join(repositoryRoot, '.venv/bin/python');

export default defineConfig({
  testDir: path.join(repositoryRoot, 'tests/browser'),
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [['line'], ['html', { open: 'never', outputFolder: 'output/playwright/report' }]]
    : [['list'], ['html', { open: 'never', outputFolder: 'output/playwright/report' }]],
  outputDir: path.join(repositoryRoot, 'output/playwright/results'),
  snapshotPathTemplate:
    '{testDir}/__screenshots__/{testFilePath}/{projectName}/{arg}{ext}',
  expect: {
    timeout: 5_000,
    toHaveScreenshot: {
      animations: 'disabled',
      maxDiffPixelRatio: 0.01,
    },
  },
  use: {
    baseURL: 'http://127.0.0.1:5010',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: `"${python}" -m tests.browser_server`,
    cwd: repositoryRoot,
    url: 'http://127.0.0.1:5010',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'chromium',
      grepInvert: /@visual/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      grepInvert: /@visual/,
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      grepInvert: /@visual/,
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'visual-desktop',
      grep: /@visual/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: 'visual-mobile',
      grep: /@visual/,
      use: {
        ...devices['iPhone 13'],
      },
    },
  ],
});
