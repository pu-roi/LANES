import { expect, test, type Page } from "@playwright/test";
import type { NewsDecisionRequest } from "../src/features/admin/review/reviewApi";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } });

const time = "2026-10-05T01:00:00Z";
const claim = { raw_place_name: "Caruncho Avenue", canonical_city: "Pasig", canonical_barangay: null,
  canonical_road: "Caruncho Avenue", depth_raw: "knee-deep", depth_formatted: "Knee-deep", condition: "active",
  event_time_resolved: time, event_time_kind: "absolute", evidence_sentence: "Knee-deep flooding on Caruncho Avenue in Pasig.",
  uncertainty_reasons: [], is_historical: false, is_forecast: false, is_negated: false, road_passability: "unknown",
  action_type: "flagged_review", action_rationale: "The exact affected section needs review.", road_placement: null };
const summary = { location: "Caruncho Avenue", area: "Pasig", location_qualifier: null, water_level: "Knee-deep",
  condition: "Flooding reported", flood_time: time, flood_time_label: "Flood observation time", passability: "Not established",
  map_status: "Needs review", reading_status: "reported_location", reading_reason: null };
const source = { title: "Pasig flooding report", canonical_url: "https://example.org/flood", publisher: "fixture-source",
  excerpt: "", article_text: claim.evidence_sentence, published_at: time };
const news = { item: { key: "2:0", run_id: 2, claim_index: 0, article_id: 8, article_version_id: 8,
  title: source.title, publisher_source_id: source.publisher, publisher: "Example News", published_at: time,
  saved_at: time, captured_at: time, extracted_at: time, claim, summary }, claim, captured_input: source,
  input_fingerprint: "fixture", pipeline_version: "fixture-v10", extraction_errors: [], is_metadata_only: false,
  lifecycle_status: "not_available", read_only: true };
const saved = { id: 91, revision: 2, operation: "correct", public_state: "alert", review_state: "resolved",
  reason_code: "staff_correction", decided_at: time, observed_at: time, expires_at: "2026-10-05T03:00:00Z" };
const savedFor = (request: NewsDecisionRequest) => request.operation === "reject"
  ? { ...saved, operation: "reject", public_state: "withdrawn", reason_code: "staff_reject" }
  : saved;

async function setup(page: Page, lostResponse: boolean) {
  const control = { previews: [] as NewsDecisionRequest[], saves: [] as NewsDecisionRequest[], historyReads: 0,
    unrelatedWrites: [] as string[], saved: false };
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api.maptiler.com/maps/**/style.json?**", (route) => route.fulfill({ json: {
    version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#f1f5f9" } }],
  } }));
  await page.route("**/api/v1/**", (route) => {
    const path = decodeURIComponent(new URL(route.request().url()).pathname);
    if (path.endsWith("/auth/test-token")) return route.fulfill({ json: { id: 7, email: "test@example.org", username: "staff",
      is_active: true, role: { id: 1, name: "Super Admin" }, profile: { first_name: "Test", last_name: "Staff" } } });
    if (path.endsWith("/claims/71/decision-preview")) {
      const request = route.request().postDataJSON() as NewsDecisionRequest;
      control.previews.push(request);
      if (request.operation === "reject") return route.fulfill({ json: { public_state: "withdrawn", review_state: "resolved",
        status: null, reason_code: "staff_reject", affects_routing: false } });
      return route.fulfill({ json: { public_state: "alert", review_state: "resolved", status: "Active",
        reason_code: "staff_correction", affects_routing: false } });
    }
    if (path.endsWith("/claims/71/decisions")) {
      control.saves.push(route.request().postDataJSON());
      if (control.saves.length === 1) {
        control.saved = lostResponse;
        return route.fulfill({ status: 503, json: { detail: "Temporary response failure" } });
      }
      control.saved = true;
      return route.fulfill({ json: savedFor(control.saves.at(-1)!) });
    }
    if (path.endsWith("/claims/71/history")) {
      control.historyReads++;
      return route.fulfill({ json: { items: control.saved ? [{ ...savedFor(control.saves[0]), request_id: control.saves[0].request_id }] : [] } });
    }
    if (route.request().method() !== "GET") control.unrelatedWrites.push(path);
    let body: unknown = [];
    if (path.endsWith("/admin/review/items")) body = { items: [{ key: "news_claim:2:0", source: "news_claim", report_id: null,
      run_id: 2, claim_index: 0, title: source.title, location: "Caruncho Avenue", evidence: claim.evidence_sentence,
      review_reason: claim.action_rationale, queued_at: time }], total: 1, item_total: 1, page: 1, pages: 1, page_size: 20,
      counts: { all: 1, news_claims: 1, user_reports: 0 }, read_only: true };
    else if (path.endsWith("/items/news_claim:2:0")) body = { key: "news_claim:2:0", source: "news_claim", is_current_review: true,
      report: null, news, news_actions_available: true, news_case: { case_id: 71, revision: control.saved ? 2 : 1,
        allowed_actions: ["correct", "clear", "defer", "reject", "reopen"], current: control.saved ? savedFor(control.saves[0]) : null,
        decisions: control.saved ? [savedFor(control.saves[0])] : [], evaluation_options: [
          { evaluation_id: 301, source_id: 11, run_id: 2, claim_ordinal: 0, condition: "active", observed_at: time, outcome: "eligible", reason_code: "supported" },
          { evaluation_id: 302, source_id: 12, run_id: 3, claim_ordinal: 0, condition: "subsided", observed_at: time, outcome: "eligible", reason_code: "matched" },
        ] } };
    else if (path.endsWith("/placement")) body = { run_id: 2, claim_index: 0, input_fingerprint: "fixture",
      evidence_pipeline_version: "fixture-v10", placement_revision: "fixture-spatial", claim, read_only: true,
      preview: { status: "unresolved", reason: "no_supported_geometry", selected_candidate_id: null, placement_kind: null,
        candidates: [], total_candidate_count: 0, candidates_truncated: false, osm_source_id: null, osm_catalog_sha256: null,
        osm_snapshot_at: null, noah_catalog_sha256: null, noah_source_ids: {}, noah_attribution: null,
        history_status: "not_applicable", history_sha256: null, unmatched_history: [], uncertainty_reasons: [],
        proves_current_flood: false, may_affect_routing: false, read_only: true } };
    return route.fulfill({ json: body });
  });
  await page.goto("/admin/map", { waitUntil: "domcontentloaded" });
  const panel = page.getByRole("region", { name: "Needs Review", exact: true });
  await panel.getByRole("button", { name: "Inspect news claim: Caruncho Avenue" }).click();
  const decisions = panel.getByRole("region", { name: "News decisions" });
  await expect(decisions.getByText("News decision · revision 1", { exact: true })).toBeVisible();
  return { control, panel, decisions };
}

