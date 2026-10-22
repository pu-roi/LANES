import { expect as baseExpect, test, type Page } from "@playwright/test";
import { installChrisFixtures, expectNoOverflow, floodHistoryResponse, floodMapResponse } from "./helpers/chrisIntegration";
import { mapLayers } from "./helpers/mapLayers";

const expect = baseExpect.configure({ timeout: 20_000 });
test.setTimeout(120_000);
test.use({ browserName: "chromium" });
const fill = "historical-flood-events-fill";
const heat = "historical-flood-heatmap-layer";
const zone = (id: number, x: number) => ({ id, geometry: { type: "Polygon", coordinates: [[[x,14.57],[x+.001,14.57],[x+.001,14.571],[x,14.571],[x,14.57]]] }, created_at: "2026-10-20T00:00:00Z", is_active: false, severity: "high" });
const events = [0,1].map(index => ({ id: 920+index, status: "ended", first_reported_at: "2026-10-20T00:00:00Z", verified_at: "2026-10-20T01:00:00Z", ended_at: "2026-10-20T02:00:00Z",
  peak_severity: index ? "extreme" : "low", peak_depth: "knee", supporting_report_count: 0, reporter_count: 0,
  duration_seconds: 3600, duration_minutes: 60,
  locations: [{ id: index+1, location_type: "road", display_name: `Historical Road ${index}`, normalized_name: `historical road ${index}`, created_at: "2026-10-20T00:00:00Z" }],
  zones: [zone(910+index,121.08+index*.12)], reports: [], timeline: [],
  heatmap_features: [{ type: "Feature", geometry: { type: "Point", coordinates: [121.0805+index*.12,14.5705] }, properties: { event_id: 920+index, zone_id: 910+index, weight: index ? 5 : 1 } }],
}));

