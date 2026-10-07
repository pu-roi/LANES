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
  preview_geometry: { type: "MultiLineString", coordinates: [
    [[121.08 + index * .001, 14.57], [121.0803 + index * .001, 14.5703]],
    [[121.0807 + index * .001, 14.5707], [121.081 + index * .001, 14.571]],
  ] }, fragment_status: "available", modeled_fragments: [],
  matching_history: index ? [] : [{ source_year: "2023", source_record_no: "19", barangay: "Maybunga", street: "Caruncho", landmark: "Test crossing" }] }));
const preview = { status: "ambiguous", reason: "competing_road_sections", selected_candidate_id: "section-0",
  placement_kind: "predicted", candidates, total_candidate_count: 2, candidates_truncated: false,
  osm_source_id: "fixture-osm", osm_catalog_sha256: "fixture-osm-hash", osm_snapshot_at: source.published_at,
  noah_catalog_sha256: "fixture-noah-hash", noah_source_ids: { "5": "fixture-noah" }, noah_attribution: "UP NOAH · fixture",
  history_status: "available", history_sha256: "fixture-history", unmatched_history: [], uncertainty_reasons: [],
  reported_severity: "medium", proves_current_flood: false, may_affect_routing: false, read_only: true };

// Inspect rendered pixels in the canvas interior, excluding map controls.
// The fixture basemap has no yellow road auras; count transparent severity pixels.
async function suggestionPixels(page: Page) {
  const bounds = await page.locator(".maplibregl-canvas").boundingBox();
  if (!bounds || bounds.width < 200 || bounds.height < 160) return -1;
  const png = await page.screenshot({ clip: { x: bounds.x + 60, y: bounds.y + 60,
    width: bounds.width - 120, height: bounds.height - 120 } });
  return page.evaluate(async (base64) => {
    const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
    const canvas = document.createElement("canvas"); canvas.width = image.width; canvas.height = image.height;
    const context = canvas.getContext("2d")!; context.drawImage(image, 0, 0);
    const rgba = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let total = 0;
    for (let index = 0; index < rgba.length; index += 4) {
      if (rgba[index] > rgba[index + 2] + 20 && rgba[index + 1] > rgba[index + 2] + 10
        && Math.abs(rgba[index] - rgba[index + 1]) < 45) total++;
    }
    return total;
  }, png.toString("base64"));
}

