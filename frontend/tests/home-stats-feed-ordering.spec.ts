import { expect as baseExpect, test, type Page } from '@playwright/test';
import type { FeedPost } from '../src/features/feed/feedApi';

const expect = baseExpect.configure({ timeout: 30_000 });
test.setTimeout(90_000);
test.use({ browserName: 'chromium' });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
} });

async function setup(page: Page) {
  // Install before navigation so existing React Query intervals are controlled.
  await page.clock.install();
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    localStorage.setItem('lanes_token', 'test-only-token');
    const streams: MockSource[] = [];
    class MockSource extends EventTarget {
      onopen: ((event: Event) => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      constructor(public url: string) {
        super();
        streams.push(this);
        queueMicrotask(() => this.onopen?.(new Event('open')));
      }
      close() { streams.splice(streams.indexOf(this), 1); }
    }
    Object.defineProperty(window, 'EventSource', { value: MockSource });
    Object.assign(window, { emitTestUpdate: (event: string, snapshot = false) => {
      for (const stream of streams) {
        if (snapshot && stream.url.endsWith('/sync/stream')) {
          stream.dispatchEvent(new MessageEvent('update', { data: '[]' }));
        } else if (!snapshot && stream.url.endsWith('/sse/stream')) {
          stream.onmessage?.(new MessageEvent('message', { data: JSON.stringify({ event }) }));
        }
      }
    } });
    Object.defineProperty(navigator, 'geolocation', { value: {
      getCurrentPosition: (success: PositionCallback) => success({ coords: {
        latitude: 14.57, longitude: 121.08,
      } } as GeolocationPosition),
    } });
  });
  const post = (id: number, content: string, age: number, distance: number): FeedPost => ({
    id, user_id: 7, content, created_at: new Date(Date.now() - age * 3_600_000).toISOString(),
    updated_at: new Date().toISOString(), author_name: 'Citizen',
    upvotes: id === 1 ? 100 : 0, downvotes: 0, comment_count: id === 1 ? 50 : 0,
    distance_meters: distance, location_lat: 14.57, location_lng: 121.08,
  });
  const state = { count: 3, statsFailure: false, visitFailure: false,
    posts: [post(3, 'Outside area newest', 0, 50000), post(2, 'Latest nearby update', 1, 1000),
            post(1, 'Older popular update', 5, 1)], feedRequests: [] as string[], statsRequests: 0,
    voteRequests: 0, errors };
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    let body: unknown = [];
    if (path.endsWith('/public/stats') || path.endsWith('/public/visits')) {
      if (path.endsWith('/public/stats')) state.statsRequests++;
      if (state.statsFailure || (state.visitFailure && path.endsWith('/public/visits'))) {
        return route.fulfill({ status: 503, json: { detail: 'Statistics temporarily unavailable' } });
      }
      body = { daily_verified_reports: state.count, total_visitors: 12345, recorded: true };
    } else if (path.endsWith('/auth/test-token')) body = { id: 7, username: 'citizen',
      is_active: true, role: { name: 'Commuter' } };
    else if (path.endsWith('/feed')) {
      const tab = url.searchParams.get('tab')!;
      state.feedRequests.push(tab);
      const posts = tab === 'nearby' ? state.posts.filter(post => post.distance_meters! < 5000) : state.posts;
      body = { posts, total: posts.length, has_more: false };
    } else if (/\/feed\/\d+\/vote$/.test(path)) {
      state.voteRequests++;
      const selected = state.posts.find(post => post.id === Number(path.split('/').at(-2)))!;
      selected.upvotes++;
      selected.user_interaction = 'upvote';
      body = { post_id: selected.id, upvotes: selected.upvotes, downvotes: 0, user_interaction: 'upvote' };
    } else if (path.endsWith('/feed/leaderboard')) body = { reporters: [] };
    else if (path.endsWith('/feed/hotspots')) body = { hotspots: [], window_hours: 24, as_of: new Date().toISOString() };
    else if (path.endsWith('/news/local-updates')) body = { items: [], as_of: new Date().toISOString() };
    else if (path.endsWith('/notifications')) body = { notifications: [], unread_count: 0, total: 0, has_more: false };
    else if (path.includes('/weather')) body = { temp: 28, feels_like: 30, condition: 'Cloudy',
      icon: 'cloudy', location: 'Pasig' };
    return route.fulfill({ json: body });
  });
  return state;
}

