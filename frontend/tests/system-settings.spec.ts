import { expect, test, type Page } from "@playwright/test";

test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });

function configuration(canEdit = true) {
  const depths = [
    { key: "gutter", label: "Gutter" }, { key: "half-knee", label: "Half-Knee" },
    { key: "half-tire", label: "Half-Tire" }, { key: "knee", label: "Knee" },
    { key: "tires", label: "Tires" }, { key: "waist", label: "Waist" },
    { key: "chest", label: "Chest" }, { key: "neck", label: "Neck & Above" },
    { key: "unknown", label: "Unknown depth" },
  ];
  return {
    revision: 1, updated_at: null, updated_by: 1, can_edit: canEdit,
    automatic_news_buffer_metres: 25,
    settings: { staff_road_buffer_metres: 25, evidence_expiry_minutes: Object.fromEntries(depths.map(depth => [depth.key, 120])),
      news_unconfirmed_retention_hours: 24, citizen_auto_approval_enabled: false,
      citizen_min_trust: 75, citizen_min_accuracy: 90, citizen_min_human_reviews: 5,
      news_collection_enabled: true, news_processing_enabled: true, news_publication_enabled: true,
      news_collection_interval_minutes: 30, news_source_ids: ["verified"] },
    depth_options: depths,
    source_options: [{ id: "verified", publisher: "Verified publisher" }],
    runtime: { last_started_at: null, last_successful_at: null, last_finished_at: null,
      next_collection_at: null, running: false, error_code: null, scheduler_tick_minutes: 15,
      stage_counts: {}, stage_outcomes: { processing: "enabled", publication: "enabled" },
      stages: { collection: { last_attempt_at: "2026-10-07T10:00:00Z", last_success_at: "2026-10-07T10:01:00Z",
        outcome: "completed", counts: { entries_read: 94, eligible_candidates: 0 }, errors: [] } } },
  };
}

