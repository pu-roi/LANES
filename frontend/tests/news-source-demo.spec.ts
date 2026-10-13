import { expect, test } from "@playwright/test";

const demoURL = process.env.LANES_NLP_DEMO_URL;
type DemoZone = { depth: string | null; report_text: string; news?: { geometry_basis: string; source_url: string;
  depth_label: string | null; location_qualifier: string | null }[];
  report_geometry?: { coordinates: unknown }; geometry: { coordinates: unknown } };
test.skip(!demoURL, "Opt-in persisted local NLP demonstration; no API fixtures or production access.");
test.setTimeout(90_000);
test.use({ browserName: "chromium", ...(demoURL ? { baseURL: demoURL } : {}),
  launchOptions: { args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } });

test("real pipeline polygons and source details render on the map", async ({ page }, info) => {
  expect(new URL(demoURL!).hostname).toMatch(/^(127\.0\.0\.1|localhost)$/);
  const response = await page.request.get("/api/v1/reports/active-zones");
  expect(response.ok()).toBeTruthy();
  const zones: DemoZone[] = await response.json();
  const zone = zones.find(z => z.news?.some(n => n.geometry_basis === "estimated_road_corridor"
    && n.depth_label === "19 inches" && n.location_qualifier?.startsWith("Santo Domingo,")));
  expect(zones.length).toBeGreaterThanOrEqual(7);
  expect(zone).toBeTruthy();
  expect(zone!.depth).toBe("knee");
  expect(zone!.report_text).not.toContain("\u25b6");
  expect(zone!.report_text).not.toContain(" … ");
  expect(zone!.report_text.length).toBeGreaterThan(300);
  function coordinate(value: unknown): number[] | undefined {
    if (Array.isArray(value) && value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") return [value[0], value[1]];
    if (Array.isArray(value)) for (const child of value) { const point = coordinate(child); if (point) return point; }
  }
  const center = coordinate(zone!.report_geometry?.coordinates || zone!.geometry.coordinates);
  expect(center).toBeTruthy();
  await page.addInitScript(point => sessionStorage.setItem("lanes_map_viewport", JSON.stringify({ center: point, zoom: 17 })), center!);
  const loaded = page.waitForResponse(r => r.url().includes("/reports/active-zones") && r.status() === 200);
  await page.goto("/map", { waitUntil: "domcontentloaded" });
  await loaded;
  const canvas = page.locator(".maplibregl-canvas");
  await expect(canvas).toBeVisible();
  const bounds = await canvas.boundingBox();
  expect(bounds).toBeTruthy();
  const details = page.getByText("Estimated road corridor; flood extent is unmeasured.", { exact: true });
  await expect(async () => {
    if (info.project.name === "mobile-chromium") await page.mouse.click(bounds!.x + bounds!.width / 2, bounds!.y + bounds!.height / 2);
    else await page.mouse.move(bounds!.x + bounds!.width / 2, bounds!.y + bounds!.height / 2);
    await expect(details).toBeVisible({ timeout: 1000 });
  }).toPass({ timeout: 30_000 });
  await expect(page.locator(`a[href="${zone!.news![0].source_url}"]`)).toBeVisible();
  const expand = page.getByRole("button", { name: "See more", exact: true });
  if (await expand.count()) {
    await expand.click();
    await expect(page.getByRole("button", { name: "See less", exact: true })).toBeVisible();
  }
  await page.screenshot({ path: info.outputPath("real-nlp-map.png") });
});
