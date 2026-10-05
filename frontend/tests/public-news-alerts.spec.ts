import { expect, test, type Page, type TestInfo } from "@playwright/test";
import type { PublicNewsAlert } from "../src/features/news/publicNewsApi";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } });

const active: PublicNewsAlert = {
  case_id: 71, decision_id: 81, revision: 1, status: "Active", location_label: "C5, Ugong, Pasig",
  location_qualifier: "Reported road; exact affected section unverified", depth_label: "Approximately knee-deep",
  condition_label: "Flooding reported", passability_label: "Not established for all vehicles",
  observed_at: "2026-10-05T01:00:00Z", expires_at: "2026-10-05T03:00:00Z", cleared_at: null,
  updated_at: "2026-10-05T01:05:00Z", source_title: "Flood report along C5", source_publisher: "Example News",
  source_url: "https://example.org/flood", source_published_at: "2026-10-05T01:04:00Z", correction_note: null,
  evidence_excerpt: "Approximately knee-deep water was reported along C5.", geometry_precision: "text_only",
  display_geojson: null, current_status_unknown: false, affects_routing: false,
};

async function setup(page: Page) {
  const control = { failure: false, empty: false, refreshGate: null as Promise<void> | null, item: { ...active }, requests: [] as number[], writes: [] as string[] };
  const hydrationErrors: string[] = [];
  page.on("pageerror", (error) => { if (/hydration|didn.t match/i.test(error.message)) hydrationErrors.push(error.message); });
  page.on("close", () => expect(hydrationErrors).toEqual([]));
  await page.addInitScript(() => {
    class MockEventSource extends EventTarget {
      onopen: (() => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onerror: (() => void) | null = null;
      listener: EventListener;
      constructor(url: string) {
        super();
        this.listener = ((event: CustomEvent) => {
          if (url.includes("/sse/stream")) this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(event.detail) }));
        }) as EventListener;
        window.addEventListener("fixture-news-sse", this.listener);
        queueMicrotask(() => this.onopen?.());
      }
      close() { window.removeEventListener("fixture-news-sse", this.listener); }
    }
    Object.defineProperty(window, "EventSource", { value: MockEventSource });
  });
  await page.route("**/api.maptiler.com/maps/**/style.json?**", (route) => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }],
  } }));
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request(), url = new URL(request.url());
    if (request.method() !== "GET") control.writes.push(url.pathname);
    if (url.pathname.endsWith("/news/alerts")) {
      const pageNumber = Number(url.searchParams.get("page"));
      control.requests.push(pageNumber);
      if (control.refreshGate) await control.refreshGate;
      if (control.failure) return route.fulfill({ status: 503, json: { detail: "News projection temporarily unavailable" } });
      return route.fulfill({ json: { items: control.empty ? [] : [{ ...control.item, case_id: pageNumber === 1 ? 71 : 72,
        location_label: pageNumber === 1 ? control.item.location_label : "Ortigas Avenue, Pasig" }],
        total: control.empty ? 0 : 11, page: pageNumber, page_size: 10, pages: control.empty ? 0 : 2,
        as_of: "2026-10-05T01:05:00Z" } });
    }
    if (url.pathname.endsWith("/feed/leaderboard")) return route.fulfill({ json: { reporters: [] } });
    if (url.pathname.endsWith("/feed")) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/map");
  return control;
}

async function openAlerts(page: Page, info: TestInfo) {
  if (info.project.name === "mobile-chromium") await page.getByRole("button", { name: "Report Flood Hazard" }).click();
  await page.getByRole("button", { name: "News alerts", exact: true }).click();
  await expect(page.getByRole("heading", { name: "News alerts", exact: true })).toBeVisible();
}

