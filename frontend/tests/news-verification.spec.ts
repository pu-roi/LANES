import { expect as baseExpect, test } from '@playwright/test';
import { installChrisFixtures, expectNoOverflow } from './helpers/chrisIntegration';

const expect = baseExpect.configure({ timeout: 15_000 });
test.setTimeout(120_000);
test.use({ browserName: 'chromium' });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });

const date = '2026-09-09T08:30:00Z';
const locationIssue = { field: 'location', label: 'Location', state: 'uncertain', code: 'location_unresolved',
  reason: 'The exact affected location has not been established in the saved placement evidence.' };
const roadIssue = { field: 'road', label: 'Street / road', state: 'missing', code: 'road_unresolved',
  reason: 'The source mentions a road or section, but its street identity was not resolved.' };
const depthIssue = { field: 'water_level', label: 'Water level / depth', state: 'missing', code: 'depth_missing',
  reason: 'No water level or depth wording was saved from the article. Check the source; do not infer a depth from the hazard map.' };
const baseSummary = { location: 'Talipapa Alley', area: 'Quezon City', location_qualifier: null, water_level: '8 inches',
  condition: 'Flooding reported', passability: 'Passable with caution; vehicle types not specified', flood_time: date,
  flood_time_label: 'Flood observed in article', map_status: 'Exact map location unknown', reading_status: 'reported_location',
  reading_reason: null, verification_status: 'needs_verification', verification_issues: [locationIssue, roadIssue] };
const claim = { raw_place_name: 'Talipapa Alley', canonical_city: 'Quezon City', canonical_road: null, canonical_barangay: null,
  depth_raw: '8 inches', condition: 'active', event_time_resolved: date, event_time_kind: 'observation', evidence_sentence: 'Talipapa Alley - 8 inches, gutter deep' };
const item = { key: '1:0', run_id: 1, claim_index: 0, article_id: 274, article_version_id: 573,
  title: 'Saved flood article', publisher: 'Fixture publisher', publisher_source_id: 'fixture', published_at: date,
  captured_at: date, saved_at: date, extracted_at: date, claim, summary: baseSummary };

test('field verification badges explain incomplete evidence without changing records', async ({ page }, info) => {
  const { errors } = await installChrisFixtures(page, 'Admin');
  const mutations: string[] = [];
  const items = [item,
    { ...item, key: '1:1', claim_index: 1, summary: { ...baseSummary, location: 'Missing measurement road', water_level: 'Not stated in article', verification_issues: [locationIssue, depthIssue] } },
    { ...item, key: '1:2', claim_index: 2, summary: { ...baseSummary, location: 'Palali St at NS Amoranto', area: 'Sienna, Quezon City',
      water_level: '37 inches, waist deep', placement_is_estimate: true, map_status: 'Estimated zone plotted; exact flood extent needs verification',
      verification_issues: [{ ...locationIssue, code: 'estimated_extent', reason: 'An estimated zone is plotted. Its exact flooded section and extent still need verification.' }] } },
    { ...item, key: '1:3', claim_index: 3, summary: { ...baseSummary, location: 'Older saved record', verification_status: undefined, verification_issues: undefined } }];
  await page.route('**/api/v1/admin/news/**', route => {
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() !== 'GET') mutations.push(route.request().method());
    if (path.endsWith('/results')) return route.fulfill({ json: { items, total: items.length, page: 1, page_size: 12, pages: 1, publishers: [], scope: 'latest_reported_locations', read_only: true } });
    if (path.includes('/results/')) return route.fulfill({ json: { item, claim, captured_input: { title: item.title, publisher: 'fixture',
      canonical_url: 'https://example.org/flood', article_text: claim.evidence_sentence, published_at: date }, extraction_errors: [], source_review: null } });
    return route.fulfill({ json: { state: 'not_recorded', status_label: 'No worker cycle recorded', read_only: true, checked_at: date,
      queue_counts: {}, stages: {}, feed_counts: {}, running: false, enabled_sources: 0, collection_interval_minutes: 30 } });
  });
  if (info.project.name === 'desktop-chromium') await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/admin/news', { waitUntil: 'domcontentloaded' });
  await page.getByRole('tab', { name: 'Flooded Areas', exact: true }).click();
  const talipapa = page.getByRole('article', { name: 'Flood observation: Talipapa Alley', exact: true });
  await expect(talipapa.getByText('Needs Verification', { exact: true })).toBeVisible();
  const fields = talipapa.getByRole('list', { name: 'Fields needing verification' });
  await expect(fields.getByRole('listitem')).toHaveCount(2);
  await expect(fields.getByText('Street / road', { exact: true })).toBeVisible();
  await expect(fields.getByText('Water level / depth', { exact: true })).toHaveCount(0);
  await expect(talipapa.getByText('8 inches', { exact: true })).toBeVisible();
  await talipapa.getByText('Why these need checking', { exact: true }).click();
  await expect(talipapa.getByText(roadIssue.reason, { exact: false })).toBeVisible();
  const missing = page.getByRole('article', { name: 'Flood observation: Missing measurement road', exact: true });
  await expect(missing.getByRole('list', { name: 'Fields needing verification' }).getByText('Water level / depth', { exact: true })).toBeVisible();
  const estimated = page.getByRole('article', { name: 'Flood observation: Palali St at NS Amoranto', exact: true });
  await estimated.getByText('Why these need checking', { exact: true }).click();
  await expect(estimated.getByText(/An estimated zone is plotted/)).toBeVisible();
  await expect(estimated.getByText('37 inches, waist deep', { exact: true })).toBeVisible();
  const old = page.getByRole('article', { name: 'Flood observation: Older saved record', exact: true });
  await expect(old.getByText('Verification status unavailable for this saved record.')).toBeVisible();
  await expectNoOverflow(page);
  await page.screenshot({ path: info.outputPath('verification-cards.png'), fullPage: true });
  await talipapa.getByRole('button', { name: /^Info:/ }).click();
  const dialog = page.getByRole('dialog', { name: 'News Flood Details', exact: true });
  await expect(dialog.getByText('Needs Verification', { exact: true })).toBeVisible();
  await dialog.getByText('Why these need checking', { exact: true }).click();
  await expect(dialog.getByText(roadIssue.reason, { exact: false })).toBeVisible();
  await expect(dialog.getByText(claim.evidence_sentence, { exact: true })).toBeVisible();
  await expectNoOverflow(page);
  await page.screenshot({ path: info.outputPath('verification-details.png'), fullPage: true });
  await page.keyboard.press('Escape');
  if (info.project.name === 'mobile-chromium') {
    for (const viewport of [{ width: 320, height: 740 }, { width: 844, height: 390 }]) {
      await page.setViewportSize(viewport);
      await expect(talipapa.getByText('Needs Verification', { exact: true })).toBeVisible();
      await expectNoOverflow(page);
    }
  }
  expect(mutations).toEqual([]);
  expect(errors).toEqual([]);
});
