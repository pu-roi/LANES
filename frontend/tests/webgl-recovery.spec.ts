import { expect, test, type Page } from "@playwright/test";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
} });

async function setup(page: Page, blocked: boolean) {
  await page.addInitScript(({ blocked }) => {
    const state = window as unknown as { blockMapGraphics: boolean; graphicsCanvases: Set<HTMLCanvasElement> };
    state.blockMapGraphics = blocked;
    state.graphicsCanvases = new Set();
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(this: HTMLCanvasElement, id: string, options?: unknown) {
      if (id === "webgl2" || id === "webgl" || id === "experimental-webgl") {
        state.graphicsCanvases.add(this);
        if (state.blockMapGraphics) {
          this.dispatchEvent(new WebGLContextEvent("webglcontextcreationerror", { statusMessage: "Web page caused context loss and was blocked" }));
          return null;
        }
      }
      return Reflect.apply(original, this, [id, options]);
    } as typeof original;
  }, { blocked });
  await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }],
  } }));
  await page.route("**/api/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/news/alerts")) return route.fulfill({ json: { items: [], total: 0, pages: 0, page: 1, page_size: 10 } });
    if (path.endsWith("/feed")) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    return route.fulfill({ json: [] });
  });
}

test("blocked WebGL shows a recoverable map error without crashing or looping", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await setup(page, true);
  await page.goto("/map");
  await expect(page.getByRole("heading", { name: "Map unavailable", exact: true })).toBeVisible();
  await expect(page.getByText("Loading map...", { exact: true })).toHaveCount(0);
  expect(await page.locator(".maplibregl-canvas").count()).toBe(0);
  expect(await page.evaluate(() => (window as unknown as { graphicsCanvases: Set<HTMLCanvasElement> }).graphicsCanvases.size)).toBe(1);
  // A failed retry is handled too, and each attempt clears its partial canvas.
  await page.getByRole("button", { name: "Retry map", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Map unavailable", exact: true })).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { graphicsCanvases: Set<HTMLCanvasElement> }).graphicsCanvases.size)).toBe(2);
  await page.screenshot({ path: testInfo.outputPath("blocked-webgl.png") });
  await page.evaluate(() => { (window as unknown as { blockMapGraphics: boolean }).blockMapGraphics = false; });
  await page.getByRole("button", { name: "Retry map", exact: true }).click();
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Map unavailable", exact: true })).toHaveCount(0);
  await expect(page.getByText("Loading map...", { exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => (window as unknown as { graphicsCanvases: Set<HTMLCanvasElement> }).graphicsCanvases.size)).toBe(3);
  expect(errors).toEqual([]);
});

test("an existing map reports context loss and recovers with the browser", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await setup(page, false);
  await page.goto("/map");
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await expect(page.getByText("Loading map...", { exact: true })).toHaveCount(0);
  await page.locator(".maplibregl-canvas").evaluate(canvas => {
    const gl = (canvas as HTMLCanvasElement).getContext("webgl2") || (canvas as HTMLCanvasElement).getContext("webgl");
    const extension = gl?.getExtension("WEBGL_lose_context");
    if (!extension) throw new Error("Test browser does not support simulated context loss");
    (window as unknown as { lostGraphics: WEBGL_lose_context }).lostGraphics = extension;
    extension.loseContext();
  });
  await expect(page.getByRole("heading", { name: "Map unavailable", exact: true })).toBeVisible();
  await expect(page.getByText(/browser interrupted the map's graphics/)).toBeVisible();
  await page.evaluate(() => (window as unknown as { lostGraphics: WEBGL_lose_context }).lostGraphics.restoreContext());
  await expect(page.getByRole("heading", { name: "Map unavailable", exact: true })).toHaveCount(0);
  expect(await page.locator(".maplibregl-canvas").count()).toBe(1);
  expect(errors).toEqual([]);
});