test("shows source-qualified text alerts, preserves route inputs, and paginates on the server", async ({ page }, info) => {
  const control = await setup(page);
  if (info.project.name === "mobile-chromium") await page.getByText("Expand", { exact: true }).click();
  const routeInput = page.getByPlaceholder("Choose destination").first();
  await expect(routeInput).toBeVisible();
  await routeInput.fill("My saved route destination");
  await routeInput.press("Tab");
  await openAlerts(page, info);
  if (info.project.name === "mobile-chromium") {
    await expect(page.getByRole("button", { name: "Close news alerts" })).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(page.getByRole("button", { name: "Next", exact: true })).toBeFocused();
  }
  await expect(page.getByText("News status: Active", { exact: true })).toBeVisible();
  await expect(page.getByText("Approximately knee-deep", { exact: true })).toBeVisible();
  await expect(page.getByText("Not established for all vehicles", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /Flood report along C5/ })).toHaveAttribute("href", "https://example.org/flood");
  await expect(page.getByText(/do not change route avoidance zones/)).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Ortigas Avenue, Pasig" })).toBeVisible();
  expect(control.requests).toContain(2);
  await page.screenshot({ path: info.outputPath("public-news-alerts.png") });
  if (info.project.name === "mobile-chromium") {
    const bounds = await page.getByRole("dialog", { name: "News alerts" }).boundingBox();
    const viewport = page.viewportSize()!;
    expect(bounds!.x).toBeGreaterThanOrEqual(0);
    expect(bounds!.width).toBeLessThanOrEqual(viewport.width);
    expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(viewport.height - 64);
  }
  control.empty = true;
  await page.getByRole("button", { name: "Refresh news alerts" }).click();
  await expect(page.getByText("No published news alerts in this snapshot.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Previous", exact: true }).click();
  await expect.poll(() => control.requests.at(-1)).toBe(1);
  await expect(page.getByRole("button", { name: "Refresh news alerts" })).toBeEnabled();
  await page.getByRole("button", { name: "Close news alerts" }).click();
  await expect(routeInput).toHaveValue("My saved route destination");
  await page.locator('a[href="/feed"]:visible').first().click();
  await expect(page).toHaveURL(/\/feed$/, { timeout: 30_000 });
  await page.locator('a[href="/map"]:visible').first().click();
  await expect(page).toHaveURL(/\/map$/, { timeout: 30_000 });
  await expect(routeInput).toHaveValue("My saved route destination");
  expect(control.writes).toEqual([]);
});

test("refreshes expiry and corrections from SSE without creating avoidance geometry", async ({ page }, info) => {
  const control = await setup(page);
  await openAlerts(page, info);
  await expect(page.getByText("News status: Active", { exact: true })).toBeVisible();
  control.item = { ...active, status: "Unconfirmed", current_status_unknown: true };
  await page.evaluate(() => window.dispatchEvent(new CustomEvent("fixture-news-sse", { detail: { event: "news_status_changed" } })));
  await expect(page.getByText("News status: Unconfirmed", { exact: true })).toBeVisible();
  await expect(page.getByText("Current flooding is unconfirmed.", { exact: true })).toBeVisible();
  control.item = { ...active, status: "Cleared", revision: 2, cleared_at: "2026-10-05T03:10:00Z",
    correction_note: "Matched later observation reports subsidence.", source_url: "javascript:alert('unsafe')" };
  await page.getByRole("button", { name: "Refresh news alerts" }).click();
  await expect(page.getByText("News status: Cleared", { exact: true })).toBeVisible();
  await expect(page.getByText(/Matched later observation reports subsidence/)).toBeVisible();
  await expect(page.getByRole("link", { name: /Flood report along C5/ })).toHaveCount(0);
  await expect(page.getByText(/Clearance observation:/)).toBeVisible();
  expect(control.writes).toEqual([]);
});

test("makes offline and refresh failures explicit and never presents cached Active as current", async ({ page, context }, info) => {
  const control = await setup(page);
  await openAlerts(page, info);
  await expect(page.getByText("News status: Active", { exact: true })).toBeVisible();
  let completeRefresh: (() => void) | undefined;
  control.refreshGate = new Promise<void>((resolve) => { completeRefresh = resolve; });
  await page.getByRole("button", { name: "Refresh news alerts" }).click();
  await expect(page.getByText("Last downloaded: Active", { exact: true })).toBeVisible();
  await expect(page.getByText(/Refreshing server status/)).toBeVisible();
  completeRefresh?.();
  control.refreshGate = null;
  await expect(page.getByText("News status: Active", { exact: true })).toBeVisible();
  control.failure = true;
  await page.getByRole("button", { name: "Refresh news alerts" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Could not refresh news alerts" })).toBeVisible();
  await expect(page.getByText("Last downloaded: Active", { exact: true })).toBeVisible();
  await expect(page.getByText("News status: Active", { exact: true })).toHaveCount(0);
  control.failure = false;
  await page.getByRole("button", { name: "Retry news alerts" }).click();
  await expect(page.getByText("News status: Active", { exact: true })).toBeVisible();
  await context.setOffline(true);
  await expect(page.getByText(/Offline\. Current status unavailable/)).toBeVisible();
  await expect(page.getByText("Last downloaded: Active", { exact: true })).toBeVisible();
  await context.setOffline(false);
  await expect(page.getByText("News status: Active", { exact: true })).toBeVisible();
});

test("polls server status at a bounded interval and handles empty projections", async ({ page }, info) => {
  await page.clock.install();
  const control = await setup(page);
  await openAlerts(page, info);
  await expect(page.getByText("News status: Active", { exact: true })).toBeVisible();
  control.empty = true;
  await page.clock.fastForward(31_000);
  await expect(page.getByText("No published news alerts in this snapshot.", { exact: true })).toBeVisible();
  expect(control.requests.length).toBeGreaterThanOrEqual(2);
});
