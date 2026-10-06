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
      body = { items: [], total: 0, page: 1, page_size: 12, pages: 1, publishers: [], counts: { ready: 0, needs_checking: 0, excluded: 0, no_locations: 0, waiting: 0, processing: 0, processing_failed: 0, retrieval_failed: 0, missing_text: 0 } };
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

test("excluded project history stays outside attention and is accessible on desktop and mobile", async ({ page }, testInfo) => {
  await mockSession(page);
  const title = "Previously saved Taguig flood-control investigation";
  const states: string[] = [];
  await page.route("**/api/v1/admin/news/collection?**", (route) => {
    const state = new URL(route.request().url()).searchParams.get("status") ?? "attention";
    states.push(state);
    const items = state === "excluded" ? [{ id: 23, title, publisher: "Example News",
      published_at: "2026-09-30T04:04:00Z", article_error: null, collection_status: "excluded",
      collection_label: "Excluded from flood reports", collection_reason: "No verified Metro Manila flood observation is available. Kept for history.",
      location_count: 0, questionable_count: 0 }] : [];
    return route.fulfill({ contentType: "application/json", body: JSON.stringify({ items, total: items.length,
      page: 1, pages: 1, page_size: 12, publishers: [], counts: { ready: 0, needs_checking: 0, excluded: 1,
      no_locations: 0, waiting: 0, processing: 0, processing_failed: 0, retrieval_failed: 0, missing_text: 0 } }) });
  });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Collection status", exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
  await expect(drawer.getByText("No saved articles match this collection state.", { exact: true })).toBeVisible();
  await expect(drawer.getByRole("heading", { name: title })).toHaveCount(0);
  await drawer.getByLabel("Collection state").click();
  await page.getByRole("button", { name: "Excluded from flood reports", exact: true }).click();
  await expect(drawer.getByRole("heading", { name: title })).toBeVisible();
  await expect(drawer.getByText("No verified Metro Manila flood observation is available. Kept for history.")).toBeVisible();
  expect(states).toContain("attention");
  expect(states).toContain("excluded");
  if (testInfo.project.name === "mobile-chromium") await page.setViewportSize({ width: 320, height: 640 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("excluded-history.png") });
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
    // Chromium can return 320.000009 CSS pixels for a 320px transformed
    // dialog. Keep the separate document-overflow assertion above strict.
    expect(bounds!.width).toBeLessThanOrEqual(viewport.width + 0.01);
    expect(bounds!.height).toBeLessThanOrEqual(viewport.height + 0.01);
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

test("pipeline history is lazy, paginated, safe to inspect and GET-only", async ({ page }) => {
  await mockSession(page);
  const methods: string[] = [];
  const historyReads: string[] = [];
  await page.route("**/api/v1/admin/news/monitoring", (route) => route.fulfill({ contentType: "application/json", body: JSON.stringify({ articles_total: 1, body_counts: { available: 0, missing: 0, error: 1 }, latest_processing_counts: { not_recorded: 1, pending: 0, processing: 0, completed: 0, retry_wait: 0, failed: 0 }, recent_retrieval_issues: [], issue_limit: 10, discovery_history: "recorded", fallback_history: "recorded", collection_to_alert_delay: "unavailable", read_only: true }) }));
  await page.route("**/api/v1/admin/news/monitoring/*?*", (route) => {
    methods.push(route.request().method());
    historyReads.push(route.request().url());
    const url = new URL(route.request().url());
    const discovery = url.pathname.endsWith("discovery");
    const current = Number(url.searchParams.get("page"));
    return route.fulfill({ contentType: "application/json", body: JSON.stringify({ read_only: true, total: discovery ? 6 : 1, page: current, page_size: 5, pages: discovery ? 2 : 1, items: [{ id: current, status: discovery ? "failed" : "completed", started_at: "2026-10-02T12:00:00Z", finished_at: "2026-10-02T12:01:00Z", error_code: discovery ? "feed_partial_failure" : null, trigger: "collector", article_id: 1, retrieve_articles: true, retry_after_seconds: null, feeds: discovery ? [{ source_id: "Example", feed_url: "https://example.org/rss", status: "http_error", checked_at: "2026-10-02T12:00:00Z", error_code: "feed_probe_failed", entries_seen: 0, candidates_saved: 0, body_errors: 0, scope_unresolved: 0 }] : [], leads: discovery ? [] : [{ ordinal: 0, article_url: "javascript:alert(1)", source_id: null, retrieved_at: null, retrieval_status: "not_requested", error_code: null, assessment: "unverified_index_lead" }] }] }) });
  });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  const opener = page.getByRole("button", { name: "Sources & feeds", exact: true });
  await opener.click();
  expect(historyReads).toEqual([]);
  const drawer = page.getByRole("dialog", { name: "Sources & feeds", exact: true });
  await drawer.getByRole("button", { name: "Pipeline", exact: true }).click();
  const discovery = drawer.getByRole("region", { name: "Discovery history", exact: true });
  const fallback = drawer.getByRole("region", { name: "Fallback history", exact: true });
  await expect(discovery.getByText("Recorded issue: feed partial failure", { exact: true })).toBeVisible();
  await discovery.locator("summary").click();
  await expect(discovery.getByText("Entries seen: 0 · Candidates saved: 0", { exact: true })).toBeVisible();
  await discovery.getByRole("button", { name: /^Next(?: Page)?$/ }).click();
  await expect.poll(() => historyReads.some((url) => url.includes("discovery?page=2"))).toBe(true);
  await fallback.locator("summary").click();
  await expect(fallback.getByRole("link", { name: "javascript:alert(1)" })).toHaveCount(0);
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }, { width: 320, height: 640 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(viewport);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await expect(drawer.getByRole("button", { name: "Close sources and feeds" })).toBeVisible();
  }
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
  expect(methods.every((method) => method === "GET")).toBe(true);
});

test("history storage failure remains an error until retry succeeds", async ({ page }) => {
  await mockSession(page);
  let fail = true;
  await page.route("**/api/v1/admin/news/monitoring", (route) => route.fulfill({ contentType: "application/json", body: JSON.stringify({ articles_total: 0, body_counts: { available: 0, missing: 0, error: 0 }, latest_processing_counts: {}, recent_retrieval_issues: [], issue_limit: 10, discovery_history: "recorded", fallback_history: "recorded", collection_to_alert_delay: "unavailable" }) }));
  await page.route("**/api/v1/admin/news/monitoring/*?*", (route) => route.fulfill({ status: fail ? 503 : 200, contentType: "application/json", body: JSON.stringify(fail ? { detail: "News telemetry storage is unavailable" } : { items: [], total: 0, page: 1, page_size: 5, pages: 1, read_only: true }) }));
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Sources & feeds", exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Sources & feeds", exact: true });
  await drawer.getByRole("button", { name: "Pipeline", exact: true }).click();
  const history = drawer.getByRole("region", { name: "Discovery history", exact: true });
  await expect(history.getByRole("alert")).toContainText("News telemetry storage is unavailable");
  await expect(history.getByText("No discovery history recorded yet.", { exact: true })).toHaveCount(0);
  fail = false;
  await history.getByRole("button", { name: "Refresh discovery history", exact: true }).click();
  await expect(history.getByText("No discovery history recorded yet.", { exact: true })).toBeVisible();
});
