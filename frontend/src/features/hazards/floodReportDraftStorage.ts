import { del, get, set } from "idb-keyval";
import type { DraftReport, FloodReportMapState } from "@/features/map/MapContext";

const DRAFT_VERSION = 1;
const DRAFT_KEY_PREFIX = "lanes:flood-report-draft:v1:";
const LEGACY_TEXT_KEY = "lanes_active_flood_form_text";
const LEGACY_FILE_KEY = "lanes_active_flood_form_files";
const LEGACY_MAP_DRAFTS_KEY = "lanes_map_drafts";

export interface FloodReportDraftActiveState extends FloodReportMapState {
  startInput: string;
  endInput: string;
  visualOption: string | null;
  passableVehicles: string[];
  hiddenHazards: "yes" | "no" | "unsure" | null;
  showSurvey: boolean;
  description: string;
  mediaFiles: File[];
  isPublic: boolean;
  step: 1 | 2;
}

export interface SavedFloodReportDraft {
  version: typeof DRAFT_VERSION;
  ownerId: string;
  updatedAt: string;
  active: FloodReportDraftActiveState;
  queuedDrafts: DraftReport[];
}

function keyFor(userId: string) {
  return `${DRAFT_KEY_PREFIX}${userId}`;
}

export async function loadFloodReportDraft(userId: string): Promise<SavedFloodReportDraft | null> {
  const saved = await get<unknown>(keyFor(userId));
  if (!saved || typeof saved !== "object") return null;

  const draft = saved as Partial<SavedFloodReportDraft>;
  if (draft.version !== DRAFT_VERSION || draft.ownerId !== userId || !draft.active || !Array.isArray(draft.queuedDrafts)) {
    await del(keyFor(userId));
    return null;
  }

  return draft as SavedFloodReportDraft;
}

export function saveFloodReportDraft(userId: string, draft: Omit<SavedFloodReportDraft, "version" | "ownerId" | "updatedAt">) {
  return set(keyFor(userId), {
    version: DRAFT_VERSION,
    ownerId: userId,
    updatedAt: new Date().toISOString(),
    ...draft,
  } satisfies SavedFloodReportDraft);
}

export function discardFloodReportDraft(userId: string) {
  return del(keyFor(userId));
}

/** Removes incomplete, device-wide drafts without assigning them to a different account. */
export async function removeLegacyFloodReportDrafts() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(LEGACY_TEXT_KEY);
  }
  await Promise.all([del(LEGACY_FILE_KEY), del(LEGACY_MAP_DRAFTS_KEY)]);
}