async function setup(page: Page, mode: "ready" | "unresolved" | "unavailable" | "limited" | "queue_error" | "grouped" | "large_group" | "separate_group" | "growth" | "growth_error" | "panel_details" | "news_zone" = "ready") {
  const writes: string[] = [];
  const sources: string[] = [];
  const filterRequests: Record<string, string>[] = [];
  const mergePayloads: Record<string, unknown>[] = [];
  const previewControl = { unavailable: mode === "growth_error" };
  const growthReport = { ...report, geometry: candidates[0].centerline_geojson };
  const groupedMembers = Array.from({ length: mode === "large_group" ? 25 : 3 }, (_, index) => ({
    key: `user_report:${index + 2}`, source: "user_report", report_id: index + 2, run_id: null, claim_index: null,
    title: `Report #${index + 2}`, location: mode === "separate_group" && index === 1 ? "Other Street" : "Dr. Sixto Antonio Avenue", evidence: `Individual evidence ${index + 2}`,
    review_reason: "Pending user-report verification.", queued_at: source.published_at,
    severity: index === 1 ? "high" : "low", depth: index === 1 ? "waist" : "ankle",
  }));
  const grouping = ["grouped", "large_group", "separate_group", "panel_details"].includes(mode);
  const zone = { id: 9, report_id: 2, name: "Maybunga bridge", is_active: true,
    created_at: source.published_at, updated_at: source.published_at, expires_at: "2026-10-04T08:00:00Z",
    severity: "medium", depth: "knee", report_text: report.raw_text, report_source: "direct_user",
    passable_vehicles: "Heavy vehicles", hidden_hazards: "Open drain", admin_notes: "Keep the bridge approach clear.",
    reporter_name: report.reporter_name,
    geometry: { type: "Polygon", coordinates: [[[121.08,14.57],[121.081,14.57],[121.081,14.571],[121.08,14.57]]] },
    contributors: [2, 3].map((id) => ({ report_id: id, reporter_name: `Reporter ${id}`, raw_text: `Zone evidence ${id}`,
      severity: id === 2 ? "medium" : "high", depth: "knee", created_at: source.published_at,
      reporter_trust_score: 80, is_primary: id === 2, geometry: report.geometry })) };
  const groupReason = "Nearby reports within 2 hours. Barangay boundaries do not exclude review. Confirm flood extent before merging.";
  if (mode === "news_zone") Object.assign(zone, { report_id: null, report_source: "news", reporter_name: "Example News", contributors: [],
    news: [{ case_id: 71, status: "Active", source_title: "News flood zone evidence", source_publisher: "Example News",
      source_url: "https://example.org/flood", observed_at: source.published_at, geometry_basis: "estimated_road_corridor" }] });
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
    else if (path.endsWith("/admin/zone-updates/counts")) body = {};
    else if (path.endsWith("/admin/zones/9/updates")) body = { updates: [], next_before_id: null, is_active: true, can_review: true };
    else if (path.endsWith("/admin/zones/9")) body = zone;
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
    else if (path.endsWith("/zones/9/update-context")) body = { start: [121.08,14.57], end: [121.081,14.571], name: zone.name, depth: zone.depth, is_bidirectional: false };
    else if (path.endsWith("/reports/preview-bidirectional")) {
      const data = route.request().postDataJSON();
      const line = { type: "LineString", coordinates: [data.start, data.end] };
      body = { original: line, opposite: null, coverage_geometry: line, validation_status: "validated", road_type: "LOCAL", message: "Selected road verified." };
    }
    else if (path.endsWith("/notifications")) body = { notifications: [], total: 0, unread_count: 0, has_more: false };
    else if (path.endsWith("/admin/zones/all") && ["panel_details", "news_zone"].includes(mode)) body = { zones: [zone], total: 1 };
    else if (path.endsWith("/reports/active-zones") && ["panel_details", "news_zone"].includes(mode)) body = [zone];
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
      filterRequests.push(Object.fromEntries(url.searchParams.entries()));
      const relatedMembers = mode === "separate_group" ? groupedMembers.filter((member) => member.report_id !== 3) : groupedMembers;
      const userRow = grouping ? { ...relatedMembers[0], member_count: relatedMembers.length, members: relatedMembers.slice(0, 3), group_reason: groupReason,
        ...(mode === "panel_details" ? { location_summary: "Dr. Sixto Antonio Avenue · Bridge approach", area_summary: "Maybunga, Pasig · Rosario, Pasig", severity_levels: ["low", "high"], depth_levels: ["ankle", "waist"] } : {}) } :
        { key: "user_report:2", source: "user_report", report_id: 2, run_id: null, claim_index: null, title: "Report #2",
          location: "Maybunga bridge", evidence: report.raw_text, review_reason: "Pending user-report verification.", queued_at: source.published_at, severity: "medium", depth: "knee" };
      const rows = [{ key: "news_claim:2:0", source: "news_claim", report_id: null, run_id: 2, claim_index: 0,
        title: source.title, location: "Caruncho Avenue", evidence: claim.evidence_sentence, review_reason: claim.action_rationale, queued_at: source.published_at },
      userRow, ...(mode === "separate_group" ? [{ ...groupedMembers[1], member_count: 1, members: [], group_reason: null }] : [])];
      const items = rows.filter((row) => (filter === "all" || row.source === (filter === "news_claims" ? "news_claim" : "user_report")) && (mode !== "panel_details" || (
        (!url.searchParams.get("q") || (row.source === "user_report" && url.searchParams.get("q") === "Report #3")) &&
        (!url.searchParams.get("city") || url.searchParams.get("city") === "Pasig") &&
        (!url.searchParams.get("barangay") || url.searchParams.get("barangay") === "Rosario") &&
        (!url.searchParams.get("severity") || (row.source === "user_report" && url.searchParams.get("severity") === "high"))
      )));
      const userCount = grouping ? groupedMembers.length : 1;
      body = { items, total: items.length, item_total: filter === "all" ? userCount + 1 : filter === "news_claims" ? 1 : userCount,
        page: 1, pages: 1, page_size: 20, counts: { all: userCount + 1, news_claims: 1, user_reports: userCount }, read_only: true,
        ...(mode === "panel_details" ? { item_total: items.reduce((sum, item) => sum + (item.source === "user_report" ? 3 : 1), 0), facets: { cities: filter === "news_claims" ? ["Pasig"] : ["Pasig", "Cainta"], barangays: url.searchParams.get("city") === "Cainta" ? ["San Andres"] : ["Maybunga", "Rosario"] } } : {}) };
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
        } : mode === "unavailable" ? { ...preview, status: "source_unavailable", reason: "noah_unavailable", history_status: "source_unavailable", candidates: candidates.map((candidate) => ({ ...candidate, preview_geometry: null, fragment_status: "source_unavailable" })) } : preview };
    }
    return route.fulfill({ status: 200, json: body });
  });
  await page.goto("/admin/map", { waitUntil: "domcontentloaded" });
  return { writes, sources, filterRequests, mergePayloads, previewControl };
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
    await expect.poll(() => suggestionPixels(page)).toBeGreaterThan(100);
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


