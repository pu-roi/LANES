import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";

type FeatureId = string | number;
const previous = new WeakMap<GeoJSONSource, Map<FeatureId, GeoJSON.Feature>>();

/** Keep bounded viewport chunks from resending every previously loaded shape. */
export function syncGeoJSONSource(map: MapLibreMap, id: string, data: GeoJSON.FeatureCollection) {
  const existing = map.getSource(id) as GeoJSONSource | undefined;
  const next = new Map<FeatureId, GeoJSON.Feature>();
  for (const feature of data.features) {
    if (feature.id === undefined || next.has(feature.id)) {
      // Other callers can still supply ordinary GeoJSON without stable IDs.
      if (existing) { existing.setData(data); previous.delete(existing); }
      else map.addSource(id, { type: "geojson", data });
      return;
    }
    next.set(feature.id, feature);
  }
  if (!existing) {
    map.addSource(id, { type: "geojson", data });
    previous.set(map.getSource(id) as GeoJSONSource, next);
    return;
  }
  const before = previous.get(existing);
  if (!before) existing.setData(data);
  else {
    const order = [...next.keys()];
    if ([...before.keys()].some((key, index) => order[index] !== key)) {
      // Selected operational features are deliberately sorted on top. Reorder
      // or replace a viewport in one operation rather than changing draw order.
      existing.setData(data);
      previous.set(existing, next);
      return;
    }
    const remove = [...before.keys()].filter(key => !next.has(key));
    const add: GeoJSON.Feature[] = [];
    const update = [];
    for (const [key, feature] of next) {
      const old = before.get(key);
      if (!old) { add.push(feature); continue; }
      const geometryChanged = old.geometry !== feature.geometry && JSON.stringify(old.geometry) !== JSON.stringify(feature.geometry);
      if (geometryChanged || JSON.stringify(old.properties) !== JSON.stringify(feature.properties)) update.push({
        id: key, ...(geometryChanged ? { newGeometry: feature.geometry } : {}), removeAllProperties: true,
        addOrUpdateProperties: Object.entries(feature.properties ?? {}).map(([key, value]) => ({ key, value })),
      });
    }
    if (remove.length || add.length || update.length) existing.updateData({ remove, add, update });
  }
  previous.set(existing, next);
}
