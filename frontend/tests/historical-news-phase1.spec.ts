import { expect, test } from '@playwright/test';
import { installChrisFixtures, fixtureZone, floodHistoryResponse, floodMapResponse, zoneMapResponse, expectNoOverflow } from './helpers/chrisIntegration';
import { mapLayers } from './helpers/mapLayers';
import { inspectZoneGroup } from './helpers/zoneQueue';

test.setTimeout(120_000);
test.use({ browserName: 'chromium' });
if (process.env.PLAYWRIGHT_CHROME_PATH) test.use({ launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROME_PATH } });
const dataset = 'capstone-september-2026-v1';
const designation = { schema_version: 'historical-import-v1', dataset_id: dataset, disposition: 'active_demo',
  label: 'Historical demonstration — September 2026', occurrence_date: '2026-09-24', observed_at: null, precision: 'date',
  closure_basis: 'demo_administration', simulated_interval_minutes: null, imported_at: '2026-10-22T02:00:00Z',
  source_url: 'https://example.org/fictional', source_publisher: 'Fictional source', source_excerpt: 'Fictional Road was flooded knee-deep.', article_id: 11, run_id: 21, group_id: 'g0' };
const zone = { ...fixtureZone, historical: designation, affects_routing: false, report_source: 'news',
  reporter_name: designation.source_publisher, reporter_role: 'News report' };
const mention = { id: 'm0', text: 'Fictional Road', label: 'ROAD', start: 0, end: 14 };
const result = { processing_method: 'ner_rules_v1', article_id: 11, claims: [], extracted_at: '2026-10-22T02:00:00Z', extractor_version: 'fictional-test', is_metadata_only: false, errors: [],
  native: { neural_mentions: [mention], effective_mentions: [mention, { id: 'm1', text: 'Pasig City', label: 'CITY', start: 70, end: 80 }], proposals: [{}], abstentions: [{}], graph: { mentions: [mention], facts: [
    { id: 'f0', kind: 'depth', value: 'knee-deep', uncertainty: ['collective'], evidence: [{ start: 0, end: 40, text: designation.source_excerpt }] },
    { id: 'f1', kind: 'time', value: 'September 24, 2026', temporal_role: 'observation', evidence: [{ start: 41, end: 59, text: 'September 24, 2026' }] },
  ] } }, projection: { groups: [{ group_id: 'g0', scope: 'collective', disposition: 'native_only', target_entity_ids: ['m0'], fact_ids: ['f0'], reasons: ['collective_scope_preserved'] }], fact_accounting: [{ fact_id: 'f1', disposition: 'unassigned' }] } };
const summary = { location: 'Fictional Road', area: 'Pasig', water_level: 'knee-deep', condition: 'Flooding reported', flood_time: null, flood_time_label: 'Source observation', map_status: 'Unresolved', reading_reason: 'collective_scope_preserved' };
const item = { key: '21:group:g0', result_kind: 'ner_group', processing_method: 'ner_rules_v1', run_id: 21, article_id: 11, claim_index: null, group_id: 'g0', publisher: 'Fictional source', saved_at: '2026-10-22T02:00:00Z', published_at: '2026-09-24T00:00:00Z', summary };

