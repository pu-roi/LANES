import { expect, test } from '@playwright/test';
import { installChrisFixtures, expectNoOverflow } from './helpers/chrisIntegration';

const date = '2026-10-23T02:00:00Z';
const original = { title: 'Flood report', publisher: 'fictional', canonical_url: 'https://example.org/report', published_at: date, excerpt: '',
  article_text: 'Quezon City (as of 8:55 a.m.)\n▶️ Waist-deep (37 inches)\nDon Jose Street\nPalali Street' };
const current = { ...original, article_text: 'Updated 3:09 p.m.\nMalabon City\nSample Avenue - Gutter deep, passable to all vehicles as of 2:47 p.m.' };
const item = { key: '380:group:resolved-n13', result_kind: 'ner_group', processing_method: 'ner_rules_v1', run_id: 380, article_id: 47,
  article_version_id: 574, claim_index: null, group_id: 'resolved-n13', publisher: 'Fictional publisher', saved_at: date, captured_at: date, published_at: date,
  summary: { location: 'Don Jose Street', area: 'Sienna, Quezon City', location_qualifier: 'Measurements retain their reported scope; see the source evidence.',
    water_level: 'Waist-deep (37 inches), shared', condition: 'Flooding reported', passability: 'Not stated in article', flood_time: '2026-09-09T00:55:00Z',
    flood_time_label: 'Flood observed in article', map_status: 'Map location not checked' } };
const result = { processing_method: 'ner_rules_v1', article_id: 47, claims: [], errors: [], native: {
  neural_mentions: [{ id: 'n13', text: 'Don Jose Street', label: 'ROAD', start: 50, end: 65 }],
  effective_mentions: [], proposals: [], abstentions: [], graph: { mentions: [], facts: [] } }, projection: { groups: [], fact_accounting: [] } };

test('selected flood summary and current article stay separate from immutable processing evidence', async ({ page }, info) => {
  test.setTimeout(120_000);
  const { errors } = await installChrisFixtures(page, 'Admin');
  const mobile = info.project.name === 'mobile-chromium';
  if (mobile) await page.setViewportSize({ width: 320, height: 740 });
  const methods: string[] = [];
  await page.route('**/news-simulation.local.json', route => route.fulfill({ status: 404, body: '' }));
  await page.route('**/api/v1/admin/news/**', route => {
    methods.push(route.request().method());
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/results/380/groups/resolved-n13')) return route.fulfill({ json: { item, result,
      claim: { canonical_road: 'Don Jose Street', canonical_barangay: 'Sienna', evidence_sentence: original.article_text }, captured_input: original,
      supporting_passages: ['Quezon City (as of 8:55 a.m.)', '▶️ Waist-deep (37 inches)', 'Don Jose Street'], depth_scope: 'shared',
      source_review: { state: 'different_capture', current_input: current, current_fetched_at: date, selected_captured_at: date } } });
    if (path.endsWith('/results')) return route.fulfill({ json: { items: [item], total: 1, page: 1, pages: 1, page_size: 12, publishers: [], scope: 'latest_reported_locations' } });
    if (path.endsWith('/articles/47')) return route.fulfill({ json: { article: { ...current, id: 47, first_seen_at: date, fetched_at: date, feed_entries: [] }, publisher: item.publisher,
      versions: [{ id: 574, input_snapshot: original, created_at: date, input_fingerprint: 'fixture' }], flood_summaries: {}, history_total: 1,
      runs: [{ id: 380, article_version_id: 574, status: 'completed', created_at: date, completed_at: date, attempt_count: 1, mode: 'ner_rules_v1', result }] } });
    return route.fulfill({ json: { state: 'not_recorded', queue_counts: {}, stages: {}, feed_counts: {} } });
  });
  await page.goto('/admin/news');
  await page.getByRole('tab', { name: 'Flooded Areas' }).click();
  await page.getByRole('button', { name: /^Info: Don Jose Street/ }).click();
  const dialog = page.getByRole('dialog', { name: 'News Flood Details', exact: true });
  await expect(dialog.getByRole('heading', { name: 'Don Jose Street', exact: true })).toBeVisible();
  await expect(dialog.getByText('Waist-deep (37 inches), shared', { exact: true })).toBeVisible();
  await expect(dialog.getByText(/8:55 AM/)).toBeVisible();
  await expect(dialog.getByRole('alert')).toContainText('different saved article version');
  await expect(dialog.getByText(/Original NER locations/)).toHaveCount(0);
  await expect(dialog.getByText(/characters 50/)).toHaveCount(0);
  await expect(dialog.getByText('Palali Street', { exact: false })).toHaveCount(0);
  await expect(dialog.getByText(/without a separate measurement for this road/)).toBeVisible();
  await expect(dialog.getByText('▶️', { exact: false })).toHaveCount(0);
  await dialog.getByRole('button', { name: 'Source Article', exact: true }).click();
  await expect(dialog.getByText(current.article_text, { exact: true })).toBeVisible();
  await expect(dialog.getByText(original.article_text, { exact: true })).toHaveCount(0);
  await expect(dialog.getByRole('alert')).toContainText('current saved publisher article');
  await page.screenshot({ path: info.outputPath('current-source.png') });
  if (mobile) await dialog.getByRole('button', { name: 'Processing history', exact: true }).click();
  await dialog.getByRole('button', { name: 'View extraction #380', exact: true }).click();
  await expect(dialog.getByRole('heading', { name: 'Original NER locations (1)', exact: true })).toBeVisible();
  await dialog.getByRole('button', { name: 'Article', exact: true }).click();
  await expect(dialog.getByText(original.article_text.replace('▶️ ', ''), { exact: true })).toBeVisible();
  await expect(dialog.getByText(current.article_text, { exact: true })).toBeHidden();
  await expect(dialog.getByText('Captured extraction input', { exact: true })).toBeVisible();
  await expectNoOverflow(page);
  await page.screenshot({ path: info.outputPath('saved-processing-input.png') });
  expect(errors).toEqual([]);
  expect(methods.every(method => method === 'GET')).toBeTruthy();
});
