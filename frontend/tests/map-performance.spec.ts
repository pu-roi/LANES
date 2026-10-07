import { expect, test, type Page } from "@playwright/test";

test.setTimeout(90_000);
test.use({ browserName: 'chromium' });

async function setup(page: Page) {
  let zoneReads = 0;
  await page.addInitScript(() => {
    class FakeEventSource extends EventTarget {
      onopen: (() => void) | null = null;
      onerror: (() => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      constructor(public url: string) {
        super();
        if (url.endsWith('/sync/stream')) {
          (window as unknown as { emitFloodSnapshot: (event: string, data: string) => void }).emitFloodSnapshot =
            (event, data) => this.dispatchEvent(new MessageEvent(event, { data }));
          setTimeout(() => this.dispatchEvent(new MessageEvent('init', { data: '[]' })), 0);
        }
      }
      close() {}
    }
    window.EventSource = FakeEventSource as unknown as typeof EventSource;
  });
  await page.route('**/api.maptiler.com/maps/**/style.json?**', route => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#f1f5f9' } }],
  } }));
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/reports/active-zones')) { zoneReads++; return route.fulfill({ json: [] }); }
    if (path.endsWith('/feed/leaderboard')) return route.fulfill({ json: { reporters: [] } });
    if (path.endsWith('/feed')) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    if (path.endsWith('/news/alerts')) return route.fulfill({ json: { items: [], total: 0, pages: 0, page: 1, page_size: 10, as_of: new Date().toISOString() } });
    return route.fulfill({ json: [] });
  });
  return { reads: () => zoneReads };
}

async function emit(page: Page, event: string, data: string) {
  await page.evaluate(({ event, data }) => {
    (window as unknown as { emitFloodSnapshot: (event: string, data: string) => void }).emitFloodSnapshot(event, data);
  }, { event, data });
}

test('initial Feed defers the map until map navigation', async ({ page }) => {
  const control = await setup(page);
  await page.goto('/feed');
  await expect(page.getByRole('link', { name: 'Map', exact: true }).first()).toBeVisible();
  expect(await page.locator('.maplibregl-canvas').count()).toBe(0);
  expect(control.reads()).toBe(0);
  await page.getByRole('link', { name: 'Map', exact: true }).first().click();
  await expect(page.locator('.maplibregl-canvas')).toBeVisible();
  await expect.poll(control.reads).toBeGreaterThan(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('offline engine waits for map rendering and browser idle time', async ({ page }) => {
  await setup(page);
  let wrapperReads = 0;
  await page.route('**/valhalla.js', route => {
    wrapperReads++;
    return route.fulfill({ contentType: 'application/javascript', body: 'self.ValhallaModule = async () => ({});' });
  });
  await page.addInitScript(() => {
    const idleCallbacks: IdleRequestCallback[] = [];
    const target = window as unknown as { runOfflineIdle: () => void; offlineIdleCount: number };
    target.offlineIdleCount = 0;
    window.requestIdleCallback = (callback) => {
      idleCallbacks.push(callback);
      target.offlineIdleCount++;
      return idleCallbacks.length;
    };
    window.cancelIdleCallback = () => {};
    target.runOfflineIdle = () => {
      for (const callback of idleCallbacks.splice(0)) callback({ didTimeout: false, timeRemaining: () => 50 });
    };
  });
  await page.goto('/feed');
  await expect(page.getByRole('link', { name: 'Map', exact: true }).first()).toBeVisible();
  expect(wrapperReads).toBe(0);
  await page.getByRole('link', { name: 'Map', exact: true }).first().click();
  await expect(page.locator('.maplibregl-canvas')).toBeVisible();
  await expect.poll(() => page.evaluate(() => (window as unknown as { offlineIdleCount: number }).offlineIdleCount)).toBeGreaterThan(0);
  expect(wrapperReads).toBe(0);
  await page.evaluate(() => (window as unknown as { runOfflineIdle: () => void }).runOfflineIdle());
  await expect.poll(() => wrapperReads).toBe(1);
});

test('unchanged live snapshots avoid refetches, changes and reconnects refresh, polling recovers', async ({ page }) => {
  await page.clock.install();
  const control = await setup(page);
  await page.goto('/map');
  await expect(page.locator('.maplibregl-canvas')).toBeVisible();
  await expect.poll(control.reads).toBeGreaterThan(0);
  const initialReads = control.reads();
  await emit(page, 'update', '[]');
  await page.waitForTimeout(250);
  expect(control.reads()).toBe(initialReads);
  await emit(page, 'update', '[{"id":1}]');
  await expect.poll(control.reads).toBe(initialReads + 1);
  await emit(page, 'update', '[{"id":1}]');
  await page.waitForTimeout(250);
  expect(control.reads()).toBe(initialReads + 1);
  await emit(page, 'init', '[{"id":2}]');
  await expect.poll(control.reads).toBe(initialReads + 2);
  await page.clock.fastForward(60_000);
  await expect.poll(control.reads).toBe(initialReads + 3);
});
