import { expect as baseExpect, test, type Page } from "@playwright/test";
const expect = baseExpect.configure({ timeout: 30_000 });

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: {
  executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
} });

const claim = { raw_place_name: "Caruncho Avenue", canonical_city: "Pasig", canonical_barangay: null,
  canonical_road: "Caruncho Avenue", depth_raw: "knee-deep", depth_formatted: "Knee-deep", condition: "active",
  event_time_resolved: null, event_time_kind: "unspecified", evidence_sentence: "Knee-deep flooding was reported on Caruncho Avenue in Pasig.",
  uncertainty_reasons: ["observation_time_missing"], is_historical: false, is_forecast: false, is_negated: false,
  road_passability: "unknown", action_type: "flagged_review", action_rationale: "Exact affected section and observation time are unresolved.", road_placement: null };
const summary = { location: "Caruncho Avenue", area: "Pasig", location_qualifier: null, water_level: "Knee-deep",
  condition: "Flooding reported", flood_time: null, flood_time_label: "Flood observation time", passability: "Not stated",
  map_status: "Location suggestion available", reading_status: "reported_location", reading_reason: null };
const source = { title: "Pasig flooding report", canonical_url: "https://example.org/flood", publisher: "feedspot-01",
  excerpt: "", article_text: claim.evidence_sentence, published_at: "2026-10-04T02:00:00Z" };
const news = { item: { key: "2:0", run_id: 2, claim_index: 0, article_id: 8, article_version_id: 8,
  title: source.title, publisher_source_id: source.publisher, publisher: "Example News", published_at: source.published_at,
  saved_at: source.published_at, captured_at: source.published_at, extracted_at: source.published_at, claim, summary },
  claim, captured_input: source, input_fingerprint: "fixture", pipeline_version: "fixture-v10", extraction_errors: [],
  is_metadata_only: false, lifecycle_status: "not_available", read_only: true };
const report = { id: 2, raw_text: "Water is rising near the bridge.", source: "direct_user", severity: "medium", depth: "knee",
  city: "Pasig", barangay: "Maybunga", status: "pending", geometry: { type: "Point", coordinates: [121.08, 14.57] },
  media_urls: [], created_at: source.published_at, updated_at: source.published_at, reporter_name: "Test reporter" };
const candidates = [0, 1].map((index) => ({ candidate_id: `section-${index}`, kind: "road_section", centerline_geojson: {
  type: "LineString", coordinates: [[121.08 + index * .001, 14.57], [121.081 + index * .001, 14.571]],
}, osm_way_ids: [index + 1], cross_streets: [["Test crossing"]], ambiguous_carriageway: false, article_place_level: 1,
  approximate_length_m: 120, modeled_overlap_m: { "5": { "1": 60 } }, modeled_overlap_fraction: { "5": .5, "25": .7, "100": .8 },
  matching_history: index ? [] : [{ source_year: "2023", source_record_no: "19", barangay: "Maybunga", street: "Caruncho", landmark: "Test crossing" }] }));
const preview = { status: "ambiguous", reason: "competing_road_sections", selected_candidate_id: "section-0",
  placement_kind: "predicted", candidates, total_candidate_count: 2, candidates_truncated: false,
  osm_source_id: "fixture-osm", osm_catalog_sha256: "fixture-osm-hash", osm_snapshot_at: source.published_at,
  noah_catalog_sha256: "fixture-noah-hash", noah_source_ids: { "5": "fixture-noah" }, noah_attribution: "UP NOAH · fixture",
  history_status: "available", history_sha256: "fixture-history", unmatched_history: [], uncertainty_reasons: [],
  proves_current_flood: false, may_affect_routing: false, read_only: true };

// Inspect rendered pixels in the canvas interior, excluding map controls.
// The fixture basemap has no blue roads, so these pixels belong to suggestions.
async function suggestionPixels(page: Page) {
  const bounds = await page.locator(".maplibregl-canvas").boundingBox();
  if (!bounds || bounds.width < 600 || bounds.height < 160) return -1;
  const png = await page.screenshot({ clip: { x: bounds.x + 60, y: bounds.y + 60,
    width: bounds.width - 120, height: bounds.height - 120 } });
  return page.evaluate(async (base64) => {
    const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
    const canvas = document.createElement("canvas"); canvas.width = image.width; canvas.height = image.height;
    const context = canvas.getContext("2d")!; context.drawImage(image, 0, 0);
    const rgba = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let total = 0;
    for (let index = 0; index < rgba.length; index += 4) {
      if (rgba[index + 2] > 120 && rgba[index + 2] > rgba[index] * 1.3 && rgba[index + 2] > rgba[index + 1] * 1.05) total++;
    }
    return total;
  }, png.toString("base64"));
}