test("queue search and location filters retain complete groups and survive returning from evidence", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const { writes, filterRequests } = await setup(page, "panel_details");
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  const search = panel.getByRole("searchbox", { name: "Search review queue" });
  await expect(panel.getByText("Maybunga, Pasig · Rosario, Pasig", { exact: true })).toBeVisible();
  await search.fill("Report #3");
  await expect(panel.getByText("3 reports requiring review · 1 review card")).toBeVisible();
  await panel.getByRole("button", { name: "Filters", exact: true }).click();
  const barangayFilter = panel.getByRole("button", { name: "Filter by barangay", exact: true });
  await expect(barangayFilter).toBeDisabled();
  await expect(barangayFilter).toHaveText("Select a city first");
  await panel.getByRole("button", { name: "Filter by city", exact: true }).click();
  await page.getByRole("button", { name: "Pasig", exact: true }).click();
  await expect(barangayFilter).toBeEnabled();
  await panel.getByRole("button", { name: "Filter by barangay", exact: true }).click();
  await page.getByRole("button", { name: "Rosario", exact: true }).click();
  await panel.getByRole("button", { name: "Filter by severity", exact: true }).click();
  await page.getByRole("button", { name: "High", exact: true }).click();
  await expect.poll(() => filterRequests.some((request) => request.q === "Report #3" && request.city === "Pasig" && request.barangay === "Rosario" && request.severity === "high")).toBe(true);
  await page.screenshot({ path: info.outputPath("queue-search-filters.png") });
  await panel.getByRole("button", { name: "Inspect user report: Dr. Sixto Antonio Avenue", exact: true }).click();
  const evidence = panel.getByRole("region", { name: "User report evidence", exact: true });
  await expect(evidence.getByText("Report #2", { exact: true })).toBeVisible();
  await expect(evidence.getByText("Reported by", { exact: true })).toBeVisible();
  await expect(evidence.getByText("Attachments", { exact: true })).toBeVisible();
  await expect(panel.getByRole("region", { name: "Related reports", exact: true }).getByText("Report #3", { exact: true })).toBeVisible();
  const approve = evidence.getByRole("button", { name: "Approve", exact: true });
  expect((await approve.boundingBox())!.height).toBe(info.project.name === "mobile-chromium" ? 44 : 32);
  await page.screenshot({ path: info.outputPath("report-shared-details.png") });
  await panel.getByRole("button", { name: "Back to queue", exact: true }).click();
  await expect(search).toHaveValue("Report #3");
  await expect(panel.getByRole("button", { name: "Filter by barangay" })).toHaveText(/Rosario/);
  await panel.getByRole("button", { name: "Filter by city" }).click();
  await page.getByRole("button", { name: "Cainta", exact: true }).click();
  await expect(panel.getByRole("button", { name: "Filter by barangay" })).toHaveText("All barangays");
  await barangayFilter.click();
  await expect(page.locator('[data-portal="select-dropdown"]').getByRole("button", { name: "San Andres", exact: true })).toBeVisible();
  await expect(page.locator('[data-portal="select-dropdown"]').getByRole("button", { name: "Rosario", exact: true })).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(panel.getByText("No items need review in this filter.")).toBeVisible();
  await panel.getByRole("button", { name: /News Claims/ }).click();
  await expect(panel.getByRole("button", { name: "Filter by city" })).toHaveText("Cainta");
  await panel.getByRole("button", { name: /^All \d/ }).click();
  await panel.getByRole("button", { name: "Clear filters", exact: true }).click();
  await expect(search).toHaveValue("");
  await expect(barangayFilter).toBeDisabled();
  await expect(barangayFilter).toHaveText("Select a city first");
  await expect(panel.getByText("4 reports requiring review · 2 review cards")).toBeVisible();
  if (info.project.name === "mobile-chromium") {
    await page.setViewportSize({ width: 320, height: 740 });
    expect(await panel.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath("queue-narrow-filters.png") });
    await page.setViewportSize({ width: 844, height: 390 });
    expect(await panel.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  }
  expect(writes).toEqual([]);
});

