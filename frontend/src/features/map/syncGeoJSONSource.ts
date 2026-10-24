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
      const oldProperties = old.properties ?? {};
      const properties = feature.properties ?? {};
      // Clearing and re-adding properties in one worker diff can drop every
      // property in MapLibre, leaving black roads and invisible overview pins.
      const removeProperties = Object.keys(oldProperties)
        .filter(key => oldProperties[key] !== undefined && properties[key] === undefined);
      const addOrUpdateProperties = Object.entries(properties)
        .filter(([key, value]) => value !== undefined && JSON.stringify(oldProperties[key]) !== JSON.stringify(value))
        .map(([key, value]) => ({ key, value }));
      if (geometryChanged || removeProperties.length || addOrUpdateProperties.length) update.push({
        id: key, ...(geometryChanged ? { newGeometry: feature.geometry } : {}),
        ...(removeProperties.length ? { removeProperties } : {}),
        // Keep the array even for geometry-only diffs: MapLibre can coalesce
        // this update with a subsequent property removal before worker delivery.
        addOrUpdateProperties,
      });
    }
    if (remove.length || add.length || update.length) existing.updateData({ remove, add, update });
  }
  previous.set(existing, next);
}
