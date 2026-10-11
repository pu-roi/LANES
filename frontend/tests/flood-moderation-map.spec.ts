import { expect as baseExpect, test, type Page } from "@playwright/test";
const expect = baseExpect.configure({ timeout: 30_000 });

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
} });

type Status = "pending" | "approved" | "rejected";
const report = {
  id: 42, source: "direct_user", raw_text: "Flooding at the bridge approach.",
  severity: "medium", depth: "knee", status: "pending" as Status,
  created_at: "2026-10-11T01:00:00Z", updated_at: "2026-10-11T01:00:00Z",
  geometry: { type: "LineString", coordinates: [[121.0798, 14.57], [121.0802, 14.57]] },
  is_bidirectional: true, survey: { hidden_hazards: "yes", passable_vehicles: "suv,heavy" },
  human_readable_location: "Bridge approach", barangay: "Maybunga", city: "Pasig",
  reporter_name: "Test Citizen", reporter_username: "citizen", zone_id: 9,
};
const zone = {
  id: 9, report_id: 8, name: "Bridge flood zone", is_active: true, severity: "medium", depth: "knee",
  created_at: report.created_at, updated_at: report.updated_at, expires_at: "2099-01-01T00:00:00Z",
  geometry: { type: "Polygon", coordinates: [[[121.0797,14.5699],[121.0803,14.5699],[121.0803,14.5701],[121.0797,14.5701],[121.0797,14.5699]]] },
  passable_vehicles: report.survey.passable_vehicles, hidden_hazards: "yes", is_bidirectional: true,
  contributors: [{ report_id: 42, geometry: report.geometry, raw_text: report.raw_text,
    severity: "medium", depth: "knee", reporter_name: "Test Citizen", created_at: report.created_at }],
};

async function setup(page: Page, status: Status = "pending") {
  const state = { status, missing: false, nullSurvey: false, activeZone: true };
  const writes: string[] = [];
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }],
  } }));
  await page.route("**/api/v1/**", route => {
    const path = decodeURIComponent(new URL(route.request().url()).pathname);
    if (route.request().method() !== "GET" && !path.endsWith("/auth/test-token")) writes.push(path);
    const current = { ...report, status: state.status,
      ...(state.nullSurvey ? { depth: null, is_bidirectional: null, survey: null } : {}) };
    let body: unknown = [];
    if (path.endsWith("/auth/test-token")) body = { id: 7, username: "admin", is_active: true, role: { id: 1, name: "Super Admin" } };
    else if (path.endsWith("/admin/moderation/flood-reports")) body = [{ report_id: 42, status,
      source: report.source, raw_text: report.raw_text, severity: report.severity, depth: report.depth,
      submitted_at: report.created_at, reporter: "citizen", location: "Bridge approach", zone_id: 9 }];
    else if (path.endsWith("/admin/reports/detail/42")) {
      if (state.missing) return route.fulfill({ status: 404, json: { detail: "Report not found" } });
      body = current;
    } else if (path.endsWith("/admin/reports/pending")) body = state.status === "pending" ? [current] : [];
    else if (path.endsWith("/reports/active-zones")) body = state.activeZone ? [zone] : [];
    else if (path.endsWith("/admin/zones/all")) body = { zones: state.activeZone ? [zone] : [], total: state.activeZone ? 1 : 0 };
    else if (path.endsWith("/admin/review/items")) body = { items: [], total: 0, pages: 1, page: 1, counts: { all: 0, news_claims: 0, user_reports: 0 } };
    else if (path.endsWith("/items/user_report:42")) body = { key: "user_report:42", source: "user_report",
      is_current_review: state.status === "pending", report: current, news: null };
    else if (path.includes("/groups/user_report:42/members")) body = { items: [], total: 0, pages: 1, page: 1 };
    else if (path.endsWith("/notifications")) body = { notifications: [], total: 0, unread_count: 0, has_more: false };
    return route.fulfill({ json: body });
  });
  return { state, writes };
}

