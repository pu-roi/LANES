import { expect as baseExpect, test, type Page } from "@playwright/test";
import { installChrisFixtures, expectNoOverflow, fixtureZone, zoneMapResponse } from "./helpers/chrisIntegration";
import { mapLayers } from "./helpers/mapLayers";

const expect = baseExpect.configure({ timeout: 30_000 });

test.setTimeout(120_000);
test.use({ browserName: "chromium", reducedMotion: "reduce", launchOptions: {
  args: ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"],
} });

const date = "2026-10-25T01:00:00Z";
const zone = { ...fixtureZone, id: 92, name: "Reviewed Riverside road", report_source: "news",
  location_label: "Reviewed Riverside road, Quezon City", report_text: "Saved reported flood",
  geometry: { type: "Polygon", coordinates: [[[121.0112,14.6428],[121.0117,14.6428],[121.0117,14.6433],[121.0112,14.6433],[121.0112,14.6428]]] } };
const claim = { raw_place_name: zone.name, canonical_road: zone.name, canonical_city: "Quezon City", evidence_sentence: "Reported flooding at Riverside.", condition: "active" };
const item = { key: "401:group:resolved-n5", run_id: 401, group_id: "resolved-n5", claim_index: 5,
  result_kind: "ner_group", article_id: 274, article_version_id: 573, publisher: "Fixture publisher", title: "Saved flood article",
  captured_at: date, published_at: date, saved_at: date, claim,
  summary: { location: zone.name, area: "Quezon City", water_level: "19 inches", condition: "Flooding reported",
    flood_time: date, flood_time_label: "Flood observed in article", map_status: "Estimated zone plotted", reading_reason: null } };

async function setup(page: Page, options: { failed?: boolean; unplotted?: boolean; ordinalFree?: boolean; inactive?: boolean } = {}) {
  const fixtures = await installChrisFixtures(page, "Admin");
  const writes: string[] = [];
  const targetReads: string[] = [];
  let failed = !!options.failed;
  await page.route("**/news-simulation.local.json", route => route.fulfill({ status: 404, body: "" }));
  await page.route("**/api/v1/admin/**", async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (route.request().method() !== "GET") writes.push(path);
    if (path.endsWith("/auth/test-token")) return route.fallback();
    if (path.endsWith("/map-target")) {
      targetReads.push(url.search);
      if (failed) { failed = false; return route.fulfill({ status: 503, json: { detail: "Saved flood zone links are unavailable. Please retry." } }); }
      return route.fulfill({ json: { zone_id: options.unplotted ? null : 92, claim_index: options.ordinalFree ? null : 5, read_only: true } });
    }
    if (path.endsWith("/news/results")) return route.fulfill({ json: { items: [{ ...item, claim_index: options.ordinalFree ? null : 5 }], total: 1, page: 1, pages: 1, page_size: 12, publishers: [], scope: "latest_reported_locations" } });
    if (path.includes("/news/results/401/")) return route.fulfill({ json: { item, claim, captured_input: {
      title: item.title, publisher: item.publisher, canonical_url: "https://example.org/flood", article_text: claim.evidence_sentence, published_at: date }, extraction_errors: [] } });
    if (path.endsWith("/news/automation")) return route.fulfill({ json: { state: "not_recorded", status_label: "No worker cycle recorded",
      read_only: true, checked_at: date, queue_counts: {}, stages: {}, feed_counts: {}, running: false, enabled_sources: 0, collection_interval_minutes: 30 } });
    if (path.endsWith("/zones/92")) {
      await new Promise(resolve => setTimeout(resolve, 500));
      return route.fulfill({ json: { ...zone, is_active: !options.inactive } });
    }
    if (path.endsWith("/zones/groups/92/members")) return route.fulfill({ json: { zone_id: 92, zones: [zone], total: 1, zone_total: 2,
      page: 1, pages: 1, page_size: 20, group_reason: "Saved linked road", read_only: true } });
    // The current list/map viewport contains only an unrelated zone. The URL
    // handoff must fetch the linked identity rather than select the first row.
    if (path.endsWith("/zones/map")) return route.fulfill({ json: zoneMapResponse([fixtureZone], url.href) });
    if (path.endsWith("/review/items")) return route.fulfill({ json: { items: [], total: 0, counts: { all: 0 }, read_only: true } });
    return route.fallback();
  });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await page.getByRole("tab", { name: "Flooded Areas", exact: true }).click();
  await page.getByRole("button", { name: `Info: ${zone.name}` }).click();
  return { ...fixtures, writes, targetReads };
}

for (const ordinalFree of [false, true]) test(`Inspect placement selects and flies to the linked active zone (${ordinalFree ? "native group without ordinal" : "projected claim"})`, async ({ page }, info) => {
  const { writes, targetReads } = await setup(page, { ordinalFree });
  await page.getByRole("button", { name: "Inspect placement on map", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/map\?tab=zones&focus_zone_id=92$/);
  await expect(page.getByRole("dialog", { name: "News Flood Details" })).toHaveCount(0);
  await expect(page.locator("canvas.maplibregl-canvas")).toBeVisible();
  await expect.poll(async () => (await mapLayers(page))?.rendered.some(feature =>
    feature.properties.id === 92 && feature.properties.is_selected === true), { timeout: 30_000 }).toBe(true);
  await expect.poll(async () => (await mapLayers(page))?.center[0]).toBeCloseTo(121.01145, 3);
  await expect.poll(async () => (await mapLayers(page))?.center[1]).toBeCloseTo(14.64305, 3);
  const camera = (await mapLayers(page))!;
  expect(camera.center[0]).toBeCloseTo(121.01145, 3);
  expect(camera.center[1]).toBeCloseTo(14.64305, 3);
  expect(camera.zoom).toBeGreaterThan(14);
  expect(targetReads).toEqual(["?group_id=resolved-n5"]);
  await page.screenshot({ path: info.outputPath("linked-zone-map.png"), scale: "css" });
  if (info.project.name === "mobile-chromium") await page.getByRole("button", { name: "Back to zones", exact: true }).filter({ visible: true }).click();
  await expect(page.getByRole("region", { name: "Active Zones", exact: true })).toBeVisible();
  await expect(page.getByRole("article", { name: "Zone #92", exact: true })).toHaveClass(/bg-blue-50/);
  await expectNoOverflow(page);
  expect(writes).toEqual([]);
});

test("placement lookup errors remain in the modal and retry navigates successfully", async ({ page }) => {
  await setup(page, { failed: true });
  const action = page.getByRole("button", { name: "Inspect placement on map", exact: true });
  await action.click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("Saved flood zone links are unavailable");
  await expect(page).toHaveURL(/\/admin\/news$/);
  await action.click();
  await expect(page).toHaveURL(/focus_zone_id=92/);
});

test("unplotted observations keep the saved placement review path", async ({ page }) => {
  await setup(page, { unplotted: true });
  await page.getByRole("button", { name: "Inspect placement on map", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/map\?review_news=401:5$/);
});

test("a zone deactivated after the news lookup surfaces a visible error", async ({ page }) => {
  await setup(page, { inactive: true });
  await page.getByRole("button", { name: "Inspect placement on map", exact: true }).click();
  await expect(page.getByText("The linked flood zone is no longer active.", { exact: true })).toBeVisible();
});
