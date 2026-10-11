import { expect as baseExpect, test, type Page } from "@playwright/test";
import type { NewsAutomationStatus } from "../src/features/news/newsApi";

test.setTimeout(90_000);
const expect = baseExpect.configure({ timeout: 30_000 });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });

function status(): NewsAutomationStatus {
  return { read_only: true, checked_at: "2026-10-11T13:00:00Z", state: "running", status_label: "Gathering news",
    running: true, current_stage: "collection", stage_label: "Gathering news", stage_started_at: "2026-10-11T13:00:00Z",
    collection_enabled: true, processing_enabled: true, publication_enabled: true, enabled_sources: 7,
    collection_interval_minutes: 30, scheduler_tick_target_minutes: 15, next_collection_due_at: "2026-10-11T13:30:00Z",
    collection_overdue: false, last_started_at: "2026-10-11T13:00:00Z", last_finished_at: null,
    last_successful_at: null, last_progress_at: "2026-10-11T13:00:00Z", latest_collection_at: "2026-10-11T13:00:00Z", last_cycle: null,
    feed_counts: { entries_read: 135, eligible_candidates: 0, articles_saved_or_seen: 1, feed_errors: 0, body_errors: 0, scope_unresolved: 0 },
    stages: {}, queue_counts: { pending: 0, processing: 0, retry_wait: 0, failed: 0 }, error_code: null };
}

async function setup(page: Page, readStatus: () => object, readResults: () => object = () => ({ items: [], total: 0 })) {
  await page.addInitScript(() => localStorage.setItem("lanes_token", "fixture-news-status"));
  await page.route("**/news-simulation.local.json", route => route.fulfill({ status: 404, json: {} }));
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let body: object = [];
    if (path.endsWith("/auth/test-token")) body = { id: 1, is_active: true, username: "Fixture admin", role: { name: "Super Admin" } };
    if (path.endsWith("/admin/news/automation")) body = readStatus();
    if (path.endsWith("/admin/news/results")) body = { page: 1, pages: 1, page_size: 12, publishers: [], scope: "latest_reported_locations", ...readResults() };
    if (path.includes("/notifications")) body = { notifications: [], total: 0, unread_count: 0, has_more: false };
    await route.fulfill({ json: body });
  });
}

test("polling reflects real stages and refreshes flood cards when the cycle finishes", async ({ page }, info) => {
  let state = status();
  let reads = 0;
  const methods: string[] = [];
  page.on("request", request => { if (request.url().includes("/admin/news/")) methods.push(request.method()); });
  await setup(page, () => { reads++; return state; }, () => ({ items: state.running ? [] : [{ key: "1:0", run_id: 1, claim_index: 0,
    publisher: "Daily Tribune", published_at: "2026-10-11T12:50:00Z", summary: { location: "Boni Avenue",
      area: "Mandaluyong", water_level: "10-inch", flood_time_label: "Flood observed in article", flood_time: "2026-10-11T12:34:00Z", condition: "Flooding reported" } }], total: state.running ? 0 : 1 }));
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("status").filter({ hasText: "Gathering news" })).toBeVisible();
  const initialReads = reads;
  state = { ...state, status_label: "Processing articles", current_stage: "extraction" };
  await expect(page.getByRole("status").filter({ hasText: "Processing articles" })).toBeVisible({ timeout: 25_000 });
  expect(reads).toBeGreaterThan(initialReads);
  state = { ...state, running: false, state: "idle", status_label: "Idle; last cycle finished", current_stage: null,
    last_finished_at: "2026-10-11T13:01:00Z",
    last_cycle: { started_at: "2026-10-11T13:00:00Z", finished_at: "2026-10-11T13:01:00Z", outcome: "completed",
      counts: { extraction: { completed: 1 }, footprints: { total_activated: 1 } }, error_code: null } };
  await expect(page.getByRole("heading", { name: "Boni Avenue", exact: true })).toBeVisible({ timeout: 25_000 });
  expect(methods.every(method => method === "GET")).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("automation-completed.png"), fullPage: true });
});