async function setup(page: Page, mode: "ready" | "unresolved" | "unavailable" | "limited" | "queue_error" | "grouped" | "large_group" | "separate_group" | "growth" | "growth_error" = "ready") {
  const writes: string[] = [];
  const sources: string[] = [];
  const mergePayloads: Record<string, unknown>[] = [];
  const previewControl = { unavailable: mode === "growth_error" };
  const growthReport = { ...report, geometry: candidates[0].centerline_geojson };
  const groupedMembers = Array.from({ length: mode === "large_group" ? 25 : 3 }, (_, index) => ({
    key: `user_report:${index + 2}`, source: "user_report", report_id: index + 2, run_id: null, claim_index: null,
    title: `Report #${index + 2}`, location: mode === "separate_group" && index === 1 ? "Other Street" : "Dr. Sixto Antonio Avenue", evidence: `Individual evidence ${index + 2}`,
    review_reason: "Pending user-report verification.", queued_at: source.published_at,
    severity: index === 1 ? "high" : "low", depth: index === 1 ? "waist" : "ankle",
  }));
  const grouping = ["grouped", "large_group", "separate_group"].includes(mode);
  const groupReason = "Nearby reports within 2 hours. Barangay boundaries do not exclude review. Confirm flood extent before merging.";
  const fullReport = (id: number) => {
    const member = groupedMembers.find((row) => row.report_id === id);
    return grouping ? { ...report, id, raw_text: member?.evidence, severity: member?.severity, depth: member?.depth,
      barangay: mode === "separate_group" && id === 3 ? "Rosario" : "Maybunga",
      geometry: mode === "separate_group" ? { type: "Point", coordinates: [121.08 + (id === 3 ? .0007 : id === 4 ? -.0007 : 0), 14.57] } : report.geometry,
    } : mode.startsWith("growth") ? growthReport : report;
  };
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api.maptiler.com/maps/**/style.json?**", (route) => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }],
  } }));
  await page.route("**/api/v1/**", (route) => {
    const url = new URL(route.request().url());
    const path = decodeURIComponent(url.pathname);
    if (route.request().method() !== "GET" && !path.endsWith("/auth/test-token") && !path.endsWith("/reports/merge-preview")) writes.push(path);
    let body: unknown = [];
    if (path.endsWith("/auth/test-token")) body = { id: 7, email: "test@example.org", username: "test", is_active: true,
      role: { id: 1, name: "Super Admin" }, profile: { first_name: "Test", last_name: "Staff" } };
    else if (path.endsWith("/reports/merge-candidates")) body = {
      primary_report: growthReport, candidates: [], total_candidates: 0, detected_conflicts: [],
      suggested_merged_geometry: null, zone_candidates: [{ zone_id: 9, event_id: 6,
        name: "Ongoing flood", distance_m: 20, severity: "medium", depth: "knee", match_reasons: [] }],
    };
    else if (path.endsWith("/reports/merge-preview")) {
      if (previewControl.unavailable) return route.fulfill({ status: 503, json: { detail: "Coverage preview is unavailable." } });
      const payload = route.request().postDataJSON();
      body = { geometry: { type: "Polygon", coordinates: [[[121.079,14.569],[121.083,14.569],[121.083,14.572],[121.079,14.572],[121.079,14.569]]] },
        reviewed_geometry: payload.final_data.geometry, source_geometry: payload.final_data.geometry,
        preserves_existing_coverage: payload.merge_mode !== "add_section", read_only: true };
    }
    else if (path.endsWith("/reports/merge")) {
      mergePayloads.push(route.request().postDataJSON());
      body = { message: "Reviewed update published", zone_id: 9, zone_name: "Ongoing flood", merged_count: 1,
        awarded_user_ids: [], zone: { id: 9, event_id: 6, severity: "medium", depth: "knee", geometry: report.geometry } };
    }
    else if (path.endsWith("/notifications")) body = { notifications: [], total: 0, unread_count: 0, has_more: false };
    else if (path.endsWith("/admin/zones")) body = { items: [], total: 0, page: 1, limit: 10, pages: 1 };
    else if (path.endsWith("/admin/reports/pending") && mode === "separate_group") body = groupedMembers.map((member) => fullReport(member.report_id));
    else if (path.includes("/admin/reports/detail/")) body = fullReport(Number(path.split("/").pop()));
    else if (/\/admin\/reports\/\d+\/approve$/.test(path)) {
      const id = Number(path.split("/").at(-2));
      const index = groupedMembers.findIndex((member) => member.report_id === id);
      if (index >= 0) groupedMembers.splice(index, 1);
      body = { ...report, id, status: "approved" };
    }
    else if (path.endsWith("/admin/review/items")) {
      if (mode === "queue_error") return route.fulfill({ status: 503, json: { detail: "Review queue storage is unavailable." } });
      const filter = url.searchParams.get("source") ?? "all"; sources.push(filter);
      const relatedMembers = mode === "separate_group" ? groupedMembers.filter((member) => member.report_id !== 3) : groupedMembers;
      const userRow = grouping ? { ...relatedMembers[0], member_count: relatedMembers.length, members: relatedMembers.slice(0, 3), group_reason: groupReason } :
        { key: "user_report:2", source: "user_report", report_id: 2, run_id: null, claim_index: null, title: "Report #2",
          location: "Maybunga bridge", evidence: report.raw_text, review_reason: "Pending user-report verification.", queued_at: source.published_at, severity: "medium", depth: "knee" };
      const rows = [{ key: "news_claim:2:0", source: "news_claim", report_id: null, run_id: 2, claim_index: 0,
        title: source.title, location: "Caruncho Avenue", evidence: claim.evidence_sentence, review_reason: claim.action_rationale, queued_at: source.published_at },
      userRow, ...(mode === "separate_group" ? [{ ...groupedMembers[1], member_count: 1, members: [], group_reason: null }] : [])];
      const items = rows.filter((row) => filter === "all" || row.source === (filter === "news_claims" ? "news_claim" : "user_report"));
      const userCount = grouping ? groupedMembers.length : 1;
      body = { items, total: items.length, item_total: filter === "all" ? userCount + 1 : filter === "news_claims" ? 1 : userCount,
        page: 1, pages: 1, page_size: 20, counts: { all: userCount + 1, news_claims: 1, user_reports: userCount }, read_only: true };
    } else if (path.endsWith("/items/news_claim:2:0")) body = { key: "news_claim:2:0", source: "news_claim", is_current_review: true, report: null, news, news_actions_available: false };
    else if (path.includes("/items/user_report:")) {
      const id = Number(path.split(":").pop());
      body = { key: `user_report:${id}`, source: "user_report", is_current_review: true,
        report: fullReport(id),
        news: null, news_actions_available: false };
    } else if (/\/groups\/user_report:\d+\/members$/.test(path)) {
      const selected = Number(path.split("/").at(-2)?.split(":").pop());
      const members = !grouping ? [groupedMembers[0]] : mode === "separate_group"
        ? groupedMembers.filter((member) => selected === 3 ? member.report_id === 3 : member.report_id !== 3) : groupedMembers;
      const memberPage = Number(url.searchParams.get("page") ?? 1);
      body = { key: members[0].key, items: members.slice((memberPage - 1) * 20, memberPage * 20), total: members.length,
        page: memberPage, page_size: 20, pages: Math.ceil(members.length / 20), group_reason: members.length > 1 ? groupReason : null, read_only: true };
    }
    else if (path.endsWith("/placement")) {
      if (mode === "limited") return route.fulfill({ status: 429, json: { detail: "Too many placement requests." } });
      body = { run_id: 2, claim_index: 0, input_fingerprint: "fixture", evidence_pipeline_version: "fixture-v10",
        placement_revision: "fixture-spatial", claim, read_only: true, preview: mode === "unresolved" ? {
          ...preview, status: "unresolved", reason: "no_supported_geometry", candidates: [], total_candidate_count: 0,
        } : mode === "unavailable" ? { ...preview, status: "source_unavailable", reason: "noah_unavailable", history_status: "source_unavailable" } : preview };
    }
    return route.fulfill({ status: 200, json: body });
  });
  await page.goto("/admin/map", { waitUntil: "domcontentloaded" });
  return { writes, sources, mergePayloads, previewControl };
}

