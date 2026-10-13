import { expect, test } from "@playwright/test";

if (process.env.PLAYWRIGHT_CHROME_PATH) {
  test.use({ browserName: "chromium", launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });
}

for (const share of [false, true]) {
  test(`flood submission ${share ? "shares immediately while awaiting review" : "stays private without sharing"}`, async ({ page }, testInfo) => {
    test.setTimeout(90_000);
    const content = "Fresh community flood observation";
    let submitted = false;
    let shared = false;
    await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
    await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: { version: 8, sources: {}, layers: [] } }));
    await page.route("**/api/v1/**", async route => {
      const path = new URL(route.request().url()).pathname;
      if (path.endsWith("/reports/preview-bidirectional")) {
        const geometry = { type: "LineString", coordinates: [[121.0, 14.5], [121.001, 14.501]] };
        return route.fulfill({ json: { original: geometry, opposite: null, coverage_geometry: geometry,
          road_type: "SINGLE_DIRECTION", validation_status: "VALIDATED", message: "Road preview ready" } });
      }
      if (path.endsWith("/auth/test-token")) return route.fulfill({ json: {
        id: 987654, username: "sharing-test", is_active: true, role: { name: "Commuter", permissions: {} },
      } });
      if (path.endsWith("/reports") && route.request().method() === "POST") {
        const body = route.request().postData() || "";
        shared = /name="is_public"\r\n\r\ntrue/.test(body);
        submitted = true;
        return route.fulfill({ status: 201, json: { id: 876543, status: "pending" } });
      }
      if (path.endsWith("/feed")) return route.fulfill({ json: {
        posts: submitted && shared ? [{ id: 876544, user_id: 987654, content, author_name: "Sharing Test",
          created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
          upvotes: 0, downvotes: 0, comment_count: 0,
          report: { id: 876543, raw_text: content, source: "direct_user", status: "pending", severity: "low" },
        }] : [], total: submitted && shared ? 1 : 0, has_more: false,
      } });
      if (path.endsWith("/notifications")) return route.fulfill({ json: { notifications: [], unread_count: 0, total: 0, has_more: false } });
      if (path.endsWith("/feed/leaderboard")) return route.fulfill({ json: { reporters: [] } });
      if (path.endsWith("/feed/hotspots")) return route.fulfill({ json: { hotspots: [], window_hours: 24, as_of: new Date().toISOString() } });
      if (path.endsWith("/news/local-updates")) return route.fulfill({ json: { items: [], as_of: new Date().toISOString() } });
      return route.fulfill({ json: [] });
    });
    await page.goto("/map?action=report");
    await page.evaluate(async content => {
      const draft = { version: 1, ownerId: "987654", updatedAt: new Date().toISOString(), queuedDrafts: [], active: {
        floodStart: { coords: [121.0, 14.5], label: "Start" }, floodEnd: { coords: [121.001, 14.501], label: "End" },
        floodPreviewGeometry: { type: "LineString", coordinates: [[121.0, 14.5], [121.001, 14.501]] },
        floodOppositeGeometry: null, floodIsBidirectional: false, startInput: "Start", endInput: "End",
        visualOption: "gutter", passableVehicles: ["Motorcycle"], hiddenHazards: "no", showSurvey: false,
        description: content, mediaFiles: [], isPublic: false, step: 2,
      } };
      await new Promise<void>((resolve, reject) => {
        const request = indexedDB.open("keyval-store");
        request.onupgradeneeded = () => request.result.createObjectStore("keyval");
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const transaction = request.result.transaction("keyval", "readwrite");
          transaction.objectStore("keyval").put(draft, "lanes:flood-report-draft:v1:987654");
          transaction.oncomplete = () => { request.result.close(); resolve(); };
          transaction.onerror = () => reject(transaction.error);
        };
      });
    }, content);
    await page.reload();
    if (testInfo.project.name === "mobile-chromium") {
      await page.getByRole("button", { name: "Report Flood Hazard" }).click();
      await page.getByRole("button", { name: "Flood Report", exact: true }).click();
    } else await page.getByRole("button", { name: "Expand panel" }).click();
    const checkbox = page.getByRole("checkbox", { name: "Share in Community Feed" });
    await expect(checkbox).not.toBeChecked();
    if (share) {
      await checkbox.check();
      await expect(page.getByText(/labeled as awaiting review until approved/)).toBeVisible();
    }
    await page.getByRole("button", { name: "Submit All (1)", exact: true }).click();
    await expect(page.getByText("Reports Submitted", { exact: true })).toBeVisible();
    expect(submitted).toBe(true);
    expect(shared).toBe(share);
    if (share) await expect(page.getByText(/Shared in the Community Feed/)).toBeVisible();
    await page.getByRole("link", { name: /^Feed/ }).first().click();
    await expect(page).toHaveURL(/\/feed$/);
    if (share) {
      const article = page.locator("article").filter({ hasText: content });
      await expect(article.getByText("Awaiting review", { exact: true })).toBeVisible();
      await expect(article.locator('[title="Verified by Admin"]')).toHaveCount(0);
      const bounds = await article.boundingBox();
      expect(bounds!.x).toBeGreaterThanOrEqual(0);
      expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
      await article.screenshot({ path: testInfo.outputPath("pending-community-post.png") });
    } else await expect(page.locator("article").filter({ hasText: content })).toHaveCount(0);
  });
}
