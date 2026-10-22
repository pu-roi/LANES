import { expect as baseExpect, test } from "@playwright/test";
import { installChrisFixtures } from "./helpers/chrisIntegration";
import { mapLayers } from "./helpers/mapLayers";

const expect = baseExpect.configure({ timeout: 20_000 });
test.setTimeout(120_000);
test.use({ browserName: "chromium", actionTimeout: 30_000 });
for (const target of ["public", "admin"] as const) {
  test(`${target} Analytics retains shared heatmap visibility and style recovery`, async ({ page }, info) => {
    const state = await installChrisFixtures(page, target === "admin" ? "Admin" : "Commuter");
    await page.route("**/api/v1/analytics/stats", route => route.fulfill({ json: { top_barangays: [], top_locations: [] } }));
    await page.route("**/api/v1/analytics/heatmap", route => route.fulfill({ json: { type: "FeatureCollection", features: [
      { type: "Feature", geometry: { type: "Point", coordinates: [121.08,14.57] }, properties: { weight: 3 } },
    ] } }));
    await page.goto(target === "public" ? "/map?panel=analytics" : "/admin/map");
    if (target === "admin") {
      if (info.project.name === "mobile-chromium") await page.getByRole("button", { name: "Open map", exact: true }).click();
      await page.getByTitle("Toggle Analytics", { exact: true }).click();
    }
    await expect.poll(async () => (await mapLayers(page))?.layers.some(layer => layer.id === "heatmap-layer")).toBe(true);
    const paint = (await mapLayers(page))!.layers.find(layer => layer.id === "heatmap-layer")!;
    expect(paint.maxzoom).toBe(15);
    await mapLayers(page, { zoom: 13, reloadStyle: true });
    await expect.poll(async () => (await mapLayers(page))?.layers.some(layer => layer.id === "heatmap-layer")).toBe(true);
    await page.getByRole("button", { name: "Close panel", exact: true }).filter({ visible: true }).last().click();
    await expect.poll(async () => (await mapLayers(page))?.layers.some(layer => layer.id === "heatmap-layer")).toBe(false);
    expect(state.errors).toEqual([]);
  });
}
