import { expect, test, type Page } from "@playwright/test";

test.setTimeout(90_000);
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
} });

async function setup(page: Page) {
  const state = { queueError: false, membersError: false, gone: false };
  const writes: { path: string; body: unknown }[] = [];
  const requests: Record<string, string>[] = [];
  const zones = Array.from({ length: 25 }, (_, index) => ({
    id: index + 9, name: `Bridge section ${index + 9}`, report_id: index + 50, is_active: true,
    created_at: "2026-10-21T01:00:00Z", updated_at: "2026-10-21T01:00:00Z", expires_at: "2099-01-01T00:00:00Z",
    severity: index === 1 ? "high" : "medium", depth: index === 1 ? "waist" : "knee",
    report_source: index % 3 === 0 ? "direct_user" : index % 3 === 1 ? "news" : null,
    report_text: `Saved evidence for section ${index + 9}`, contributors: [],
    geometry: { type: "Polygon", coordinates: [[[121.08,14.57],[121.0801,14.57],[121.0801,14.5701],[121.08,14.57]]] },
  }));
  const group = { zone_id: 9, member_count: 25, location: "Bridge flood sections", area_summary: "Maybunga · Rosario, Pasig",
    sources: ["user_reports", "news", "official"], severity_levels: ["medium", "high"], depth_levels: ["knee", "waist"],
    queued_at: zones[0].created_at, evidence: zones[0].report_text, group_reason: "Nearby active zone boundaries; each zone retains its own evidence and actions." };
  const cards = [group, ...Array.from({ length: 21 }, (_, index) => ({ ...group, zone_id: 100 + index,
    member_count: 1, location: `Separate location ${index}`, sources: ["official"] }))];
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: { version: 8, sources: {}, layers: [
    { id: "background", type: "background", paint: { "background-color": "#f1f5f9" } },
  ] } }));
  await page.route("**/api/v1/**", route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    let body: unknown = [];
    if (route.request().method() !== "GET" && !path.endsWith("/auth/test-token")) {
      writes.push({ path, body: route.request().postData() ? route.request().postDataJSON() : null });
    }
    if (path.endsWith("/auth/test-token")) body = { id: 7, username: "admin", is_active: true, role: { name: "Super Admin", id: 1 } };
    else if (path.endsWith("/notifications")) body = { notifications: [], total: 0, unread_count: 0, has_more: false };
    else if (path.endsWith("/admin/review/items")) body = { items: [], zones: [], total: 0, page: 1, pages: 1, read_only: true, counts: { all: 0, user_reports: 0, news_claims: 0 } };
    else if (path.endsWith("/admin/zones/queue")) {
      requests.push(Object.fromEntries(url.searchParams));
      if (state.queueError) return route.fulfill({ status: 503, json: { detail: "Queue storage offline" } });
      const p = Number(url.searchParams.get("page") || 1);
      const filtered = ["q", "city", "barangay", "severity"].some(key => url.searchParams.get(key)) || (url.searchParams.get("source") || "all") !== "all";
      const items = state.gone || url.searchParams.get("q") === "nothing" ? [] : filtered ? [group] : cards;
      const history = url.searchParams.get("active_only") === "false";
      body = { items: items.slice((p - 1) * 20, p * 20), zones: history ? zones.slice((p - 1) * 20, p * 20) : [],
        total: history ? 25 : items.length, item_total: items.length ? 25 + items.length - 1 : 0,
        counts: { all: 46, user_reports: 9, news: 8, official: 29, other: 0 },
        facets: { cities: ["Pasig"], barangays: ["Maybunga", "Rosario"] }, page: p,
        pages: history ? 2 : Math.max(1, Math.ceil(items.length / 20)), page_size: 20, read_only: true };
    } else if (/\/admin\/zones\/groups\/\d+\/members$/.test(path)) {
      if (state.gone) return route.fulfill({ status: 404, json: { detail: "This group is no longer active." } });
      if (state.membersError) return route.fulfill({ status: 503, json: { detail: "Group storage offline" } });
      const p = Number(url.searchParams.get("page") || 1);
      body = { zone_id: 9, zones: zones.slice((p - 1) * 20, p * 20), total: 25, page: p, pages: 2,
        page_size: 20, group_reason: group.group_reason, read_only: true };
    } else if (/\/admin\/zones\/\d+$/.test(path)) body = zones.find(zone => zone.id === Number(path.split("/").pop()));
    else if (path.endsWith("/reports/active-zones")) body = zones;
    else if (path.endsWith("/admin/zone-updates/counts")) body = {};
    else if (path.endsWith("/deactivate-bulk")) body = { message: "Zones deactivated", count: 2 };
    else if (path.endsWith("/deactivate")) body = zones[0];
    return route.fulfill({ json: body });
  });
  await page.goto("/admin/map");
  await page.getByRole("button", { name: /Active Zones/ }).click();
  const panel = page.getByRole("region", { name: "Active Zones", exact: true });
  await expect(panel.getByRole("button", { name: "Inspect zone group: Bridge flood sections", exact: true })).toBeVisible();
  return { panel, state, writes, requests, zones };
}

