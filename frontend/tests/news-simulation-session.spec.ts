import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import ts from "typescript";

// Run the actual session resolver/client in isolated browser-like contexts.
// HTTP is recorded, never sent to a normal or private database.
function session(environment: string, host: string, port: string, configuration: unknown, status = 200, apiStatus = 200) {
  const requests: { url: string; options?: RequestInit }[] = [];
  const storage = new Map([["lanes_token", "normal-token"], ["lanes_token:news-reconstruction", "reconstruction-token"]]);
  const databaseNames: string[] = [];
  const context = {
    process: { env: { NODE_ENV: environment } },
    window: { location: { hostname: host, port } },
    localStorage: { getItem: (key: string) => storage.get(key), removeItem: (key: string) => storage.delete(key) },
    indexedDB: { open: (name: string) => {
      databaseNames.push(name);
      const request: { result: unknown; onsuccess?: () => void } = { result: { transaction: () => ({ objectStore: () => ({
        get: () => { const item: { result: unknown[]; onsuccess?: () => void } = { result: [] }; queueMicrotask(() => item.onsuccess?.()); return item; },
      }) }) } };
      queueMicrotask(() => request.onsuccess?.());
      return request;
    } },
    FormData,
    fetch: async (url: string, options?: RequestInit) => {
      requests.push({ url, options });
      return { status: url === "/news-simulation.local.json" ? status : apiStatus,
        ok: (url === "/news-simulation.local.json" ? status : apiStatus) < 400,
        json: async () => url === "/news-simulation.local.json" ? configuration : [] };
    },
  };
  function load(file: string, imports = {}) {
    const exports: Record<string, unknown> = {};
    const source = fs.readFileSync(path.resolve("src/lib", file), "utf8");
    const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2017 } }).outputText;
    vm.runInNewContext(code, { ...context, exports, require: () => imports });
    return exports;
  }
  const modes = load("localNewsSimulation.ts");
  return { requests, storage, databaseNames,
    mode: modes as typeof import("../src/lib/localNewsSimulation"),
    offline: load("offline/storage.ts", modes) as typeof import("../src/lib/offline/storage"),
    client: load("apiClient.ts", modes) as typeof import("../src/lib/apiClient"),
    streams: load("sse.ts", modes) as typeof import("../src/lib/sse") };
}

for (const port of ["3000", "3001"]) test(`persisted simulation on ${port} uses one backend for public zones, Admin, auth, actions and SSE`, async () => {
  const { client, streams, requests } = session("development", "127.0.0.1", port, { mode: "persisted", port });
  expect(await client.getApiBaseUrl()).toBe("/simulation/api/v1");
  for (const endpoint of ["/reports/active-zones", "/admin/zones", "/admin/review", "/admin/news/results"]) {
    await client.apiClient.get(endpoint);
    expect(requests.at(-1)?.url).toBe(`/simulation/api/v1${endpoint}`);
  }
  await client.apiClient.post("/auth/test-token");
  expect(requests.at(-1)?.url).toBe("/simulation/api/v1/auth/test-token");
  await client.apiClient.post("/admin/zones/9/deactivate");
  expect(requests.at(-1)?.url).toBe("/simulation/api/v1/admin/zones/9/deactivate");
  expect(requests.at(-1)?.options?.headers).toEqual({ Authorization: "Bearer reconstruction-token" });
  for (const endpoint of ["/sync/stream", "/sse/stream"]) {
    expect(await streams.getSessionSseUrl(endpoint)).toBe(`http://127.0.0.1:8001/api/v1${endpoint}`);
  }
  expect(requests.filter(request => request.url === "/news-simulation.local.json")).toHaveLength(1);
});

for (const scenario of [
  { environment: "development", host: "localhost", port: "3000", status: 200 },
  { environment: "production", host: "localhost", port: "3001", status: 200 },
  { environment: "development", host: "lanes.example", port: "3001", status: 200 },
  { environment: "development", host: "localhost", port: "3001", status: 404 },
]) {
  test(`normal session stays connected: ${JSON.stringify(scenario)}`, async () => {
    const { client, requests } = session(scenario.environment, scenario.host, scenario.port,
      { mode: "persisted", port: "3001" }, scenario.status);
    await client.apiClient.get("/reports/active-zones");
    expect(requests.at(-1)?.url).toBe("/api/v1/reports/active-zones");
  });
}

test("legacy preview stays additive and does not redirect Admin or auth", async () => {
  const { client, requests, streams } = session("development", "localhost", "3000", { mode: "september24" });
  await client.apiClient.get("/news/simulation");
  expect(requests.at(-1)?.url).toBe("/simulation/api/v1/news/simulation");
  await client.apiClient.get("/reports/active-zones");
  expect(requests.at(-1)?.url).toBe("/api/v1/reports/active-zones");
  expect(await client.getApiBaseUrl()).toBe("/api/v1");
  expect(await streams.getSessionSseUrl("/sync/stream")).toBe("http://127.0.0.1:8000/api/v1/sync/stream");
});

test("invalid persisted configuration surfaces an error before API requests", async () => {
  const { client, requests } = session("development", "localhost", "3000", { mode: "persisted", port: "9999" });
  const message = await client.apiClient.get("/reports/active-zones").then(
    () => "unexpected success", (error: Error) => error.message);
  expect(message).toContain("local port 3000 or 3001");
  expect(requests).toHaveLength(1);
});

test("reconstruction rejection clears only its token and keeps its own offline flood cache", async () => {
  const { client, storage, offline, databaseNames } = session("development", "localhost", "3000",
    { mode: "persisted", port: "3000" }, 200, 401);
  const error = await client.apiClient.post("/auth/test-token").then(() => "unexpected success", (error: Error) => error.message);
  expect(error).toContain("401");
  expect(storage.get("lanes_token")).toBe("normal-token");
  expect(storage.has("lanes_token:news-reconstruction")).toBe(false);
  await offline.getFloodsOffline();
  expect(databaseNames).toEqual(["lanes-offline-db:news-reconstruction"]);
});

test("current data mode restores normal token and offline flood cache", async () => {
  const { client, requests, mode, offline, databaseNames, storage } = session("development", "localhost", "3000", null, 404);
  await client.apiClient.post("/auth/test-token");
  expect(requests.at(-1)?.url).toBe("/api/v1/auth/test-token");
  expect(requests.at(-1)?.options?.headers).toEqual({ Authorization: "Bearer normal-token" });
  expect(await mode.getSessionStorageKey("lanes_token")).toBe("lanes_token");
  expect(storage.get("lanes_token:news-reconstruction")).toBe("reconstruction-token");
  await offline.getFloodsOffline();
  expect(databaseNames).toEqual(["lanes-offline-db"]);
});

for (const environment of ["production", "development"]) test(`port 3000 reconstruction is ignored outside local development: ${environment}`, async () => {
  const { client, mode, requests } = session(environment, environment === "production" ? "localhost" : "lanes.example", "3000",
    { mode: "persisted", port: "3000" });
  await client.apiClient.get("/reports/active-zones");
  expect(requests.at(-1)?.url).toBe("/api/v1/reports/active-zones");
  expect(await mode.getSessionStorageKey("lanes_token")).toBe("lanes_token");
  expect(requests).toHaveLength(1);
});
