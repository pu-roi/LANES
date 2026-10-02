import { expect as baseExpect, test, type Page, type Route } from "@playwright/test";
import { readFileSync } from "node:fs";

const expect = baseExpect.configure({ timeout: 30_000 });
test.setTimeout(90_000);
test.use({ browserName: "chromium" });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });

const article = {
  id: 1, title: "Flood reports in Pasig", excerpt: "Publisher flood report for inspection.", canonical_url: "https://example.org/news/1",
  publisher_source_id: "feedspot-01", publisher: "GMA News Online", published_at: "2026-10-01T13:00:00Z", last_seen_at: "2026-10-02T10:00:00Z",
  body_status: "available", article_error: null, review_state: "pending", processing_status: "completed", latest_run_id: 12,
};
const input = { title: article.title, canonical_url: article.canonical_url, publisher: "feedspot-01", excerpt: article.excerpt,
  article_text: "Current captured evidence: knee-deep flooding in Maybunga, Pasig.", published_at: article.published_at };
const claim = { raw_place_name: "Maybunga", canonical_city: "City of Pasig", canonical_barangay: "Maybunga", canonical_road: null,
  depth_raw: "knee-deep", depth_formatted: "Knee-deep (0.5 m)", condition: "active", event_time_resolved: null, event_time_kind: "unspecified",
  evidence_sentence: input.article_text, uncertainty_reasons: ["event_time_unknown"], is_historical: false, is_forecast: false,
  is_negated: false, road_passability: "unknown", action_type: "flagged_review", road_placement: { status: "unresolved", reason: "no_reported_road" } };
const summary = { location: "Maybunga", area: "City of Pasig", location_qualifier: null, water_level: "Knee-deep (0.5 m)",
  condition: "Flooding reported", flood_time: null, flood_time_label: "Flood time in article", map_status: "Exact map location unknown",
  reading_status: "reported_location", reading_reason: null };
const result = { article_id: 1, claims: [claim], extracted_at: "2026-10-02T10:00:00Z", extractor_version: "test-rules", is_metadata_only: false, errors: [] };
const run = { id: 12, article_version_id: 22, pipeline_version: "test-current", mode: "rules_only", status: "completed", attempt_count: 1,
  next_attempt_at: null, started_at: "2026-10-02T09:59:00Z", completed_at: "2026-10-02T10:00:00Z", error_code: null, result,
  created_at: "2026-10-02T09:59:00Z", updated_at: "2026-10-02T10:00:00Z" };
const detail = {
  article: { ...input, id: 1, publisher_source_id: "feedspot-01", fetched_at: "2026-10-02T09:59:00Z", first_seen_at: "2026-10-02T09:59:00Z",
    last_seen_at: article.last_seen_at, article_error: null, review_state: "pending", feed_entries: [] },
  publisher: article.publisher, body_status: "available",
  runs: [run, { ...run, id: 11, article_version_id: 21, pipeline_version: "test-old", result: { ...result, claims: [] } }],
  versions: [{ id: 22, input_fingerprint: "a".repeat(64), input_snapshot: input, created_at: "2026-10-02T09:59:00Z" },
    { id: 21, input_fingerprint: "b".repeat(64), input_snapshot: { ...input, title: "Older flood report",
      article_text: "Older captured evidence from a different article version.", published_at: "2026-09-30T12:00:00Z" }, created_at: "2026-09-30T12:05:00Z" }],
  history_total: 2, history_limit: 20, read_only: true, flood_summaries: { 12: [summary], 11: [] },
};
const resultItem = { key: "12:0", run_id: 12, claim_index: 0, article_id: 1, article_version_id: 22, title: article.title,
  publisher_source_id: article.publisher_source_id, publisher: article.publisher, published_at: article.published_at,
  extracted_at: result.extracted_at, captured_at: run.created_at, saved_at: detail.article.first_seen_at, claim, summary };
const resultDetail = { item: resultItem, claim, captured_input: input, input_fingerprint: "a".repeat(64),
  pipeline_version: "test-current", extraction_errors: [], is_metadata_only: false, lifecycle_status: "not_available", read_only: true };
const counts = { ready: 0, needs_checking: 13, no_locations: 0, waiting: 0, processing: 0, processing_failed: 0, retrieval_failed: 0, missing_text: 0 };