test("group cards share filters and preserve the full group, queue page and scroll", async ({ page }, info) => {
  const { panel, writes, requests } = await setup(page);
  const search = panel.getByRole("searchbox", { name: "Search zone queue" });
  await search.fill("section 33");
  await expect.poll(() => requests.some(request => request.q === "section 33")).toBe(true);
  await panel.getByRole("button", { name: "Filters", exact: true }).click();
  await panel.getByLabel("Filter by city", { exact: true }).click();
  await page.getByRole("button", { name: "Pasig", exact: true }).click();
  await panel.getByLabel("Filter by barangay", { exact: true }).click();
  await page.getByRole("button", { name: "Rosario", exact: true }).click();
  await panel.getByLabel("Filter by severity", { exact: true }).click();
  await page.getByRole("button", { name: "High", exact: true }).click();
  await panel.getByRole("group", { name: "Zone source" }).getByRole("button", { name: /^News/ }).click();
  await expect.poll(() => requests.some(request => request.q === "section 33" && request.city === "Pasig" && request.barangay === "Rosario" && request.severity === "high" && request.source === "news")).toBe(true);
  await expect(panel.getByText("25 zones · 1 zone card")).toBeVisible();
  if (info.project.name === "mobile-chromium") await page.setViewportSize({ width: 320, height: 740 });
  expect(await panel.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("zone-queue-filters.png") });
  await panel.getByRole("button", { name: "Inspect zone group: Bridge flood sections", exact: true }).click();
  await expect(panel.getByRole("article", { name: "Zone #9", exact: true })).toBeVisible();
  await expect(panel.getByRole("checkbox", { name: "Select Zone #9", exact: true })).not.toBeChecked();
  await panel.getByRole("button", { name: "Back to queue", exact: true }).click();
  await expect(search).toHaveValue("section 33");
  await expect(panel.getByLabel("Filter by barangay", { exact: true })).toHaveText("Rosario");
  await expect(panel.getByRole("button", { name: "Inspect zone group: Bridge flood sections", exact: true })).toBeFocused();
  await panel.getByRole("button", { name: "Clear filters", exact: true }).click();
  await panel.getByRole("group", { name: "Zone source" }).getByRole("button", { name: /^All/ }).click();
  await panel.getByRole("button", { name: "Filters", exact: true }).click();
  await panel.getByRole("button", { name: /^Next( Page)?$/i }).click();
  const card = panel.getByRole("button", { name: "Inspect zone group: Separate location 19", exact: true });
  await card.click();
  await panel.getByRole("button", { name: "Back to queue", exact: true }).click();
  await expect(card).toBeVisible();
  await expect(card).toBeFocused();
  expect(writes).toEqual([]);
});

