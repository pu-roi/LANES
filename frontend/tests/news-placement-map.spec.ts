import { expect, test, type Page } from "@playwright/test";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
} });

// UI fixtures only: no article replay, moderation, provider calls or activation.
const geometry = { type: "MultiLineString", coordinates: [
  [[121.079, 14.57], [121.0798, 14.57]], [[121.0802, 14.57], [121.081, 14.57]],
] };
const placement = { run_id: 61, claim_index: 1, placement_revision: "ui-fixture", read_only: true,
  claim: { raw_place_name: "Boni Avenue", canonical_road: "Boni Avenue", canonical_city: "Mandaluyong",
    canonical_barangay: null, depth_formatted: "Ankle-deep", depth_raw: "ankle", road_passability: "unknown",
    event_time_resolved: null, evidence_sentence: "Flooding reported along Boni Avenue. ".repeat(8) },
  preview: { reported_severity: "low", status: "predicted_candidate", selected_candidate_id: "section-a", reason: "unique_ranked_prediction_not_verified_flood_extent",
    display_zone: { candidate_ids: ["section-a"],
      core_geometry: geometry,
      // Server-supplied dissolved halo; intentionally distinct from the core.
      aura_geometry: { type: "Polygon", coordinates: [[[121.078775,14.569775], [121.081225,14.569775],
        [121.081225,14.570225], [121.078775,14.570225], [121.078775,14.569775]]] } },
    candidates: [{ candidate_id: "section-a", preview_geometry: geometry, cross_streets: [["Martinez Street"], ["F. Ortigas Street"]],
      ambiguous_carriageway: false }, { candidate_id: "section-b", preview_geometry: { type: "LineString",
      coordinates: [[121.079, 14.5704], [121.081, 14.5704]] }, cross_streets: [], ambiguous_carriageway: true }] } };

async function setup(page: Page, unresolved = false) {
  const writes: string[] = [];
  await page.addInitScript(() => sessionStorage.setItem("lanes_map_viewport", JSON.stringify({ center: [121.08, 14.57], zoom: 16 })));
  await page.route("**/news-simulation.local.json", route => route.fulfill({ json: { mode: "september24" } }));
  await page.route("**/api.maptiler.com/maps/**/style.json?**", route => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }],
  } }));
  await page.route("**/api/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() !== "GET") writes.push(path);
    if (path.endsWith("/news/simulation")) return route.fulfill({ json: { mode: "september24", status: "Needs Review",
      routing_affected: false, article_title: "Boni Avenue source report", source_url: "https://example.org/boni",
      placement: unresolved ? { ...placement, preview: { ...placement.preview, status: "ambiguous",
        selected_candidate_id: null, reason: "top_section_has_arbitrary_bounds",
        // Reproduce a stale server response which still grouped alternatives.
        display_zone: { ...placement.preview.display_zone, candidate_ids: ["section-a", "section-b"] } } } : placement } });
    // An unrelated real zone participates in the overview, but not candidate focus.
    if (path.endsWith("/reports/active-zones")) return route.fulfill({ json: [{ id: 17, is_active: true, severity: "high",
      geometry: { type: "Polygon", coordinates: [[[121.129, 14.599], [121.131, 14.599], [121.131, 14.601], [121.129, 14.599]]] } }] });
    if (path.endsWith("/feed/leaderboard")) return route.fulfill({ json: { reporters: [] } });
    if (path.endsWith("/feed")) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/map");
  return writes;
}

async function roadPixel(page: Page) {
  const canvas = page.locator(".maplibregl-canvas");
  const box = await canvas.boundingBox();
  if (!box) return null;
  const png = await canvas.screenshot({ scale: "css" });
  const point = await page.evaluate(async base64 => {
    const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
    const surface = document.createElement("canvas"); surface.width = image.width; surface.height = image.height;
    const context = surface.getContext("2d")!; context.drawImage(image, 0, 0);
    const pixels = context.getImageData(0, 0, image.width, image.height).data;
    const points: number[][] = [];
    for (let y = 110; y < image.height - 110; y++) for (let x = 50; x < image.width - 50; x++) {
      const index = (y * image.width + x) * 4;
      if (pixels[index + 1] > pixels[index] + 10 && pixels[index] > pixels[index + 2] + 20) points.push([x, y]);
    }
    // Choose the middle of a painted run, rather than its round-cap edge or
    // the gap between two genuine disconnected sections.
    if (!points.length) return null;
    const row = points[Math.floor(points.length / 2)][1];
    const rowPoints = points.filter(point => point[1] === row);
    const runs: number[][][] = [[]];
    for (const point of rowPoints) {
      const run = runs[runs.length - 1];
      if (run.length && point[0] > run[run.length - 1][0] + 1) runs.push([]);
      runs[runs.length - 1].push(point);
    }
    const longest = runs.sort((a, b) => b.length - a.length)[0];
    return longest[Math.floor(longest.length / 2)];
  }, png.toString("base64"));
  return point ? { x: box.x + point[0], y: box.y + point[1] } : null;
}

