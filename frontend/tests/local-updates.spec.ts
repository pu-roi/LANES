import { expect, test, type Page, type TestInfo } from "@playwright/test";

test.use({ browserName: "chromium" });
test.setTimeout(90_000);

async function setup(page: Page, info: TestInfo, state: "populated" | "empty" | "error" = "populated") {
  const control = { state, requests: 0 };
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/news/local-updates")) {
      control.requests++;
      expect(route.request().method()).toBe("GET");
      if (control.state === "error") return route.fulfill({ status: 503, json: { detail: "Local news unavailable" } });
      return route.fulfill({ json: { items: control.state === "empty" ? [] : [
        { id: 51, title: "Floodwaters reported along C5 Road in Pasig City", publisher: "Example News",
          source_url: "https://example.org/news/flood", published_at: "2026-10-11T01:00:00Z" },
      ], as_of: "2026-10-11T01:10:00Z" } });
    }
    if (url.pathname.endsWith("/feed")) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    if (url.pathname.endsWith("/feed/hotspots")) return route.fulfill({ json: { hotspots: [], window_hours: 48 } });
    if (url.pathname.endsWith("/feed/leaderboard")) return route.fulfill({ json: { reporters: [] } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/feed", { waitUntil: "domcontentloaded" });
  await expect.poll(() => control.requests, { timeout: 45_000 }).toBeGreaterThan(0);
  const panel = page.getByRole("region", { name: "Local Updates" }).filter({ visible: true });
  if (info.project.name === "mobile-chromium") await panel.locator("summary").click();
  return { control, panel };
}

test("shows collected article links and publisher dates on desktop and mobile", async ({ page }, info) => {
  const { panel } = await setup(page, info);
  const link = panel.getByRole("link", { name: /Floodwaters reported along C5/ });
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute("href", "https://example.org/news/flood");
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", "noopener noreferrer");
  await expect(panel.getByText("Example News", { exact: true })).toBeVisible();
  await expect(panel.locator("time")).toHaveAttribute("datetime", "2026-10-11T01:00:00Z");
  await expect(panel.getByText(/may not reflect current conditions/)).toBeVisible();
  await expect(page.getByText(/City Council announces new drainage/)).toHaveCount(0);
  const bounds = await panel.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.screenshot({ path: info.outputPath("local-updates.png"), fullPage: true });
});

test("shows an honest empty state", async ({ page }, info) => {
  const { panel } = await setup(page, info, "empty");
  await expect(panel.getByText("No recent local flood news is available.")).toBeVisible();
  await expect(panel.getByRole("link")).toHaveCount(0);
});

test("surfaces failures and retries", async ({ page }, info) => {
  const { control, panel } = await setup(page, info, "error");
  await expect(panel.getByRole("alert")).toContainText("Couldn’t load local news.");
  control.state = "populated";
  await panel.getByRole("button", { name: "Retry local news" }).click();
  await expect(panel.getByRole("link")).toBeVisible();
  expect(control.requests).toBeGreaterThan(1);
});

test("refreshes articles and preserves cached news on a failed refresh", async ({ page }, info) => {
  const { control, panel } = await setup(page, info);
  await expect(panel.getByRole("link")).toBeVisible();
  control.state = "error";
  await panel.getByRole("button", { name: "Refresh local news" }).click();
  await expect(panel.getByRole("alert")).toContainText("Previously downloaded articles are shown below.");
  await expect(panel.getByRole("link")).toBeVisible();
  control.state = "empty";
  await panel.getByRole("button", { name: "Retry local news" }).click();
  await expect(panel.getByText("No recent local flood news is available.")).toBeVisible();
});

test("identifies offline cached articles", async ({ page, context }, info) => {
  const { panel } = await setup(page, info);
  await expect(panel.getByRole("link")).toBeVisible();
  await context.setOffline(true);
  await expect(panel.getByText(/Offline. Showing last downloaded news/)).toBeVisible();
  await expect(panel.getByRole("link")).toBeVisible();
  await expect(panel.getByRole("button", { name: "Refresh local news" })).toBeDisabled();
  await context.setOffline(false);
});
