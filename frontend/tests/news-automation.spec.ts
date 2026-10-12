import { expect as baseExpect, test, type Page } from "@playwright/test";
import type { NewsAutomationStatus } from "../src/features/news/newsApi";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
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

test("audit cooldown diagnostics preserve unknown quota and fit desktop/mobile", async ({ page }, info) => {
  const state = status();
  state.running = false;
  state.status_label = "Last cycle needs attention";
  state.audit = { state: "cooldown", checked_at: "2026-10-11T13:00:00Z", next_check_at: "2026-10-11T13:30:00Z",
    used: 52, limit: 50, remaining: 0, request_count: 4, claims_dispatched: 26, http_status: 429,
    error_code: "auditor_daily_quota_exhausted" };
  const methods: string[] = [];
  page.on("request", r => { if (r.url().includes("/admin/news/")) methods.push(r.method()); });
  await setup(page, () => state);
  await page.goto("/admin/news");
  await page.getByText("Run details and diagnostics", { exact: true }).click();
  const diagnostics = page.getByTestId("news-audit-diagnostics");
  await expect(diagnostics).toBeVisible();
  await expect(diagnostics).toContainText("auditor_daily_quota_exhausted");
  await expect(diagnostics).toContainText("26");
  await expect(diagnostics).toContainText("429");
  const bounds = await diagnostics.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x+bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.screenshot({ path: `test-results/news-audit-quota-${info.project.name}.png`, fullPage: true });
  state.audit.remaining = null;
  state.audit.used = null;
  state.audit.limit = null;
  await page.getByRole("button", { name: "Refresh automation status" }).click();
  await expect(diagnostics).toContainText("Not recorded");
  expect(methods.every(m => m === "GET")).toBeTruthy();
});

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

test("Gemini configuration cooldown shows unknown allowance on desktop/mobile", async ({ page }, info) => {
  const state = status();
  state.audit = { state: "model_cooldown", checked_at: "2026-10-13T03:00:00Z", next_check_at: null,
    used: null, limit: null, remaining: null, request_count: 1, claims_dispatched: 8,
    http_status: 400, error_code: "auditor_http_error", model_next_check_at: "2026-10-13T04:00:00Z",
    actual_model: "gemini-3.8-flash" };
  const methods: string[] = [];
  page.on("request", request => { if (request.url().includes("/admin/news/")) methods.push(request.method()); });
  await setup(page, () => state);
  await page.goto("/admin/news");
  await page.getByText("Run details and diagnostics", { exact: true }).click();
  const diagnostics = page.getByTestId("news-audit-diagnostics");
  await expect(diagnostics).toContainText("gemini-3.8-flash");
  await expect(diagnostics).toContainText("auditor_http_error");
  await expect(diagnostics).toContainText("400");
  await expect(diagnostics).toContainText("Not recorded");
  await expect(diagnostics).toContainText("Model recovery check");
  const bounds = await diagnostics.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  expect(methods.every(method => method === "GET")).toBeTruthy();
  await page.screenshot({ path: `test-results/news-gemini-cooldown-${info.project.name}.png`, fullPage: true });
});


