import type { Page } from "@playwright/test";

/** Open a group and return from its automatic mobile map to inspect its records. */
export async function inspectZoneGroup(page: Page, location?: string) {
  await page.getByRole("button", { name: location ? `Inspect zone group: ${location}` : /^Inspect zone group:/, exact: !!location }).click();
  if (await page.evaluate(() => window.matchMedia("(max-width: 767px)").matches)) {
    await page.getByRole("button", { name: "Back to zones", exact: true }).click();
  }
}
