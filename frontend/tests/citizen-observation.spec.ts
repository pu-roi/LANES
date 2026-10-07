import { expect, test } from "@playwright/test";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });

for (const automatic of [true, false]) test(`saved citizen observation survives reload and shows ${automatic ? "automatic approval" : "manual review"} feedback`, async ({ page }, info) => {
  await page.addInitScript(() => localStorage.setItem("lanes_token", "synthetic-citizen-fixture"));
  let submitted = "";
  await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: { version: 8, sources: {}, layers: [] } }));
  await page.route("**/api/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/auth/test-token")) return route.fulfill({ json: { id: 73, username: "Fixture citizen", is_active: true, role: { name: "Commuter", permissions: {} } } });
    if (path.endsWith("/reports") && route.request().method() === "POST") {
      submitted = route.request().postData() || "";
      return route.fulfill({ status: 201, json: { id: 91, status: automatic ? "approved" : "pending",
        automatic_review_reason: automatic ? "existing_zone_corroborated" : "automatic_approval_disabled" } });
    }
    if (path.endsWith("/feed")) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/map?action=report");
  await page.evaluate(async () => {
    const draft = { version: 1, ownerId: "73", updatedAt: new Date().toISOString(),
      active: { floodStart: null, floodEnd: null, floodPreviewGeometry: null, floodOppositeGeometry: null,
        floodIsBidirectional: false, startInput: "", endInput: "", visualOption: null, passableVehicles: [],
        hiddenHazards: null, showSurvey: false, description: "", mediaFiles: [], isPublic: false, step: 1,
        observedAt: "2026-10-07T15:30" },
      queuedDrafts: [{ id: "observation-fixture", observedAt: "2026-10-07T15:30",
        geometry: { type: "LineString", coordinates: [[121.08,14.57],[121.081,14.57]] },
        oppositeGeometry: null, isBidirectional: false, severity: "medium", depth: "knee",
        description: "Current knee-deep flood on the affected road", mediaFiles: [],
        startLabel: "Fixture road", endLabel: "End", roadName: "Fixture road",
        passableVehicles: ["Large Trucks / Buses"], hiddenHazards: "no" }] };
    await new Promise<void>((resolve, reject) => {
      const request = indexedDB.open("keyval-store");
      request.onupgradeneeded = () => request.result.createObjectStore("keyval");
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const transaction = request.result.transaction("keyval", "readwrite");
        transaction.objectStore("keyval").put(draft, "lanes:flood-report-draft:v1:73");
        transaction.oncomplete = () => { request.result.close(); resolve(); };
        transaction.onerror = () => reject(transaction.error);
      };
    });
  });
  await page.reload();
  if (info.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: "Report Flood Hazard" }).click();
    await page.getByRole("button", { name: "Flood Report", exact: true }).click();
  } else await page.getByRole("button", { name: "Expand panel" }).click();
  await expect(page.getByLabel("When did you observe this flood? (Optional)")).toHaveValue("2026-10-07T15:30");
  await page.getByRole("button", { name: "View drafts", exact: true }).click();
  await page.getByRole("button", { name: "Submit All 1 Drafts" }).click();
  await expect.poll(() => submitted).toContain('name="observed_at"');
  expect(submitted).toContain('name="survey_data"');
  expect(submitted).toContain("Large Trucks / Buses");
  await expect(page.getByText(automatic ? "Eligible reports were automatically approved. Check My Reports for each report status." : "Thank you! Your reports are now in review.")).toBeVisible();
});