async function geometryPixels(page: Page) {
  const png = await page.locator(".maplibregl-canvas").screenshot({ scale: "css" });
  return page.evaluate(async base64 => {
    const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
    const surface = document.createElement("canvas"); surface.width = image.width; surface.height = image.height;
    const context = surface.getContext("2d")!; context.drawImage(image, 0, 0);
    const viewport = JSON.parse(sessionStorage.getItem("lanes_map_viewport")!);
    const world = 512 * 2 ** viewport.zoom;
    const mercatorY = (lat: number) => (1 - Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) / Math.PI) / 2;
    const read = (lng: number, lat: number) => {
      const x = Math.round(image.width / 2 + (lng - viewport.center[0]) / 360 * world);
      const y = Math.round(image.height / 2 + (mercatorY(lat) - mercatorY(viewport.center[1])) * world);
      return Array.from(context.getImageData(x, y, 1, 1).data).slice(0, 3);
    };
    return { fragment: read(121.0794, 14.57), gap: read(121.08, 14.57), otherCarriageway: read(121.08, 14.5704),
      aura: read(121.08, 14.56986) };
  }, png.toString("base64"));
}

test("news suggestions share flood details and focus only the chosen road", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  const writes = await setup(page);
  await expect.poll(() => roadPixel(page), { timeout: 30_000 }).not.toBeNull();
  const point = (await roadPixel(page))!;
  const link = page.getByRole("link", { name: /Boni Avenue source report/ });
  if (info.project.name === "desktop-chromium") {
    await page.mouse.move(point.x, point.y);
    await expect(link).toBeVisible();
    await link.hover();
    await expect(link).toBeVisible();
    await page.mouse.move(350, 110);
    await expect(link).toBeHidden();
  }
  await page.mouse.click(point.x, point.y);
  await expect.poll(() => page.evaluate(() => JSON.parse(sessionStorage.getItem("lanes_map_viewport") || "{}").zoom)).toBe(16);
  if (info.project.name === "desktop-chromium") {
    await expect(link).toBeHidden();
    const focusedPoint = (await roadPixel(page))!;
    await expect(async () => {
      // Hover is ignored during a camera animation; enter again once settled.
      await page.mouse.move(350, 110);
      await page.mouse.move(focusedPoint.x, focusedPoint.y);
      await expect(link).toBeVisible({ timeout: 800 });
    }).toPass({ timeout: 10_000 });
  }
  await expect(link).toBeVisible();
  await expect(page.getByText("Needs Review", { exact: true })).toBeVisible();
  await expect(page.getByText("Height", { exact: true })).toBeVisible();
  await expect(page.getByText("Ankle-deep", { exact: true })).toBeVisible();
  await expect(page.getByText(/current flooding and its extent are unconfirmed/)).toBeVisible();
  const viewport = await page.evaluate(() => JSON.parse(sessionStorage.getItem("lanes_map_viewport") || "{}"));
  expect(viewport.center[0]).toBeCloseTo(121.08, 2);
  expect(viewport.center[1]).toBeCloseTo(14.57, 2);
  await page.screenshot({ path: info.outputPath("news-placement-details.png") });
  if (info.project.name === "desktop-chromium") {
    const bubble = await page.locator(".maplibregl-popup").boundingBox();
    expect(bubble!.y).toBeGreaterThanOrEqual(0);
    expect(bubble!.y + bubble!.height).toBeLessThanOrEqual(page.viewportSize()!.height);
  }
  if (info.project.name === "mobile-chromium") {
    const close = page.getByRole("button", { name: "Close flood details" });
    await expect(close).toBeInViewport();
    await close.click();
  } else await page.mouse.move(350, 110);
  await expect(link).toBeHidden();
  const colors = await geometryPixels(page);
  expect(colors.fragment[1] - colors.fragment[0]).toBeGreaterThan(10);
  // The opposite candidate is retained as evidence, not painted with the selected road.
  expect(colors.otherCarriageway).toEqual([241, 245, 249]);
  // The chosen core is solid. The real gap contains only the faint outer halo.
  expect(colors.fragment[1] - colors.fragment[2]).toBeGreaterThan(100);
  expect(colors.aura[1] - colors.aura[0]).toBeGreaterThan(10);
  expect(colors.aura[1] - colors.aura[2]).toBeLessThan(100);
  expect(colors.gap).toEqual(colors.aura);
  await page.locator(".maplibregl-canvas").screenshot({ path: info.outputPath("news-placement-focused-road.png") });
  if (info.project.name === "mobile-chromium") for (const size of [{ width: 320, height: 740 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(size);
    await expect.poll(() => roadPixel(page)).not.toBeNull();
    const road = (await roadPixel(page))!;
    await page.mouse.click(road.x, road.y);
    await expect(page.getByRole("button", { name: "Close flood details" })).toBeInViewport();
    await link.scrollIntoViewIfNeeded();
    await expect(link).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`news-placement-${size.width}x${size.height}.png`) });
    await page.getByRole("button", { name: "Close flood details" }).click();
    await expect(link).toBeHidden();
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  expect(writes).toEqual([]);
});

test("unresolved alternatives never paint a public zone or move focus away from active zones", async ({ page }, info) => {
  const writes = await setup(page, true);
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await expect.poll(() => page.evaluate(() => {
    const view = JSON.parse(sessionStorage.getItem("lanes_map_viewport") || "{}");
    return view.center?.[0];
  })).toBeCloseTo(121.13, 3);
  // Zoom in to ensure neither detail strokes nor overview pins represent the alternatives.
  for (let count = 0; count < 3; count++) await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await expect.poll(() => roadPixel(page)).toBeNull();
  await expect(page.locator(".maplibregl-popup")).toHaveCount(0);
  await page.screenshot({ path: info.outputPath("unresolved-public-alternatives-excluded.png") });
  expect(writes).toEqual([]);
});
