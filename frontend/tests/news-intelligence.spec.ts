import { expect as baseExpect, test, type Page } from "@playwright/test";

const expect = baseExpect.configure({ timeout: 30_000 });

test.setTimeout(90_000);
test.use({ browserName: "chromium" });

if (process.env.PLAYWRIGHT_CHROME_PATH) {
  test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });
}

// Mock the existing session/API boundary; never sign in to production for UI checks.
async function mockSession(page: Page, role = "Super Admin") {
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    let body: unknown = [];
    if (path.endsWith("/auth/test-token")) {
      body = { id: 987654, username: "news-ui-test", role: { name: role } };
    } else if (path.includes("/notifications")) {
      body = { notifications: [], total: 0, unread_count: 0, has_more: false };
    } else if (path.endsWith("/admin/zones")) {
      body = { items: [], total: 0, page: 1, limit: 10, pages: 0 };
    } else if (path.endsWith("/admin/news/results")) {
      body = { items: [], total: 0, page: 1, page_size: 12, pages: 1, publishers: [], scope: "latest_reported_locations", read_only: true };
    } else if (path.endsWith("/admin/news/collection")) {
      body = { items: [], total: 0, page: 1, page_size: 12, pages: 1, publishers: [], counts: { ready: 0, needs_checking: 0, no_locations: 0, waiting: 0, processing: 0, processing_failed: 0, retrieval_failed: 0, missing_text: 0 } };
    }
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
}

