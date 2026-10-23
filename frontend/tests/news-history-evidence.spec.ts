import { expect, test } from '@playwright/test';
import { installChrisFixtures, floodHistoryResponse, floodMapResponse, expectNoOverflow } from './helpers/chrisIntegration';

test.setTimeout(120_000);
const date = '2026-10-22T02:00:00Z';
const original = { title: 'Original morning flood article', publisher: 'Fictional publisher', canonical_url: 'https://example.org/original',
  published_at: '2026-09-09T01:19:06Z', article_text: 'Original morning source: Fictional Road was flooded 26 inches deep.', excerpt: '' };
const source = { article_id: 47, article_version_id: 137, run_id: 137, claim_index: 0, group_id: null,
  title: original.title, publisher: original.publisher, source_url: original.canonical_url, published_at: original.published_at,
  excerpt: original.article_text, observed_at: '2026-09-09T00:55:00Z', occurrence_date: '2026-09-09', precision: 'instant',
  road: 'Fictional Road', city: 'Quezon City', barangay: null, depth_raw: '26 inches', depth_normalized: 'tires',
  condition: 'active', passability: 'unknown', extraction_mode: 'rules_only', extraction_status: 'completed', completed_at: date,
  geometry_basis: 'estimated_road_corridor', geometry_provenance: null, closure_basis: 'administrative' };

test('View Event retains article evidence, source dates and separate citizen reports with Retry', async ({ page }, info) => {
  await installChrisFixtures(page, 'Admin');
  if (info.project.name === 'mobile-chromium') await page.setViewportSize({ width: 320, height: 740 });
  const record = { id: 61, origin: 'news', status: 'ended', first_reported_at: source.observed_at, verified_at: date, ended_at: date,
    peak_severity: 'high', peak_depth: 'tires', duration_basis: 'administrative', closure_basis: 'administrative',
    occurrence_date: '2026-09-09', observed_at: source.observed_at, observation_precision: 'instant',
    news_article_count: 1, news_evidence_count: 1, duration_minutes: null, supporting_report_count: 0, reporter_count: 0,
    locations: [], zones: [], reports: [], timeline: [], heatmap_features: [] };
  let unavailable = true;
  const methods: string[] = [];
  await page.route('**/api/v1/admin/flood-events/**', async route => {
    methods.push(route.request().method()); const url = new URL(route.request().url());
    if (url.pathname.endsWith('/records')) return route.fulfill({ json: floodHistoryResponse([record], url.href) });
    if (url.pathname.endsWith('/map')) return route.fulfill({ json: floodMapResponse([record], url.href) });
    if (url.pathname.endsWith('/inspection')) return route.fulfill({ json: record });
    if (url.pathname.endsWith('/news_sources')) return unavailable
      ? route.fulfill({ status: 503, json: { detail: 'Temporary saved evidence failure' } })
      : route.fulfill({ json: { items: [source], total: 1, page: 1, pages: 1, page_size: 20 } });
    if (url.pathname.includes('/inspection/')) return route.fulfill({ json: { items: [], total: 0, page: 1, pages: 1, page_size: 20 } });
    return route.fallback();
  });
  await page.route('**/api/v1/admin/news/articles/47', route => route.fulfill({ json: {
    publisher: original.publisher, article: { ...original, id: 47, title: 'Later corrected title', article_text: 'Later correction must not replace morning evidence', first_seen_at: date, feed_entries: [] },
    versions: [{ id: 137, input_snapshot: original, created_at: date, input_fingerprint: 'original' }],
    runs: [{ id: 137, article_version_id: 137, status: 'completed', created_at: date, completed_at: date, attempt_count: 1, mode: 'rules_only', result: { claims: [], errors: [] } }], flood_summaries: { 137: [] },
  } }));
  await page.goto('/admin/flood-history?event_id=61');
  const modal = page.getByRole('dialog', { name: 'Flood Event Details', exact: true });
  await expect(modal.getByText('Source observation', { exact: true })).toBeVisible();
  await expect(modal.getByText('Not established by source', { exact: true })).toBeVisible();
  await expect(modal.getByText('Record ended', { exact: true })).toBeVisible();
  await expect(modal.getByRole('alert').filter({ hasText: 'Could not load news sources' })).toBeVisible();
  unavailable = false;
  await modal.getByRole('button', { name: 'Retry news sources', exact: true }).click();
  await expect(modal.getByText('26 inches', { exact: true })).toBeVisible();
  await expect(modal.getByRole('heading', { name: original.title })).toBeVisible();
  await expectNoOverflow(page);
  await page.screenshot({ path: info.outputPath('news-event-details.png'), fullPage: true });
  await modal.getByRole('button', { name: 'View captured article and extraction' }).click();
  const article = page.getByRole('dialog', { name: 'News Article', exact: true });
  await article.getByRole('button', { name: 'Article', exact: true }).click();
  await article.getByText('Full article text', { exact: true }).click();
  await expect(article.getByText(original.article_text, { exact: true })).toBeVisible();
  await expect(article.getByText('Later correction must not replace morning evidence')).toHaveCount(0);
  await article.getByRole('button', { name: 'Close article details' }).click();
  await modal.getByRole('button', { name: 'Reports (0)', exact: true }).click();
  await expect(modal.getByText('No citizen reports are linked to this event.', { exact: false })).toBeVisible();
  await modal.getByRole('button', { name: 'Overview', exact: true }).click();
  await modal.getByRole('button', { name: 'View captured article and extraction' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog', { name: 'News Article', exact: true })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog', { name: 'News Article', exact: true })).toHaveCount(0);
  await expect(modal).toBeVisible();
  await expect(page.getByRole('button', { name: 'Historical dataset' })).toHaveCount(0);
  expect(methods.every(method => method === 'GET')).toBeTruthy();
});
