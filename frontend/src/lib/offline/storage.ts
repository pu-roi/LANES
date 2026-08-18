/**
 * Handles downloading and storing massive offline data (Valhalla tiles) in the OPFS.
 */

// IndexedDB fallback for tile archives when OPFS (navigator.storage.getDirectory) is not available
const TILE_DB_NAME = 'lanes-tiles-db';
const TILE_STORE_NAME = 'tiles_archive';

async function getTileDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(TILE_DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(TILE_STORE_NAME)) {
        db.createObjectStore(TILE_STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function downloadRoutingTiles(
  url: string,
  filename: string = 'philippines_routing.tar',
  onProgress?: (pct: number, loaded?: number, total?: number) => void
): Promise<boolean> {
  try {
    const response = await fetch(url);
    if (!response.body) throw new Error("No response body");

    const contentLength = response.headers.get('content-length');
    const total = contentLength ? parseInt(contentLength, 10) : 0;
    let loaded = 0;

    // Check if OPFS is supported in current context
    const hasOpfs = typeof navigator !== 'undefined' && navigator.storage && typeof navigator.storage.getDirectory === 'function';

    if (hasOpfs) {
      try {
        const root = await navigator.storage.getDirectory();
        const directory = await root.getDirectoryHandle('offline_maps', { create: true });
        const fileHandle = await directory.getFileHandle(filename, { create: true });
        
        // @ts-ignore
        const writable = await fileHandle.createWritable();
        const reader = response.body.getReader();
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          await writable.write(value);
          loaded += value.length;
          if (total && onProgress) {
            onProgress(Math.round((loaded / total) * 100), loaded, total);
          }
        }
        await writable.close();
        return true;
      } catch (opfsErr) {
        console.warn("OPFS write failed, falling back to IndexedDB:", opfsErr);
      }
    }

    // Fallback: Read into array buffer and store in IndexedDB
    const reader = response.body.getReader();
    const chunks: Uint8Array[] = [];
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) {
        chunks.push(value);
        loaded += value.length;
        if (total && onProgress) {
          onProgress(Math.round((loaded / total) * 100), loaded, total);
        }
      }
    }

    // Combine chunks
    const totalLen = chunks.reduce((acc, c) => acc + c.length, 0);
    const fullBuffer = new Uint8Array(totalLen);
    let offset = 0;
    for (const chunk of chunks) {
      fullBuffer.set(chunk, offset);
      offset += chunk.length;
    }

    const db = await getTileDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(TILE_STORE_NAME, 'readwrite');
      const store = tx.objectStore(TILE_STORE_NAME);
      const req = store.put(fullBuffer.buffer, filename);
      req.onsuccess = () => resolve(true);
      req.onerror = () => reject(req.error);
    });
  } catch (error) {
    console.error("Failed to store routing tiles:", error);
    return false;
  }
}

export async function isRoutingDataAvailable(filename: string = 'philippines_routing.tar'): Promise<boolean> {
  // Check OPFS
  if (typeof navigator !== 'undefined' && navigator.storage && typeof navigator.storage.getDirectory === 'function') {
    try {
      const root = await navigator.storage.getDirectory();
      const directory = await root.getDirectoryHandle('offline_maps', { create: false });
      await directory.getFileHandle(filename, { create: false });
      return true;
    } catch {
      // Not in OPFS, check IndexedDB next
    }
  }

  // Check IndexedDB
  try {
    const db = await getTileDB();
    return new Promise((resolve) => {
      const tx = db.transaction(TILE_STORE_NAME, 'readonly');
      const store = tx.objectStore(TILE_STORE_NAME);
      const req = store.get(filename);
      req.onsuccess = () => resolve(!!req.result);
      req.onerror = () => resolve(false);
    });
  } catch {
    return false;
  }
}

// -- IndexedDB cache for dynamic data (Flood Polygons) --

const DB_NAME = 'lanes-offline-db';
const STORE_NAME = 'floods';

async function getDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveFloodsOffline(floods: any[]): Promise<void> {
  try {
    const db = await getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      // We store the whole array under a single key for simplicity
      const request = store.put(floods, 'latest_floods');
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error("Failed to save floods to IndexedDB:", error);
  }
}

export async function getFloodsOffline(): Promise<any[]> {
  try {
    const db = await getDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get('latest_floods');
      request.onsuccess = () => {
        resolve(request.result || []);
      };
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error("Failed to read floods from IndexedDB:", error);
    return [];
  }
}
