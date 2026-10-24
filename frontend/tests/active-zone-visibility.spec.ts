import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import ts from "typescript";
import { mapLayers } from "./helpers/mapLayers";
import { zoneMapResponse } from "./helpers/chrisIntegration";

test.setTimeout(90_000);
test.use({ browserName: "chromium", reducedMotion: "reduce", launchOptions: {
  args: ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"],
} });

const zones = [[121.001, 14.592], [120.962, 14.669]].map(([lng, lat], index) => ({
  id: 91 + index, name: `NCR fixture road ${index + 1}`, report_id: null, is_active: true,
  severity: "low", depth: "gutter", report_source: "news", report_text: "Original road flood evidence",
  contributors: [], news: [], created_at: "2026-10-24T01:00:00Z", expires_at: null,
  geometry: { type: "Polygon", coordinates: [[[lng-.0002,lat-.001],[lng+.0002,lat-.001],
    [lng+.0002,lat+.001],[lng-.0002,lat+.001],[lng-.0002,lat-.001]]] },
  report_geometry: { type: "LineString", coordinates: [[lng,lat-.001],[lng,lat+.001]] },
}));
const groups = zones.map(zone => ({ zone_id: zone.id, location: zone.name, member_count: 1,
  area_summary: "NCR fixture", sources: ["news"], severity_levels: ["low"], depth_levels: ["gutter"],
  queued_at: zone.created_at, evidence: zone.report_text, group_reason: "One source-bound road",
  bounds: [zone.report_geometry.coordinates[0][0]-.0002,zone.report_geometry.coordinates[0][1],
    zone.report_geometry.coordinates[1][0]+.0002,zone.report_geometry.coordinates[1][1]] }));

