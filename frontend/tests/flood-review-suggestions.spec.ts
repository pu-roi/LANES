import { expect, test, type Page } from "@playwright/test";
import type { CaseReviewSuggestion, ReviewSuggestionState, WetEvidence, ZonePrediction, DurationCalculation, CrossLocationPrediction } from "../src/features/flood-followups/reviewSuggestionApi";
import calculations from "./fixtures/subsidence-calculation.json";

test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } });

const stamp = "2026-10-08T01:00:00Z";
const wet: WetEvidence = { audit_id: 4, review_id: null, observed_at: "2026-10-07T23:00:00Z", available_at: "2026-10-07T23:10:00Z", provenance: "original_citizen_observation" };
const baseCase: CaseReviewSuggestion = { report_id: 2, location: "Maybunga bridge", zone_id: 9, can_issue: true, ineligibility_reason: null,
  reference: wet, latest_wet: wet, suggestion: null, state: "no_suggestion", state_reason: null, evaluated_at: stamp };
const saved = { id: 81, issued_at: stamp, issued_by: 7, suggested_review_at: "2026-10-08T04:00:00Z",
  reference: wet, latest_wet: wet, model: { model_sha256: "fixture-model-checksum", algorithm: "intercept_only_lognormal_aft", target_version: "fixture" },
  quantiles: [.1, .5, .9].map((quantile, index) => ({ quantile, remaining_minutes: [120, 180, 360][index], estimated_reported_subsidence_at: ["2026-10-08T03:00:00Z", "2026-10-08T04:00:00Z", "2026-10-08T07:00:00Z"][index] })) };
const followup = { id: 42, report_id: 2, user_id: 8, request_id: "1d884c7c-934c-48d0-b872-04d04f638d15", condition: "still_flooded", observed_at: stamp,
  submitted_at: stamp, evidence_text: "Knee deep water remains on the saved bridge approach.", depth_cm: 45, source_url: null,
  same_location_confirmed: true, original_observed_at: wet.observed_at, original_available_at: wet.available_at, original_observation_audit_id: 4,
  location_snapshot: { report_id: 2, city: "Pasig", barangay: "Maybunga", human_readable_location: "Maybunga bridge", geometry_sha256: "fixture", zone_id: 9, event_id: null },
  review_state: "pending", review: null, source_claim_only: true, model_admitted: false };