test("decision preview requires private reasons and audited evidence; failed save retries the same request", async ({ page }, info) => {
  const { control, panel, decisions } = await setup(page, false);
  await expect(panel.getByText("No supported map geometry. Evidence remains available for review.", { exact: true })).toBeVisible();
  await expect(panel.getByRole("button", { name: "Approve", exact: true })).toHaveCount(0);
  expect(control.previews).toEqual([]);
  expect(control.saves).toEqual([]);
  await decisions.getByRole("button", { name: "News decision", exact: true }).click();
  await page.getByRole("button", { name: "Correct using audited evidence", exact: true }).click();
  await expect(decisions.getByRole("button", { name: "Check decision effect" })).toBeDisabled();
  await decisions.getByRole("button", { name: "Audited evidence", exact: true }).click();
  await expect(page.getByRole("button", { name: /Run 3 · subsided/ })).toHaveCount(0);
  await page.screenshot({ path: info.outputPath("news-decision-evidence-choice.png") });
  await page.getByRole("button", { name: /Run 2 · active/ }).click();
  await decisions.getByRole("button", { name: "Check decision effect" }).click();
  expect(control.previews).toEqual([]);
  await decisions.getByRole("textbox", { name: "Internal news decision reason" }).fill("Staff-only investigation reason.");
  await decisions.getByRole("textbox", { name: "Public correction", exact: true }).fill("The location was corrected using the source report.");
  await decisions.getByRole("button", { name: "Check decision effect" }).click();
  await expect(decisions.getByText("Server effect: Active · resolved", { exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath("news-decision-controls.png") });
  expect(control.previews).toHaveLength(1);
  expect(control.saves).toEqual([]);
  expect(control.previews[0]).toMatchObject({ expected_revision: 1, operation: "correct", evaluation_id: 301,
    reason: "Staff-only investigation reason.", public_correction: "The location was corrected using the source report." });
  expect(control.previews[0].request_id).toMatch(/^[0-9a-f-]{36}$/);
  await decisions.getByRole("button", { name: "Save news decision" }).click();
  await expect(decisions.getByRole("alert")).toContainText("Your draft is retained");
  await expect(decisions.getByRole("textbox", { name: "Internal news decision reason" })).toHaveValue("Staff-only investigation reason.");
  expect(control.historyReads).toBe(1);
  await decisions.getByRole("button", { name: "Save news decision" }).click();
  await expect(decisions.getByRole("status")).toHaveText("Decision saved at revision 2.");
  expect(control.saves).toHaveLength(2);
  expect(control.saves[1]).toEqual(control.saves[0]);
  expect(control.saves[0]).toEqual(control.previews[0]);
  expect(control.unrelatedWrites).toEqual([]);
});

test("lost save response recovers from history by request ID without submitting a second decision", async ({ page }) => {
  const { control, decisions } = await setup(page, true);
  await decisions.getByRole("button", { name: "News decision", exact: true }).click();
  await page.getByRole("button", { name: "Reject / withdraw", exact: true }).click();
  await decisions.getByRole("textbox", { name: "Internal news decision reason" }).fill("Staff review found conflicting source evidence.");
  await decisions.getByRole("button", { name: "Check decision effect" }).click();
  await expect(decisions.getByRole("button", { name: "Save news decision" })).toBeVisible();
  await decisions.getByRole("button", { name: "Save news decision" }).click();
  await expect(decisions.getByRole("status")).toHaveText("Decision saved at revision 2.");
  await expect(decisions.getByRole("button", { name: "Save news decision" })).toHaveCount(0);
  expect(control.saves).toHaveLength(1);
  expect(control.historyReads).toBe(1);
  expect(control.saves[0].request_id).toBe(control.previews[0].request_id);
  expect(control.unrelatedWrites).toEqual([]);
});