test("active news zones reuse the staff summary with source and estimate details", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const { writes } = await setup(page, "news_zone");
  await page.getByRole("button", { name: /Active Zones/ }).click();
  const zone = page.getByRole("article", { name: "Zone #9", exact: true });
  await expect(zone.getByRole("link", { name: /News flood zone evidence/ })).toHaveAttribute("href", "https://example.org/flood");
  await expect(zone.getByText("Estimated road corridor", { exact: true })).toBeVisible();
  await expect(zone.getByText("Observed", { exact: true })).toBeVisible();
  expect(await zone.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("news-zone-existing-staff-summary.png") });
  expect(writes).toEqual([]);
});

test("active zones share report styling and keep zone-specific actions and contributor focus", async ({ page }, info) => {
  if (info.project.name === "desktop-chromium") await page.setViewportSize({ width: 1440, height: 900 });
  const { writes } = await setup(page, "panel_details");
  await page.getByRole("button", { name: /Active Zones/ }).click();
  const panel = page.getByRole("region", { name: "Active Zones", exact: true });
  const zone = panel.getByRole("article", { name: "Zone #9", exact: true });
  await expect(zone.getByText("Open drain", { exact: true })).toBeVisible();
  await expect(zone.getByText("Heavy vehicles", { exact: true })).toBeVisible();
  await expect(zone.getByText("Keep the bridge approach clear.", { exact: true })).toBeVisible();
  await expect(zone.getByText("Expires", { exact: true })).toBeVisible();
  await zone.getByRole("checkbox", { name: "Select Zone #9", exact: true }).check();
  await expect(zone.getByRole("checkbox")).toBeChecked();
  const view = zone.getByRole("button", { name: "View on map", exact: true });
  expect((await view.boundingBox())!.height).toBe(info.project.name === "mobile-chromium" ? 44 : 32);
  await zone.getByRole("button", { name: /Reported by/ }).click();
  const contributors = zone.getByRole("region", { name: "Zone #9 contributing reports", exact: true });
  await expect(contributors.getByRole("article")).toHaveCount(2);
  await contributors.getByRole("button", { name: "Inspect Report #3 on map", exact: true }).click();
  await expect(contributors.getByRole("button", { name: "Restore zone on map", exact: true })).toHaveAttribute("aria-pressed", "true");
  await contributors.getByRole("button", { name: "Restore zone on map", exact: true }).click();
  await zone.getByRole("button", { name: /Reported by/ }).click();
  await page.screenshot({ path: info.outputPath("zone-shared-details.png") });
  await zone.getByRole("checkbox", { name: "Select Zone #9", exact: true }).uncheck();
  await zone.getByRole("button", { name: "Deactivate", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Confirm Deactivation", exact: true })).toBeVisible();
  await expect(page.getByText("#9", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  if (info.project.name === "mobile-chromium") {
    await page.setViewportSize({ width: 320, height: 740 });
    await view.scrollIntoViewIfNeeded();
    expect(await panel.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath("zone-narrow-details.png") });
    await page.setViewportSize({ width: 844, height: 390 });
    expect(await panel.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  }
  await zone.getByRole("button", { name: "Edit", exact: true }).click();
  await expect(page.getByText(/Edit Zone #9/, { exact: true }).first()).toBeVisible();
  expect(writes).toEqual([]);
});

test("active zone public updates stay pending until an explicit staff review", async ({ page }, info) => {
  await setup(page, "panel_details");
  let reviewed = false;
  const update = { id: 501, zone_id: 9, author_id: 21, author_name: "Witness", condition: "no_floodwater",
    observed_at: new Date().toISOString(), submitted_at: new Date().toISOString(), observed_location: "Eastbound bridge approach",
    description: "No water on this side of the bridge.", depth: null, severity: null, latitude: null, longitude: null,
    passable_vehicles: null, hidden_hazards: "unsure", media_urls: ["https://example.org/zone-evidence.png"], review_state: "pending", review: null };
  await page.route("**/api/v1/admin/zone-updates/counts?**", route => route.fulfill({ json: reviewed ? {} : { "9": 1 } }));
  await page.route("**/api/v1/admin/zones/9/updates", route => route.fulfill({ json: { updates: [{ ...update, review_state: reviewed ? "reviewed" : "pending", review: reviewed ? { note: "Keep zone; one dry spot only", reviewed_at: new Date().toISOString() } : null }], next_before_id: null, is_active: true, can_review: true } }));
  await page.route("**/api/v1/admin/zones/9/updates/501/review", async route => {
    expect(route.request().postDataJSON()).toEqual({ decision: "reviewed", note: "Keep zone; one dry spot only" });
    reviewed = true; await route.fulfill({ json: { ...update, review_state: "reviewed" } });
  });
  await page.getByRole("button", { name: /Active Zones/ }).click();
  const zone = page.getByRole("article", { name: "Zone #9", exact: true });
  await expect(zone.getByRole("button", { name: "Info for Zone #9" })).toBeVisible();
  await zone.getByRole("button", { name: "1 new update", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Flood Zone Details" });
  await expect(dialog.getByRole("article", { name: "Public update #501" })).toBeVisible();
  await expect(dialog.locator("..")).toHaveCSS("opacity", "1");
  expect(reviewed).toBe(false);
  await page.screenshot({ path: info.outputPath("zone-community-updates.png") });
  await dialog.getByRole("button", { name: "View evidence (1)", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Evidence viewer" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Close media viewer" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Evidence viewer" })).toHaveCount(0);
  await expect(dialog).toBeVisible();
  await dialog.getByLabel("Review note").fill("Keep zone; one dry spot only");
  await dialog.getByRole("button", { name: "Mark reviewed", exact: true }).click();
  await expect(dialog.getByText("Reviewed", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Close flood zone details" }).click();
  await expect(zone.getByRole("button", { name: "1 new update", exact: true })).toHaveCount(0);
  await zone.getByRole("button", { name: "Info for Zone #9" }).click();
  await expect(dialog.getByText("Official depth", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Edit zone", exact: true }).click();
  await expect(page.getByText("Edit Zone #9", { exact: true }).first()).toBeVisible();
});

test("public zone observation keeps evidence and the submission ID on upload retry", async ({ page }, info) => {
  await setup(page, "panel_details");
  await page.route("**/photon.komoot.io/api/**", route => route.fulfill({ json: { features: [] } }));
  await page.route("**/api/v1/auth/test-token", route => route.fulfill({ json: { id: 21, username: "Witness", is_active: true, role: { name: "Commuter" } } }));
  let attempts = 0;
  const requests: string[] = [];
  await page.route("**/api/v1/zones/9/updates", async route => {
    attempts++; requests.push(route.request().postData() ?? "");
    await route.fulfill({ status: attempts === 1 ? 502 : 200, json: attempts === 1 ? { detail: "Attachment failed. Please retry." } : { id: 501 } });
  });
  await page.goto("/map?zone_update=9&zone_condition=no_floodwater");
  await expect(page.getByRole("button", { name: "No floodwater", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Observed depth")).toHaveCount(0);
  await expect(page.getByPlaceholder("e.g. Ortigas Ave, Pasig (Start)")).toHaveValue("14.57000, 121.08000");
  await expect(page.getByLabel("Observed at", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Observed spot / road direction")).toHaveCount(0);
  await page.getByPlaceholder("e.g. C. Raymundo Ave (End)").fill("121.082,14.572");
  await expect(page.getByText("Coordinates: 121.08200, 14.57200", { exact: true })).toBeAttached();
  await page.getByText("Coordinates: 121.08200, 14.57200", { exact: true }).click();
  await page.getByRole("button", { name: "Next Step", exact: true }).click();
  await page.getByRole("button", { name: "Take Survey", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Community Survey", exact: true })).toBeVisible();
  await page.getByRole("checkbox", { name: "Pedestrians", exact: true }).check();
  await page.getByRole("button", { name: "No", exact: true }).click();
  await page.getByRole("button", { name: "Done & Return", exact: true }).click();
  await expect(page.getByText("Survey complete. Thank you!", { exact: true })).toBeVisible();
  await page.getByLabel("Description", { exact: true }).fill("No visible water on the bridge approach.");
  await expect(page.getByLabel("Capture flood photo or video")).toHaveAttribute("capture", "environment");
  await expect(page.getByLabel("Capture flood photo or video")).toHaveAttribute("accept", "image/*,video/*");
  await expect(page.getByRole("button", { name: /^(Take photo|Record video|Choose files)$/ })).toHaveCount(0);
  await page.getByLabel("Attach flood zone photos or videos").setInputFiles({ name: "bridge.png", mimeType: "image/png", buffer: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9kAAAAASUVORK5CYII=", "base64") });
  await expect(page.getByRole("button", { name: "Remove bridge.png", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Open camera", exact: true }).scrollIntoViewIfNeeded();
  await page.getByLabel("Description", { exact: true }).blur();
  await expect(page.getByRole("heading", { name: "Report Flood", exact: true })).toBeInViewport();
  await page.screenshot({ path: info.outputPath("zone-public-observation.png") });
  await page.getByRole("button", { name: "Submit update", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Attachment failed. Please retry." })).toHaveText("Attachment failed. Please retry.");
  await expect(page.getByRole("button", { name: "Remove bridge.png", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Submit update", exact: true }).click();
  await expect(page.getByText("Update received", { exact: true })).toBeVisible();
  const ids = requests.map(body => body.match(/"request_id":"([^"]+)"/)?.[1]);
  expect(ids[0]).toBeTruthy(); expect(ids[0]).toEqual(ids[1]);
  expect(requests[0]).toContain('"depth":null');
  expect(requests[0]).toContain('filename="bridge.png"');
  expect(requests[0]).toContain('"road_start":[121.08,14.57]');
  expect(requests[0]).toContain('"road_end":[121.082,14.572]');
  expect(requests[0]).toContain('"passable_vehicles":["walk"]');
  expect(requests[0]).not.toContain('"observed_at"');
});

test("public zone popup quick action opens the shared observation panel", async ({ page }, info) => {
  await setup(page, "panel_details");
  await page.route("**/api/v1/auth/test-token", route => route.fulfill({ json: { id: 21, username: "Witness", is_active: true, role: { name: "Commuter" } } }));
  await page.goto("/map?lat=14.57025&lng=121.08075&zoom=16");
  await expect(async () => {
    if (await page.getByRole("button", { name: "Still flooded", exact: true }).isVisible()) return;
    // Locate the fixture's yellow flood pin/area in actual rendered pixels;
    // mobile map framing differs from the desktop camera center.
    const bounds = (await page.locator(".maplibregl-canvas").boundingBox())!;
    const png = await page.screenshot({ scale: "css", clip: bounds });
    const point = await page.evaluate(async base64 => {
      const image = new Image(); image.src = `data:image/png;base64,${base64}`; await image.decode();
      const canvas = document.createElement("canvas"); canvas.width = image.width; canvas.height = image.height;
      const context = canvas.getContext("2d")!; context.drawImage(image, 0, 0);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
      let x = 0, y = 0, count = 0;
      for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] > 200 && pixels[i + 1] > 150 && pixels[i + 1] < 240 && pixels[i + 2] < 210
          && pixels[i] > pixels[i + 1] + 5 && pixels[i + 1] > pixels[i + 2] + 30) {
          x += (i / 4) % canvas.width; y += Math.floor(i / 4 / canvas.width); count++;
        }
      }
      return count ? { x: x / count, y: y / count } : null;
    }, png.toString("base64"));
    expect(point).toBeTruthy();
    const x = bounds.x + point!.x, y = bounds.y + point!.y;
    if (info.project.name === "mobile-chromium") await page.touchscreen.tap(x, y);
    else await page.mouse.move(x, y);
    await expect(page.getByRole("button", { name: "Still flooded", exact: true })).toBeVisible({ timeout: 2000 });
  }).toPass({ timeout: 20000 });
  await page.screenshot({ path: info.outputPath("zone-popup-quick-actions.png") });
  await page.getByRole("button", { name: "Still flooded", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Report Flood", exact: true })).toHaveCount(1);
  await expect(page.getByText("Updating existing flood zone", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Still flooded", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Depth unsure", exact: true })).toHaveCount(0);
  await expect(page.getByPlaceholder("e.g. Ortigas Ave, Pasig (Start)")).toBeVisible();
});

test("shared Report Flood panel preserves the new report draft when switching out of a zone update", async ({ page }, info) => {
  const { writes } = await setup(page, "panel_details");
  await page.route("**/api/v1/auth/test-token", route => route.fulfill({ json: { id: 21, username: "Witness", is_active: true, role: { name: "Commuter" } } }));
  await page.goto("/map");
  await page.evaluate(async () => {
    const original = new File(["original report photo"], "original-report.jpg", { type: "image/jpeg" });
    const draft = { version: 1, ownerId: "21", updatedAt: new Date().toISOString(), active: {
      floodStart: { coords: [121.08, 14.57], label: "Original report start" },
      floodEnd: { coords: [121.081, 14.571], label: "Original report end" },
      floodPreviewGeometry: { type: "LineString", coordinates: [[121.08,14.57],[121.081,14.571]] },
      floodOppositeGeometry: null, floodIsBidirectional: false, startInput: "Original report start", endInput: "Original report end",
      visualOption: "gutter", passableVehicles: ["Large Trucks / Buses"], hiddenHazards: "no", showSurvey: false,
      description: "My unfinished new flood report", mediaFiles: [original], isPublic: false, step: 2,
    }, queuedDrafts: [] };
    await new Promise<void>((resolve, reject) => {
      const request = indexedDB.open("keyval-store");
      request.onupgradeneeded = () => request.result.createObjectStore("keyval");
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const tx = request.result.transaction("keyval", "readwrite");
        tx.objectStore("keyval").put(draft, "lanes:flood-report-draft:v1:21");
        tx.oncomplete = () => { request.result.close(); resolve(); };
        tx.onerror = () => reject(tx.error);
      };
    });
  });
  await page.goto("/map?zone_update=9&zone_condition=still_flooded");
  await expect(page.getByText("Draft Restored", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Report Flood", exact: true })).toHaveCount(1);
  await expect(page.getByRole("heading", { name: "Update Flood Zone", exact: true })).toHaveCount(0);
  await expect(page.getByPlaceholder("e.g. Ortigas Ave, Pasig (Start)")).toHaveValue("14.57000, 121.08000");
  await page.getByRole("group", { name: "Flood Severity", exact: true }).getByRole("button", { name: /^Waist/ }).click();
  await page.getByRole("button", { name: "Next Step", exact: true }).click();
  await page.getByLabel("Description", { exact: true }).fill("Different witness observation");
  await expect(page.getByRole("button", { name: "Remove original-report.jpg", exact: true })).toHaveCount(0);
  await page.getByLabel("Attach flood zone photos or videos").setInputFiles({ name: "zone-only.png", mimeType: "image/png", buffer: Buffer.from("separate evidence") });
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await page.getByRole("button", { name: "Other change / Unsure", exact: true }).click();
  await page.getByRole("button", { name: "Next Step", exact: true }).click();
  await expect(page.getByLabel("Description", { exact: true })).toHaveValue("Different witness observation");
  await expect(page.getByRole("button", { name: "Remove zone-only.png", exact: true })).toBeVisible();
  if (info.project.name === "mobile-chromium") await page.setViewportSize({ width: 320, height: 700 });
  await page.screenshot({ path: info.outputPath("shared-report-update-mode.png") });
  const newReport = page.getByRole("button", { name: "New report", exact: true });
  const header = page.getByRole("heading", { name: "Report Flood", exact: true });
  await expect(header).toBeInViewport();
  expect(await header.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  const buttonBounds = (await newReport.boundingBox())!, headingBounds = (await header.boundingBox())!;
  expect(Math.abs((buttonBounds.y + buttonBounds.height / 2) - (headingBounds.y + headingBounds.height / 2))).toBeLessThan(3);
  await newReport.click();
  await expect(page.getByRole("heading", { name: "Discard this update?", exact: true })).toBeVisible();
  await expect(page.getByText("Your current Flood Zone update fields and attachments will be lost. Your unfinished flood report will be kept.", { exact: true })).toBeVisible();
  const cancelBounds = (await page.getByRole("button", { name: "Keep editing", exact: true }).boundingBox())!;
  const confirmBounds = (await page.getByRole("button", { name: "Discard", exact: true }).boundingBox())!;
  expect(cancelBounds.x).toBeGreaterThanOrEqual(16);
  expect(confirmBounds.x + confirmBounds.width).toBeLessThanOrEqual((await page.evaluate(() => window.innerWidth)) - 16);
  await page.screenshot({ path: info.outputPath("new-report-discard-warning.png") });
  await page.getByRole("button", { name: "Keep editing", exact: true }).click();
  await expect(page.getByLabel("Description", { exact: true })).toHaveValue("Different witness observation");
  await expect(page.getByRole("button", { name: "Remove zone-only.png", exact: true })).toBeVisible();
  await newReport.click();
  await page.getByRole("button", { name: "Discard", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Report Flood", exact: true })).toHaveCount(1);
  await expect(page.getByLabel("Description", { exact: true })).toHaveValue("My unfinished new flood report");
  await expect(page.getByRole("button", { name: "Remove original-report.jpg", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Remove zone-only.png", exact: true })).toHaveCount(0);
  await expect(newReport).toHaveCount(0);
  await expect(page.getByLabel("Observed at", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("When did you observe this flood? (Optional)")).toHaveCount(0);
  await page.getByRole("button", { name: "Back", exact: true }).click();
  await expect(page.getByPlaceholder("e.g. Ortigas Ave, Pasig (Start)")).toHaveValue("Original report start");
  await expect(page.getByPlaceholder("e.g. C. Raymundo Ave (End)")).toHaveValue("Original report end");
  await page.screenshot({ path: info.outputPath("shared-report-restored-draft.png") });
  expect(writes.filter(path => !path.endsWith("/preview-bidirectional"))).toEqual([]);
});

test("zone update road endpoints can be selected on the map without losing the report panel", async ({ page }, info) => {
  await setup(page, "panel_details");
  await page.route("**/api/v1/auth/test-token", route => route.fulfill({ json: { id: 21, username: "Witness", is_active: true, role: { name: "Commuter" } } }));
  await page.route("**/photon.komoot.io/api/**", route => route.fulfill({ json: { features: [] } }));
  await page.goto("/map?zone_update=9&zone_condition=still_flooded");
  const end = page.getByPlaceholder("e.g. C. Raymundo Ave (End)");
  await expect(end).toHaveValue("14.57100, 121.08100");
  await end.click();
  await page.getByRole("button", { name: "Choose on Map", exact: true }).click();
  if (info.project.name === "mobile-chromium") {
    await expect(page.getByRole("button", { name: "Set Flood End", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Report Flood", exact: true })).toBeHidden();
    await page.getByRole("button", { name: "Set Flood End", exact: true }).click();
  } else {
    const canvas = page.locator(".maplibregl-canvas");
    const bounds = (await canvas.boundingBox())!;
    await canvas.click({ position: { x: bounds.width * .4, y: bounds.height * .5 } });
  }
  await expect(page.getByRole("heading", { name: "Report Flood", exact: true })).toBeVisible();
  await expect(end).not.toHaveValue("14.57100, 121.08100");
  await expect(end).not.toHaveValue("");
  await expect(page.getByRole("button", { name: "Next Step", exact: true })).toBeEnabled();
  await page.screenshot({ path: info.outputPath("zone-update-map-picker.png") });
});

test("guest zone updates use the identical original Report Flood login view", async ({ page }, info) => {
  const { writes } = await setup(page, "panel_details");
  await page.route("**/api/v1/auth/test-token", route => route.fulfill({ status: 401, json: { detail: "Sign in required" } }));
  await page.goto("/map?action=report");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("lanes_token"))).toBeNull();
  if (info.project.name === "mobile-chromium") {
    await page.getByRole("button", { name: "Report Flood Hazard" }).click();
    await page.getByRole("button", { name: "Flood Report", exact: true }).click();
  } else {
    await page.getByRole("button", { name: "Expand panel", exact: true }).click();
  }
  const heading = page.getByRole("heading", { name: "Login Required", exact: true });
  await expect(heading).toBeVisible();
  const original = await heading.locator("..").evaluate(element => {
    const clone = element.cloneNode(true) as HTMLElement;
    clone.querySelector("a")?.removeAttribute("href");
    return { html: clone.outerHTML, width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height };
  });
  await page.screenshot({ path: info.outputPath("original-report-login.png") });
  await page.goto("/map?zone_update=9&zone_condition=no_floodwater");
  await expect(heading).toBeVisible();
  const update = await heading.locator("..").evaluate(element => {
    const clone = element.cloneNode(true) as HTMLElement;
    clone.querySelector("a")?.removeAttribute("href");
    return { html: clone.outerHTML, width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height };
  });
  expect(update.html).toEqual(original.html);
  expect(update.width).toBeCloseTo(original.width, 2);
  expect(update.height).toBeCloseTo(original.height, 2);
  await expect(page.getByRole("button", { name: "Go to Login", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Go to Login", exact: true })).toHaveAttribute("href", "/login?redirect=%2Fmap%3Fzone_update%3D9%26zone_condition%3Dno_floodwater");
  await expect(page.getByText("Updating existing flood zone", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Official depth:", { exact: false })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Return to new flood report", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "New report", exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Report Flood", exact: true })).toHaveCount(1);
  await page.screenshot({ path: info.outputPath("zone-update-report-login.png") });
  expect(writes.filter(path => !path.endsWith("/preview-bidirectional"))).toEqual([]);
});
