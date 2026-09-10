import { del, get, set } from "idb-keyval";
import type { FloodReportMapState } from "@/features/map/MapContext";
import type { ZoneDataEditorValues } from "../ZoneDataEditorForm";
import type { GeometryMode, ZoneDraftItem } from "./types";

const DRAFT_VERSION = 1;
const DRAFT_KEY_PREFIX = "lanes:admin-create-zone-draft:v1:";
const LEGACY_KEY = "lanes_admin_zone_drafts";

export interface SavedCreateZoneDraft {
  version: typeof DRAFT_VERSION;
  ownerId: string;
  updatedAt: string;
  active: FloodReportMapState & {
    geometryMode: GeometryMode;
    drawnFeatures: any[];
    editorValues: ZoneDataEditorValues;
    passableVehicles: string[];
    hiddenHazards: string;
    adminNotes: string;
    mediaFiles: File[];
  };
  queuedDrafts: ZoneDraftItem[];
}

function keyFor(userId: string) {
  return `${DRAFT_KEY_PREFIX}${userId}`;
}

export async function loadCreateZoneDraft(userId: string): Promise<SavedCreateZoneDraft | null> {
  const saved = await get<unknown>(keyFor(userId));
  if (!saved || typeof saved !== "object") return null;
  const draft = saved as Partial<SavedCreateZoneDraft>;
  if (draft.version !== DRAFT_VERSION || draft.ownerId !== userId || !draft.active || !Array.isArray(draft.queuedDrafts)) {
    await del(keyFor(userId));
    return null;
  }
  return draft as SavedCreateZoneDraft;
}

export function saveCreateZoneDraft(userId: string, draft: Omit<SavedCreateZoneDraft, "version" | "ownerId" | "updatedAt">) {
  return set(keyFor(userId), {
    version: DRAFT_VERSION,
    ownerId: userId,
    updatedAt: new Date().toISOString(),
    ...draft,
  } satisfies SavedCreateZoneDraft);
}

export function discardCreateZoneDraft(userId: string) {
  return del(keyFor(userId));
}

export async function removeLegacyCreateZoneDraft() {
  if (typeof window !== "undefined") localStorage.removeItem(LEGACY_KEY);
}

export async function hasCreateZoneDraft(userId: string) {
  return (await loadCreateZoneDraft(userId)) !== null;
}