async function setup(page: Page, handoff = false) {
  const state = { gate: null as Promise<void> | null, failed: false, empty: false, viewportReads: 0 };
  const writes: string[] = [];
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: { version: 8, sources: {},
    layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }] } }));
  await page.route("https://*.tile.openstreetmap.org/**", route => route.fulfill({ contentType: "image/png",
    body: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", "base64") }));
  const pending = { id: 501, status: "pending", source: "direct_user", raw_text: "Pending Pasig fixture",
    severity: "medium", created_at: zones[0].created_at, geometry: zones[0].report_geometry };
  await page.route("**/api/v1/**", async route => {
    const url = new URL(route.request().url()), path = decodeURIComponent(url.pathname);
    if (route.request().method() !== "GET" && !path.endsWith("/auth/test-token")) writes.push(path);
    let body: unknown = [];
    if (path.endsWith("/auth/test-token")) body = { id: 7, username: "admin", is_active: true, role: { name: "Super Admin", id: 1 } };
    else if (path.endsWith("/notifications")) body = { notifications: [], total: 0, unread_count: 0, has_more: false };
    else if (path.endsWith("/admin/reports/detail/501")) body = pending;
    else if (path.endsWith("/items/user_report:501")) body = { key: "user_report:501", source: "user_report", is_current_review: true, report: pending, news: null };
    else if (path.endsWith("/admin/reports/pending")) body = handoff ? [pending] : [];
    else if (path.endsWith("/admin/review/items")) body = { items: [], zones: [], total: 0, page: 1, pages: 1, counts: { all: 0, user_reports: 0, news_claims: 0 } };
    else if (path.endsWith("/admin/zones/map")) {
      if (!url.searchParams.has("summary_only")) {
        state.viewportReads++;
        if (state.gate) await state.gate;
      }
      if (state.failed) return route.fulfill({ status: 503, json: { detail: "Fixture map unavailable" } });
      const bbox = url.searchParams.get("bbox")?.split(",").map(Number);
      const shown = state.empty ? [] : !bbox ? zones : zones.filter(zone => {
        const [lng,lat] = zone.report_geometry.coordinates[0];
        return lng >= bbox[0] && lng <= bbox[2] && lat >= bbox[1] && lat <= bbox[3];
      });
      body = zoneMapResponse(shown, url.href);
    } else if (path.endsWith("/admin/zones/queue")) body = { items: groups, zones: [], total: 2, item_total: 2,
      counts: { all: 2, news: 2, user_reports: 0, official: 0, other: 0 }, facets: { cities: [], barangays: [] },
      page: 1, pages: 1, page_size: 20, read_only: true };
    else if (/\/admin\/zones\/groups\/\d+\/members$/.test(path)) {
      const id = Number(path.split("/").at(-2));
      body = { zone_id: id, zones: zones.filter(zone => zone.id === id), zone_total: 2, total: 1,
        page: 1, pages: 1, page_size: 20, group_reason: "One source-bound road", read_only: true };
    } else if (/\/admin\/zones\/\d+$/.test(path)) body = zones.find(zone => zone.id === Number(path.split("/").at(-1)));
    else if (path.endsWith("/reports/active-zones")) body = zones;
    else if (path.endsWith("/admin/zones/count")) body = { total: 2 };
    return route.fulfill({ json: body });
  });
  await page.goto(handoff ? "/admin/map?focus_report_id=501&tab=pending" : "/admin/map", { waitUntil: "domcontentloaded" });
  if (handoff) await expect(page.getByRole("region", { name: "User report evidence", exact: true }))
    .toContainText("Pending Pasig fixture", { timeout: 30_000 });
  await page.getByRole("button", { name: /Active Zones/ }).click();
  await expect(page.getByRole("button", { name: "Inspect zone group: NCR fixture road 1", exact: true })).toBeVisible();
  return { state, writes };
}

async function openMap(page: Page) {
  const button = page.getByRole("button", { name: "Open map", exact: true });
  // The width media-query hook hydrates after navigation; do not mistake its
  // initial desktop render for an already-open compact map.
  if ((page.viewportSize()?.width ?? 1024) < 768) await expect(button).toBeVisible({ timeout: 30_000 });
  if (await button.count()) await button.click();
  await expect(page.locator("canvas.maplibregl-canvas")).toBeVisible({ timeout: 30_000 });
}

async function coloredZones(page: Page) {
  const snapshot = await mapLayers(page);
  return [...new Set(snapshot?.rendered.filter(f => f.layer.startsWith("active-zones-")
    && f.properties.color === "#84cc16").map(f => Number(f.properties.id)))].sort();
}

test("worker updates retain rendered color, evidence and flags across selection and property removal", async ({ page }) => {
  await page.setContent('<div id="map" style="width:100%;height:400px"></div>');
  await page.addScriptTag({ path: require.resolve("maplibre-gl/dist/maplibre-gl.js") });
  const compiled = ts.transpileModule(readFileSync(resolve("src/features/map/syncGeoJSONSource.ts"), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  await page.addScriptTag({ content: `window.syncModule={exports:{}};(function(exports){${compiled}})(window.syncModule.exports);` });
  const result = await page.evaluate(async () => {
    const w = window as unknown as { maplibregl: typeof import("maplibre-gl"); syncModule: { exports: typeof import("../src/features/map/syncGeoJSONSource") } };
    const map = new w.maplibregl.Map({ container: "map", style: { version: 8, sources: {}, layers: [
      { id: "background", type: "background", paint: { "background-color": "#ffffff" } },
    ] }, center: [121,14.6], zoom: 16, canvasContextAttributes: { preserveDrawingBuffer: true } });
    await new Promise(resolve => map.once("load", resolve));
    const samples = [];
    for (const [index, selected] of [false,true,false,true].entries()) {
      w.syncModule.exports.syncGeoJSONSource(map, "fixture", { type: "FeatureCollection", features: [{ type: "Feature", id: "91:road",
        properties: { id: 91, color: "#84cc16", severity: "LOW", is_selected: selected,
          is_road_line: true, report_text: "Original evidence", ...(index < 2 ? { obsolete: "remove me" } : {}) },
        geometry: { type: "LineString", coordinates: [[121,14.599],[121,14.601]] },
      }] });
      if (!map.getLayer("line")) map.addLayer({ id: "line", type: "line", source: "fixture", paint: { "line-color": ["get","color"], "line-width": 15 } });
      await new Promise(resolve => map.once("idle", resolve));
      const canvas = document.createElement("canvas"); canvas.width = map.getCanvas().width; canvas.height = map.getCanvas().height;
      const context = canvas.getContext("2d")!; context.drawImage(map.getCanvas(),0,0);
      samples.push({ properties: map.querySourceFeatures("fixture")[0].properties,
        pixel: [...context.getImageData(Math.floor(canvas.width/2),Math.floor(canvas.height/2),1,1).data] });
    }
    // Queue geometry and property changes without an intervening worker round
    // trip, then add/reorder/remove a different feature on the same source.
    const feature: GeoJSON.Feature = { type: "Feature", id: "91:road",
      properties: { id: 91, color: "#84cc16", severity: "LOW", is_selected: true,
        is_road_line: true, report_text: "Original evidence" },
      geometry: { type: "LineString", coordinates: [[121,14.598],[121,14.602]] } };
    const sync = (features: GeoJSON.Feature[]) => w.syncModule.exports.syncGeoJSONSource(map,"fixture",{type:"FeatureCollection",features});
    sync([feature]);
    sync([{...feature,properties:{id:91,color:"#84cc16",severity:"LOW",is_selected:false,is_road_line:true}}]);
    await new Promise(resolve => map.once("idle",resolve));
    const burst = map.querySourceFeatures("fixture")[0].properties;
    const second = {...feature,id:"92:road",properties:{id:92,color:"#f97316",severity:"HIGH"}};
    sync([feature,second]);
    sync([second,feature]);
    sync([second]);
    await new Promise(resolve => map.once("idle",resolve));
    const remaining = [...new Set(map.querySourceFeatures("fixture").map(f=>f.properties.id))];
    map.remove(); return { samples, burst, remaining };
  });
  for (const [index, sample] of result.samples.entries()) {
    expect(sample.pixel).toEqual([132,204,22,255]);
    expect(sample.properties).toMatchObject({ id: 91, color: "#84cc16", severity: "LOW", report_text: "Original evidence", is_road_line: true, is_selected: index % 2 === 1 });
    if (index >= 2) expect(sample.properties).not.toHaveProperty("obsolete");
  }
  expect(result.burst).toMatchObject({id:91,color:"#84cc16",severity:"LOW",is_selected:false,is_road_line:true});
  expect(result.burst).not.toHaveProperty("report_text");
  expect(result.remaining).toEqual([92]);
});

test("overview frames all NCR floods, survives style reload, and does not undo manual panning", async ({ page }) => {
  const { writes } = await setup(page); await openMap(page);
  await expect.poll(() => coloredZones(page), { timeout: 30_000 }).toEqual([91,92]);
  await mapLayers(page, { center: [121.001,14.592], zoom: 16 });
  await expect.poll(() => coloredZones(page)).toContain(91);
  await mapLayers(page, { reloadStyle: true });
  await expect.poll(() => coloredZones(page), { timeout: 20_000 }).toContain(91);
  const layers = (await mapLayers(page))!.layers.map(layer => layer.id);
  for (const id of ["active-zones-layer","active-zones-road-core-layer","active-zones-circle-layer"]) {
    expect(layers.indexOf(id)).toBeGreaterThan(layers.indexOf("pasig-mask-fill"));
  }
  for (const terrain of [true,false]) {
    await mapLayers(page, { terrain });
    await expect.poll(() => coloredZones(page), { timeout: 20_000 }).toContain(91);
  }
  for (const zoom of [13.9,14,14.1,16]) {
    await mapLayers(page, { zoom });
    await expect.poll(() => coloredZones(page)).toContain(91);
  }
  expect((await mapLayers(page))?.center[0]).toBeCloseTo(121.001,4);
  expect(writes).toEqual([]);
});

test("returning from individual inspection restores the complete active overview", async ({ page }) => {
  await setup(page);
  const panel = page.getByRole("region", { name: "Active Zones", exact: true });
  await panel.getByRole("button", { name: "Inspect zone group: NCR fixture road 1", exact: true }).click();
  const mobileBack = page.getByRole("button", { name: "Back to zones", exact: true }).filter({ visible: true });
  if (await panel.isHidden()) await mobileBack.click();
  await panel.getByRole("button", { name: "View on map", exact: true }).click();
  await expect.poll(() => coloredZones(page), { timeout: 30_000 }).toContain(91);
  await expect.poll(async () => (await mapLayers(page))?.rendered.some(f => f.properties.id === 91
    && f.properties.is_selected === true && f.properties.color === "#84cc16")).toBe(true);
  if (await panel.isHidden()) await mobileBack.click();
  await panel.getByRole("button", { name: "Back to zones", exact: true }).click();
  await openMap(page);
  await expect.poll(() => coloredZones(page), { timeout: 30_000 }).toEqual([91,92]);
});

test("slow and failed viewport refreshes retain geometry; authoritative empty results clear it", async ({ page }) => {
  const { state, writes } = await setup(page); await openMap(page);
  await expect.poll(() => coloredZones(page), { timeout: 30_000 }).toEqual([91,92]);
  let release = () => {};
  state.gate = new Promise<void>(resolve => { release = resolve; });
  const reads = state.viewportReads;
  try {
    const camera = await mapLayers(page);
    await mapLayers(page, { center: [camera!.center[0]+.001,camera!.center[1]] });
    await expect.poll(() => state.viewportReads).toBeGreaterThan(reads);
    expect(await coloredZones(page)).toEqual([91,92]);
    // Pan again while the previous viewport is still in flight. The superseded
    // request must not clear the current shapes or override the latest result.
    const pendingReads = state.viewportReads;
    await mapLayers(page, { center: [camera!.center[0]+.002,camera!.center[1]] });
    await expect.poll(() => state.viewportReads).toBeGreaterThan(pendingReads);
    expect(await coloredZones(page)).toEqual([91,92]);
    await expect(page.getByText("Updating flood map…", { exact: true })).toHaveCount(0);
    state.failed = true; release(); state.gate = null;
    await expect(page.getByRole("alert").filter({ hasText: "Active flood map could not be refreshed.", visible: true }))
      .toContainText("Previously loaded floods remain visible");
    expect(await coloredZones(page)).toEqual([91,92]);
    state.failed = false; state.empty = true;
    await page.getByRole("button", { name: "Retry flood map", exact: true }).filter({ visible: true }).click();
    await expect.poll(() => coloredZones(page)).toEqual([]);
    await expect(page.getByText("No active floods have mapped boundaries.", { exact: true }).filter({ visible: true })).toBeVisible();
    expect(writes).toEqual([]);
  } finally { release(); state.gate = null; }
});

test("review handoff isolation cannot hide the Active Zones overview", async ({ page }) => {
  await setup(page, true); await openMap(page);
  await expect.poll(() => coloredZones(page), { timeout: 30_000 }).toEqual([91,92]);
});

test("drawing failures remain visible and recover after style restoration", async ({ page }) => {
  await setup(page); await openMap(page);
  await expect.poll(() => coloredZones(page), { timeout: 30_000 }).toEqual([91,92]);
  await mapLayers(page, { failFloodLayer: true, reloadStyle: true });
  await expect(page.getByRole("alert").filter({ hasText: "Flood zones could not be drawn.", visible: true })).toBeVisible();
  await page.getByRole("button", { name: "Retry flood map", exact: true }).filter({ visible: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Flood zones could not be drawn.", visible: true })).toBeVisible();
  await mapLayers(page, { restore: true, reloadStyle: true });
  await expect.poll(() => coloredZones(page), { timeout: 20_000 }).toEqual([91,92]);
  await expect(page.getByRole("alert").filter({ hasText: "Flood zones could not be drawn.", visible: true })).toHaveCount(0);
});

test("explicit coordinate handoffs retain their focus instead of fitting the overview", async ({ page }) => {
  test.setTimeout(120_000); // Two full navigations, including compact canvas hydration.
  await setup(page);
  await page.goto("/admin/map?tab=zones&lat=14.592&lng=121.001&zoom=16");
  await openMap(page);
  await expect.poll(async () => (await mapLayers(page))?.center[0], { timeout: 30_000 }).toBeCloseTo(121.001,4);
  await expect.poll(async () => (await mapLayers(page))?.zoom).toBeCloseTo(16,1);
  await expect.poll(() => coloredZones(page)).toEqual([91]);
});