async function openDetails(page: Page) {
  await page.goto("/admin/moderation?tab=flood");
  await page.getByRole("button", { name: "Info", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Flood Report Details" });
  await expect(dialog).toBeVisible();
  return dialog;
}

async function verifyMapFocus(page: Page) {
  const openMap = page.getByRole("button", { name: "Open map", exact: true });
  if ((page.viewportSize()?.width ?? 1440) < 768) await openMap.click();
  await expect(page.getByText("Z: 16.0", { exact: true })).toBeVisible({ timeout: 30_000 });
  // Verify the flood feature actually renders near the center of the destination canvas.
  // The neutral basemap has no yellow/orange flood pixels.
  await expect.poll(async () => {
    const canvas = page.locator(".maplibregl-canvas");
    const bounds = await canvas.boundingBox();
    if (!bounds) return 0;
    const png = await page.screenshot({ clip: { x: bounds.x + bounds.width / 2 - 65,
      y: bounds.y + bounds.height / 2 - 65, width: 130, height: 130 } });
    return page.evaluate(async base64 => {
      const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
      const canvas = document.createElement("canvas"); canvas.width = 130; canvas.height = 130;
      const context = canvas.getContext("2d")!; context.drawImage(image, 0, 0, 130, 130);
      const rgba = context.getImageData(0, 0, 130, 130).data;
      let count = 0;
      for (let i = 0; i < rgba.length; i += 4) {
        if (rgba[i] > rgba[i + 2] + 25 && rgba[i + 1] > rgba[i + 2] + 15) count++;
      }
      return count;
    }, png.toString("base64"));
  }, { timeout: 30_000 }).toBeGreaterThan(10);
}

for (const status of ["pending", "approved"] as const) {
  test(`${status} details match spatial evidence and focus the correct tab on first visit`, async ({ page }, testInfo) => {
    const { writes } = await setup(page, status);
    const dialog = await openDetails(page);
    await expect(dialog.getByText('Knee • 19" (0.48m)', { exact: true })).toBeVisible();
    await expect(dialog.getByText("Yes", { exact: true })).toBeVisible();
    await expect(dialog.getByText("Both directions", { exact: true })).toBeVisible();
    await expect(dialog.getByText("SUVs / Pickups, Large Trucks / Buses", { exact: true })).toBeVisible();
    await expect(dialog.getByRole("button", { name: "View on Map", exact: true })).toHaveCount(1);
    await expect(dialog.getByRole("button", { name: /Focus/ })).toHaveCount(0);
    const reportBadge = dialog.getByText("#42", { exact: true });
    await expect.poll(() => reportBadge.evaluate((badge) => {
      const bounds = badge.getBoundingClientRect();
      const foreground = document.elementFromPoint(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
      return foreground !== null && badge.contains(foreground);
    })).toBe(true);
    await page.screenshot({ path: testInfo.outputPath("moderation-details.png") });
    await dialog.getByRole("button", { name: "View on Map", exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`focus_report_id=42.*tab=${status === "approved" ? "zones" : "pending"}`));
    await expect(page.getByRole("region", { name: status === "approved" ? "Active Zones" : "Needs Review", exact: true })).toBeVisible({ timeout: 30_000 });
    if (status === "pending") {
      await expect(page.getByRole("region", { name: "Needs Review", exact: true }).getByText(report.raw_text)).toBeVisible();
      await page.getByRole("button", { name: "Info", exact: true }).click();
      const spatial = page.getByRole("dialog", { name: "Flood Report Details" });
      await expect(spatial.getByText('Knee • 19" (0.48m)', { exact: true })).toBeVisible();
      await expect(spatial.getByText("SUVs / Pickups, Large Trucks / Buses", { exact: true })).toBeVisible();
      await expect(spatial.getByText("Yes", { exact: true })).toBeVisible();
      await expect(spatial.getByText("Both directions", { exact: true })).toBeVisible();
      await spatial.getByRole("button", { name: "Close flood report details" }).click();
    }
    await verifyMapFocus(page);
    await page.screenshot({ path: testInfo.outputPath("focused-map.png") });
    expect(writes).toEqual([]);
  });
}

test("navigation uses latest status after another staff member approves the report", async ({ page }) => {
  const { state } = await setup(page);
  const dialog = await openDetails(page);
  state.status = "approved";
  await dialog.getByRole("button", { name: "View on Map", exact: true }).click();
  await expect(page).toHaveURL(/tab=zones/);
  await expect(page.getByRole("region", { name: "Active Zones", exact: true })).toBeVisible({ timeout: 30_000 });
});

test("destination overrides a stale pending tab hint for an approved report", async ({ page }) => {
  await setup(page, "approved");
  await page.goto("/admin/map?focus_report_id=42&tab=pending&lat=14.6&lng=121.1");
  await expect(page.getByRole("region", { name: "Active Zones", exact: true })).toBeVisible({ timeout: 30_000 });
  await verifyMapFocus(page);
});

test("missing survey fields show unknown values instead of one direction or no hazards", async ({ page }) => {
  const { state } = await setup(page);
  state.nullSurvey = true;
  const dialog = await openDetails(page);
  await expect(dialog.getByText("Not recorded", { exact: true })).toHaveCount(4);
  await expect(dialog.getByText("One direction", { exact: true })).toHaveCount(0);
});

test("unavailable report details show an error and can be retried", async ({ page }) => {
  const { state } = await setup(page);
  state.missing = true;
  await page.goto("/admin/moderation?tab=flood");
  await page.getByRole("button", { name: "Info", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Could not load flood report details" })).toBeVisible();
  state.missing = false;
  await page.getByRole("button", { name: "Retry details" }).click();
  await expect(page.getByRole("dialog", { name: "Flood Report Details" })).toBeVisible();
});

test("a report removed after opening details prevents navigation and surfaces the error", async ({ page }) => {
  const { state } = await setup(page);
  const dialog = await openDetails(page);
  state.missing = true;
  await dialog.getByRole("button", { name: "View on Map", exact: true }).click();
  await expect(page.getByText("Could not open report on map", { exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/admin\/moderation/);
});

test("rejected reports retain inspection-only evidence without approval actions", async ({ page }) => {
  const { writes } = await setup(page, "rejected");
  const dialog = await openDetails(page);
  await dialog.getByRole("button", { name: "View on Map", exact: true }).click();
  await expect(page.getByText(/This item no longer belongs to the current review queue/)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("button", { name: /^Approve/ })).toHaveCount(0);
  expect(writes).toEqual([]);
});

test("approved report with no available active zone stays out of Needs Review", async ({ page }) => {
  const { state } = await setup(page, "approved");
  state.activeZone = false;
  await page.goto("/admin/map?focus_report_id=42&tab=zones");
  await expect(page.getByRole("region", { name: "Active Zones", exact: true })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("This approved report no longer has an available active zone.", { exact: true })).toBeVisible();
});