async function setup(page: Page, records: (Omit<(typeof events)[number], "heatmap_features"> & { heatmap_features: unknown[] })[] = events) {
  const state = await installChrisFixtures(page,"Admin");
  const writes: string[] = [];
  let unmapped = false;
  const controls = { pageError: false };
  const historyRequests: URLSearchParams[] = [];
  await page.route(/\/api\/v1\/admin\/flood-events\/(records|map)\?/, route => {
    const parameters = new URL(route.request().url()).searchParams;
    historyRequests.push(parameters);
    if (parameters.has("page") && controls.pageError) return route.fulfill({ status: 503, json: { detail: "Fixture page storage unavailable" } });
    const q = parameters.get("search");
    const data = q === "nothing" ? [] : q ? records.slice(0,1) : records;
    const mapped = data.map(event => unmapped ? { ...event, zones: [{ ...event.zones[0], geometry: null }], heatmap_features: [] } : event);
    return route.fulfill({ json: new URL(route.request().url()).pathname.endsWith('/map') ? floodMapResponse(mapped, route.request().url()) : floodHistoryResponse(mapped, route.request().url()) });
  });
  await page.route("**/api/v1/admin/flood-events/920/inspection", route => route.fulfill({json:events[0]}));
  await page.route("**/api/v1/admin/flood-events/920/inspection/*?*", route => {
    const collection = new URL(route.request().url()).pathname.split('/').pop() as 'zones' | 'reports' | 'timeline' | 'locations';
    return route.fulfill({ json: { items: events[0][collection], total: events[0][collection].length, page: 1, pages: 1, page_size: 20 } });
  });
  page.on("request", request => { if (request.url().includes("/api/v1/") && !request.url().includes("/auth/test-token") && request.method() !== "GET") writes.push(request.method()+" "+request.url()); });
  await page.goto("/admin/flood-history");
  // Analytics data confirms client hydration before interacting with the tabs.
  await expect(page.getByText("Verified Flood Events",{exact:true}).first()).toBeVisible();
  await page.getByRole("button", {name:"Flood Events",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Flood Event Records",exact:true})).toBeVisible();
  return { ...state, writes, controls, historyRequests, setUnmapped: () => {unmapped=true;} };
}
async function openMap(page: Page) {
  const button = page.getByRole("button", {name:"Map",exact:true});
  if (await button.isVisible()) await button.click();
  await expect.poll(async () => (await mapLayers(page))?.layers.some(layer=>layer.id===heat || layer.id===fill)).toBe(true);
  await expect.poll(async () => {
    const sources = (await mapLayers(page))?.sources;
    return ["historical-flood-events-source", "historical-flood-heatmap-source"].reduce((total,id) => total +
      ((sources?.[id] as { data?: { features?: unknown[] } })?.data?.features?.length || 0), 0);
  }).toBeGreaterThan(0);
}

const pagedEvents = Array.from({ length: 45 }, (_, index) => {
  const id = 2000 + index, zoneId = 3000 + index, x = 121.08 + index * .002;
  return { ...events[0], id, locations: [{ ...events[0].locations[0], display_name: `Pagination Road ${index}` }],
    zones: [zone(zoneId, x)], heatmap_features: [{ type: "Feature", geometry: { type: "Point", coordinates: [x + .0005, 14.5705] },
      properties: { event_id: id, zone_id: zoneId, weight: 1 } }] };
});

test("workspace tabs retain the initialized map and manual camera", async ({ page }) => {
  await setup(page);
  await openMap(page);
  await mapLayers(page, { pan: true });
  const before = (await mapLayers(page))!.center;
  const canvas = await page.locator('[aria-label="Historical flood map"] canvas.maplibregl-canvas').elementHandle();
  await page.getByRole("button", { name: "Analytics", exact: true }).click();
  expect(await canvas!.evaluate(element => element.isConnected)).toBe(true);
  await page.getByRole("button", { name: "Flood Events", exact: true }).click();
  await openMap(page);
  expect(await canvas!.evaluate(element => element.isConnected)).toBe(true);
  expect((await mapLayers(page))!.center).toEqual(before);
});

for (const count of [1000, 10000]) test(`production browsing renders ${count} zones through bounded chunks`, async ({ page }, info) => {
  test.setTimeout(180_000);
  if (info.project.name === "mobile-chromium") await page.setViewportSize({ width: 320, height: 740 });
  const records = Array.from({ length: count }, (_, index) => ({ ...events[0], id: 10000+index,
    zones: [zone(20000+index,121.08)], heatmap_features: index ? [] : [{ ...events[0].heatmap_features[0],
      properties: { weight: count, zone_count: count } }] }));
  const client = await page.context().newCDPSession(page);
  await client.send("Performance.enable");
  const started = Date.now();
  const state = await setup(page, records);
  const list = page.getByRole("region", { name: "Flood event list", exact: true });
  await expect(list.locator("article")).toHaveCount(20);
  const cardsMs = Date.now()-started;
  const opened = Date.now();
  await openMap(page);
  const firstMapMs = Date.now()-opened;
  await mapLayers(page, { zoom: 15 });
  await expect.poll(async () => (await mapLayers(page, { countsOnly: true }))?.sourceCounts["historical-flood-events-source"],
    { timeout: 120_000 }).toBe(count);
  const metrics = await client.send("Performance.getMetrics");
  await client.detach();
  const measurements = { count, project: info.project.name, transport: "fictional bounded responses, production frontend",
    cardsMs, firstMapMs, completeMapMs: Date.now()-opened,
    browser: metrics.metrics.filter((metric: { name: string }) => ["JSHeapUsedSize", "TaskDuration", "ScriptDuration"].includes(metric.name)) };
  console.log("BROWSER_SCALE", JSON.stringify(measurements));
  await info.attach("browse-measurements", { body: JSON.stringify(measurements,null,2), contentType: "application/json" });
  await expectNoOverflow(page);
  expect(state.writes).toEqual([]);
  expect(state.errors).toEqual([]);
});

test("history beyond 250 stays reachable and viewport chunks load completely", async ({ page }, info) => {
  if (info.project.name === "mobile-chromium") await page.setViewportSize({ width: 320, height: 740 });
  const many = Array.from({ length: 600 }, (_, index) => ({ ...events[0], id: 4000+index,
    zones: [zone(5000+index,121.08)], heatmap_features: [{ ...events[0].heatmap_features[0], properties: { event_id: 4000+index, zone_id: 5000+index, weight: 1 } }] }));
  const state = await setup(page, many);
  const list = page.getByRole("region", { name: "Flood event list", exact: true });
  const pagination = page.getByRole("region", { name: "Flood event pagination", exact: true });
  await expect(pagination.getByRole("status")).toContainText("600 events");
  await expect(list.locator("article")).toHaveCount(20);
  await openMap(page);
  await mapLayers(page, { zoom: 15 });
  await expect.poll(async () => ((await mapLayers(page))?.sources["historical-flood-events-source"] as { data: { features: unknown[] } })?.data.features.length).toBe(600);
  expect(state.historyRequests.some(params => Number(params.get("cursor")) > 0)).toBe(true);
  if (info.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: "List", exact: true }).click();
    for (let index=0;index<13;index++) {
      await pagination.getByRole("button", { name: "Next", exact: true }).click();
      await expect(pagination.getByRole("status")).toContainText(`Page ${index+2} of 30`);
    }
  } else await pagination.getByTitle("Last Page", { exact: true }).click();
  await expect(list.locator("article")).toHaveCount(20);
  const id = info.project.name === "mobile-chromium" ? 4260 : 4580;
  await expect(list.locator(`article[data-event-id="${id}"]`)).toBeVisible();
  await expectNoOverflow(page);
  expect(state.writes).toEqual([]);
});