test("member pagination and bulk selection remain scoped to individual zones", async ({ page }, info) => {
  const { panel, writes } = await setup(page);
  await panel.getByRole("button", { name: "Inspect zone group: Bridge flood sections", exact: true }).click();
  await expect(panel.getByRole("article", { name: /^Zone #/ })).toHaveCount(20);
  await panel.getByRole("checkbox", { name: "Select all on this page", exact: true }).check();
  await expect(panel.getByRole("checkbox", { name: /^Select Zone #/ }).first()).toBeChecked();
  await panel.getByRole("button", { name: /^Next( Page)?$/i }).click();
  await expect(panel.getByRole("article", { name: /^Zone #/ })).toHaveCount(5);
  await expect(panel.getByRole("checkbox", { name: "Select all on this page", exact: true })).not.toBeChecked();
  await panel.getByRole("checkbox", { name: "Select Zone #33", exact: true }).check();
  if (info.project.name === "mobile-chromium") await page.setViewportSize({ width: 320, height: 740 });
  expect(await panel.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("zone-group-members.png") });
  await panel.getByRole("button", { name: "Back to queue", exact: true }).click();
  await panel.getByRole("button", { name: "All History", exact: true }).click();
  await expect(panel.getByRole("article", { name: /^Zone #/ })).toHaveCount(20);
  await expect(panel.getByRole("button", { name: /^Inspect zone group:/ })).toHaveCount(0);
  await expect(panel.getByRole("checkbox", { name: "Select all on this page", exact: true })).toBeChecked();
  expect(writes).toEqual([]);
});

test("queue errors, member retries and disappearing groups are visible", async ({ page }) => {
  const { panel, state, writes } = await setup(page);
  state.queueError = true;
  await panel.getByRole("button", { name: "Refresh zone queue", exact: true }).click();
  await expect(panel.getByRole("alert")).toContainText("Queue storage offline");
  state.queueError = false;
  await panel.getByRole("button", { name: "Retry zone queue", exact: true }).click();
  state.membersError = true;
  await panel.getByRole("button", { name: "Inspect zone group: Bridge flood sections", exact: true }).click();
  await expect(panel.getByRole("alert")).toContainText("Group storage offline");
  state.membersError = false;
  await panel.getByRole("button", { name: "Retry zone group", exact: true }).click();
  await expect(panel.getByRole("article", { name: "Zone #9", exact: true })).toBeVisible();
  state.gone = true;
  await panel.getByRole("button", { name: "Refresh zone queue", exact: true }).click();
  await expect(panel.getByRole("alert")).toContainText("no longer active");
  await expect(panel.getByRole("article", { name: /^Zone #/ })).toHaveCount(0);
  await panel.getByRole("button", { name: "Back to queue", exact: true }).click();
  await expect(panel.getByText("No zones match this view.", { exact: true })).toBeVisible();
  expect(writes).toEqual([]);
});

test("bulk deactivation requires confirmation and uses only explicitly selected IDs", async ({ page }) => {
  const { panel, writes } = await setup(page);
  await panel.getByRole("button", { name: "Inspect zone group: Bridge flood sections", exact: true }).click();
  await panel.getByRole("checkbox", { name: "Select Zone #9", exact: true }).check();
  await panel.getByRole("checkbox", { name: "Select Zone #10", exact: true }).check();
  await panel.getByRole("button", { name: "Deactivate Selected", exact: true }).click();
  const heading = page.getByRole("heading", { name: "Confirm Bulk Deactivation", exact: true });
  const dialog = heading.locator("..").locator("..");
  await expect(heading).toBeVisible();
  expect(writes).toEqual([]);
  await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
  await panel.getByRole("button", { name: "Deactivate Selected", exact: true }).click();
  await dialog.getByRole("button", { name: "Deactivate Selected", exact: true }).click();
  await expect.poll(() => writes).toEqual([{ path: "/api/v1/admin/zones/deactivate-bulk", body: { zone_ids: [9, 10] } }]);
  await expect(panel.getByRole("button", { name: "Clear selection", exact: true })).toHaveCount(0);
});