async function setup(page: Page, options: { readOnly?: boolean; missing?: boolean; failure?: boolean; due?: boolean; owner?: boolean; review?: boolean; queueError?: boolean; zone?: boolean; state?: ReviewSuggestionState; getFailure?: boolean; unlinked?: boolean; unsupported?: boolean; registrationSimulation?: boolean; pooled?: boolean; crossLocation?: "estimate" | "missing" | "failure" | "proxy" } = {}) {
  await page.clock.install({ time: new Date(options.due ? "2026-10-08T05:00:00Z" : stamp) });
  let state: CaseReviewSuggestion = { ...baseCase, can_issue: !options.readOnly && !options.missing,
    ineligibility_reason: options.missing ? "An explicit observation time is required." : null,
    reference: options.missing ? null : wet, latest_wet: options.missing ? null : wet,
    ...(options.due ? { suggestion: saved, state: "due", state_reason: "The suggested review time has arrived. Current evidence is still needed." } : {}),
    ...(options.state ? { suggestion: saved, state: options.state } : {}),
    ...(options.unsupported ? { can_issue: false, ineligibility_reason: "This location is outside the model's study scope." } : {}) };
  const posts: Record<string, unknown>[] = [];
  let reviewed = false;
  let ownerSaved: Record<string, unknown> | null = null;
  let getRequests = 0;
  let comparisonRequests = 0;
  const zone = { id: 9, report_id: options.unlinked ? null : 2, name: "Maybunga bridge", is_active: true, created_at: stamp, updated_at: stamp,
    expires_at: "2026-10-10T00:00:00Z", severity: "medium", depth: "knee", report_source: "direct_user", original_report_text: "Water at the bridge.",
    location_label: "Maybunga bridge", contributors: [], geometry: { type: "Polygon", coordinates: [[[121.08,14.57],[121.081,14.57],[121.081,14.571],[121.08,14.57]]] } };
  await page.addInitScript(() => localStorage.setItem("lanes_token", "synthetic-review-fixture"));
  await page.route("**/api.maptiler.com/**", route => route.fulfill({ json: { version: 8, sources: {}, layers: [] } }));
  await page.route("**/api/v1/**", async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (path.endsWith("/auth/test-token")) return route.fulfill({ json: { id: 7, username: "Fixture", email: "fixture@example.invalid", is_active: true,
      created_at: stamp, role: { name: options.owner ? "Commuter" : "Super Admin", permissions: { reports: options.readOnly ? "view" : "full", zones: "full" } },
      profile: { first_name: "Test", last_name: "Citizen", trust_score: 75, accuracy_rate: 100, reports_submitted: 1, reports_approved: 1 } } });
    if (path.endsWith("/admin/moderation/flood-reports")) {
      const cases = [
        { report_id: 2, status: "approved", zone_id: 9 },
        { report_id: 3, status: "pending", zone_id: null },
        { report_id: 4, status: "rejected", zone_id: null, rejection_reason: "insufficient_evidence" },
      ].map(item => ({ source: "direct_user", raw_text: "Water at the bridge.", severity: "medium", depth: "knee",
        submitted_at: stamp, location: "Maybunga bridge", reporter: "Fixture", ...item }));
      const filter = url.searchParams.get("status_filter");
      return route.fulfill({ json: filter === "all" ? cases : cases.filter(item => item.status === filter) });
    }
    if (path.endsWith("/cross-location-prediction")) {
      expect(route.request().method()).toBe("GET");
      if (options.crossLocation === "failure" && ++comparisonRequests === 1) return route.fulfill({ status: 503, json: { detail: "Comparison source storage is unavailable." } });
      const available = options.crossLocation && options.crossLocation !== "missing";
      const result: CrossLocationPrediction = {
        zone_id: 9, status: available ? "research_comparison" : "abstained", selected_for_primary: false,
        changes_status_expiry_or_routing: false, reason: available ? null : "No frozen depth features were captured with this source; current values are not backfilled.",
        validation_summary: "36 conditional records share 3 subsidence summaries. Holdouts are incomplete and results vary; prospective accuracy is unverified. The baseline remains the primary estimate.",
        selection_blockers: ["no_prospective_calibration"], model_sha256: "fixture-cross-location", qualified_rows: 36, shared_outcomes: 3,
        trained_locations: ["Maybunga", "Dela Paz", "Santolan", "Santa Lucia"], target_location: "Ugong",
        depth_cm: available ? 40 : null, depth_basis: options.crossLocation === "proxy" ? "reported_canonical_gauge_proxy" : "reported_numeric_centimeters",
        reference_basis: options.crossLocation === "proxy" ? "registration_proxy" : "observed_reference", source_audit_id: 140,
        reference_at: wet.observed_at, source_observed_at: options.crossLocation === "proxy" ? null : wet.observed_at,
        prediction_as_of_at: stamp, quantiles: available ? saved.quantiles : [],
        calculation: available ? { log_duration_location: 6.9, predictive_log_scale: .8, shared_depth_effect: .02, local_effect: 0,
          coefficient_variance: .2, unseen_location_variance: .1225, location_outcomes: 0,
          transfer_basis: "shared_depth_with_unseen_location_prior", uncertainty_method: "conditional_composite_laplace_coefficients_plus_unseen_location_prior" } : null,
        warnings: options.crossLocation === "proxy" ? ["Depth is a canonical gauge proxy, not measured centimetres. This comparison is a proxy-depth simulation."] : [],
      };
      return route.fulfill({ json: result });
    }
    if (path.endsWith("/subsidence-prediction")) {
      expect(route.request().method()).toBe("GET");
      if ((options.getFailure || options.failure) && ++getRequests === 1) return route.fulfill({ status: 503, json: { detail: "The model is temporarily unavailable. Try again." } });
      const unavailable = options.missing || options.unlinked || options.unsupported;
      const result: ZonePrediction = { zone_id: 9, state: unavailable ? "unavailable" : options.state === "evidence_stale" ? "expired" : options.state === "case_closed" ? "inactive" : options.state === "evidence_changed" || options.state === "followup_received" ? "needs_review" : "estimated",
        city: "Pasig", barangays: [options.unsupported ? "Ugong" : "Maybunga"], coordinates: [121.08,14.57], boundary_revision: "fixture", nearby_report_count: options.unlinked ? 1 : 0,
        evaluated_at: await page.evaluate(() => new Date().toISOString()), reference: unavailable ? null : { source_kind: "original_citizen_observation", source_id: 4, report_id: 2, observed_at: wet.observed_at, available_at: wet.available_at },
        latest_wet: null, evidence: [], model: { status: "research_model_available", supported_barangays: ["Maybunga", "Dela Paz", "Santolan", "Sta. Lucia"], model_sha256: "fixture-model-checksum" },
        quantiles: unavailable || options.state && !["scheduled", "due"].includes(options.state) ? [] : saved.quantiles,
        continuity_assumed: !unavailable, research_only: true, changes_status_expiry_or_routing: false,
        registration_audit_id: options.registrationSimulation ? 140 : null,
        registration_simulation: options.registrationSimulation ? { status: "research_estimate", abstention_reason: null,
          reference_at: wet.observed_at, prediction_as_of_at: stamp, model: { status: "research_model_available", supported_barangays: ["Maybunga"], model_sha256: "fixture" },
          quantiles: saved.quantiles, pooled_geographic_transfer: true } : null,
        warnings: options.pooled ? ["Pooled Pasig transfer: this barangay has no subsidence outcomes in the training cohort; location accuracy is unverified."] : [],
        pooled_geographic_transfer: !!options.pooled,
        reasons: options.unsupported ? ["This location is outside the Pasig model scope."] : options.missing || options.unlinked ? ["No qualified observation time is recorded for this zone; creation time is not a flood observation."] : options.state === "evidence_stale" ? ["Zone evidence has expired."] : options.state === "case_closed" ? ["The flood zone or incident is inactive."] : options.state && ["evidence_changed", "followup_received"].includes(options.state) ? ["New citizen evidence needs review before recalculating this episode."] : [] };
      return route.fulfill({ json: result });
    }
    if (path.endsWith("/review-suggestion")) {
      if (route.request().method() === "GET" && options.getFailure && ++getRequests === 1) return route.fulfill({ status: 503, json: { detail: "The model is temporarily unavailable. Try again." } });
      if (route.request().method() === "POST") {
        const body = route.request().postDataJSON(); posts.push(body);
        expect(Object.keys(body).sort()).toEqual(["acknowledge_research_limitations", "assume_continuous_wet", "request_id"]);
        if (options.failure && posts.length === 1) return route.fulfill({ status: 503, json: { detail: "The model is temporarily unavailable. Try again." } });
        state = { ...state, suggestion: saved, state: "scheduled" };
      }
      return route.fulfill({ json: { ...state, evaluated_at: await page.evaluate(() => new Date().toISOString()) } });
    }
    if (path.endsWith("/admin/flood-review-suggestions")) {
      if (options.queueError) return route.fulfill({ status: 503, json: { detail: "Suggestions could not be loaded." } });
      return route.fulfill({ json: { cases: state.suggestion && (url.searchParams.get("actionable_only") === "false" || state.state !== "scheduled") ? [state] : [],
        next_before_id: null, evaluated_at: stamp, page_scanned: state.suggestion ? 1 : 0 } });
    }
    if (path.endsWith("/admin/flood-follow-ups")) return route.fulfill({ json: { follow_ups: options.review && !reviewed ? [followup] : [], next_before_id: null } });
    if (path.endsWith("/flood-follow-ups/42/review")) {
      const body = route.request().postDataJSON(); expect(body.same_location_verified).toBe(true);
      reviewed = true;
      state = { ...state, state: "evidence_changed", state_reason: "Reviewed evidence changed. Inspect it before using this suggestion." };
      return route.fulfill({ json: { ...followup, review_state: "accepted", review: { ...body, id: 43, reviewer_id: 7, reviewed_at: stamp } } });
    }
    if (path.endsWith("/reports/me")) return route.fulfill({ json: [{ id: 2, raw_text: "Water remains at Maybunga bridge.", status: "approved", severity: "medium", created_at: stamp, human_readable_location: "Maybunga bridge" }] });
    if (path.endsWith("/reports/2/follow-ups")) {
      if (route.request().method() === "POST") {
        const body = route.request().postDataJSON(); posts.push(body);
        if (posts.length === 1) return route.fulfill({ status: 503, json: { detail: "Follow-up storage unavailable. Retry later." } });
        ownerSaved = { ...followup, ...body, user_id: 7 };
        return route.fulfill({ json: ownerSaved });
      }
      return route.fulfill({ json: { follow_ups: ownerSaved ? [ownerSaved] : [], can_submit: true, ineligibility_reason: null } });
    }
    if (path.endsWith("/feed")) return route.fulfill({ json: { posts: [], total: 0, has_more: false } });
    if (path.endsWith("/reports/latest-snapshot")) return route.fulfill({ json: { zones: [], alerts: [], version: "fixture" } });
    if (path.endsWith("/admin/review/items")) return route.fulfill({ json: { items: [], total: 0, next_before: null } });
    if (path.endsWith("/admin/zones/all")) return route.fulfill({ json: { zones: options.zone ? [zone] : [], total: options.zone ? 1 : 0 } });
    if (path.endsWith("/admin/zones/9")) return route.fulfill({ json: zone });
    if (path.endsWith("/reports/active-zones")) return route.fulfill({ json: options.zone ? [zone] : [] });
    if (path.endsWith("/admin/zones/9/updates")) return route.fulfill({ json: { updates: [], next_before_id: null, is_active: true, can_review: true } });
    if (path.endsWith("/admin/zone-updates/counts")) return route.fulfill({ json: {} });
    return route.fulfill({ json: [] });
  });
  await page.goto(options.owner ? "/profile" : options.zone ? "/admin/map" : "/admin/moderation?tab=flood");
  return posts;
}

