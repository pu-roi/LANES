import { expect, test } from "@playwright/test";
import { installChrisFixtures } from './helpers/chrisIntegration';
test.setTimeout(90_000);
test.use({ browserName: 'chromium' });

test.describe("Flood History & Analytics administrator workspace", () => {
  test.beforeEach(async ({ page }) => { await installChrisFixtures(page, 'Admin'); });

  test("shows distinct-event analytics and safe planning export controls", async ({ page }) => {
    await page.goto("/admin/flood-history");

    await expect(page.getByRole("heading", { name: "Flood History & Analytics" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "City planning analytics" })).toBeVisible();
    await expect(page.getByText(/Approved reports are a separate confidence signal\./)).toBeVisible();
    await expect(page.getByRole("button", { name: "Records CSV" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Analytics JSON" })).toBeVisible();
  });

  test("filters the protected event records workspace", async ({ page }) => {
    await page.goto("/admin/flood-history");
    await page.getByRole("button", { name: "Flood Events", exact: true }).click();

    await expect(page.getByRole("heading", { name: "Flood Event Records" })).toBeVisible();
    await page.getByRole("button", { name: "Event status" }).click();
    await page.getByRole("button", { name: "Ended", exact: true }).click();
    await page.getByRole("button", { name: "Peak severity" }).click();
    await page.getByRole("button", { name: "High", exact: true }).click();
    await page.getByLabel("Barangay", { exact: true }).fill("San Antonio");
    await expect(page.getByRole("button", { name: "Clear filters" })).toBeVisible();
  });

  test("offers an explicit mobile map/list switcher", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobile-chromium", "This interaction is mobile-specific.");
    await page.goto("/admin/flood-history");
    await page.getByRole("button", { name: "Flood Events", exact: true }).click();

    await expect(page.getByRole("button", { name: "List" })).toBeVisible();
    await page.getByRole("button", { name: "Map" }).click();
    await expect(page.getByText("Verified event footprints")).toBeVisible();
  });
});
