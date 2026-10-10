import type { Map, PositionAnchor } from "maplibre-gl";

/** Keep flood details clear of the navigation and near-edge map controls. */
export function floodPopupAnchor(map: Map, lngLat: { lng: number; lat: number }, popupHeight: number): PositionAnchor {
  const { x, y } = map.project(lngLat);
  const width = map.getCanvas().clientWidth;
  const height = map.getCanvas().clientHeight;
  const below = height - y;
  const right = width - x;
  if (y >= Math.max(500, popupHeight + 100) && y >= below) {
    return x < 190 ? "bottom-left" : right < 190 ? "bottom-right" : "bottom";
  }
  if (below >= popupHeight + 14) return x < 190 ? "top-left" : right < 190 ? "top-right" : "top";
  return x >= 360 ? "right" : right >= x ? "left" : "right";
}