test("mixed queue keeps news inspection separate from user-report actions", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const { writes, sources } = await setup(page);
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await expect(panel.getByRole("button", { name: "Inspect news claim: Caruncho Avenue" })).toBeVisible();
  await panel.getByRole("button", { name: /News Claims/ }).click();
  await expect(panel.getByRole("button", { name: "Inspect user report: Maybunga bridge" })).toHaveCount(0);
  await panel.getByRole("button", { name: "Inspect news claim: Caruncho Avenue" }).click();
  const suggestions = panel.getByRole("button", { name: /Inspect suggestion/ });
  await expect(suggestions).toHaveCount(2);
  await expect(suggestions.first()).toHaveAttribute("aria-pressed", "false");
  await expect(suggestions.last()).toHaveAttribute("aria-pressed", "false");
  await suggestions.last().click();
  await expect(suggestions.last()).toHaveAttribute("aria-pressed", "true");
  await expect(panel.getByRole("button", { name: "Approve", exact: true })).toHaveCount(0);
  await expect(panel.getByText(/do not confirm current flooding or change routing/)).toBeVisible();
  await panel.getByText("Full article text", { exact: true }).click();
  await expect(panel.getByRole("heading", { name: "Pasig flooding report" })).toBeVisible();
  if (info.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: "Open map", exact: true }).click();
    await expect(page.getByRole("button", { name: "Evidence", exact: true })).toBeVisible();
    await page.locator(".maplibregl-canvas").screenshot({ path: info.outputPath("news-candidate-map.png") });
    await page.getByRole("button", { name: "Evidence", exact: true }).click();
  }
  await page.screenshot({ path: info.outputPath("news-placement-inspection.png") });
  if (info.project.name === "desktop-chromium") {
    await expect.poll(() => suggestionPixels(page)).toBeGreaterThan(100);
    await page.locator(".maplibregl-canvas").screenshot({ path: info.outputPath("news-candidate-map.png") });
    await page.getByTitle("Change Map Style", { exact: true }).click();
    await page.getByRole("button", { name: /Dark/ }).click();
    await expect.poll(() => suggestionPixels(page)).toBeGreaterThan(100);
    await page.locator(".maplibregl-canvas").screenshot({ path: info.outputPath("news-candidate-after-style.png") });
  }
  await panel.getByRole("button", { name: "Back to queue" }).click();
  if (info.project.name === "desktop-chromium") {
    await expect.poll(() => suggestionPixels(page)).toBe(0);
    await page.locator(".maplibregl-canvas").screenshot({ path: info.outputPath("map-after-news-close.png") });
  }
  await expect(panel.getByRole("button", { name: /News Claims/ })).toHaveAttribute("aria-pressed", "true");
  await panel.getByRole("button", { name: /User Reports/ }).click();
  await panel.getByRole("button", { name: "Inspect user report: Maybunga bridge" }).click();
  await expect(panel.getByRole("button", { name: "Approve", exact: true })).toBeVisible();
  expect(sources).toContain("news_claims"); expect(sources).toContain("user_reports"); expect(writes).toEqual([]);
});

