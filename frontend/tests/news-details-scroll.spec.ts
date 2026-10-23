import { expect, test, type Locator, type Page } from '@playwright/test';
import { installChrisFixtures, expectNoOverflow } from './helpers/chrisIntegration';

test.use({ browserName: 'chromium' });

const savedAt = '2026-10-22T02:00:00Z';
const mentions = Array.from({ length: 25 }, (_, i) => ({ id: `m${i}`, text: `Fixture Road ${i}`, label: 'ROAD', start: i * 20, end: i * 20 + 15 }));
const result = { processing_method: 'ner_rules_v1', article_id: 11, claims: [], extracted_at: savedAt, extractor_version: 'fixture', is_metadata_only: false, errors: [],
  native: { neural_mentions: mentions, effective_mentions: mentions, proposals: [], abstentions: [], graph: { mentions, facts: [] } },
  projection: { groups: [], fact_accounting: [] } };
const item = { key: '21:group:g0', result_kind: 'ner_group', processing_method: 'ner_rules_v1', run_id: 21, article_id: 11, claim_index: null, group_id: 'g0', publisher: 'Fixture publisher', saved_at: savedAt, published_at: savedAt,
  summary: { location: 'Fixture Road', area: 'Pasig', water_level: 'Unknown', condition: 'Flooding reported', flood_time: null, flood_time_label: 'Source observation', map_status: 'Unresolved' } };
const captured = { title: 'Long fixture article', publisher: item.publisher, canonical_url: 'https://example.org/fixture', published_at: savedAt, excerpt: '',
  article_text: `${'Fixture article paragraph about flooding.\n\n'.repeat(60)}End of saved article.` };

async function scrollDown(page: Page, target: Locator, touch: boolean) {
  const bounds = await target.boundingBox();
  if (!bounds) throw new Error('Missing scroll target');
  const x = bounds.x + bounds.width / 2;
  const top = Math.max(0, bounds.y);
  const bottom = Math.min(bounds.y + bounds.height, page.viewportSize()!.height - 60);
  const y = (top + bottom) / 2;
  if (touch) {
    const session = await page.context().newCDPSession(page);
    const distance = Math.min(400, (bottom - top) * 0.7);
    await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: y + distance / 2 }] });
    for (let step = 1; step <= 8; step++) await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y + distance / 2 - step * distance / 8 }] });
    await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await session.detach();
  } else {
    await page.mouse.move(x, y);
    await page.mouse.wheel(0, 900);
  }
}

test('long News Flood Details evidence and source panes scroll without moving the background', async ({ page }, info) => {
  test.setTimeout(120_000);
  const { errors } = await installChrisFixtures(page, 'Admin');
  const newsRequests: string[] = [];
  await page.route('**/news-simulation.local.json', route => route.fulfill({ status: 404, body: '' }));
  const mobile = info.project.name === 'mobile-chromium';
  if (mobile) await page.setViewportSize({ width: 320, height: 740 });
  await page.route('**/api/v1/admin/news/**', route => {
    newsRequests.push(route.request().method());
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/results/21/groups/g0')) return route.fulfill({ json: { item, result, historical_outputs: [], claim: { evidence_sentence: captured.article_text }, captured_input: captured, extraction_errors: [], is_metadata_only: false } });
    if (path.endsWith('/results')) return route.fulfill({ json: { items: [item], total: 1, page: 1, page_size: 12, pages: 1, publishers: [], scope: 'latest_reported_locations', read_only: true } });
    if (path.endsWith('/articles/11')) return route.fulfill({ json: { article: { ...captured, id: 11, first_seen_at: savedAt, feed_entries: [] }, publisher: item.publisher, versions: [], flood_summaries: {}, history_total: 25,
      runs: Array.from({ length: 25 }, (_, i) => ({ id: 21 + i, article_version_id: 1, status: 'completed', created_at: savedAt, completed_at: savedAt, attempt_count: 1, mode: 'ner_rules_v1', result })) } });
    return route.fulfill({ json: { state: 'not_recorded', status_label: 'No worker cycle recorded', queue_counts: {}, stages: {}, feed_counts: {} } });
  });
  await page.goto('/admin/news');
  await page.getByRole('tab', { name: 'Flooded Areas' }).click();
  await page.getByRole('button', { name: /^Info: Fixture Road/ }).click();
  const dialog = page.getByRole('dialog', { name: 'News Flood Details', exact: true });
  const evidence = dialog.getByRole('region', { name: 'News evidence', exact: true });
  await expect(evidence.getByRole('heading', { name: 'Fixture Road', exact: true })).toBeVisible();
  await expect(evidence.getByRole('heading', { name: /Original NER locations/ })).toHaveCount(0);
  // A real wheel/touch gesture over a long selected observation must reach its footer.
  const tail = evidence.getByText('Times shown in Philippine time.', { exact: false });
  await expect(async () => {
    await scrollDown(page, evidence, mobile);
    await expect(tail).toBeInViewport({ timeout: 250 });
  }).toPass({ timeout: 12_000, intervals: [100, 200, 300] });
  await expect(dialog.getByRole('button', { name: 'Close flood details' })).toBeInViewport();
  await page.screenshot({ path: info.outputPath('flood-details-bottom.png') });

  await dialog.getByRole('button', { name: 'Source Article', exact: true }).click();
  await expect(async () => {
    await scrollDown(page, evidence, mobile);
    await expect(evidence.getByText('Collection details', { exact: true })).toBeInViewport({ timeout: 250 });
  }).toPass({ timeout: 45_000, intervals: [100, 200, 300] });
  await page.screenshot({ path: info.outputPath('source-article-bottom.png') });
  if (mobile) await dialog.getByRole('button', { name: 'Processing history', exact: true }).click();
  const history = dialog.getByRole('region', { name: 'Article processing records', exact: true });
  await expect(async () => {
    await scrollDown(page, history, mobile);
    await expect(history.getByRole('button', { name: 'View extraction #45', exact: true })).toBeInViewport({ timeout: 250 });
  }).toPass({ timeout: 30_000, intervals: [100, 200, 300] });
  await expectNoOverflow(page);
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
  expect(errors).toEqual([]);
  expect(newsRequests.length).toBeGreaterThan(0);
  expect(newsRequests.every(method => method === 'GET')).toBeTruthy();
  await dialog.getByRole('button', { name: 'Close flood details' }).click();
  await expect(dialog).toHaveCount(0);
});
