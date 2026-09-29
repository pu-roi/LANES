import { expect, test } from "@playwright/test";

// Local machines without Playwright's bundled browsers can use installed Chrome.
if (process.env.PLAYWRIGHT_CHROME_PATH) {
  test.use({
    browserName: "chromium",
    launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH },
  });
}

test("keeps selected photo and video attached in the flood report panel", async ({ page }, testInfo) => {
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/auth/test-token", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ id: 987654, username: "media-test" }),
  }));

  await page.goto("/map?action=report");
  await page.evaluate(async () => {
    const draft = {
      version: 1,
      ownerId: "987654",
      updatedAt: new Date().toISOString(),
      active: {
        floodStart: { coords: [121.0, 14.5], label: "Start" },
        floodEnd: { coords: [121.001, 14.501], label: "End" },
        floodPreviewGeometry: { type: "LineString", coordinates: [[121.0, 14.5], [121.001, 14.501]] },
        floodOppositeGeometry: null,
        floodIsBidirectional: false,
        startInput: "Start",
        endInput: "End",
        visualOption: "gutter",
        passableVehicles: [],
        hiddenHazards: null,
        showSurvey: false,
        description: "",
        mediaFiles: [],
        isPublic: false,
        step: 2,
      },
      queuedDrafts: [],
    };
    await new Promise<void>((resolve, reject) => {
      const request = indexedDB.open("keyval-store");
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const transaction = request.result.transaction("keyval", "readwrite");
        transaction.objectStore("keyval").put(draft, "lanes:flood-report-draft:v1:987654");
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      };
    });
  });
  await page.reload();

  if (testInfo.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: "Report Flood Hazard" }).click();
    await page.getByRole("button", { name: "Flood Report", exact: true }).click();
  }

  const picker = page.getByLabel("Add photos or videos to flood report");
  await expect(picker).toBeVisible();
  await picker.setInputFiles([
    { name: "street.jpg", mimeType: "image/jpeg", buffer: Buffer.from("photo") },
    { name: "street.mp4", mimeType: "video/mp4", buffer: Buffer.from("video") },
  ]);

  await expect(page.getByText("2 files ready to publish")).toBeVisible();
  await expect(page.getByText("street.jpg")).toBeVisible();
  await expect(page.getByText("street.mp4")).toBeVisible();
});
