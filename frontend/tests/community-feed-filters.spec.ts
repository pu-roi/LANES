import { expect as baseExpect, test, type Page } from '@playwright/test';
import type { FeedPost } from '../src/features/feed/feedApi';

const expect = baseExpect.configure({ timeout: 30_000 });
test.setTimeout(90_000);
test.use({ browserName: 'chromium' });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
} });
const now = Date.parse('2026-10-11T12:00:00Z');

async function setup(page: Page, loggedIn = true, locationAvailable = true) {
  await page.clock.install({ time: now });
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(({ loggedIn, locationAvailable }) => {
    if (loggedIn) localStorage.setItem('lanes_token', 'test-only-token');
    const sources: MockSource[] = [];
    class MockSource extends EventTarget {
      onopen: ((event: Event) => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      constructor(public url: string) {
        super(); sources.push(this);
        queueMicrotask(() => this.onopen?.(new Event('open')));
      }
      close() { sources.splice(sources.indexOf(this), 1); }
    }
    Object.defineProperty(window, 'EventSource', { value: MockSource });
    Object.assign(window, { emitFeedEvent: () => sources.forEach(source => {
      if (source.url.endsWith('/sse/stream')) source.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({ event: 'report_approved' }),
      }));
    }) });
    Object.defineProperty(navigator, 'geolocation', { value: {
      getCurrentPosition: (success: PositionCallback, failure: PositionErrorCallback) => {
        if (locationAvailable) success({ coords: { latitude: 14.57, longitude: 121.08 } } as GeolocationPosition);
        else failure({ code: 1, message: 'Location permission denied' } as GeolocationPositionError);
      },
    } });
  }, { loggedIn, locationAvailable });
  const dataset = Array.from({ length: 45 }, (_, index) => {
    const id = index + 1;
    const ageHours = id === 1 ? 720 : id === 2 ? 48 : (45 - id) / 10;
    return { id, user_id: 7, content: `Public update ${id}`, created_at: new Date(now - ageHours * 3_600_000).toISOString(),
      updated_at: new Date(now).toISOString(), upvotes: 0, downvotes: 0, comment_count: 0, author_name: 'Citizen',
      distance_meters: id === 45 ? 20000 : id === 44 ? 4000 : 500,
      report: { id, raw_text: `Public update ${id}`, source: 'direct_user', status: 'approved',
        severity: id === 3 ? 'medium' : 'high' },
      lifecycle: id % 2 ? 'active' : 'resolved',
    } as FeedPost & { lifecycle: string };
  });
  const state = { dataset, requests: [] as URLSearchParams[], fail: false,
    votePending: false, finishVote: null as (() => void) | null, errors };
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    let body: unknown = [];
    if (path.endsWith('/feed')) {
      const query = url.searchParams;
      state.requests.push(query);
      if (state.fail) return route.fulfill({ status: 503, json: { detail: 'Feed temporarily unavailable' } });
      let posts = [...state.dataset];
      if (query.get('tab') === 'nearby') posts = posts.filter(post => post.distance_meters! <= Number(query.get('radius') || 5000));
      if (query.get('severity')) posts = posts.filter(post => post.report?.severity === query.get('severity'));
      if (query.get('flood_status') !== 'all') posts = posts.filter(post => post.lifecycle === query.get('flood_status'));
      const period = query.get('date_range');
      const hours = period === 'today' ? 12 : period === '24h' ? 24 : period === '3d' ? 72 : period === '7d' ? 168 : null;
      if (hours !== null) posts = posts.filter(post => Date.parse(post.created_at) >= now - hours * 3_600_000);
      posts.sort((a, b) => (Date.parse(b.created_at) - Date.parse(a.created_at)) || b.id - a.id);
      if (query.get('sort') === 'oldest') posts.reverse();
      const skip = Number(query.get('skip')), limit = Number(query.get('limit'));
      body = { posts: posts.slice(skip, skip + limit), total: posts.length, has_more: skip + limit < posts.length };
    } else if (path.endsWith('/auth/test-token')) body = { id: 7, username: 'citizen', is_active: true, role: { name: 'Commuter' } };
    else if (/\/feed\/\d+\/vote$/.test(path)) {
      if (state.votePending) {
        await new Promise<void>(resolve => { state.finishVote = resolve; });
        return route.fulfill({ status: 503, json: { detail: 'Vote unavailable' } });
      }
      body = { post_id: Number(path.split('/').at(-2)), upvotes: 1, downvotes: 0, user_interaction: 'upvote' };
    } else if (path.endsWith('/feed/leaderboard')) body = { reporters: [] };
    else if (path.endsWith('/feed/hotspots')) body = { hotspots: [], window_hours: 24, as_of: new Date(now).toISOString() };
    else if (path.endsWith('/news/local-updates')) body = { items: [], as_of: new Date(now).toISOString() };
    else if (path.endsWith('/notifications')) body = { notifications: [], unread_count: 0, total: 0, has_more: false };
    return route.fulfill({ json: body });
  });
  return state;
}