function fulfill(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function setup(page: Page, articleDetail: unknown = detail, fail = { list: 0, detail: 0 }) {
  const reads: URL[] = [], mutations: string[] = [];
  await page.addInitScript(() => localStorage.setItem("lanes_token", "test-only-token"));
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.includes("/admin/news")) {
      reads.push(url);
      if (route.request().method() !== "GET") mutations.push(route.request().method());
      expect(route.request().headers().authorization).toBe("Bearer test-only-token");
      if (url.pathname.endsWith("/results")) return fulfill(route, { items: [resultItem], total: 1, page: 1, page_size: 12, pages: 1,
        publishers: [{ id: "feedspot-01", label: article.publisher }], scope: "latest_reported_locations", read_only: true });
      if (url.pathname.includes("/results/")) return fulfill(route, resultDetail);
      if (url.pathname.endsWith("/collection")) {
        if (fail.list > 0) return fulfill(route, { detail: "News storage unavailable" }, 503);
        return fulfill(route, { items: [{ ...article, collection_status: "needs_checking", collection_label: "Needs checking",
          collection_reason: "Some extracted mentions need checking.", location_count: 1, questionable_count: 1 }], total: 13,
          page: Number(url.searchParams.get("page") ?? 1), page_size: 12, pages: 2, counts, publishers: [{ id: "feedspot-01", label: article.publisher }] });
      }
      if (fail.detail > 0) return fulfill(route, { detail: "Detail storage unavailable" }, 503);
      return fulfill(route, articleDetail);
    }
    if (url.pathname.endsWith("/auth/test-token")) return fulfill(route, { id: 987654, username: "news-ui-test", role: { name: "Super Admin" } });
    if (url.pathname.includes("/notifications")) return fulfill(route, { notifications: [], total: 0, unread_count: 0, has_more: false });
    return fulfill(route, []);
  });
  await page.goto("/admin/news", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Flood Locations from News", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Collection status", exact: true }).click();
  return { reads, mutations };
}