test('native group and zero-zone source evidence are inspectable with Retry', async ({ page }, info) => {
  await installChrisFixtures(page, 'Admin');
  if (info.project.name === 'mobile-chromium') await page.setViewportSize({ width: 320, height: 740 });
  const requests: string[] = []; let fail = true;
  await page.route('**/api/v1/admin/news/**', async route => {
    requests.push(`${route.request().method()} ${route.request().url()}`);
    if (route.request().url().includes('/results/21/groups/g0')) {
      if (fail) return route.fulfill({ status: 503, json: { detail: 'Fictional temporary storage failure' } });
      return route.fulfill({ json: { item, result, historical_outputs: [], claim: { canonical_road: null, road_passability: 'unknown', evidence_sentence: designation.source_excerpt }, captured_input: { title: 'Fictional article', canonical_url: designation.source_url, publisher: 'Fictional source', article_text: designation.source_excerpt, published_at: item.published_at }, pipeline_version: 'fixture-native', extraction_errors: [], is_metadata_only: false } });
    }
    if (new URL(route.request().url()).pathname.endsWith('/results')) return route.fulfill({ json: { items: [item], total: 1, page: 1, page_size: 12, pages: 1, publishers: [], scope: 'latest_reported_locations', read_only: true } });
    return route.fulfill({ json: { state: 'not_recorded', status_label: 'No worker cycle recorded', queue_counts: {}, stages: {}, feed_counts: {} } });
  });
  await page.goto('/admin/news');
  await page.getByRole('tab', { name: 'Flooded Areas' }).click();
  await page.getByRole('button', { name: /^Info: Fictional Road/ }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'Flood details could not be loaded' })).toBeVisible();
  fail = false; await page.getByRole('button', { name: 'Retry flood details' }).click();
  await expect(page.getByRole('heading', { name: 'Original NER locations (1)' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Rule-based location repairs (1)' })).toBeVisible();
  await expect(page.getByText('collective_scope_preserved', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('No historical geometry qualification saved.', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Inspect placement on map' })).toHaveCount(0);
  await expectNoOverflow(page);
  await page.screenshot({ path: info.outputPath('native-evidence.png'), fullPage: true });
  expect(requests.every(request => request.startsWith('GET '))).toBeTruthy();
});

test('unified history removes the dataset selector and obsolete URL filter while retaining event inspection', async ({ page }, info) => {
  await installChrisFixtures(page, 'Admin');
  if (info.project.name === 'mobile-chromium') await page.setViewportSize({ width: 320, height: 740 });
  const reads: URL[] = [];
  let inspectionUnavailable = true;
  const record = { id: 920, status: 'ended', first_reported_at: null, verified_at: designation.imported_at, ended_at: designation.imported_at,
    origin: 'news', duration_basis: 'demo_administration', closure_basis: 'demo_administration', occurrence_date: '2026-09-24', observation_precision: 'date',
    peak_severity: 'medium', peak_depth: 'knee', historical: designation, duration_minutes: null, supporting_report_count: 0, reporter_count: 0,
    locations: [{ id: 1, location_type: 'road', display_name: 'Fictional Road', normalized_name: 'fictional road', created_at: designation.imported_at }], zones: [{ ...zone, is_active: false }], reports: [], timeline: [], heatmap_features: [] };
  await page.route('**/api/v1/admin/flood-events/**', async route => {
    const url = new URL(route.request().url()); reads.push(url);
    if (url.pathname.endsWith('/records')) return route.fulfill({ json: floodHistoryResponse([record], url.href) });
    if (url.pathname.endsWith('/map')) return route.fulfill({ json: floodMapResponse([record], url.href) });
    if (url.pathname.endsWith('/inspection')) return inspectionUnavailable
      ? route.fulfill({ status: 503, json: { detail: 'Fictional temporary history failure' } })
      : route.fulfill({ json: record });
    if (url.pathname.includes('/inspection/')) return route.fulfill({ json: { items: [], total: 0, page: 1, pages: 1, page_size: 20 } });
    if (url.pathname.endsWith('/export')) return route.fulfill({ body: '[]', contentType: 'application/json', headers: { 'Content-Disposition': 'attachment; filename="fictional.json"' } });
    return route.fallback();
  });
  await page.goto(`/admin/flood-history?dataset_id=${dataset}&event_id=920`);
  await expect(page.getByRole('button', { name: 'Historical dataset' })).toHaveCount(0);
  await expect(page).not.toHaveURL(/dataset_id=/);
  await expect(page).toHaveURL(/event_id=920/);
  await expect(page.getByRole('alert').filter({ hasText: 'Event details could not be loaded' })).toBeVisible();
  inspectionUnavailable = false;
  await page.getByRole('button', { name: 'Retry event details' }).click();
  await expect(page.getByRole('dialog').getByText(designation.label)).toHaveCount(0);
  await expect(page.getByRole('dialog').getByText('2026-09-24', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Close flood event details' }).click();
  await expect(page.getByText('Observed duration not established')).toBeVisible();
  await expectNoOverflow(page);
  await page.screenshot({ path: info.outputPath('dataset-history.png'), fullPage: true });
  await page.getByRole('button', { name: 'Analytics', exact: true }).click();
  const downloaded = page.waitForEvent('download'); await page.getByRole('button', { name: 'Records JSON' }).click(); await downloaded;
  expect(reads.filter(url => /\/(records|map|export)$/.test(url.pathname)).every(url => !url.searchParams.has('dataset_id'))).toBeTruthy();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Historical dataset' })).toHaveCount(0);
  await expect(page).not.toHaveURL(/dataset_id=/);
});

test('public map preserves the existing popup without a presentation label', async ({ page }, info) => {
  await installChrisFixtures(page, 'Commuter');
  await page.route('**/api/v1/reports/active-zones', route => route.fulfill({ json: [zone] }));
  await page.goto('/map');
  await expect.poll(async () => (await mapLayers(page))?.rendered.some(feature => feature.properties?.historical_json?.includes('historical-import-v1')), { timeout: 45_000 }).toBeTruthy();
  const canvas = page.locator('.maplibregl-canvas'); const bounds = await canvas.boundingBox();
  if (!bounds) throw new Error('Fixture map did not render');
  await page.mouse.move(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
  if (info.project.name === 'mobile-chromium') await page.mouse.click(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
  await expect(page.getByText(designation.label, { exact: true })).toHaveCount(0);
  await expect(page.getByText('Source observation 2026-09-24', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Still flooded', exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath('public-demo-map.png') });
});

test('Spatial Operations keeps existing details, confirms deactivation and retains evidence', async ({ page }, info) => {
  await installChrisFixtures(page, 'Admin');
  let active = true; const writes: string[] = [];
  const group = { historical: designation, zone_id: 910, member_count: 1, location: 'Fictional Road', area_summary: 'Pasig', sources: ['news'], severity_levels: ['medium'], depth_levels: ['knee'], evidence: designation.source_excerpt, queued_at: designation.imported_at, group_reason: 'Separate historical demonstration.', bounds: [121.079,14.569,121.081,14.571] };
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url()); const path = url.pathname;
    if (path.endsWith('/admin/zones/910/deactivate')) { writes.push(`${route.request().method()} ${path}`); active = false; return route.fulfill({ json: { ...zone, is_active: false } }); }
    if (path.endsWith('/admin/zones/queue')) return route.fulfill({ json: { items: active ? [group] : [], zones: [], total: active ? 1 : 0, item_total: active ? 1 : 0, counts: { all: active ? 1 : 0, news: active ? 1 : 0, user_reports: 0, official: 0, other: 0 }, facets: { cities: ['Pasig'], barangays: [] }, page: 1, pages: 1, page_size: 20, read_only: true } });
    if (path.endsWith('/admin/zones/groups/910/members')) return route.fulfill({ json: { zone_id: 910, zones: active ? [zone] : [], total: active ? 1 : 0, page: 1, pages: 1, page_size: 20, group_reason: group.group_reason, read_only: true } });
    if (path.endsWith('/admin/zones/map')) return route.fulfill({ json: zoneMapResponse(active ? [zone] : [], url.href) });
    if (path.endsWith('/admin/zones/910')) return route.fulfill({ json: { ...zone, is_active: active } });
    if (path.includes('/admin/flood-events/')) {
      const record = { id: 920, historical: designation, status: active ? 'active' : 'ended', verified_at: designation.imported_at, ended_at: active ? null : designation.imported_at, peak_severity: 'medium', peak_depth: 'knee', reports: [], timeline: [], zones: [{ ...zone, is_active: active }], locations: [], heatmap_features: [] };
      if (path.endsWith('/records')) return route.fulfill({ json: floodHistoryResponse([record], url.href) });
      if (path.endsWith('/map')) return route.fulfill({ json: floodMapResponse([record], url.href) });
      if (path.endsWith('/inspection')) return route.fulfill({ json: record });
    }
    if (path.endsWith('/reports/active-zones')) return route.fulfill({ json: active ? [zone] : [] });
    return route.fallback();
  });
  await page.goto('/admin/map');
  await page.getByRole('button', { name: /Active Zones/ }).click();
  const panel = page.getByRole('region', { name: 'Active Zones', exact: true });
  await expect(panel.getByText(designation.label, { exact: false })).toHaveCount(0);
  await inspectZoneGroup(page, 'Fictional Road');
  await panel.getByRole('button', { name: 'Info for Zone #910', exact: true }).click();
  const details = page.getByRole('dialog', { name: 'Flood Zone Details' });
  await expect(details.getByText(designation.label, { exact: true })).toHaveCount(0);
  await expect(details.getByText('Severity:', { exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath('admin-demo-details.png') });
  await details.getByRole('button', { name: 'Deactivate zone', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Confirm Deactivation', exact: true })).toBeVisible();
  expect(writes).toEqual([]);
  await page.getByRole('button', { name: 'Deactivate Zone', exact: true }).click();
  await expect.poll(() => writes).toEqual(['PATCH /api/v1/admin/zones/910/deactivate']);
  const publicPage = await page.context().newPage();
  await installChrisFixtures(publicPage, 'Commuter');
  await publicPage.route('**/api/v1/reports/active-zones', route => route.fulfill({ json: active ? [zone] : [] }));
  try {
    await publicPage.goto('/map');
    await expect.poll(async () => (await mapLayers(publicPage))?.rendered.filter(feature => feature.properties?.historical_json?.includes('historical-import-v1')).length ?? -1, { timeout: 45_000 }).toBe(0);
  } finally { await publicPage.close(); }
  await page.goto(`/admin/flood-history?dataset_id=${dataset}&event_id=920`);
  const history = page.getByRole('dialog', { name: 'Flood Event Details' });
  await expect(history.getByText(designation.label, { exact: true })).toHaveCount(0);
  await expect(history.getByText('ended', { exact: true })).toBeVisible();
});
