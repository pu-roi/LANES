import { expect, test } from "@playwright/test";
import { installChrisFixtures, expectNoOverflow } from "./helpers/chrisIntegration";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });

test("opens the history detail modal and its no-report collections", async ({ page }) => {
  await installChrisFixtures(page, "Admin");
  const requests: string[] = [];
  page.on("request", request => {
    if (request.url().includes("/flood-events/920/inspection")) requests.push(request.url());
  });
  // The existing fixture is a no-report incident. Opening the dialog, rather
  // than merely checking its history card, exercises the missed interaction.
  await page.goto("/admin/flood-history");
  await page.getByText("Flood Events", { exact: true }).click();
  await expect(page.getByText("Flood Event #920", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View event", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Flood Event Details", exact: true });
  await expect(dialog.getByRole("heading", { name: "Official incident summary" })).toBeVisible();
  await expect(dialog.getByRole("alert")).toHaveCount(0);
  await dialog.getByText("Reports (0)", { exact: true }).click();
  await expect(dialog.getByText(/No citizen reports are linked to this event/)).toBeVisible();
  await dialog.getByText("Official history", { exact: true }).click();
  await expect(dialog.getByText("Official Zone #910", { exact: true })).toBeVisible();
  await expect(dialog.getByRole("alert")).toHaveCount(0);
  await expectNoOverflow(page);
  expect(requests.some(value => new URL(value).pathname.endsWith("/inspection"))).toBeTruthy();
  expect(requests.some(value => new URL(value).pathname.endsWith("/inspection/zones"))).toBeTruthy();
  await dialog.getByRole("button", { name: "Close flood event details" }).click();
  await expect(dialog).toHaveCount(0);
});