test("article inspection preserves server filters, page, focus and input provenance", async ({ page }, info) => {
  const { reads, mutations } = await setup(page);
  const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
  await drawer.getByRole("textbox", { name: "Search collection" }).fill("Pasig");
  await drawer.getByRole("button", { name: "Search", exact: true }).click();
  await expect.poll(() => reads.some((url) => url.searchParams.get("search") === "Pasig")).toBe(true);
  await drawer.getByRole("button", { name: "Publisher", exact: true }).click();
  await drawer.getByRole("button", { name: "GMA News Online", exact: true }).click();
  await expect.poll(() => reads.some((url) => url.searchParams.get("publisher") === "feedspot-01")).toBe(true);
  await drawer.getByRole("button", { name: "Publisher", exact: true }).click();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeVisible();
  await expect(drawer.getByRole("button", { name: "Publisher", exact: true })).toBeFocused();
  await drawer.getByRole("button", { name: info.project.name === "mobile-chromium" ? "Next" : "Next Page", exact: true }).click();
  await expect(drawer.getByText(/13 saved articles match these filters · Page 2 of 2/)).toBeVisible();
  const open = drawer.getByRole("button", { name: `View article: ${article.title}` });
  await open.click();
  await expect(drawer.getByText(input.article_text, { exact: true })).toBeHidden();
  await drawer.getByText("Full article text", { exact: true }).click();
  await expect(drawer.getByText(input.article_text, { exact: true })).toBeVisible();
  await expect(drawer.getByRole("link", { name: "Read on GMA News Online" })).toHaveAttribute("rel", "noopener noreferrer");
  await drawer.getByText("More details", { exact: true }).click();
  await drawer.getByRole("button", { name: "View extraction #11", exact: true }).click();
  await expect(drawer.getByText("No flood locations extracted.", { exact: true })).toBeVisible();
  await drawer.getByText("Captured article text", { exact: true }).click();
  await expect(drawer.getByText("Older captured evidence from a different article version.", { exact: true })).toBeVisible();
  await expect(drawer.getByText("Article published: Sep 30, 2026, 8:00 PM", { exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Back to collection" }).click();
  await expect(open).toBeFocused();
  await expect(drawer.getByRole("textbox", { name: "Search collection" })).toHaveValue("Pasig");
  await expect(drawer.getByText(/Page 2 of 2/).first()).toBeVisible();
  await drawer.getByRole("button", { name: "Close collection status" }).focus();
  await page.keyboard.press("Shift+Tab");
  expect(await page.evaluate(() => Boolean(document.activeElement?.closest('[role="dialog"]')))).toBe(true);
  await page.keyboard.press("Escape");
  await expect(drawer).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Collection status", exact: true })).toBeFocused();
  expect(mutations).toEqual([]);
});

test("list and detail failures surface errors and retry successfully", async ({ page }) => {
  const failures = { list: 1, detail: 1 };
  const { mutations } = await setup(page, detail, failures);
  const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
  await expect(drawer.getByRole("alert")).toContainText("News storage unavailable");
  failures.list = 0;
  await drawer.getByRole("button", { name: "Retry collection" }).click();
  await drawer.getByRole("button", { name: `View article: ${article.title}` }).click();
  await expect(drawer.getByRole("alert")).toContainText("Detail storage unavailable");
  failures.detail = 0;
  await drawer.getByRole("button", { name: "Retry article" }).click();
  await drawer.getByText("Full article text", { exact: true }).click();
  await expect(drawer.getByText(input.article_text, { exact: true })).toBeVisible();
  expect(mutations).toEqual([]);
});

test("missing bodies and empty processing history remain explicit on narrow screens", async ({ page }) => {
  await setup(page, { ...detail, article: { ...detail.article, article_text: null, article_error: "Article HTTP 403" },
    body_status: "error", runs: [], versions: [], history_total: 0 });
  const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
  await drawer.getByRole("button", { name: `View article: ${article.title}` }).click();
  await expect(drawer.getByText("Latest article retrieval failed: Article HTTP 403")).toBeVisible();
  await expect(drawer.getByText("Full article text unavailable.")).toBeVisible();
  await drawer.getByText("More details", { exact: true }).click();
  await expect(drawer.getByText("No processing history recorded.")).toBeVisible();
  for (const viewport of [{ width: 320, height: 640 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(viewport);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const bounds = await drawer.boundingBox();
    expect(bounds!.height).toBeLessThanOrEqual(viewport.height);
    await expect(drawer.getByRole("button", { name: "Close collection status" })).toBeVisible();
  }
});

test("failed recorded runs expose their error without showing older claims as current", async ({ page }) => {
  await setup(page, { ...detail, runs: [{ ...run, status: "failed", error_code: "extraction_failed", result: null }, detail.runs[1]], flood_summaries: { 11: [] } });
  const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
  await drawer.getByRole("button", { name: `View article: ${article.title}` }).click();
  await drawer.getByText("More details", { exact: true }).click();
  await drawer.getByRole("button", { name: "View extraction #12", exact: true }).click();
  await expect(drawer.getByRole("alert")).toContainText("extraction_failed");
  await expect(drawer.getByRole("heading", { name: "Maybunga", exact: true })).toHaveCount(0);
});

test("a saved publisher article renders its actual captured body and extraction", async ({ page }) => {
  test.skip(!process.env.NEWS_ARTICLE_PAGE_FIXTURE || !process.env.NEWS_ARTICLE_DETAIL_FIXTURE, "Requires recorded real-publisher responses.");
  const savedPage = JSON.parse(readFileSync(process.env.NEWS_ARTICLE_PAGE_FIXTURE!, "utf8"));
  const savedDetail = JSON.parse(readFileSync(process.env.NEWS_ARTICLE_DETAIL_FIXTURE!, "utf8"));
  await setup(page, savedDetail);
  await page.route("**/api/v1/admin/news/collection?**", (route) => fulfill(route, { ...savedPage, counts,
    items: savedPage.items.map((item: object) => ({ ...item, collection_label: "Locations available", collection_reason: "Recorded evidence", location_count: 1, questionable_count: 0 })) }));
  const drawer = page.getByRole("dialog", { name: "Collection status", exact: true });
  await drawer.getByRole("button", { name: "Refresh collection" }).click();
  await drawer.getByRole("button", { name: `View article: ${savedDetail.article.title}` }).click();
  await drawer.getByText("Full article text", { exact: true }).click();
  const latestVersion = savedDetail.versions.find((version: { id: number }) => version.id === savedDetail.runs[0]?.article_version_id);
  await expect(drawer.getByText(latestVersion?.input_snapshot.article_text ?? savedDetail.article.article_text, { exact: true })).toBeVisible();
  await expect(drawer.getByText("Sep 9, 2026, 5:03 PM", { exact: true })).toBeVisible();
  await drawer.getByText("More details", { exact: true }).click();
  await drawer.getByRole("button", { name: `View extraction #${savedDetail.runs[0].id}`, exact: true }).click();
  await drawer.locator("summary").filter({ hasText: /^Extracted locations/ }).click();
  await expect(drawer.getByRole("heading", { name: /NS Amoranto/ }).first()).toBeVisible();
});

test("Info keeps processing history inside Source Article with responsive panes", async ({ page }) => {
  await setup(page);
  await page.getByRole("button", { name: "Close collection status" }).click();
  const open = page.getByRole("button", { name: /^Info: Maybunga/ });
  await open.click();
  const dialog = page.getByRole("dialog", { name: "News Flood Details", exact: true });
  await expect(dialog.getByRole("heading", { name: "Maybunga", exact: true })).toBeVisible();
  await expect(dialog.getByText("Not stated in article", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Full article text", { exact: true })).toHaveCount(0);
  const evidence = dialog.getByRole("region", { name: "News evidence", exact: true });
  const history = dialog.getByRole("region", { name: "Article processing records", exact: true });
  const isMobile = (page.viewportSize()?.width ?? 0) < 1024;
  await expect(history).toHaveCount(0);
  await expect(dialog.getByRole("button", { name: "Processing history", exact: true })).toHaveCount(0);
  const viewport = page.viewportSize()!;
  const bounds = await dialog.boundingBox();
  expect(bounds!.height).toBeLessThanOrEqual(viewport.height);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(await evidence.evaluate((node) => getComputedStyle(node).overflowY)).toBe("auto");
  await dialog.getByRole("button", { name: "Source Article", exact: true }).click();
  await expect(dialog.getByRole("heading", { name: article.title })).toBeVisible();
  await expect(dialog.getByText("Saved in LANES", { exact: true })).toBeVisible();
  await expect(dialog.getByText(input.article_text, { exact: true })).toBeVisible();
  await expect(evidence.getByText(article.excerpt, { exact: true })).toHaveCount(0);
  if (isMobile) {
    await expect(history).toBeHidden();
    await dialog.getByRole("button", { name: "Processing history", exact: true }).click();
    await expect(evidence).toBeHidden();
    await expect(history.getByRole("heading", { name: "Processing history", exact: true })).toBeVisible();
  } else {
    await expect(history.getByRole("heading", { name: "Processing history", exact: true })).toBeVisible();
    const left = await evidence.boundingBox(), right = await history.boundingBox();
    expect(left!.x + left!.width).toBeLessThanOrEqual(right!.x);
    expect(await history.evaluate((node) => getComputedStyle(node).overflowY)).toBe("auto");
    await expect(evidence.getByText(input.article_text, { exact: true })).toBeVisible();
  }
  const recordOpener = history.getByRole("button", { name: "View extraction #11", exact: true });
  await recordOpener.click();
  const record = dialog.getByRole("region", { name: "Extraction record inspection", exact: true });
  await expect(record.getByRole("heading", { name: "Extraction record #11", exact: true })).toBeFocused();
  await expect(history).toBeHidden();
  await expect(record.getByText("No flood locations extracted.", { exact: true })).toBeVisible();
  await record.getByRole("button", { name: "Article", exact: true }).click();
  await expect(record.getByRole("heading", { name: "Older flood report", exact: true })).toBeVisible();
  await expect(record.getByText("Older captured evidence from a different article version.", { exact: true })).toBeVisible();
  await record.getByRole("button", { name: "Technical", exact: true }).click();
  await expect(record.getByText("test-old", { exact: true })).toBeVisible();
  await record.getByRole("button", { name: "Back to source article", exact: true }).click();
  await expect(recordOpener).toBeFocused();
  if (isMobile) await dialog.getByRole("button", { name: "Article", exact: true }).click();
  await expect(evidence.getByText(input.article_text, { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Flood Details", exact: true }).click();
  await expect(dialog.getByRole("heading", { name: "Maybunga", exact: true })).toBeVisible();
  await expect(history).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(open).toBeFocused();
});
