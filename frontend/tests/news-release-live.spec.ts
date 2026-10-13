import { expect, test } from "@playwright/test";

const site = process.env.LANES_LIVE_SITE_URL;
const api = process.env.LANES_LIVE_API_URL;
test.skip(!site || !api, "Opt-in deployment smoke check using real public responses.");
test.setTimeout(90_000);
test.use({ browserName: "chromium", ...(site ? { baseURL: site } : {}),
  launchOptions: { args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } });

test("deployed home and map load with real public flood APIs", async ({ page }, info) => {
  expect(new URL(site!).protocol).toBe("https:");
  expect(new URL(api!).protocol).toBe("https:");
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  const health = await page.request.get(`${api}/health`);
  expect(health.status()).toBe(200);
  const zones = await page.request.get(`${api}/api/v1/reports/active-zones`);
  const alerts = await page.request.get(`${api}/api/v1/news/alerts?page_size=100`);
  expect(zones.status()).toBe(200);
  expect(alerts.status()).toBe(200);
  expect(Array.isArray(await zones.json())).toBeTruthy();
  expect(await alerts.json()).toHaveProperty("items");
  const history = await page.request.get(`${api}/api/v1/admin/flood-events/history`);
  expect(history.status()).toBe(401);
  const home = await page.goto("/", { waitUntil: "domcontentloaded" });
  expect(home?.status()).toBe(200);
  await expect(page.locator("main")).toBeVisible();
  const map = await page.goto("/map", { waitUntil: "domcontentloaded" });
  expect(map?.status()).toBe(200);
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  if (info.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: "Report Flood Hazard", exact: true }).click();
  }
  await page.getByRole("button", { name: "News alerts", exact: true }).click();
  await expect(page.getByRole("button", { name: "Close news alerts", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  expect(errors).toEqual([]);
  await page.screenshot({ path: info.outputPath("live-news-map.png") });
});
