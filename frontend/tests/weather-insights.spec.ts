import { expect, test, type Page } from '@playwright/test';

test.setTimeout(90_000);
test.use({ browserName: 'chromium' });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });

const safeMessage = 'AI weather insights are temporarily unavailable. You can still view the forecast and chart legend.';
const leakedMessage = 'OpenRouter API error: {"user_id":"private-account","message":"Add 10 credits","previous_errors":[]}';

async function setup(page: Page, outcome: 'failure' | 'success' | 'empty') {
  const calls: string[] = [];
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/weather/insights')) {
      calls.push(route.request().method());
      return outcome === 'success' ? route.fulfill({ json: { model: 'gemini-3.8-flash', insights: {
        storm_risk: 'Next four hours: 33% chance of rain with 0 mm forecast precipitation.',
        environment: '28°C, 80% humidity and 3 km/h wind.' } } }) :
        route.fulfill({ status: 429, json: { detail: leakedMessage } });
    }
    if (path.endsWith('/weather/forecast')) return route.fulfill({ json: { location: 'Pasig City',
      forecast: outcome === 'empty' ? [] : Array.from({ length: 12 }, (_, index) => ({
        dt: 1791849600 + index * 3600, time: '2026-10-13 08:00:00', temp: 28, pop: 33,
        condition: 'Cloudy', icon: 'cloudy', precip_mm: 0, humidity_pct: 80, wind_kmh: 3, wind_dir: 90,
      })) } });
    if (path.endsWith('/weather/current')) return route.fulfill({ json: { temp: 28, feels_like: 30,
      condition: 'Cloudy', icon: 'cloudy', location: 'Pasig City' } });
    if (path.endsWith('/public/stats') || path.endsWith('/public/visits')) return route.fulfill({ json: {
      daily_verified_reports: 0, total_visitors: 1, recorded: true } });
    if (path.endsWith('/feed')) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    return route.fulfill({ json: [] });
  });
  return calls;
}

test('public weather failures stay safe and chart legend fits mobile and desktop', async ({ page }, info) => {
  const calls = await setup(page, 'failure');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Insights', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'AI Weather Insights' });
  await expect(dialog).toBeVisible();
  expect(calls).toEqual([]);
  await dialog.getByRole('button', { name: 'Generate AI Insights' }).click();
  await expect(dialog.getByRole('alert')).toContainText(safeMessage);
  await expect(dialog).not.toContainText('OpenRouter');
  await expect(dialog).not.toContainText('private-account');
  await expect(dialog).not.toContainText('Add 10 credits');
  await expect(dialog).toContainText('Chart Legend');
  const bounds = await dialog.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  expect(bounds!.y).toBeGreaterThanOrEqual(0);
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(page.viewportSize()!.height);
  await dialog.getByRole('button', { name: 'Try Again' }).click();
  await expect.poll(() => calls.length).toBe(2);
  await dialog.screenshot({ path: info.outputPath('weather-safe-error.png') });
});

test('Gemini explanations render without exposing provider diagnostics', async ({ page }) => {
  const calls = await setup(page, 'success');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Insights', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'AI Weather Insights' });
  await dialog.getByRole('button', { name: 'Generate AI Insights' }).click();
  await expect(dialog).toContainText('gemini-3.8-flash');
  await expect(dialog).toContainText('33% chance of rain');
  await expect(dialog.getByRole('alert')).toHaveCount(0);
  expect(calls).toEqual(['POST']);
});

test('missing forecast cannot dispatch an AI request', async ({ page }) => {
  const calls = await setup(page, 'empty');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Insights', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'AI Weather Insights' });
  await expect(dialog.getByRole('button', { name: 'Generate AI Insights' })).toBeDisabled();
  await expect(dialog.getByRole('status')).toContainText('Insights need forecast data');
  expect(calls).toEqual([]);
});
