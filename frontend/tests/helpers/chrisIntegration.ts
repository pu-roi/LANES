import { expect, type Page } from '@playwright/test';

const now = new Date().toISOString();
export const fixtureZone = {
  id: 910, name: 'Fixture flood zone', is_active: true, severity: 'medium', depth: 'knee',
  created_at: now, updated_at: now, expires_at: null, contributors: [], news: [],
  location_label: 'Fixture Road, Pasig', report_source: 'official', passable_vehicles: 'Unknown',
  geometry: { type: 'Polygon', coordinates: [[[121.079, 14.569], [121.081, 14.569], [121.081, 14.571], [121.079, 14.571], [121.079, 14.569]]] },
};
const fixtureEvent = {
  id: 920, status: 'active', first_reported_at: now, verified_at: now, ended_at: null,
  peak_severity: 'medium', peak_depth: 'knee', supporting_report_count: 0, reporter_count: 0,
  locations: [{ id: 1, location_type: 'road', display_name: 'Fixture Road', normalized_name: 'fixture road', created_at: now }],
  zones: [fixtureZone], reports: [], timeline: [],
};
const analytics = {
  total_events: 1, active_events: 1, ended_events: 0,
  peak_severity_distribution: [{ severity: 'medium', event_count: 1 }],
  duration: { ended_event_count: 0, average_minutes: null, distribution: [] },
  events_over_time: [], approved_reports_over_time: [], verification_pattern: [],
  recurring_barangays: [], frequently_affected_roads: [],
  supporting_report_volume: { approved_report_count: 0, average_per_event: 0 }, definitions: {},
};
const places = [
  { id: 931, user_id: 7, name: 'Fixture Home', address: 'Fixture Road', latitude: 14.57, longitude: 121.08, icon: '🏠', pin_order: null, created_at: now },
  { id: 932, user_id: 7, name: 'Fixture Work', address: 'Fixture Avenue', latitude: 14.571, longitude: 121.081, icon: '💼', pin_order: null, created_at: now },
];

/** All API requests terminate in fictional fixtures; no backend is required. */
export async function installChrisFixtures(page: Page, role: 'Admin' | 'Commuter' | null = 'Commuter') {
  const errors: string[] = [];
  const requests: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(loggedIn => {
    if (loggedIn) localStorage.setItem('lanes_token', 'fictional-browser-fixture');
    sessionStorage.setItem('lanes_map_viewport', JSON.stringify({ center: [121.08, 14.57], zoom: 16 }));
    class FixtureEventSource extends EventTarget {
      onopen: (() => void) | null = null;
      constructor() { super(); queueMicrotask(() => this.onopen?.()); }
      close() { /* No server connection exists. */ }
    }
    Object.defineProperty(window, 'EventSource', { value: FixtureEventSource });
    Object.defineProperty(navigator, 'geolocation', { value: {
      getCurrentPosition: (_success: PositionCallback, failure: PositionErrorCallback) => failure({ code: 1, message: 'Fixture location denied' } as GeolocationPositionError),
    } });
  }, role !== null);
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (path.includes('/api/v1/')) {
      requests.push(`${route.request().method()} ${path}`);
      let body: unknown = [];
      if (path.endsWith('/auth/test-token')) body = { id: 7, username: 'fixture', email: 'fixture@example.org', created_at: now, is_active: true, is_verified: true,
        role: { name: role === 'Admin' ? 'Super Admin' : role, permissions: { reports: 'full', map: 'full' } },
        profile: { first_name: 'Fixture', last_name: 'Citizen', is_public: true, address: {} } };
      else if (path.endsWith('/users/me/places')) body = places;
      else if (path.endsWith('/notifications')) body = { notifications: [], unread_count: 0, total: 0, has_more: false };
      else if (path.endsWith('/feed')) body = { posts: [], total: 0, has_more: false };
      else if (path.endsWith('/feed/leaderboard')) body = { reporters: [] };
      else if (path.endsWith('/feed/hotspots')) body = { hotspots: [], window_hours: 24, as_of: now };
      else if (path.endsWith('/news/local-updates')) body = { items: [], as_of: now };
      else if (path.endsWith('/reports/active-zones')) body = [fixtureZone];
      else if (path.endsWith('/admin/zones/all')) body = { zones: [fixtureZone], total: 1 };
      else if (path.endsWith('/admin/zones/910')) body = fixtureZone;
      else if (path.endsWith('/admin/flood-events/analytics')) body = analytics;
      else if (path.endsWith('/admin/flood-events/history')) body = [fixtureEvent];
      else if (path.endsWith('/admin/flood-events/920/history-detail')) body = fixtureEvent;
      else if (path.includes('/updates')) body = { updates: [], next_before_id: null, can_review: true };
      else if (path.endsWith('/admin/review/items')) body = { items: [], total: 0, page: 1, page_size: 20, pages: 1,
        counts: { all: 0, user_reports: 0, news_claims: 0 }, read_only: true };
      else if (path.endsWith('/admin/dashboard/stats')) body = { total_reports: 0, pending_reports: 0, active_zones: 1, total_users: 1, top_barangays: [], top_locations: [] };
      else if (path.endsWith('/analytics/heatmap')) body = { type: 'FeatureCollection', features: [] };
      else if (path.endsWith('/reports/route')) body = { recommended_index: 0, engine_used: 'valhalla', fallback_used: false,
        routes: [{ index: 0, label: 'Fixture route', distance: 1000, duration: 120, safety_score: 100, category: 'balanced',
          geometry: { type: 'LineString', coordinates: [[121.08, 14.57], [121.081, 14.571], [121.082, 14.572]] },
          flood_exposure: { zone_count: 0, highest_severity: 'none', message: 'Fixture route', exposure_score: 0 },
          instructions: [{ instruction: 'Continue along Fixture Road', type: 1, begin_shape_index: 0, end_shape_index: 1, distance: 500 },
            { instruction: 'Turn onto Fixture Avenue', type: 2, begin_shape_index: 1, end_shape_index: 2, distance: 500 }] }] };
      return route.fulfill({ json: body });
    }
    if (url.hostname === 'photon.komoot.io') {
      const end = (url.searchParams.get('q') || '').includes('Destination');
      return route.fulfill({ json: { features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: end ? [121.082, 14.572] : [121.08, 14.57] },
        properties: { osm_id: end ? 2 : 1, name: end ? 'Fixture Destination' : 'Fixture Origin', city: 'Pasig' } }] } });
    }
    if (path.endsWith('/style.json') && url.hostname !== '127.0.0.1') return route.fulfill({ json: {
      version: 8, sources: {}, layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#f1f5f9' } }],
    } });
    if (url.hostname.endsWith('tile.openstreetmap.org')) return route.fulfill({ contentType: 'image/png',
      body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64') });
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) return route.abort();
    return route.continue();
  });
  return { errors, requests };
}

export async function expectNoOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
}
