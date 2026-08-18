import { createCustomRoutingEngine } from './valhallaCore';
import { createOpfsTarTileSourceFactory, parseTarIndex, type TileSource } from 'valhalla-wasm';

declare const ValhallaModule: (o?: any) => Promise<any>;

const TILE_DB_NAME = 'lanes-tiles-db';
const TILE_STORE_NAME = 'tiles_archive';

async function getArrayBufferFromIndexedDB(key: string): Promise<ArrayBuffer | null> {
  return new Promise((resolve) => {
    try {
      const req = indexedDB.open(TILE_DB_NAME, 1);
      req.onsuccess = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(TILE_STORE_NAME)) {
          return resolve(null);
        }
        const tx = db.transaction(TILE_STORE_NAME, 'readonly');
        const store = tx.objectStore(TILE_STORE_NAME);
        const getReq = store.get(key);
        getReq.onsuccess = () => resolve(getReq.result || null);
        getReq.onerror = () => resolve(null);
      };
      req.onerror = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

async function hybridTileSourceFactory(region: string): Promise<TileSource | null> {
  const filename = `${region}_routing.tar`;

  // 1. Try OPFS
  if (typeof navigator !== 'undefined' && navigator.storage && typeof navigator.storage.getDirectory === 'function') {
    try {
      const rootDir = await navigator.storage.getDirectory();
      const mapDir = await rootDir.getDirectoryHandle('offline_maps', { create: false });
      const fileHandle = await mapDir.getFileHandle(filename, { create: false });
      // @ts-ignore
      const handle = await fileHandle.createSyncAccessHandle();
      const totalSize = handle.getSize();
      const read = (into: Uint8Array, at: number, _length: number) => handle.read(into, { at });
      const entries = parseTarIndex(read, totalSize);
      console.log(`[valhalla-worker] Loaded OPFS tile source for ${region} with ${entries.length} tiles`);
      return { entries, read };
    } catch (e) {
      console.warn(`[valhalla-worker] OPFS tile source not found for ${region}, checking IndexedDB...`);
    }
  }

  // 2. Try IndexedDB Buffer
  try {
    const buffer = await getArrayBufferFromIndexedDB(filename);
    if (buffer) {
      const uint8 = new Uint8Array(buffer);
      const totalSize = uint8.byteLength;
      const read = (into: Uint8Array, at: number, length: number) => {
        const slice = uint8.subarray(at, at + length);
        into.set(slice);
        return slice.length;
      };
      const entries = parseTarIndex(read, totalSize);
      console.log(`[valhalla-worker] Loaded IndexedDB tile source for ${region} with ${entries.length} tiles`);
      return { entries, read };
    }
  } catch (idbErr) {
    console.error(`[valhalla-worker] Failed to load tile source from IndexedDB:`, idbErr);
  }

  console.error(`[valhalla-worker] No tile archive found in OPFS or IndexedDB for "${region}"`);
  return null;
}

let routerPromise: Promise<(req: any) => Promise<any>> | null = null;

async function initEngine() {
  if (!routerPromise) {
    routerPromise = (async () => {
      console.log("[valhalla-worker] Starting Engine Initialization...");
      const wasmOrigin = (typeof location !== 'undefined' && location.origin) ? location.origin : '';
      
      // Dynamically load valhalla.js if not yet in global scope
      if (typeof ValhallaModule === 'undefined') {
        try {
          const scriptUrl = `${wasmOrigin}/valhalla.js`;
          console.log("[valhalla-worker] Loading Emscripten JS wrapper from:", scriptUrl);
          // @ts-ignore
          self.importScripts(scriptUrl);
        } catch (e) {
          console.error("[valhalla-worker] importScripts failed:", e);
          throw new Error("Could not load /valhalla.js bundle inside worker.");
        }
      }

      console.log("[valhalla-worker] Creating Routing Engine with valhalla.wasm...");
      return createCustomRoutingEngine({
        initModule: () => {
          console.log("[valhalla-worker] Instantiating ValhallaModule...");
          return ValhallaModule({
            locateFile: (p: string) => {
              const fullWasmPath = `${wasmOrigin}/${p}`;
              console.log("[valhalla-worker] Locating WASM resource:", fullWasmPath);
              return fullWasmPath;
            }
          });
        },
        tileSourceFactory: hybridTileSourceFactory,
        onProgress: (m: string) => {
          console.log("[valhalla-worker] Progress update:", m);
          self.postMessage({ type: 'progress', message: m });
        },
      });
    })();
  }
  return routerPromise;
}

self.onmessage = async (e: MessageEvent) => {
  if (e.data?.type === 'init') {
    console.log("[valhalla-worker] Eagerly initializing engine while online...");
    try {
      const route = await initEngine();
      // Force the WASM module to actually download and compile by sending a dummy route.
      // createRoutingEngine is lazy, so we MUST call the closure to trigger initModule().
      await route({ start: [0, 0], end: [0, 0], regions: [] });
    } catch (err) {
      // This will throw "No route found", which is perfectly fine.
      console.log("[valhalla-worker] Eager init complete. Dummy route result:", err);
    }
    return;
  }
  
  try {
    console.log("[valhalla-worker] Received routing request:", e.data);
    const route = await initEngine();
    console.log("[valhalla-worker] Engine ready, dispatching route calculation...");
    const result = await route(e.data);
    console.log("[valhalla-worker] Routing completed successfully:", result);
    self.postMessage({ type: 'success', result });
  } catch (error: any) {
    console.error("[valhalla-worker] Error during routing calculation:", error);
    self.postMessage({ type: 'error', error: error.message || String(error) });
  }
};
