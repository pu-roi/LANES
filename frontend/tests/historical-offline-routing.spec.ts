import { expect, test } from '@playwright/test';
import { rejects } from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';

function routingFixture(cached: unknown[], failStorage = false) {
  const messages: { exclude_polygons?: number[][][]; vehicle_profile: string }[] = [];
  const cloud: unknown[] = [];
  const navigator = { onLine: false };
  class FixtureWorker {
    listeners = new Map<string, (event: { data: unknown }) => void>();
    addEventListener(type: string, callback: (event: { data: unknown }) => void) { this.listeners.set(type, callback); }
    removeEventListener(type: string) { this.listeners.delete(type); }
    postMessage(payload: typeof messages[number]) {
      messages.push(payload);
      queueMicrotask(() => this.listeners.get('message')?.({ data: { type: 'success', result: {
        success: true, geometry: { type: 'LineString', coordinates: [[121, 14.5], [121.1, 14.6]] },
      } } }));
    }
  }
  const exportHolder = { exports: {} as { getRoute: (...args: unknown[]) => Promise<{ offline_limited: boolean }> } };
  const code = ts.transpileModule(readFileSync(resolve('src/features/routing/routingApi.ts'), 'utf8'), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
  }).outputText.replaceAll('import.meta.url', JSON.stringify('file:///fixture/routingApi.js'));
  runInNewContext(code, { module: exportHolder, exports: exportHolder.exports, window: {}, navigator, Worker: FixtureWorker,
    URL, setTimeout, clearTimeout, queueMicrotask, console: { log() {}, warn() {}, error() {} },
    require: (name: string) => {
      if (name === '@/lib/offline/storage') return { getFloodsOffline: async () => {
        if (failStorage) throw new Error('Fixture cache unavailable');
        return cached;
      } };
      if (name === '@/lib/apiClient') return { apiClient: { post: async (...args: unknown[]) => {
        cloud.push(args); return { offline_limited: false };
      } } };
      throw new Error(`Unexpected dependency ${name}`);
    },
  });
  return { route: exportHolder.exports.getRoute, messages, cloud, navigator };
}

test('offline worker excludes ordinary blocked geometry and honors saved demo eligibility', async () => {
  const ordinary = [[121, 14.5], [121.001, 14.5], [121, 14.5]];
  const demo = [[122, 15], [122.001, 15], [122, 15]];
  const fixture = routingFixture([
    { polygon: { type: 'Polygon', coordinates: [ordinary] }, routing_restrictions: { light: 'blocked', motorcycle: 'passable' } },
    { affects_routing: false, polygon: { type: 'Polygon', coordinates: [demo] }, routing_restrictions: { light: 'blocked', motorcycle: 'blocked' } },
  ]);
  await fixture.route([121, 14.5], [121.1, 14.6]);
  expect(fixture.messages[0].exclude_polygons).toEqual([ordinary]);
  await fixture.route([121, 14.5], [121.1, 14.6], false, 'motorcycle');
  expect(fixture.messages[1].exclude_polygons).toBeUndefined();
  fixture.navigator.onLine = true;
  await fixture.route([121, 14.5], [121.1, 14.6]);
  expect(fixture.cloud).toHaveLength(1);
});

test('offline cache failure is surfaced before requesting a WASM route', async () => {
  const fixture = routingFixture([], true);
  await rejects(async () => { await fixture.route([121, 14.5], [121.1, 14.6]); },
    /Offline routing cannot verify flood restrictions/);
  expect(fixture.messages).toEqual([]);
});