test("overdue collection and partial retrieval remain visible on narrow and wide screens", async ({ page }, info) => {
  await setup(page, () => ({ ...status(), running: false, state: "overdue", status_label: "Collection overdue", collection_overdue: true,
    feed_counts: { ...status().feed_counts, body_errors: 2, scope_unresolved: 2 } }));
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("status").filter({ hasText: "Collection overdue" })).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "deployed scheduler" })).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "article retrieval" })).toBeVisible();
  for (const width of info.project.name === "mobile-chromium" ? [390, 320] : [1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.screenshot({ path: info.outputPath("automation-overdue.png"), fullPage: true });
});

test("status failure is shown and refresh can recover without collecting", async ({ page }) => {
  await setup(page, status);
  let fail = true;
  await page.route("**/api/v1/admin/news/automation", route => route.fulfill({ status: fail ? 503 : 200,
    json: fail ? { detail: "News automation status is unavailable" } : { ...status(), running: false, status_label: "Idle; last cycle finished" } }));
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("alert").filter({ hasText: "News automation status is unavailable" })).toBeVisible();
  fail = false;
  await page.getByRole("button", { name: "Refresh automation status" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Idle; last cycle finished" })).toBeVisible();
});

test("adaptive weather sources, timestamps, coverage and dispatch failures are visible", async ({ page }, info) => {
  const state = { ...status(), running: false, weather: {
    mode: "adaptive", catalog_version: "ncr-upstream-v1", coverage_label: "Sampled Metro Manila and upstream coverage; not street-level rain detection",
    points: [{ locality: "Antipolo", latitude: 14.66, longitude: 121.23, role: "upstream", relevance: "Watershed rain context" }],
    effective_interval_minutes: 15, reason: "Relevant weather risk", last_positive_at: "2026-10-11T13:00:00Z",
    controller_heartbeat_at: "2026-10-11T13:00:00Z", controller_stale: false,
    dispatch_state: "unknown", dispatch_error: "news_dispatch_unavailable", last_dispatch_at: null,
    last_tick_duration_ms: 250, checks: 3, provider_failures: 1, worker_starts: 1,
    providers: [{ name: "PAGASA", source_url: "https://www.pagasa.dost.gov.ph/regional-forecast/ncrprsd", checked_at: "2026-10-11T13:00:00Z",
      status: "risk", risk_locations: ["Metro Manila", "Rizal upstream"], error_code: "advisory_timestamp_missing",
      bulletins: [{ identity: "Rainfall Advisory No. 6", issued_at: "2026-10-11T12:00:00Z", valid_until: "2026-10-11T15:00:00Z", relevant: true, locations: ["Metro Manila"] }] },
      { name: "Open-Meteo", source_url: "https://api.open-meteo.com/v1/forecast", checked_at: "2026-10-11T13:00:00Z", status: "risk", risk_locations: ["Antipolo"], error_code: null, bulletins: [] }],
  } };
  const methods: string[] = [];
  page.on("request", request => { if (request.url().includes("/admin/news/")) methods.push(request.method()); });
  await setup(page, () => state);
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  const panel = page.getByRole("region", { name: "Weather-based scheduling" });
  await expect(panel.getByText("15-minute automatic interval")).toBeVisible();
  await expect(panel.getByRole("link", { name: "PAGASA", exact: true })).toHaveAttribute("href", "https://www.pagasa.dost.gov.ph/regional-forecast/ncrprsd");
  await expect(panel.getByText(/Rainfall Advisory No. 6.*Issued.*Valid until/)).toBeVisible();
  await expect(panel.getByRole("alert").filter({ hasText: "news_dispatch_unavailable" })).toBeVisible();
  await panel.getByText("Monitored locations and controller diagnostics").click();
  await expect(panel.getByText("Antipolo (upstream)", { exact: true })).toBeVisible();
  for (const width of info.project.name === "mobile-chromium" ? [390, 320] : [1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  expect(methods.every(method => method === "GET")).toBe(true);
  await page.screenshot({ path: info.outputPath("weather-scheduling.png"), fullPage: true });
});
