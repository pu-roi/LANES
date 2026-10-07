import { expect, test, type Page, type TestInfo } from '@playwright/test';

// Both configured viewport projects exercise the Chromium browser used by Android/PWA.
test.use({ browserName: 'chromium' });

async function setup(page: Page, info: TestInfo, state: 'populated' | 'fallback' | 'empty' | 'error') {
  const control = { state, requests: 0 };
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/feed/hotspots')) {
      control.requests++;
      if (control.state === 'error') return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      return route.fulfill({ json: {
        hotspots: control.state === 'empty' ? [] : [{ id: '71', name: 'Ortigas Avenue, Pasig',
          latitude: 14.58, longitude: 121.08, post_count: 4, contributor_count: 3,
          latest_post_at: new Date().toISOString() }],
        window_hours: control.state === 'populated' ? 24 : 48, as_of: new Date().toISOString(),
      } });
    }
    if (url.pathname.endsWith('/feed')) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    if (url.pathname.endsWith('/feed/leaderboard')) return route.fulfill({ json: { reporters: [] } });
    return route.fulfill({ json: [] });
  });
  await page.goto('/feed', { waitUntil: 'domcontentloaded' });
  // The feed is server rendered; wait for client hydration before using its drawer.
  await expect.poll(() => control.requests, { timeout: 20_000 }).toBeGreaterThan(0);
  if (info.project.name === 'mobile-chromium') {
    await page.getByRole('button', { name: 'Open navigation menu' }).click();
  }
  return control;
}

test('shows recent activity and a working map link on desktop and mobile', async ({ page }, info) => {
  await setup(page, info, 'populated');
  const panel = page.getByRole('region', { name: 'Trending Hotspots' }).filter({ visible: true });
  await expect(panel.getByText('Community activity · Last 24 hours')).toBeVisible();
  const link = panel.getByRole('link', { name: 'Ortigas Avenue, Pasig 4 posts' });
  await expect(link).toHaveAttribute('href', '/map?lat=14.58&lng=121.08&zoom=15');
  await expect(link).toHaveAttribute('title', '4 posts from 3 people in the last 24 hours');
  // The mobile drawer slides in; measure after it reaches the viewport.
  await expect.poll(async () => (await panel.boundingBox())?.x).toBeGreaterThanOrEqual(0);
  const bounds = await panel.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.screenshot({ path: info.outputPath('trending-hotspots.png') });
  await link.click();
  await expect(page).toHaveURL(/\/map\?lat=14.58&lng=121.08&zoom=15/);
});

test('has an honest recent empty state', async ({ page }, info) => {
  await setup(page, info, 'empty');
  const panel = page.getByRole('region', { name: 'Trending Hotspots' }).filter({ visible: true });
  await expect(panel.getByText('No trending places in the last 48 hours.')).toBeVisible();
  await expect(panel.getByRole('link')).toHaveCount(0);
});

test('surfaces failures and retries successfully', async ({ page }, info) => {
  const control = await setup(page, info, 'error');
  const panel = page.getByRole('region', { name: 'Trending Hotspots' }).filter({ visible: true });
  await expect(panel.getByRole('alert')).toHaveText('Couldn’t load recent hotspots.');
  control.state = 'populated';
  await panel.getByRole('button', { name: 'Retry' }).click();
  await expect(panel.getByRole('link', { name: 'Ortigas Avenue, Pasig 4 posts' })).toBeVisible();
  expect(control.requests).toBeGreaterThan(1);
});

test('refreshes automatically so expired activity disappears', async ({ page }, info) => {
  await page.clock.install();
  const control = await setup(page, info, 'populated');
  const panel = page.getByRole('region', { name: 'Trending Hotspots' }).filter({ visible: true });
  await expect(panel.getByRole('link')).toHaveCount(1);
  control.state = 'empty';
  await page.clock.fastForward(61_000);
  await expect(panel.getByText('No trending places in the last 48 hours.')).toBeVisible();
  await expect(panel.getByRole('link')).toHaveCount(0);
});

test('labels the fallback window and returns to 24 hours after fresh activity', async ({ page }, info) => {
  await page.clock.install();
  const control = await setup(page, info, 'fallback');
  const panel = page.getByRole('region', { name: 'Trending Hotspots' }).filter({ visible: true });
  await expect(panel.getByText('Community activity · Past 48 hours')).toBeVisible();
  await expect(panel.getByRole('link')).toHaveAttribute('title', '4 posts from 3 people in the last 48 hours');
  await expect(panel.getByText('Community activity · Last 24 hours')).toHaveCount(0);
  await expect.poll(async () => (await panel.boundingBox())?.x).toBeGreaterThanOrEqual(0);
  await page.screenshot({ path: info.outputPath('trending-hotspots-fallback.png') });
  control.state = 'populated';
  await page.clock.fastForward(61_000);
  await expect(panel.getByText('Community activity · Last 24 hours')).toBeVisible();
  await expect(panel.getByRole('link')).toHaveAttribute('title', '4 posts from 3 people in the last 24 hours');
});