async function openPrediction(page: Page) {
  await page.getByRole("button", { name: /Active Zones/ }).click();
  await page.getByRole("button", { name: "Info for Zone #9" }).click();
  return page.getByRole("dialog", { name: "Flood Zone Details" }).getByRole("region", { name: "Automatic subsidence prediction for zone 9" });
}

async function expectNoManualFields(panel: ReturnType<Page["getByRole"]>) {
  await expect(panel.locator("input, select, textarea")).toHaveCount(0);
  await expect(panel.getByRole("checkbox")).toHaveCount(0);
  await expect(panel.getByRole("button", { name: /test|save|calculate/i })).toHaveCount(0);
}

for (const state of ["estimate", "missing", "failure", "proxy"] as const) {
  test(`cross-location comparison ${state} preserves the baseline and automatic flow`, async ({ page }, info) => {
    const requests: string[] = [];
    page.on("request", request => { if (request.url().includes("cross-location-prediction")) requests.push(request.method()); });
    const posts = await setup(page, { zone: true, crossLocation: state });
    const panel = await openPrediction(page);
    await expect(panel.getByText(/Around/).first()).toBeVisible();
    const baseline = await panel.getByText(/Around/).first().textContent();
    expect(requests).toHaveLength(0);
    await panel.getByRole("button", { name: "View calculation details" }).click();
    const comparison = panel.getByRole("region", { name: "Depth and location research comparison" });
    if (state === "failure") {
      await expect(comparison.getByRole("alert")).toContainText("Comparison source storage is unavailable.");
      await comparison.getByRole("button", { name: "Retry comparison" }).click();
    }
    await expect(comparison.getByText(/36 conditional records share 3/)).toBeVisible();
    if (state === "missing") {
      await expect(comparison.getByText(/No frozen depth features/)).toBeVisible();
      await expect(comparison.getByText(/Candidate comparison:/)).toHaveCount(0);
    } else {
      await expect(comparison.getByText(/Candidate comparison:/)).toBeVisible();
      await expect(comparison.getByText("Ugong: 0 shared summaries")).toBeVisible();
      await expect(comparison.getByText(/added uncertainty for an unseen location/)).toBeVisible();
      if (state === "proxy") {
        await expect(comparison.getByText(/proxy-depth simulation/)).toBeVisible();
        await expect(comparison.getByText(/actual observation unknown/)).toBeVisible();
      }
    }
    expect(await panel.getByText(/Around/).first().textContent()).toBe(baseline);
    await expectNoManualFields(panel);
    expect(await comparison.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
    await comparison.getByRole("heading").evaluate(element => element.scrollIntoView({ block: "start" }));
    await page.screenshot({ path: info.outputPath(`cross-location-${state}.png`) });
    await comparison.getByText(/Training locations:/).scrollIntoViewIfNeeded();
    const last = await comparison.getByText(/Training locations:/).boundingBox();
    const footer = await page.getByRole("button", { name: "Edit zone", exact: true }).boundingBox();
    expect(last && footer && last.y + last.height <= footer.y).toBe(true);
    await page.screenshot({ path: info.outputPath(`cross-location-${state}-support.png`) });
    expect(posts).toHaveLength(0);
    expect(requests.every(method => method === "GET")).toBe(true);
  });
}

test("Moderation Center excludes active-zone ML and flood follow-up sections", async ({ page }, info) => {
  const evidenceRequests: string[] = [];
  page.on("request", request => { if (/flood-review-suggestions|review-suggestion|flood-follow-ups/.test(request.url())) evidenceRequests.push(request.url()); });
  await setup(page, { queueError: true, review: true, due: true });
  await expect(page.getByText("Flood report #2", { exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "ML review assistant" })).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Flood condition follow-ups" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Experimental ML review suggestion" })).toHaveCount(0);
  expect(evidenceRequests).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("moderation-restored.png") });
});