async function emit(page: Page, event: string, snapshot = false) {
  await page.evaluate(({ event, snapshot }) => {
    (window as unknown as { emitTestUpdate: (event: string, snapshot: boolean) => void })
      .emitTestUpdate(event, snapshot);
  }, { event, snapshot });
}

test('homepage daily UTC label and count update on moderation SSE and flood sync', async ({ page }, testInfo) => {
  const state = await setup(page);
  await page.goto('/');
  const label = page.getByText('Floods Today (UTC)', { exact: true });
  const counter = label.locator('..');
  await expect(counter).toContainText('3');
  await expect(page.getByText('Site Visitors', { exact: true }).locator('..')).toContainText('12,345');
  await label.scrollIntoViewIfNeeded();
  const bounds = await counter.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await counter.locator('..').screenshot({ path: testInfo.outputPath('homepage-stats.png'), animations: 'disabled' });
  state.count = 2;
  await emit(page, 'zone_deactivated');
  await expect(counter).toContainText('2');
  state.count = 4;
  await emit(page, '', true);
  await expect(counter).toContainText('4');
  expect(state.errors).toEqual([]);
});

test('homepage polling refreshes count and failed visitor telemetry preserves stats', async ({ page }) => {
  const state = await setup(page);
  state.visitFailure = true;
  await page.goto('/');
  await expect(page.getByText('Visitor Count Unavailable', { exact: true }).first()).toBeVisible();
  const counter = page.getByText('Floods Today (UTC)', { exact: true }).locator('..');
  await expect(counter).toContainText('3');
  state.count = 1;
  await page.clock.fastForward(60_001);
  await expect(counter).toContainText('1');
  expect(state.errors).toEqual([]);
});

test('unavailable homepage statistics do not display a false zero', async ({ page }) => {
  const state = await setup(page);
  state.statsFailure = true;
  await page.goto('/');
  const counter = page.getByText('Floods Today (UTC)', { exact: true }).locator('..');
  await expect(counter).toContainText('—');
  await expect(page.getByText('Stats Error', { exact: true })).toBeVisible();
  expect(state.errors).toEqual([]);
});

for (const tab of ['recent', 'nearby']) {
  test(`${tab} preserves server chronology after votes, tab switches and SSE refresh`, async ({ page }) => {
    const state = await setup(page);
    await page.goto('/feed');
    const contents = page.locator('article p.whitespace-pre-wrap');
    await expect(contents).toHaveText(['Outside area newest', 'Latest nearby update', 'Older popular update']);
    if (tab === 'nearby') await page.getByRole('button', { name: 'Nearby', exact: true }).click();
    const expected = tab === 'nearby' ? ['Latest nearby update', 'Older popular update'] :
      ['Outside area newest', 'Latest nearby update', 'Older popular update'];
    await expect(contents).toHaveText(expected);
    await page.locator('article').filter({ hasText: 'Older popular update' })
      .getByRole('button', { name: 'Upvote', exact: true }).click();
    await expect.poll(() => state.voteRequests).toBe(1);
    await expect(contents).toHaveText(expected);
    await page.getByRole('button', { name: tab === 'nearby' ? 'Recent' : 'Nearby', exact: true }).click();
    await page.getByRole('button', { name: tab === 'nearby' ? 'Nearby' : 'Recent', exact: true }).click();
    await expect(contents).toHaveText(expected);
    state.posts.unshift({ ...state.posts[1], id: 4, content: 'Fresh eligible report', upvotes: 0,
      created_at: new Date().toISOString() });
    await emit(page, 'feed_post_created');
    await expect(contents).toHaveText(['Fresh eligible report', ...expected]);
    const requests = state.feedRequests.length;
    await page.clock.fastForward(60_001);
    await expect.poll(() => state.feedRequests.length).toBeGreaterThan(requests);
    await expect(contents).toHaveText(['Fresh eligible report', ...expected]);
    expect(state.errors).toEqual([]);
  });
}