async function setup(page: Page, options: { readOnly?: boolean; forbidden?: boolean; failure?: boolean; conflict?: boolean } = {}) {
  let state = configuration(!options.readOnly);
  await page.addInitScript(() => localStorage.setItem("lanes_token", "synthetic-settings-fixture"));
  await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: { version: 8, sources: {}, layers: [] } }));
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/auth/test-token")) return route.fulfill({ json: { id: 1, username: "Fixture admin", is_active: true,
      role: { name: "Super Admin", permissions: { settings: options.readOnly ? "view" : "full" } } } });
    if (path.endsWith("/admin/settings/configuration")) {
      if (options.forbidden) return route.fulfill({ status: 403, json: { detail: "Not authorized to view system settings" } });
      if (route.request().method() === "PUT") {
        if (options.failure) return route.fulfill({ status: 503, json: { detail: "Settings were not saved. Retry later." } });
        if (options.conflict) {
          state = { ...state, revision: 2, settings: { ...state.settings, staff_road_buffer_metres: 32 } };
          return route.fulfill({ status: 409, json: { detail: "Settings changed elsewhere. Reload before saving your draft." } });
        }
        const payload = route.request().postDataJSON();
        expect(payload.revision).toBe(state.revision);
        state = { ...state, settings: payload.settings, revision: state.revision + 1 };
      }
      return route.fulfill({ json: state });
    }
    if (path.endsWith("/reports/latest-snapshot")) return route.fulfill({ json: { zones: [], alerts: [], version: "fixture" } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/admin/settings");
}

async function switchTab(page: Page, name: string) {
  await page.getByRole("navigation", { name: "Settings sections" }).getByRole("button", { name, exact: true }).click();
}

test("settings save and revert work with actual units and recorded health", async ({ page }, info) => {
  await setup(page);
  await expect(page.getByRole("heading", { name: "System Settings", exact: true })).toBeVisible();
  const buffer = page.getByRole("spinbutton", { name: "Staff road buffer (metres)" });
  await expect(buffer).toBeVisible();
  await page.screenshot({ path: info.outputPath("settings-overview.png"), scale: "css" });
  await buffer.fill("35");
  await switchTab(page, "News automation");
  await page.getByRole("button", { name: "Collection interval (minutes)" }).click();
  await page.getByRole("button", { name: "15 minutes", exact: true }).click();
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(page.getByText("Saved configuration · revision 2")).toBeVisible();
  await switchTab(page, "Flood zones");
  await buffer.fill("45");
  await page.getByRole("button", { name: "Revert", exact: true }).click();
  await expect(buffer).toHaveValue("35");
  await switchTab(page, "Operational status");
  await expect(page.getByText("No eligible flood reports found in this collection run.")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await switchTab(page, "Flood zones");
  await page.screenshot({ path: info.outputPath("settings-top.png"), scale: "css" });
  await switchTab(page, "News automation");
  await page.screenshot({ path: info.outputPath("settings-news.png"), scale: "css" });
});

test("view permission allows status inspection and disables all editing", async ({ page }) => {
  await setup(page, { readOnly: true });
  await expect(page.getByText(/You have view-only access/)).toBeVisible();
  await expect(page.getByRole("spinbutton", { name: "Staff road buffer (metres)" })).toBeDisabled();
  await switchTab(page, "Citizen approval");
  await expect(page.getByRole("checkbox", { name: "Enable citizen automatic approval" })).toBeDisabled();
  await switchTab(page, "News automation");
  await expect(page.getByLabel("Automatic RSS collection", { exact: false })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Collection interval (minutes)" })).toBeDisabled();
  await expect(page.getByRole("checkbox", { name: "Verified publisher" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Save settings" })).toBeDisabled();
});

test("settings shares Admin gutters and separate tabs preserve unsaved controls", async ({ page }, info) => {
  test.setTimeout(60_000);
  await setup(page);
  const settingsForm = page.locator("form").filter({ has: page.getByRole("heading", { name: "System Settings", exact: true }) });
  const settingsBounds = await settingsForm.boundingBox();
  await page.goto("/admin/roles");
  const rolesBounds = await page.getByRole("heading", { name: "Role Management", exact: true }).locator("../..").locator("..").boundingBox();
  expect(settingsBounds).not.toBeNull();
  expect(rolesBounds).not.toBeNull();
  expect(settingsBounds!.x).toBeCloseTo(rolesBounds!.x, 0);
  expect(settingsBounds!.width).toBeCloseTo(rolesBounds!.width, 0);

  await page.goto("/admin/settings");
  await expect(page.getByRole("region", { name: "Flood Zone Configuration" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Citizen Automatic Approval", includeHidden: true })).toBeHidden();
  await page.getByRole("spinbutton", { name: "Staff road buffer (metres)" }).fill("40");
  await switchTab(page, "News automation");
  await expect(page.getByRole("region", { name: "News Automation" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Flood Zone Configuration", includeHidden: true })).toBeHidden();
  await page.getByRole("checkbox", { name: "Automatic RSS collection", exact: true }).uncheck();
  await page.getByRole("checkbox", { name: "Verified publisher" }).uncheck();
  await page.getByRole("button", { name: "Collection interval (minutes)" }).click();
  await page.getByRole("button", { name: "60 minutes", exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await expect(page.getByRole("button", { name: "Save settings" })).toBeInViewport();
  await page.screenshot({ path: info.outputPath("settings-controls.png"), scale: "css" });
  await page.getByRole("button", { name: "Revert", exact: true }).click();
  await expect(page.getByRole("checkbox", { name: "Automatic RSS collection", exact: true })).toBeChecked();
  await expect(page.getByRole("checkbox", { name: "Verified publisher" })).toBeChecked();
  await expect(page.getByRole("button", { name: "Collection interval (minutes)" })).toHaveText("30 minutes");
  await switchTab(page, "Flood zones");
  await expect(page.getByRole("spinbutton", { name: "Staff road buffer (metres)" })).toHaveValue("25");
});

test("saving reveals invalid fields in another tab and preserves edits across all tabs", async ({ page }, info) => {
  await setup(page);
  let saves = 0;
  page.on("request", request => {
    if (request.method() === "PUT" && request.url().includes("/admin/settings/configuration")) saves += 1;
  });
  const buffer = page.getByRole("spinbutton", { name: "Staff road buffer (metres)" });
  await buffer.fill("");
  await switchTab(page, "News automation");
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(buffer).toBeVisible();
  await expect(buffer).toBeFocused();
  expect(saves).toBe(0);
  await buffer.fill("35");

  await switchTab(page, "Evidence expiry");
  const knee = page.getByRole("spinbutton", { name: "Knee expiry (minutes)", exact: true });
  await knee.fill("150");
  await switchTab(page, "Operational status");
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(knee).toBeVisible();
  await expect(knee).toBeFocused();
  expect(saves).toBe(0);
  await knee.fill("100");
  await page.screenshot({ path: info.outputPath("settings-evidence-tab.png"), scale: "css" });
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(page.getByText("Saved configuration · revision 2")).toBeVisible();
  expect(saves).toBe(1);
  await switchTab(page, "Flood zones");
  await expect(buffer).toHaveValue("35");
  await switchTab(page, "Evidence expiry");
  await expect(knee).toHaveValue("100");
});

test("failed save keeps the administrator draft and displays the error", async ({ page }) => {
  await setup(page, { failure: true });
  const buffer = page.getByRole("spinbutton", { name: "Staff road buffer (metres)" });
  await buffer.fill("40");
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Settings were not saved. Retry later." })).toBeVisible();
  await expect(buffer).toHaveValue("40");
  await expect(page.getByText("Unsaved changes", { exact: true })).toBeVisible();
});

test("conflict preserves the draft and revert loads the current revision", async ({ page }) => {
  await setup(page, { conflict: true });
  const buffer = page.getByRole("spinbutton", { name: "Staff road buffer (metres)" });
  await buffer.fill("40");
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /Settings changed elsewhere/ }).first()).toBeVisible();
  await expect(buffer).toHaveValue("40");
  await page.getByRole("button", { name: "Revert", exact: true }).click();
  await expect(buffer).toHaveValue("32");
});

test("missing settings permission shows an authorization error", async ({ page }) => {
  await setup(page, { forbidden: true });
  await expect(page.getByRole("alert").filter({ hasText: "Not authorized to view system settings" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry loading settings" })).toBeVisible();
});

test("unsaved settings require confirmation before sidebar navigation", async ({ page }) => {
  await setup(page);
  await page.getByRole("spinbutton", { name: "Staff road buffer (metres)" }).fill("40");
  if ((page.viewportSize()?.width || 1280) < 768) await page.getByRole("button", { name: "Open admin menu" }).click();
  else await page.getByRole("navigation", { name: "Admin navigation" }).hover();
  page.once("dialog", dialog => dialog.dismiss());
  await page.getByRole("link", { name: "Dashboard", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/settings$/);
  await expect(page.getByRole("spinbutton", { name: "Staff road buffer (metres)" })).toHaveValue("40");
});