const contents = (page: Page) => page.locator('article p.whitespace-pre-wrap');
async function openFilters(page: Page) {
  await page.getByRole('button', { name: /^Filters/ }).click();
  await expect(page.getByRole('region', { name: 'Community feed filters' })).toBeVisible();
}
async function select(page: Page, label: string, option: string) {
  const trigger = page.getByRole('button', { name: label, exact: true });
  await trigger.click();
  await page.getByRole('button', { name: option, exact: true }).click();
  await expect(trigger).toContainText(option);
}

test('default All Time and newest order, responsive controls and oldest sorting', async ({ page }, testInfo) => {
  const state = await setup(page);
  await page.goto('/feed');
  await expect(contents(page).first()).toHaveText('Public update 45');
  await expect(contents(page)).toHaveCount(20);
  await openFilters(page);
  await expect(page.getByRole('button', { name: 'Sort posts', exact: true })).toContainText('Newest First');
  await expect(page.getByRole('button', { name: 'Date posted', exact: true })).toContainText('All Time');
  const panel = page.getByRole('region', { name: 'Community feed filters' });
  const bounds = await panel.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await panel.screenshot({ path: testInfo.outputPath('community-filters.png'), animations: 'disabled' });
  await select(page, 'Sort posts', 'Oldest First');
  await expect(contents(page).first()).toHaveText('Public update 1');
  expect(state.requests.at(-1)!.get('sort')).toBe('oldest');
  expect(state.errors).toEqual([]);
});