test("Moderation Center retains pending approved rejected filters and map handoff", async ({ page }) => {
  await setup(page);
  await page.getByRole("button", { name: "Status", exact: true }).click();
  await page.getByRole("button", { name: "Pending", exact: true }).click();
  await expect(page.getByText("Flood report #3", { exact: true })).toBeVisible();
  await expect(page.getByText("Flood report #2", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Status", exact: true }).click();
  await page.getByRole("button", { name: "Rejected", exact: true }).click();
  await expect(page.getByText("Flood report #4", { exact: true })).toBeVisible();
  await expect(page.getByText(/Reason:\s*Insufficient evidence/)).toBeVisible();
  await page.getByRole("button", { name: "Status", exact: true }).click();
  await page.getByRole("button", { name: "Approved / linked", exact: true }).click();
  await expect(page.getByText("Flood report #2", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Review on Map", exact: true }).click();
  await expect(page).toHaveURL(/\/admin\/map\?.*focus_report_id=2.*tab=zones.*focus_zone_id=9/);
});

test("owner supplies an explicit observed time and can retry a failed follow-up", async ({ page }, info) => {
  const posts = await setup(page, { owner: true });
  await page.getByRole("button", { name: info.project.name === "mobile-chromium" ? "Reports" : "Hazard Reports", exact: true }).click();
  await page.getByRole("button", { name: "Record or view a flood follow-up" }).click();
  const panel = page.getByRole("region", { name: "Follow-ups for report 2" });
  const clock = panel.locator("input[type='datetime-local']");
  await expect(clock).toHaveValue("");
  await panel.getByRole("button", { name: "Observed flood condition" }).click();
  await page.getByRole("button", { name: "Still flooded", exact: true }).click();
  await clock.fill("2026-10-07T08:00");
  await panel.getByLabel("What you observed and the evidence source").fill("The same bridge approach still has water blocking the road.");
  await panel.getByRole("checkbox").check();
  await panel.getByRole("button", { name: "Submit follow-up for review" }).click();
  await expect(panel.getByRole("alert")).toContainText("storage unavailable");
  await panel.getByRole("button", { name: "Retry same follow-up" }).click();
  await expect(panel.getByText("Follow-up saved and pending staff review.", { exact: false })).toBeVisible();
  expect(posts).toHaveLength(2); expect(posts[0]).toEqual(posts[1]);
  expect(posts[0].observed_at).toMatch(/Z$/);
  await panel.scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath("owner-timed-followup.png"), fullPage: true });
});

test("Overview automatically displays an estimate and recorded evidence without inputs", async ({ page }, info) => {
  const posts = await setup(page, { zone: true });
  await page.clock.setFixedTime(new Date(stamp));
  const panel = await openPrediction(page);
  await expect(panel.getByRole("heading", { name: "Estimated subsidence" })).toBeVisible();
  await expect(panel.getByText("Detected location: Maybunga, Pasig")).toBeVisible();
  await expect(panel.getByText("Approximately 3h remaining", { exact: true })).toBeVisible();
  await expect(panel.getByText(/Model interval:/)).toContainText("11:00 AM");
  await expect(panel.getByText(/Model interval:/)).toContainText("3:00 PM");
  await expectNoManualFields(panel);
  const dialog = page.getByRole("dialog", { name: "Flood Zone Details" });
  const expiry = dialog.locator("dl").filter({ has: page.getByText("Expires", { exact: true }) });
  await expect(expiry).toContainText("Oct 10");
  expect(await panel.evaluate(element => !!(document.querySelector("[role='dialog'] dl")!.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING))).toBe(true);
  const details = panel.getByRole("button", { name: "View calculation details" });
  await expect(details).toHaveAttribute("aria-expanded", "false");
  await panel.scrollIntoViewIfNeeded();
  expect(await dialog.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  expect((await details.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  const close = await dialog.getByRole("button", { name: "Close flood zone details", exact: true }).boundingBox();
  expect(close!.y).toBeGreaterThanOrEqual(0);
  expect(close!.y + close!.height).toBeLessThanOrEqual(page.viewportSize()!.height);
  await page.screenshot({ path: info.outputPath("automatic-zone-prediction.png"), scale: "css" });
  await details.click();
  await panel.getByText("Source records and model information", { exact: true }).click();
  await expect(panel.getByText("First recorded flooding", { exact: true })).toBeVisible();
  await expect(panel.getByText("Model checksum: fixture-model-checksum")).toBeVisible();
  await panel.getByRole("button", { name: "Hide calculation details" }).click();
  await expect(panel.getByText("Model checksum: fixture-model-checksum")).toHaveCount(0);
  expect(posts).toHaveLength(0);
});

test("view-only staff receive automatic read-only predictions", async ({ page }) => {
  const posts = await setup(page, { zone: true, readOnly: true });
  const panel = await openPrediction(page);
  await expect(panel.getByText(/Approximately.*remaining/)).toBeVisible();
  await expectNoManualFields(panel);
  expect(posts).toHaveLength(0);
});

for (const missing of ["missing", "unlinked", "unsupported"] as const) {
  test(`automatic ${missing} explanation has no manual fallback`, async ({ page }) => {
    const requests: string[] = [];
    page.on("request", request => { if (/duration-preview|review-suggestion/.test(request.url())) requests.push(request.url()); });
    await setup(page, { zone: true, [missing]: true });
    const panel = await openPrediction(page);
    await expect(panel.getByText("Estimate unavailable", { exact: true })).toBeVisible();
    await expect(panel.getByText(missing === "unsupported" ? "This location is outside the Pasig model scope." : "No qualified observation time is recorded for this zone; creation time is not a flood observation.")).toBeVisible();
    await expect(panel.getByText(/Detected location:/)).toBeVisible();
    await expectNoManualFields(panel);
    expect(requests).toEqual([]);
  });
}

for (const [state, label] of [
  ["evidence_changed", "Evidence needs review"], ["followup_received", "Evidence needs review"],
  ["evidence_stale", "Evidence expired — needs current evidence"], ["case_closed", "Flood zone inactive"],
] as const) {
  test(`automatic ${state} suppresses a misleading countdown`, async ({ page }) => {
    await setup(page, { zone: true, state });
    const panel = await openPrediction(page);
    await expect(panel.getByText(label, { exact: true })).toBeVisible();
    await expect(panel.getByText(/Approximately.*remaining|^Around /)).toHaveCount(0);
    await expectNoManualFields(panel);
  });
}

test("elapsed prediction asks for a condition check without changing zone status", async ({ page }) => {
  const posts = await setup(page, { zone: true, due: true });
  const panel = await openPrediction(page);
  await expect(panel.getByText("Estimated time passed — check current conditions", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog").locator("dl").filter({ has: page.getByText("Status", { exact: true }) })).toContainText("Active");
  expect(posts).toHaveLength(0);
});

test("automatic calculation failure has a visible retry and recovers", async ({ page }) => {
  const posts = await setup(page, { zone: true, getFailure: true });
  await page.clock.setFixedTime(new Date(stamp));
  const panel = await openPrediction(page);
  await expect(panel.getByRole("alert")).toContainText("model is temporarily unavailable");
  await panel.getByRole("button", { name: "Retry prediction" }).click();
  await expect(panel.getByText("Approximately 3h remaining", { exact: true })).toBeVisible();
  await expect(panel.getByRole("alert")).toHaveCount(0);
  expect(posts).toHaveLength(0);
});

test("prediction loading preserves existing expiry", async ({ page }) => {
  await setup(page, { zone: true });
  let release!: () => void;
  const ready = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/admin/zones/9/subsidence-prediction", async route => {
    await ready;
    await route.fulfill({ json: { zone_id: 9, state: "unavailable", evaluated_at: stamp, city: "Pasig", barangays: ["Maybunga"], reasons: ["No qualified observation time."], quantiles: [], reference: null, latest_wet: null, evidence: [], nearby_report_count: 0, model: null } });
  });
  const panel = await openPrediction(page);
  await expect(panel.getByText("Calculating from recorded zone evidence…", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog").getByText("Expires", { exact: true })).toBeVisible();
  release();
  await expect(panel.getByText("Estimate unavailable", { exact: true })).toBeVisible();
  await expect(panel.getByText("Calculating from recorded zone evidence…", { exact: true })).toHaveCount(0);
});

test("official registration simulation is automatic and visibly distinct from an observation", async ({ page }, info) => {
  const posts = await setup(page, { zone: true, unlinked: true, registrationSimulation: true });
  await page.clock.setFixedTime(new Date(stamp));
  const panel = await openPrediction(page);
  await expect(panel.getByText("Subsidence simulation · registration time proxy")).toBeVisible();
  await expect(panel.getByText("Approximately 3h remaining", { exact: true })).toBeVisible();
  await expect(panel.getByText(/Actual observation time is unknown/)).toBeVisible();
  await expect(panel.getByText(/Pooled Pasig estimate/)).toBeVisible();
  await expect(panel.getByText("Estimate unavailable", { exact: true })).toHaveCount(0);
  await expectNoManualFields(panel);
  await panel.scrollIntoViewIfNeeded();
  const dialog = page.getByRole("dialog", { name: "Flood Zone Details" });
  expect(await dialog.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await expect(dialog.getByText("Expires", { exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath("automatic-registration-simulation.png") });
  await panel.getByRole("button", { name: "View calculation details" }).click();
  await panel.getByText("Source records and model information", { exact: true }).click();
  await expect(panel.getByText(/Simulation registration record #140/)).toBeVisible();
  expect(posts).toHaveLength(0);
});

test("pooled transfer estimate does not claim barangay-specific training accuracy", async ({ page }) => {
  await setup(page, { zone: true, pooled: true });
  const panel = await openPrediction(page);
  await expect(panel.getByText(/Approximately.*remaining/)).toBeVisible();
  await expect(panel.getByText(/Pooled Pasig transfer:.*accuracy is unverified/)).toBeVisible();
  await expectNoManualFields(panel);
});

test("calculation details lazily show source-labelled context without extra inputs", async ({ page },info) => {
  const requests:string[]=[];
  page.on("request",r=>{if(r.url().endsWith("/prediction-features"))requests.push(r.url());});
  await setup(page,{zone:true});
  await page.route("**/admin/zones/9/prediction-features",route=>route.fulfill({json:{schema_version:"flood_features_v1",recorded_at:stamp,observed_at:null,
    depth_cm:20.32,depth_basis:"reported_canonical_gauge_proxy",errors:[],environment:{elevation_m:14,rainfall_previous_3h_mm:1.3,errors:[]}}}));
  const panel=await openPrediction(page);
  await expect(panel.getByText(/Approximately.*remaining/)).toBeVisible();
  expect(requests).toHaveLength(0);
  await panel.getByRole("button",{name:"View calculation details"}).click();
  await expect(panel.getByText("Terrain background: 14 m (90 m modelled surface)")).toBeVisible();
  await expect(panel.getByText("Rainfall background, previous 3 hours: 1.3 mm (coarse weather grid)")).toBeVisible();
  await expect(panel.getByText(/displayed baseline does not yet use terrain or rainfall/)).toBeVisible();
  await expectNoManualFields(panel);
  expect(await panel.evaluate(e=>e.scrollWidth<=e.clientWidth)).toBe(true);
  await panel.getByText("Current model input context").scrollIntoViewIfNeeded();
  await page.screenshot({path:info.outputPath("model-input-context.png")});
});

test("input context failure is visible and retries without losing the forecast", async ({ page }) => {
  await setup(page,{zone:true});let calls=0;
  await page.route("**/admin/zones/9/prediction-features",route=>++calls===1?route.fulfill({status:503,json:{detail:"Model input context is unavailable."}}):route.fulfill({json:{errors:[],environment:{errors:["Modelled elevation unavailable; no value was substituted."]}}}));
  const panel=await openPrediction(page);
  await panel.getByRole("button",{name:"View calculation details"}).click();
  await expect(panel.getByRole("alert")).toContainText("Model input context is unavailable.");
  await expect(panel.getByText(/Approximately.*remaining/)).toBeVisible();
  await panel.getByRole("button",{name:"Retry model inputs"}).click();
  await expect(panel.getByText("Modelled elevation unavailable; no value was substituted.")).toBeVisible();
  await expectNoManualFields(panel);
});

for (const [mode, age] of [["registration proxy", "0"], ["recorded observation", "360"]] as const) {
  test(`calculation walkthrough explains the real formula for ${mode}`, async ({ page }, info) => {
    const posts = await setup(page, { zone: true });
    const calculation = calculations[age] as DurationCalculation;
    const simulation = age === "0";
    const model = { status: "research_model_available", supported_barangays: ["Dela Paz", "Maybunga", "Santolan", "Sta. Lucia"], model_sha256: "fixture" };
    await page.route("**/admin/zones/9/subsidence-prediction", route => route.fulfill({ json: {
      zone_id: 9, state: simulation ? "unavailable" : "estimated", city: "Pasig", barangays: ["Maybunga"],
      evaluated_at: stamp, prediction_as_of_at: stamp, reasons: [], evidence: [], nearby_report_count: 0, model,
      reference: simulation ? null : { observed_at: calculation.reference_at, available_at: stamp, source_id: 4, source_kind: "original_citizen_observation" }, latest_wet: null,
      quantiles: simulation ? [] : calculation.quantiles, calculation: simulation ? null : calculation,
      registration_simulation: simulation ? { status: "research_estimate", reference_at: calculation.reference_at, prediction_as_of_at: stamp, quantiles: calculation.quantiles, model, calculation } : null,
    } }));
    const panel = await openPrediction(page);
    await panel.getByRole("button", { name: "View calculation details" }).click();
    const walkthrough = panel.locator('[aria-label="Calculation walkthrough"]');
    await expect(walkthrough.getByRole("heading", { name: "How this estimate is calculated" })).toBeVisible();
    await expect(walkthrough.getByText("ln(T) = μ + σ × Z", { exact: true })).toBeVisible();
    await expect(walkthrough.getByText(/Total duration = exp\(6.964058/)).toBeVisible();
    await expect(walkthrough.getByText(/Remaining at anchor =/)).toBeVisible();
    await expect(walkthrough.getByText(/Turn the duration into a date/)).toBeVisible();
    await expect(walkthrough.getByText(/does not mean the forecast is proven 80% accurate/)).toBeVisible();
    if (simulation) await expect(walkthrough.getByText(/We do not know when flooding actually began/)).toBeVisible();
    await walkthrough.getByText("Elapsed-time formula", { exact: true }).click();
    await expect(walkthrough.getByText("p = F(a) + q × (1 − F(a))", { exact: true })).toBeVisible();
    await expect(walkthrough.getByText(new RegExp(`Here a = ${age} minutes`))).toBeVisible();
    await expectNoManualFields(panel);
    expect(await walkthrough.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
    await walkthrough.getByText("Elapsed-time formula", { exact: true }).click();
    await walkthrough.getByRole("heading", { name: "How this estimate is calculated" }).scrollIntoViewIfNeeded();
    await page.screenshot({ path: info.outputPath(`calculation-${age}-steps.png`) });
    await walkthrough.getByText(/Turn the duration into a date/).scrollIntoViewIfNeeded();
    await page.screenshot({ path: info.outputPath(`calculation-${age}-result.png`) });
    expect(posts).toHaveLength(0);
  });
}

test("approved citizen submission simulates a cross-barangay zone without claiming an observation", async ({ page }, info) => {
  const posts = await setup(page, { zone: true });
  const calculation = calculations["0"] as DurationCalculation;
  const model = { status: "research_model_available", supported_barangays: ["Dela Paz", "Maybunga", "Santolan", "Sta. Lucia"], model_sha256: "fixture" };
  await page.route("**/admin/zones/9/subsidence-prediction", route => route.fulfill({ json: {
    zone_id: 9, state: "unavailable", city: "Pasig", barangays: ["San Nicolas", "Santo Tomas"],
    evaluated_at: stamp, reasons: ["No qualified observation time is recorded for this zone; creation time is not a flood observation."],
    evidence: [], reference: null, latest_wet: null, quantiles: [], model,
    warnings: ["Shared Pasig estimate across these barangays; separate street or barangay effects are not learned, and local accuracy is unverified."],
    submission_simulation: { status: "research_estimate", input_provenance: "citizen_submission_proxy_simulation",
      reference_at: calculation.reference_at, prediction_as_of_at: stamp, quantiles: calculation.quantiles,
      model, calculation, pooled_geographic_transfer: true },
    submission_report_id: 16, submission_audit_id: 164, submission_approval_audit_id: 166,
  } }));
  const panel = await openPrediction(page);
  await expect(panel.getByText("Detected location: San Nicolas / Santo Tomas, Pasig")).toBeVisible();
  await expect(panel.getByText("Subsidence simulation · report submission time proxy")).toBeVisible();
  await expect(panel.getByText(/Uses approved report #16 submitted/)).toBeVisible();
  await expect(panel.getByText(/Actual observation time is unknown/)).toBeVisible();
  await expect(panel.getByText("Estimate unavailable", { exact: true })).toHaveCount(0);
  await expect(panel.getByText(/crosses or has ambiguous barangay/)).toHaveCount(0);
  await panel.getByRole("button", { name: "View calculation details" }).click();
  await expect(panel.getByText(/Citizen report submitted:/)).toBeVisible();
  await expect(panel.getByText(/First recorded flooding:/)).toHaveCount(0);
  await expectNoManualFields(panel);
  expect(await panel.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await panel.getByText(/Citizen report submitted:/).scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath("citizen-submission-simulation.png") });
  expect(posts).toHaveLength(0);
});
