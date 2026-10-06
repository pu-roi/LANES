import { expect, test, type Page } from "@playwright/test";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } });

const news = { case_id: 71, decision_id: 81, revision: 2, status: "Active", location_label: "C5, Ugong, Pasig",
  observed_at: "2026-10-06T01:00:00Z", expires_at: "2026-10-06T03:00:00Z", updated_at: "2026-10-06T01:05:00Z",
  source_title: "Flood report along C5", source_publisher: "Example News", source_url: "https://example.org/flood",
  geometry_basis: "estimated_road_corridor", geometry_precision: "operational_polygon", affects_routing: true,
  evidence_excerpt: "Knee-deep flooding along the reported C5 section.", current_status_unknown: false };
const zone = { id: 9, report_id: null, event_id: 6, is_active: true, severity: "medium", depth: "knee",
  created_at: news.updated_at, updated_at: news.updated_at, expires_at: news.expires_at,
  report_source: "news", reporter_name: "Example News", reporter_role: "News report", report_text: news.evidence_excerpt,
  passable_vehicles: "Unknown", contributors: [], news: [news],
  geometry: { type: "Polygon", coordinates: [[[121.079,14.569775],[121.081,14.569775],[121.081,14.570225],[121.079,14.570225],[121.079,14.569775]]] },
  report_geometry: { type: "LineString", coordinates: [[121.079,14.57],[121.081,14.57]] } };

async function pixels(page: Page) {
  const canvas = page.locator(".maplibregl-canvas");
  const bounds = await canvas.boundingBox();
  if (!bounds) return { core: 0, aura: 0, point: [0, 0] };
  const png = await page.screenshot({ scale: "css", clip: { x: bounds.x + 60, y: bounds.y + 60, width: bounds.width-120, height: bounds.height-120 } });
  const result = await page.evaluate(async (base64) => {
    const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
    const canvas = document.createElement("canvas"); canvas.width = image.width; canvas.height = image.height;
    const context = canvas.getContext("2d")!; context.drawImage(image, 0, 0);
    const rgba = context.getImageData(0, 0, canvas.width, canvas.height).data;
    const points: number[][] = []; let aura = 0;
    for (let i = 0; i < rgba.length; i += 4) {
      const r=rgba[i], g=rgba[i+1], b=rgba[i+2];
      if (r > 210 && g > 150 && g < 210 && b < 60) points.push([(i/4)%canvas.width, Math.floor(i/4/canvas.width)]);
      if (b > 100 && r-b > 35 && g-b > 20) aura++;
    }
    return { core: points.length, aura, point: points[Math.floor(points.length/2)] || [0, 0] };
  }, png.toString("base64"));
  return { ...result, point: [bounds.x+60+result.point[0], bounds.y+60+result.point[1]] };
}

test("news zone reuses the solid core and transparent aura with source details", async ({ page }, info) => {
  await page.addInitScript(() => sessionStorage.setItem("lanes_map_viewport", JSON.stringify({ center: [121.08, 14.57], zoom: 16 })));
  await page.route("**/api.maptiler.com/maps/**/style.json?**", (route) => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }],
  } }));
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/reports/active-zones")) return route.fulfill({ json: [zone] });
    if (path.endsWith("/feed/leaderboard")) return route.fulfill({ json: { reporters: [] } });
    if (path.endsWith("/feed")) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/map");
  await expect.poll(async () => (await pixels(page)).core, { timeout: 30_000 }).toBeGreaterThan(100);
  await expect.poll(async () => (await pixels(page)).aura, { timeout: 30_000 }).toBeGreaterThan(100);
  const rendered = await pixels(page);
  expect(rendered.aura).toBeGreaterThan(100);
  await page.locator(".maplibregl-canvas").screenshot({ path: info.outputPath("news-zone-existing-layers.png") });
  if (info.project.name === "mobile-chromium") await page.mouse.click(rendered.point[0], rendered.point[1]);
  else await page.mouse.move(rendered.point[0], rendered.point[1]);
  await expect(page.getByRole("link", { name: /Flood report along C5/ })).toBeVisible();
  await expect(page.getByText("Estimated road corridor; flood extent is unmeasured.", { exact: true })).toBeVisible();
  await expect(page.getByText(/Evidence expires/)).toBeVisible();
  await page.screenshot({ path: info.outputPath("news-zone-existing-details.png") });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