for (const [option, value] of [['Today (UTC)', 'today'], ['Last 24 Hours', '24h'],
  ['Last 3 Days', '3d'], ['Last 7 Days', '7d']] as const) {
  test(`${option} filters the complete dataset with continuous stream`, async ({ page }) => {
    const state = await setup(page);
    await page.goto('/feed');
    await expect(contents(page)).toHaveCount(20);
    await openFilters(page);
    await select(page, 'Date posted', option);
    expect(state.requests.at(-1)!.get('date_range')).toBe(value);
    await expect(page.getByRole('button', { name: 'Load more posts', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Load more posts', exact: true }).scrollIntoViewIfNeeded();
    await expect(contents(page)).toHaveCount(40);
    expect(state.requests.at(-1)!.get('date_range')).toBe(value);
    expect(state.requests.at(-1)!.get('skip')).toBe('20');
    expect(state.errors).toEqual([]);
  });
}

test('combined filters survive continuous loading, hard refresh, voting and live refresh', async ({ page }) => {
  const state = await setup(page);
  await page.goto('/feed');
  await expect(contents(page)).toHaveCount(20);
  await openFilters(page);
  await select(page, 'Date posted', 'Last 24 Hours');
  await select(page, 'Flood status', 'Active Floods');
  await select(page, 'Flood severity', 'High');
  await expect(page.getByRole('button', { name: 'Load more posts', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Load more posts', exact: true }).scrollIntoViewIfNeeded();
  await expect(contents(page)).toHaveCount(21);
  await expect(contents(page).last()).toHaveText('Public update 5');
  await page.reload();
  await expect(contents(page)).toHaveCount(20);
  const query = state.requests.at(-1)!;
  expect([query.get('date_range'), query.get('flood_status'), query.get('severity')])
    .toEqual(['24h', 'active', 'high']);
  await page.getByRole('button', { name: 'Upvote', exact: true }).first().click();
  const requests = state.requests.length;
  await page.evaluate(() => (window as unknown as { emitFeedEvent: () => void }).emitFeedEvent());
  await expect.poll(() => state.requests.length).toBeGreaterThan(requests);
  expect(state.errors).toEqual([]);
});

test('Nearby radius, resolved reports and filters persist across tabs then reset', async ({ page }) => {
  const state = await setup(page);
  await page.goto('/feed');
  await expect(contents(page)).toHaveCount(20);
  await openFilters(page);
  await select(page, 'Flood status', 'Resolved Reports');
  await select(page, 'Sort posts', 'Oldest First');
  await page.getByRole('button', { name: 'Nearby', exact: true }).click();
  await select(page, 'Nearby radius', '1 km');
  await expect(page).toHaveURL(/radius=1000/);
  await expect(contents(page).first()).toHaveText('Public update 2');
  expect(state.requests.at(-1)!.get('radius')).toBe('1000');
  await page.getByRole('button', { name: 'Recent', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Nearby radius', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Flood status', exact: true })).toContainText('Resolved Reports');
  await page.getByRole('button', { name: 'Nearby', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Nearby radius', exact: true })).toContainText('1 km');
  await page.getByRole('region', { name: 'Community feed filters' }).getByRole('button', { name: 'Reset Filters', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sort posts', exact: true })).toContainText('Newest First');
  await expect(page.getByRole('button', { name: 'Nearby radius', exact: true })).toContainText('Auto');
  await expect(contents(page).first()).toHaveText('Public update 44');
  expect(state.requests.at(-1)!.get('radius')).toBeNull();
  expect(state.errors).toEqual([]);
});

test('empty combinations offer reset and failed filter requests display errors', async ({ page }) => {
  const state = await setup(page);
  await page.goto('/feed');
  await expect(contents(page)).toHaveCount(20);
  await openFilters(page);
  await select(page, 'Flood severity', 'Extreme');
  await expect(page.getByText('No posts match these filters.', { exact: false })).toBeVisible();
  await expect(contents(page)).toHaveCount(0);
  await page.getByRole('button', { name: 'Reset Filters', exact: true }).last().click();
  await expect(contents(page).first()).toHaveText('Public update 45');
  state.fail = true;
  await select(page, 'Date posted', 'Last 3 Days');
  await expect(page.getByText('Failed to load feed.', { exact: true })).toBeVisible();
  expect(state.errors).toEqual([]);
});

test('failed pending vote cannot restore results into a different filtered cache', async ({ page }) => {
  const state = await setup(page);
  state.votePending = true;
  await page.goto('/feed');
  await expect(contents(page)).toHaveCount(20);
  await page.locator('article').first().getByRole('button', { name: 'Upvote', exact: true }).click();
  await expect.poll(() => state.finishVote !== null).toBe(true);
  await openFilters(page);
  await select(page, 'Flood status', 'Resolved Reports');
  await expect(contents(page).first()).toHaveText('Public update 44');
  state.finishVote!();
  await expect(page.getByText('Failed to vote', { exact: true })).toBeVisible();
  await expect(contents(page).first()).toHaveText('Public update 44');
  await expect(contents(page)).not.toContainText(['Public update 45']);
  expect(state.errors).toEqual([]);
});

test('Nearby with unavailable location preserves the existing location prompt', async ({ page }) => {
  const state = await setup(page, false, false);
  await page.goto('/feed?tab=nearby&date_range=7d&radius=1000');
  await expect(page.getByText('Location Required for Nearby Feed', { exact: true })).toBeVisible();
  await openFilters(page);
  await expect(page.getByRole('button', { name: 'Nearby radius', exact: true })).toContainText('1 km');
  await expect(page.getByRole('button', { name: 'Date posted', exact: true })).toContainText('Last 7 Days');
  expect(state.requests).toHaveLength(0);
  expect(state.errors).toEqual([]);
});

test('Feed button in navigation bar refreshes feed and returns to top', async ({ page }) => {
  const state = await setup(page);
  await page.goto('/feed');
  await expect(contents(page)).toHaveCount(20);

  // Scrolling toward Load more also activates the continuous-feed sentinel.
  await page.getByRole('button', { name: 'Load more posts', exact: true }).scrollIntoViewIfNeeded();
  await expect(contents(page)).toHaveCount(40);

  // Scroll down
  await page.evaluate(() => window.scrollTo(0, 800));

  // Click Feed button in navbar
  const feedBtn = page.getByRole('link', { name: 'Feed', exact: true }).first();
  await feedBtn.click();

  // Reset to initial page and fresh posts
  await expect(contents(page)).toHaveCount(20);
  expect(state.errors).toEqual([]);
});