test("shared pagination limits cards to 20 and preserves all filtered map records", async ({ page }, info) => {
  if (info.project.name === "mobile-chromium") await page.setViewportSize({ width: 320, height: 740 });
  const state = await setup(page, pagedEvents);
  const list = page.getByRole("region", { name: "Flood event list", exact: true });
  const pagination = page.getByRole("region", { name: "Flood event pagination", exact: true });
  await expect(list.locator("article")).toHaveCount(20);
  await openMap(page);
  await mapLayers(page, { zoom: 14 });
  await expect.poll(async () => ((await mapLayers(page))?.sources["historical-flood-events-source"] as { data: { features: unknown[] } })?.data.features.length).toBe(45);
  const initial = (await mapLayers(page))!;
  expect((initial.sources["historical-flood-events-source"] as { data: { features: unknown[] } }).data.features).toHaveLength(45);
  if (info.project.name === "mobile-chromium") await page.getByRole("button", { name: "List", exact: true }).click();
  const next = () => pagination.getByRole("button", { name: info.project.name === "mobile-chromium" ? "Next" : "Next Page", exact: true });
  await next().click();
  await expect(pagination.getByRole("status")).toContainText("Page 2 of 3");
  await expect(list.locator("article")).toHaveCount(20);
  await expect(pagination).toBeInViewport();
  await page.screenshot({ path: info.outputPath("history-page-two.png") });
  await list.locator('[aria-busy]').evaluate(element => { element.scrollTop = element.scrollHeight; });
  await next().click();
  await expect(pagination.getByRole("status")).toContainText("Page 3 of 3");
  await expect(list.locator("article")).toHaveCount(5);
  await expect(next()).toBeDisabled();
  expect(await list.locator('[aria-busy]').evaluate(element => element.scrollTop)).toBe(0);
  const after = (await mapLayers(page))!;
  expect(after.center).toEqual(initial.center);
  expect((after.sources["historical-flood-events-source"] as { data: { features: unknown[] } }).data.features).toHaveLength(45);
  await page.getByLabel("Search events").fill("Pagination Road");
  await expect(pagination.getByRole("status")).toContainText("1 event · Up to 20 per page · Page 1 of 1");
  await expect(list.locator("article")).toHaveCount(1);
  await expect(pagination.getByRole("button")).toHaveCount(0);
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await expect(list.locator("article")).toHaveCount(20);
  await expect(pagination.getByRole("status")).toContainText("Page 1 of 3");
  expect(state.historyRequests.filter(parameters => parameters.has("page")).every(parameters => parameters.get("page_size") === "20")).toBe(true);
  await expectNoOverflow(page);
  await pagination.scrollIntoViewIfNeeded();
  await expect(pagination).toBeVisible();
  await page.screenshot({ path: info.outputPath("history-shared-pagination.png") });
  expect(state.writes).toEqual([]);
  expect(state.errors).toEqual([]);
});

