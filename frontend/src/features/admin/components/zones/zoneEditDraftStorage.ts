import { del, get, keys, set } from "idb-keyval";
import type { ZoneDataEditorValues } from "../ZoneDataEditorForm";

const VERSION = 1;
const PREFIX = "lanes:admin-edit-zone-draft:v1:";

export interface SavedZoneEditDraft {
  version: typeof VERSION;
  ownerId: string;
  zoneId: number;
  baselineUpdatedAt: string;
  updatedAt: string;
  editorValues: ZoneDataEditorValues;
  passableVehicles: string[];
  hiddenHazards: string;
  adminNotes: string;
  mediaFiles: File[];
}

const keyFor = (ownerId: string, zoneId: number) => `${PREFIX}${ownerId}:${zoneId}`;

export async function loadZoneEditDraft(ownerId: string, zoneId: number): Promise<SavedZoneEditDraft | null> {
  const saved = await get<unknown>(keyFor(ownerId, zoneId));
  if (!saved || typeof saved !== "object") return null;
  const draft = saved as Partial<SavedZoneEditDraft>;
  if (draft.version !== VERSION || draft.ownerId !== ownerId || draft.zoneId !== zoneId || !draft.editorValues) {
    await del(keyFor(ownerId, zoneId));
    return null;
  }
  return draft as SavedZoneEditDraft;
}

export function saveZoneEditDraft(ownerId: string, zoneId: number, draft: Omit<SavedZoneEditDraft, "version" | "ownerId" | "zoneId" | "updatedAt">) {
  return set(keyFor(ownerId, zoneId), {
    version: VERSION,
    ownerId,
    zoneId,
    updatedAt: new Date().toISOString(),
    ...draft,
  } satisfies SavedZoneEditDraft);
}

export function discardZoneEditDraft(ownerId: string, zoneId: number) {
  return del(keyFor(ownerId, zoneId));
}

/** The latest unfinished edit lets Pane 2 resume after a reload or login. */
export async function findLatestZoneEditDraft(ownerId: string): Promise<SavedZoneEditDraft | null> {
  const allKeys = await keys();
  const prefix = `${PREFIX}${ownerId}:`;
  const matches = allKeys.filter((key): key is string => typeof key === "string" && key.startsWith(prefix));
  const drafts = await Promise.all(matches.map((key) => get<SavedZoneEditDraft>(key)));
  return drafts.filter((draft): draft is SavedZoneEditDraft => Boolean(draft)).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))[0] ?? null;
}
