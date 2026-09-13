import { del, get, keys, set } from "idb-keyval";
import type { ZoneDataEditorValues } from "../ZoneDataEditorForm";
import type { AvoidanceZone, ReportGeometry } from "../../adminApi";

const VERSION = 2;
const PREFIX = "lanes:admin-edit-zone-draft:v2:";
const LEGACY_PREFIX = "lanes:admin-edit-zone-draft:v1:";

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
  /** Immutable server-derived values used to prove this is a real edit. */
  baseline: ZoneEditValues;
}

export interface ZoneEditValues {
  editorValues: ZoneDataEditorValues;
  passableVehicles: string[];
  hiddenHazards: string;
  adminNotes: string;
}

const keyFor = (ownerId: string, zoneId: number) => `${PREFIX}${ownerId}:${zoneId}`;

export async function loadZoneEditDraft(ownerId: string, zoneId: number): Promise<SavedZoneEditDraft | null> {
  const saved = await get<unknown>(keyFor(ownerId, zoneId));
  if (!saved || typeof saved !== "object") return null;
  const draft = saved as Partial<SavedZoneEditDraft>;
  if (draft.version !== VERSION || draft.ownerId !== ownerId || draft.zoneId !== zoneId || !draft.editorValues || !draft.baseline) {
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

/**
 * Normalises the editable values before comparing them with the server
 * baseline.  IndexedDB drafts are a convenience only: an unchanged copy of
 * an active zone must never be enough to reopen Edit Zone on a later visit.
 */
function comparable(values: ZoneEditValues) {
  const normaliseText = (value: string | null | undefined) => (value ?? "").trim();
  return JSON.stringify({
    name: normaliseText(values.editorValues.name),
    severity: values.editorValues.severity,
    depth: normaliseText(values.editorValues.depth),
    passableVehicles: [...new Set(values.passableVehicles)].sort(),
    hiddenHazards: normaliseText(values.hiddenHazards),
    adminNotes: normaliseText(values.adminNotes),
    isBidirectional: Boolean(values.editorValues.is_bidirectional),
    geometry: values.editorValues.geometry,
  });
}

export function areZoneEditValuesEqual(left: ZoneEditValues, right: ZoneEditValues): boolean {
  return comparable(left) === comparable(right);
}

export function hasZoneEditChanges(
  values: ZoneEditValues,
  baseline: ZoneEditValues,
  mediaFiles: File[] = [],
): boolean {
  return mediaFiles.length > 0 || !areZoneEditValuesEqual(values, baseline);
}

export function getZoneEditValues(draft: SavedZoneEditDraft): ZoneEditValues {
  return {
    editorValues: draft.editorValues,
    passableVehicles: draft.passableVehicles,
    hiddenHazards: draft.hiddenHazards,
    adminNotes: draft.adminNotes,
  };
}

export function getZoneEditBaseline(zone: AvoidanceZone): ZoneEditValues {
  const passableVehicles = zone.passable_vehicles_override?.split(",").filter(Boolean) ?? [];
  const sourceGeometry = zone.report_geometry?.type === "LineString" || zone.report_geometry?.type === "MultiLineString"
    ? zone.report_geometry
    : zone.geometry;
  return {
    editorValues: {
      name: zone.name || `Official Zone #${zone.id}`,
      severity: (zone.severity_override || "medium") as ZoneDataEditorValues["severity"],
      depth: zone.depth_override || "knee",
      passable_vehicles: passableVehicles,
      hidden_hazards: zone.hidden_hazards_override || "unsure",
      is_bidirectional: sourceGeometry.type === "MultiLineString",
      geometry: sourceGeometry as ReportGeometry,
      admin_notes: zone.admin_notes || "",
    },
    passableVehicles,
    hiddenHazards: zone.hidden_hazards_override || "unsure",
    adminNotes: zone.admin_notes || "",
  };
}

/** The latest unfinished edit lets Pane 2 resume after a reload or login. */
export async function findLatestZoneEditDraft(ownerId: string): Promise<SavedZoneEditDraft | null> {
  const allKeys = await keys();
  const legacyPrefix = `${LEGACY_PREFIX}${ownerId}:`;
  await Promise.all(
    allKeys
      .filter((key): key is string => typeof key === "string" && key.startsWith(legacyPrefix))
      .map((key) => del(key)),
  );
  const prefix = `${PREFIX}${ownerId}:`;
  const matches = allKeys.filter((key): key is string => typeof key === "string" && key.startsWith(prefix));
  const drafts = await Promise.all(matches.map(async (key) => {
    const zoneId = Number(key.slice(prefix.length));
    return Number.isSafeInteger(zoneId) ? loadZoneEditDraft(ownerId, zoneId) : null;
  }));
  return drafts.filter((draft): draft is SavedZoneEditDraft => Boolean(draft)).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))[0] ?? null;
}