test("news inspection preserves the mounted Create Zone draft", async ({ page }, info) => {
  test.skip(info.project.name !== "desktop-chromium", "Desktop keeps the queue beside the draft workspace.");
  await page.setViewportSize({ width: 1440, height: 900 });
  await setup(page);
  await page.getByTitle("Create official zone", { exact: true }).click();
  const description = page.getByPlaceholder("e.g., Pumping truck stationed on westbound lane. Detour all light vehicles via Shaw Blvd.");
  await description.fill("Draft retained while inspecting news.");
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await panel.getByRole("button", { name: "Inspect news claim: Caruncho Avenue" }).click();
  await expect(panel.getByRole("button", { name: /Inspect suggestion 1/ })).toBeVisible();
  await page.getByTitle("Resume Create Zone draft", { exact: true }).click();
  await expect(description).toHaveValue("Draft retained while inspecting news.");
});

test("related reports open inside evidence without a queue dropdown", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const { writes } = await setup(page, "grouped");
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await expect(panel.getByText("4 reports requiring review · 2 review cards")).toBeVisible();
  const userCard = panel.getByRole("article", { name: "User report: Dr. Sixto Antonio Avenue · 3 related reports" });
  const newsCard = panel.getByRole("article", { name: "News claim: Caruncho Avenue" });
  await expect(userCard).toHaveClass(/bg-sky-50/);
  await expect(newsCard).toHaveClass(/bg-violet-50/);
  await page.screenshot({ path: info.outputPath("review-grouped-cards.png") });
  const opener = userCard.getByRole("button", { name: "Inspect user report: Dr. Sixto Antonio Avenue", exact: true });
  await expect(opener).not.toHaveAttribute("aria-expanded");
  await expect(userCard.getByRole("button")).toHaveCount(1);
  await opener.click();
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #2", { exact: true })).toBeVisible();
  const related = panel.getByRole("region", { name: "Related reports", exact: true });
  await expect(related.getByRole("region", { name: /Report #\d+ evidence/ })).toHaveCount(2);
  await expect(related.getByText("Report #2", { exact: true })).toHaveCount(0);
  const third = related.getByRole("region", { name: "Report #3 evidence", exact: true });
  for (const action of ["Info", "Review Merge Suggestions", "Reject", "Approve"]) {
    await expect(third.getByRole("button", { name: action, exact: true })).toBeVisible();
  }
  await expect(related.getByText("high", { exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath("review-related-in-detail.png") });
  await third.getByText(/Individual evidence 3/).click();
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #3", { exact: true })).toBeVisible();
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByRole("button", { name: "Approve", exact: true })).toBeVisible();
  await expect(third).toHaveCount(0);
  const fourth = related.getByRole("region", { name: "Report #4 evidence", exact: true });
  await expect(fourth.getByRole("button", { name: "Info", exact: true })).toBeVisible();
  await fourth.getByRole("button", { name: "Info", exact: true }).click();
  await expect(page.getByRole("dialog").getByText("#4", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close flood report details", exact: true }).click();
  if (info.project.name === "mobile-chromium") {
    await page.setViewportSize({ width: 320, height: 740 });
    await fourth.scrollIntoViewIfNeeded();
    expect(await related.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    await page.setViewportSize({ width: 844, height: 390 });
    await page.getByRole("button", { name: "Open map", exact: true }).click();
    await page.getByRole("button", { name: "Evidence", exact: true }).click();
    await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #3", { exact: true })).toBeVisible();
  }
  await panel.getByRole("button", { name: "Back to queue" }).click();
  await expect(related).toHaveCount(0);
  await expect(opener).toBeFocused();
  await newsCard.getByRole("button").click();
  await expect(panel.getByText("News claim · inspection only", { exact: true })).toBeVisible();
  await expect(related).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(writes).toEqual([]);
});

test("large related groups load members lazily and retain every paginated report", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const { writes } = await setup(page, "large_group");
  const requests: string[] = [];
  page.on("request", (request) => { if (request.url().includes("/members?")) requests.push(request.url()); });
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  const card = panel.getByRole("article", { name: /25 related reports/ });
  await expect(card).toBeVisible();
  expect(requests).toEqual([]);
  await card.getByRole("button").click();
  const related = panel.getByRole("region", { name: "Related reports", exact: true });
  await expect(related.getByRole("region", { name: /Report #\d+ evidence/ })).toHaveCount(19);
  if (info.project.name === "desktop-chromium") await related.getByTitle("Next Page", { exact: true }).click();
  else await related.getByRole("button", { name: "Next", exact: true }).click();
  await expect(related.getByRole("region", { name: /Report #\d+ evidence/ })).toHaveCount(5);
  await expect(related.getByText("Report #26", { exact: true })).toBeVisible();
  await related.getByRole("region", { name: "Report #26 evidence", exact: true }).getByText(/Individual evidence 26/).click();
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #26", { exact: true })).toBeVisible();
  await expect(related.getByRole("region", { name: /Report #\d+ evidence/ })).toHaveCount(4);
  expect(requests.some((url) => url.includes("page=2"))).toBe(true);
  expect(writes).toEqual([]);
});

test("related report approval targets its own ID and keeps the primary report open", async ({ page }) => {
  const { writes } = await setup(page, "grouped");
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await panel.getByRole("article", { name: /3 related reports/ }).getByRole("button").click();
  const related = panel.getByRole("region", { name: "Related reports", exact: true });
  const fourth = related.getByRole("region", { name: "Report #4 evidence", exact: true });
  await fourth.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(fourth).toHaveCount(0);
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #2", { exact: true })).toBeVisible();
  await expect(related.getByRole("region", { name: "Report #3 evidence", exact: true }).getByRole("button", { name: "Approve", exact: true })).toBeVisible();
  expect(writes).toEqual(["/api/v1/admin/reports/4/approve"]);
});

test("external report selection resolves the selected group without inheriting the queue card", async ({ page }) => {
  const { writes } = await setup(page, "separate_group");
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await panel.getByRole("article", { name: /2 related reports/ }).getByRole("button").click();
  const related = panel.getByRole("region", { name: "Related reports", exact: true });
  await expect(related.getByText("Report #4", { exact: true })).toBeVisible();
  // Next's native history integration selects a report through the Moderation
  // Center handoff, bypassing the queue card just as map selection does.
  await page.evaluate(() => history.pushState(null, "", "/admin/map?focus_report_id=3"));
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #3", { exact: true })).toBeVisible();
  await expect(related).toHaveCount(0);
  await page.evaluate(() => history.pushState(null, "", "/admin/map?focus_report_id=4"));
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #4", { exact: true })).toBeVisible();
  await expect(related.getByText("Report #2", { exact: true })).toBeVisible();
  await expect(related.getByText("Report #3", { exact: true })).toHaveCount(0);
  expect(writes).toEqual([]);
});

test("clicking a map report clears the previously opened unrelated group", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const { writes } = await setup(page, "separate_group");
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await panel.getByRole("article", { name: /2 related reports/ }).getByRole("button").click();
  await expect(panel.getByRole("region", { name: "Related reports", exact: true }).getByText("Report #4", { exact: true })).toBeVisible();
  if (info.project.name === "mobile-chromium") await page.getByRole("button", { name: "Open map", exact: true }).click();
  await expect.poll(() => page.evaluate(() => JSON.parse(localStorage.getItem("lanes_admin_map_viewport") ?? "{}").zoom)).toBe(16);
  const canvas = page.locator(".maplibregl-canvas");
  // On the blank fixture basemap, the only red area in the right half of the
  // map is report #3's high-severity point aura. Click actual rendered pixels.
  let point: { x: number; y: number } | null = null;
  await expect.poll(async () => {
    const png = await canvas.screenshot();
    point = await page.evaluate(async (base64) => {
      const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
      const surface = document.createElement("canvas"); surface.width = image.width; surface.height = image.height;
      const context = surface.getContext("2d")!; context.drawImage(image, 0, 0);
      const pixels = context.getImageData(0, 0, image.width, image.height).data;
      // Isolate the largest red component so the palette control cannot
      // move the click away from the report's actual hit target.
      const mask = new Uint8Array(image.width * image.height);
      for (let y = 100; y < image.height - 100; y++) for (let x = Math.floor(image.width / 2); x < image.width - 60; x++) {
        const offset = (y * image.width + x) * 4;
        if (pixels[offset] > pixels[offset + 1] * 1.2 && pixels[offset] > pixels[offset + 2] * 1.2) mask[y * image.width + x] = 1;
      }
      let largest = { count: 0, x: 0, y: 0 };
      for (let start = 0; start < mask.length; start++) {
        if (!mask[start]) continue;
        const pending = [start]; mask[start] = 0;
        let count = 0, x = 0, y = 0;
        while (pending.length) {
          const index = pending.pop()!;
          count++; x += index % image.width; y += Math.floor(index / image.width);
          for (const next of [index - 1, index + 1, index - image.width, index + image.width]) {
            if (next >= 0 && next < mask.length && mask[next]) { mask[next] = 0; pending.push(next); }
          }
        }
        if (count > largest.count) largest = { count, x, y };
      }
      return largest.count > 20 ? { x: largest.x / largest.count / devicePixelRatio, y: largest.y / largest.count / devicePixelRatio } : null;
    }, png.toString("base64"));
    return point !== null;
  }).toBe(true);
  await canvas.click({ position: point! });
  if (info.project.name === "mobile-chromium") await page.getByRole("button", { name: "Evidence", exact: true }).click();
  await expect(panel.getByRole("region", { name: "User report evidence" }).getByText("Report #3", { exact: true })).toBeVisible();
  await expect(panel.getByRole("region", { name: "Related reports", exact: true })).toHaveCount(0);
  expect(writes).toEqual([]);
});

test("a related report detail failure exposes retry without moderation actions", async ({ page }) => {
  const { writes } = await setup(page, "grouped");
  let fail = true;
  await page.route("**/api/v1/admin/review/items/user_report%3A3", (route) => fail
    ? route.fulfill({ status: 503, json: { detail: "Report evidence unavailable" } }) : route.fallback());
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await panel.getByRole("article", { name: /3 related reports/ }).getByRole("button").click();
  const third = panel.getByRole("region", { name: "Report #3 evidence", exact: true });
  await expect(third.getByRole("alert")).toContainText("Report evidence unavailable");
  await expect(third.getByRole("button", { name: "Approve", exact: true })).toHaveCount(0);
  fail = false;
  await third.getByRole("button", { name: "Retry Report #3", exact: true }).click();
  await expect(third.getByRole("button", { name: "Approve", exact: true })).toBeVisible();
  expect(writes).toEqual([]);
});

test("related member failures stay visible until an explicit retry", async ({ page }) => {
  await setup(page, "large_group");
  let fail = true;
  await page.route("**/api/v1/admin/review/groups/**/members?**", (route) => {
    if (fail) return route.fulfill({ status: 503, json: { detail: "Related reports could not be loaded." } });
    return route.fallback();
  });
  const card = page.getByRole("article", { name: /25 related reports/ });
  await card.getByRole("button").click();
  const related = page.getByRole("region", { name: "Related reports", exact: true });
  await expect(related.getByRole("alert")).toContainText("Related reports could not be loaded");
  await expect(related.getByRole("region", { name: /Report #\d+ evidence/ })).toHaveCount(0);
  fail = false;
  await related.getByRole("button", { name: "Retry related reports" }).click();
  await expect(related.getByRole("region", { name: /Report #\d+ evidence/ })).toHaveCount(19);
});

test("narrow and landscape evidence/map switching keeps content within the viewport", async ({ page }, info) => {
  test.skip(info.project.name !== "mobile-chromium", "Touch layouts only.");
  await page.setViewportSize({ width: 320, height: 740 });
  await setup(page);
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await panel.getByRole("button", { name: "Inspect news claim: Caruncho Avenue" }).click();
  await expect(panel.getByRole("button", { name: /Inspect suggestion 1/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("review-narrow.png") });
  await page.setViewportSize({ width: 844, height: 390 });
  await page.getByRole("button", { name: "Open map", exact: true }).click();
  await expect(panel).toBeHidden();
  await expect(page.getByRole("button", { name: "Evidence", exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath("review-landscape-map.png") });
  await page.getByRole("button", { name: "Evidence", exact: true }).click();
  await expect(panel.getByRole("button", { name: "Back to queue" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

for (const mode of ["unresolved", "unavailable", "limited", "queue_error"] as const) test(`review exposes ${mode} without invented placement`, async ({ page }, info) => {
  const { writes } = await setup(page, mode);
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  if (mode === "queue_error") await expect(panel.getByRole("alert")).toContainText("Review queue could not be loaded");
  else {
    await panel.getByRole("button", { name: "Inspect news claim: Caruncho Avenue" }).click();
    if (mode === "unresolved") {
      await expect(panel.getByText(/No supported map geometry/)).toBeVisible();
      await expect(panel.getByRole("button", { name: /Inspect suggestion/ })).toHaveCount(0);
    } else if (mode === "unavailable") await expect(panel.getByText(/analytical source is unavailable/)).toBeVisible();
    else await expect(panel.getByRole("alert")).toContainText("Too many placement requests");
  }
  await page.screenshot({ path: info.outputPath(`review-${mode}.png`) });
  expect(writes).toEqual([]);
});

async function openGrowthEditor(page: Page) {
  const evidence = page.getByRole("region", { name: "Needs Review", exact: true });
  await evidence.getByRole("button", { name: "Inspect user report: Maybunga bridge" }).click();
  await evidence.getByRole("button", { name: "Review Merge Suggestions", exact: true }).click();
  const workspace = page.getByRole("complementary", { name: "Merge and spatial review workspace" });
  await workspace.getByRole("button", { name: /Zone #9/ }).click();
  await workspace.getByRole("button", { name: "Compare Selected" }).click();
  await workspace.getByRole("button", { name: "Edit Final Zone" }).click();
  return workspace;
}

for (const mode of ["extend", "corroborate", "add_section"] as const) {
  test(`reviewed ${mode} publishes one report into an existing event`, async ({ page }, info) => {
    if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
    const { writes, mergePayloads } = await setup(page, "growth");
    const workspace = await openGrowthEditor(page);
    await workspace.getByLabel("How does this report affect the event?").selectOption(mode);
    if (mode !== "corroborate") {
      await workspace.getByRole("checkbox", { name: "Large Trucks / Buses" }).check();
      await workspace.getByPlaceholder("e.g., Pumping truck stationed on westbound lane. Detour all light vehicles via Shaw Blvd.").fill("Reviewed affected section");
      await workspace.getByRole("button", { name: "Use selected report extents" }).click();
    }
    await expect(workspace.getByRole("button", { name: "Review Confirmation" })).toBeEnabled();
    expect(writes).toEqual([]);
    await workspace.getByRole("button", { name: "Review Confirmation" }).click();
    if (mode === "corroborate") await expect(workspace.getByText("The existing boundary and operational conditions remain unchanged.")).toBeVisible();
    const labels = workspace.getByText("Reports included", { exact: true });
    const labelBounds = await labels.boundingBox();
    const drawerBounds = await workspace.boundingBox();
    expect(labelBounds!.x).toBeGreaterThanOrEqual(drawerBounds!.x);
    expect(drawerBounds!.x).toBeGreaterThanOrEqual(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if (info.project.name === "mobile-chromium" && mode === "extend") {
      await page.setViewportSize({ width: 320, height: 740 });
      await expect(workspace.getByRole("button", { name: "Confirm & Publish" })).toBeVisible();
      expect((await labels.boundingBox())!.x).toBeGreaterThanOrEqual(56);
      await page.screenshot({ path: info.outputPath("growth-narrow.png") });
      await page.setViewportSize({ width: 844, height: 390 });
      await workspace.getByRole("button", { name: "Map", exact: true }).click();
      await page.getByRole("button", { name: "Return to merge", exact: true }).click();
      await expect(workspace.getByRole("button", { name: "Confirm & Publish" })).toBeVisible();
      await page.screenshot({ path: info.outputPath("growth-landscape.png") });
    }
    await page.screenshot({ path: info.outputPath(`growth-${mode}-confirmation.png`) });
    await workspace.getByRole("button", { name: "Confirm & Publish" }).click();
    await expect(workspace).toHaveCount(0);
    expect(mergePayloads).toHaveLength(1);
    expect(mergePayloads[0]).toMatchObject({ primary_report_id: 2, merged_report_ids: [], target_zone_id: 9, merge_mode: mode });
    expect(writes).toEqual(["/api/v1/admin/reports/merge"]);
  });
}

test("failed coverage preview blocks publication and can be retried", async ({ page }) => {
  const { writes, previewControl } = await setup(page, "growth_error");
  const workspace = await openGrowthEditor(page);
  await expect(workspace.getByRole("alert")).toContainText("Coverage preview is unavailable.");
  await expect(workspace.getByRole("button", { name: "Review Confirmation" })).toBeDisabled();
  expect(writes).toEqual([]);
  previewControl.unavailable = false;
  await workspace.getByRole("button", { name: "Retry coverage preview" }).click();
  await expect(workspace.getByRole("button", { name: "Review Confirmation" })).toBeEnabled();
  expect(writes).toEqual([]);
});