test("model recovery phase and reviewed coverage remain visible on desktop/mobile", async ({ page }, info) => {
  const state = status();
  state.audit = { state: "model_cooldown", checked_at: "2026-10-11T13:00:00Z", next_check_at: null,
    used: 20, limit: 50, remaining: 30, request_count: 2, claims_dispatched: 16, http_status: 200,
    error_code: "auditor_timeout", model_next_check_at: "2026-10-11T13:15:00Z", failure_phase: "body",
    timeout_kind: "overall", elapsed_ms: 60000, actual_model: "fixture/model:free",
    boundary_expected: 1710, boundary_qualified: 1524, boundary_missing: 186 };
  const methods: string[] = [];
  page.on("request", request => { if (request.url().includes("/admin/news/")) methods.push(request.method()); });
  await setup(page, () => state);
  await page.goto("/admin/news");
  await page.getByText("Run details and diagnostics", { exact: true }).click();
  const diagnostics = page.getByTestId("news-audit-diagnostics");
  await expect(diagnostics).toContainText("body · overall timeout · 60.0 seconds");
  await expect(diagnostics).toContainText("Model recovery check");
  await expect(diagnostics).toContainText("1524 of 1710");
  await expect(diagnostics).toContainText("186 still need reviewed coverage");
  await expect(diagnostics).toContainText("fixture/model:free");
  expect(methods.every(method => method === "GET")).toBeTruthy();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: info.outputPath("model-recovery-and-coverage.png"), fullPage: true });
});

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
  await page.getByRole("tab", { name: "Flooded Areas" }).click();
  await expect(page.getByRole("tabpanel", { name: "Overview" })).toBeHidden();
  await expect(page.getByText(/No reported flood locations match these filters/)).toBeVisible();
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
  await expect(panel.getByRole("alert").filter({ hasText: "Worker dispatch needs attention" })).toBeVisible();
  await expect(panel.getByText(/Rainfall Advisory No. 6.*Issued.*Valid until/)).toBeHidden();
  await page.screenshot({ path: info.outputPath("overview-compact.png"), fullPage: true });
  await panel.getByText("Weather details", { exact: true }).click();
  await expect(panel.getByText(/Rainfall Advisory No. 6.*Issued.*Valid until/)).toBeVisible();
  await expect(panel.getByRole("alert").filter({ hasText: "news_dispatch_unavailable" })).toBeVisible();
  await expect(panel.getByText("Antipolo (upstream)", { exact: true })).toBeVisible();
  await expect(page.getByText("Worker last started", { exact: true })).toBeHidden();
  await page.getByText("Run details and diagnostics", { exact: true }).click();
  await expect(page.getByText("Worker last started", { exact: true })).toBeVisible();
  for (const width of info.project.name === "mobile-chromium" ? [390, 320] : [1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  expect(methods.every(method => method === "GET")).toBe(true);
  await page.screenshot({ path: info.outputPath("weather-scheduling.png"), fullPage: true });
});


test("tabs load areas on demand, support keyboard navigation and preserve search", async ({ page }) => {
  let resultsReads = 0;
  await setup(page, status, () => { resultsReads++; return { items: [], total: 0 }; });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  const overview = page.getByRole("tab", { name: "Overview", exact: true });
  const areas = page.getByRole("tab", { name: "Flooded Areas", exact: true });
  await expect(overview).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("status").filter({ hasText: "Gathering news" })).toBeVisible();
  expect(resultsReads).toBe(0);
  await expect(page.getByRole("tabpanel", { name: "Flooded Areas" })).toBeHidden();
  await expect(page.getByText("Worker last started", { exact: true })).toBeHidden();
  await overview.focus();
  await page.keyboard.press("ArrowRight");
  await expect(areas).toBeFocused();
  await expect(areas).toHaveAttribute("aria-selected", "true");
  await expect(page.getByText(/No reported flood locations match these filters/)).toBeVisible();
  const search = page.getByRole("textbox", { name: "Search flood locations" });
  await search.fill("Boni Avenue");
  await areas.focus();
  await page.keyboard.press("Home");
  await expect(overview).toBeFocused();
  await expect(page.getByRole("tabpanel", { name: "Flooded Areas" })).toBeHidden();
  await page.keyboard.press("End");
  await expect(areas).toBeFocused();
  await expect(search).toHaveValue("Boni Avenue");
  await page.keyboard.press("ArrowRight");
  await expect(overview).toBeFocused();
  await page.keyboard.press("ArrowLeft");
  await expect(areas).toBeFocused();
});

test("loading and paused collection keep overview status clear", async ({ page }) => {
  await setup(page, status);
  let release!: () => void;
  const response = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/v1/admin/news/automation", async route => {
    await response;
    await route.fulfill({ json: { ...status(), running: false, collection_enabled: false,
      status_label: "Collection paused", next_collection_due_at: null } });
  });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("status").filter({ hasText: "Loading status" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Refresh automation status" })).toBeDisabled();
  release();
  await expect(page.getByRole("status").filter({ hasText: "Collection paused" })).toBeVisible();
  await expect(page.getByText("Collection paused", { exact: true })).toHaveCount(2);
  await expect(page.getByText("Processing Enabled", { exact: true })).toBeVisible();
  await expect(page.getByText("No saved weather checks. Refresh after the controller runs.")).toBeVisible();
});