test("off-page map selection opens the containing page and page failures can retry", async ({ page }, info) => {
  const state = await setup(page, pagedEvents);
  const list = page.getByRole("region", { name: "Flood event list", exact: true });
  const pagination = page.getByRole("region", { name: "Flood event pagination", exact: true });
  await openMap(page);
  const last = pagedEvents[44], centre: [number, number] = [121.08 + 44 * .002 + .0005, 14.5705];
  await mapLayers(page, { zoom: 16, center: centre });
  await expect.poll(async () => (await mapLayers(page))?.rendered.some(feature => feature.layer === fill && feature.properties?.event_id === last.id)).toBe(true);
  const canvas = page.locator('[aria-label="Historical flood map"] .maplibregl-canvas');
  const bounds = (await canvas.boundingBox())!;
  await canvas.click({ position: { x: bounds.width / 2, y: bounds.height / 2 } });
  await expect(pagination.getByRole("status")).toContainText("Page 3 of 3");
  await expect(list.locator(`article[data-event-id="${last.id}"]`)).toHaveClass(/bg-blue/);
  expect(state.historyRequests.some(parameters => parameters.get("focus_event_id") === String(last.id))).toBe(true);
  await page.route(`**/api/v1/admin/flood-events/${last.id}/inspection`, route => route.fulfill({ json: last }));
  await page.route(`**/api/v1/admin/flood-events/${last.id}/inspection/locations?*`, route => route.fulfill({ json: {
    items: last.locations, total: last.locations.length, page: 1, pages: 1, page_size: 20,
  } }));
  await list.locator(`article[data-event-id="${last.id}"]`).getByRole("button", { name: "View event", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Flood Event Details" })).toBeVisible();
  await page.getByRole("button", { name: "Close flood event details", exact: true }).click();
  await expect(pagination.getByRole("status")).toContainText("Page 3 of 3");
  state.controls.pageError = true;
  await pagination.getByRole("button", { name: info.project.name === "mobile-chromium" ? "Previous" : "Previous Page", exact: true }).click();
  await expect(list.getByRole("alert")).toContainText("Fixture page storage unavailable");
  state.controls.pageError = false;
  await list.getByRole("button", { name: "Retry records", exact: true }).click();
  await expect(pagination.getByRole("status")).toContainText("Page 2 of 3");
  await expect(list.locator("article")).toHaveCount(20);
  await expectNoOverflow(page);
  expect(state.writes).toEqual([]);
  expect(state.errors).toEqual([]);
});

test("initial footprints and filtered heatmap share the records and equal desktop columns", async ({page},info) => {
  const state=await setup(page);
  await expect(page.getByRole("region", { name: "Flood event list", exact: true }).locator("article")).toHaveCount(2);
  if (info.project.name === "mobile-chromium") expect(state.historyRequests).toHaveLength(1);
  expect(state.historyRequests.every(params => !params.has("limit"))).toBe(true);
  if (info.project.name==="desktop-chromium") {
    const children=page.getByTestId("flood-event-records-layout").locator(":scope > div");
    const a=await children.nth(0).boundingBox(),b=await children.nth(1).boundingBox();
    expect(Math.abs(a!.width-b!.width)).toBeLessThanOrEqual(1);
  }
  await openMap(page);
  await expect.poll(() => state.historyRequests.length).toBeGreaterThanOrEqual(2);
  let snapshot=(await mapLayers(page))!;
  expect(snapshot.zoom).toBeLessThan(14);
  const data=snapshot.sources["historical-flood-heatmap-source"] as {data:{features:unknown[]}};
  expect(data.data.features).toHaveLength(2);
  expect(snapshot.layers.some(layer=>layer.id==="historical-flood-events-outline")).toBe(false);
  await mapLayers(page,{zoom:14,center:[121.0805,14.5705]});
  await expect.poll(async ()=>(await mapLayers(page))?.rendered.some(feature=>feature.layer===fill)).toBe(true);
  await mapLayers(page,{zoom:15});
  await expect.poll(async ()=>(await mapLayers(page))?.rendered.some(feature=>feature.layer===heat)).toBe(false);
  await expect(page.getByText("Stronger fill: selected event")).toBeVisible();
  await page.screenshot({path:info.outputPath("history-shared-polygon-style.png")});
  if(info.project.name==="mobile-chromium") await page.getByRole("button",{name:"List",exact:true}).click();
  await page.getByLabel("Search events").fill("Historical Road 0");
  await openMap(page);
  await expect.poll(async () => ((await mapLayers(page))?.sources["historical-flood-events-source"] as { data: { features: unknown[] } })?.data.features.length).toBe(1);
  await mapLayers(page, { zoom: 12 });
  await expect.poll(async()=> ((await mapLayers(page))?.sources["historical-flood-heatmap-source"] as {data:{features:unknown[]}})?.data.features.length).toBe(1);
  snapshot=(await mapLayers(page))!;
  expect(snapshot.center[0]).toBeLessThan(121.09);
  await mapLayers(page,{pan:true});
  const center=(await mapLayers(page))!.center;
  expect((await mapLayers(page))!.center).toEqual(center);
  await expectNoOverflow(page);
  expect(state.writes).toEqual([]);
  expect(state.errors).toEqual([]);
});

test("style reload restores layers, failures are visible, and detail map handoffs survive", async ({page},info)=>{
  const state=await setup(page);
  await openMap(page);
  await mapLayers(page,{failHeatmap:true,reloadStyle:true});
  await expect(page.getByRole("alert").filter({hasText:"heatmap could not be drawn"})).toBeVisible();
  await mapLayers(page,{restore:true,reloadStyle:true});
  await expect.poll(async()=>(await mapLayers(page))?.layers.some(layer=>layer.id===heat)).toBe(true);
  await expect(page.getByRole("alert").filter({hasText:"heatmap could not be drawn"})).toHaveCount(0);
  if(info.project.name==="mobile-chromium") await page.getByRole("button",{name:"List",exact:true}).click();
  await page.getByRole("button",{name:"View event",exact:true}).first().click();
  await page.getByRole("button",{name:"View on historical map",exact:true}).click();
  await expect.poll(async()=>(await mapLayers(page))?.center[0]).toBeLessThan(121.09);
  await expectNoOverflow(page);
  expect(state.writes).toEqual([]);
  expect(state.errors).toEqual([]);
});

test("320 px switching and empty or unmapped records remain usable",async({page},info)=>{
  const state=await setup(page);
  if(info.project.name==="mobile-chromium") await page.setViewportSize({width:320,height:740});
  await openMap(page);
  await page.screenshot({path:info.outputPath("history-heatmap-overview.png")});
  await page.getByLabel("Search events").fill("nothing");
  await expect(page.getByText("No historical flood shapes match these filters.")).toBeVisible();
  state.setUnmapped();
  await page.getByLabel("Search events").fill("unmapped");
  await expect(page.getByText(/These records have no valid mapped footprints/)).toBeVisible();
  if(info.project.name==="mobile-chromium") await page.getByRole("button",{name:"List",exact:true}).click();
  await expect(page.getByText("Flood Event #920",{exact:true})).toBeVisible();
  await expectNoOverflow(page);
  expect(state.writes).toEqual([]);
});

test("individual historical zone and supporting report focus preserve their own geometry",async({page},info)=>{
  const state=await setup(page);
  if(info.project.name==="mobile-chromium") await page.setViewportSize({width:320,height:740});
  await openMap(page);
  await mapLayers(page,{zoom:15});
  await expect.poll(async()=>(await mapLayers(page))?.sourceCounts["historical-flood-events-source"]).toBe(2);
  const reportGeometry={type:"LineString",coordinates:[[121.0801,14.5701],[121.0808,14.5708]]};
  await page.route("**/api/v1/admin/flood-events/920/inspection",route=>route.fulfill({json:{...events[0],supporting_report_count:1,reports:[{
    id:950,status:"approved",source:"user_report",severity:"high",depth:"knee",raw_text:"Original historical report evidence",
    reporter_name:"Historical witness",created_at:"2026-10-20T00:00:00Z",geometry:reportGeometry,media_urls:[],
  }]}}));
  await page.route("**/api/v1/admin/flood-events/920/inspection/reports?*", route => route.fulfill({ json: { items: [{
    id:950,status:"approved",source:"user_report",severity:"high",depth:"knee",raw_text:"Original historical report evidence",
    reporter_name:"Historical witness",created_at:"2026-10-20T00:00:00Z",geometry:reportGeometry,media_urls:[],
  }], total: 1, page: 1, pages: 1, page_size: 20 } }));
  for(const kind of ["zone","report","zone","zone"]){
    await mapLayers(page,{pan:true});
    const before=(await mapLayers(page))!;
    const baseSource=before.sources["historical-flood-events-source"];
    const basePaint=before.layers.find(layer=>layer.id===fill)?.paint;
    if(info.project.name==="mobile-chromium") await page.getByRole("button",{name:"List",exact:true}).click();
    await page.getByRole("button",{name:"View event",exact:true}).first().click();
    const dialog=page.getByRole("dialog",{name:"Flood Event Details"});
    if(kind==="zone"){
      await dialog.getByRole("button",{name:"Official history",exact:true}).click();
      await dialog.getByRole("button",{name:"View zone on map",exact:true}).click();
    }else{
      await dialog.getByRole("button",{name:"Reports (1)",exact:true}).click();
      await dialog.getByRole("button",{name:"View report 950 details",exact:true}).click();
      await dialog.getByRole("button",{name:"View on Map",exact:true}).click();
    }
    await expect(dialog).toBeHidden();
    await expect.poll(async()=>(await mapLayers(page))?.center[0]).toBeLessThan(121.082);
    await expect.poll(async()=>(await mapLayers(page))?.zoom).toBeGreaterThan(14);
    if(kind==="zone"){
      for(const reload of [false,true]){
        if(reload) await mapLayers(page,{reloadStyle:true});
        await expect.poll(async()=>(await mapLayers(page))?.sourceCounts["historical-flood-focus-source"]).toBe(0);
        await expect.poll(async()=>(await mapLayers(page))?.sources["historical-flood-events-source"]).toEqual(baseSource);
        expect((await mapLayers(page))!.layers.find(layer=>layer.id===fill)?.paint).toEqual(basePaint);
      }
    }else{
      await expect.poll(async()=>((await mapLayers(page))?.sources["historical-flood-focus-source"] as {data:{features:{geometry:unknown}[]}})?.data.features[0]?.geometry)
        .toEqual(reportGeometry);
    }
  }
  await expectNoOverflow(page);
  expect(state.writes).toEqual([]);
  expect(state.errors).toEqual([]);
});