test("staff can inspect locations and collection status without fabricated news data", async ({ page }, testInfo) => {
  if (testInfo.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  await mockSession(page);
  const newsRequests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.includes("/api/v1/admin/news")) newsRequests.push(request.url());
  });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Flood Locations from News", exact: true })).toBeVisible();
  const navigation = page.getByRole("navigation", { name: "Admin navigation" });
  await expect(navigation.getByRole("link", { name: "News Intelligence" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByText(/No reported flood locations match these filters/)).toBeVisible();
  const collection = page.getByRole("button", { name: "Collection status", exact: true });
  await collection.focus();
  await page.keyboard.press("Enter");
  const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
  await expect(drawer.getByText("No saved articles match this collection state.", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(collection).toBeFocused();
  expect(newsRequests.length).toBeGreaterThan(0);
  expect(newsRequests.every((url) => /\/admin\/news\/(collection|results)$/.test(new URL(url).pathname))).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("news-foundation.png") });
  await page.getByRole("button", { name: "Spatial Operations", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/map$/);
  await navigation.getByRole("link", { name: "News Intelligence" }).click();
  await expect(page.getByRole("heading", { name: "Flood Locations from News", exact: true })).toBeVisible();
});

test("mobile menu shows labels and narrow layouts keep content within viewport", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium", "Mobile navigation and narrow-screen coverage.");
  await mockSession(page);
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Flood Locations from News", exact: true })).toBeVisible();
  for (const viewport of [{ width: 390, height: 844 }, { width: 320, height: 640 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(viewport);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.getByRole("button", { name: "Collection status", exact: true }).click();
    const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
    await expect(drawer).toBeVisible();
    const bounds = await drawer.boundingBox();
    expect(bounds!.width).toBeLessThanOrEqual(viewport.width);
    expect(bounds!.height).toBeLessThanOrEqual(viewport.height);
    await page.keyboard.press("Escape");
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open admin menu" }).click();
  await expect(page.getByRole("button", { name: "Close admin menu" })).toHaveAttribute("aria-expanded", "true");
  const navigation = page.getByRole("navigation", { name: "Admin navigation" });
  await expect(navigation.getByRole("link", { name: "News Intelligence" }).locator("span")).toHaveCSS("opacity", "1");
  await page.screenshot({ path: testInfo.outputPath("mobile-menu.png") });
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Open admin menu" })).toHaveAttribute("aria-expanded", "false");
  await page.getByRole("button", { name: "Open admin menu" }).click();
  await navigation.getByRole("link", { name: "News Intelligence" }).click();
  await expect(page.getByRole("button", { name: "Open admin menu" })).toHaveAttribute("aria-expanded", "false");
});

test("existing admin guard redirects a non-staff session", async ({ page }) => {
  await mockSession(page, "Citizen");
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\/(?:map)?$/);
  await expect(page.getByRole("heading", { name: "Flood Locations from News", exact: true })).toHaveCount(0);
});

test("source monitoring reads recorded feed dates and errors without triggering collection", async ({ page }) => {
  await mockSession(page);
  const methods: string[] = [];
  const feedReads: string[] = [];
  await page.route("**/api/v1/admin/news/sources", (route) => {
    methods.push(route.request().method());
    expect(route.request().headers().authorization).toBe("Bearer test-only-token");
    return route.fulfill({ contentType: "application/json", body: JSON.stringify([
      { id: "publisher-1", publisher: "Example News", article_domains: ["example.org"], feed_urls: ["https://example.org/rss"], enabled: true, verified_at: "2026-10-01" },
      { id: "publisher-2", publisher: "Disabled News", article_domains: [], feed_urls: [], enabled: false, verified_at: null },
    ]) });
  });
  await page.route("**/api/v1/admin/news/feeds", (route) => {
    methods.push(route.request().method());
    feedReads.push(route.request().url());
    return route.fulfill({ contentType: "application/json", body: JSON.stringify([
      { source_id: "publisher-1", feed_url: "https://example.org/rss", last_checked_at: "2026-10-02T12:00:00Z", last_success_at: "2026-10-01T12:00:00Z", last_error: "Feed HTTP 403" },
      { source_id: "unlisted-source", feed_url: "javascript:alert(1)", last_checked_at: null, last_success_at: null, last_error: null },
    ]) });
  });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  const opener = page.getByRole("button", { name: "Sources & feeds", exact: true });
  await opener.click();
  const drawer = page.getByRole("dialog", { name: "Sources & feeds", exact: true });
  await expect(drawer.getByRole("heading", { name: "Example News", exact: true })).toBeVisible();
  await expect(drawer.getByText("Disabled", { exact: true })).toBeVisible();
  expect(feedReads).toEqual([]);
  await drawer.getByRole("button", { name: "Feed checks", exact: true }).click();
  await expect(drawer.getByText("Feed HTTP 403", { exact: true })).toBeVisible();
  await expect(drawer.getByText("Oct 1, 2026, 8:00 PM", { exact: true })).toBeVisible();
  await expect(drawer.getByText("Not recorded", { exact: true }).first()).toBeVisible();
  await drawer.locator("summary").filter({ hasText: "Feed details" }).first().click();
  await expect(drawer.getByRole("link", { name: "https://example.org/rss" })).toHaveAttribute("rel", "noopener noreferrer");
  await drawer.locator("summary").filter({ hasText: "Feed details" }).last().click();
  await expect(drawer.getByRole("link", { name: "javascript:alert(1)" })).toHaveCount(0);
  await drawer.getByRole("button", { name: "Refresh saved status", exact: true }).click();
  await expect.poll(() => feedReads.length).toBe(2);
  for (const viewport of [{ width: 320, height: 640 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(viewport);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const bounds = await drawer.boundingBox();
    expect(bounds!.width).toBeLessThanOrEqual(viewport.width);
    expect(bounds!.height).toBeLessThanOrEqual(viewport.height);
    await expect(drawer.getByRole("button", { name: "Close sources and feeds" })).toBeVisible();
  }
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
  expect(methods.every((method) => method === "GET")).toBe(true);
});

test("source monitoring surfaces read failures and explicit empty states", async ({ page }) => {
  await mockSession(page);
  let failSources = true, failFeeds = true;
  await page.route("**/api/v1/admin/news/sources", (route) => route.fulfill({ status: failSources ? 503 : 200, contentType: "application/json", body: JSON.stringify(failSources ? { detail: "Source catalogue unavailable" } : []) }));
  await page.route("**/api/v1/admin/news/feeds", (route) => route.fulfill({ status: failFeeds ? 503 : 200, contentType: "application/json", body: JSON.stringify(failFeeds ? { detail: "Feed storage unavailable" } : []) }));
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Sources & feeds", exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Sources & feeds", exact: true });
  await expect(drawer.getByRole("alert")).toContainText("Source catalogue unavailable");
  failSources = false;
  await drawer.getByRole("button", { name: "Retry publishers", exact: true }).click();
  await expect(drawer.getByText("No publishers are configured.", { exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Feed checks", exact: true }).click();
  await expect(drawer.getByRole("alert")).toContainText("Feed storage unavailable");
  failFeeds = false;
  await drawer.getByRole("button", { name: "Retry feed checks", exact: true }).click();
  await expect(drawer.getByText("No feed checkpoints recorded. Feed health is not established.", { exact: true })).toBeVisible();
});
